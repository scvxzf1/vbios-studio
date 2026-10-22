# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Collapsible log panel with copy and clear actions."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController

Translate = Callable[[str], str]


class LogPanel(Gtk.Expander):
    def __init__(self, _: Translate, controller: UiController) -> None:
        super().__init__(label=_("log.title"))
        self._ = _
        self.controller = controller
        self.set_expanded(False)
        set_accessible(self, _("log.title"))
        self.add_css_class("vb-log-panel")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        toolbar = Gtk.Box(spacing=6)
        toolbar.set_halign(Gtk.Align.END)
        self.copy_button = Gtk.Button(label=_("log.copy"))
        self.clear_button = Gtk.Button(label=_("log.clear"))
        for button, text in (
            (self.copy_button, _("log.copy")),
            (self.clear_button, _("log.clear")),
        ):
            button.add_css_class("flat")
            set_accessible(button, text)
            toolbar.append(button)
        box.append(toolbar)

        self.view = Gtk.TextView()
        self.view.set_editable(False)
        self.view.set_cursor_visible(False)
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view.add_css_class("vb-log")
        set_accessible(self.view, _("log.title"))
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(96)
        scroller.set_max_content_height(180)
        scroller.set_child(self.view)
        box.append(scroller)
        self.set_child(box)
        self.copy_button.connect("clicked", lambda _b: self.copy())
        self.clear_button.connect("clicked", lambda _b: self.clear())
        controller.subscribe(self._on_change)
        self.refresh()

    def _on_change(self, reason: str) -> None:
        if reason == "log":
            self.refresh()

    def refresh(self) -> None:
        lines = [
            f"{entry.timestamp.strftime('%H:%M:%S')}  {entry.level:<5}  {entry.message}"
            for entry in self.controller.log_entries[-200:]
        ]
        self.view.get_buffer().set_text("\n".join(lines) if lines else self._("log.empty"))

    def copy(self) -> None:
        buffer = self.view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        Gdk.Display.get_default().get_clipboard().set(text)

    def clear(self) -> None:
        self.controller.log_entries.clear()
        self.refresh()

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.set_label(_("log.title"))
        self.copy_button.set_label(_("log.copy"))
        self.clear_button.set_label(_("log.clear"))
        set_accessible(self.view, _("log.title"))
        self.refresh()
