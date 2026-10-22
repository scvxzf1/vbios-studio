"""Frozen comparison structure: field_diffs and image_diffs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from vbios_studio.domain.models import FieldSnapshot
from vbios_studio.ui.demo import demo_snapshot
from vbios_studio.ui.diff_model import compare


def test_identical_roms_return_empty_lists() -> None:
    left = demo_snapshot(Path("/tmp/left.rom"))
    right = demo_snapshot(Path("/tmp/right.rom"))
    result = compare(left, right)
    assert result == {"field_diffs": [], "image_diffs": []}


def test_one_field_difference_has_frozen_structure() -> None:
    left = demo_snapshot(Path("/tmp/left.rom"))
    right = demo_snapshot(Path("/tmp/right.rom"), variant=1)
    result = compare(left, right)
    assert len(result["field_diffs"]) == 1
    item = result["field_diffs"][0]
    assert set(item) == {"key", "label", "left", "right", "risk", "changed"}
    assert item["key"] == "power_max_w"
    assert item["left"] == "250"
    assert item["right"] == "275"
    assert item["changed"] is True
    assert result["image_diffs"] == []


def test_image_difference_has_type_size_and_checksums() -> None:
    left = demo_snapshot(Path("/tmp/left.rom"))
    images = list(left.images)
    images[1] = replace(images[1], checksum_ok=False)
    right = replace(left, images=tuple(images))
    result = compare(left, right)
    assert result["field_diffs"] == []
    assert len(result["image_diffs"]) == 1
    item = result["image_diffs"][0]
    assert set(item) == {"index", "type", "size", "checksum_left", "checksum_right", "equal"}
    assert item == {
        "index": 2,
        "type": "efi",
        "size": 262144,
        "checksum_left": "balanced",
        "checksum_right": "unbalanced",
        "equal": False,
    }


def test_left_and_right_only_fields_are_reported() -> None:
    left = demo_snapshot(Path("/tmp/left.rom"))
    right = replace(
        left, fields=tuple(field for field in left.fields if field.key != "power_min_w")
    )
    result = compare(left, right)
    item = next(item for item in result["field_diffs"] if item["key"] == "power_min_w")
    assert item["left"] == "100"
    assert item["right"] is None
    assert item["changed"] is True


def test_added_field_has_deterministic_right_only_representation() -> None:
    left = demo_snapshot(Path("/tmp/left.rom"))
    extra = FieldSnapshot(
        key="fan_curve_4",
        label="Fan curve 4",
        section="fans",
        unit="%",
        current="55",
        default="50",
        minimum="0",
        maximum="100",
        risk="T3",
        offset=0x4000,
        editable=True,
        opt_in=True,
        experimental=True,
        description="Extra fan curve.",
    )
    right = replace(left, fields=(*left.fields, extra))
    result = compare(left, right)
    item = next(item for item in result["field_diffs"] if item["key"] == "fan_curve_4")
    assert item["left"] is None
    assert item["right"] == "55"
    assert item["risk"] == "T3"
    assert item["changed"] is True
