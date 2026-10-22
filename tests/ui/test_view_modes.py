"""Table and form views share the same controller state."""

from __future__ import annotations

from vbios_studio.ui.controller import UiController


def test_view_mode_switch_keeps_staged_values(controller: UiController) -> None:
    controller.set_view_mode("table")
    controller.set_value("power_min_w", "135")
    assert controller.view_mode == "table"
    controller.set_view_mode("form")
    assert controller.view_mode == "form"
    field = controller.find_field("power_min_w")
    assert field is not None
    assert controller.value_of(field) == "135"


def test_view_mode_rejects_unknown_mode(controller: UiController) -> None:
    try:
        controller.set_view_mode("grid")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown view mode must be rejected")
