"""Structured domain errors shared by every layer.

Callers must not build user-facing validation text in the UI: raise a
``DomainError`` with a stable ``code`` and let the presentation layer
translate the code. ``message`` and ``hint`` are English diagnostics for logs
and developer-facing output.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PROFILE_ARCH_MISMATCH = "PROFILE_ARCH_MISMATCH"
OUTPUT_EXISTS = "OUTPUT_EXISTS"
SOURCE_AS_OUTPUT = "SOURCE_AS_OUTPUT"
REFUSE_MODIFIED_IMAGE = "REFUSE_MODIFIED_IMAGE"
REFUSE_BAD_CHECKSUM = "REFUSE_BAD_CHECKSUM"
NVFLASH_NOT_FOUND = "NVFLASH_NOT_FOUND"
ELEVATION_REQUIRED = "ELEVATION_REQUIRED"
UNSUPPORTED_ARCHITECTURE = "UNSUPPORTED_ARCHITECTURE"
FIELD_OUT_OF_BOUNDS = "FIELD_OUT_OF_BOUNDS"
DEPENDENT_FIELD_DISABLED = "DEPENDENT_FIELD_DISABLED"
NOT_OPENED = "NOT_OPENED"
UNKNOWN_FIELD = "UNKNOWN_FIELD"
FIELD_READ_ONLY = "FIELD_READ_ONLY"
INVALID_VALUE = "INVALID_VALUE"
NO_CHANGES = "NO_CHANGES"
STRUCTURE_INVALID = "STRUCTURE_INVALID"
CHECKSUM_UNBALANCED = "CHECKSUM_UNBALANCED"
CROSS_IMAGE_EDIT = "CROSS_IMAGE_EDIT"
CHECKSUM_OVERLAP = "CHECKSUM_OVERLAP"
OVERLAPPING_EDITS = "OVERLAPPING_EDITS"
SOURCE_CHANGED = "SOURCE_CHANGED"
IO_ERROR = "IO_ERROR"
INTEGRITY_FAILED = "INTEGRITY_FAILED"
OUT_OF_BOUNDS = "OUT_OF_BOUNDS"


class DomainError(Exception):
    """A stable, structured error raised by domain, ports or adapters."""

    code: str
    message: str
    hint: str
    details: Mapping[str, Any]

    def __init__(
        self,
        code: str,
        message: str,
        hint: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation for CLI and logs."""
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "details": dict(self.details),
        }

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
