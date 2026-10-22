"""Profile port: export staged changes and apply a saved profile."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from vbios_studio.domain.models import EditPreview


class ProfilePort(Protocol):
    """JSON profile import/export with all-or-nothing validation."""

    def export_changes(self) -> dict[str, Any]:
        """Serialize the current staged changes with schema and risk metadata."""

    def apply_profile(self, document: Mapping[str, Any]) -> EditPreview:
        """Apply a profile atomically or raise ``DomainError`` without changes."""
