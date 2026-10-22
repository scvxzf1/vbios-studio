"""nvflash hard-guard tests: only a pristine image may reach the runner."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fakes import FakeRunner
from rom_helpers import make_rom

from vbios_studio.adapters.system.nvflash import NvflashGuard
from vbios_studio.domain.errors import (
    CHECKSUM_UNBALANCED,
    NVFLASH_NOT_FOUND,
    REFUSE_MODIFIED_IMAGE,
)

DEVICE = "10de:28b0"


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def _nvflash(tmp_path: Path) -> Path:
    path = tmp_path / "nvflash"
    path.write_bytes(b"fake nvflash")
    path.chmod(0o755)
    return path


def _guard(
    *, path: Path | None = None, version: str = "5.821.0"
) -> tuple[NvflashGuard, FakeRunner]:
    runner = FakeRunner()
    return (
        NvflashGuard(
            allow_flash=True,
            runner=runner,
            nvflash_path=str(path) if path is not None else None,
            nvflash_version=version,
            is_elevated=True,
        ),
        runner,
    )


def _check(guard: NvflashGuard, candidate: Path, original: Path, expected: str, **options):
    return guard.check(
        str(candidate),
        str(original),
        expected,
        DEVICE,
        understand_risk=True,
        confirmation=f"FLASH ORIGINAL {expected[:8]}",
        backup_confirmed=True,
        **options,
    )


def test_modified_image_is_refused_before_any_command(tmp_path: Path) -> None:
    """A candidate with different bytes is refused even when its hash ledger matches."""
    original = _write(tmp_path / "original.rom", make_rom())
    candidate = _write(tmp_path / "candidate.rom", make_rom())
    data = bytearray(candidate.read_bytes())
    data[512 + 100] ^= 0x01
    candidate.write_bytes(data)
    guard, runner = _guard(path=_nvflash(tmp_path))
    decision = _check(
        guard, candidate, original, hashlib.sha256(candidate.read_bytes()).hexdigest()
    )
    assert decision.allowed is False
    assert decision.code == REFUSE_MODIFIED_IMAGE
    assert "modified" in decision.message.lower()
    assert runner.calls == []


def test_unbalanced_checksum_is_refused_before_any_command(tmp_path: Path) -> None:
    """A byte-identical but checksum-unbalanced original is refused."""
    original = _write(tmp_path / "unbalanced.rom", make_rom(balanced=False))
    candidate = original
    guard, runner = _guard(path=_nvflash(tmp_path))
    decision = _check(
        guard, candidate, original, hashlib.sha256(candidate.read_bytes()).hexdigest()
    )
    assert decision.allowed is False
    assert decision.code == CHECKSUM_UNBALANCED
    assert "Image 1" in decision.message
    assert "0x" in decision.message
    assert decision.details["image_index"] == 1
    assert decision.details["checksum"] != 0
    assert runner.calls == []


def test_missing_nvflash_is_reported_without_any_command(tmp_path: Path) -> None:
    """A missing executable yields NVFLASH_NOT_FOUND and the runner is untouched."""
    original = _write(tmp_path / "original.rom", make_rom())
    candidate = _write(tmp_path / "candidate.rom", make_rom())
    guard = NvflashGuard(
        allow_flash=True,
        runner=FakeRunner(),
        nvflash_path=str(tmp_path / "does-not-exist"),
        nvflash_version="5.821.0",
        is_elevated=True,
    )
    decision = _check(
        guard, candidate, original, hashlib.sha256(candidate.read_bytes()).hexdigest()
    )
    assert decision.allowed is False
    assert decision.code == NVFLASH_NOT_FOUND
    assert "install" in decision.hint.lower()
    assert guard.runner.calls == []


def test_flash_channel_is_disabled_by_default(tmp_path: Path) -> None:
    """Without explicit opt-in, even a pristine image is refused."""
    original = _write(tmp_path / "original.rom", make_rom())
    guard = NvflashGuard(runner=FakeRunner(), is_elevated=True)
    decision = guard.check(
        str(original),
        str(original),
        hashlib.sha256(original.read_bytes()).hexdigest(),
        DEVICE,
    )
    assert decision.allowed is False
    assert decision.code == "FLASH_DISABLED"
    assert guard.runner.calls == []


def test_pristine_image_is_allowed_and_flash_uses_a_list_command(tmp_path: Path) -> None:
    """A fully validated original produces exactly one list-argument command."""
    original = _write(tmp_path / "original.rom", make_rom())
    candidate = _write(tmp_path / "candidate.rom", make_rom())
    nvflash = _nvflash(tmp_path)
    guard, runner = _guard(path=nvflash)
    expected = hashlib.sha256(candidate.read_bytes()).hexdigest()
    decision = _check(guard, candidate, original, expected)
    assert decision.allowed is True
    assert decision.code == "ALLOWED"
    result = guard.flash(
        str(candidate),
        str(original),
        expected,
        DEVICE,
        confirmation=f"FLASH ORIGINAL {expected[:8]}",
        backup_confirmed=True,
        understand_risk=True,
    )
    assert result.ok is True
    assert runner.calls == [[str(nvflash), "--write", str(candidate)]]
    assert all("--protectoff" not in part and "--erase" not in part for part in runner.calls[0])


def test_single_image_one_byte_change_is_checksum_unbalanced(tmp_path: Path) -> None:
    """A single-image byte edit must report its image index and 8-bit sum."""
    candidate = _write(tmp_path / "candidate.rom", make_rom())
    data = bytearray(candidate.read_bytes())
    data[512 + 2048 + 200] ^= 0x7F
    candidate.write_bytes(data)
    # Use the same bytes as the pristine reference to isolate checksum validation;
    # the modified/hash checks are covered by their own tests.
    pristine = _write(tmp_path / "pristine.rom", candidate.read_bytes())
    guard, runner = _guard(path=_nvflash(tmp_path))
    decision = _check(
        guard, candidate, pristine, hashlib.sha256(candidate.read_bytes()).hexdigest()
    )
    assert decision.allowed is False
    assert decision.code == CHECKSUM_UNBALANCED
    assert "Image 1" in decision.message
    assert "8-bit checksum" in decision.message
    assert runner.calls == []
