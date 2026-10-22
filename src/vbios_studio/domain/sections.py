"""Section identifiers and ordering shared by catalogs and the GTK views."""

from __future__ import annotations

from collections.abc import Iterable

from .models import SectionSnapshot

SECTION_ORDER: tuple[tuple[str, str, int], ...] = (
    ("info", "File information", 0),
    ("power", "Power", 1),
    ("voltage", "Voltage", 2),
    ("current", "Current", 3),
    ("clocks", "Clocks", 4),
    ("fans", "Fans", 5),
    ("memory", "Memory", 6),
    ("advanced", "Advanced", 7),
    ("other", "Other", 8),
    ("apply", "Apply", 9),
    ("log", "Log", 10),
)

_POWER_KEYS = frozenset(
    {
        "power_min_w",
        "power_default_w",
        "power_max_w",
        "board_fixed_rated_w",
        "slot_power_max_w",
        "slot_power_rated_w",
        "connector_sum_power_max_w",
        "connector_sum_power_rated_w",
        "nvvdd_power_threshold_max_w",
        "nvvdd_power_threshold_rated_w",
        "max_operating_temp_c",
    }
)
_CURRENT_KEYS = frozenset(
    {
        "current_limit_a",
        "ocp_limit_a",
        "input_policy_9_max_raw",
        "input_current_rated_ma",
        "input_current_max_ma",
        "input_current_policy7_limit_ma",
    }
)
_MEMORY_KEYS = frozenset({"memory_offset_max_mhz", "memory_offset_min_mhz"})


def field_section(key: str) -> str:
    """Return the stable section id for a field key.

    Unknown keys fall back by unit suffix, then to ``other`` so the UI can show
    them without inventing a section.
    """
    if key.startswith(("perf_cf_", "lpwr_")):
        return "advanced"
    if key.startswith("fan_"):
        return "fans"
    if key in _POWER_KEYS:
        return "power"
    if key in _CURRENT_KEYS:
        return "current"
    if key in _MEMORY_KEYS:
        return "memory"
    if key.endswith("_mv") or key in {"nvvdd_rel_alt_follow_ov"} or "selector_index" in key:
        return "voltage"
    if key.endswith("_ma") or key.endswith("_a") or "current_threshold" in key:
        return "current"
    if key.endswith("_mhz") or key.endswith("_follows_offset"):
        return "clocks"
    if key.endswith("_w"):
        return "power"
    return "other"


def section_snapshots(keys: Iterable[str]) -> tuple[SectionSnapshot, ...]:
    """Return ordered sections, always including ``info``."""
    present = {"info"} | {field_section(key) for key in keys}
    return tuple(
        SectionSnapshot(id=section, title=title, order=order)
        for section, title, order in SECTION_ORDER
        if section in present
    )
