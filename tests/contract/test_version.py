"""Contract tests for version consistency and the vendored upstream package."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import vbios_studio

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "src" / "nvidia_vbios"
MANIFEST = ROOT / "tests" / "contract" / "upstream-manifest.json"


def test_version_matches_pyproject() -> None:
    """``vbios_studio.__version__`` matches the packaging version."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert vbios_studio.__version__ == data["project"]["version"]


def test_vendored_upstream_is_present_and_untouched() -> None:
    """Every vendored upstream file matches the frozen SHA-256 manifest."""
    import nvidia_vbios

    assert nvidia_vbios.__version__ == "0.1.28"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["commit"] == "1f8ee665bd175bd9ede367e6d15308f837bd987b"

    expected: dict[str, str] = manifest["files"]
    actual_files = {
        path.relative_to(VENDOR).as_posix()
        for path in VENDOR.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    assert actual_files == set(expected), "vendored file set differs from manifest"
    for relative, digest in expected.items():
        data = (VENDOR / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, f"modified vendored file: {relative}"


def test_manifest_matches_upstream_pin_document() -> None:
    """The manifest pin is the same 40-character SHA recorded in UPSTREAM.md."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
    assert manifest["commit"] in upstream
    assert len(manifest["commit"]) == 40
