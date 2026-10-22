"""In-memory demo ports used by ``--selftest`` and screenshot generation.

They exercise every view without touching a ROM, the registry or the network.
The real application injects adapters through the same protocols.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import (
    ApplyPreview,
    ApplyResult,
    DeviceStatus,
    DocumentSnapshot,
    EditPreview,
    FieldChange,
    FieldDiff,
    FieldError,
    ImageDiff,
    ManifestView,
    RomDiff,
    SaveResult,
)
from vbios_studio.domain.risk import max_risk
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.demo_data import demo_snapshot


class DemoEditor:
    def __init__(self, path: Path | None = None) -> None:
        self.snapshot = demo_snapshot(path)
        self._original = {field.key: field.current for field in self.snapshot.fields}
        self._changes: dict[str, str] = {}

    def open(self, path: Path) -> DocumentSnapshot:
        self.snapshot = demo_snapshot(path)
        self._original = {field.key: field.current for field in self.snapshot.fields}
        self._changes = {}
        return self.snapshot

    def stage(self, changes: Mapping[str, str]) -> EditPreview:
        fields = {field.key: field for field in self.snapshot.fields}
        changed: list[FieldChange] = []
        errors = []
        for key, value in changes.items():
            field = fields.get(key)
            if field is None:
                errors.append(self._error(key, "UNKNOWN_FIELD", f"Unknown field: {key}"))
                continue
            if not field.editable:
                errors.append(self._error(key, "FIELD_READ_ONLY", f"{field.label} is read-only"))
                continue
            try:
                number = float(value)
            except ValueError:
                errors.append(self._error(key, "INVALID_VALUE", f"{field.label} requires a number"))
                continue
            if (field.minimum is not None and number < float(field.minimum)) or (
                field.maximum is not None and number > float(field.maximum)
            ):
                errors.append(
                    self._error(key, "OUT_OF_RANGE", f"{field.label} is outside its range")
                )
                continue
            if str(value) != str(field.current):
                changed.append(
                    FieldChange(key, field.label, field.current, str(value), field.unit, field.risk)
                )
        self._changes = {
            key: value for key, value in changes.items() if key not in {e.key for e in errors}
        }
        risk = max_risk(change.risk for change in changed)
        return EditPreview(tuple(changed), tuple(errors), risk, risk == "T3")

    def _error(self, key: str, code: str, message: str) -> FieldError:
        return FieldError(key, code, message, "Correct the value and try again.")

    def preview(self) -> ManifestView:
        return ManifestView(self.snapshot.sha256, "0.1.0", "demo", (), (), bool(self._changes))

    def save_as(self, path: Path) -> SaveResult:
        data = b"demo" + str(self._changes).encode()
        return SaveResult(Path(path), hashlib.sha256(data).hexdigest(), self.preview(), ())

    def reset(self) -> None:
        self._changes = {}


class DemoDiff:
    def diff_against(self, path: Path) -> RomDiff:
        right = demo_snapshot(path, variant=1)
        left = demo_snapshot(Path("/tmp/demo-rtx5090.rom"))
        field_diffs = []
        for lf, rf in zip(left.fields, right.fields, strict=True):
            if lf.current != rf.current:
                field_diffs.append(
                    FieldDiff(lf.key, lf.label, lf.current, rf.current, lf.risk, True)
                )
        image_diffs = [
            ImageDiff(1, "legacy", 131072, "balanced", "balanced", True),
            ImageDiff(2, "efi", 262144, "balanced", "balanced", True),
            ImageDiff(3, "npds-data", 655360, "balanced", "balanced", True),
        ]
        return RomDiff(
            tuple(field_diffs), tuple(image_diffs), {"fields": len(field_diffs), "images": 0}
        )


class DemoProfile:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "schema_version": 1,
            "architecture": "Blackwell GB20x",
            "changes": {},
        }

    def export_changes(self) -> dict[str, Any]:
        return dict(self.data)

    def apply_profile(self, document: Mapping[str, Any]) -> EditPreview:
        if document.get("schema_version") != 1:
            raise DomainError(
                "PROFILE_SCHEMA", "Unsupported preset schema.", "Use schema_version 1."
            )
        if document.get("architecture") != "Blackwell GB20x":
            raise DomainError(
                "PROFILE_ARCH_MISMATCH",
                "Preset architecture does not match.",
                "Use a preset for this GPU.",
            )
        changes = document.get("changes") or {}
        return EditPreview(
            tuple(
                FieldChange(key, key, None, str(value), "", "T2") for key, value in changes.items()
            ),
            (),
            "T2",
            False,
        )


class DemoApply:
    def __init__(self) -> None:
        self.dry_run_calls = 0
        self.execute_calls = 0
        self.restore_calls = 0

    def device_status(self) -> DeviceStatus:
        return DeviceStatus(
            0, "NVIDIA GeForce RTX 5090", "10de:2b85", "621.01", "no-override", True
        )

    def dry_run(self) -> ApplyPreview:
        self.dry_run_calls += 1
        return ApplyPreview(
            "load",
            r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
            {"vbios": "<32 bytes>", "EnableGpuFirmware": "0x11"},
            40,
            True,
            ("Modifying the registry requires administrator rights.",),
        )

    def execute(self) -> ApplyResult:
        self.execute_calls += 1
        return ApplyResult(True, "override-active", "Override applied.", {})

    def restore(self) -> ApplyResult:
        self.restore_calls += 1
        return ApplyResult(True, "no-override", "Previous state restored.", {})


def demo_controller() -> UiController:
    return UiController(DemoEditor(), DemoDiff(), DemoProfile(), DemoApply())
