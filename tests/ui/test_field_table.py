"""Table structure and numeric typography (monospace, right aligned)."""

from __future__ import annotations

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.field_table import FieldTable, make_value_entry
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.field_text import format_numeric


def test_value_editor_is_monospace_and_right_aligned(gtk_initialised) -> None:
    entry = make_value_entry()
    assert entry.has_css_class("vb-num")
    assert entry.get_alignment() == 1.0


def test_table_has_the_seven_frozen_columns(gtk_initialised, controller: UiController) -> None:
    table = FieldTable(_, controller, lambda _key, _value: None)
    titles = [column.get_title() for column in table.view.get_columns()]
    assert titles == ["Field", "Current", "Unit", "Range", "Default", "Risk", "Offset"]
    assert len(table.store) == len(controller.filtered_fields)


def test_table_refresh_tracks_filters(gtk_initialised, controller: UiController) -> None:
    table = FieldTable(_, controller, lambda _key, _value: None)
    controller.set_filter(query="power")
    table.refresh()
    assert len(table.store) == len(controller.filtered_fields)
    assert len(table.store) < len(controller.visible_fields)


def test_table_and_form_share_staged_values(gtk_initialised, controller: UiController) -> None:
    controller.set_value("power_min_w", "130")
    table = FieldTable(_, controller, lambda _key, _value: None)
    table.refresh()
    row = next(
        table.store.get_item(index)
        for index in range(len(table.store))
        if table.store.get_item(index).field.key == "power_min_w"
    )
    assert row.value == "130"


def test_large_numeric_bounds_are_compacted_for_display() -> None:
    assert format_numeric("2147483.647") == "2.15M"
    assert format_numeric("1200") == "1200"
    assert format_numeric(None) == "—"
