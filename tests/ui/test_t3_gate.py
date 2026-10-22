"""T3 fields stay hidden and locked until an explicit per-field confirmation."""

from __future__ import annotations

import contextlib

import pytest

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.risk_badge import RiskBadge
from vbios_studio.ui.controller import ConfirmationRequired, T3LockedError, UiController
from vbios_studio.ui.theme import RISK_COLORS, RISK_CSS_CLASSES


def test_t3_field_is_hidden_and_locked(controller: UiController) -> None:
    assert "power_max_w" not in {field.key for field in controller.visible_fields}
    with pytest.raises(T3LockedError):
        controller.set_value("power_max_w", "300")
    assert controller.changes == {}


def test_unlock_requires_per_field_confirmation(controller: UiController) -> None:
    controller.set_experimental_unlocked(True)
    assert "power_max_w" in {field.key for field in controller.visible_fields}
    with pytest.raises(ConfirmationRequired) as raised:
        controller.set_value("power_max_w", "300")
    assert raised.value.old == "250"
    assert raised.value.new == "300"
    assert controller.changes == {}
    preview = controller.set_value("power_max_w", "300", t3_confirmed=True)
    assert not preview.errors
    assert controller.changes == {"power_max_w": "300"}


def test_cancel_means_zero_changes(controller: UiController) -> None:
    controller.set_experimental_unlocked(True)
    with contextlib.suppress(ConfirmationRequired):
        controller.set_value("power_max_w", "300")
    assert controller.changes == {}
    assert controller.can_undo is False


def test_risk_colours_are_central_and_exact() -> None:
    assert RISK_COLORS == {"T0": "#6B7280", "T1": "#2563EB", "T2": "#D97706", "T3": "#DC2626"}
    assert RISK_CSS_CLASSES == {"T0": "risk-t0", "T1": "risk-t1", "T2": "risk-t2", "T3": "risk-t3"}


def test_risk_badge_has_text_and_colour(gtk_initialised) -> None:
    for risk in ("T0", "T1", "T2", "T3"):
        badge = RiskBadge(risk, _)
        assert risk in badge.get_text()
        assert badge.has_css_class(RISK_CSS_CLASSES[risk])
