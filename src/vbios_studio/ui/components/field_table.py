# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Dense, sortable table view of the field catalogue."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GObject, Gtk

from vbios_studio.domain.models import FieldSnapshot
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.components.risk_badge import ExperimentalBadge, RiskBadge
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.field_text import field_label, format_numeric

Translate = Callable[[str], str]


def make_value_entry() -> Gtk.Entry:
    """Create the monospaced, right-aligned editor used by the value column."""
    entry = Gtk.Entry()
    entry.set_alignment(1.0)
    entry.set_width_chars(10)
    entry.add_css_class("vb-num")
    entry.set_margin_top(4)
    entry.set_margin_bottom(4)
    return entry


class FieldRowItem(GObject.Object):
    __gtype_name__ = "VbiosFieldRowItem"

    def __init__(self, field: FieldSnapshot, value: str | None, modified: bool) -> None:
        super().__init__()
        self.field = field
        self.value = value
        self.modified = modified


class FieldTable(Gtk.Box):
    """A Gtk.ColumnView with the seven frozen columns from GUI-03."""

    def __init__(
        self, _: Translate, controller: UiController, on_commit: Callable[[str, str], None]
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._ = _
        self.controller = controller
        self.on_commit = on_commit
        self.store = Gio.ListStore(item_type=FieldRowItem)
        self.view = Gtk.ColumnView.new(Gtk.NoSelection(model=self.store))
        self.view.set_show_column_separators(True)
        self.view.set_show_row_separators(True)
        self.view.add_css_class("vb-field-table")
        self.view.set_vexpand(True)
        self._build_columns()
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(self.view)
        scroller.set_vexpand(True)
        self.append(scroller)
        self.refresh()

    # -- columns -----------------------------------------------------------
    def _text_column(
        self,
        title: str,
        kind: str,
        *,
        width: int = -1,
        css: tuple[str, ...] = (),
        xalign: float = 0.0,
        sort_key: str = "",
    ) -> None:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_text_cell, css, xalign)
        factory.connect("bind", self._bind_text_cell, kind)
        column = Gtk.ColumnViewColumn(title=title, factory=factory)
        if width > 0:
            column.set_fixed_width(width)
        column.set_resizable(True)
        column.set_expand(kind == "label")
        column.set_sorter(self._sorter(sort_key or kind))
        self.view.append_column(column)

    def _setup_text_cell(
        self,
        _factory: Gtk.SignalListItemFactory,
        item: Gtk.ListItem,
        css: tuple[str, ...],
        xalign: float,
    ) -> None:
        label = Gtk.Label(xalign=xalign)
        label.set_ellipsize(3)
        for name in css:
            label.add_css_class(name)
        item.set_child(label)

    def _bind_text_cell(
        self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem, kind: str
    ) -> None:
        row: FieldRowItem = item.get_item()
        label: Gtk.Label = item.get_child()
        field = row.field
        if kind == "unit":
            text = field.unit
        elif kind == "range":
            if field.minimum is None and field.maximum is None:
                text = "—"
            else:
                minimum = format_numeric(field.minimum)
                maximum = format_numeric(field.maximum)
                text = f"{minimum} – {maximum}"
        elif kind == "default":
            text = format_numeric(field.default)
        elif kind == "offset":
            text = f"0x{field.offset:04X}" if field.offset is not None else "—"
        elif kind == "value":
            text = row.value if row.value is not None else self._("fields.not_available")
        else:
            text = ""
        label.set_text(text)
        if kind == "offset":
            set_accessible(
                label, f"{field_label(field, self._)}: {self._('fields.column.offset')} {text}"
            )

    def _build_columns(self) -> None:
        _ = self._
        # Field column: two-line cell with the localised label, stable key and badges.
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_field_cell)
        factory.connect("bind", self._bind_field_cell)
        column = Gtk.ColumnViewColumn(title=_("fields.column.field"), factory=factory)
        column.set_fixed_width(300)
        column.set_resizable(True)
        column.set_sorter(self._sorter("label"))
        self.view.append_column(column)

        # Current value: editable entry.
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_value_cell)
        factory.connect("bind", self._bind_value_cell)
        column = Gtk.ColumnViewColumn(title=_("fields.column.current"), factory=factory)
        column.set_fixed_width(120)
        column.set_resizable(True)
        column.set_sorter(self._sorter("value"))
        self.view.append_column(column)

        self._text_column(
            _("fields.column.unit"), "unit", width=60, css=("vb-dim",), sort_key="unit"
        )
        self._text_column(
            _("fields.column.range"),
            "range",
            width=150,
            css=("vb-num",),
            xalign=1.0,
            sort_key="range",
        )
        self._text_column(
            _("fields.column.default"),
            "default",
            width=95,
            css=("vb-num",),
            xalign=1.0,
            sort_key="default",
        )
        self.view.append_column(self._risk_column())
        self._text_column(
            _("fields.column.offset"),
            "offset",
            width=95,
            css=("vb-num",),
            xalign=1.0,
            sort_key="offset",
        )

    def _risk_column(self) -> Gtk.ColumnViewColumn:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_risk_cell)
        factory.connect("bind", self._bind_risk_cell)
        column = Gtk.ColumnViewColumn(title=self._("fields.column.risk"), factory=factory)
        column.set_fixed_width(125)
        column.set_resizable(True)
        column.set_sorter(self._sorter("risk"))
        return column

    def _setup_field_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        title_row = Gtk.Box(spacing=6)
        label = Gtk.Label(xalign=0)
        label.set_ellipsize(3)
        title_row.append(label)
        meta_row = Gtk.Box(spacing=6)
        key = Gtk.Label(xalign=0)
        key.add_css_class("vb-mono")
        key.add_css_class("vb-dim")
        meta_row.append(key)
        badges = Gtk.Box(spacing=4)
        meta_row.append(badges)
        box.append(title_row)
        box.append(meta_row)
        item.set_child(box)

    def _bind_field_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        row: FieldRowItem = item.get_item()
        box: Gtk.Box = item.get_child()
        title_row: Gtk.Box = box.get_first_child()
        label: Gtk.Label = title_row.get_first_child()
        meta_row: Gtk.Box = box.get_last_child()
        key: Gtk.Label = meta_row.get_first_child()
        badges: Gtk.Box = meta_row.get_last_child()
        label.set_text(field_label(row.field, self._))
        key.set_text(row.field.key + ("  •  " + self._("fields.modified") if row.modified else ""))
        while (child := badges.get_first_child()) is not None:
            badges.remove(child)
        if row.field.experimental:
            badges.append(ExperimentalBadge(self._))

    def _setup_risk_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        box = Gtk.Box(spacing=4)
        box.set_valign(Gtk.Align.CENTER)
        item.set_child(box)

    def _bind_risk_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        row: FieldRowItem = item.get_item()
        box: Gtk.Box = item.get_child()
        while (child := box.get_first_child()) is not None:
            box.remove(child)
        box.append(RiskBadge(row.field.risk, self._))

    def _setup_value_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        entry = make_value_entry()
        focus = Gtk.EventControllerFocus()
        focus.connect("leave", self._commit_entry)
        entry.add_controller(focus)
        entry.connect("activate", self._commit_entry)
        item.set_child(entry)

    def _commit_entry(self, entry: Gtk.Entry) -> None:
        key = getattr(entry, "_vbios_field_key", None)
        if key:
            self.on_commit(key, entry.get_text())

    def _bind_value_cell(self, _factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        row: FieldRowItem = item.get_item()
        entry: Gtk.Entry = item.get_child()
        entry._vbios_field_key = row.field.key
        entry.set_text(row.value or "")
        entry.set_editable(row.field.editable)
        entry.set_sensitive(row.field.editable)
        set_accessible(
            entry, f"{field_label(row.field, self._)}: {self._('fields.column.current')}"
        )

    def _sorter(self, kind: str) -> Gtk.CustomSorter:
        def compare(a: FieldRowItem, b: FieldRowItem) -> int:
            left, right = a.field, b.field
            if kind == "label":
                ltext, rtext = (
                    field_label(left, self._).casefold(),
                    field_label(right, self._).casefold(),
                )
                return (ltext > rtext) - (ltext < rtext)
            if kind == "value":
                return int(self._numeric(a.value) - self._numeric(b.value))
            if kind == "unit":
                return (left.unit > right.unit) - (left.unit < right.unit)
            if kind == "range":
                return int(self._numeric(left.minimum) - self._numeric(b.minimum))
            if kind == "default":
                return int(self._numeric(left.default) - self._numeric(b.default))
            if kind == "risk":
                order = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
                return order.get(left.risk, 0) - order.get(right.risk, 0)
            if kind == "offset":
                return (left.offset if left.offset is not None else -1) - (
                    right.offset if right.offset is not None else -1
                )
            return 0

        return Gtk.CustomSorter.new(compare)

    @staticmethod
    def _numeric(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("-inf")

    def refresh(self) -> None:
        self.store.remove_all()
        for field in self.controller.filtered_fields:
            self.store.append(
                FieldRowItem(
                    field, self.controller.value_of(field), self.controller.is_modified(field.key)
                )
            )

    def retranslate(self, _: Translate) -> None:
        self._ = _
        titles = (
            "fields.column.field",
            "fields.column.current",
            "fields.column.unit",
            "fields.column.range",
            "fields.column.default",
            "fields.column.risk",
            "fields.column.offset",
        )
        for column, msgid in zip(self.view.get_columns(), titles, strict=True):
            column.set_title(_(msgid))
        self.refresh()
