"""Negative tests: tampered signatures, cross-architecture and out-of-bounds edits."""

from __future__ import annotations

from pathlib import Path

import pytest
from rom_fixtures import synthetic_rom

from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.errors import DomainError


def _expected_names(target: Path) -> tuple[Path, Path, Path]:
    return (
        target,
        target.with_name(target.name + ".json"),
        target.with_name(target.stem + "-loader.bin"),
    )


def _assert_no_outputs(target: Path) -> None:
    assert not any(path.exists() for path in _expected_names(target))


def _corrupt_npds_magic(blob: bytes) -> bytes:
    data = bytearray(blob)
    data[3584 + 32 : 3584 + 36] = b"XXXX"  # NPDS magic of the last data image
    return bytes(data)


def test_tampered_signature_area_is_refused_without_writing(tmp_path: Path) -> None:
    """Changing the source signature after staging makes save fail with no output."""
    source = tmp_path / "source.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    adapter.open(source)
    assert adapter.stage({"power_max_w": "100"}).errors == ()

    tampered = bytearray(source.read_bytes())
    tampered[512 + 1] = 0xAB  # legacy 55 AA signature
    source.write_bytes(tampered)
    target = tmp_path / "generated.rom"
    with pytest.raises(DomainError) as exc:
        adapter.save_as(target)
    assert exc.value.code == "SOURCE_CHANGED"
    assert not any(path.exists() for path in _expected_names(target))


def test_tampered_image_header_opens_as_read_only_and_refuses_edits(tmp_path: Path) -> None:
    """A broken NPDS header becomes a read-only structural report and stays unsaved."""
    source = tmp_path / "broken.rom"
    source.write_bytes(_corrupt_npds_magic(synthetic_rom(copies=1)))
    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    assert document.architecture == "unknown"
    assert document.fields == ()
    preview = adapter.stage({"power_max_w": "100"})
    assert preview.changed == ()
    assert preview.errors
    assert preview.errors[0].code in {"UNSUPPORTED_FORMAT", "UNSUPPORTED_ARCHITECTURE"}
    target = tmp_path / "generated.rom"
    with pytest.raises(DomainError) as exc:
        adapter.save_as(target)
    assert exc.value.code == "NO_CHANGES"
    _assert_no_outputs(target)


def test_cross_architecture_field_is_refused(tmp_path: Path) -> None:
    """An Ampere-only field cannot be staged on a single-rail Ada image."""
    source = tmp_path / "ada.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    adapter.open(source)
    preview = adapter.stage({"msvdd_rel_max_mv": "900"})
    assert preview.changed == ()
    assert preview.errors[0].code == "FIELD_READ_ONLY"
    target = tmp_path / "generated.rom"
    with pytest.raises(DomainError) as exc:
        adapter.save_as(target)
    assert exc.value.code == "NO_CHANGES"
    _assert_no_outputs(target)

    ampere = tmp_path / "ampere.rom"
    ampere.write_bytes(synthetic_rom(family="ampere", copies=1))
    other = UpstreamEditorAdapter()
    other.open(ampere)
    blocked = other.stage({"board_fixed_rated_w": "300"})
    assert blocked.errors[0].code == "FIELD_READ_ONLY"
    _assert_no_outputs(tmp_path / "ampere-out.rom")


def test_out_of_bounds_value_is_refused(tmp_path: Path) -> None:
    """A value above the encoding ceiling is rejected before any file is written."""
    source = tmp_path / "ada.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    adapter.open(source)
    preview = adapter.stage({"power_max_w": "9999999"})
    assert preview.changed == ()
    assert preview.errors[0].code == "OUT_OF_BOUNDS"
    target = tmp_path / "generated.rom"
    with pytest.raises(DomainError) as exc:
        adapter.save_as(target)
    assert exc.value.code == "NO_CHANGES"
    _assert_no_outputs(target)


def test_negative_values_and_overwrite_are_refused(tmp_path: Path) -> None:
    """Negative values fail bounds; an existing destination is never overwritten."""
    source = tmp_path / "ada.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    adapter.open(source)
    assert adapter.stage({"power_max_w": "-5"}).errors[0].code == "OUT_OF_BOUNDS"

    adapter.stage({"power_max_w": "100"})
    target = tmp_path / "generated.rom"
    target.write_bytes(b"KEEP")
    with pytest.raises(DomainError) as exc:
        adapter.save_as(target)
    assert exc.value.code == "OUTPUT_EXISTS"
    assert target.read_bytes() == b"KEEP"
    assert not target.with_name(target.name + ".json").exists()
