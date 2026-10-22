"""Small accessibility helpers shared by every component."""

from __future__ import annotations

from collections.abc import Iterable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

_A11Y_ATTR = "_vbios_accessible_label"


def set_accessible(widget: Gtk.Widget, label: str, description: str | None = None) -> Gtk.Widget:
    """Give a widget an explicit accessible name and remember it for tests.

    GTK derives a button's accessible name from its label, but compound controls
    (entries inside a row, icon-only buttons) need an explicit name.  The value is
    also stored as widget data so the accessibility test can assert coverage
    without a screen reader.
    """
    if not label:
        raise ValueError("accessible label must not be empty")
    widget.update_property([Gtk.AccessibleProperty.LABEL], [label])
    if description:
        widget.update_property([Gtk.AccessibleProperty.DESCRIPTION], [description])
    setattr(widget, _A11Y_ATTR, label)
    return widget


def accessible_label(widget: Gtk.Widget) -> str | None:
    value = getattr(widget, _A11Y_ATTR, None)
    return value if isinstance(value, str) else None


_INTERACTIVE = (
    Gtk.Button,
    Gtk.Entry,
    Gtk.ToggleButton,
    Gtk.CheckButton,
    Gtk.Switch,
    Gtk.Expander,
    Gtk.TextView,
    Gtk.ListBoxRow,
)


def focusable_widgets(root: Gtk.Widget) -> list[Gtk.Widget]:
    """Depth-first focus chain of the interactive controls.

    GTK's internal ColumnView row widgets and scrolled windows are focusable
    implementation details; the accessibility contract applies to controls the
    user can operate (buttons, entries, switches, expanders, log view).
    """
    found: list[Gtk.Widget] = []

    def internal(widget: Gtk.Widget) -> bool:
        parent = widget.get_parent()
        while parent is not None:
            if type(parent).__name__ in ("MenuButton", "AdwBackButton", "WindowControls"):
                return True
            parent = parent.get_parent()
        return False

    def walk(widget: Gtk.Widget) -> None:
        if (
            isinstance(widget, _INTERACTIVE)
            and widget.get_focusable()
            and widget.get_visible()
            and not internal(widget)
        ):
            found.append(widget)
        child = widget.get_first_child()
        while child is not None:
            walk(child)
            child = child.get_next_sibling()

    walk(root)
    return found


def widget_order(root: Gtk.Widget) -> list[Gtk.Widget]:
    """Depth-first list of every widget, used to assert layout/tab order."""
    ordered: list[Gtk.Widget] = []

    def walk(widget: Gtk.Widget) -> None:
        ordered.append(widget)
        child = widget.get_first_child()
        while child is not None:
            walk(child)
            child = child.get_next_sibling()

    walk(root)
    return ordered


def tab_chain(window: Gtk.Window, limit: int = 200) -> list[Gtk.Widget]:
    """Walk the real focus chain with Tab, including GTK-internal controls."""
    chain: list[Gtk.Widget] = []
    start = getattr(window, "header", None)
    start = getattr(start, "open_button", None)
    if start is not None:
        start.grab_focus()
        window.set_focus(start)
        chain.append(start)
    for _ in range(limit):
        window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        focused = window.get_focus()
        if focused is None or (chain and focused is chain[-1]):
            break
        chain.append(focused)
    return chain


def assert_labels(widgets: Iterable[Gtk.Widget]) -> list[str]:
    missing: list[str] = []
    for widget in widgets:
        if not accessible_label(widget):
            missing.append(type(widget).__name__)
    return missing
