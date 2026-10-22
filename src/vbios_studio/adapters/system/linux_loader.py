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

    def run(self) -> None:
        """The adapter intentionally has no execution path."""
        raise RuntimeError("LinuxLoaderAdapter never executes the external loader; use guidance()")
