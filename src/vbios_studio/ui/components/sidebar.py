# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Left navigation: document identity plus section/tool destinations."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.field_text import architecture_label, section_title
from vbios_studio.ui.theme import add_class

Translate = Callable[[str], str]

NAV_ITEMS = (
    ("info", "view-grid-symbolic"),
    ("power", "power-symbolic"),
    ("voltage", "battery-symbolic"),
    ("current", "flash-symbolic"),
    ("clocks", "alarm-symbolic"),
    ("fans", "fan-symbolic"),
    ("memory", "drive-harddisk-symbolic"),
    ("advanced", "applications-system-symbolic"),
)
TOOL_ITEMS = (
    ("apply", "document-send-symbolic"),
    ("diff", "edit-copy-symbolic"),
    ("log", "utilities-terminal-symbolic"),
)


class Sidebar(Gtk.Box):
    def __init__(
        self, _: Translate, controller: UiController, on_select: Callable[[str], None]
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._ = _
        self.controller = controller
        self.on_select = on_select
        self.rows: dict[str, Gtk.ListBoxRow] = {}
        self._building = False

        identity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        identity.set_margin_top(14)
        identity.set_margin_bottom(6)
        identity.set_margin_start(16)
        identity.set_margin_end(16)
        self.product = Gtk.Label(label=_("sidebar.no_document"), xalign=0, wrap=True)
        self.product.add_css_class("vb-product")
        set_accessible(self.product, _("file.product"))
        self.identity_line = Gtk.Label(label="", xalign=0)
        self.identity_line.add_css_class("vb-dim")
        self.chips = Gtk.Box(spacing=6)
        self.arch_chip = Gtk.Label(label="")
        self.arch_chip.add_css_class("vb-chip")
        self.arch_chip.add_css_class("vb-chip-accent")
        self.file_chip = Gtk.Label(label="")
        add_class(self.file_chip, "vb-chip", "vb-dim")
        self.chips.append(self.arch_chip)
        self.chips.append(self.file_chip)
        identity.append(self.product)
        identity.append(self.identity_line)
        identity.append(self.chips)
        self.append(identity)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("navigation-sidebar")
        self.listbox.connect("row-selected", self._on_row_selected)
        scroller.set_child(self.listbox)
        self.append(scroller)
        self.rebuild()
        self.update(controller)

    def _make_row(
        self, key: str, icon_name: str, label: str, count: int | None = None
    ) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.add_css_class("vb-nav-row")
        row._vbios_section_id = key
        box = Gtk.Box(spacing=10)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        box.append(icon)
        text = Gtk.Label(label=label, xalign=0)
        box.append(text)
        if count is not None:
            count_label = Gtk.Label(label=str(count), xalign=1)
            count_label.set_hexpand(True)
            count_label.add_css_class("vb-nav-count")
            box.append(count_label)
        row.set_child(box)
        set_accessible(row, label)
        self.rows[key] = row
        return row

    def rebuild(self) -> None:
        self._building = True
        while (child := self.listbox.get_first_child()) is not None:
            self.listbox.remove(child)
        self.rows.clear()
        _ = self._
        for key, icon in NAV_ITEMS:
            if key not in (
                "info",
                "power",
                "voltage",
                "current",
                "clocks",
                "fans",
                "memory",
                "advanced",
            ):
                continue
            self.listbox.append(
                self._make_row(key, icon, section_title(key, _), None if key == "info" else 0)
            )
        separator = Gtk.ListBoxRow()
        separator.set_selectable(False)
        separator.set_activatable(False)
        separator.set_focusable(False)
        separator.set_can_focus(False)
        line = Gtk.Separator()
        line.set_margin_top(6)
        line.set_margin_bottom(6)
        separator.set_child(line)
        self.listbox.append(separator)
        for key, icon in TOOL_ITEMS:
            label = {
                "apply": _("section.apply"),
                "diff": _("section.diff"),
                "log": _("section.log"),
            }[key]
            self.listbox.append(self._make_row(key, icon, label))
        self._building = False
        self.select(self.controller.current_section)

    def update(self, controller: UiController) -> None:
        self.controller = controller
        snap = controller.snapshot
        if snap is None:
            self.product.set_text(self._("sidebar.no_document"))
            self.identity_line.set_text(self._("sidebar.open_hint"))
            self.arch_chip.set_visible(False)
            self.file_chip.set_visible(False)
        else:
            self.product.set_text(snap.product_name or snap.display_name)
            self.identity_line.set_text(snap.display_name)
            self.arch_chip.set_text(architecture_label(snap.architecture))
            self.arch_chip.set_visible(True)
            self.file_chip.set_text(self._("sidebar.image_count").format(count=len(snap.images)))
            self.file_chip.set_visible(True)
        counts = controller.section_counts()
        for key, row in self.rows.items():
            if key in counts:
                box = row.get_child()
                count_label = box.get_last_child() if box is not None else None
                if isinstance(count_label, Gtk.Label):
                    count_label.set_text("" if key == "info" else str(counts[key]))
        self.select(controller.current_section)

    def select(self, section: str) -> None:
        row = self.rows.get(section)
        if row is not None and self.listbox.get_selected_row() is not row:
            self._building = True
            self.listbox.select_row(row)
            self._building = False

    def _on_row_selected(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if self._building or row is None:
            return
        section = getattr(row, "_vbios_section_id", None)
        if section:
            self.on_select(section)

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.rebuild()
