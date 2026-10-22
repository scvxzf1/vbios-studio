# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Bottom status bar: file, architecture, unsaved changes and checksum state."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.field_text import architecture_label

Translate = Callable[[str], str]


class StatusBar(Gtk.Box):
    def __init__(self, _: Translate, controller: UiController) -> None:
        super().__init__(spacing=12)
        self._ = _
        self.controller = controller
        self.add_css_class("vb-statusbar")
        self.file_label = self._segment("")
        self.arch_label = self._segment("")
        self.unsaved_label = self._segment("")
        self.checksum_label = self._segment("")
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.append(spacer)
        self.log_toggle = Gtk.ToggleButton(label=_("log.show"))
        self.log_toggle.set_tooltip_text(_("log.toggle_tooltip"))
        set_accessible(self.log_toggle, _("log.show"))
        self.append(self.log_toggle)
        self.refresh()

    def _segment(self, text: str) -> Gtk.Label:
        if self.get_first_child() is not None:
            self.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        label = Gtk.Label(label=text, xalign=0)
        label.add_css_class("vb-dim")
        set_accessible(label, text or "status")
        self.append(label)
        return label

    def refresh(self) -> None:
        _ = self._
        snap = self.controller.snapshot
        if snap is None:
            self.file_label.set_text(_("status.no_file"))
            self.arch_label.set_text(_("status.no_architecture"))
            self.unsaved_label.set_text(_("status.no_changes"))
            self.checksum_label.set_text(_("status.no_document"))
            return
        self.file_label.set_text(snap.display_name)
        self.file_label.remove_css_class("vb-dim")
        self.file_label.add_css_class("vb-section-title")
        self.arch_label.set_text(architecture_label(snap.architecture))
        count = self.controller.change_count
        self.unsaved_label.set_text(
            _("status.unsaved_one").format(count=count)
            if count == 1
            else _("status.unsaved").format(count=count)
        )
        if count:
            self.unsaved_label.remove_css_class("vb-dim")
            self.unsaved_label.add_css_class("vb-warning-text")
        else:
            self.unsaved_label.add_css_class("vb-dim")
            self.unsaved_label.remove_css_class("vb-warning-text")
        if self.controller.all_checksums_ok:
            self.checksum_label.set_text(_("status.checksums_ok"))
            self.checksum_label.remove_css_class("vb-bad")
            self.checksum_label.add_css_class("vb-ok")
        else:
            self.checksum_label.set_text(_("status.checksums_bad"))
            self.checksum_label.remove_css_class("vb-ok")
            self.checksum_label.add_css_class("vb-bad")
        for label, text in (
            (self.file_label, _("status.file")),
            (self.arch_label, _("status.architecture")),
            (self.unsaved_label, _("status.unsaved")),
            (self.checksum_label, _("status.checksums")),
        ):
            set_accessible(label, f"{text}: {label.get_text()}")

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.log_toggle.set_label(_("log.show"))
        set_accessible(self.log_toggle, _("log.show"))
        self.refresh()
