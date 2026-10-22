"""Meta-tests: the quality gates must fail on deliberately broken input."""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=False)


def _tool(name: str) -> str:
    adjacent = Path(sys.executable).with_name(name)
    return str(adjacent) if adjacent.is_file() else (shutil.which(name) or name)


def test_ruff_check_fails_on_unused_import(tmp_path: Path) -> None:
    """A dead import must make the ruff gate exit non-zero."""
    source = tmp_path / "broken.py"
    source.write_text("import os\n\nvalue = 1\n", encoding="utf-8")
    result = _run(sys.executable, "-m", "ruff", "check", "--isolated", "--no-cache", str(source))
    assert result.returncode != 0, result.stdout
    assert "F401" in result.stdout


def test_ruff_format_check_fails_on_unformatted_file(tmp_path: Path) -> None:
    """Sloppy formatting must make ``ruff format --check`` exit non-zero."""
    source = tmp_path / "unformatted.py"
    source.write_text("value = {'a':1,'b':2}\n", encoding="utf-8")
    result = _run(
        sys.executable, "-m", "ruff", "format", "--check", "--isolated", "--no-cache", str(source)
    )
    assert result.returncode != 0, result.stdout


def test_mypy_strict_fails_on_type_error(tmp_path: Path) -> None:
    """A return type mismatch must make strict mypy exit non-zero."""
    source = tmp_path / "typed.py"
    source.write_text("def broken(value: int) -> str:\n    return value\n", encoding="utf-8")
    result = _run(sys.executable, "-m", "mypy", "--strict", "--no-incremental", str(source))
    assert result.returncode != 0, result.stdout
    assert "Returning Any" in result.stdout or "Incompatible return" in result.stdout


def test_import_linter_fails_on_layer_violation(tmp_path: Path) -> None:
    """A domain module importing adapters must break the declared contract."""
    package = tmp_path / "layerpkg"
    (package / "domain").mkdir(parents=True)
    (package / "adapters").mkdir()
    for init in (
        package / "__init__.py",
        package / "domain" / "__init__.py",
        package / "adapters" / "__init__.py",
    ):
        init.write_text('"""Synthetic package."""\n', encoding="utf-8")
    (package / "adapters" / "impl.py").write_text('"""Adapter."""\nVALUE = 1\n', encoding="utf-8")
    (package / "domain" / "core.py").write_text(
        '"""Domain module that violates the layering."""\nfrom layerpkg.adapters import impl\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [tool.importlinter]
            root_packages = ["layerpkg"]

            [[tool.importlinter.contracts]]
            name = "forbidden-layer"
            type = "forbidden"
            source_modules = ["layerpkg.domain"]
            forbidden_modules = ["layerpkg.adapters"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    result = _run(
        _tool("lint-imports"),
        "--config",
        str(tmp_path / "pyproject.toml"),
        "--no-cache",
        "--no-logo",
        cwd=tmp_path,
    )
    assert result.returncode != 0, result.stdout
    assert "forbidden-layer" in result.stdout
