"""Confirmation words are frozen by docs/risk-model.md §7.2."""

from __future__ import annotations

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.settings import request_experimental_unlock
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.dialogs.confirm_dialog import (
    EXPERIMENTAL_UNLOCK_WORD,
    T3_CONFIRM_WORD,
    ConfirmationRules,
)


def test_frozen_words_match_risk_model() -> None:
    assert EXPERIMENTAL_UNLOCK_WORD == "I UNDERSTAND"
    assert T3_CONFIRM_WORD == "T3"


def test_t3_rules_accept_field_key_or_t3() -> None:
    rules = ConfirmationRules(
        require_checkbox=True,
        allowed_words=("power_max_w", T3_CONFIRM_WORD),
    )
    assert rules.accepts(True, "power_max_w") is True
    assert rules.accepts(True, "T3") is True
    assert rules.accepts(True, "CONFIRM") is False
    assert rules.accepts(False, "T3") is False


def test_i18n_words_match_the_frozen_rules() -> None:
    assert "I UNDERSTAND" in _("experimental.word")
    assert "T3" in _("t3.confirm.word")
    assert "{key}" in _("t3.confirm.body")


def test_experimental_dialog_uses_i_understand(gtk_initialised, controller: UiController) -> None:
    dialog = request_experimental_unlock(None, _, controller)
    assert dialog.rules.required_word == "I UNDERSTAND"
    assert dialog.rules.accepts(True, "ENABLE") is False
    assert dialog.rules.accepts(True, "I UNDERSTAND") is True
    dialog.destroy()
