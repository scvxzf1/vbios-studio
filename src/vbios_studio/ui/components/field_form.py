# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Form view: one collapsible card per section, optimised for reading and editing."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.domain.models import FieldSnapshot
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.components.risk_badge import ExperimentalBadge, RiskBadge
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.field_text import SECTION_ORDER, field_label, format_numeric, section_title
from vbios_studio.ui.theme import add_class

Translate = Callable[[str], str]


class FieldForm(Gtk.Box):
    def __init__(
        self, _: Translate, controller: UiController, on_commit: Callable[[str, str], None]
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._ = _
        self.controller = controller
        self.on_commit = on_commit
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_vexpand(True)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content.set_margin_top(4)
        self.content.set_margin_bottom(18)
        self.content.set_margin_start(2)
        self.content.set_margin_end(2)
        self.scroller.set_child(self.content)
        self.append(self.scroller)
        self.refresh()

    def _clear(self) -> None:
        while (child := self.content.get_first_child()) is not None:
            self.content.remove(child)

    def refresh(self) -> None:
        self._clear()
        groups: dict[str, list[FieldSnapshot]] = {}
        for field in self.controller.filtered_fields:
            groups.setdefault(field.section, []).append(field)
        ordered = [section for section in SECTION_ORDER if section in groups]
        ordered += [section for section in groups if section not in ordered]
        for section in ordered:
            self.content.append(self._section_card(section, groups[section]))

    def _section_card(self, section: str, fields: list[FieldSnapshot]) -> Gtk.Widget:
        _ = self._
        expander = Gtk.Expander(label=f"{section_title(section, _)}  ({len(fields)})")
        set_accessible(expander, f"{section_title(section, _)} ({len(fields)})")
        expander.set_expanded(
            section == self.controller.current_section
            or any(self.controller.is_modified(field.key) for field in fields)
        )
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("vb-card")
        card.set_margin_top(4)
        for index, field in enumerate(fields):
            if index:
                card.append(Gtk.Separator())
            card.append(self._field_row(field))
        expander.set_child(card)
        return expander

    def _field_row(self, field: FieldSnapshot) -> Gtk.Widget:
        _ = self._
        row = Gtk.Box(spacing=14)
        row.set_margin_top(8)
        row.set_margin_bottom(8)
        row.set_margin_start(14)
        row.set_margin_end(14)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        left.set_hexpand(True)
        title_row = Gtk.Box(spacing=6)
        label = Gtk.Label(label=field_label(field, _), xalign=0)
        label.add_css_class("vb-field-label")
        title_row.append(label)
        title_row.append(RiskBadge(field.risk, _))
        if field.experimental:
            title_row.append(ExperimentalBadge(_))
        left.append(title_row)
        key = Gtk.Label(label=field.key, xalign=0)
        add_class(key, "vb-mono", "vb-dim")
        left.append(key)
        if field.description:
            description = Gtk.Label(label=field.description, xalign=0)
            description.set_wrap(True)
            description.set_max_width_chars(72)
            description.add_css_class("vb-dim")
            left.append(description)
        hint = self._range_hint(field)
        if hint:
            hint_label = Gtk.Label(label=hint, xalign=0)
            add_class(hint_label, "vb-mono", "vb-dim")
            left.append(hint_label)
        row.append(left)

        right = Gtk.Box(spacing=6)
        right.set_valign(Gtk.Align.START)
        entry = Gtk.Entry()
        entry.set_alignment(1.0)
        entry.set_width_chars(12)
        entry.add_css_class("vb-num")
        entry.set_text(self.controller.value_of(field) or "")
        entry.set_editable(field.editable)
        entry.set_sensitive(field.editable)
        entry._vbios_field_key = field.key
        focus = Gtk.EventControllerFocus()
        focus.connect(
            "leave",
            lambda _c, e=entry: self.on_commit(
                getattr(e, "_vbios_field_key", None) or "", e.get_text()
            ),
        )
        entry.add_controller(focus)
        entry.connect(
            "activate",
            lambda e: self.on_commit(getattr(e, "_vbios_field_key", None) or "", e.get_text()),
        )
        set_accessible(entry, f"{field_label(field, _)}: {_('fields.column.current')}")
        right.append(entry)
        unit = Gtk.Label(label=field.unit, xalign=0)
        unit.set_size_request(44, -1)
        unit.add_css_class("vb-dim")
        right.append(unit)
        row.append(right)
        return row

    def _range_hint(self, field: FieldSnapshot) -> str:
        parts: list[str] = []
        if field.minimum is not None or field.maximum is not None:
            minimum = format_numeric(field.minimum)
            maximum = format_numeric(field.maximum)
            parts.append(f"{minimum} – {maximum} {field.unit}")
        if field.default is not None:
            parts.append(
                self._("fields.default_hint").format(
                    value=format_numeric(field.default), unit=field.unit
                )
            )
        if field.offset is not None:
            parts.append(f"@ 0x{field.offset:04X}")
        return "   ".join(parts)

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.refresh()
