"""Localised labels for field keys and sections.

The domain snapshot carries a stable field key plus an English fallback label.  This
module maps the key to a gettext msgid so the same key can be rendered in every
configured language, including parameterised fan/connector/rail fields.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from vbios_studio.domain.models import FieldSnapshot

Translate = Callable[[str], str]

SECTION_ORDER: tuple[str, ...] = (
    "info",
    "power",
    "voltage",
    "current",
    "clocks",
    "fans",
    "memory",
    "advanced",
    "apply",
    "log",
)
SECTION_ICONS: dict[str, str] = {
    "info": "view-grid-symbolic",
    "power": "power-symbolic",
    "voltage": "battery-symbolic",
    "current": "flash-symbolic",
    "clocks": "alarm-symbolic",
    "fans": "fan-symbolic",
    "memory": "drive-harddisk-symbolic",
    "advanced": "applications-system-symbolic",
    "apply": "document-send-symbolic",
    "log": "utilities-terminal-symbolic",
}
SECTION_MSGIDS: dict[str, str] = {
    "info": "section.info",
    "power": "section.power",
    "voltage": "section.voltage",
    "current": "section.current",
    "clocks": "section.clocks",
    "fans": "section.fans",
    "memory": "section.memory",
    "advanced": "section.advanced",
    "apply": "section.apply",
    "log": "section.log",
}

_EXACT: dict[str, str] = {
    "power_min_w": "field.power_min_w",
    "power_max_w": "field.power_max_w",
    "power_default_w": "field.power_default_w",
    "board_fixed_rated_w": "field.board_fixed_rated_w",
    "slot_power_rated_w": "field.slot_power_rated_w",
    "slot_power_max_w": "field.slot_power_max_w",
    "connector_sum_power_rated_w": "field.connector_sum_power_rated_w",
    "connector_sum_power_max_w": "field.connector_sum_power_max_w",
    "nvvdd_power_threshold_rated_w": "field.nvvdd_power_threshold_rated_w",
    "nvvdd_power_threshold_max_w": "field.nvvdd_power_threshold_max_w",
    "max_operating_temp_c": "field.max_operating_temp_c",
    "nvvdd_rel_max_mv": "field.nvvdd_rel_max_mv",
    "msvdd_rel_max_mv": "field.msvdd_rel_max_mv",
    "nvvdd_rel_alt_follow_ov": "field.nvvdd_rel_alt_follow_ov",
    "input_current_rated_ma": "field.input_current_rated_ma",
    "input_current_max_ma": "field.input_current_max_ma",
    "input_current_policy7_limit_ma": "field.input_current_policy7_limit_ma",
    "current_limit_a": "field.current_limit_a",
    "ocp_limit_a": "field.ocp_limit_a",
    "slot_current_threshold_rated_ma": "field.slot_current_threshold_rated_ma",
    "slot_current_threshold_max_ma": "field.slot_current_threshold_max_ma",
    "fan_channels": "field.fan_channels",
    "fan_pwm_frequency_hz": "field.fan_pwm_frequency_hz",
    "fan_zero_rpm": "field.fan_zero_rpm",
    "gpc_offset_min_mhz": "field.gpc_offset_min_mhz",
    "gpc_offset_max_mhz": "field.gpc_offset_max_mhz",
    "memory_offset_min_mhz": "field.memory_offset_min_mhz",
    "memory_offset_max_mhz": "field.memory_offset_max_mhz",
    "dram_min_table_mhz": "field.dram_min_table_mhz",
    "dram_max_table_mhz": "field.dram_max_table_mhz",
    "gpc_curve_offset_mhz": "field.gpc_curve_offset_mhz",
    "factory_gpc_offset_mhz": "field.factory_gpc_offset_mhz",
    "factory_rated_boost_mhz": "field.factory_rated_boost_mhz",
    "perf_cf_util_policy": "field.perf_cf_util_policy",
    "lpwr_gr_power_gating": "field.lpwr_gr_power_gating",
    "lpwr_mscg": "field.lpwr_mscg",
    "lpwr_nvdec_gating": "field.lpwr_nvdec_gating",
    "lpwr_nvenc_gating": "field.lpwr_nvenc_gating",
    "lpwr_ofa_gating": "field.lpwr_ofa_gating",
    "lpwr_nvjpg_gating": "field.lpwr_nvjpg_gating",
    "lpwr_difr": "field.lpwr_difr",
    "lpwr_difr_dfpr_idle_ms": "field.lpwr_difr_dfpr_idle_ms",
    "lpwr_difr_sw_asr_idle_us": "field.lpwr_difr_sw_asr_idle_us",
    "lpwr_difr_cg_idle_us": "field.lpwr_difr_cg_idle_us",
    "lpwr_gr_rail_gating": "field.lpwr_gr_rail_gating",
    "lpwr_gr_rail_gating_idle_us": "field.lpwr_gr_rail_gating_idle_us",
}

_RAIL = r"(nvvdd|msvdd)"
_ROLE = r"(rel|alt|ov)"
_CONNECTOR_POWER = re.compile(r"connector_(\d+)_power_(max|rated)_w")
_CONNECTOR_CURRENT = re.compile(r"connector_(\d+)_current_threshold_(max|rated)_ma")
_FAN_LIMIT = re.compile(r"fan_(\d+)_(min|max)_(rpm|pct)")
_FAN_CURVE = re.compile(r"fan_(\d+|extra_(\d+))_curve_(\d)_(temp_c|rpm|pct)")
_FAN_ZERO = re.compile(r"fan_(\d+|extra_(\d+))_zero_rpm_(low|high)_temp_c")
_PERF_CF = re.compile(r"perf_cf_(gpc|dram|vid)_(target_pct|jump_pct|hysteresis_down|hysteresis_up)")
_MEMORY_POINT = re.compile(r"memory_point_(\d+)_follows_offset")
_CLOCK_DOMAIN = re.compile(r"(xbar|sys|vid)_(max|min)_table_mhz")
_RAIL_EQ = re.compile(_RAIL + r"_" + _ROLE + r"_equation_max_mv")
_RAIL_FIXED = re.compile(_RAIL + r"_" + _ROLE + r"_fixed_mv")
_RAIL_VMIN = re.compile(_RAIL + r"_vmin_mv")
_RAIL_VMIN_SLOT = re.compile(_RAIL + r"_vmin_equation_max_mv")
_RAIL_OCP = re.compile(_RAIL + r"_output_ocp_(max|rated)_ma")


_ARCHITECTURE_NAMES = {
    "blackwell": "Blackwell GB20x",
    "ada": "Ada AD10x",
    "ampere": "Ampere GA10x",
    "turing": "Turing TU10x/TU11x",
    "ga100": "GA100 (read-only)",
    "unknown": "Unknown",
}


def format_numeric(value: str | None) -> str:
    """Compact huge integer bounds for read-only table cells (``2.15M``)."""
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
    return value


def architecture_label(value: str) -> str:
    """Render machine architecture codes (``ada``) as the names used in the UI."""
    key = (value or "").strip().lower()
    return _ARCHITECTURE_NAMES.get(key, value)


def section_title(section_id: str, _: Translate, fallback: str | None = None) -> str:
    msgid = SECTION_MSGIDS.get(section_id)
    if msgid:
        text = _(msgid)
        if text != msgid:
            return text
    return fallback or section_id.replace("_", " ").title()


def field_label(field: FieldSnapshot, _: Translate) -> str:
    """Return the localised label for ``field``, falling back to the snapshot label."""
    key = field.key
    if key in _EXACT:
        text = _(_EXACT[key])
        if text != _EXACT[key]:
            return text
        return field.label or key
    match = _CONNECTOR_POWER.fullmatch(key)
    if match:
        return _("field.connector_power_" + match.group(2)).format(connector=match.group(1))
    match = _CONNECTOR_CURRENT.fullmatch(key)
    if match:
        return _("field.connector_current_threshold_" + match.group(2)).format(
            connector=match.group(1)
        )
    match = _FAN_LIMIT.fullmatch(key)
    if match:
        return _(f"field.fan_{match.group(2)}_{match.group(3)}").format(fan=match.group(1))
    match = _FAN_CURVE.fullmatch(key)
    if match:
        owner, extra, point, unit = match.groups()
        if extra:
            return _("field.fan_extra_curve_" + unit).format(curve=extra, point=point)
        return _("field.fan_curve_" + unit).format(fan=owner, point=point)
    match = _FAN_ZERO.fullmatch(key)
    if match:
        owner, extra, side = match.groups()
        if extra:
            return _("field.fan_extra_zero_rpm_" + side + "_temp_c").format(curve=extra)
        return _("field.fan_zero_rpm_" + side + "_temp_c").format(fan=owner)
    match = _PERF_CF.fullmatch(key)
    if match:
        return _("field.perf_cf_" + match.group(2)).format(domain=match.group(1).upper())
    match = _MEMORY_POINT.fullmatch(key)
    if match:
        return _("field.memory_point_follows_offset").format(point=match.group(1))
    match = _CLOCK_DOMAIN.fullmatch(key)
    if match:
        return _("field.clock_domain_" + match.group(2)).format(domain=match.group(1).upper())
    match = _RAIL_EQ.fullmatch(key)
    if match:
        return _("field.equation").format(rail=match.group(1).upper(), role=match.group(2).upper())
    match = _RAIL_FIXED.fullmatch(key)
    if match:
        return _("field.fixed").format(rail=match.group(1).upper(), role=match.group(2).upper())
    match = _RAIL_VMIN.fullmatch(key)
    if match:
        return _("field.vmin").format(rail=match.group(1).upper())
    match = _RAIL_VMIN_SLOT.fullmatch(key)
    if match:
        return _("field.vmin_slot").format(rail=match.group(1).upper())
    match = _RAIL_OCP.fullmatch(key)
    if match:
        return _(
            "field.output_ocp" if match.group(2) == "max" else "field.output_ocp_rated"
        ).format(rail=match.group(1).upper())
    return field.label or key


def risk_label(risk: str, _: Translate) -> str:
    names = {"T0": "risk.t0", "T1": "risk.t1", "T2": "risk.t2", "T3": "risk.t3"}
    return _(names.get(risk, "risk.unknown"))


def experimental_label(_: Translate) -> str:
    return _("badge.experimental")
