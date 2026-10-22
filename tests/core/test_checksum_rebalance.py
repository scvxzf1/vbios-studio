"""Last-byte checksum balancing and image-preservation tests."""

from __future__ import annotations

import pytest
from rom_fixtures import synthetic_rom

from vbios_studio.domain.errors import CHECKSUM_OVERLAP, OVERLAPPING_EDITS, DomainError
from vbios_studio.domain.rom import ByteEdit, apply_byte_edits, rebalance_image, scan_rom


def test_only_the_modified_image_checksum_byte_changes(tmp_path) -> None:
    """Touched images sum to zero and every untouched image stays byte-identical."""
    before = synthetic_rom(copies=2)
    structure = scan_rom(before)
    target = structure.images[3]
    edit_at = target.offset + 200
    outcome = apply_byte_edits(before, [ByteEdit(edit_at, b"\xde\xad", "power_max_w")])

    assert outcome.modified_images == (3,)
    assert outcome.checksum_repairs[0].checksum_offset == target.end - 1
    assert outcome.blob != before
    after_structure = scan_rom(outcome.blob)
    assert after_structure.valid is True
    assert all(image.checksum_ok for image in after_structure.images)

    changed = {index for index in range(len(before)) if before[index] != outcome.blob[index]}
    allowed = set(range(edit_at, edit_at + 2)) | {target.end - 1}
    assert changed <= allowed
    assert outcome.blob[target.end - 1] != before[target.end - 1]
    for old, new in zip(structure.images, after_structure.images, strict=True):
        if old.index == target.index:
            continue
        assert new.offset == old.offset
        assert outcome.blob[old.offset : old.end] == before[old.offset : old.end]


def test_rebalance_image_is_idempotent_for_a_balanced_image() -> None:
    """Balancing an already balanced image returns the same bytes."""
    blob = synthetic_rom(copies=1)
    image = scan_rom(blob).images[2]
    assert rebalance_image(blob, image) == blob


def test_checksum_byte_and_overlapping_edits_are_refused() -> None:
    """A field may not write the checksum byte, and ambiguous edits are rejected."""
    blob = synthetic_rom(copies=1)
    image = scan_rom(blob).images[2]
    with pytest.raises(DomainError) as checksum:
        apply_byte_edits(blob, [ByteEdit(image.end - 1, b"\x00", "bad")])
    assert checksum.value.code == CHECKSUM_OVERLAP

    with pytest.raises(DomainError) as overlap:
        apply_byte_edits(
            blob,
            [ByteEdit(image.offset + 10, b"\x01\x02"), ByteEdit(image.offset + 11, b"\x03")],
        )
    assert overlap.value.code == OVERLAPPING_EDITS
