# mypy: disable-error-code="no-untyped-call"
"""Bridge between VBIOS Studio DTOs and the vendored ``nvidia_vbios`` API.

The upstream package is a byte-for-byte mirror pinned in ``UPSTREAM.md``. Only
this module may import it; domain, ports and UI stay independent of upstream
implementation details. All validation and byte generation still happen in the
upstream editor, wrapped in the immutable DTOs and risk registry of this project.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from nvidia_vbios import __version__ as _upstream_version
from nvidia_vbios.editor import normalize as upstream_normalize
from nvidia_vbios.editor import plan as upstream_plan
from nvidia_vbios.editor import save as upstream_save
from nvidia_vbios.rom import VbiosError, inspect_image
from nvidia_vbios.rom import load as upstream_load
from vbios_studio import __version__ as _tool_version
from vbios_studio.domain.catalog import format_value
from vbios_studio.domain.document import build_catalog_document
from vbios_studio.domain.errors import (
    FIELD_READ_ONLY,
    INTEGRITY_FAILED,
    IO_ERROR,
    NO_CHANGES,
    NOT_OPENED,
    OUTPUT_EXISTS,
    SOURCE_AS_OUTPUT,
    SOURCE_CHANGED,
    UNKNOWN_FIELD,
    UNSUPPORTED_ARCHITECTURE,
    DomainError,
)
from vbios_studio.domain.manifest import build_manifest, checksum_repairs
from vbios_studio.domain.models import (
    DocumentSnapshot,
    EditPreview,
    FieldChange,
    FieldError,
    ManifestView,
    SaveResult,
)
from vbios_studio.domain.risk import max_risk
from vbios_studio.domain.risk_registry import classify_change, is_registered
from vbios_studio.domain.rom import scan_rom
from vbios_studio.domain.serialization import document_to_dict, structure_to_dict

UPSTREAM_PIN = "1f8ee665bd175bd9ede367e6d15308f837bd987b"
_REPRESENTATIONS = {
    "ada": "ada-relocated-v2",
    "ampere": "ampere-relocated-v1",
    "turing": "turing-e0-end-v1",
}
_HINTS = {
    "OUT_OF_BOUNDS": "Use a value inside the field minimum/maximum and ordering group.",
    "UNREPRESENTABLE_VALUE": "Use a value exactly representable in the stored units.",
    "FIELD_READ_ONLY": "This field cannot be written on the loaded image.",
    "UNKNOWN_FIELD": "The field is not part of this image's validated catalog.",
    "INTEGRITY_FAILED": "The source image failed integrity checks; reload a pristine ROM.",
    "UNSUPPORTED_ARCHITECTURE": "Only read-only structural inspection is available for this image.",
    "DEPENDENT_FIELD_DISABLED": "Enable the dependent switch in the same edit.",
}


def upstream_version() -> str:
    """Return the vendored upstream editor version without importing GTK."""
    return _upstream_version


def _error(exc: VbiosError, fallback: str = INTEGRITY_FAILED) -> DomainError:
    code = str(getattr(exc, "code", fallback))
    return DomainError(
        code,
        str(exc),
        _HINTS.get(code, "Fix the input and retry; no files were written."),
        getattr(exc, "details", {}) or {},
    )


def _same_value(left: str | None, right: str) -> bool:
    try:
        return left is not None and Decimal(left) == Decimal(right)
    except (InvalidOperation, ValueError):
        return left == right


class UpstreamEditorAdapter:
    """``EditorPort`` implementation backed by the vendored editor."""

    def __init__(self) -> None:
        self._image: Any | None = None
        self._report: dict[str, Any] = {}
        self._document: DocumentSnapshot | None = None
        self._structure: Any | None = None
        self._descriptors: dict[str, dict[str, Any]] = {}
        self._fields: dict[str, Any] = {}
        self._staged: dict[str, str] = {}
        self._changes: tuple[FieldChange, ...] = ()
        self._planned: Any | None = None
        self._read_only = True
        self._read_only_code = NOT_OPENED
        self._read_only_reason = "No ROM has been opened."

    # ---------------------------------------------------------------- loading
    def open(self, path: Path) -> DocumentSnapshot:
        """Load a ROM read-only and build its snapshot and field catalog."""
        source = Path(path)
        try:
            image = upstream_load(str(source))
        except VbiosError as exc:
            raise _error(exc, IO_ERROR) from exc
        try:
            report = inspect_image(image)
        except Exception as exc:  # hostile files must degrade, not crash
            report = {
                "architecture": {"family": "unknown", "reason": str(exc)},
                "diagnostics": [
                    {"code": getattr(exc, "code", "UNSUPPORTED_FORMAT"), "message": str(exc)}
                ],
                "fields": [],
                "versions": [],
                "pci_device": None,
                "format": None,
                "integrity": {"valid": None},
            }
        structure = scan_rom(image.blob)
        catalog = build_catalog_document(
            path=source,
            sha256=image.sha256,
            file_size=len(image.blob),
            report=report,
            structure=structure,
        )
        self._image, self._report, self._document, self._structure = (
            image,
            report,
            catalog.document,
            structure,
        )
        self._descriptors = {
            str(item["key"]): dict(item)
            for item in report.get("fields") or ()
            if isinstance(item, Mapping)
        }
        self._fields = {field.key: field for field in catalog.document.fields}
        self._staged, self._changes, self._planned = {}, (), None
        self._read_only = catalog.read_only
        self._read_only_code = catalog.read_only_code
        self._read_only_reason = catalog.read_only_reason
        return catalog.document

    def catalog_json(self) -> dict[str, Any]:
        """Return the field-catalog JSON including the structural report."""
        if self._document is None or self._structure is None:
            raise DomainError(
                NOT_OPENED, "open a ROM before requesting a catalog", "call open() first"
            )
        result = document_to_dict(self._document)
        result.update(
            read_only=self._read_only,
            read_only_code=self._read_only_code or None,
            read_only_reason=self._read_only_reason or None,
            structure=structure_to_dict(self._structure),
            upstream={"version": upstream_version(), "pin": UPSTREAM_PIN},
        )
        return result

    # --------------------------------------------------------------- staging
    def stage(self, changes: Mapping[str, str]) -> EditPreview:
        """Validate and replace the staged change set, returning a preview."""
        if self._document is None:
            raise DomainError(NOT_OPENED, "open a ROM before staging changes", "call open() first")
        requested = {str(key): str(value) for key, value in changes.items()}
        if not requested:
            self.reset()
            return EditPreview((), (), "T0", False)
        if self._read_only:
            return self._errors(
                [
                    FieldError(
                        key=key,
                        code=self._read_only_code or UNSUPPORTED_ARCHITECTURE,
                        message=self._read_only_reason,
                        hint="This image is a read-only structural report.",
                    )
                    for key in (requested or {"*": ""})
                ]
            )
        errors: list[FieldError] = []
        for key in requested:
            descriptor, field = self._descriptors.get(key), self._fields.get(key)
            if field is None:
                errors.append(
                    FieldError(key, UNKNOWN_FIELD, f"{key} is not in this image's catalog", "")
                )
            elif (
                descriptor is None
                or not descriptor.get("editable")
                or not field.editable
                or not is_registered(key)
            ):
                errors.append(
                    FieldError(
                        key,
                        FIELD_READ_ONLY,
                        f"{key} is read-only on this image",
                        "Only independently validated fields can be changed.",
                    )
                )
        if errors:
            return self._errors(errors)
        try:
            planned = upstream_plan(self._image, requested)
        except VbiosError as exc:
            error = _error(exc)
            key = str(error.details.get("field") or next(iter(requested), "*"))
            return self._errors([FieldError(key, error.code, error.message, error.hint)])
        changes_out: list[FieldChange] = []
        for key, raw in requested.items():
            field = self._fields[key]
            new = format_value(raw) or raw
            if _same_value(field.current, new):
                continue
            changes_out.append(
                FieldChange(
                    key=key,
                    label=field.label,
                    old=field.current,
                    new=new,
                    unit=field.unit,
                    risk=classify_change(
                        key, field.current, new, family=self._family, editable=field.editable
                    ),
                )
            )
        self._staged, self._planned = requested, planned
        self._changes = tuple(changes_out)
        levels = [change.risk for change in self._changes]
        return EditPreview(
            changed=self._changes,
            errors=(),
            batch_risk=max_risk(levels),
            requires_t3_confirmation="T3" in levels,
        )

    def _errors(self, errors: Sequence[FieldError]) -> EditPreview:
        return EditPreview(
            changed=(), errors=tuple(errors), batch_risk="T0", requires_t3_confirmation=False
        )

    @property
    def _family(self) -> str:
        return self._document.architecture if self._document else "unknown"

    def preview(self) -> ManifestView:
        """Return the manifest that the next save would publish."""
        if self._document is None:
            raise DomainError(NOT_OPENED, "open a ROM before previewing", "call open() first")
        repairs: tuple[Mapping[str, Any], ...] = ()
        if self._planned is not None and self._structure is not None:
            repairs = tuple(checksum_repairs(self._planned.manifest, self._structure.images))
        return ManifestView(
            source_sha256=self._document.sha256,
            tool_version=_tool_version,
            upstream_pin=UPSTREAM_PIN,
            changes=self._changes,
            checksum_repairs=repairs,
            modified=bool(self._changes),
        )

    def reset(self) -> None:
        """Discard staged changes and the cached plan, keeping the ROM open."""
        self._staged, self._changes, self._planned = {}, (), None

    # --------------------------------------------------------------- saving
    def _payload(self, target: Path, image: Any) -> tuple[Path, bytes, str | None]:
        representation = _REPRESENTATIONS.get(self._family)
        used = representation
        try:
            normalized = (
                upstream_normalize(image, representation=representation)
                if representation
                else upstream_normalize(image)
            )
        except VbiosError:
            if representation is None:
                raise
            normalized, used = upstream_normalize(image), "normalized-bank"
        suffix = "-loader-e0end.bin" if self._family == "turing" else "-loader.bin"
        return target.with_name(target.stem + suffix), normalized.blob, used

    def save_as(self, path: Path) -> SaveResult:
        """Write a new ROM, manifest and loader payload without touching the source."""
        if self._document is None:
            raise DomainError(NOT_OPENED, "open a ROM before saving", "call open() first")
        if self._planned is None or not self._changes:
            raise DomainError(
                NO_CHANGES, "no staged change to save", "stage at least one field first"
            )
        target = Path(path)
        source = Path(self._document.path)
        assert self._structure is not None
        if target.resolve() == source.resolve():
            raise DomainError(SOURCE_AS_OUTPUT, "output must not overwrite the source", "new path")
        manifest_path = target.with_name(target.name + ".json")
        try:
            payload_path, payload_blob, representation = self._payload(target, self._planned.image)
        except VbiosError as exc:
            raise _error(exc, INTEGRITY_FAILED) from exc
        for candidate in (target, manifest_path, payload_path):
            if candidate.exists() or candidate.is_symlink():
                raise DomainError(
                    OUTPUT_EXISTS, f"refusing to overwrite {candidate}", "choose a new path"
                )
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with payload_path.open("xb") as stream:
                stream.write(payload_blob)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise DomainError(
                IO_ERROR, f"cannot write loader payload: {exc}", "check permissions"
            ) from exc
        payload_sha = hashlib.sha256(payload_blob).hexdigest()
        after = scan_rom(self._planned.blob)
        manifest = build_manifest(
            tool_version=_tool_version,
            upstream_pin=UPSTREAM_PIN,
            source_path=source,
            source_sha256=self._document.sha256,
            target_path=target,
            output_sha256=self._planned.image.sha256,
            changes=self._changes,
            plan_manifest=self._planned.manifest,
            before_images=self._structure.images,
            after_images=after.images,
            report=self._report,
            payload={
                "path": str(payload_path),
                "sha256": payload_sha,
                "size": len(payload_blob),
                "representation": representation,
            },
        )
        try:
            upstream_save(self._planned, target, manifest=manifest)
        except VbiosError as exc:
            payload_path.unlink(missing_ok=True)
            raise _error(exc) from exc
        actual_source = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_source != self._document.sha256:
            raise DomainError(
                SOURCE_CHANGED, "source ROM changed since it was opened", "reopen the source"
            )
        output_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        if output_sha != self._planned.image.sha256:
            raise DomainError(
                INTEGRITY_FAILED, "published ROM does not match the planned bytes", "retry the save"
            )
        view = ManifestView(
            source_sha256=self._document.sha256,
            tool_version=_tool_version,
            upstream_pin=UPSTREAM_PIN,
            changes=self._changes,
            checksum_repairs=tuple(manifest["checksum_repairs"]),
            modified=True,
        )
        return SaveResult(
            path=target, sha256=output_sha, manifest=view, payload_paths=(payload_path,)
        )

    def export_loader_payload(self, path: Path, *, staged: bool = True) -> Path:
        """Export a loader payload for the staged image (or the source when not staged)."""
        if self._document is None:
            raise DomainError(
                NOT_OPENED, "open a ROM before exporting a payload", "call open() first"
            )
        image = self._planned.image if staged and self._planned is not None else self._image
        payload_path, payload, _ = self._payload(Path(path), image)
        try:
            with payload_path.open("xb") as stream:
                stream.write(payload)
        except FileExistsError as exc:
            raise DomainError(
                OUTPUT_EXISTS, f"refusing to overwrite {payload_path}", "choose a new path"
            ) from exc
        except OSError as exc:
            raise DomainError(
                IO_ERROR, f"cannot write loader payload: {exc}", "check permissions"
            ) from exc
        return payload_path
