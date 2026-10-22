# ruff: noqa: E402
"""Settings helpers: experimental-mode gate with an explicit risk acknowledgement."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.ui.controller import UiController
from vbios_studio.ui.dialogs.confirm_dialog import ConfirmationRules, ConfirmDialog

Translate = Callable[[str], str]


def request_experimental_unlock(
    parent: Gtk.Window,
    _: Translate,
    controller: UiController,
    on_done: Callable[[], None] | None = None,
) -> ConfirmDialog:
    def unlock() -> None:
        controller.set_experimental_unlocked(True)
        if on_done is not None:
            on_done()

    dialog = ConfirmDialog(
        parent,
        _("experimental.title"),
        _("experimental.body"),
        rules=ConfirmationRules(require_checkbox=True, required_word="ENABLE"),
        confirm_label=_("experimental.enable"),
        cancel_label=_("common.cancel"),
        checkbox_label=_("experimental.checkbox"),
        word_label=_("experimental.word"),
        on_confirm=unlock,
        width=560,
    )
    dialog.present()
    return dialog
