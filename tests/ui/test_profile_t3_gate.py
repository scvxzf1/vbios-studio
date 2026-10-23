"""Preset application must use the same T3 gate as a single-field edit."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from tests.ui.test_profiles import TrackingProfile
from vbios_studio.ui.controller import ConfirmationRequired, UiController
from vbios_studio.ui.demo import DemoEditor


class CountingEditor(DemoEditor):
    """Track how many times a profile is allowed to reach the editor port."""

    def __init__(self) -> None:
        super().__init__()
        self.stage_calls = 0

    def stage(self, changes):
        self.stage_calls += 1
        return super().stage(changes)


def _controller() -> tuple[UiController, CountingEditor, TrackingProfile]:
    editor = CountingEditor()
    profile = TrackingProfile(editor, "Blackwell GB20x")
    controller = UiController(editor, None, profile, None)
    controller.open_path(Path("/tmp/profile-t3.rom"))
    return controller, editor, profile


def _t3_profile() -> dict[str, object]:
    return {
        "schema_version": 1,
        "architecture": "Blackwell GB20x",
        "changes": {"power_max_w": "300"},
    }


def test_locked_profile_is_rejected_before_staging() -> None:
    controller, editor, profile = _controller()
    with pytest.raises(ConfirmationRequired) as raised:
        controller.apply_profile(_t3_profile())
    assert raised.value.field.key == "power_max_w"
    assert len(raised.value.fields) == 1
    assert controller.changes == {}
    assert editor.stage_calls == 0
    assert profile.write_calls == 0


def test_unlocked_but_unconfirmed_profile_is_rejected_before_staging() -> None:
    controller, editor, profile = _controller()
    controller.set_experimental_unlocked(True)
    with pytest.raises(ConfirmationRequired):
        controller.apply_profile(_t3_profile())
    assert controller.changes == {}
    assert editor.stage_calls == 0
    assert profile.write_calls == 0


def test_confirmed_profile_stages_exactly_once() -> None:
    controller, editor, profile = _controller()
    controller.set_experimental_unlocked(True)
    preview = controller.apply_profile(_t3_profile(), confirmed_t3={"power_max_w"})
    assert not preview.errors
    assert controller.changes == {"power_max_w": "300"}
    assert editor.stage_calls == 1
    assert profile.write_calls == 1


def test_profile_dialog_cancel_does_not_stage_and_confirm_does(
    gtk_initialised, monkeypatch
) -> None:
    from vbios_studio.ui import profile_flow
    from vbios_studio.ui.main_window import MainWindow

    controller, editor, profile = _controller()
    controller.set_experimental_unlocked(True)
    window = MainWindow(None, controller)

    class FakeDialog:
        instances: ClassVar[list[FakeDialog]] = []

        def __init__(self, _parent, _title, _body, *, rules, on_confirm, **_kwargs):
            self.rules = rules
            self.on_confirm = on_confirm
            self.__class__.instances.append(self)

        def connect(self, *_args) -> None:
            return None

        def present(self) -> None:
            return None

    monkeypatch.setattr(profile_flow, "ConfirmDialog", FakeDialog)
    FakeDialog.instances.clear()
    window.profile_flow.apply_document(_t3_profile())
    dialog = FakeDialog.instances[-1]
    assert controller.changes == {}
    assert editor.stage_calls == 0
    assert dialog.rules.accepts(True, "power_max_w") is True
    assert dialog.rules.accepts(True, "T3") is True

    dialog.on_confirm()
    assert controller.changes == {"power_max_w": "300"}
    assert editor.stage_calls == 1
    assert profile.write_calls == 1
    window.destroy()
