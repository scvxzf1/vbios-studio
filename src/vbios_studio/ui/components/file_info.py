# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""File information card and image-chain table."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.domain.models import DocumentSnapshot
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.field_text import architecture_label
from vbios_studio.ui.theme import add_class

Translate = Callable[[str], str]


def _text(value: str | None, fallback: str) -> str:
    return value if value else fallback


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    if size >= 1024:
        return f"{size / 1024:.0f} KiB"
    return f"{size} B"


class FileInfoCard(Gtk.Box):
    """Product identity, hashes and the parsed image chain, all read-only."""

    def __init__(self, _: Translate) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._ = _
        self.add_css_class("vb-card")
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.append(self._content)
        self.snapshot: DocumentSnapshot | None = None

    def update(self, snapshot: DocumentSnapshot) -> None:
        self.snapshot = snapshot
        self._rebuild()

    def retranslate(self, _: Translate) -> None:
        self._ = _
        if self.snapshot is not None:
            self._rebuild()

    def _rebuild(self) -> None:
        while (child := self._content.get_first_child()) is not None:
            self._content.remove(child)
        assert self.snapshot is not None
        snap = self.snapshot
        unknown = self._("common.unknown")
        top = Gtk.Box(spacing=14)
        top.set_margin_top(16)
        top.set_margin_bottom(12)
        top.set_margin_start(18)
        top.set_margin_end(18)
        icon = Gtk.Image.new_from_icon_name("video-display-symbolic")
        icon.set_pixel_size(44)
        icon.set_valign(Gtk.Align.START)
        top.append(icon)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_hexpand(True)
        title_row = Gtk.Box(spacing=8)
        product_name = _text(snap.product_name, unknown)
        product = Gtk.Label(label=product_name, xalign=0)
        product.add_css_class("vb-product")
        set_accessible(product, self._("file.product"))
        title_row.append(product)
        arch_chip = Gtk.Label(label=architecture_label(snap.architecture))
        arch_chip.add_css_class("vb-chip")
        arch_chip.add_css_class("vb-chip-accent")
        set_accessible(arch_chip, self._("file.architecture"))
        title_row.append(arch_chip)
        info.append(title_row)
        pci = _text(snap.pci_id, unknown)
        bios = _text(snap.bios_version, unknown)
        board = getattr(snap, "board", None)
        build_date = getattr(snap, "build_date", None)
        line = self._("file.identity_line").format(pci=pci, bios=bios)
        identity = Gtk.Label(label=line, xalign=0, wrap=True)
        identity.add_css_class("vb-dim")
        set_accessible(identity, self._("file.identity"))
        info.append(identity)
        if board or build_date:
            extra = self._("file.board_build_line").format(
                board=board or unknown, build=build_date or unknown
            )
            extra_label = Gtk.Label(label=extra, xalign=0)
            extra_label.add_css_class("vb-dim")
            info.append(extra_label)
        sha_text = self._("file.sha256_line").format(
            sha=snap.sha256, size=format_size(snap.file_size)
        )
        sha = Gtk.Label(label=sha_text, xalign=0)
        add_class(sha, "vb-mono", "vb-dim")
        sha.set_selectable(True)
        set_accessible(sha, self._("file.sha256"))
        info.append(sha)
        top.append(info)

        arch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        arch_box.set_valign(Gtk.Align.START)
        arch_caption = Gtk.Label(label=self._("file.architecture").upper(), xalign=0)
        arch_caption.add_css_class("vb-dim")
        arch_value = Gtk.Label(label=architecture_label(snap.architecture), xalign=0)
        arch_value.add_css_class("vb-section-title")
        arch_box.append(arch_caption)
        arch_box.append(arch_value)
        top.append(arch_box)
        self._content.append(top)
        self._content.append(Gtk.Separator())

        chain_header = Gtk.Box(spacing=0)
        chain_header.set_margin_top(8)
        chain_header.set_margin_bottom(2)
        chain_header.set_margin_start(18)
        chain_header.set_margin_end(18)
        columns = (
            ("file.chain.index", 44),
            ("file.chain.type", 130),
            ("file.chain.offset", 110),
            ("file.chain.size", 110),
            ("file.chain.checksum", 130),
            ("file.chain.last", 70),
        )
        for msgid, width in columns:
            label = Gtk.Label(label=self._(msgid).upper(), xalign=0)
            label.set_size_request(width, -1)
            label.add_css_class("vb-dim")
            chain_header.append(label)
        self._content.append(chain_header)

        for image in snap.images:
            row = Gtk.Box(spacing=0)
            row.set_margin_top(3)
            row.set_margin_bottom(3)
            row.set_margin_start(18)
            row.set_margin_end(18)
            cells = (
                (str(image.index), 44, "vb-mono", Gtk.Align.START),
                (image.kind, 130, "", Gtk.Align.START),
                (f"0x{image.offset:06X}", 110, "vb-mono", Gtk.Align.START),
                (format_size(image.size), 110, "vb-mono", Gtk.Align.START),
                (
                    self._("file.chain.balanced")
                    if image.checksum_ok
                    else self._("file.chain.unbalanced"),
                    130,
                    "",
                    Gtk.Align.START,
                ),
                (
                    self._("common.yes") if image.is_last else self._("common.no"),
                    70,
                    "",
                    Gtk.Align.START,
                ),
            )
            for text, width, css, align in cells:
                label = Gtk.Label(label=text, xalign=0 if align == Gtk.Align.START else 1)
                label.set_size_request(width, -1)
                if css:
                    label.add_css_class(css)
                if text in (self._("file.chain.balanced"), self._("file.chain.unbalanced")):
                    label.add_css_class("vb-ok" if image.checksum_ok else "vb-bad")
                row.append(label)
            self._content.append(row)
        spacer = Gtk.Box()
        spacer.set_size_request(-1, 10)
        self._content.append(spacer)
