# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Read-only two-ROM comparison view (field level + image level)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.domain.models import RomDiff
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.components.risk_badge import RiskBadge

Translate = Callable[[str], str]


class DiffView(Gtk.Box):
    def __init__(self, _: Translate, on_choose: Callable[[], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._ = _
        self.on_choose = on_choose
        header = Gtk.Box(spacing=12)
        title = Gtk.Label(label=_("diff.title"), xalign=0)
        title.add_css_class("vb-page-title")
        set_accessible(title, _("diff.title"))
        header.append(title)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        self.choose_button = Gtk.Button(label=_("diff.choose"))
        self.choose_button.add_css_class("suggested-action")
        self.choose_button.connect("clicked", lambda _b: self.on_choose())
        set_accessible(self.choose_button, _("diff.choose"))
        header.append(self.choose_button)
        self.append(header)
        self.summary = Gtk.Label(label=_("diff.empty_hint"), xalign=0)
        self.summary.set_wrap(True)
        self.summary.add_css_class("vb-dim")
        self.append(self.summary)

        self.field_title = Gtk.Label(label=_("diff.fields"), xalign=0)
        self.field_title.add_css_class("vb-section-title")
        self.append(self.field_title)
        self.field_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.field_box.add_css_class("vb-card")
        self.append(self.field_box)

        self.image_title = Gtk.Label(label=_("diff.images"), xalign=0)
        self.image_title.add_css_class("vb-section-title")
        self.append(self.image_title)
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.image_box.add_css_class("vb-card")
        self.append(self.image_box)

    def _clear(self, box: Gtk.Box) -> None:
        while (child := box.get_first_child()) is not None:
            box.remove(child)

    def show_rom_diff(self, diff: RomDiff) -> None:
        self._clear(self.field_box)
        self._clear(self.image_box)
        if not diff.field_diffs and not diff.image_diffs:
            self.summary.set_text(self._("diff.identical"))
            return
        self.summary.set_text(
            self._("diff.summary").format(
                fields=len(diff.field_diffs),
                images=len(diff.image_diffs),
            )
        )
        header = self._row(
            ("diff.column.field", 260),
            ("diff.column.left", 160),
            ("diff.column.right", 160),
            ("diff.column.risk", 100),
            ("diff.column.status", 120),
        )
        self.field_box.append(header)
        for item in diff.field_diffs:
            row = Gtk.Box(spacing=8)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            row.set_margin_start(10)
            row.set_margin_end(10)
            row.append(self._cell(item.label, 260))
            row.append(self._cell(item.left if item.left is not None else "—", 160, ("vb-num",)))
            row.append(self._cell(item.right if item.right is not None else "—", 160, ("vb-num",)))
            risk = Gtk.Box()
            risk.set_size_request(100, -1)
            risk.append(RiskBadge(item.risk, self._))
            row.append(risk)
            row.append(self._cell(self._("diff.status." + item.status), 120))
            if item.changed:
                row.add_css_class("vb-diff-row")
            self.field_box.append(row)

        header = self._row(
            ("diff.column.index", 50),
            ("diff.column.type", 130),
            ("diff.column.size", 100),
            ("diff.column.checksum_left", 140),
            ("diff.column.checksum_right", 140),
            ("diff.column.equal", 90),
        )
        self.image_box.append(header)
        for image in diff.image_diffs:
            row = Gtk.Box(spacing=8)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            row.set_margin_start(10)
            row.set_margin_end(10)
            row.append(self._cell(str(image.index), 50, ("vb-num",)))
            row.append(self._cell(image.kind, 130))
            row.append(self._cell(str(image.size), 100, ("vb-num",)))
            row.append(self._cell(image.checksum_left or "—", 140, ("vb-num",)))
            row.append(self._cell(image.checksum_right or "—", 140, ("vb-num",)))
            row.append(self._cell(self._("common.yes") if image.equal else self._("common.no"), 90))
            self.image_box.append(row)

    def show_compare_dict(self, data: dict[str, Any]) -> None:
        self._clear(self.field_box)
        self._clear(self.image_box)
        fields = data.get("field_diffs", [])
        images = data.get("image_diffs", [])
        if not fields and not images:
            self.summary.set_text(self._("diff.identical"))
            return
        self.summary.set_text(self._("diff.summary").format(fields=len(fields), images=len(images)))
        self.field_box.append(
            self._row(
                ("diff.column.field", 260),
                ("diff.column.left", 160),
                ("diff.column.right", 160),
                ("diff.column.risk", 100),
                ("diff.column.status", 120),
            )
        )
        for item in fields:
            row = Gtk.Box(spacing=8)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            row.set_margin_start(10)
            row.set_margin_end(10)
            row.append(self._cell(str(item.get("label") or item.get("key", "")), 260))
            row.append(
                self._cell(
                    str(item.get("left") if item.get("left") is not None else "—"), 160, ("vb-num",)
                )
            )
            row.append(
                self._cell(
                    str(item.get("right") if item.get("right") is not None else "—"),
                    160,
                    ("vb-num",),
                )
            )
            risk = Gtk.Box()
            risk.set_size_request(100, -1)
            risk.append(RiskBadge(str(item.get("risk", "T0")), self._))
            row.append(risk)
            row.append(self._cell(self._("diff.status.different"), 120))
            self.field_box.append(row)
        self.image_box.append(
            self._row(
                ("diff.column.index", 50),
                ("diff.column.type", 130),
                ("diff.column.size", 100),
                ("diff.column.checksum_left", 140),
                ("diff.column.checksum_right", 140),
                ("diff.column.equal", 90),
            )
        )
        for item in images:
            row = Gtk.Box(spacing=8)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            row.set_margin_start(10)
            row.set_margin_end(10)
            row.append(self._cell(str(item.get("index", "")), 50, ("vb-num",)))
            row.append(self._cell(str(item.get("type", "")), 130))
            row.append(self._cell(str(item.get("size", "")), 100, ("vb-num",)))
            row.append(self._cell(str(item.get("checksum_left") or "—"), 140, ("vb-num",)))
            row.append(self._cell(str(item.get("checksum_right") or "—"), 140, ("vb-num",)))
            row.append(
                self._cell(self._("common.yes") if item.get("equal") else self._("common.no"), 90)
            )
            self.image_box.append(row)

    def _row(self, *columns: tuple[str, int]) -> Gtk.Box:
        row = Gtk.Box(spacing=8)
        row.add_css_class("vb-table-head")
        row.set_margin_top(6)
        row.set_margin_bottom(2)
        row.set_margin_start(10)
        row.set_margin_end(10)
        for msgid, width in columns:
            label = Gtk.Label(label=self._(msgid).upper(), xalign=0)
            label.set_size_request(width, -1)
            row.append(label)
        return row

    def _cell(self, text: str, width: int, css: tuple[str, ...] = ()) -> Gtk.Label:
        label = Gtk.Label(label=text, xalign=0)
        label.set_size_request(width, -1)
        label.set_ellipsize(3)
        for name in css:
            label.add_css_class(name)
        return label

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.summary.set_text(_("diff.empty_hint"))
        self.choose_button.set_label(_("diff.choose"))
        self.field_title.set_text(_("diff.fields"))
        self.image_title.set_text(_("diff.images"))
