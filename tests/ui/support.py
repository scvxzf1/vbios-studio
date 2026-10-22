"""Small helpers shared by GTK tests."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib  # noqa: E402


def pump_events(times: int = 5) -> None:
    """Iterate the GLib main context until pending layout work is done."""
    context = GLib.MainContext.default()
    for _ in range(times):
        while context.pending():
            context.iteration(False)
