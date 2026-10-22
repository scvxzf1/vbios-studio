"""Contract tests: the CLI must work when importing ``gi`` is fatal."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _run_with_broken_gtk(tmp_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    (tmp_path / "gi.py").write_text(
        'raise RuntimeError("GTK import is forbidden in this contract test")\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(tmp_path), str(SRC)])
    env["PYTHONNOUSERSITE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "vbios_studio", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_version_does_not_import_gtk(tmp_path: Path) -> None:
    """``python -m vbios_studio --version`` succeeds with a poisoned gi module."""
    result = _run_with_broken_gtk(tmp_path, ["--version"])
    assert result.returncode == 0, result.stderr
    assert "vbios-studio" in result.stdout
    assert "0.1.0" in result.stdout


def test_selftest_does_not_import_gtk(tmp_path: Path) -> None:
    """The headless selftest also avoids PyGObject."""
    result = _run_with_broken_gtk(tmp_path, ["--selftest"])
    assert result.returncode == 0, result.stderr
    assert "selftest: ok" in result.stdout
