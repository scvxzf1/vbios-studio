"""Meta-tests: hygiene and structure checks must fail on planted violations."""

from __future__ import annotations

from pathlib import Path

from tools.checks.repo_hygiene import gitignore_gaps, scan_repository
from tools.checks.structure_audit import (
    docs_tree_findings,
    docstring_findings,
    oversized_files,
)


def _write(path: Path, content: str = "test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_rom_payload_makes_hygiene_scan_fail(tmp_path: Path) -> None:
    """A planted .rom file must be reported as a forbidden binary."""
    _write(tmp_path / "firmware.rom", "\x00firmware")
    findings = scan_repository(tmp_path)
    assert any(finding.kind == "forbidden-binary" for finding in findings)


def test_env_file_makes_hygiene_scan_fail(tmp_path: Path) -> None:
    """A planted .env file must be reported as a forbidden file."""
    _write(tmp_path / ".env", "TOKEN=value\n")
    findings = scan_repository(tmp_path)
    assert any(finding.kind == "forbidden-file" for finding in findings)


def test_one_megabyte_file_makes_hygiene_scan_fail(tmp_path: Path) -> None:
    """A planted 1 MB payload must trip the size gate."""
    payload = tmp_path / "blob.dat"
    payload.write_bytes(b"x" * 1_000_001)
    findings = scan_repository(tmp_path)
    assert any(finding.kind == "large-file" for finding in findings)


def test_clean_tree_produces_no_hygiene_findings(tmp_path: Path) -> None:
    """The scanner has no false positives on a small clean tree."""
    _write(tmp_path / "README.md", "# clean\n")
    _write(tmp_path / "src" / "pkg" / "mod.py", '"""Doc."""\n')
    assert scan_repository(tmp_path) == ()


def test_gitignore_missing_pattern_is_detected(tmp_path: Path) -> None:
    """A partial .gitignore must report exactly the missing policy entries."""
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    gaps = gitignore_gaps(tmp_path)
    assert "*.rom" in gaps
    assert "*.exe" in gaps
    assert ".venv/" in gaps


def test_missing_docstring_is_detected(tmp_path: Path) -> None:
    """A module without a docstring must be reported."""
    module = tmp_path / "src" / "pkg" / "mod.py"
    _write(module, "VALUE = 1\n")
    findings = docstring_findings([module], root=tmp_path)
    assert any(finding.kind == "missing-docstring" for finding in findings)


def test_401_line_module_is_detected(tmp_path: Path) -> None:
    """A file one line over the cap must be reported."""
    module = tmp_path / "src" / "pkg" / "long.py"
    _write(module, '"""Long module."""\n' + "x = 1\n" * 400)
    findings = oversized_files([module], root=tmp_path, limit=400)
    assert any(finding.kind == "file-too-long" for finding in findings)


def test_undocumented_source_module_is_detected(tmp_path: Path) -> None:
    """A source module absent from docs/file-tree.md must be reported."""
    module = tmp_path / "src" / "vbios_studio" / "domain" / "hidden.py"
    _write(module, '"""Hidden module."""\n')
    _write(tmp_path / "docs" / "file-tree.md", "# Tree\n\nNo modules here.\n")
    findings = docs_tree_findings(tmp_path)
    assert any(finding.kind == "undocumented-module" for finding in findings)


def test_stale_file_tree_path_is_detected(tmp_path: Path) -> None:
    """A documented but non-existent source path must be reported."""
    (tmp_path / "src" / "vbios_studio").mkdir(parents=True)
    _write(tmp_path / "docs" / "file-tree.md", "`src/vbios_studio/ghost.py`\n")
    findings = docs_tree_findings(tmp_path)
    assert any(finding.kind == "stale-path" for finding in findings)
