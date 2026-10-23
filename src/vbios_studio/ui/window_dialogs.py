# ruff: noqa: E402
"""File dialogs and profile/diff/save flows for the main window."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from vbios_studio.domain.errors import DomainError
from vbios_studio.i18n import gettext as _
from vbios_studio.ui import profile_io

if TYPE_CHECKING:
    from vbios_studio.ui.main_window import MainWindow


class WindowDialogs:
    def __init__(self, window: MainWindow) -> None:
        self.window = window

    def _file_dialog(self, title: str) -> Gtk.FileDialog:
        dialog = Gtk.FileDialog()
        dialog.set_title(title)
        filters = Gio.ListStore(item_type=Gtk.FileFilter)
        every = Gtk.FileFilter()
        every.set_name(_("dialog.filter.all"))
        every.add_pattern("*")
        rom = Gtk.FileFilter()
        rom.set_name(_("dialog.filter.rom"))
        rom.add_pattern("*.rom")
        rom.add_pattern("*.bin")
        filters.append(rom)
        filters.append(every)
        dialog.set_filters(filters)
        return dialog

    def open_dialog(self) -> None:
        dialog = self._file_dialog(_("dialog.open.title"))
        dialog.open(self.window, None, self._open_finished)

    def _open_finished(self, dialog: Gtk.FileDialog, result: Any) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        if file.get_path():
            self.open_path(Path(file.get_path()))

    def open_path(self, path: Path) -> None:
        try:
            self.window.controller.open_path(path)
        except DomainError as exc:
            self.window._show_error(_("open.error.title"), exc)
        except Exception as exc:
            self.window._show_error(_("open.error.title"), exc)

    def save_dialog(self) -> None:
        if self.window.controller.snapshot is None:
            return
        dialog = self._file_dialog(_("dialog.save.title"))
        stem = Path(self.window.controller.snapshot.display_name).stem
        dialog.set_initial_name(f"{stem}-modified.rom")
        dialog.save(self.window, None, self._save_finished)

    def _save_finished(self, dialog: Gtk.FileDialog, result: Any) -> None:
        try:
            file = dialog.save_finish(result)
        except GLib.Error:
            return
        if not file.get_path():
            return
        try:
            saved = self.window.controller.save_as(Path(file.get_path()))
        except DomainError as exc:
            self.window._show_error(_("save.error.title"), exc)
            return
        warning = Adw.AlertDialog(heading=_("save.warning.title"), body=_("save.warning.body"))
        warning.add_response("close", _("common.close"))
        warning.present(self)
        self.window._toast(_("save.success").format(path=str(saved.path)))

    def save_profile_dialog(self) -> None:
        if self.window.controller.snapshot is None:
            return
        dialog = Gtk.FileDialog()
        dialog.set_title(_("profile.save"))
        dialog.set_initial_name("vbios-studio-preset.json")
        dialog.save(self.window, None, self._save_profile_finished)

    def _save_profile_finished(self, dialog: Gtk.FileDialog, result: Any) -> None:
        try:
            file = dialog.save_finish(result)
        except GLib.Error:
            return
        if not file.get_path():
            return
        try:
            data = self.window.controller.export_profile()
            profile_io.write_profile(Path(file.get_path()), data)
        except (DomainError, OSError, ValueError) as exc:
            self.window._show_error(_("profile.error.title"), exc)
            return
        self.window._toast(_("profile.saved"))

    def load_profile_dialog(self) -> None:
        if self.window.controller.snapshot is None:
            return
        dialog = self._file_dialog(_("profile.load"))
        dialog.open(self.window, None, self._load_profile_finished)

    def _load_profile_finished(self, dialog: Gtk.FileDialog, result: Any) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        if not file.get_path():
            return
        try:
            data = profile_io.read_profile(Path(file.get_path()))
        except (DomainError, OSError, ValueError) as exc:
            self.window._show_error(_("profile.error.title"), exc)
            return
        self.window.profile_flow.apply_document(data)

    def choose_diff_dialog(self) -> None:
        if self.window.controller.snapshot is None:
            return
        dialog = self._file_dialog(_("diff.choose"))
        dialog.open(self.window, None, self._diff_finished)

    def _diff_finished(self, dialog: Gtk.FileDialog, result: Any) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        if not file.get_path():
            return
        try:
            diff = self.window.controller.compare(Path(file.get_path()))
        except DomainError as exc:
            self.window._show_error(_("diff.error.title"), exc)
            return
        self.window.navigate("diff")
        self.window.diff_view.show_rom_diff(diff)
        self.window._refresh_all()
