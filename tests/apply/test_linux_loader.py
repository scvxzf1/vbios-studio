"""Linux loader probe/guidance tests; no system files or processes are touched."""

from __future__ import annotations

from pathlib import Path

from vbios_studio.adapters.system.linux_loader import LinuxLoaderAdapter


def test_find_loader_prefers_which_and_common_paths(tmp_path: Path) -> None:
    """Discovery returns an executable loader path and otherwise None."""
    executable = tmp_path / "loader"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    found = LinuxLoaderAdapter(which=lambda name: str(executable), search_paths=())
    assert found.find_loader() == str(executable)
    assert found.probe().found is True

    missing = LinuxLoaderAdapter(which=lambda name: None, search_paths=())
    assert missing.find_loader() is None
    assert missing.probe().to_dict()["found"] is False


def test_guidance_is_copyable_and_never_suggests_automatic_execution(tmp_path: Path) -> None:
    """Guidance names the payload and clearly states that it is manual-only."""
    executable = tmp_path / "loader"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = LinuxLoaderAdapter(which=lambda name: str(executable), search_paths=())
    payload = tmp_path / "edited-loader.bin"
    text = adapter.guidance(str(payload))
    assert str(payload) in text
    assert str(executable) in text
    assert "does not run" in text
    assert "manual" in text.lower() or "manually" in text.lower()
    assert "sudo" not in text
    prepared = adapter.prepare(str(payload))
    assert prepared["manual_only"] is True
    assert prepared["loader"]["found"] is True
    assert prepared["guidance"] == text


def test_guidance_works_when_loader_is_absent(tmp_path: Path) -> None:
    """An absent external loader still yields useful, copyable guidance."""
    adapter = LinuxLoaderAdapter(which=lambda name: None, search_paths=())
    text = adapter.guidance(str(tmp_path / "payload.bin"))
    assert "not found" in text
    assert "Panchovix/nvidia-linux-vbios-vix-loader" in text
