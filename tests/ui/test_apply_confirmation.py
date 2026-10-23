"""Apply confirmation text comes from the apply port's exact operation plan."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.apply.fakes import FakePlatform, FakeRunner
from vbios_studio.adapters.system.windows_plan import (
    ENABLE_GPU_FIRMWARE_VALUE,
    OVERRIDE_VALUE_NAME,
    PREVIOUS_VALUE_NAME,
    REG_BINARY,
    REG_DWORD,
    REG_SZ,
)
from vbios_studio.adapters.system.windows_registry import WindowsRegistryAdapter
from vbios_studio.i18n import gettext as _
from vbios_studio.ui.components.apply_panel import ApplyPanel
from vbios_studio.ui.demo import demo_controller

PAYLOAD = b"PAYLOAD"


def _t3_panel() -> ApplyPanel:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply-t3-banner.rom"))
    controller.set_experimental_unlocked(True)
    controller.set_value("power_max_w", "300", t3_confirmed=True)
    controller.set_value("power_default_w", "350", t3_confirmed=True)
    panel = ApplyPanel(_, controller, on_error=lambda _title, _exc: None)
    panel.refresh()
    return panel


def test_t3_banner_lists_every_t3_key_old_new_and_risk(gtk_initialised) -> None:
    panel = _t3_panel()
    text = panel.t3_banner_label.get_text()
    assert "power_max_w" in text
    assert "power_default_w" in text
    assert "250 → 300" in text
    assert "250 → 350" in text
    assert "[T3]" in text
    assert panel.t3_banner.get_visible() is True


def test_t3_banner_is_hidden_without_t3_changes(gtk_initialised) -> None:
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply-no-t3.rom"))
    panel = ApplyPanel(_, controller, on_error=lambda _title, _exc: None)
    panel.refresh()
    assert panel.t3_banner.get_visible() is False


def test_final_confirmation_body_lists_t3_and_operations(gtk_initialised) -> None:
    panel = _t3_panel()
    bodies: list[str] = []
    panel.confirm = lambda _title, body, _run: bodies.append(body)
    panel.dry_run()
    panel.request_execute()
    assert bodies
    body = bodies[-1]
    assert "power_max_w" in body
    assert "power_default_w" in body
    assert "250 → 300" in body
    assert "[T3]" in body
    assert "SET vbios (source: payload)" in body
    assert "SET EnableGpuFirmware (source: constant)" in body


class CountingAdapter(WindowsRegistryAdapter):
    """Real Windows adapter with a restore call counter for cancel assertions."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.restore_calls = 0

    def restore(self):
        self.restore_calls += 1
        return super().restore()


def _real_panel(
    platform: FakePlatform,
    *,
    adapter_class: type[CountingAdapter] = CountingAdapter,
) -> tuple[ApplyPanel, CountingAdapter]:
    adapter = adapter_class(platform=platform, runner=FakeRunner())
    adapter.configure_payload(PAYLOAD)
    controller = demo_controller()
    controller.open_path(Path("/tmp/apply-production.rom"))
    controller.apply_port = adapter
    panel = ApplyPanel(_, controller, on_error=lambda _title, _exc: None)
    panel.refresh()
    return panel, adapter


def _actual_mutations(platform: FakePlatform) -> set[tuple[str, str]]:
    return {(operation, name) for operation, name in platform.key.mutations}


def test_backup_none_confirmation_lists_three_keys_and_matches_writes(
    gtk_initialised,
) -> None:
    platform = FakePlatform({ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12)})
    panel, adapter = _real_panel(platform)
    expected = adapter.describe_operations("load")
    assert {operation.name for operation in expected} == {
        PREVIOUS_VALUE_NAME,
        OVERRIDE_VALUE_NAME,
        ENABLE_GPU_FIRMWARE_VALUE,
    }

    bodies: list[str] = []
    panel.confirm = lambda _title, body, run: (bodies.append(body), run())
    panel.dry_run()
    panel.request_execute()
    actual = _actual_mutations(platform)
    assert actual == {(operation.op, operation.name) for operation in expected}
    assert len(expected) == 3
    for operation in expected:
        assert operation.name in bodies[-1]


def test_existing_backup_omits_previous_key_and_matches_writes(gtk_initialised) -> None:
    platform = FakePlatform(
        {
            ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12),
            PREVIOUS_VALUE_NAME: (REG_SZ, "0x00000012"),
        }
    )
    panel, adapter = _real_panel(platform)
    expected = adapter.describe_operations("load")
    assert PREVIOUS_VALUE_NAME not in {operation.name for operation in expected}

    bodies: list[str] = []
    panel.confirm = lambda _title, body, run: (bodies.append(body), run())
    panel.dry_run()
    panel.request_execute()
    assert _actual_mutations(platform) == {(operation.op, operation.name) for operation in expected}
    assert PREVIOUS_VALUE_NAME not in bodies[-1]


@pytest.mark.parametrize("entry", ["direct", "after_apply", "after_refresh"])
def test_restore_confirmation_uses_live_operations_and_cancel_is_zero_call(
    gtk_initialised, entry: str
) -> None:
    if entry == "after_apply":
        platform = FakePlatform({ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12)})
    else:
        platform = FakePlatform(
            {
                ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12),
                PREVIOUS_VALUE_NAME: (REG_SZ, "0x00000012"),
                OVERRIDE_VALUE_NAME: (REG_BINARY, PAYLOAD),
                "romOverride00": (REG_BINARY, b"old"),
            }
        )
    panel, adapter = _real_panel(platform)

    if entry == "after_apply":
        panel.confirm = lambda _title, _body, run: run()
        panel.dry_run()
        panel.request_execute()
    elif entry == "after_refresh":
        panel.refresh()

    expected = adapter.describe_operations("restore")
    bodies: list[str] = []
    panel.confirm = lambda _title, body, _run: bodies.append(body)
    before = list(platform.key.mutations)
    panel.request_restore()

    assert bodies
    body = bodies[-1]
    for operation in expected:
        assert operation.name in body
    assert adapter.restore_calls == 0
    assert platform.key.mutations == before
