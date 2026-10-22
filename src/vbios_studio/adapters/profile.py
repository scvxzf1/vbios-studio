"""Production ``ProfilePort`` adapter for JSON presets.

The adapter is intentionally a thin layer over ``EditorPort``: export uses the
already-validated ``FieldChange`` records, while import performs the schema and
architecture checks and hands the complete change set to ``EditorPort.stage``
once. The editor performs all field/bounds validation before mutating state, so
a bad preset is rejected without partial writes.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from vbios_studio.domain.errors import NOT_OPENED, DomainError
from vbios_studio.domain.models import EditPreview
from vbios_studio.domain.risk import max_risk

from .upstream import UpstreamEditorAdapter

SCHEMA_VERSION = 1


class UpstreamProfileAdapter:
    """``ProfilePort`` implementation backed by the open upstream editor."""

    def __init__(self, editor: UpstreamEditorAdapter) -> None:
        self._editor = editor

    def _document(self) -> Any:
        document = getattr(self._editor, "_document", None)
        if document is None:
            raise DomainError(NOT_OPENED, "open a ROM before using a profile", "call open() first")
        return document

    def export_changes(self) -> dict[str, Any]:
        """Serialize the staged changes with schema, architecture and risk metadata."""
        document = self._document()
        preview = self._editor.preview()
        changes = {change.key: change.new for change in preview.changes}
        fields = [
            {
                "key": change.key,
                "label": change.label,
                "old": change.old,
                "new": change.new,
                "unit": change.unit,
                "risk": change.risk,
            }
            for change in preview.changes
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "tool": "vbios-studio",
            "architecture": document.architecture,
            "format": document.architecture,
            "source_sha256": document.sha256,
            "changes": changes,
            "fields": fields,
            "risks": {change.key: change.risk for change in preview.changes},
            "batch_risk": max_risk([change.risk for change in preview.changes]),
        }

    def apply_profile(self, document: Mapping[str, Any]) -> EditPreview:
        """Validate a preset atomically and stage all of its changes at once."""
        if not isinstance(document, Mapping) or document.get("schema_version") != SCHEMA_VERSION:
            raise DomainError(
                "PROFILE_SCHEMA",
                "Unsupported preset schema.",
                "Use a profile with schema_version 1.",
            )
        current = self._document()
        architecture = document.get("architecture")
        if not isinstance(architecture, str) or architecture != current.architecture:
            raise DomainError(
                "PROFILE_ARCH_MISMATCH",
                "Preset architecture does not match the open ROM.",
                "Use a preset exported for this architecture.",
            )
        profile_format = document.get("format")
        if profile_format is not None and profile_format != current.architecture:
            raise DomainError(
                "PROFILE_ARCH_MISMATCH",
                "Preset format does not match the open ROM.",
                "Use a preset exported for this architecture.",
            )
        changes = document.get("changes")
        if not isinstance(changes, Mapping):
            raise DomainError(
                "PROFILE_SCHEMA", "Preset changes must be an object.", "Fix the preset."
            )
        normalized: dict[str, str] = {}
        for key, value in changes.items():
            if not isinstance(key, str) or isinstance(value, (Mapping, list, tuple)):
                raise DomainError(
                    "PROFILE_SCHEMA",
                    "Preset changes must map field names to values.",
                    "Fix the preset.",
                )
            normalized[key] = str(value)
        return self._editor.stage(normalized)
