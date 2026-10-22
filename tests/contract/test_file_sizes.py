"""Contract tests for file size and module docstring hygiene."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "vbios_studio"
TESTS = ROOT / "tests"
MAX_LINES = 400


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def test_no_python_file_exceeds_400_lines() -> None:
    """Every owned Python file stays under the 400-line limit."""
    offenders: list[str] = []
    for path in _python_files(SOURCE) + _python_files(TESTS):
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            offenders.append(f"{path.relative_to(ROOT)}: {line_count} lines")
    assert not offenders, "files over 400 lines: " + ", ".join(offenders)


def test_every_python_module_has_a_docstring() -> None:
    """All owned modules start with a module-level docstring."""
    offenders: list[str] = []
    for path in _python_files(SOURCE) + _python_files(TESTS):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not ast.get_docstring(tree):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "modules without docstrings: " + ", ".join(offenders)
