"""Editing port: open a ROM, stage changes, preview, save and reset."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from vbios_studio.domain.models import (
    DocumentSnapshot,
    EditPreview,
    ManifestView,
    SaveResult,
)


class EditorPort(Protocol):
    """The UI's only handle on a loaded ROM and its staged changes.

    Implementations live in ``vbios_studio.adapters`` (t3 bridges the upstream
    editor). Every ``stage`` call must return a domain-validated
    :class:`~vbios_studio.domain.models.EditPreview`; the UI never validates
    values itself.
    """

    def open(self, path: Path) -> DocumentSnapshot:
        """Load a ROM read-only and return its immutable snapshot."""

    def stage(self, changes: Mapping[str, str]) -> EditPreview:
        """Stage textual field values and return the validated preview."""

    def preview(self) -> ManifestView:
        """Return the manifest that would be written by the next save."""

    def save_as(self, path: Path) -> SaveResult:
        """Write a new ROM, payloads and manifest without touching the source."""

    def reset(self) -> None:
        """Discard every staged change while keeping the document open."""
