#!/usr/bin/env python3
"""Pre-push / pre-publication audit for VBIOS Studio.

The audit is deliberately independent from GitHub: it inspects the working tree
that is about to be committed, so it also works before ``git init`` and inside a
release tarball.  With ``--strict`` any finding is a non-zero exit.

Checks
------
* file count, total size and the largest file;
* binary files (reported for transparency; only forbidden firmware/native
  suffixes fail);
* forbidden payloads (``.rom``, ``.bin``, ``.exe``, ``.dll``, ...);
* files larger than 1 MB;
* likely secrets (private keys, cloud tokens, credential assignments);
* ``.gitignore`` policy gaps;
* tracked files that match ``.gitignore`` (must be empty).

Usage
-----
    python tools/prepush_audit.py
    python tools/prepush_audit.py --strict
    python tools/prepush_audit.py --strict --report docs/prepush-audit.md
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.checks.repo_hygiene import (  # noqa: E402
    FORBIDDEN_NAMES,
    FORBIDDEN_SUFFIXES,
    MAX_FILE_BYTES,
    HygieneFinding,
    gitignore_gaps,
    iter_repo_files,
    scan_repository,
    tracked_ignored_files,
)

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp"})


@dataclass(frozen=True, slots=True)
class AuditReport:
    """All facts collected by one audit run."""

    root: Path
    files: tuple[Path, ...]
    total_bytes: int
    largest: tuple[Path, int] | None
    binaries: tuple[tuple[Path, int], ...]
    findings: tuple[HygieneFinding, ...]
    ignore_gaps: tuple[str, ...]
    tracked_ignored: tuple[str, ...]
    tracked_count: int | None

    @property
    def forbidden(self) -> tuple[HygieneFinding, ...]:
        return tuple(f for f in self.findings if f.kind in {"forbidden-binary", "forbidden-file"})

    @property
    def large(self) -> tuple[HygieneFinding, ...]:
        return tuple(f for f in self.findings if f.kind == "large-file")

    @property
    def secrets(self) -> tuple[HygieneFinding, ...]:
        return tuple(f for f in self.findings if f.kind == "secret")

    @property
    def passed(self) -> bool:
        return not (
            self.forbidden or self.large or self.secrets or self.ignore_gaps or self.tracked_ignored
        )


def _read_head(path: Path, size: int = 8192) -> bytes:
    try:
        return path.read_bytes()[:size]
    except OSError:
        return b""


def _is_binary(path: Path) -> bool:
    return b"\x00" in _read_head(path)


def _tracked_count(root: Path) -> int | None:
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return sum(1 for line in result.stdout.splitlines() if line)


def collect(root: Path = ROOT) -> AuditReport:
    """Collect an audit report for *root*."""
    root = root.resolve()
    files = tuple(iter_repo_files(root))
    sizes = [(path, path.stat().st_size) for path in files]
    largest = max(sizes, key=lambda item: item[1]) if sizes else None
    binaries = tuple((path, size) for path, size in sizes if _is_binary(path))
    return AuditReport(
        root=root,
        files=files,
        total_bytes=sum(size for _, size in sizes),
        largest=largest,
        binaries=binaries,
        findings=scan_repository(root),
        ignore_gaps=gitignore_gaps(root),
        tracked_ignored=tracked_ignored_files(root),
        tracked_count=_tracked_count(root),
    )


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _human(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def _finding_lines(findings: tuple[HygieneFinding, ...]) -> list[str]:
    return [f"  - {finding}" for finding in findings] or ["  - 无"]


def render_text(report: AuditReport) -> str:
    """Render the human-readable console report."""
    root = report.root
    largest = report.largest
    tracked = (
        report.tracked_count if report.tracked_count is not None else "n/a (not a git checkout)"
    )
    lines = [
        "VBIOS Studio prepush audit",
        f"root: {root}",
        f"files scanned: {len(report.files)}",
        f"tracked files: {tracked}",
        f"total size: {_human(report.total_bytes)}",
        (
            f"largest file: {_relative(largest[0], root)} ({largest[1]:,} bytes)"
            if largest
            else "largest file: n/a"
        ),
        f"likely binary files: {len(report.binaries)}",
    ]
    for path, size in report.binaries:
        suffix = path.suffix.lower()
        note = " (image asset, expected)" if suffix in IMAGE_SUFFIXES else ""
        lines.append(f"  - {_relative(path, root)} ({size:,} bytes){note}")
    if not report.binaries:
        lines.append("  - 无")
    lines += [
        f"forbidden payloads: {len(report.forbidden)}",
        *_finding_lines(report.forbidden),
        f"large files (> {MAX_FILE_BYTES:,} bytes): {len(report.large)}",
        *_finding_lines(report.large),
        f"secret findings: {len(report.secrets)}",
        *_finding_lines(report.secrets),
        f".gitignore gaps: {len(report.ignore_gaps)}",
        *[f"  - {gap}" for gap in report.ignore_gaps],
        f"tracked-but-ignored files: {len(report.tracked_ignored)}",
        *[f"  - {path}" for path in report.tracked_ignored],
        "",
        f"CONCLUSION: {'PASS' if report.passed else 'FAIL'}",
    ]
    return "\n".join(lines) + "\n"


def render_markdown(report: AuditReport) -> str:
    """Render the committed audit report (docs/prepush-audit.md)."""
    root = report.root
    largest = report.largest
    tracked = report.tracked_count if report.tracked_count is not None else "n/a（尚未 git init）"
    lines = [
        "# 上传前仓库审计报告（prepush audit）",
        "",
        "> 本报告由 `python tools/prepush_audit.py --strict --report docs/prepush-audit.md` 生成。"
        "结论基于当前工作树的实际字节；任何一项检查失败都会使 `--strict` 退出非 0。",
        "",
        "## 结论",
        "",
        f"**{'PASS' if report.passed else 'FAIL'}**",
        "",
        "## 概览",
        "",
        "| 项目 | 结果 |",
        "| --- | --- |",
        f"| 扫描文件数 | {len(report.files)} |",
        f"| Git 跟踪文件数 | {tracked} |",
        f"| 总体积 | {_human(report.total_bytes)} |",
        (
            f"| 最大文件 | `{_relative(largest[0], root)}`（{largest[1]:,} bytes） |"
            if largest
            else "| 最大文件 | n/a |"
        ),
        f"| 疑似二进制文件 | {len(report.binaries)} |",
        f"| 禁止的固件/原生二进制 | {len(report.forbidden)} |",
        f"| 超过 1 MB 的文件 | {len(report.large)} |",
        f"| 疑似密钥 | {len(report.secrets)} |",
        f"| `.gitignore` 缺失模式 | {len(report.ignore_gaps)} |",
        f"| 被 ignore 但已跟踪的文件 | {len(report.tracked_ignored)} |",
        "",
        "## 疑似二进制清单",
        "",
    ]
    if report.binaries:
        lines += ["| 文件 | 大小 | 说明 |", "| --- | ---: | --- |"]
        for path, size in report.binaries:
            suffix = path.suffix.lower()
            note = "界面截图（预期资产）" if suffix in IMAGE_SUFFIXES else "需人工确认"
            lines.append(f"| `{_relative(path, root)}` | {size:,} bytes | {note} |")
    else:
        lines.append("无。")
    lines += ["", "## 禁止的固件 / 原生二进制", ""]
    lines += _finding_lines(report.forbidden)
    lines += ["", "## 超大文件（> 1 MB）", ""]
    lines += _finding_lines(report.large)
    lines += ["", "## 疑似密钥扫描", ""]
    lines += _finding_lines(report.secrets)
    lines += ["", "## .gitignore 策略", ""]
    if report.ignore_gaps:
        lines += [f"- 缺失：`{gap}`" for gap in report.ignore_gaps]
    else:
        lines.append(
            "覆盖完整：`.venv/`、`__pycache__/`、`*.pyc`、`*.egg-info/`、"
            "`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、pip 缓存、"
            "`build/`、`dist/`、`*.rom`、`*.bin`、`*.exe`、`.env`、`.DS_Store`。"
        )
    lines += ["", "## 被 ignore 但已跟踪的文件", ""]
    lines += [f"- `{path}`" for path in report.tracked_ignored] or ["无（符合要求）。"]
    lines += [
        "",
        "## 判定规则",
        "",
        "- 禁止的固件/原生二进制：`" + "`, `".join(sorted(FORBIDDEN_SUFFIXES)) + "`；",
        "- 禁止的环境文件：`" + "`, `".join(sorted(FORBIDDEN_NAMES)) + "`；",
        f"- 单文件上限：{MAX_FILE_BYTES:,} bytes；",
        "- 被 `.gitignore` 命中却仍被 Git 跟踪的文件必须为 0。",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 when any finding exists")
    parser.add_argument("--report", type=Path, help="write a Markdown report to this path")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to audit")
    args = parser.parse_args(argv)

    report = collect(args.root)
    sys.stdout.write(render_text(report))
    if args.report:
        destination = args.report if args.report.is_absolute() else report.root / args.report
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_markdown(report), encoding="utf-8")
        print(f"\nreport written to {destination}")
    if args.strict and not report.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
