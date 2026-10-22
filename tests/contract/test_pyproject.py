"""Contract tests for packaging metadata and optional GTK dependency."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _pyproject() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_project_metadata() -> None:
    """Project name, version and Python floor are frozen for v0.1.0."""
    project = _pyproject()["project"]
    assert project["name"] == "vbios-studio"
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.11"


def test_pygobject_is_only_an_optional_extra() -> None:
    """PyGObject must never be a required runtime dependency."""
    project = _pyproject()["project"]
    required = " ".join(project.get("dependencies", []))
    assert "PyGObject" not in required
    gtk_extra = project["optional-dependencies"]["gtk"]
    assert any("PyGObject" in item for item in gtk_extra)


def test_packages_are_discovered_under_src() -> None:
    """Setuptools finds both our package and the vendored upstream package."""
    tool = _pyproject()["tool"]["setuptools"]
    assert tool["package-dir"][""] == "src"
    include = tool["packages"]["find"]["include"]
    assert "vbios_studio*" in include
    assert "nvidia_vbios*" in include


def test_console_scripts_are_declared() -> None:
    """The CLI and GUI console scripts point at real module functions."""
    scripts = _pyproject()["project"]["scripts"]
    assert scripts["vbios-studio"] == "vbios_studio.app.cli:main"
    assert scripts["vbios-studio-gui"] == "vbios_studio.app.gui:main"
