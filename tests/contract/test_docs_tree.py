"""Docs contract: README warnings, required docs, and file-tree accuracy."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = (
    "architecture.md",
    "file-tree.md",
    "risk-model.md",
    "testing.md",
    "upstream-sync.md",
    "i18n.md",
    "security.md",
    "faq.md",
)
SOURCE = ROOT / "src" / "vbios_studio"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_docs_exist() -> None:
    """The published documentation set is present under docs/."""
    for name in DOCS:
        assert (ROOT / "docs" / name).is_file(), f"missing docs/{name}"


def test_readme_has_prominent_incomplete_warning() -> None:
    """The warning must be in the first screen, before ordinary marketing copy."""
    text = _read(ROOT / "README.md")
    head = text[:2500]
    assert "测试不完全" in head
    assert "未在真实硬件验证" in head
    assert "nvflash" in head


def test_readme_has_required_sections() -> None:
    """Support matrix, install, quick start, risk and disclaimer are mandatory."""
    text = _read(ROOT / "README.md")
    for heading in ("支持矩阵", "安装", "快速开始", "风险分级", "许可证与免责声明"):
        assert heading in text, f"README lacks section: {heading}"


def test_readme_links_every_document() -> None:
    """Every docs page is linked from the README documentation table."""
    text = _read(ROOT / "README.md")
    for name in DOCS:
        assert f"docs/{name}" in text, f"README does not link docs/{name}"


def test_file_tree_lists_every_source_module() -> None:
    """Every Python module under src/vbios_studio is documented by path."""
    text = _read(ROOT / "docs" / "file-tree.md")
    modules = sorted(path.relative_to(ROOT).as_posix() for path in SOURCE.rglob("*.py"))
    assert modules, "no source modules found"
    missing = [module for module in modules if module not in text]
    assert not missing, f"file-tree.md misses source modules: {missing}"


def test_file_tree_has_no_stale_source_paths() -> None:
    """Every src/vbios_studio path mentioned by file-tree.md must exist."""
    text = _read(ROOT / "docs" / "file-tree.md")
    mentioned = set(re.findall(r"src/vbios_studio/[A-Za-z0-9_./-]+\.(?:py|po|mo)", text))
    stale = sorted(path for path in mentioned if not (ROOT / path).is_file())
    assert not stale, f"file-tree.md mentions missing paths: {stale}"


def test_file_tree_lists_every_package_and_test_area() -> None:
    """Package directories and test areas are represented in the tree document."""
    text = _read(ROOT / "docs" / "file-tree.md")
    for package in ("domain", "ports", "adapters", "ui", "app", "i18n"):
        assert f"src/vbios_studio/{package}/" in text
    for area in (
        "tests/contract",
        "tests/core",
        "tests/apply",
        "tests/ui",
        "tests/i18n",
        "tests/release",
    ):
        assert area in text


def test_security_doc_states_the_hard_boundaries() -> None:
    """security.md must carry the four user-facing safety promises."""
    text = _read(ROOT / "docs" / "security.md")
    for phrase in ("NVIDIA 固件", "不上传", "管理员", "nvflash"):
        assert phrase in text, f"security.md lacks phrase: {phrase}"


def test_upstream_sync_doc_has_commands_and_pin_rules() -> None:
    """upstream-sync.md must be executable, not a vague policy."""
    text = _read(ROOT / "docs" / "upstream-sync.md")
    for phrase in ("git ls-remote", "git clone", "UPSTREAM.md", "40 位", "冲突", "pin"):
        assert phrase in text, f"upstream-sync.md lacks phrase: {phrase}"
