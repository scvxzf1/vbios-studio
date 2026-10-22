"""JSON-compatible serialization of immutable domain snapshots."""

from __future__ import annotations

from typing import Any

from .models import DocumentSnapshot, FieldSnapshot, ImageSnapshot, SectionSnapshot
from .rom import RomStructure


def field_to_dict(field: FieldSnapshot) -> dict[str, Any]:
    """Serialize one field snapshot."""
    return {
        "key": field.key,
        "label": field.label,
        "section": field.section,
        "unit": field.unit,
        "current": field.current,
        "default": field.default,
        "minimum": field.minimum,
        "maximum": field.maximum,
        "risk": field.risk,
        "offset": field.offset,
        "editable": field.editable,
        "opt_in": field.opt_in,
        "experimental": field.experimental,
        "description": field.description,
        "depends_on": dict(field.depends_on) if field.depends_on else None,
    }


def image_to_dict(image: ImageSnapshot) -> dict[str, Any]:
    """Serialize one image snapshot."""
    return {
        "index": image.index,
        "kind": image.kind,
        "offset": image.offset,
        "size": image.size,
        "checksum_ok": image.checksum_ok,
        "is_last": image.is_last,
    }


def section_to_dict(section: SectionSnapshot) -> dict[str, Any]:
    """Serialize one navigation section."""
    return {"id": section.id, "title": section.title, "order": section.order}


def document_to_dict(document: DocumentSnapshot) -> dict[str, Any]:
    """Serialize a document snapshot including its complete field catalog."""
    return {
        "schema_version": 1,
        "path": str(document.path),
        "display_name": document.display_name,
        "sha256": document.sha256,
        "file_size": document.file_size,
        "architecture": document.architecture,
        "product_name": document.product_name,
        "pci_id": document.pci_id,
        "bios_version": document.bios_version,
        "images": [image_to_dict(image) for image in document.images],
        "sections": [section_to_dict(section) for section in document.sections],
        "fields": [field_to_dict(field) for field in document.fields],
    }


def structure_to_dict(structure: RomStructure) -> dict[str, Any]:
    """Serialize the pure structural report."""
    return structure.to_dict()
