"""Policy check for .gitignore coverage of generated and sensitive artefacts."""

from __future__ import annotations

from pathlib import Path

import pytest
from tools.checks.repo_hygiene import REQUIRED_GITIGNORE_PATTERNS, gitignore_gaps

ROOT = Path(__file__).resolve().parents[2]


def test_required_patterns_are_documented() -> None:
    """The policy itself explicitly names every generated/sensitive artefact class."""
    assert {"*.rom", "*.bin", "*.exe", ".venv/", ".env", "__pycache__/"}.issubset(
        REQUIRED_GITIGNORE_PATTERNS
    )


def test_complete_policy_file_passes(tmp_path: Path) -> None:
    """A .gitignore containing the full policy has no gaps."""
    (tmp_path / ".gitignore").write_text(
        "\n".join(REQUIRED_GITIGNORE_PATTERNS) + "\n", encoding="utf-8"
    )
    assert gitignore_gaps(tmp_path) == ()


def test_gitignore_covers_generated_artefacts_when_present() -> None:
    """If .gitignore exists (t10), every required pattern must be present."""
    if not (ROOT / ".gitignore").is_file():
        pytest.skip(".gitignore is delivered by t10 after the test system (t7)")
    gaps = gitignore_gaps(ROOT)
    assert not gaps, f".gitignore misses: {gaps}"
