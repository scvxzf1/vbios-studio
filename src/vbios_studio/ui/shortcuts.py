"""Keyboard accelerators shared by the main window."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

Action = Callable[[], None]


def install_shortcuts(window: Gtk.Widget, mapping: dict[str, Action]) -> Gtk.ShortcutController:
    """Attach accelerators (Ctrl+O, Ctrl+Z, ...) to a window."""
    controller = Gtk.ShortcutController()
    for accelerator, callback in mapping.items():
        trigger = Gtk.ShortcutTrigger.parse_string(accelerator)
        action = Gtk.CallbackAction.new(lambda _widget, _args, cb=callback: (cb(), True)[1])
        controller.add_shortcut(Gtk.Shortcut.new(trigger, action))
    window.add_controller(controller)
    return controller
