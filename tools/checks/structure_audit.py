"""Structure checks: module docstrings, file-size cap and docs/file-tree drift."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

MAX_PYTHON_LINES = 400
_TREE_PATH = re.compile(r"src/vbios_studio/[A-Za-z0-9_./-]+\.(?:py|po|mo)")


@dataclass(frozen=True, slots=True)
class StructureFinding:
    """One structural inconsistency in the project tree."""

    path: str
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.kind}: {self.detail}"


def owned_python_files(root: Path) -> list[Path]:
    """Return owned source and test modules, excluding caches and vendored code."""
    files: list[Path] = []
    for base in (root / "src" / "vbios_studio", root / "tests"):
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" not in path.parts:
                files.append(path)
    return files


def oversized_files(
    paths: Iterable[Path], *, root: Path, limit: int = MAX_PYTHON_LINES
) -> tuple[StructureFinding, ...]:
    """Return files whose physical line count exceeds ``limit``."""
    findings: list[StructureFinding] = []
    for path in paths:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > limit:
            findings.append(
                StructureFinding(
                    path.relative_to(root).as_posix(),
                    "file-too-long",
                    f"{line_count} lines exceeds {limit}",
                )
            )
    return tuple(findings)


def docstring_findings(paths: Iterable[Path], *, root: Path) -> tuple[StructureFinding, ...]:
    """Return modules whose first statement is not a module docstring."""
    findings: list[StructureFinding] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if not ast.get_docstring(tree):
            findings.append(
                StructureFinding(
                    path.relative_to(root).as_posix(),
                    "missing-docstring",
                    "module docstring absent",
                )
            )
    return tuple(findings)


def docs_tree_findings(root: Path) -> tuple[StructureFinding, ...]:
    """Check docs/file-tree.md against the real ``src/vbios_studio`` tree."""
    docs = root / "docs" / "file-tree.md"
    if not docs.is_file():
        return (StructureFinding("docs/file-tree.md", "missing-doc", "file-tree.md not found"),)
    text = docs.read_text(encoding="utf-8")
    source = root / "src" / "vbios_studio"
    modules = sorted(path.relative_to(root).as_posix() for path in source.rglob("*.py"))
    findings: list[StructureFinding] = []
    for module in modules:
        if module not in text:
            findings.append(
                StructureFinding(
                    "docs/file-tree.md", "undocumented-module", f"missing source path {module}"
                )
            )
    mentioned = set(_TREE_PATH.findall(text))
    for path in sorted(mentioned):
        if not (root / path).is_file():
            findings.append(
                StructureFinding(
                    "docs/file-tree.md", "stale-path", f"documented path does not exist: {path}"
                )
            )
    return tuple(findings)


def tree_area_findings(root: Path, areas: Iterable[str]) -> tuple[StructureFinding, ...]:
    """Check that each required test area is named in docs/file-tree.md."""
    docs = root / "docs" / "file-tree.md"
    if not docs.is_file():
        return (StructureFinding("docs/file-tree.md", "missing-doc", "file-tree.md not found"),)
    text = docs.read_text(encoding="utf-8")
    return tuple(
        StructureFinding("docs/file-tree.md", "undocumented-test-area", f"missing {area}")
        for area in areas
        if area not in text
    )
