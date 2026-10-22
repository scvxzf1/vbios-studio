# ruff: noqa: E402
"""Help → keyboard shortcuts."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from vbios_studio.ui.a11y import set_accessible

Translate = Callable[[str], str]

SHORTCUTS = (
    ("shortcut.open", "Ctrl+O"),
    ("shortcut.save", "Ctrl+Shift+S"),
    ("shortcut.undo", "Ctrl+Z"),
    ("shortcut.redo", "Ctrl+Y / Ctrl+Shift+Z"),
    ("shortcut.search", "Ctrl+F"),
    ("shortcut.log", "Ctrl+L"),
    ("shortcut.close", "Ctrl+W"),
)


def show_shortcuts(parent: Gtk.Window, _: Translate) -> Adw.Window:
    window = Adw.Window(transient_for=parent, modal=True, title=_("help.shortcuts"))
    window.set_default_size(460, 420)
    toolbar = Adw.ToolbarView()
    header = Adw.HeaderBar()
    header.set_title_widget(Gtk.Label(label=_("help.shortcuts")))
    toolbar.add_top_bar(header)
    page = Adw.PreferencesPage()
    group = Adw.PreferencesGroup(title=_("help.shortcuts"))
    for msgid, keys in SHORTCUTS:
        row = Adw.ActionRow(title=_(msgid))
        label = Gtk.Label(label=keys)
        label.add_css_class("vb-kbd")
        label.set_valign(Gtk.Align.CENTER)
        row.add_suffix(label)
        set_accessible(row, f"{_(msgid)}: {keys}")
        group.add(row)
    page.add(group)
    toolbar.set_content(page)
    window.set_content(toolbar)
    window.present()
    return window
