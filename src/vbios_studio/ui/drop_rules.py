"""Validation rules for a drag-and-drop payload (GTK-free and unit-testable)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


class DropError(Exception):
    """A rejected drop; ``code`` is stable for the error dialog and tests."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def validate_drop(paths: Sequence[Path], *, is_directory: Sequence[bool] | None = None) -> Path:
    """Return the one accepted file or raise :class:`DropError`.

    Codes: ``DROP_EMPTY``, ``DROP_NOT_A_FILE`` (a folder), ``DROP_MULTIPLE_FILES``.
    ROM recognition itself belongs to the domain and happens in ``EditorPort.open``.
    """
    if not paths:
        raise DropError("DROP_EMPTY", "No file was dropped.", "Drop one .rom or .bin file.")
    if len(paths) > 1:
        raise DropError(
            "DROP_MULTIPLE_FILES",
            f"Drop exactly one file, not {len(paths)}.",
            "Close the other files and try again.",
        )
    path = Path(paths[0])
    if is_directory is not None and len(is_directory) == 1 and is_directory[0]:
        raise DropError(
            "DROP_NOT_A_FILE",
            "A folder cannot be opened as a VBIOS image.",
            "Choose a .rom or .bin file.",
        )
    return path
