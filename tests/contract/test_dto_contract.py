"""Contract tests for the frozen DTO shapes used by the GTK views (t14)."""

from __future__ import annotations

from dataclasses import fields

from vbios_studio.domain.models import EditPreview, FieldDiff, ImageDiff, RomDiff


def _names(model: type[object]) -> list[str]:
    return [item.name for item in fields(model)]


def test_field_diff_shape_is_frozen_for_diff_table() -> None:
    """The diff table renders exactly these six columns, including ``changed``."""
    assert _names(FieldDiff) == ["key", "label", "left", "right", "risk", "changed"]


def test_image_diff_shape_is_frozen_for_diff_table() -> None:
    """Image rows carry kind, size and equal so the UI needs no second lookup."""
    assert _names(ImageDiff) == [
        "index",
        "kind",
        "size",
        "checksum_left",
        "checksum_right",
        "equal",
    ]


def test_rom_diff_and_edit_preview_expose_batch_risk() -> None:
    """The UI can render a full diff and a risk summary from the DTOs alone."""
    assert _names(RomDiff) == ["field_diffs", "image_diffs", "summary"]
    assert "batch_risk" in _names(EditPreview)
    assert "requires_t3_confirmation" in _names(EditPreview)
