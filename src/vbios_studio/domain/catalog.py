"""Map vendor-neutral field descriptors to immutable UI field snapshots.

The adapter supplies plain dictionaries copied from the vendored upstream
catalog. This module owns the risk annotation, unit formatting and the
read-only fallback for canonical fields the upstream parser does not expose.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import FieldSnapshot
from .risk_registry import is_experimental, is_opt_in, is_registered, risk_for_field
from .sections import field_section

_UNIT_BY_SUFFIX = (
    ("_mhz", "MHz"),
    ("_ma", "mA"),
    ("_mv", "mV"),
    ("_uv", "uV"),
    ("_w", "W"),
    ("_pct", "%"),
    ("_rpm", "RPM"),
    ("_hz", "Hz"),
    ("_ms", "ms"),
    ("_us", "us"),
    ("_c", "C"),
)


def format_value(value: Any) -> str | None:
    """Format a catalog number without binary-float noise or trailing zeros."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "1" if value else "0"
    text = str(value)
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return text
    if not number.is_finite():
        return text
    if number == number.to_integral_value():
        return str(int(number))
    return format(number.normalize(), "f")


def _unit_for_key(key: str) -> str:
    for suffix, unit in _UNIT_BY_SUFFIX:
        if key.endswith(suffix):
            return unit
    if "follows_offset" in key:
        return "flag"
    return ""


def _description(descriptor: Mapping[str, Any]) -> str:
    parts: list[str] = []
    reason = descriptor.get("reason")
    if reason:
        parts.append(str(reason))
    evidence = descriptor.get("evidence") or ()
    kinds = sorted(
        {
            str(item.get("kind"))
            for item in evidence
            if isinstance(item, Mapping) and item.get("kind")
        }
    )
    if kinds:
        parts.append("evidence: " + ", ".join(kinds))
    return "; ".join(parts) or "No independent evidence is available."


def _offset(descriptor: Mapping[str, Any]) -> int | None:
    offsets = descriptor.get("offsets") or ()
    return int(offsets[0]) if offsets else None


def build_field_snapshot(descriptor: Mapping[str, Any], *, family: str | None) -> FieldSnapshot:
    """Build one field snapshot from an upstream descriptor dictionary."""
    key = str(descriptor["key"])
    bounds = descriptor.get("bounds") or {}
    editable = bool(descriptor.get("editable")) and is_registered(key)
    return FieldSnapshot(
        key=key,
        label=str(descriptor.get("label") or key.replace("_", " ").title()),
        section=field_section(key),
        unit=str(descriptor.get("units") or _unit_for_key(key)),
        current=format_value(descriptor.get("current")),
        default=format_value(descriptor.get("factory_default")),
        minimum=format_value(bounds.get("minimum")),
        maximum=format_value(bounds.get("maximum")),
        risk=risk_for_field(key, family=family, editable=editable),
        offset=_offset(descriptor),
        editable=editable,
        opt_in=bool(descriptor.get("opt_in")) or is_opt_in(key),
        experimental=is_experimental(key, family),
        description=_description(descriptor),
        depends_on=dict(descriptor["depends_on"]) if descriptor.get("depends_on") else None,
    )


_FAN_KEYS = ("fan_channels", "fan_pwm_frequency_hz", "fan_zero_rpm")
_ADVANCED_KEYS = (
    "perf_cf_util_policy",
    "perf_cf_gpc_target_pct",
    "perf_cf_gpc_jump_pct",
    "perf_cf_gpc_hysteresis_down",
    "perf_cf_gpc_hysteresis_up",
    "perf_cf_dram_target_pct",
    "perf_cf_dram_jump_pct",
    "perf_cf_dram_hysteresis_down",
    "perf_cf_dram_hysteresis_up",
    "perf_cf_vid_target_pct",
    "perf_cf_vid_jump_pct",
    "perf_cf_vid_hysteresis_down",
    "perf_cf_vid_hysteresis_up",
    "lpwr_gr_power_gating",
    "lpwr_mscg",
    "lpwr_nvdec_gating",
    "lpwr_nvenc_gating",
    "lpwr_ofa_gating",
    "lpwr_nvjpg_gating",
    "lpwr_difr",
    "lpwr_difr_dfpr_idle_ms",
    "lpwr_difr_sw_asr_idle_us",
    "lpwr_difr_cg_idle_us",
    "lpwr_gr_rail_gating",
    "lpwr_gr_rail_gating_idle_us",
)

_BASE_FIELD_KEYS: tuple[str, ...] = (
    "power_min_w",
    "power_default_w",
    "power_max_w",
    "board_fixed_rated_w",
    "slot_power_rated_w",
    "slot_power_max_w",
    "connector_sum_power_rated_w",
    "connector_sum_power_max_w",
    "nvvdd_power_threshold_rated_w",
    "nvvdd_power_threshold_max_w",
    "max_operating_temp_c",
    "nvvdd_rel_equation_max_mv",
    "nvvdd_rel_max_mv",
    "nvvdd_rel_fixed_mv",
    "nvvdd_alt_fixed_mv",
    "nvvdd_ov_equation_max_mv",
    "nvvdd_vmin_mv",
    "nvvdd_vmin_equation_max_mv",
    "nvvdd_alt_equation_max_mv",
    "nvvdd_rel_alt_follow_ov",
    "msvdd_rel_equation_max_mv",
    "msvdd_rel_max_mv",
    "msvdd_ov_equation_max_mv",
    "msvdd_vmin_mv",
    "msvdd_vmin_equation_max_mv",
    "msvdd_alt_equation_max_mv",
    "factory_gpc_offset_mhz",
    "factory_rated_boost_mhz",
    "gpc_curve_offset_mhz",
    "gpc_offset_max_mhz",
    "gpc_offset_min_mhz",
    "memory_offset_max_mhz",
    "memory_offset_min_mhz",
    "xbar_max_table_mhz",
    "xbar_min_table_mhz",
    "sys_max_table_mhz",
    "sys_min_table_mhz",
    "vid_max_table_mhz",
    "vid_min_table_mhz",
    "input_current_rated_ma",
    "input_current_max_ma",
    "input_current_policy7_limit_ma",
    "nvvdd_output_ocp_rated_ma",
    "nvvdd_output_ocp_max_ma",
    "msvdd_output_ocp_rated_ma",
    "msvdd_output_ocp_max_ma",
    "slot_current_threshold_rated_ma",
    "slot_current_threshold_max_ma",
    "current_limit_a",
    "ocp_limit_a",
    "input_policy_9_max_raw",
)

CANONICAL_FIELD_KEYS: tuple[str, ...] = (
    *_BASE_FIELD_KEYS,
    *(
        f"connector_{n}_{kind}_{side}"
        for n in range(1, 5)
        for kind, side in (
            ("power", "rated_w"),
            ("power", "max_w"),
            ("current_threshold", "rated_ma"),
            ("current_threshold", "max_ma"),
        )
    ),
    *_FAN_KEYS,
    *(f"memory_point_{n}_follows_offset" for n in range(1, 8)),
    *_ADVANCED_KEYS,
)


def placeholder_snapshot(key: str, *, family: str | None) -> FieldSnapshot:
    """Build a T0 read-only fallback for a canonical field upstream does not expose."""
    return FieldSnapshot(
        key=key,
        label=key.replace("_", " ").title(),
        section=field_section(key),
        unit=_unit_for_key(key),
        current=None,
        default=None,
        minimum=None,
        maximum=None,
        risk="T0",
        offset=None,
        editable=False,
        opt_in=is_opt_in(key),
        experimental=is_experimental(key, family),
        description=(
            "This field is part of the frozen catalog but the vendored upstream parser "
            "did not expose it for this image; shown read-only."
        ),
        depends_on=None,
    )


def build_field_snapshots(
    descriptors: Iterable[Mapping[str, Any]],
    *,
    family: str | None,
    include_placeholders: bool = True,
) -> tuple[FieldSnapshot, ...]:
    """Build the catalog, appending read-only placeholders for missing keys."""
    fields = [build_field_snapshot(descriptor, family=family) for descriptor in descriptors]
    if not include_placeholders:
        return tuple(fields)
    seen = {field.key for field in fields}
    fields.extend(
        placeholder_snapshot(key, family=family) for key in CANONICAL_FIELD_KEYS if key not in seen
    )
    return tuple(fields)
