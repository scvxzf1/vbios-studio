"""Meta-test: README test counts must match the collected test tree."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
UI_TESTS = REPO_ROOT / "tests" / "ui"


def _readme_counts(path: Path) -> tuple[int, int]:
    """Return (pytest total, UI test file count) declared by a README."""
    text = path.read_text(encoding="utf-8")
    pytest_match = re.search(r"`pytest -q \| tail -1`\s*→\s*\*\*(\d+) passed\*\*", text)
    ui_match = re.search(r"`ls tests/ui/test_\*\.py \| wc -l`\s*→\s*\*\*(\d+)\*\*", text)
    if pytest_match is None or ui_match is None:
        raise AssertionError(
            "README 缺少可解析的测试计数声明：需要 "
            "`pytest -q | tail -1` → **N passed** 与 "
            "`ls tests/ui/test_*.py | wc -l` → **N**"
        )
    return int(pytest_match.group(1)), int(ui_match.group(1))


def _collected_test_count() -> int:
    """Collect the repository test tree without executing any test."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"pytest --collect-only 失败（exit {result.returncode}）：\n{result.stderr}"
        )
    match = re.search(r"(\d+) tests collected", result.stdout)
    if match is None:
        raise AssertionError(f"无法从 pytest --collect-only 输出解析测试总数：\n{result.stdout}")
    return int(match.group(1))


def _assert_readme_counts(path: Path, *, actual_pytest: int, actual_ui: int) -> None:
    """Fail with an actionable message when README counts are stale."""
    documented_pytest, documented_ui = _readme_counts(path)
    assert (documented_pytest, documented_ui) == (actual_pytest, actual_ui), (
        f"README 测试计数过期：文档写 pytest {documented_pytest} / UI {documented_ui}，"
        f"实际 pytest {actual_pytest} / UI {actual_ui}，请更新 README.md 与 docs/testing.md"
    )


def test_readme_counts_match_and_stale_value_is_rejected(tmp_path: Path) -> None:
    """The real README must match; a deliberately stale README must fail."""
    actual_pytest = _collected_test_count()
    actual_ui = len(list(UI_TESTS.glob("test_*.py")))
    _assert_readme_counts(README, actual_pytest=actual_pytest, actual_ui=actual_ui)

    stale = tmp_path / "README.md"
    stale.write_text(
        "`pytest -q | tail -1` → **999 passed**；`ls tests/ui/test_*.py | wc -l` → **999**\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="文档写 pytest 999 / UI 999"):
        _assert_readme_counts(stale, actual_pytest=actual_pytest, actual_ui=actual_ui)
