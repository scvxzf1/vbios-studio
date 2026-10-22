# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Top toolbar: file actions, search, language, theme and help."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from vbios_studio.i18n import language_name
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController

Translate = Callable[[str], str]


class HeaderBar(Gtk.Box):
    def __init__(
        self,
        _: Translate,
        controller: UiController,
        *,
        on_open: Callable[[], None],
        on_save: Callable[[], None],
        on_undo: Callable[[], None],
        on_redo: Callable[[], None],
        on_search: Callable[[str], None],
        on_language: Callable[[str], None],
        on_theme: Callable[[str], None],
        on_shortcuts: Callable[[], None],
        on_about: Callable[[], None],
        on_profile_save: Callable[[], None],
        on_profile_load: Callable[[], None],
        on_diff: Callable[[], None],
        on_experimental: Callable[[], None],
        on_reset: Callable[[], None],
    ) -> None:
        super().__init__()
        self.bar = Adw.HeaderBar()
        self._ = _
        self.controller = controller
        self.on_language = on_language
        self.on_theme = on_theme
        self.language_buttons: dict[str, Gtk.CheckButton] = {}
        self.theme_buttons: dict[str, Gtk.CheckButton] = {}

        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title.set_valign(Gtk.Align.CENTER)
        self.title_label = Gtk.Label(label=_("app.title"), xalign=0.5)
        self.title_label.add_css_class("vb-header-title")
        self.subtitle = Gtk.Label(label=_("app.warning_short"), xalign=0.5)
        self.subtitle.add_css_class("vb-header-sub")
        self.subtitle.set_ellipsize(3)
        title.append(self.title_label)
        title.append(self.subtitle)
        self.bar.set_title_widget(title)

        self.open_button = self._icon_button(
            "folder-open-symbolic", _("toolbar.open.tooltip"), on_open
        )
        self.save_button = self._icon_button(
            "document-save-as-symbolic", _("toolbar.save.tooltip"), on_save
        )
        self.undo_button = self._icon_button(
            "edit-undo-symbolic", _("toolbar.undo.tooltip"), on_undo
        )
        self.redo_button = self._icon_button(
            "edit-redo-symbolic", _("toolbar.redo.tooltip"), on_redo
        )
        for button in (self.open_button, self.save_button, self.undo_button, self.redo_button):
            self.bar.pack_start(button)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(_("toolbar.search.placeholder"))
        self.search_entry.set_width_chars(16)
        self.search_entry.set_max_width_chars(22)
        self.search_entry.connect("search-changed", lambda entry: on_search(entry.get_text()))
        set_accessible(self.search_entry, _("toolbar.search.placeholder"))
        self.bar.pack_end(self.search_entry)

        self.help_button = self._menu_button(
            "help-about-symbolic",
            _("toolbar.help.tooltip"),
            self._help_popover(on_shortcuts, on_about, on_experimental),
        )
        self.bar.pack_end(self.help_button)

        self.theme_button = self._menu_button(
            "preferences-system-symbolic", _("toolbar.theme.tooltip"), self._theme_popover()
        )
        self.bar.pack_end(self.theme_button)
        self.language_button = self._menu_button(
            "set-language-symbolic", _("toolbar.language.tooltip"), self._language_popover()
        )
        self.bar.pack_end(self.language_button)
        self._ = _

        # Secondary actions live in the application menu button (kept out of the busy toolbar).
        self.menu_button = self._menu_button(
            "open-menu-symbolic",
            _("toolbar.menu.tooltip"),
            self._main_popover(on_profile_save, on_profile_load, on_diff, on_reset),
        )
        self.bar.pack_end(self.menu_button)
        self.refresh_actions()

    def _icon_button(self, icon: str, tooltip: str, callback: Callable[[], None]) -> Gtk.Button:
        button = Gtk.Button.new_from_icon_name(icon)
        button.set_tooltip_text(tooltip)
        button.connect("clicked", lambda _b: callback())
        set_accessible(button, tooltip)
        return button

    def _menu_button(self, icon: str, tooltip: str, popover: Gtk.Popover) -> Gtk.MenuButton:
        button = Gtk.MenuButton()
        button.set_icon_name(icon)
        button.set_tooltip_text(tooltip)
        button.set_popover(popover)
        set_accessible(button, tooltip)
        return button

    def _popover(self) -> tuple[Gtk.Popover, Gtk.Box]:
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        popover.set_child(box)
        return popover, box

    def _choice(
        self,
        box: Gtk.Box,
        label: str,
        group: Gtk.CheckButton | None,
        callback: Callable[[], None],
        active: bool,
    ) -> Gtk.CheckButton:
        button = Gtk.CheckButton(label=label)
        if group is not None:
            button.set_group(group)
        button.set_active(active)
        button.connect("toggled", lambda b: callback() if b.get_active() else None)
        set_accessible(button, label)
        box.append(button)
        return button

    def _language_popover(self) -> Gtk.Popover:
        popover, box = self._popover()
        heading = Gtk.Label(label=self._("toolbar.language"), xalign=0)
        heading.add_css_class("vb-dim")
        box.append(heading)
        group: Gtk.CheckButton | None = None
        for code in ("en", "zh_CN"):
            button = self._choice(
                box,
                language_name(code),
                group,
                lambda code=code: self.on_language(code),
                self.controller is not None and code == self._language(),
            )
            self.language_buttons[code] = button
            group = group or button
        return popover

    def _language(self) -> str:
        from vbios_studio.i18n import get_language

        return get_language()

    def _theme_popover(self) -> Gtk.Popover:
        popover, box = self._popover()
        heading = Gtk.Label(label=self._("toolbar.theme"), xalign=0)
        heading.add_css_class("vb-dim")
        box.append(heading)
        group: Gtk.CheckButton | None = None
        for key, msgid in (
            ("system", "theme.system"),
            ("light", "theme.light"),
            ("dark", "theme.dark"),
        ):
            button = self._choice(
                box, self._(msgid), group, lambda key=key: self.on_theme(key), key == "system"
            )
            self.theme_buttons[key] = button
            group = group or button
        return popover

    def _help_popover(
        self,
        on_shortcuts: Callable[[], None],
        on_about: Callable[[], None],
        on_experimental: Callable[[], None],
    ) -> Gtk.Popover:
        popover, box = self._popover()
        for label, callback in (
            (self._("help.shortcuts"), on_shortcuts),
            (self._("help.experimental"), on_experimental),
            (self._("help.about"), on_about),
        ):
            button = Gtk.Button(label=label)
            button.add_css_class("flat")
            button.set_halign(Gtk.Align.FILL)
            button.connect("clicked", lambda _b, cb=callback, pop=popover: (pop.popdown(), cb()))
            set_accessible(button, label)
            box.append(button)
        return popover

    def _main_popover(
        self,
        on_profile_save: Callable[[], None],
        on_profile_load: Callable[[], None],
        on_diff: Callable[[], None],
        on_reset: Callable[[], None],
    ) -> Gtk.Popover:
        popover, box = self._popover()
        for label, callback in (
            (self._("profile.save"), on_profile_save),
            (self._("profile.load"), on_profile_load),
            (self._("diff.open"), on_diff),
            (self._("edit.reset"), on_reset),
        ):
            button = Gtk.Button(label=label)
            button.add_css_class("flat")
            button.set_halign(Gtk.Align.FILL)
            button.connect("clicked", lambda _b, cb=callback, pop=popover: (pop.popdown(), cb()))
            set_accessible(button, label)
            box.append(button)
        return popover

    def refresh_actions(self) -> None:
        self.undo_button.set_sensitive(self.controller.can_undo)
        self.redo_button.set_sensitive(self.controller.can_redo)
        self.save_button.set_sensitive(self.controller.has_document)

    def set_subtitle(self, text: str) -> None:
        self.subtitle.set_text(text)

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.title_label.set_text(_("app.title"))
        self.subtitle.set_text(_("app.warning_short"))
        self.search_entry.set_placeholder_text(_("toolbar.search.placeholder"))
        for button, msgid in (
            (self.open_button, "toolbar.open.tooltip"),
            (self.save_button, "toolbar.save.tooltip"),
            (self.undo_button, "toolbar.undo.tooltip"),
            (self.redo_button, "toolbar.redo.tooltip"),
            (self.help_button, "toolbar.help.tooltip"),
            (self.theme_button, "toolbar.theme.tooltip"),
            (self.language_button, "toolbar.language.tooltip"),
            (self.menu_button, "toolbar.menu.tooltip"),
        ):
            text = _(msgid)
            button.set_tooltip_text(text)
            set_accessible(button, text)
