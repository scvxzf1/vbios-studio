"""Build a ``DocumentSnapshot`` and its catalog from an upstream report.

The upstream adapter supplies a plain report dictionary and the pure ROM
structure; this module owns the immutable conversion, the read-only fallback
decision and the field-risk annotation. It performs no I/O.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import build_field_snapshots
from .errors import INTEGRITY_FAILED, STRUCTURE_INVALID, UNSUPPORTED_ARCHITECTURE
from .models import DocumentSnapshot, ImageSnapshot
from .rom import RomStructure
from .sections import section_snapshots

KNOWN_FAMILIES = frozenset({"ada", "ampere", "turing", "blackwell-gb20x"})


@dataclass(frozen=True, slots=True)
class CatalogDocument:
    """A document snapshot plus the reason editing is enabled or disabled."""

    document: DocumentSnapshot
    family: str
    known_architecture: bool
    read_only: bool
    read_only_code: str
    read_only_reason: str


def _diagnostic(report: Mapping[str, Any]) -> tuple[str, str]:
    for item in report.get("diagnostics") or ():
        if isinstance(item, Mapping):
            return str(item.get("code") or UNSUPPORTED_ARCHITECTURE), str(
                item.get("message") or "unrecognized image"
            )
    architecture = report.get("architecture") or {}
    return UNSUPPORTED_ARCHITECTURE, str(
        architecture.get("reason") or "architecture not recognized"
    )


def build_catalog_document(
    *,
    path: Path,
    sha256: str,
    file_size: int,
    report: Mapping[str, Any],
    structure: RomStructure,
) -> CatalogDocument:
    """Build the UI document and decide whether the image is editable."""
    architecture = report.get("architecture") or {}
    family = str(architecture.get("family") or "unknown")
    known = family in KNOWN_FAMILIES and bool(report.get("format"))
    descriptors = [dict(item) for item in report.get("fields") or () if isinstance(item, Mapping)]
    fields = build_field_snapshots(
        descriptors, family=family if known else None, include_placeholders=known
    )
    images = tuple(
        ImageSnapshot(
            index=item.index,
            kind=item.kind,
            offset=item.offset,
            size=item.size,
            checksum_ok=item.checksum_ok,
            is_last=item.is_last,
        )
        for item in structure.images
    )
    versions = list(report.get("versions") or ())
    document = DocumentSnapshot(
        path=path,
        display_name=path.name,
        sha256=sha256,
        file_size=file_size,
        architecture=family if known else "unknown",
        product_name=str(architecture.get("product"))
        if known and architecture.get("product")
        else None,
        pci_id=report.get("pci_device"),
        bios_version=str(versions[0]) if versions else None,
        images=images,
        sections=section_snapshots(field.key for field in fields),
        fields=fields,
    )
    integrity = report.get("integrity") or {}
    if not known:
        code, reason = _diagnostic(report)
        return CatalogDocument(document, family, known, True, code, reason)
    if structure.issues or not structure.images:
        reason = structure.issues[0].message if structure.issues else "no PCI/NPDS images found"
        return CatalogDocument(document, family, known, True, STRUCTURE_INVALID, reason)
    if integrity.get("valid") is False:
        return CatalogDocument(
            document,
            family,
            known,
            True,
            INTEGRITY_FAILED,
            "source image failed the upstream integrity checks",
        )
    if not any(field.editable for field in fields):
        reason_any: Any = ((report.get("capabilities") or {}).get("edit") or {}).get("reason")
        return CatalogDocument(
            document,
            family,
            known,
            True,
            UNSUPPORTED_ARCHITECTURE,
            str(reason_any or "no editable field has validated evidence"),
        )
    return CatalogDocument(document, family, known, False, "", "")


def document_versions(report: Mapping[str, Any]) -> list[str]:
    """Return the parsed VBIOS version strings for reports that need them."""
    return [str(item) for item in report.get("versions") or ()]
