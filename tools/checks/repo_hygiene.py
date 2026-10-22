"""Repository hygiene scanners: forbidden payloads, large files and secrets.

The scanner is deliberately independent from git: it works on a plain tree so
it can run before the repository is initialised and on extracted release
artefacts.  ``tools/prepush_audit.py`` (t10) may additionally query git for
tracked-but-ignored files.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DEFAULT_EXCLUDED_DIRS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "build",
        "dist",
        "dist-linux",
        "dist-windows",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".import_linter_cache",
        "node_modules",
    }
)
DEFAULT_EXCLUDED_PARTS: Final[frozenset[str]] = frozenset(
    {".egg-info", ".eggs", "site-packages", ".tox"}
)
FORBIDDEN_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".rom",
        ".bin",
        ".exe",
        ".dll",
        ".sys",
        ".efi",
        ".vbi",
        ".fv",
        ".cap",
        ".img",
        ".iso",
        ".pyc",
        ".pyo",
    }
)
FORBIDDEN_NAMES: Final[frozenset[str]] = frozenset({".env", ".env.local", ".env.production"})
MAX_FILE_BYTES: Final[int] = 1_000_000
_SECRET_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("openai-token", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    (
        "assignment-secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*"
            r"['\"][^'\"]{12,}['\"]"
        ),
    ),
)
REQUIRED_GITIGNORE_PATTERNS: Final[tuple[str, ...]] = (
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "build/",
    "dist/",
    "*.rom",
    "*.bin",
    "*.exe",
    ".env",
    ".DS_Store",
    "*.egg-info/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
)


@dataclass(frozen=True, slots=True)
class HygieneFinding:
    """One problem found while scanning a repository tree."""

    path: str
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.kind}: {self.detail}"


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(relative: Path) -> bool:
    if any(part in DEFAULT_EXCLUDED_DIRS for part in relative.parts):
        return True
    return any(part.endswith(tuple(DEFAULT_EXCLUDED_PARTS)) for part in relative.parts)


def iter_repo_files(root: Path) -> Iterator[Path]:
    """Yield candidate files, skipping generated/cache directories.

    The returned paths are absolute but stable in lexicographic order, which
    keeps reports and meta-tests deterministic.
    """
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path.relative_to(root)):
            continue
        yield path


def _looks_binary(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:8192]
    except OSError:
        return True
    return b"\x00" in sample


def _secret_findings(path: Path, root: Path) -> list[HygieneFinding]:
    if _looks_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings: list[HygieneFinding] = []
    for name, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(
                HygieneFinding(_relative(path, root), "secret", f"matched {name} pattern")
            )
    return findings


def scan_repository(
    root: Path,
    *,
    max_file_bytes: int = MAX_FILE_BYTES,
    forbidden_suffixes: Iterable[str] = FORBIDDEN_SUFFIXES,
    check_secrets: bool = True,
) -> tuple[HygieneFinding, ...]:
    """Scan a tree for forbidden binaries, large files and secret material."""
    suffixes = {suffix.lower() for suffix in forbidden_suffixes}
    findings: list[HygieneFinding] = []
    for path in iter_repo_files(root):
        relative = _relative(path, root)
        suffix = path.suffix.lower()
        if suffix in suffixes:
            findings.append(
                HygieneFinding(relative, "forbidden-binary", f"{suffix} payload is not allowed")
            )
        if path.name in FORBIDDEN_NAMES or path.name.startswith(".env."):
            findings.append(HygieneFinding(relative, "forbidden-file", "environment file"))
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > max_file_bytes:
            findings.append(
                HygieneFinding(
                    relative, "large-file", f"{size} bytes exceeds {max_file_bytes} bytes"
                )
            )
        if check_secrets:
            findings.extend(_secret_findings(path, root))
    return tuple(findings)


def _gitignore_has(text: str, pattern: str) -> bool:
    """Accept the conventional spelling with or without a trailing slash."""
    candidates = {pattern, pattern.rstrip("/")}
    if pattern.endswith("/"):
        candidates.add(pattern.rstrip("/") + "/")
    return any(candidate in text for candidate in candidates)


def gitignore_gaps(root: Path) -> tuple[str, ...]:
    """Return required .gitignore patterns that are absent, or a missing-file note."""
    path = root / ".gitignore"
    if not path.is_file():
        return (".gitignore is missing",)
    text = path.read_text(encoding="utf-8")
    return tuple(
        pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if not _gitignore_has(text, pattern)
    )


def tracked_ignored_files(root: Path) -> tuple[str, ...]:
    """Return tracked paths that match .gitignore (empty outside a git checkout)."""
    if not (root / ".git").exists():
        return ()
    result = subprocess.run(
        ["git", "ls-files", "-ci", "--exclude-standard"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return (f"git ls-files failed: {result.stderr.strip()}",)
    return tuple(line for line in result.stdout.splitlines() if line)
