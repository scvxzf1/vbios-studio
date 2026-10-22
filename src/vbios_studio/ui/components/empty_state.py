# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Welcome / empty state with drag-and-drop guidance and the support matrix."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from vbios_studio.ui.a11y import set_accessible

Translate = Callable[[str], str]


class EmptyState(Gtk.Box):
    def __init__(self, _: Translate, on_open: Callable[[], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self._ = _
        self._on_open = on_open
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_margin_top(36)
        self.set_margin_bottom(36)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build()

    def _build(self) -> None:
        _ = self._
        page = Adw.StatusPage()
        page.set_icon_name("drive-harddisk-symbolic")
        page.set_title(_("empty.title"))
        page.set_description(_("empty.subtitle"))
        page.add_css_class("vb-empty")
        open_button = Gtk.Button(label=_("empty.open"))
        open_button.add_css_class("suggested-action")
        open_button.add_css_class("pill")
        open_button.set_halign(Gtk.Align.CENTER)
        open_button.connect("clicked", lambda _button: self._on_open())
        set_accessible(open_button, _("empty.open"))
        page.set_child(open_button)
        self.append(page)

        matrix = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        matrix.add_css_class("vb-card")
        matrix.set_margin_start(24)
        matrix.set_margin_end(24)
        matrix.set_size_request(560, -1)
        heading = Gtk.Label(label=_("empty.support"), xalign=0)
        heading.add_css_class("vb-section-title")
        heading.set_margin_top(14)
        heading.set_margin_start(16)
        matrix.append(heading)
        for family, state in (
            ("Blackwell GB20x", "empty.support.full"),
            ("Ada AD10x", "empty.support.full"),
            ("Ampere GA10x", "empty.support.full"),
            ("Turing TU10x/TU11x", "empty.support.experimental"),
            ("GA100 / unknown", "empty.support.readonly"),
        ):
            row = Gtk.Box(spacing=10)
            row.set_margin_start(16)
            row.set_margin_end(16)
            name = Gtk.Label(label=family, xalign=0)
            name.set_hexpand(True)
            state_label = Gtk.Label(label=_(state), xalign=0)
            state_label.add_css_class("vb-dim")
            row.append(name)
            row.append(state_label)
            matrix.append(row)
        note = Gtk.Label(label=_("empty.warning"), xalign=0)
        note.set_wrap(True)
        note.add_css_class("vb-note")
        note.set_margin_start(16)
        note.set_margin_end(16)
        note.set_margin_bottom(14)
        note.set_margin_top(6)
        matrix.append(note)
        self.append(matrix)

    def retranslate(self, _: Translate) -> None:
        # Rebuilding is cheap and guarantees every generated label switches language.
        self._ = _
        while (child := self.get_first_child()) is not None:
            self.remove(child)
        self._build()
