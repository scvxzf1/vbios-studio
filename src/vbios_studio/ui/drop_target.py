# ruff: noqa: E402
"""Drag-and-drop target: accepts exactly one local ROM file."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, Gtk

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.drop_rules import DropError, validate_drop


def install_drop_target(
    widget: Gtk.Widget,
    on_path: Callable[[Path], None],
    on_error: Callable[[str, Exception], None],
) -> Gtk.DropTarget:
    """Install a window-wide ``Gdk.FileList`` drop target."""
    target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)

    def dropped(_target: Gtk.DropTarget, value: Any, _x: float, _y: float) -> bool:
        try:
            files = value.get_files()
        except AttributeError:
            files = []
        paths: list[Path] = []
        directories: list[bool] = []
        for file in files:
            path = file.get_path()
            if path is None:
                continue
            paths.append(Path(path))
            directories.append(
                file.query_file_type(Gio.FileQueryInfoFlags.NONE, None) == Gio.FileType.DIRECTORY
            )
        try:
            path = validate_drop(paths, is_directory=directories)
        except DropError as exc:
            on_error(_("drop.error.title"), exc)
            return True
        on_path(path)
        return True

    target.connect("drop", dropped)
    widget.add_controller(target)
    return target
