"""Per-field T3 confirmation flow for preset application.

A preset is a batch, but the frozen risk model forbids batch bypass: every T3
key in the preset must receive its own confirmation dialog before the profile
adapter is allowed to stage anything.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSet
from typing import TYPE_CHECKING, Any

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import EditPreview, FieldSnapshot
from vbios_studio.i18n import gettext as _
from vbios_studio.ui.controller import ConfirmationRequired
from vbios_studio.ui.dialogs.confirm_dialog import (
    T3_CONFIRM_WORD,
    ConfirmationRules,
    ConfirmDialog,
)

if TYPE_CHECKING:
    from vbios_studio.ui.main_window import MainWindow


def uncovered_change_keys(
    existing: Mapping[str, str], document: Mapping[str, Any]
) -> tuple[str, ...]:
    """Keys whose staged values would be silently discarded by this preset."""
    if not existing:
        return ()
    changes = document.get("changes")
    if not isinstance(changes, Mapping):
        return tuple(existing)
    return tuple(key for key in existing if key not in changes)


class ProfileFlow:
    """Drive the preset load through the same gate as a single T3 edit."""

    def __init__(self, window: MainWindow) -> None:
        self.window = window

    def apply_document(self, document: Mapping[str, Any]) -> None:
        uncovered = uncovered_change_keys(self.window.controller.changes, document)
        if uncovered:
            self._confirm_replace(document, uncovered)
            return
        self._start(document)

    def _confirm_replace(self, document: Mapping[str, Any], uncovered: tuple[str, ...]) -> None:
        body = _("status.unsaved").format(count=len(self.window.controller.changes))
        body += "\n" + ", ".join(uncovered) + "\n\n" + _("apply.confirm.body")

        def proceed() -> None:
            self._start(document)

        dialog = ConfirmDialog(
            self.window,
            _("edit.reset"),
            body,
            rules=ConfirmationRules(require_checkbox=False),
            confirm_label=_("common.confirm"),
            cancel_label=_("common.cancel"),
            on_confirm=proceed,
            width=560,
        )
        dialog.present()

    def _start(self, document: Mapping[str, Any]) -> None:
        try:
            preview = self.window.controller.apply_profile(document)
        except ConfirmationRequired as need:
            self._ask(document, list(need.fields), set())
            return
        except DomainError as exc:
            self.window._show_error(_("profile.error.title"), exc)
            return
        self.finish(preview)

    def _ask(
        self,
        document: Mapping[str, Any],
        pending: list[FieldSnapshot],
        confirmed: MutableSet[str],
    ) -> None:
        if not pending:
            try:
                preview = self.window.controller.apply_profile(document, confirmed_t3=confirmed)
            except ConfirmationRequired as need:
                missing = [field for field in need.fields if field.key not in confirmed]
                if not missing:
                    self.window._show_error(
                        _("profile.error.title"),
                        DomainError(
                            "PROFILE_T3_UNCONFIRMED",
                            "The preset still requires an unconfirmed T3 field.",
                            "Retry the preset and confirm every T3 field.",
                        ),
                    )
                    self.window._refresh_all()
                    return
                self._ask(document, missing, confirmed)
                return
            except DomainError as exc:
                self.window._show_error(_("profile.error.title"), exc)
                return
            self.finish(preview)
            return

        field = pending.pop(0)
        changes = document.get("changes")
        new = str(changes.get(field.key, "")) if isinstance(changes, Mapping) else ""
        body = _("t3.confirm.body").format(
            field=field.label,
            key=field.key,
            old=field.current if field.current is not None else "—",
            new=new,
            unit=field.unit,
        )

        def commit() -> None:
            confirmed.add(field.key)
            self._ask(document, pending, confirmed)

        dialog = ConfirmDialog(
            self.window,
            _("t3.confirm.title"),
            body,
            rules=ConfirmationRules(
                require_checkbox=True,
                allowed_words=(field.key, T3_CONFIRM_WORD),
            ),
            confirm_label=_("t3.confirm.accept"),
            cancel_label=_("common.cancel"),
            checkbox_label=_("t3.confirm.checkbox"),
            word_label=_("t3.confirm.word"),
            on_confirm=commit,
            width=600,
        )
        dialog.connect("close-request", lambda _w: self.window._refresh_all())
        dialog.present()

    def finish(self, preview: EditPreview) -> None:
        if preview.errors:
            self.window._show_field_errors(preview)
            self.window._refresh_all()
            return
        self.window._toast(_("profile.applied"))
        self.window._refresh_all()


def confirm_single_edit(window: MainWindow, need: ConfirmationRequired) -> None:
    """Show the per-field T3 dialog and replay the edit with a ticket."""
    body = _("t3.confirm.body").format(
        field=need.field.label,
        key=need.field.key,
        old=need.old if need.old is not None else "—",
        new=need.new,
        unit=need.field.unit,
    )

    def commit() -> None:
        try:
            preview = window.controller.set_value(need.field.key, need.new, t3_confirmed=True)
        except DomainError as exc:
            window._show_error(_("edit.error.title"), exc)
        else:
            if preview.errors:
                window._show_field_errors(preview)
        window._refresh_all()

    dialog = ConfirmDialog(
        window,
        _("t3.confirm.title"),
        body,
        rules=ConfirmationRules(
            require_checkbox=True,
            allowed_words=(need.field.key, T3_CONFIRM_WORD),
        ),
        confirm_label=_("t3.confirm.accept"),
        cancel_label=_("common.cancel"),
        checkbox_label=_("t3.confirm.checkbox"),
        word_label=_("t3.confirm.word"),
        on_confirm=commit,
        width=600,
    )
    dialog.connect("close-request", lambda _w: window._refresh_all())
    dialog.present()
