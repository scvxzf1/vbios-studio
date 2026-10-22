"""Risk colours are centralised and badges carry the matching CSS class."""

from __future__ import annotations

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.risk_badge import RiskBadge
from vbios_studio.ui.theme import CSS, RISK_COLORS, RISK_CSS_CLASSES


def test_risk_colour_constants_are_exact_and_generate_css() -> None:
    assert RISK_COLORS == {
        "T0": "#6B7280",
        "T1": "#2563EB",
        "T2": "#D97706",
        "T3": "#DC2626",
    }
    assert set(RISK_CSS_CLASSES) == set(RISK_COLORS)
    for risk, color in RISK_COLORS.items():
        assert f".{RISK_CSS_CLASSES[risk]}" in CSS
        assert color in CSS


def test_badge_carries_risk_class_and_text(gtk_initialised) -> None:
    badge = RiskBadge("T3", _)
    assert badge.has_css_class("vb-badge")
    assert badge.has_css_class("risk-t3")
    assert "T3" in badge.get_text()
