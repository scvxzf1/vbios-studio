"""Risk registry and catalog-annotation tests."""

from __future__ import annotations

from pathlib import Path

from rom_fixtures import synthetic_rom

from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.catalog import format_value
from vbios_studio.domain.risk_registry import (
    classify_change,
    is_experimental,
    is_registered,
    risk_for_field,
)


def test_direction_aware_levels_follow_the_frozen_model() -> None:
    """Raising power stays T3 while lowering it is the documented T1 direction."""
    assert risk_for_field("power_min_w") == "T1"
    assert risk_for_field("power_max_w") == "T3"
    assert classify_change("power_max_w", 70, 100) == "T3"
    assert classify_change("power_max_w", 70, 60) == "T1"
    assert classify_change("nvvdd_rel_max_mv", 1000, 900) == "T3"
    assert classify_change("nvvdd_rel_max_mv", 1000, 1100) == "T3"
    assert classify_change("input_current_rated_ma", 30000, 25000) == "T2"
    assert classify_change("input_current_rated_ma", 30000, 32000) == "T3"
    assert classify_change("power_max_w", 70, 70) == "T0"


def test_fan_directions_and_ampere_family_bump() -> None:
    """Fan limits are T2 base with safer directions; Ampere bumps T1/T2 one step."""
    assert classify_change("fan_1_curve_1_temp_c", 70, 60) == "T1"
    assert classify_change("fan_1_curve_1_temp_c", 70, 80) == "T2"
    assert classify_change("fan_1_max_rpm", 2000, 2500) == "T1"
    assert classify_change("fan_1_max_rpm", 2000, 1500) == "T2"
    assert classify_change("power_min_w", 30, 25, family="ampere") == "T2"
    assert classify_change("fan_1_curve_1_temp_c", 70, 80, family="turing") == "T3"
    assert classify_change("power_max_w", 70, 80, family="ampere") == "T3"


def test_unknown_fields_are_t0_and_read_only() -> None:
    """A key outside the frozen registry never appears as editable."""
    assert is_registered("power_max_w") is True
    assert is_registered("made_up_field") is False
    assert risk_for_field("made_up_field") == "T0"
    assert risk_for_field("power_max_w", editable=False) == "T0"
    assert classify_change("made_up_field", 1, 2) == "T0"
    assert is_experimental("fan_channels") is True


def test_catalog_annotation_and_read_only_placeholder(tmp_path: Path) -> None:
    """The catalog carries risk/experimental flags and T0 fallbacks for missing keys."""
    source = tmp_path / "ada.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    fields = {field.key: field for field in document.fields}
    assert fields["power_max_w"].editable is True
    assert fields["power_max_w"].risk == "T3"
    assert fields["power_max_w"].experimental is True
    assert fields["msvdd_rel_max_mv"].editable is False
    assert fields["msvdd_rel_max_mv"].risk == "T0"
    placeholder = fields["connector_1_power_rated_w"]
    assert placeholder.current is None
    assert placeholder.editable is False
    assert placeholder.risk == "T0"
    assert "read-only" in placeholder.description.lower()
    assert format_value("70.0") == "70"
    assert format_value("125.9830") == "125.983"
