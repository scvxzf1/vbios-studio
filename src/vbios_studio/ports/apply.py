"""Apply port: query device state and perform controlled load/unload/flash."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from vbios_studio.domain.models import ApplyPreview, ApplyResult, DeviceStatus


@dataclass(frozen=True, slots=True)
class Operation:
    """One registry operation that an apply action will perform.

    ``source`` is a stable description of where the value comes from:
    ``payload``, ``previous``, ``backup``, ``constant`` or ``legacy``.  The
    UI uses this list as the sole confirmation text source; it must be produced
    by the same plan builder as the actual write.
    """

    op: Literal["set", "delete"]
    name: str
    source: str


ApplyAction = Literal["load", "restore"]
ApplyOperation = Operation


class ApplyPort(Protocol):
    """System-level apply operations; all writes require a prior dry-run.

    ``configure_payload`` is called by the application controller after a
    successful save so the adapter knows the exact bytes the session produced.
    ``verify`` is read-only and compares the driver's running image with the
    stored override when the platform exposes a readback reader.
    """

    def configure_payload(self, payload: bytes, *, source: Path | None = None) -> None:
        """Attach the saved loader payload to this apply session."""

    def device_status(self) -> DeviceStatus:
        """Return the selected GPU, driver version and override state."""

    def describe_operations(self, action: ApplyAction) -> tuple[Operation, ...]:
        """Return the exact operations the action will perform, read-only."""

    def dry_run(self) -> ApplyPreview:
        """Describe the planned write without touching the system and issue a one-shot ticket."""

    def execute(self) -> ApplyResult:
        """Perform the planned write only with a valid dry-run ticket."""

    def restore(self) -> ApplyResult:
        """Remove the override / restore the previous driver state."""

    def verify(self, running_image: bytes | None = None) -> ApplyResult:
        """Compare the stored override with the running image (read-only)."""
