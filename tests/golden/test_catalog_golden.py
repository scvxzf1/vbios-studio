"""Deterministic golden snapshots for the synthetic ROM field catalogue."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.serialization import field_to_dict

GOLDEN = {
    "ada": {
        "total": 109,
        "editable": 18,
        "risk": {"T0": 91, "T1": 1, "T2": 12, "T3": 5},
        "first": [
            ("power_max_w", "70", "T3", True),
            ("power_default_w", "70", "T3", True),
            ("power_min_w", "30", "T1", True),
            ("nvvdd_rel_max_mv", "955", "T3", True),
            ("nvvdd_rel_equation_max_mv", "955", "T3", True),
        ],
    },
    "ampere": {
        "total": 114,
        "editable": 15,
        "risk": {"T0": 99, "T1": 0, "T2": 1, "T3": 14},
        "first": [
            ("power_max_w", "70", "T3", True),
            ("power_default_w", "70", "T3", True),
            ("power_min_w", "30", "T2", True),
            ("nvvdd_rel_max_mv", "1081.25", "T0", False),
            ("msvdd_rel_max_mv", "1081.25", "T0", False),
        ],
    },
}


@pytest.mark.parametrize("family", ("ada", "ampere"))
def test_catalog_counts_are_stable(family: str, synthetic_rom_factory, tmp_path: Path) -> None:
    """Field count, editable count and risk distribution are golden values."""
    source = tmp_path / f"{family}.rom"
    source.write_bytes(synthetic_rom_factory(family=family, copies=2))
    document = UpstreamEditorAdapter().open(source)
    expected = GOLDEN[family]

    assert len(document.fields) == expected["total"]
    assert sum(field.editable for field in document.fields) == expected["editable"]
    counts = {
        level: sum(field.risk == level for field in document.fields)
        for level in ("T0", "T1", "T2", "T3")
    }
    assert counts == expected["risk"]
    first = [
        (field.key, field.current, field.risk, field.editable) for field in document.fields[:5]
    ]
    assert first == expected["first"]


def test_catalog_serialization_is_deterministic(synthetic_ada_rom: bytes, tmp_path: Path) -> None:
    """Serializing the same field catalogue twice produces identical dicts."""
    source = tmp_path / "stable.rom"
    source.write_bytes(synthetic_ada_rom)
    document = UpstreamEditorAdapter().open(source)
    first = [field_to_dict(field) for field in document.fields]
    second = [field_to_dict(field) for field in document.fields]
    assert first == second
    assert all("risk" in item and "section" in item for item in first)
