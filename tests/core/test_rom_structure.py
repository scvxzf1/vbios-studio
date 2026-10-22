"""ROM image-chain scanning and read-only degradation tests."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from rom_fixtures import synthetic_rom

from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.rom import scan_rom


def _repair(data: bytearray, offset: int) -> bytes:
    image = scan_rom(bytes(data)).image_at(offset)
    assert image is not None
    data[image.end - 1] = (data[image.end - 1] - sum(data[image.offset : image.end])) & 0xFF
    return bytes(data)


def _unknown_architecture_rom() -> bytes:
    blob = bytearray(synthetic_rom(copies=1))
    struct.pack_into("<H", blob, 512 + 32 + 6, 0x1234)  # legacy PCIR device ID
    return _repair(blob, 512)


def test_single_and_multi_bank_chains_are_bounded_and_balanced() -> None:
    """Every image in a single or duplicate NVIDIA bank has a zero 8-bit sum."""
    single = scan_rom(synthetic_rom(copies=1))
    assert single.valid is True
    assert single.chains == 1
    assert [image.kind for image in single.images] == [
        "legacy",
        "efi",
        "npds-data",
        "npds-data",
    ]
    assert all(image.checksum_ok for image in single.images)
    assert single.images[0].offset == 512
    assert single.images[-1].end == 11776

    multi = scan_rom(synthetic_rom(copies=3))
    assert multi.valid is True
    assert multi.chains == 3
    assert len(multi.images) == 12
    assert all(image.checksum_ok for image in multi.images)


def test_unknown_architecture_degrades_to_a_read_only_catalog(tmp_path: Path) -> None:
    """An unrecognized PCI identity yields a structural report, not an exception."""
    source = tmp_path / "unknown.rom"
    source.write_bytes(_unknown_architecture_rom())
    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    assert document.architecture == "unknown"
    assert document.pci_id == "10de:1234"
    assert len(document.images) == 4
    assert document.fields == ()
    catalog = adapter.catalog_json()
    json.dumps(catalog)
    assert catalog["read_only"] is True
    assert catalog["read_only_code"] == "UNSUPPORTED_ARCHITECTURE"
    assert catalog["structure"]["valid"] is True


def test_recognized_rom_exposes_a_field_catalog_with_json_round_trip(tmp_path: Path) -> None:
    """A recognized dual-bank ROM exposes images, sections and risk-annotated fields."""
    source = tmp_path / "ada.rom"
    source.write_bytes(synthetic_rom(copies=2))
    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    assert document.architecture == "ada"
    assert document.pci_id == "10de:28b0"
    assert len(document.images) == 8
    assert document.fields
    assert any(field.editable for field in document.fields)
    assert {field.risk for field in document.fields} <= {"T0", "T1", "T2", "T3"}
    catalog = adapter.catalog_json()
    assert catalog["read_only"] is False
    assert len(catalog["fields"]) == len(document.fields)
    assert {image["checksum_ok"] for image in catalog["structure"]["images"]} == {True}
    json.loads(json.dumps(catalog))


def _single_image_rom() -> bytes:
    data = bytearray(512 + 2048)
    start = 512
    data[start : start + 2] = b"\x55\xaa"
    struct.pack_into("<H", data, start + 0x18, 0x20)
    header = start + 0x20
    data[header : header + 4] = b"PCIR"
    struct.pack_into("<HHHH", data, header + 4, 0x10DE, 0x1DB1, 0, 0x18)
    struct.pack_into("<H", data, header + 0x10, 4)
    data[header + 0x15] = 0x80
    data[start + 2047] = -sum(data[start : start + 2047]) & 0xFF
    return bytes(data)


def test_single_image_dump_is_reported_read_only(tmp_path: Path) -> None:
    """A one-image NVIDIA dump is parsed as a read-only structure, not rejected."""
    structure = scan_rom(_single_image_rom())
    assert structure.valid is True
    assert len(structure.images) == 1
    source = tmp_path / "single.rom"
    source.write_bytes(_single_image_rom())
    document = UpstreamEditorAdapter().open(source)
    assert len(document.images) == 1
    assert document.architecture == "unknown"
