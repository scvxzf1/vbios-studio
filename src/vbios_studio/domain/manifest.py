"""Build the versioned manifest written beside every generated ROM."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import FieldChange
from .risk import max_risk
from .rom import RomImage


def checksum_repairs(
    plan_manifest: Mapping[str, Any],
    before_images: Sequence[RomImage],
) -> list[dict[str, Any]]:
    """Translate upstream integrity repairs into per-image checksum records."""
    result: list[dict[str, Any]] = []
    for repair in plan_manifest.get("integrity_repairs") or ():
        if not isinstance(repair, Mapping) or repair.get("kind") != "additive_checksum":
            continue
        offset = int(repair.get("offset", -1))
        image = next((item for item in before_images if item.offset <= offset < item.end), None)
        if image is None:
            continue
        result.append(
            {
                "kind": "additive_checksum",
                "image_index": image.index,
                "image_offset": image.offset,
                "image_size": image.size,
                "checksum_offset": offset,
                "before": image.checksum,
                "after": 0,
                "method": "last-byte-balance",
            }
        )
    return result


def build_manifest(
    *,
    tool_version: str,
    upstream_pin: str,
    source_path: Path,
    source_sha256: str,
    target_path: Path,
    output_sha256: str,
    changes: Sequence[FieldChange],
    plan_manifest: Mapping[str, Any],
    before_images: Sequence[RomImage],
    after_images: Sequence[RomImage],
    report: Mapping[str, Any],
    payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Assemble the documented manifest (FR-3.2) for one generated ROM."""
    repairs = checksum_repairs(plan_manifest, before_images)
    return {
        "schema_version": 1,
        "tool": "vbios-studio",
        "tool_version": tool_version,
        "upstream_pin": upstream_pin,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "operation": "edit",
        "modified": bool(changes),
        "source": str(source_path),
        "source_sha256": source_sha256,
        "target": str(target_path),
        "output": str(target_path),
        "sha256": output_sha256,
        "output_sha256": output_sha256,
        "architecture": (report.get("architecture") or {}).get("family"),
        "format": report.get("format"),
        "pci_device": report.get("pci_device"),
        "batch_risk": max_risk([change.risk for change in changes]),
        "requires_t3_confirmation": any(change.risk == "T3" for change in changes),
        "changes": [
            {
                "key": change.key,
                "label": change.label,
                "old": change.old,
                "new": change.new,
                "unit": change.unit,
                "risk": change.risk,
            }
            for change in changes
        ],
        "field_edits": list(plan_manifest.get("edits") or ()),
        "byte_ranges": list(plan_manifest.get("byte_ranges") or ()),
        "changed_bytes": int(plan_manifest.get("changed_bytes") or 0),
        "images": [
            {
                "index": image.index,
                "kind": image.kind,
                "offset": image.offset,
                "size": image.size,
                "checksum": image.checksum,
                "checksum_ok": image.checksum_ok,
            }
            for image in after_images
        ],
        "checksum_repairs": repairs,
        "payload": dict(payload) if payload else None,
        "cryptographic_signatures": "not verified or regenerated",
        "warning": (
            "Modified image: its vendor signature is stale. Never flash it with nvflash; "
            "apply it only through a loader override."
        ),
    }
