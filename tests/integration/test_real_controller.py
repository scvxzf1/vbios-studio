"""End-to-end offscreen integration through the real composition root."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fakes import FakePlatform, FakeRunner
from rom_fixtures import synthetic_rom

from vbios_studio.adapters.diff import UpstreamDiffAdapter
from vbios_studio.adapters.profile import UpstreamProfileAdapter
from vbios_studio.adapters.system.linux_loader import LinuxLoaderAdapter
from vbios_studio.adapters.system.windows_registry import WindowsRegistryAdapter
from vbios_studio.adapters.upstream import UpstreamEditorAdapter
from vbios_studio.app.container import build_gui_controller
from vbios_studio.domain.rom import scan_rom
from vbios_studio.ui.controller import UiController


def test_build_gui_controller_wires_real_ports() -> None:
    """The composition root returns a real controller with four production ports."""
    controller = build_gui_controller()
    assert isinstance(controller, UiController)
    assert isinstance(controller.editor, UpstreamEditorAdapter)
    assert isinstance(controller.diff_port, UpstreamDiffAdapter)
    assert isinstance(controller.profile_port, UpstreamProfileAdapter)
    assert isinstance(controller.apply_port, (WindowsRegistryAdapter, LinuxLoaderAdapter))


def test_real_controller_open_edit_generate_and_dry_run(tmp_path: Path) -> None:
    """A real controller can complete the full local workflow without a demo fake."""
    source = tmp_path / "source.rom"
    source.write_bytes(synthetic_rom(copies=2))
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    target = tmp_path / "generated.rom"

    platform = FakePlatform()
    runner = FakeRunner()
    apply = WindowsRegistryAdapter(platform=platform, runner=runner)
    controller = build_gui_controller(apply=apply)
    document = controller.open_path(source)
    assert platform.writable_opens == 0
    assert runner.calls == []
    assert document.architecture == "ada"
    assert any(field.key == "power_max_w" and field.editable for field in document.fields)

    controller.set_experimental_unlocked(True)
    preview = controller.set_value("power_max_w", "100", t3_confirmed=True)
    assert preview.errors == ()
    assert preview.changed[0].key == "power_max_w"

    exported = controller.export_profile()
    assert exported["schema_version"] == 1
    assert exported["architecture"] == "ada"
    assert exported["changes"] == {"power_max_w": "100"}
    assert exported["risks"]["power_max_w"] == "T3"

    controller.reset_changes()
    reapplied = controller.apply_profile(exported, confirmed_t3={"power_max_w"})
    assert reapplied.errors == ()
    assert controller.changes == {"power_max_w": "100"}

    saved = controller.save_as(target)
    assert saved.path == target
    assert target.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    structure = scan_rom(target.read_bytes())
    assert len(structure.images) == 8
    assert all(image.checksum_ok for image in structure.images)

    diff = controller.compare(target)
    assert diff.field_diffs
    assert diff.summary["fields_changed"] == len(diff.field_diffs)

    assert saved.payload_paths
    payload_bytes = saved.payload_paths[0].read_bytes()
    assert apply.payload == payload_bytes
    dry_run = controller.apply_dry_run()
    assert dry_run.action == "load"
    assert dry_run.target.startswith("HKLM\\")
    assert dry_run.bytes_written == len(payload_bytes)
    assert platform.writable_opens == 0
    assert platform.key.mutations == []
    assert platform.restarted == []
    assert runner.calls == []
