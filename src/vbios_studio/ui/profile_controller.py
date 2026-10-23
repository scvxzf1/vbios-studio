"""Profile export/apply mixin: the batch path honours the same T3 gate."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import (
    DocumentSnapshot,
    EditPreview,
    FieldChange,
    FieldSnapshot,
)
from vbios_studio.ports.profile import ProfilePort
from vbios_studio.ui.controller_errors import ConfirmationRequired


class ProfileControllerMixin:
    """Methods mixed into ``UiController`` so the batch path cannot bypass T3."""

    profile_port: ProfilePort | None
    snapshot: DocumentSnapshot | None
    changes: dict[str, str]
    preview: EditPreview | None
    experimental_unlocked: bool
    _undo: list[dict[str, str]]
    _redo: list[dict[str, str]]
    find_field: Callable[[str], FieldSnapshot | None]
    _push_undo: Callable[[Mapping[str, str]], None]
    log: Callable[..., None]
    _notify: Callable[[str], None]

    def export_profile(self) -> dict[str, Any]:
        if self.profile_port is None:
            raise DomainError(
                "PROFILE_UNAVAILABLE", "Presets are not available.", "Check the installation."
            )
        return self.profile_port.export_changes()

    def _profile_t3_fields(self, document: Mapping[str, Any]) -> tuple[FieldSnapshot, ...]:
        """Return T3 fields in a profile, using the open document's risk registry."""
        changes = document.get("changes")
        if not isinstance(changes, Mapping):
            return ()
        fields: list[FieldSnapshot] = []
        for key in changes:
            field = self.find_field(str(key))
            if field is not None and field.risk == "T3":
                fields.append(field)
        return tuple(fields)

    def apply_profile(
        self,
        document: Mapping[str, Any],
        *,
        confirmed_t3: Iterable[str] = (),
    ) -> EditPreview:
        """Apply a preset only after the same T3 gate as single-field edits.

        The profile adapter is not called until every T3 key has a ticket, so a
        rejected/cancelled dialog leaves both ``changes`` and the editor untouched.
        """
        if self.profile_port is None:
            raise DomainError(
                "PROFILE_UNAVAILABLE", "Presets are not available.", "Check the installation."
            )
        t3_fields = self._profile_t3_fields(document)
        tickets = set(confirmed_t3)
        if t3_fields:
            missing = [field for field in t3_fields if field.key not in tickets]
            if not self.experimental_unlocked or missing:
                first = missing[0] if missing else t3_fields[0]
                changes = document.get("changes")
                new = changes.get(first.key, "") if isinstance(changes, Mapping) else ""
                raise ConfirmationRequired(
                    first,
                    first.current,
                    str(new),
                    fields=tuple(missing or t3_fields),
                )
        previous = dict(self.changes)
        preview = self.profile_port.apply_profile(document)
        self.preview = preview
        if preview.errors:
            return preview
        self.changes = {change.key: change.new for change in preview.changed}
        if self.changes != previous:
            self._push_undo(previous)
            self._redo.clear()
        self.log(f"Applied preset ({len(self.changes)} changes)")
        self._notify("changes")
        return preview

    def changed_fields(self) -> list[FieldChange]:
        if self.preview is None:
            return []
        return list(self.preview.changed)

    def batch_risk(self) -> str:
        if self.preview is None:
            return "T0"
        return self.preview.batch_risk
