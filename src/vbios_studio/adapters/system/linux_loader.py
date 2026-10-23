"""Linux loader probe and copyable guidance.

The external ``nvidia-linux-vbios-vix-loader`` performs boot-time injection.
VBIOS Studio only detects it and prints instructions: this module never runs
the loader, never elevates privileges and never writes system files.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import ApplyPreview, ApplyResult, DeviceStatus, OverrideState
from vbios_studio.ports.apply import Operation

LOADER_EXECUTABLE = "nvidia-linux-vbios-vix-loader"
COMMON_PATHS = (
    "/usr/local/bin/nvidia-linux-vbios-vix-loader",
    "/usr/bin/nvidia-linux-vbios-vix-loader",
    "/opt/nvidia-linux-vbios-vix-loader/nvidia-linux-vbios-vix-loader",
)


@dataclass(frozen=True, slots=True)
class LoaderProbe:
    """Result of a read-only loader discovery."""

    found: bool
    path: str | None
    executable: bool
    search_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible probe."""
        return {
            "found": self.found,
            "path": self.path,
            "executable": self.executable,
            "search_paths": list(self.search_paths),
        }


class LinuxLoaderAdapter:
    """Find the external loader and prepare copyable installation guidance."""

    def __init__(
        self,
        *,
        which: Callable[[str], str | None] | None = None,
        search_paths: Sequence[str] = COMMON_PATHS,
        executable: Callable[[str], bool] | None = None,
    ) -> None:
        self._which = which or shutil.which
        self._search_paths = tuple(search_paths)
        self._executable = executable or (lambda path: os.access(path, os.X_OK))
        self._payload: bytes | None = None
        self._payload_path: Path | None = None

    def find_loader(self) -> str | None:
        """Return the loader path when installed and executable, otherwise ``None``."""
        candidates = [self._which(LOADER_EXECUTABLE), *self._search_paths]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate)
            if path.is_file() and self._executable(str(path)):
                return str(path)
        return None

    def probe(self) -> LoaderProbe:
        """Return a read-only discovery record for diagnostics."""
        path = self.find_loader()
        return LoaderProbe(path is not None, path, path is not None, self._search_paths)

    def guidance(self, payload_path: str) -> str:
        """Return copyable manual instructions; no command is executed here."""
        payload = Path(payload_path)
        discovered = self.find_loader()
        loader = discovered or LOADER_EXECUTABLE
        status = "detected" if discovered else "not found in PATH or common locations"
        return (
            "Linux loader override guidance\n"
            f"1. Loader status: {status}.\n"
            f"2. Keep the generated payload at: {payload}\n"
            "3. Install the external project from "
            "https://github.com/Panchovix/nvidia-linux-vbios-vix-loader and follow its README.\n"
            f"4. Point the loader configuration at the payload and run it manually: "
            f"{loader} --help\n"
            "5. Reboot after configuring it and verify the active VBIOS with the loader's "
            "status command.\n"
            "VBIOS Studio does not run the loader, does not request root and does not modify "
            "system files."
        )

    def prepare(self, payload_path: str) -> dict[str, object]:
        """Return a structured probe plus guidance for the apply panel."""
        probe = self.probe()
        return {
            "loader": probe.to_dict(),
            "payload": str(Path(payload_path)),
            "guidance": self.guidance(payload_path),
            "manual_only": True,
        }

    # ------------------------------------------------------------- ApplyPort
    def configure_payload(self, payload: bytes, *, source: Path | None = None) -> None:
        """Store the saved payload for guidance and verification."""
        self._payload = bytes(payload)
        self._payload_path = Path(source) if source is not None else None

    def describe_operations(self, action: Literal["load", "restore"]) -> tuple[Operation, ...]:
        """Linux never writes registry values; there are no operations."""
        if action not in ("load", "restore"):
            raise DomainError(
                "INVALID_ACTION", f"Unsupported apply action: {action}", "Use load or restore."
            )
        return ()

    def device_status(self) -> DeviceStatus:
        """Return a read-only loader detection record, never a fake GPU."""
        probe = self.probe()
        state: OverrideState = "no-override" if probe.found else "unknown"
        return DeviceStatus(0, "Linux loader (manual)", "", None, state, False)

    def dry_run(self) -> ApplyPreview:
        """Return copyable guidance; this adapter never writes system files."""
        if self._payload is None:
            return ApplyPreview(
                "load", "", {"error": "no payload configured"}, 0, False, ("Save a payload first.",)
            )
        path = str(self._payload_path) if self._payload_path is not None else "<saved payload>"
        guidance = self.guidance(path)
        return ApplyPreview(
            "load",
            "nvidia-linux-vbios-vix-loader",
            {"guidance": guidance, "manual_only": True, "payload_size": len(self._payload)},
            len(self._payload),
            False,
            ("Manual installation is required; VBIOS Studio will not run the loader.",),
        )

    def execute(self) -> ApplyResult:
        """Refuse execution: Linux injection is intentionally manual-only."""
        guidance = self.guidance(str(self._payload_path or "<saved payload>"))
        return ApplyResult(
            False,
            "manual-only",
            "Linux loader execution is manual-only; follow the exported guidance.",
            {"code": "MANUAL_ONLY", "guidance": guidance},
        )

    def restore(self) -> ApplyResult:
        """Refuse automatic restore; the external loader owns that operation."""
        return ApplyResult(
            False,
            "manual-only",
            "Restore is managed by the external Linux loader; follow its documentation.",
            {"code": "MANUAL_ONLY"},
        )

    def verify(self, running_image: bytes | None = None) -> ApplyResult:
        """Compare an explicitly supplied running image; no system read is attempted."""
        if self._payload is None:
            return ApplyResult(
                False, "unknown", "No payload is configured for comparison.", {"code": "NO_PAYLOAD"}
            )
        if running_image is None:
            return ApplyResult(
                False,
                "unknown",
                "Running image comparison is unavailable in the Linux manual path.",
                {"code": "VERIFY_UNAVAILABLE", "hint": "Use the loader's status command."},
            )
        if running_image == self._payload:
            return ApplyResult(
                True, "override-active", "Supplied running image matches the saved payload.", {}
            )
        return ApplyResult(
            False, "override-not-active", "Supplied running image differs from saved payload.", {}
        )

    def run(self) -> None:
        """The adapter intentionally has no execution path."""
        raise RuntimeError("LinuxLoaderAdapter never executes the external loader; use guidance()")
