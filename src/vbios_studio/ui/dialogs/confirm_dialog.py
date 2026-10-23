# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Second confirmation for T3 edits and every system write."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from vbios_studio.ui.a11y import set_accessible

# Frozen by docs/risk-model.md §7.2.  Do not silently change these words.
EXPERIMENTAL_UNLOCK_WORD = "I UNDERSTAND"
T3_CONFIRM_WORD = "T3"


@dataclass(frozen=True)
class ConfirmationRules:
    require_checkbox: bool = True
    required_word: str = ""
    allowed_words: tuple[str, ...] = ()

    @property
    def needs_word(self) -> bool:
        return bool(self.required_word or self.allowed_words)

    def accepts(self, checked: bool, typed: str) -> bool:
        checkbox_ok = not self.require_checkbox or checked
        accepted = self.allowed_words or ((self.required_word,) if self.required_word else ())
        word_ok = not accepted or typed.strip() in accepted
        return checkbox_ok and word_ok


class ConfirmDialog(Adw.Window):
    """Modal confirmation; ``on_confirm`` is called only when every rule passes."""

    def __init__(
        self,
        parent: Gtk.Window | None,
        title: str,
        body: str,
        *,
        rules: ConfirmationRules | None = None,
        confirm_label: str,
        cancel_label: str,
        checkbox_label: str = "",
        word_label: str = "",
        on_confirm: Callable[[], None] | None = None,
        width: int = 520,
    ) -> None:
        super().__init__(transient_for=parent, modal=True, title=title)
        self.set_default_size(width, 320)
        self.rules = rules or ConfirmationRules(require_checkbox=False)
        self.on_confirm = on_confirm
        self.checkbox: Gtk.CheckButton | None = None
        self.word_entry: Gtk.Entry | None = None

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=title))
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        icon.set_pixel_size(44)
        icon.set_halign(Gtk.Align.START)
        box.append(icon)

        heading = Gtk.Label(label=title, xalign=0)
        heading.set_wrap(True)
        heading.add_css_class("vb-section-title")
        set_accessible(heading, title)
        box.append(heading)

        body_label = Gtk.Label(label=body, xalign=0)
        body_label.set_wrap(True)
        body_label.set_selectable(True)
        set_accessible(body_label, body)
        box.append(body_label)

        if self.rules.require_checkbox:
            self.checkbox = Gtk.CheckButton(label=checkbox_label)
            set_accessible(self.checkbox, checkbox_label)
            box.append(self.checkbox)
        if self.rules.needs_word:
            label = Gtk.Label(label=word_label, xalign=0)
            box.append(label)
            self.word_entry = Gtk.Entry()
            self.word_entry.set_placeholder_text(
                self.rules.required_word or " / ".join(self.rules.allowed_words)
            )
            set_accessible(self.word_entry, word_label or self.rules.required_word)
            box.append(self.word_entry)

        buttons = Gtk.Box(spacing=8)
        buttons.set_halign(Gtk.Align.END)
        buttons.set_margin_top(4)
        self.cancel_button = Gtk.Button(label=cancel_label)
        self.cancel_button.connect("clicked", lambda _b: self.close())
        set_accessible(self.cancel_button, cancel_label)
        self.confirm_button = Gtk.Button(label=confirm_label)
        self.confirm_button.add_css_class("destructive-action")
        self.confirm_button.connect("clicked", lambda _b: self._try_confirm())
        set_accessible(self.confirm_button, confirm_label)
        buttons.append(self.cancel_button)
        buttons.append(self.confirm_button)
        box.append(buttons)

        for widget in (self.checkbox, self.word_entry):
            if widget is not None:
                widget.connect(
                    "changed" if isinstance(widget, Gtk.Entry) else "toggled",
                    self._refresh_sensitivity,
                )
        self._refresh_sensitivity()

        toolbar.set_content(box)
        self.set_content(toolbar)

    def _refresh_sensitivity(self) -> None:
        checked = bool(self.checkbox and self.checkbox.get_active())
        typed = self.word_entry.get_text() if self.word_entry else ""
        self.confirm_button.set_sensitive(self.rules.accepts(checked, typed))

    def _try_confirm(self) -> None:
        checked = bool(self.checkbox and self.checkbox.get_active())
        typed = self.word_entry.get_text() if self.word_entry else ""
        if not self.rules.accepts(checked, typed):
            return
        if self.on_confirm is not None:
            self.on_confirm()
        self.close()
