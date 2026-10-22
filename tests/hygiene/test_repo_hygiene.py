"""Repository hygiene: no firmware, no oversized payloads, no secrets."""

from __future__ import annotations

from pathlib import Path

from tools.checks.repo_hygiene import (
    DEFAULT_EXCLUDED_DIRS,
    FORBIDDEN_SUFFIXES,
    iter_repo_files,
    scan_repository,
)

ROOT = Path(__file__).resolve().parents[2]


def test_repository_contains_no_forbidden_binaries() -> None:
    """No .rom/.bin/.exe or other firmware payload may be committed."""
    findings = scan_repository(ROOT)
    forbidden = [finding for finding in findings if finding.kind == "forbidden-binary"]
    assert not forbidden, "forbidden payloads:\n" + "\n".join(map(str, forbidden))


def test_repository_contains_no_oversized_files() -> None:
    """Every non-generated repository file stays below the 1 MB audit limit."""
    findings = scan_repository(ROOT)
    large = [finding for finding in findings if finding.kind == "large-file"]
    assert not large, "files over 1 MB:\n" + "\n".join(map(str, large))


def test_repository_contains_no_secret_material() -> None:
    """Private keys, cloud tokens and credential assignments must not be present."""
    findings = scan_repository(ROOT)
    secrets = [finding for finding in findings if finding.kind == "secret"]
    assert not secrets, "potential secrets:\n" + "\n".join(map(str, secrets))


def test_scan_skips_virtualenv_and_generated_caches() -> None:
    """The scan itself must not walk .venv, build outputs or tool caches."""
    files = list(iter_repo_files(ROOT))
    assert files
    for path in files:
        relative = path.relative_to(ROOT)
        assert not (set(relative.parts) & DEFAULT_EXCLUDED_DIRS), relative


def test_test_roms_are_synthetic_and_not_vendored() -> None:
    """The only ROM bytes in the tree are produced by the fixture builder."""
    vendored = [
        path.relative_to(ROOT).as_posix()
        for path in iter_repo_files(ROOT)
        if path.suffix.lower() in {".rom", ".bin"}
    ]
    assert not vendored, f"firmware payloads leaked into the repository: {vendored}"
    assert {".rom", ".bin", ".exe"} <= FORBIDDEN_SUFFIXES
