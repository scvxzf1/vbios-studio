"""End-to-end staged edit, save-as and manifest tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rom_fixtures import synthetic_rom

from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.domain.rom import scan_rom


def test_edit_pipeline_writes_a_new_rom_manifest_and_payload(tmp_path: Path) -> None:
    """Stage -> validate -> save keeps the source intact and balances every image."""
    source = tmp_path / "source.rom"
    blob = synthetic_rom(copies=2)
    source.write_bytes(blob)
    original_sha = hashlib.sha256(blob).hexdigest()
    adapter = UpstreamEditorAdapter()
    document = adapter.open(source)
    assert document.sha256 == original_sha

    preview = adapter.stage({"power_max_w": "100"})
    assert preview.errors == ()
    assert [change.key for change in preview.changed] == ["power_max_w"]
    assert preview.changed[0].risk == "T3"
    assert preview.batch_risk == "T3"
    assert preview.requires_t3_confirmation is True
    manifest_preview = adapter.preview()
    assert manifest_preview.modified is True
    assert len(manifest_preview.checksum_repairs) == 2

    target = tmp_path / "generated.rom"
    result = adapter.save_as(target)
    assert target.read_bytes() != b""
    assert result.path == target
    assert result.sha256 == hashlib.sha256(target.read_bytes()).hexdigest()
    assert source.read_bytes() == blob
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_sha
    assert len(result.payload_paths) == 1
    payload_path = result.payload_paths[0]
    assert payload_path.exists() and payload_path.read_bytes()

    manifest_path = target.with_name(target.name + ".json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["modified"] is True
    assert manifest["source_sha256"] == original_sha
    assert manifest["output_sha256"] == result.sha256
    assert manifest["changes"][0]["key"] == "power_max_w"
    assert manifest["changes"][0]["risk"] == "T3"
    assert manifest["batch_risk"] == "T3"
    assert manifest["requires_t3_confirmation"] is True
    assert manifest["target"] == str(target)
    assert manifest["sha256"] == result.sha256
    assert manifest["checksum_repairs"]
    assert manifest["payload"]["sha256"] == hashlib.sha256(payload_path.read_bytes()).hexdigest()
    assert "never flash" in manifest["warning"].lower()

    before_structure = scan_rom(blob)
    after_structure = scan_rom(target.read_bytes())
    assert len(after_structure.images) == len(before_structure.images)
    assert all(image.checksum_ok for image in after_structure.images)
    allowed = {
        offset
        for item in manifest["byte_ranges"]
        for offset in range(item["start"], item["end_exclusive"])
    }
    output = target.read_bytes()
    changed = {index for index in range(len(blob)) if blob[index] != output[index]}
    assert changed <= allowed
    for before, after in zip(before_structure.images, after_structure.images, strict=True):
        assert after.offset == before.offset and after.size == before.size
        changed_in_image = changed & set(range(before.offset, before.end))
        if not changed_in_image:
            assert output[before.offset : before.end] == blob[before.offset : before.end]


def test_unchanged_stage_is_not_marked_modified(tmp_path: Path) -> None:
    """Re-staging the factory value clears the pending change."""
    source = tmp_path / "source.rom"
    source.write_bytes(synthetic_rom(copies=1))
    adapter = UpstreamEditorAdapter()
    adapter.open(source)
    adapter.stage({"power_max_w": "100"})
    unchanged = adapter.stage({"power_max_w": "70"})
    assert unchanged.changed == ()
    assert adapter.preview().modified is False
    adapter.reset()
    assert adapter.preview().modified is False
