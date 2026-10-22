"""Risk-level helpers shared by the field catalog and the GTK presentation.

Risk levels are frozen by ``docs/risk-model.md``: T0 read-only, T1 low,
T2 medium, T3 high/experimental. A batch inherits the highest level of any
field it touches.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import RiskLevel

RISK_LEVELS: tuple[RiskLevel, ...] = ("T0", "T1", "T2", "T3")
_RANK: dict[RiskLevel, int] = {level: index for index, level in enumerate(RISK_LEVELS)}


def risk_rank(level: RiskLevel) -> int:
    """Return the numeric rank of a risk level (T0=0 ... T3=3)."""
    return _RANK[level]


def max_risk(levels: Iterable[RiskLevel]) -> RiskLevel:
    """Return the highest risk level in ``levels`` (T0 for an empty input)."""
    highest: RiskLevel = "T0"
    for level in levels:
        if risk_rank(level) > risk_rank(highest):
            highest = level
    return highest


def is_t3(level: RiskLevel) -> bool:
    """Return whether ``level`` requires the experimental T3 gate."""
    return level == "T3"
