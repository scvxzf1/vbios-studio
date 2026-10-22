"""Apply panel: dry-run writes nothing; cancelling confirmation calls nothing."""

from __future__ import annotations

from pathlib import Path

from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.apply_panel import ApplyPanel
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.demo import demo_controller
from vbios_studio.ui.dialogs.confirm_dialog import ConfirmationRules


class TrackingApply:
    def __init__(self) -> None:
        self.dry_run_calls = 0
        self.execute_calls = 0
        self.restore_calls = 0
        self.writes = 0

    def device_status(self):
        from vbios_studio.domain.models import DeviceStatus

        return DeviceStatus(
            0, "NVIDIA GeForce RTX 5090", "10de:2b85", "621.01", "no-override", True
        )

    def dry_run(self):
        from vbios_studio.domain.models import ApplyPreview

        self.dry_run_calls += 1
        return ApplyPreview("load", "HKLM\\...\\0000", {"vbios": "<32 bytes>"}, 40, True, ())

    def execute(self):
        from vbios_studio.domain.models import ApplyResult

        self.execute_calls += 1
        self.writes += 1
        return ApplyResult(True, "override-active", "Override applied.", {})

    def restore(self):
        from vbios_studio.domain.models import ApplyResult

        self.restore_calls += 1
        self.writes += 1
        return ApplyResult(True, "no-override", "Restored.", {})


def test_dry_run_is_the_only_zero_write_preview(controller: UiController) -> None:
    apply = TrackingApply()
    controller.apply_port = apply
    preview = controller.apply_dry_run()
    assert preview.bytes_written == 40
    assert apply.dry_run_calls == 1
    assert apply.execute_calls == 0
    assert apply.writes == 0


def test_cancel_confirmation_does_not_execute(gtk_initialised) -> None:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply.rom"))
    apply = TrackingApply()
    controller.apply_port = apply
    panel = ApplyPanel(
        _, controller, on_error=lambda _title, _exc: None, confirm=lambda _t, _b, _run: None
    )
    panel.refresh()
    panel.request_execute()
    assert apply.execute_calls == 0
    assert apply.writes == 0


def test_confirm_calls_execute_once(gtk_initialised) -> None:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply.rom"))
    apply = TrackingApply()
    controller.apply_port = apply
    panel = ApplyPanel(
        _, controller, on_error=lambda _title, _exc: None, confirm=lambda _t, _b, run: run()
    )
    panel.refresh()
    panel.request_execute()
    assert apply.execute_calls == 1


def test_restore_requires_confirmation(gtk_initialised) -> None:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply.rom"))
    apply = TrackingApply()
    controller.apply_port = apply
    panel = ApplyPanel(
        _, controller, on_error=lambda _title, _exc: None, confirm=lambda _t, _b, _run: None
    )
    panel.refresh()
    panel.request_restore()
    assert apply.restore_calls == 0
    panel2 = ApplyPanel(
        _, controller, on_error=lambda _title, _exc: None, confirm=lambda _t, _b, run: run()
    )
    panel2.refresh()
    panel2.request_restore()
    assert apply.restore_calls == 1


def test_confirmation_rules_require_word_and_checkbox() -> None:
    rules = ConfirmationRules(require_checkbox=True, required_word="CONFIRM")
    assert rules.accepts(True, "CONFIRM") is True
    assert rules.accepts(False, "CONFIRM") is False
    assert rules.accepts(True, "confirm") is False


class RejectingApply(TrackingApply):
    def execute(self):
        from vbios_studio.domain.errors import DomainError

        self.execute_calls += 1
        raise DomainError("APPLY_DENIED", "Write rejected.", "Run as administrator.")


def test_rejected_apply_has_no_partial_write(gtk_initialised) -> None:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply.rom"))
    apply = RejectingApply()
    controller.apply_port = apply
    errors = []
    panel = ApplyPanel(
        _,
        controller,
        on_error=lambda title, exc: errors.append((title, exc)),
        confirm=lambda _title, _body, run: run(),
    )
    panel.refresh()
    panel.request_execute()
    assert apply.execute_calls == 1
    assert apply.writes == 0
    assert errors and errors[0][1].code == "APPLY_DENIED"
