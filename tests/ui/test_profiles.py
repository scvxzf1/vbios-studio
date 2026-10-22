"""Preset profile round-trip, architecture guard and schema rejection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import DocumentSnapshot, EditPreview
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.demo import DemoEditor, demo_snapshot


class TrackingProfile:
    """A strict profile adapter that counts attempted writes."""

    def __init__(self, editor: DemoEditor, expected_architecture: str) -> None:
        self.editor = editor
        self.expected_architecture = expected_architecture
        self.write_calls = 0
        self._staged: dict[str, str] = {}

    def export_changes(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "architecture": self.expected_architecture,
            "changes": dict(self._staged),
        }

    def apply_profile(self, document: Mapping[str, Any]) -> EditPreview:
        if document.get("schema_version") != 1:
            raise DomainError(
                "PROFILE_SCHEMA", "Unsupported preset schema.", "Use schema_version 1."
            )
        if document.get("architecture") != self.expected_architecture:
            raise DomainError(
                "PROFILE_ARCH_MISMATCH",
                "Preset architecture does not match.",
                "Use a preset for this GPU.",
            )
        changes = document.get("changes") or {}
        if not isinstance(changes, dict):
            raise DomainError("PROFILE_SCHEMA", "changes must be an object.", "Fix the preset.")
        self.write_calls += 1
        return self.editor.stage({str(key): str(value) for key, value in changes.items()})

    def track(self, changes: Mapping[str, str]) -> None:
        self._staged = dict(changes)


def _controller_with(editor: DemoEditor, profile: TrackingProfile) -> UiController:
    controller = UiController(editor, None, profile, None)
    controller.open_path(Path("/tmp/profile-source.rom"))
    return controller


def test_profile_roundtrip_preserves_changes_and_bytes(tmp_path: Path) -> None:
    editor1 = DemoEditor()
    profile1 = TrackingProfile(editor1, "Blackwell GB20x")
    controller1 = _controller_with(editor1, profile1)
    controller1.set_value("power_min_w", "120")
    controller1.set_value("gpc_offset_max_mhz", "250")
    profile1.track(controller1.changes)
    exported = profile1.export_changes()
    assert exported["schema_version"] == 1
    assert exported["changes"] == controller1.changes

    editor2 = DemoEditor()
    profile2 = TrackingProfile(editor2, "Blackwell GB20x")
    controller2 = _controller_with(editor2, profile2)
    preview = controller2.apply_profile(exported)
    assert not preview.errors
    assert controller2.changes == controller1.changes

    saved1 = controller1.save_as(tmp_path / "a.rom")
    saved2 = controller2.save_as(tmp_path / "b.rom")
    assert saved1.sha256 == saved2.sha256


def test_cross_architecture_is_rejected_with_zero_writes() -> None:
    editor = DemoEditor()
    profile = TrackingProfile(editor, "Ada AD10x")
    controller = _controller_with(editor, profile)
    ada: DocumentSnapshot = demo_snapshot(Path("/tmp/ada.rom"), variant=1)
    controller.snapshot = ada
    editor.snapshot = ada
    with pytest.raises(DomainError) as raised:
        controller.apply_profile(
            {
                "schema_version": 1,
                "architecture": "Blackwell GB20x",
                "changes": {"power_min_w": "120"},
            }
        )
    assert raised.value.code == "PROFILE_ARCH_MISMATCH"
    assert profile.write_calls == 0
    assert controller.changes == {}


def test_bad_schema_is_rejected_with_zero_writes() -> None:
    editor = DemoEditor()
    profile = TrackingProfile(editor, "Blackwell GB20x")
    controller = _controller_with(editor, profile)
    with pytest.raises(DomainError) as raised:
        controller.apply_profile(
            {"schema_version": 999, "architecture": "Blackwell GB20x", "changes": {}}
        )
    assert raised.value.code == "PROFILE_SCHEMA"
    assert profile.write_calls == 0
    assert controller.changes == {}


def test_profile_apply_is_undoable() -> None:
    editor = DemoEditor()
    profile = TrackingProfile(editor, "Blackwell GB20x")
    controller = _controller_with(editor, profile)
    controller.set_value("power_min_w", "110")
    controller.apply_profile(
        {"schema_version": 1, "architecture": "Blackwell GB20x", "changes": {"power_min_w": "130"}}
    )
    assert controller.changes == {"power_min_w": "130"}
    assert controller.undo() is True
    assert controller.changes == {"power_min_w": "110"}
