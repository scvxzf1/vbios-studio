"""Executable parity assertion against the vendored upstream ``nvidia_vbios`` fields."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from tools.checks.parity import (
    EXTRA_METADATA_KEYS,
    compare_catalogs,
    metadata_attribute_issues,
)

from nvidia_vbios.rom import from_bytes, inspect_image
from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.catalog import format_value
from vbios_studio.domain.models import FieldSnapshot

CASES = (("ada", 30), ("ampere", 39))


@pytest.mark.parametrize(("family", "upstream_field_count"), CASES)
def test_common_fields_match_upstream_exactly(
    family: str,
    upstream_field_count: int,
    synthetic_rom_factory,
    tmp_path: Path,
) -> None:
    """Same synthetic bytes, same upstream parser, field-by-field equality."""
    blob = synthetic_rom_factory(family=family, copies=2)
    source = tmp_path / f"{family}.rom"
    source.write_bytes(blob)
    report = inspect_image(from_bytes(blob))
    assert len(report["fields"]) == upstream_field_count

    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    assert document.sha256 == hashlib.sha256(blob).hexdigest()
    assert len(document.fields) >= upstream_field_count
    catalog = adapter.catalog_json()
    catalog_fields = {item["key"]: item for item in catalog["fields"]}
    assert set(catalog_fields) == {field.key for field in document.fields}
    assert catalog["upstream"]["pin"] == "1f8ee665bd175bd9ede367e6d15308f837bd987b"
    for upstream in report["fields"]:
        rendered = catalog_fields[str(upstream["key"])]
        assert rendered["label"] == upstream["label"]
        assert rendered["unit"] == (upstream.get("units") or "")
        assert rendered["current"] == format_value(upstream.get("current"))
        assert rendered["editable"] is bool(upstream.get("editable"))

    issues = compare_catalogs(report["fields"], document.fields)
    assert not issues, "upstream parity drift:\n" + "\n".join(str(issue) for issue in issues)


@pytest.mark.parametrize(("family", "upstream_field_count"), CASES)
def test_catalog_extends_only_with_declared_read_only_placeholders(
    family: str,
    upstream_field_count: int,
    synthetic_rom_factory,
    tmp_path: Path,
) -> None:
    """Every extra catalogue entry is a T0 read-only canonical placeholder."""
    blob = synthetic_rom_factory(family=family, copies=2)
    source = tmp_path / f"{family}.rom"
    source.write_bytes(blob)
    report = inspect_image(from_bytes(blob))
    document = UpstreamEditorAdapter().open(source)

    upstream_keys = {str(field["key"]) for field in report["fields"]}
    ours = {field.key: field for field in document.fields}
    extras = set(ours) - upstream_keys
    assert set(ours) >= upstream_keys
    assert len(upstream_keys) == upstream_field_count
    for key in extras:
        extra = ours[key]
        assert extra.editable is False, f"{key} must stay read-only"
        assert extra.risk == "T0", f"{key} placeholder must be T0"
        assert extra.current is None
        assert extra.offset is None


def test_field_snapshot_has_only_declared_metadata_extensions() -> None:
    """A new FieldSnapshot attribute must be added to the parity allow-list."""
    assert metadata_attribute_issues(FieldSnapshot) == ()
    assert {"section", "risk", "description", "experimental"} == EXTRA_METADATA_KEYS
