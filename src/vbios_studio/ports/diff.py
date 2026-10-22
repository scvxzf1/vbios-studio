"""Diff port: compare the open document with another ROM."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from vbios_studio.domain.models import RomDiff


class DiffPort(Protocol):
    """Read-only, field-level and image-level ROM comparison."""

    def diff_against(self, path: Path) -> RomDiff:
        """Compare the open document with the ROM at ``path``."""
