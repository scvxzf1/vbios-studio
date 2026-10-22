# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Risk badge with the single, centralised T0–T3 colour map."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.field_text import risk_label
from vbios_studio.ui.theme import RISK_CSS_CLASSES

Translate = Callable[[str], str]


class RiskBadge(Gtk.Label):
    """A text badge; colour is never the only carrier of the risk level."""

    def __init__(self, risk: str, _: Translate) -> None:
        super().__init__(label=f"{risk} {risk_label(risk, _).split(' ', 1)[-1]}")
        self.risk = risk if risk in RISK_CSS_CLASSES else "T0"
        self.add_css_class("vb-badge")
        self.add_css_class(RISK_CSS_CLASSES[self.risk])
        self.set_valign(Gtk.Align.CENTER)
        set_accessible(self, f"{risk_label(self.risk, _)}: {self.get_text()}")

    def retranslate(self, _: Translate) -> None:
        self.set_text(f"{self.risk} {risk_label(self.risk, _).split(' ', 1)[-1]}")
        set_accessible(self, f"{risk_label(self.risk, _)}: {self.get_text()}")


class ExperimentalBadge(Gtk.Label):
    def __init__(self, _: Translate, title: str | None = None) -> None:
        super().__init__(label=_("badge.experimental"))
        self.add_css_class("vb-badge-exp")
        self.set_valign(Gtk.Align.CENTER)
        self.set_tooltip_text(title or _("badge.experimental.tooltip"))
        set_accessible(self, _("badge.experimental"))
