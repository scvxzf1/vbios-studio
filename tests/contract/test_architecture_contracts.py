"""Contract tests for the import-linter configuration and architecture docs."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CONTRACTS = {
    "domain-pure",
    "ui-no-adapters",
    "ports-no-implementations",
    "layers-app-top",
}


def _contracts() -> list[dict[str, object]]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["importlinter"]["contracts"]


def test_at_least_four_import_contracts() -> None:
    """The project declares at least four import-linter contracts."""
    names = {contract["name"] for contract in _contracts()}
    assert len(names) >= 4
    assert names >= REQUIRED_CONTRACTS


def test_architecture_docs_name_every_contract() -> None:
    """docs/architecture.md has a one-to-one mapping for every contract."""
    text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    for contract in _contracts():
        name = str(contract["name"])
        assert name in text, f"architecture.md does not document contract {name}"
    assert "graph TD" in text, "architecture.md must contain a Mermaid dependency graph"


def test_layers_contract_places_app_on_top() -> None:
    """The layers contract must put app above ui/adapters/ports/domain."""
    layers = next(c for c in _contracts() if c["name"] == "layers-app-top")
    assert layers["layers"] == [
        "vbios_studio.app",
        "vbios_studio.ui",
        "vbios_studio.adapters",
        "vbios_studio.ports",
        "vbios_studio.domain",
    ]
