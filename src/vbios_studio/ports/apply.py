"""Apply port: query device state and perform controlled load/unload/flash."""

from __future__ import annotations

from typing import Protocol

from vbios_studio.domain.models import ApplyPreview, ApplyResult, DeviceStatus


class ApplyPort(Protocol):
    """System-level apply operations; all writes require a prior dry-run."""

    def device_status(self) -> DeviceStatus:
        """Return the selected GPU, driver version and override state."""

    def dry_run(self) -> ApplyPreview:
        """Describe the planned write without touching the system."""

    def execute(self) -> ApplyResult:
        """Perform the planned load/unload/flash action after confirmation."""

    def restore(self) -> ApplyResult:
        """Remove the override / restore the previous driver state."""
