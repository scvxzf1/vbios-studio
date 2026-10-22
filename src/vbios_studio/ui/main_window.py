# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Main application window: toolbar, navigation, stacked views, log and status bar."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import EditPreview, FieldError
from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.apply_panel import ApplyPanel
from vbios_studio.ui.components.diff_view import DiffView
from vbios_studio.ui.components.empty_state import EmptyState
from vbios_studio.ui.components.field_filters import FieldToolbar
from vbios_studio.ui.components.field_form import FieldForm
from vbios_studio.ui.components.field_table import FieldTable
from vbios_studio.ui.components.file_info import FileInfoCard
from vbios_studio.ui.components.header_bar import HeaderBar
from vbios_studio.ui.components.log_panel import LogPanel
from vbios_studio.ui.components.settings import request_experimental_unlock
from vbios_studio.ui.components.sidebar import Sidebar
from vbios_studio.ui.components.status_bar import StatusBar
from vbios_studio.ui.controller import ConfirmationRequired, T3LockedError, UiController
from vbios_studio.ui.dialogs.about_dialog import show_about
from vbios_studio.ui.dialogs.confirm_dialog import ConfirmationRules, ConfirmDialog
from vbios_studio.ui.dialogs.error_dialog import ErrorDialog
from vbios_studio.ui.dialogs.shortcuts_dialog import show_shortcuts
from vbios_studio.ui.drop_target import install_drop_target
from vbios_studio.ui.shortcuts import install_shortcuts

LanguageCallback = Callable[[str], None]
ThemeCallback = Callable[[str], None]


class MainWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        application: Adw.Application | None,
        controller: UiController,
        *,
        on_language: LanguageCallback | None = None,
        on_theme: ThemeCallback | None = None,
    ) -> None:
        super().__init__(application=application)
        self.set_default_size(1280, 840)
        self.set_title(_("app.title"))
        self.controller = controller
        self.on_language = on_language or (lambda _code: None)
        self.on_theme = on_theme or (lambda _theme: None)
        self._refresh_scheduled = False
        self._build_ui()
        from vbios_studio.ui.window_dialogs import WindowDialogs

        self.dialogs = WindowDialogs(self)
        self._install_shortcuts()
        self._install_drop_target()
        controller.subscribe(self._on_controller_event)
        self._refresh_all()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.toast_overlay = Adw.ToastOverlay()
        self.toolbar_view = Adw.ToolbarView()
        self.header = HeaderBar(
            _,
            self.controller,
            on_open=self.open_dialog,
            on_save=self.save_dialog,
            on_undo=self.undo,
            on_redo=self.redo,
            on_search=self._on_search,
            on_language=self.on_language,
            on_theme=self.on_theme,
            on_shortcuts=self.show_shortcuts,
            on_about=self.show_about,
            on_profile_save=self.save_profile_dialog,
            on_profile_load=self.load_profile_dialog,
            on_diff=self.choose_diff_dialog,
            on_experimental=self.enable_experimental,
            on_reset=self.reset_changes,
        )
        self.toolbar_view.add_top_bar(self.header.bar)
        self.split = Adw.NavigationSplitView()
        self.sidebar = Sidebar(_, self.controller, self.navigate)
        self.sidebar_page = Adw.NavigationPage.new(self.sidebar, _("sidebar.navigation"))
        self.split.set_sidebar(self.sidebar_page)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.empty_state = EmptyState(_, self.open_dialog)
        self.stack.add_named(self.empty_state, "empty")
        self.document_page = self._build_document_page()
        self.stack.add_named(self.document_page, "document")
        self.apply_panel = ApplyPanel(_, self.controller, self._show_error)
        self.stack.add_named(self._wrap_page(self.apply_panel), "apply")
        self.diff_view = DiffView(_, self.choose_diff_dialog)
        self.stack.add_named(self._wrap_page(self.diff_view), "diff")
        self.content_page = Adw.NavigationPage.new(self.stack, _("app.title"))
        self.split.set_content(self.content_page)
        self.toolbar_view.set_content(self.split)

        self.log_panel = LogPanel(_, self.controller)
        self.toolbar_view.add_bottom_bar(self.log_panel)
        self.status_bar = StatusBar(_, self.controller)
        self.toolbar_view.add_bottom_bar(self.status_bar)
        self.status_bar.log_toggle.connect("toggled", self._on_log_toggled)
        self.log_panel.connect("notify::expanded", self._on_log_expanded)
        self.toast_overlay.set_child(self.toolbar_view)
        self.set_content(self.toast_overlay)

    def _wrap_page(self, widget: Gtk.Widget) -> Gtk.Widget:
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        outer = Gtk.Box()
        outer.set_margin_top(18)
        outer.set_margin_bottom(18)
        outer.set_margin_start(24)
        outer.set_margin_end(24)
        widget.set_hexpand(True)
        outer.append(widget)
        scroller.set_child(outer)
        return scroller

    def _build_document_page(self) -> Gtk.Widget:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(16)
        page.set_margin_bottom(8)
        page.set_margin_start(20)
        page.set_margin_end(20)
        self.file_info = FileInfoCard(_)
        page.append(self.file_info)
        self.field_toolbar = FieldToolbar(_, self.controller)
        page.append(self.field_toolbar)
        self.field_stack = Gtk.Stack()
        self.field_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.field_table = FieldTable(_, self.controller, self._commit_value)
        self.field_form = FieldForm(_, self.controller, self._commit_value)
        self.field_stack.add_named(self.field_table, "table")
        self.field_stack.add_named(self.field_form, "form")
        self.field_stack.set_vexpand(True)
        page.append(self.field_stack)
        return page

    def _install_shortcuts(self) -> None:
        install_shortcuts(
            self,
            {
                "<Control>o": self.open_dialog,
                "<Control><Shift>s": self.save_dialog,
                "<Control>z": self.undo,
                "<Control>y": self.redo,
                "<Control><Shift>z": self.redo,
                "<Control>f": self.focus_search,
                "<Control>l": self.toggle_log,
                "<Control>w": self.close,
            },
        )

    def _install_drop_target(self) -> None:
        install_drop_target(self, self.open_path, self._show_error)

    # --------------------------------------------------------------- events
    def _on_controller_event(self, reason: str) -> None:
        if reason in ("changes", "filters", "section", "view", "experimental", "preview", "undo"):
            self._schedule_refresh()
            return
        if reason == "document":
            self._refresh_all()
        elif reason == "saved":
            self._toast(
                _("save.success").format(
                    path=str(self.controller.last_saved.path) if self.controller.last_saved else ""
                )
            )
            self._refresh_all()
        elif reason == "apply":
            self.apply_panel.refresh()
        elif reason == "diff":
            self._refresh_all()

    def _schedule_refresh(self) -> None:
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True

        def refresh() -> bool:
            self._refresh_scheduled = False
            self._refresh_fields()
            self._refresh_status()
            self.header.refresh_actions()
            return False

        GLib.idle_add(refresh)

    def _refresh_all(self) -> None:
        snapshot = self.controller.snapshot
        if snapshot is None:
            self.stack.set_visible_child_name("empty")
            self.sidebar.update(self.controller)
        else:
            self.stack.set_visible_child_name("document")
            self.file_info.update(snapshot)
            self.sidebar.update(self.controller)
        self._refresh_fields()
        self._refresh_status()
        self.header.refresh_actions()
        if snapshot is not None:
            self.header.set_subtitle(_("app.warning_short"))
            self.set_title(_("app.window_title").format(name=snapshot.display_name))
        else:
            self.header.set_subtitle(_("app.warning_short"))
            self.set_title(_("app.title"))
        self.status_bar.refresh()

    def _refresh_fields(self) -> None:
        if self.controller.snapshot is None:
            return
        self.field_table.refresh()
        self.field_form.refresh()
        self.field_toolbar.refresh()
        self.field_stack.set_visible_child_name(
            "form" if self.controller.view_mode == "form" else "table"
        )

    def _refresh_status(self) -> None:
        self.status_bar.refresh()

    # -------------------------------------------------------------- actions
    def navigate(self, section: str) -> None:
        if self.controller.snapshot is None:
            self.stack.set_visible_child_name("empty")
            return
        if section == "log":
            self.open_log()
            return
        if section == "apply":
            self.stack.set_visible_child_name("apply")
            self.controller.set_section("apply")
            self.apply_panel.refresh()
            return
        if section == "diff":
            self.stack.set_visible_child_name("diff")
            self.controller.set_section("diff")
            return
        self.stack.set_visible_child_name("document")
        self.controller.set_section(section)

    def _on_search(self, text: str) -> None:
        self.controller.set_filter(query=text)

    def focus_search(self) -> None:
        self.header.search_entry.grab_focus()

    def undo(self) -> None:
        self.controller.undo()

    def redo(self) -> None:
        self.controller.redo()

    def reset_changes(self) -> None:
        self.controller.reset_changes()

    def _on_log_toggled(self, button: Gtk.ToggleButton) -> None:
        self.log_panel.set_expanded(button.get_active())

    def _on_log_expanded(self, panel: Gtk.Expander, _param: Any) -> None:
        self.status_bar.log_toggle.set_active(panel.get_expanded())

    def toggle_log(self) -> None:
        self.status_bar.log_toggle.set_active(not self.status_bar.log_toggle.get_active())

    def open_log(self) -> None:
        self.stack.set_visible_child_name("document")
        self.status_bar.log_toggle.set_active(True)
        self.log_panel.set_expanded(True)

    def show_shortcuts(self) -> None:
        show_shortcuts(self, _)

    def show_about(self) -> None:
        show_about(self, _)

    def enable_experimental(self) -> None:
        request_experimental_unlock(self, _, self.controller, on_done=self._refresh_all)

    def _commit_value(self, key: str, text: str) -> None:
        try:
            preview = self.controller.set_value(key, text)
        except ConfirmationRequired as need:
            self._confirm_t3(need)
            return
        except T3LockedError:
            self._show_error(
                _("edit.error.title"), DomainError("T3_LOCKED", _("t3.locked"), _("t3.locked.hint"))
            )
            self._schedule_refresh()
            return
        except DomainError as exc:
            self._show_error(_("edit.error.title"), exc)
            self._schedule_refresh()
            return
        if preview.errors:
            self._show_field_errors(preview)
        self._schedule_refresh()

    def _confirm_t3(self, need: ConfirmationRequired) -> None:
        body = _("t3.confirm.body").format(
            field=need.field.label,
            old=need.old if need.old is not None else "—",
            new=need.new,
            unit=need.field.unit,
        )

        def commit() -> None:
            try:
                preview = self.controller.set_value(need.field.key, need.new, t3_confirmed=True)
            except DomainError as exc:
                self._show_error(_("edit.error.title"), exc)
            else:
                if preview.errors:
                    self._show_field_errors(preview)
            self._refresh_all()

        dialog = ConfirmDialog(
            self,
            _("t3.confirm.title"),
            body,
            rules=ConfirmationRules(require_checkbox=True, required_word="CONFIRM"),
            confirm_label=_("t3.confirm.accept"),
            cancel_label=_("common.cancel"),
            checkbox_label=_("t3.confirm.checkbox"),
            word_label=_("t3.confirm.word"),
            on_confirm=commit,
            width=600,
        )
        dialog.connect("close-request", lambda _w: self._schedule_refresh())
        dialog.present()

    def _show_field_errors(self, preview: EditPreview) -> None:
        first: FieldError = preview.errors[0]
        self._show_error(
            _("edit.error.title"),
            DomainError(first.code, first.message, first.hint, {"field": first.key}),
        )

    # ------------------------------------------------------------- dialogs
    def open_dialog(self) -> None:
        self.dialogs.open_dialog()

    def open_path(self, path: Path) -> None:
        self.dialogs.open_path(path)

    def save_dialog(self) -> None:
        self.dialogs.save_dialog()

    def save_profile_dialog(self) -> None:
        self.dialogs.save_profile_dialog()

    def load_profile_dialog(self) -> None:
        self.dialogs.load_profile_dialog()

    def choose_diff_dialog(self) -> None:
        self.dialogs.choose_diff_dialog()

    # ------------------------------------------------------------- feedback
    def _show_error(self, title: str, exc: Exception) -> None:
        dialog = ErrorDialog.from_exception(self, title, exc, _)
        dialog.present()

    def _toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast.new(message))

    def retranslate(self, translate: Callable[[str], str] = _) -> None:
        """Refresh every static label after a runtime language switch."""
        self.header.retranslate(translate)
        self.sidebar.retranslate(translate)
        self.field_toolbar.retranslate(translate)
        self.status_bar.retranslate(translate)
        self.log_panel.retranslate(translate)
        self.field_table.retranslate(translate)
        self.field_form.retranslate(translate)
        self.diff_view.retranslate(translate)
        self.apply_panel.retranslate(translate)
        if self.controller.snapshot is not None:
            self.file_info.retranslate(translate)
        self._refresh_all()
