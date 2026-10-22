"""File card identity fields and image chain are rendered from the snapshot DTO."""

from __future__ import annotations

from pathlib import Path

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.a11y import widget_order
from vbios_studio.ui.components.file_info import FileInfoCard
from vbios_studio.ui.demo import demo_snapshot
from vbios_studio.ui.field_text import architecture_label


def test_file_card_renders_identity_and_image_chain(gtk_initialised) -> None:
    snapshot = demo_snapshot(Path("/tmp/rtx5090.rom"))
    card = FileInfoCard(_)
    card.update(snapshot)
    texts = [widget.get_text() for widget in widget_order(card) if hasattr(widget, "get_text")]
    assert "NVIDIA GeForce RTX 5090" in texts
    assert any("10de:2b85" in text and "98.02.2e.00.01" in text for text in texts)
    assert "legacy" in texts and "efi" in texts and "npds-data" in texts
    assert "128 KiB" in texts
    assert "balanced" in texts
    assert card.snapshot is snapshot


def test_architecture_codes_are_human_readable() -> None:
    assert architecture_label("ada") == "Ada AD10x"
    assert architecture_label("blackwell") == "Blackwell GB20x"
    assert architecture_label("Blackwell GB20x") == "Blackwell GB20x"
