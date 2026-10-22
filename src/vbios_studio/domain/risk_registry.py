"""Per-field T0-T3 risk registry frozen by ``docs/risk-model.md``.

The registry is deliberately conservative: an unknown key is T0 read-only.
Direction-aware downgrades exist only where the frozen document defines them
(for example lowering a power limit is T1 while raising it stays T3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .models import RiskLevel
from .risk import risk_rank

Direction = str  # "increase" | "decrease"


@dataclass(frozen=True, slots=True)
class RiskRule:
    """One reviewed pattern and its most dangerous direction."""

    pattern: str
    level: RiskLevel
    experimental: bool = False
    opt_in: bool = False
    editable: bool = True
    benign_direction: Direction | None = None
    benign_level: RiskLevel | None = None

    def matches(self, key: str) -> bool:
        """Whether the key belongs to this rule."""
        return re.fullmatch(self.pattern, key) is not None


# Order matters: read-only / more specific patterns come first.
RISK_RULES: tuple[RiskRule, ...] = (
    # Read-only structural and audit fields.
    RiskRule(r"(?:nvvdd|msvdd)_vmin_equation_max_mv", "T0", editable=False),
    RiskRule(r"(?:nvvdd|msvdd)_(?:rel|alt|ov|vmin)_selector_index", "T0", editable=False),
    RiskRule(r"(?:nvvdd|msvdd)_boot_voltage_uv", "T0", editable=False),
    RiskRule(r"factory_rated_boost_mhz", "T0", editable=False),
    RiskRule(r"(?:current_limit_a|ocp_limit_a|input_policy_9_max_raw)", "T0", editable=False),
    RiskRule(r"(?:configurations|bands|timings|tables|board_profile)", "T0", editable=False),
    # Power.
    RiskRule(r"power_min_w", "T1"),
    RiskRule(
        r"power_default_w", "T3", experimental=True, benign_direction="decrease", benign_level="T1"
    ),
    RiskRule(
        r"power_max_w", "T3", experimental=True, benign_direction="decrease", benign_level="T1"
    ),
    RiskRule(
        r"slot_power_(?:max|rated)_w",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(
        r"connector_\d+_power_(?:max|rated)_w",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(
        r"connector_sum_power_(?:max|rated)_w",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(r"board_fixed_rated_w", "T3", experimental=True, opt_in=True),
    RiskRule(
        r"max_operating_temp_c",
        "T2",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(r"nvvdd_power_threshold_(?:max|rated)_w", "T3", experimental=True, opt_in=True),
    # Voltage (all T3; a lower value can still be unstable).
    RiskRule(r"(?:nvvdd|msvdd)_rel_max_mv", "T3", experimental=True),
    RiskRule(r"(?:nvvdd|msvdd)_vmin_mv", "T3", experimental=True),
    RiskRule(r"nvvdd_(?:rel|alt)_fixed_mv", "T3", experimental=True, opt_in=True),
    RiskRule(r"nvvdd_rel_alt_follow_ov", "T3", experimental=True, opt_in=True),
    RiskRule(r"(?:nvvdd|msvdd)_(?:rel|alt|ov)_equation_max_mv", "T3", experimental=True),
    # Current and protection thresholds.
    RiskRule(
        r"input_current_(?:rated|max)_ma",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T2",
    ),
    RiskRule(
        r"input_current_policy7_limit_ma",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T2",
    ),
    RiskRule(
        r"(?:nvvdd|msvdd)_output_ocp_(?:rated|max)_ma",
        "T3",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(
        r"slot_current_threshold_(?:rated|max)_ma",
        "T3",
        experimental=True,
        opt_in=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(
        r"connector_\d+_current_threshold_(?:rated|max)_ma",
        "T3",
        experimental=True,
        opt_in=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    # Fans.
    RiskRule(r"fan_channels", "T3", experimental=True),
    RiskRule(r"fan_pwm_frequency_hz", "T2", experimental=True),
    RiskRule(
        r"fan_\d+_(?:min|max)_(?:rpm|pct)",
        "T2",
        experimental=True,
        benign_direction="increase",
        benign_level="T1",
    ),
    RiskRule(
        r"fan_(?:\d+|extra_\d+)_curve_\d+_temp_c",
        "T2",
        experimental=True,
        benign_direction="decrease",
        benign_level="T1",
    ),
    RiskRule(
        r"fan_(?:\d+|extra_\d+)_curve_\d+_(?:rpm|pct)",
        "T2",
        experimental=True,
        benign_direction="increase",
        benign_level="T1",
    ),
    RiskRule(r"fan_zero_rpm", "T3", experimental=True, opt_in=True),
    RiskRule(
        r"fan_(?:\d+|extra_\d+)_zero_rpm_(?:low|high)_temp_c", "T3", experimental=True, opt_in=True
    ),
    # Clocks.
    RiskRule(r"(?:gpc|memory)_offset_(?:min|max)_mhz", "T2", experimental=True),
    RiskRule(r"(?:dram|xbar|sys|vid)_(?:min|max)_table_mhz", "T2", experimental=True),
    RiskRule(r"gpc_curve_offset_mhz", "T2", experimental=True, opt_in=True),
    RiskRule(r"factory_gpc_offset_mhz", "T2", experimental=True),
    RiskRule(r"memory_point_\d+_follows_offset", "T2", experimental=True, opt_in=True),
    # Advanced power-management switches and idle timers.
    RiskRule(r"perf_cf_.*", "T3", experimental=True),
    RiskRule(r"lpwr_.*", "T3", experimental=True),
)


def lookup_rule(key: str) -> RiskRule | None:
    """Return the first matching risk rule or ``None`` for unknown keys."""
    return next((rule for rule in RISK_RULES if rule.matches(key)), None)


def is_registered(key: str) -> bool:
    """Whether the frozen registry covers a field key."""
    return lookup_rule(key) is not None


def is_opt_in(key: str) -> bool:
    """Whether the frozen registry marks a field as opt-in only."""
    rule = lookup_rule(key)
    return bool(rule and rule.opt_in)


def is_experimental(key: str, family: str | None = None) -> bool:
    """Whether a field carries the experimental badge for this family."""
    rule = lookup_rule(key)
    if rule is None:
        return False
    if family == "blackwell-gb20x" and key in {"power_max_w", "dram_max_table_mhz"}:
        return False
    return rule.experimental


def adjust_for_family(level: RiskLevel, family: str | None) -> RiskLevel:
    """Apply the Ampere/Turing family correction from risk model section 5."""
    if family in {"ampere", "turing"}:
        if level == "T1":
            return "T2"
        if level == "T2":
            return "T3"
    return level


def risk_for_field(key: str, *, family: str | None = None, editable: bool = True) -> RiskLevel:
    """Return the base (most dangerous direction) level shown in the catalog."""
    rule = lookup_rule(key)
    if not editable or rule is None or not rule.editable:
        return "T0"
    return adjust_for_family(rule.level, family)


def _direction(old: object, new: object) -> Direction | None:
    try:
        before, after = Decimal(str(old)), Decimal(str(new))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if after > before:
        return "increase"
    if after < before:
        return "decrease"
    return None


def classify_change(
    key: str,
    old: object,
    new: object,
    *,
    family: str | None = None,
    editable: bool = True,
) -> RiskLevel:
    """Return the T0-T3 level of one concrete direction of change."""
    rule = lookup_rule(key)
    if not editable or rule is None or not rule.editable:
        return "T0"
    direction = _direction(old, new)
    if direction is None:
        try:
            if Decimal(str(old)) == Decimal(str(new)):
                return "T0"
        except (InvalidOperation, TypeError, ValueError):
            pass
    level = rule.level
    if (
        rule.benign_direction is not None
        and rule.benign_level is not None
        and direction == rule.benign_direction
    ):
        level = rule.benign_level
    return adjust_for_family(level, family)


def highest_risk(levels: list[RiskLevel]) -> RiskLevel:
    """Return the highest level in a batch (T0 for an empty batch)."""
    best: RiskLevel = "T0"
    for level in levels:
        if risk_rank(level) > risk_rank(best):
            best = level
    return best
