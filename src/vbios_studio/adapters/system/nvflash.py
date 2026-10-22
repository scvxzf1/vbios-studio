"""Hard guard for the nvflash write channel.

Only a pristine, byte-identical original image with balanced per-image checksums
may reach nvflash. A modified image is always refused: its vendor signature is
stale and writing it can brick the card. The guard itself never launches a
process; :meth:`NvflashGuard.flash` performs the single reviewed command only
after every check passes and under an injected runner with list arguments.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vbios_studio.domain.errors import (
    CHECKSUM_UNBALANCED,
    ELEVATION_REQUIRED,
    NVFLASH_NOT_FOUND,
    REFUSE_MODIFIED_IMAGE,
)
from vbios_studio.domain.models import ApplyResult
from vbios_studio.domain.rom import RomStructure, scan_rom

from ._base import CommandResult, CommandRunner, SubprocessRunner

ALLOWED_NVFLASH_VERSIONS = ("5.821", "5.842", "5.867", "5.1000")
FLASH_CONFIRMATION_PREFIX = "FLASH ORIGINAL"
FORBIDDEN_FLAGS = ("--protectoff", "--erase", "--force", "--no-preserve")
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FlashDecision:
    """Result of the frozen nvflash safety checks."""

    allowed: bool
    code: str
    message: str
    hint: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)


def _default_elevated() -> bool:
    return bool(getattr(os, "geteuid", lambda: -1)() == 0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as one, right.open("rb") as two:
        while True:
            a, b = one.read(1024 * 1024), two.read(1024 * 1024)
            if a != b:
                return False
            if not a:
                return True


def _pci_id(text: str) -> tuple[int, int] | None:
    vendor, separator, device = text.strip().partition(":")
    if not separator:
        return None
    try:
        return int(vendor, 16), int(device, 16)
    except ValueError:
        return None


def _structure_problem(structure: RomStructure) -> tuple[str, str] | None:
    if not structure.images:
        return "STRUCTURE_INVALID", "No PCI/NPDS image was found."
    for image in structure.images:
        if not image.checksum_ok:
            return (
                CHECKSUM_UNBALANCED,
                f"Image {image.index} at offset 0x{image.offset:x} has 8-bit checksum "
                f"0x{image.checksum:02x} (expected 0x00).",
            )
    if structure.issues:
        return "STRUCTURE_INVALID", f"Image structure is invalid: {structure.issues[0].message}"
    if structure.chains != 1:
        return "STRUCTURE_INVALID", "The ROM contains duplicate banks; refuse an ambiguous image."
    first, last = structure.images[0], structure.images[-1]
    if first.kind != "legacy":
        return "STRUCTURE_INVALID", "The image chain does not start with a legacy PCIR image."
    if not last.is_last:
        return "STRUCTURE_INVALID", "The image chain has no last-image flag."
    return None


class NvflashGuard:
    """Validate a candidate image before an nvflash write.

    ``check`` is a pure inspection method: it never launches a process. Tests
    and callers use it to obtain a structured refusal; :meth:`flash` is the only
    method that can run ``nvflash`` and only after ``check`` returns allowed.
    """

    def __init__(
        self,
        *,
        allow_flash: bool = False,
        runner: CommandRunner | None = None,
        nvflash_path: str | None = None,
        nvflash_version: str | None = None,
        is_elevated: bool | None = None,
        allowed_versions: tuple[str, ...] = ALLOWED_NVFLASH_VERSIONS,
    ) -> None:
        self.allow_flash = allow_flash
        self.runner = runner or SubprocessRunner()
        self.nvflash_path = nvflash_path
        self.nvflash_version = nvflash_version
        self.is_elevated = is_elevated
        self.allowed_versions = allowed_versions

    def _refuse(self, code: str, message: str, hint: str = "", **details: Any) -> FlashDecision:
        return FlashDecision(False, code, message, hint, details)

    def check(
        self,
        candidate: str,
        pristine_original: str,
        expected_sha256: str,
        device_pci_id: str,
        nvflash_path: str | None = None,
        *,
        session_modified: bool = False,
        confirmation: str = "",
        backup_confirmed: bool = False,
        understand_risk: bool = False,
        nvflash_version: str | None = None,
    ) -> FlashDecision:
        """Run every frozen guard check without launching a process."""
        if not self.allow_flash or not understand_risk:
            return self._refuse(
                "FLASH_DISABLED",
                "The nvflash channel is disabled; it needs an explicit opt-in and "
                "risk acknowledgement.",
                "Enable the flash channel explicitly and acknowledge the risk.",
            )
        candidate_path, original_path = Path(candidate), Path(pristine_original)
        if candidate_path.is_symlink() or not candidate_path.is_file():
            return self._refuse(
                "CANDIDATE_INVALID",
                "The candidate is not a regular file.",
                "Choose a normal ROM file.",
            )
        if original_path.is_symlink() or not original_path.is_file():
            return self._refuse(
                "CANDIDATE_INVALID",
                "The pristine original is not a regular file.",
                "Reopen the original ROM.",
            )
        expected = expected_sha256.strip().lower()
        try:
            actual = _sha256(candidate_path)
            identical = _same_bytes(candidate_path, original_path)
        except OSError as exc:
            return self._refuse(
                "CANDIDATE_INVALID",
                f"Cannot read the candidate or original: {exc}",
                "Check file permissions and retry.",
            )
        if not identical:
            return self._refuse(
                REFUSE_MODIFIED_IMAGE,
                "The candidate differs from the pristine original; modified images must "
                "never be flashed.",
                "Apply modified images through the Windows registry or Linux loader override "
                "instead.",
                rule="CANDIDATE_MODIFIED",
            )
        if actual != expected:
            return self._refuse(
                "CANDIDATE_HASH_MISMATCH",
                "The candidate SHA-256 differs from the session's original SHA-256.",
                "Reopen the original ROM and do not flash a replaced file.",
                expected=expected,
                actual=actual,
            )
        if session_modified:
            return self._refuse(
                "SESSION_MODIFIED",
                "The editing session has staged changes; only a pristine original may be flashed.",
                "Use the loader path for modified images.",
            )
        try:
            blob = candidate_path.read_bytes()
        except OSError as exc:
            return self._refuse(
                "CANDIDATE_INVALID", f"Cannot read the candidate: {exc}", "Check file permissions."
            )
        structure = scan_rom(blob)
        problem = _structure_problem(structure)
        if problem is not None:
            code, message = problem
            details: dict[str, Any] = {}
            if code == CHECKSUM_UNBALANCED:
                bad = next(image for image in structure.images if not image.checksum_ok)
                details = {"image_index": bad.index, "checksum": bad.checksum}
            return self._refuse(
                code, message, "Use a complete, balanced, single-bank original ROM.", **details
            )
        expected_device = _pci_id(device_pci_id)
        first = structure.images[0]
        if expected_device is None or (first.vendor, first.device) != expected_device:
            return self._refuse(
                "DEVICE_MISMATCH",
                "The candidate PCI identity does not match the target GPU.",
                "Select the GPU that matches this ROM before flashing.",
                expected=device_pci_id,
                actual=f"{first.vendor:04x}:{first.device:04x}",
            )
        path, error = self._resolve_nvflash(nvflash_path)
        if error is not None:
            return error
        version = nvflash_version or self.nvflash_version
        if version is None or not any(
            str(version).startswith(item) for item in self.allowed_versions
        ):
            return self._refuse(
                "NVFLASH_VERSION_UNSUPPORTED",
                f"nvflash version {version!r} is not in the reviewed allow-list.",
                "Install a reviewed nvflash version or update the allow-list after review.",
            )
        elevated = self.is_elevated if self.is_elevated is not None else _default_elevated()
        if not elevated:
            return self._refuse(
                ELEVATION_REQUIRED,
                "Administrator/root rights are required before launching nvflash.",
                "Run the flash from an elevated shell.",
            )
        expected_word = f"{FLASH_CONFIRMATION_PREFIX} {expected[:8]}"
        if not backup_confirmed or confirmation.strip().lower() != expected_word.lower():
            return self._refuse(
                "CONFIRMATION_REQUIRED",
                "The backup acknowledgement and confirmation word are required.",
                f"Check the backup box and type: {expected_word}",
            )
        if _sha256(candidate_path) != expected:
            return self._refuse(
                "RACE_DETECTED",
                "The candidate changed after the checks.",
                "Retry from a pristine file.",
            )
        return FlashDecision(
            True,
            "ALLOWED",
            "All frozen nvflash checks passed.",
            "",
            {"nvflash": str(path), "version": version, "sha256": expected},
        )

    def _resolve_nvflash(self, override: str | None) -> tuple[Path | None, FlashDecision | None]:
        raw = override or self.nvflash_path
        path = Path(raw) if raw else None
        if path is None:
            found = shutil.which("nvflash")
            path = Path(found) if found else None
        if path is None or path.is_symlink() or not path.is_file() or not os.access(path, os.X_OK):
            return None, self._refuse(
                NVFLASH_NOT_FOUND,
                "nvflash was not found or is not an executable regular file.",
                "Install nvflash and verify its path before using the flash channel.",
            )
        return path, None

    def flash(
        self,
        candidate: str,
        pristine_original: str,
        expected_sha256: str,
        device_pci_id: str,
        **options: Any,
    ) -> ApplyResult:
        """Run the single reviewed nvflash write command after all checks."""
        options.setdefault("understand_risk", True)
        decision = self.check(
            candidate, pristine_original, expected_sha256, device_pci_id, **options
        )
        if not decision.allowed:
            return ApplyResult(
                False, "refused", decision.message, {"code": decision.code, "hint": decision.hint}
            )
        command = [str(decision.details["nvflash"]), "--write", str(candidate)]
        if any(flag in command for flag in FORBIDDEN_FLAGS):
            return ApplyResult(
                False,
                "refused",
                "A forbidden nvflash flag was requested.",
                {"code": "FORBIDDEN_FLAG"},
            )
        try:
            result: CommandResult = self.runner.run(command)
        except OSError as exc:
            return ApplyResult(
                False,
                "flash-failed",
                f"nvflash could not start: {exc}",
                {
                    "code": "FLASH_IO_ERROR",
                    "hint": "Restore from a vendor backup or hardware programmer.",
                },
            )
        _LOGGER.info(
            "nvflash result: candidate=%s sha256=%s exit_code=%s",
            candidate,
            expected_sha256,
            result.returncode,
        )
        return ApplyResult(
            result.returncode == 0,
            "flashed" if result.returncode == 0 else "flash-failed",
            "nvflash completed."
            if result.returncode == 0
            else "nvflash failed; do not retry automatically.",
            {
                "code": "FLASH_OK" if result.returncode == 0 else "FLASH_FAILED",
                "exit_code": result.returncode,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )
