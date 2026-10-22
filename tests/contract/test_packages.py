"""Contract tests for the six-package layout and package documentation."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "vbios_studio"
PACKAGES = ("domain", "ports", "adapters", "ui", "app", "i18n")


def _docstring(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return ast.get_docstring(tree) or ""


def test_six_packages_have_init_and_readme() -> None:
    """Every required subpackage carries __init__.py and README.md."""
    for name in PACKAGES:
        package = SRC / name
        assert package.is_dir(), f"missing package: {name}"
        assert (package / "__init__.py").is_file(), f"missing {name}/__init__.py"
        assert (package / "README.md").is_file(), f"missing {name}/README.md"


def test_every_package_init_has_module_docstring() -> None:
    """Package initializers and the top-level package are documented."""
    candidates = [SRC / "__init__.py"] + [SRC / name / "__init__.py" for name in PACKAGES]
    for path in candidates:
        assert _docstring(path), f"missing module docstring: {path}"


def test_every_package_readme_documents_role_and_dependencies() -> None:
    """Each README explains responsibilities and the dependency direction."""
    for name in PACKAGES:
        text = (SRC / name / "README.md").read_text(encoding="utf-8")
        assert "职责" in text, f"{name}/README.md lacks a responsibilities section"
        assert "依赖" in text, f"{name}/README.md lacks a dependency section"


def test_top_level_readme_documents_layout() -> None:
    """The package README lists all six layers and the entry points."""
    text = (SRC / "README.md").read_text(encoding="utf-8")
    for name in PACKAGES:
        assert name in text, f"top-level README does not mention {name}"
    assert "python -m vbios_studio --version" in text
