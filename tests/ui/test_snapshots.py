"""Snapshot test: the offscreen selftest produces three real PNG files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def test_selftest_writes_three_screenshots(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    command = [
        "xvfb-run",
        "-a",
        "-s",
        "-screen 0 1400x900x24",
        sys.executable,
        "-m",
        "vbios_studio.ui",
        "--selftest",
        "--screenshots",
        str(tmp_path),
    ]
    result = subprocess.run(
        command, cwd=ROOT, env=env, capture_output=True, text=True, check=False, timeout=120
    )
    assert result.returncode == 0, result.stderr
    names = ("01-main-window.png", "02-fields-risk.png", "03-apply-panel.png")
    for name in names:
        path = tmp_path / name
        assert path.exists(), name
        width, height = _png_size(path)
        assert width >= 800 and height >= 600


def test_repository_screenshots_are_real_png() -> None:
    folder = ROOT / "docs-assets" / "screenshots"
    files = sorted(folder.glob("*.png"))
    assert len(files) >= 3
    for path in files:
        width, height = _png_size(path)
        assert width >= 800 and height >= 600
