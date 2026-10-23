"""Shared controller exceptions for T3 edits and profile application."""

from __future__ import annotations

from vbios_studio.domain.models import FieldSnapshot


class ConfirmationRequired(Exception):  # noqa: N818
    """Raised when T3 fields need an explicit second confirmation.

    ``fields`` carries every T3 field still awaiting a ticket; profile apply can
    therefore ask for each field in turn without staging anything first.
    """

    def __init__(
        self,
        field: FieldSnapshot,
        old: str | None,
        new: str,
        *,
        fields: tuple[FieldSnapshot, ...] | None = None,
    ) -> None:
        super().__init__(f"confirmation required for {field.key}")
        self.field = field
        self.old = old
        self.new = new
        self.fields = fields if fields is not None else (field,)


class T3LockedError(Exception):
    """Raised when a caller tries to edit a T3 field before unlocking experimental mode."""
