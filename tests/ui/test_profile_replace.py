"""Profile replacement must warn before overwriting uncovered staged edits."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from tests.ui.test_profiles import TrackingProfile
from vbios_studio.domain.models import EditPreview
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.demo import DemoEditor
from vbios_studio.ui.profile_flow import ProfileFlow, uncovered_change_keys


class CountingEditor(DemoEditor):
    def __init__(self) -> None:
        super().__init__()
        self.stage_calls = 0

    def stage(self, changes: Mapping[str, str]) -> EditPreview:
        self.stage_calls += 1
        return super().stage(changes)


class FakeWindow:
    def __init__(self, controller: UiController) -> None:
        self.controller = controller
        self.errors: list[tuple[str, Exception]] = []
        self.toasts: list[str] = []

    def _show_error(self, title: str, exc: Exception) -> None:
        self.errors.append((title, exc))

    def _show_field_errors(self, _preview: EditPreview) -> None:
        return None

    def _toast(self, message: str) -> None:
        self.toasts.append(message)

    def _refresh_all(self) -> None:
        return None


def _profile_controller() -> tuple[UiController, CountingEditor, TrackingProfile, FakeWindow]:
    editor = CountingEditor()
    profile = TrackingProfile(editor, "Blackwell GB20x")
    controller = UiController(editor, None, profile, None)
    controller.open_path(Path("/tmp/profile-replace.rom"))
    return controller, editor, profile, FakeWindow(controller)


def test_uncovered_keys_detects_only_uncovered_existing_edits() -> None:
    existing = {"gpc_offset_max_mhz": "100", "power_min_w": "120"}
    document = {"changes": {"power_min_w": "130"}}
    assert uncovered_change_keys(existing, document) == ("gpc_offset_max_mhz",)
    assert uncovered_change_keys({}, document) == ()
    assert uncovered_change_keys(existing, {"changes": "bad"}) == (
        "gpc_offset_max_mhz",
        "power_min_w",
    )


def test_cancel_replace_keeps_changes_and_stage_count(gtk_initialised, monkeypatch) -> None:
    from vbios_studio.ui import profile_flow

    controller, editor, profile, window = _profile_controller()
    controller.set_value("gpc_offset_max_mhz", "150")
    controller.set_value("power_min_w", "110")
    before = dict(controller.changes)
    before_stage = editor.stage_calls
    profile_doc = {
        "schema_version": 1,
        "architecture": "Blackwell GB20x",
        "changes": {"power_min_w": "120"},
    }

    class FakeDialog:
        instances: ClassVar[list[FakeDialog]] = []

        def __init__(self, _parent, title, body, *, on_confirm, **_kwargs):
            self.title = title
            self.body = body
            self.on_confirm = on_confirm
            self.__class__.instances.append(self)

        def present(self) -> None:
            return None

    monkeypatch.setattr(profile_flow, "ConfirmDialog", FakeDialog)
    FakeDialog.instances.clear()
    ProfileFlow(window).apply_document(profile_doc)
    assert FakeDialog.instances
    dialog = FakeDialog.instances[-1]
    assert "2" in dialog.body
    assert "gpc_offset_max_mhz" in dialog.body
    assert "power_min_w" not in dialog.body
    # Cancel: the fake dialog is never confirmed.
    assert controller.changes == before
    assert editor.stage_calls == before_stage
    assert profile.write_calls == 0


def test_confirm_replace_applies_profile(gtk_initialised, monkeypatch) -> None:
    from vbios_studio.ui import profile_flow

    controller, editor, profile, window = _profile_controller()
    controller.set_value("gpc_offset_max_mhz", "150")
    before_stage = editor.stage_calls
    profile_doc = {
        "schema_version": 1,
        "architecture": "Blackwell GB20x",
        "changes": {"power_min_w": "120"},
    }

    class FakeDialog:
        instances: ClassVar[list[FakeDialog]] = []

        def __init__(self, _parent, _title, _body, *, on_confirm, **_kwargs):
            self.on_confirm = on_confirm
            self.__class__.instances.append(self)

        def present(self) -> None:
            return None

    monkeypatch.setattr(profile_flow, "ConfirmDialog", FakeDialog)
    FakeDialog.instances.clear()
    ProfileFlow(window).apply_document(profile_doc)
    FakeDialog.instances[-1].on_confirm()
    assert controller.changes == {"power_min_w": "120"}
    assert editor.stage_calls == before_stage + 1
    assert profile.write_calls == 1
