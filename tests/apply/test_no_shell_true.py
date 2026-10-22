"""Repository-wide AST audit: no shell strings and no unsafe os process calls."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", ".venv", "__pycache__", "build", "dist", ".mypy_cache", ".ruff_cache"}
_OS_SYSTEM = "os." + "system"
_OS_POPEN = "os." + "popen"
_SHELL_TRUE = "shell=" + "True"


def _files() -> list[Path]:
    return [
        path for path in ROOT.rglob("*.py") if not any(part in SKIP_PARTS for part in path.parts)
    ]


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _truthy_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and bool(node.value)


def _string_command(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


def violations(source: str, filename: str = "<memory>") -> list[str]:
    """Return human-readable violations found in one Python source string."""
    tree = ast.parse(source, filename=filename)
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted(node.func)
        if name in {_OS_SYSTEM, _OS_POPEN}:
            found.append(f"{filename}:{node.lineno}: {name} is forbidden")
        if name.startswith("subprocess."):
            for keyword in node.keywords:
                if keyword.arg == "shell" and _truthy_constant(keyword.value):
                    found.append(f"{filename}:{node.lineno}: {name} uses {_SHELL_TRUE}")
            if node.args and _string_command(node.args[0]):
                found.append(f"{filename}:{node.lineno}: {name} passes a string command")
    return found


def test_no_shell_true_or_os_system_anywhere() -> None:
    """Every process call is either an argument list or a validated runner call."""
    bad: list[str] = []
    for path in _files():
        bad.extend(violations(path.read_text(encoding="utf-8"), str(path)))
    assert not bad, "\n".join(bad)


def test_scanner_catches_both_forbidden_patterns() -> None:
    """The audit itself is exercised against deliberately bad snippets."""
    assert violations(f"import os\n{_OS_SYSTEM}('echo hi')\n")
    assert violations(f"import subprocess\nsubprocess.run('echo hi', {_SHELL_TRUE})\n")
    assert violations(f"import subprocess\nsubprocess.call(['echo', 'hi'], {_SHELL_TRUE})\n")
    assert violations("import subprocess\nsubprocess.run(['echo', 'hi'])\n") == []


def test_production_runner_rejects_non_list_commands() -> None:
    """The shared production runner refuses strings and tuples before starting."""
    from vbios_studio.adapters.system._base import SubprocessRunner

    runner = SubprocessRunner()
    for command in ("echo hi", ("echo", "hi")):
        try:
            runner.run(command)  # type: ignore[arg-type]
        except ValueError:
            continue
        raise AssertionError(f"runner accepted {command!r}")
