"""The offscreen selftest is deterministic, diagnosable and concurrency-safe."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _command(target: Path) -> list[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return [
        "xvfb-run",
        "-a",
        "-s",
        "-screen 0 1400x900x24",
        sys.executable,
        "-m",
        "vbios_studio.ui",
        "--selftest",
        "--screenshots",
        str(target),
    ]


def test_two_selftests_run_concurrently(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    first, second = tmp_path / "first", tmp_path / "second"
    processes = [
        subprocess.Popen(
            _command(first),
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ),
        subprocess.Popen(
            _command(second),
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ),
    ]
    results = [(*process.communicate(timeout=120), process.returncode) for process in processes]
    for index, (stdout, stderr, returncode) in enumerate(results):
        assert returncode == 0, f"process {index}: {stderr}\n{stdout}"
        assert "selftest: ok" in stdout
        assert (first if index == 0 else second).joinpath("01-main-window.png").exists()
