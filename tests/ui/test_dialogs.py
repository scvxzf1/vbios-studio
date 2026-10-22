"""Empty state, copyable error dialog and the keyboard-shortcut table."""

from __future__ import annotations

from tests.ui.support import pump_events
from vbios_studio.domain.errors import DomainError
from vbios_studio.i18n import gettext as _
from vbios_studio.ui.a11y import widget_order
from vbios_studio.ui.components.empty_state import EmptyState
from vbios_studio.ui.dialogs.error_dialog import ErrorDialog
from vbios_studio.ui.dialogs.shortcuts_dialog import SHORTCUTS, show_shortcuts
from vbios_studio.ui.main_window import MainWindow


def test_empty_state_has_drag_drop_guidance_and_support_matrix(gtk_initialised) -> None:
    opened = []
    state = EmptyState(_, lambda: opened.append(True))
    texts = [widget.get_text() for widget in widget_order(state) if hasattr(widget, "get_text")]
    assert "Drop a VBIOS file here" in texts
    assert "Blackwell GB20x" in texts
    assert "Turing TU10x/TU11x" in texts
    button = next(
        widget
        for widget in widget_order(state)
        if hasattr(widget, "get_label") and widget.get_label() == "Open a file…"
    )
    button.emit("clicked")
    assert opened == [True]


def test_error_dialog_details_are_copyable(gtk_initialised) -> None:
    error = DomainError("ROM_INVALID", "Not a VBIOS ROM.", "Choose a .rom file.")
    dialog = ErrorDialog.from_exception(None, _("open.error.title"), error, _)
    assert "[ROM_INVALID] Not a VBIOS ROM." in dialog.details_text
    assert "Choose a .rom file." in dialog.details_text
    assert dialog.details_text
    dialog.destroy()


def test_shortcut_table_lists_every_binding(gtk_initialised, controller) -> None:
    window = MainWindow(None, controller)
    window.present()
    pump_events(4)
    dialog = show_shortcuts(window, _)
    pump_events(4)
    rows = [widget for widget in widget_order(dialog) if hasattr(widget, "get_title")]
    titles = [row.get_title() for row in rows if row.get_title()]
    assert len(titles) >= len(SHORTCUTS)
    assert any(
        "Ctrl+O" in str(widget.get_label())
        for widget in widget_order(dialog)
        if hasattr(widget, "get_label")
    )
    dialog.destroy()
    window.destroy()
