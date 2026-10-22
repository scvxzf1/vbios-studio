"""Search and the three independent filter switches."""

from __future__ import annotations

from vbios_studio.ui.controller import UiController


def test_query_is_case_insensitive_for_key_and_label(controller: UiController) -> None:
    controller.set_filter(query="POWER")
    keys = {field.key for field in controller.filtered_fields}
    assert "power_min_w" in keys
    assert len(controller.filtered_fields) == len(keys)
    assert all(
        "power" in field.key.casefold() or "power" in field.label.casefold()
        for field in controller.filtered_fields
    )


def test_only_modified_filter_and_count(controller: UiController) -> None:
    controller.set_value("power_min_w", "120")
    controller.set_value("gpc_offset_max_mhz", "250")
    controller.toggle_filter("only_modified", True)
    filtered = controller.filtered_fields
    assert {field.key for field in filtered} == {"power_min_w", "gpc_offset_max_mhz"}
    assert len(filtered) == controller.change_count


def test_only_t3_filter(controller: UiController) -> None:
    controller.set_experimental_unlocked(True)
    controller.toggle_filter("only_t3", True)
    assert controller.filtered_fields
    assert all(field.risk == "T3" for field in controller.filtered_fields)
    assert len(controller.filtered_fields) == len(
        [f for f in controller.visible_fields if f.risk == "T3"]
    )


def test_only_current_section_filter(controller: UiController) -> None:
    controller.set_section("power")
    controller.toggle_filter("only_current_section", True)
    assert controller.filtered_fields
    assert all(field.section == "power" for field in controller.filtered_fields)
    assert len(controller.filtered_fields) == len(controller.fields_for_section("power"))


def test_combined_filters_hit_count_equals_list_length(controller: UiController) -> None:
    controller.set_experimental_unlocked(True)
    controller.set_value("power_max_w", "300", t3_confirmed=True)
    controller.set_section("power")
    controller.toggle_filter("only_modified", True)
    controller.toggle_filter("only_t3", True)
    controller.toggle_filter("only_current_section", True)
    filtered = controller.filtered_fields
    assert len(filtered) == 1
    assert filtered[0].key == "power_max_w"


def test_zero_hits_does_not_mutate_switches(controller: UiController) -> None:
    before = controller.filters
    controller.set_filter(query="zzz-no-such-field")
    assert controller.filtered_fields == []
    assert controller.filters.only_modified is before.only_modified
    assert controller.filters.only_t3 is before.only_t3
    assert controller.filters.only_current_section is before.only_current_section
