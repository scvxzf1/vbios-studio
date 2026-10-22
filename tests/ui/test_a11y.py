# ruff: noqa: E402
"""Accessibility: every operable control has a label and Tab order is sensible."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from tests.ui.support import pump_events
from vbios_studio.ui.a11y import accessible_label, focusable_widgets, tab_chain, widget_order
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.main_window import MainWindow


def test_every_operable_control_has_accessible_label(
    gtk_initialised, controller: UiController
) -> None:
    window = MainWindow(None, controller)
    window.present()
    pump_events(8)
    widgets = focusable_widgets(window)
    assert widgets
    missing = [type(widget).__name__ for widget in widgets if not accessible_label(widget)]
    assert not missing, f"missing accessible labels: {missing}"
    window.destroy()


def test_tab_order_toolbar_navigation_fields_log(gtk_initialised, controller: UiController) -> None:
    window = MainWindow(None, controller)
    window.present()
    pump_events(8)
    chain = tab_chain(window)
    open_index = chain.index(window.header.open_button)
    nav_index = chain.index(window.sidebar.rows["info"])
    assert open_index < nav_index
    order = widget_order(window)
    assert (
        order.index(window.sidebar)
        < order.index(window.field_table)
        < order.index(window.log_panel)
    )
    window.destroy()
