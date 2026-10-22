"""Structure audit: docs/file-tree accuracy, docstrings and 400-line cap."""

from __future__ import annotations

from pathlib import Path

from tools.checks.structure_audit import (
    MAX_PYTHON_LINES,
    docs_tree_findings,
    docstring_findings,
    oversized_files,
    owned_python_files,
    tree_area_findings,
)

ROOT = Path(__file__).resolve().parents[2]


def test_owned_python_files_stay_within_line_limit() -> None:
    """Every source and test module honours the 400-line cap."""
    findings = oversized_files(owned_python_files(ROOT), root=ROOT)
    assert not findings, "oversized modules:\n" + "\n".join(map(str, findings))
    assert MAX_PYTHON_LINES == 400


def test_every_owned_module_has_a_docstring() -> None:
    """A missing module docstring is a structure defect."""
    findings = docstring_findings(owned_python_files(ROOT), root=ROOT)
    assert not findings, "missing docstrings:\n" + "\n".join(map(str, findings))


def test_file_tree_lists_and_resolves_every_source_module() -> None:
    """docs/file-tree.md must neither omit nor invent source paths."""
    findings = docs_tree_findings(ROOT)
    assert not findings, "file-tree drift:\n" + "\n".join(map(str, findings))


def test_file_tree_names_all_test_areas() -> None:
    """The published test tree includes every executed test area."""
    areas = (
        "tests/contract",
        "tests/core",
        "tests/apply",
        "tests/ui",
        "tests/integration",
        "tests/i18n",
        "tests/release",
        "tests/golden",
        "tests/hygiene",
        "tests/meta",
    )
    findings = tree_area_findings(ROOT, areas)
    assert not findings, "\n".join(map(str, findings))
