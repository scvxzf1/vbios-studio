"""Production ``DiffPort`` adapter built on the pure document comparator.

The comparison algorithm itself lives in the pure UI-neutral
``vbios_studio.ui.diff_model.compare`` function. The composition root injects
that callable so this adapter never imports the UI and never duplicates the
algorithm. This module only loads the right-hand ROM and converts the frozen
mapping into the domain ``RomDiff`` DTO.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

from vbios_studio.domain.errors import NOT_OPENED, DomainError
from vbios_studio.domain.models import DocumentSnapshot, FieldDiff, ImageDiff, RiskLevel, RomDiff

from .upstream import UpstreamEditorAdapter

CompareDocuments = Callable[[DocumentSnapshot, DocumentSnapshot], Mapping[str, Any] | RomDiff]


def _risk(value: Any) -> RiskLevel:
    return cast(RiskLevel, value if value in {"T0", "T1", "T2", "T3"} else "T0")


def _as_rom_diff(raw: Mapping[str, Any] | RomDiff) -> RomDiff:
    if isinstance(raw, RomDiff):
        return raw
    field_diffs = tuple(
        FieldDiff(
            key=str(item.get("key", "")),
            label=str(item.get("label", "")),
            left=item.get("left"),
            right=item.get("right"),
            risk=_risk(item.get("risk")),
            changed=bool(item.get("changed", True)),
        )
        for item in raw.get("field_diffs") or ()
        if isinstance(item, Mapping)
    )
    image_diffs = tuple(
        ImageDiff(
            index=int(item.get("index", 0)),
            kind=str(item.get("kind", item.get("type", "unknown"))),
            size=int(item.get("size", 0)),
            checksum_left=item.get("checksum_left"),
            checksum_right=item.get("checksum_right"),
            equal=bool(item.get("equal", False)),
        )
        for item in raw.get("image_diffs") or ()
        if isinstance(item, Mapping)
    )
    return RomDiff(
        field_diffs=field_diffs,
        image_diffs=image_diffs,
        summary={"fields_changed": len(field_diffs), "images_changed": len(image_diffs)},
    )


class UpstreamDiffAdapter:
    """``DiffPort`` implementation using the open editor and an injected comparator."""

    def __init__(self, editor: UpstreamEditorAdapter, compare: CompareDocuments) -> None:
        self._editor = editor
        self._compare = compare

    def diff_against(self, path: Path) -> RomDiff:
        """Compare the currently open document with the ROM at ``path``."""
        left = getattr(self._editor, "_document", None)
        if left is None:
            raise DomainError(NOT_OPENED, "open a ROM before comparing", "call open() first")
        target = UpstreamEditorAdapter()
        right = target.open(Path(path))
        return _as_rom_diff(self._compare(left, right))
