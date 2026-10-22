# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Field toolbar: view switch, search/filter toggles and live match counter."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController

Translate = Callable[[str], str]


class FieldToolbar(Gtk.Box):
    def __init__(self, _: Translate, controller: UiController) -> None:
        super().__init__(spacing=10)
        self._ = _
        self.controller = controller
        self.title = Gtk.Label(label=_("fields.title"), xalign=0)
        self.title.add_css_class("vb-section-title")
        set_accessible(self.title, _("fields.title"))
        self.append(self.title)
        self.count = Gtk.Label(label="", xalign=0)
        self.count.add_css_class("vb-dim")
        set_accessible(self.count, _("fields.count"))
        self.append(self.count)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.append(spacer)

        self._refreshing = False
        self.filter_button = Gtk.MenuButton(label=_("fields.filter"))
        self.filter_button.set_tooltip_text(_("fields.filter.tooltip"))
        set_accessible(self.filter_button, _("fields.filter.tooltip"))
        self.filter_button.set_popover(self._filter_popover())
        self.append(self.filter_button)

        switch_box = Gtk.Box()
        switch_box.add_css_class("linked")
        self.table_button = Gtk.ToggleButton(label=_("fields.view.table"))
        self.form_button = Gtk.ToggleButton(label=_("fields.view.form"))
        self.table_button.set_group(self.form_button)
        self.table_button.set_active(True)
        for button, msgid in (
            (self.table_button, "fields.view.table"),
            (self.form_button, "fields.view.form"),
        ):
            set_accessible(button, _(msgid))
            button.connect("toggled", lambda b, mode=msgid: self._on_view_toggled(b, mode))
            switch_box.append(button)
        self.append(switch_box)
        self.refresh()

    def _filter_popover(self) -> Gtk.Popover:
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=self._("fields.filter"), xalign=0)
        heading.add_css_class("vb-dim")
        box.append(heading)
        self.switches: dict[str, Gtk.Switch] = {}
        rows = (
            ("only_modified", "fields.filter.modified"),
            ("only_t3", "fields.filter.t3"),
            ("only_current_section", "fields.filter.section"),
        )
        for key, msgid in rows:
            row = Gtk.Box(spacing=12)
            label = Gtk.Label(label=self._(msgid), xalign=0)
            label.set_hexpand(True)
            switch = Gtk.Switch()
            switch.set_valign(Gtk.Align.CENTER)
            switch.connect("notify::active", lambda s, _p, key=key: self._on_switch(key, s))
            set_accessible(switch, self._(msgid))
            row.append(label)
            row.append(switch)
            box.append(row)
            self.switches[key] = switch
        reset = Gtk.Button(label=self._("fields.filter.reset"))
        reset.add_css_class("flat")
        reset.connect("clicked", lambda _b: self._reset_filters())
        set_accessible(reset, self._("fields.filter.reset"))
        box.append(reset)
        popover.set_child(box)
        return popover

    def _reset_filters(self) -> None:
        self.controller.set_filter(only_modified=False, only_t3=False, only_current_section=False)
        self.controller.set_filter(query="")

    def _on_switch(self, key: str, switch: Gtk.Switch) -> None:
        if not self._refreshing:
            self.controller.toggle_filter(key, switch.get_active())

    def _on_view_toggled(self, button: Gtk.ToggleButton, msgid: str) -> None:
        if not button.get_active():
            return
        self.controller.set_view_mode("table" if msgid == "fields.view.table" else "form")

    def refresh(self) -> None:
        _ = self._
        total = len(self.controller.visible_fields)
        shown = len(self.controller.filtered_fields)
        self.count.set_text(_("fields.count_value").format(shown=shown, total=total))
        set_accessible(self.count, self.count.get_text())
        self.filter_button.set_label(
            _("fields.filter.active").format(count=self.controller.filters.active_count)
            if self.controller.filters.active_count
            else _("fields.filter")
        )
        self._refreshing = True
        for key, switch in self.switches.items():
            value = bool(getattr(self.controller.filters, key))
            if switch.get_active() != value:
                switch.set_active(value)
        self._refreshing = False
        if self.controller.view_mode == "form" and not self.form_button.get_active():
            self.form_button.set_active(True)
        elif self.controller.view_mode == "table" and not self.table_button.get_active():
            self.table_button.set_active(True)

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.title.set_text(_("fields.title"))
        self.filter_button.set_label(_("fields.filter"))
        self.table_button.set_label(_("fields.view.table"))
        self.form_button.set_label(_("fields.view.form"))
        self.refresh()
