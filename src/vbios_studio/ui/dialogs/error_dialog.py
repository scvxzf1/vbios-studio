# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""One error surface for every failure: title, diagnostic and copyable details."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from vbios_studio.ui.a11y import set_accessible


class ErrorDialog(Adw.Window):
    def __init__(
        self,
        parent: Gtk.Window | None,
        title: str,
        message: str,
        details: str = "",
        _: Callable[[str], str] | None = None,
    ) -> None:
        translate = _ or (lambda text: text)
        super().__init__(transient_for=parent, modal=True, title=title)
        self.set_default_size(560, 360)
        self.details_text = "\n".join(part for part in (message, details) if part)
        self._translate = translate

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=title))
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)

        icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
        icon.set_pixel_size(48)
        icon.set_halign(Gtk.Align.START)
        box.append(icon)

        heading = Gtk.Label(label=message, xalign=0)
        heading.set_wrap(True)
        heading.add_css_class("vb-section-title")
        set_accessible(heading, message)
        box.append(heading)

        view = Gtk.TextView()
        view.set_editable(False)
        view.set_cursor_visible(False)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.add_css_class("vb-mono")
        view.get_buffer().set_text(self.details_text)
        set_accessible(view, translate("error.details"))
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(view)
        scroller.set_vexpand(True)
        scroller.add_css_class("vb-card")
        box.append(scroller)

        buttons = Gtk.Box(spacing=8)
        buttons.set_halign(Gtk.Align.END)
        copy = Gtk.Button(label=translate("error.copy"))
        copy.connect("clicked", lambda _button: self.copy_details())
        set_accessible(copy, translate("error.copy"))
        close = Gtk.Button(label=translate("common.close"))
        close.add_css_class("suggested-action")
        close.connect("clicked", lambda _button: self.close())
        set_accessible(close, translate("common.close"))
        buttons.append(copy)
        buttons.append(close)
        box.append(buttons)

        toolbar.set_content(box)
        self.set_content(toolbar)

    def copy_details(self) -> None:
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(self.details_text)

    @staticmethod
    def from_exception(
        parent: Gtk.Window | None,
        title: str,
        exc: Exception,
        _: Callable[[str], str] | None = None,
    ) -> ErrorDialog:
        code = getattr(exc, "code", type(exc).__name__)
        message = getattr(exc, "message", str(exc))
        hint = getattr(exc, "hint", "")
        details = f"[{code}] {message}"
        if hint:
            details += f"\n\n{hint}"
        return ErrorDialog(parent, title, message, details, _)
