"""Windows registry override protocol tests using an in-memory backend."""

from __future__ import annotations

import hashlib

import pytest
from fakes import FakePlatform, FakeRunner

from vbios_studio.adapters.system.windows_plan import REG_BINARY, REG_DWORD, REG_SZ
from vbios_studio.adapters.system.windows_registry import (
    ENABLE_GPU_FIRMWARE_VALUE,
    FIRMWARE_OVERRIDE,
    OVERRIDE_VALUE_NAME,
    PREVIOUS_VALUE_NAME,
    WindowsRegistryAdapter,
)
from vbios_studio.domain.models import ApplyPreview, ApplyResult


def _adapter(platform: FakePlatform) -> WindowsRegistryAdapter:
    return WindowsRegistryAdapter(platform=platform, runner=FakeRunner())


def test_dry_run_performs_zero_writes() -> None:
    """Dry-run renders the plan but never opens the key for writing."""
    platform = FakePlatform({ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12)})
    preview = _adapter(platform).load(b"PAYLOAD", dry_run=True)
    assert isinstance(preview, ApplyPreview)
    assert preview.action == "load"
    assert preview.bytes_written == len(b"PAYLOAD")
    assert preview.values["VixLoaderPreviousEnableGpuFirmware"]["value"] == "0x00000012"
    assert preview.values["EnableGpuFirmware"] == {"type": "REG_DWORD", "value": FIRMWARE_OVERRIDE}
    assert preview.values["device"] == "NVIDIA GeForce RTX 4090"
    assert "restart_device" in preview.values
    assert platform.writable_opens == 0
    assert platform.key.mutations == []
    assert platform.key.values[ENABLE_GPU_FIRMWARE_VALUE] == (REG_DWORD, 0x12)


def test_load_writes_protocol_and_reads_back() -> None:
    """A real load writes all protocol values, flushes and restarts once."""
    platform = FakePlatform(
        {
            ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12),
            "romOverride00": (REG_BINARY, b"old"),
        }
    )
    result = _adapter(platform).load(b"PAYLOAD", dry_run=False)
    assert isinstance(result, ApplyResult)
    assert result.ok is True
    assert result.state == "override-active"
    assert platform.writable_opens == 1
    assert platform.key.flushes == 1
    assert platform.key.values[OVERRIDE_VALUE_NAME] == (REG_BINARY, b"PAYLOAD")
    assert platform.key.values[ENABLE_GPU_FIRMWARE_VALUE] == (REG_DWORD, FIRMWARE_OVERRIDE)
    assert platform.key.values[PREVIOUS_VALUE_NAME] == (REG_SZ, "0x00000012")
    assert "romOverride00" not in platform.key.values
    assert result.details["payload_sha256"] == hashlib.sha256(b"PAYLOAD").hexdigest()
    assert platform.restarted


@pytest.mark.parametrize("initial", [(REG_DWORD, 0x11), (REG_DWORD, 0x00), None])
def test_unload_restores_the_first_load_value(initial: tuple[int, int] | None) -> None:
    """Unload restores 0x11/other values and deletes when the original was absent."""
    values = {} if initial is None else {ENABLE_GPU_FIRMWARE_VALUE: initial}
    platform = FakePlatform(values)
    adapter = _adapter(platform)
    assert adapter.load(b"PAYLOAD", dry_run=False).ok is True
    assert platform.key.values[PREVIOUS_VALUE_NAME][1] == (
        "absent" if initial is None else f"{initial[1]:#010x}"
    )
    result = adapter.unload(dry_run=False)
    assert isinstance(result, ApplyResult)
    assert result.ok is True
    assert result.state == "no-override"
    assert platform.key.values.get(ENABLE_GPU_FIRMWARE_VALUE) == initial
    assert OVERRIDE_VALUE_NAME not in platform.key.values
    assert PREVIOUS_VALUE_NAME not in platform.key.values
    assert len(platform.restarted) == 2


def test_elevation_is_reported_without_writes() -> None:
    """A non-elevated load returns a structured error and writes nothing."""
    platform = FakePlatform(admin=False)
    result = _adapter(platform).load(b"PAYLOAD", dry_run=False)
    assert isinstance(result, ApplyResult)
    assert result.ok is False
    assert result.details["code"] == "ELEVATION_REQUIRED"
    assert "Administrator" in result.details["hint"]
    assert platform.writable_opens == 0
    assert platform.key.mutations == []
    assert platform.restarted == []


def test_readback_mismatch_is_structured_and_does_not_restart() -> None:
    """A backend that silently drops writes is detected by readback."""
    platform = FakePlatform()
    platform.key.drop_writes = True
    result = _adapter(platform).load(b"PAYLOAD", dry_run=False)
    assert isinstance(result, ApplyResult)
    assert result.ok is False
    assert result.details["code"] == "READBACK_MISMATCH"
    assert platform.restarted == []
    assert platform.key.mutations


def test_restart_failure_is_structured() -> None:
    """A failed pnputil restart is reported after the values are verified."""
    platform = FakePlatform(restart_code=1)
    result = _adapter(platform).load(b"PAYLOAD", dry_run=False)
    assert isinstance(result, ApplyResult)
    assert result.ok is False
    assert result.details["code"] == "RESTART_FAILED"
    assert platform.key.values[OVERRIDE_VALUE_NAME] == (REG_BINARY, b"PAYLOAD")


def test_unload_dry_run_is_zero_write() -> None:
    """After a load, an unload dry-run adds no mutation."""
    platform = FakePlatform()
    adapter = _adapter(platform)
    adapter.load(b"PAYLOAD", dry_run=False)
    before = list(platform.key.mutations)
    preview = adapter.unload(dry_run=True)
    assert isinstance(preview, ApplyPreview)
    assert preview.action == "unload"
    assert platform.key.mutations == before


def test_verify_distinguishes_no_override_match_and_mismatch() -> None:
    """Verify returns the three upstream override states."""
    empty = FakePlatform()
    no_override = _adapter(empty).verify(b"anything")
    assert no_override.state == "no-override"

    platform = FakePlatform()
    adapter = _adapter(platform)
    assert adapter.load(b"PAYLOAD", dry_run=False).ok is True
    matching = adapter.verify(b"PAYLOAD")
    assert matching.ok is True
    assert matching.state == "override-active"
    assert matching.details["code"] == "VERIFY_MATCH"
    different = adapter.verify(b"OTHER")
    assert different.state == "override-not-active"
    assert different.details["code"] == "VERIFY_MISMATCH"


def test_execute_without_dry_run_ticket_is_refused_with_zero_writes() -> None:
    """A port-level execute cannot write without a dry-run ticket."""
    platform = FakePlatform()
    adapter = _adapter(platform)
    adapter.configure_payload(b"PAYLOAD")
    result = adapter.execute()
    assert isinstance(result, ApplyResult)
    assert result.ok is False
    assert result.details["code"] == "CONFIRMATION_REQUIRED"
    assert platform.writable_opens == 0
    assert platform.key.mutations == []
    assert platform.restarted == []


def test_execute_consumes_one_shot_ticket_and_binds_the_target() -> None:
    """Execute succeeds once after dry-run, then a new ticket is required."""
    platform = FakePlatform()
    adapter = _adapter(platform)
    adapter.configure_payload(b"PAYLOAD")
    preview = adapter.dry_run()
    assert isinstance(preview, ApplyPreview)
    first = adapter.execute()
    assert first.ok is True
    assert platform.writable_opens == 1
    second = adapter.execute()
    assert second.ok is False
    assert second.details["code"] == "CONFIRMATION_REQUIRED"
    assert platform.writable_opens == 1

    assert adapter.dry_run().bytes_written == len(b"PAYLOAD")
    adapter.adapter_index = 3
    mismatch = adapter.execute()
    assert mismatch.ok is False
    assert mismatch.details["code"] == "CONFIRMATION_MISMATCH"
    assert platform.writable_opens == 1


def test_verify_reads_the_running_image_from_the_platform() -> None:
    """The adapter's verify hook uses the platform's running-image reader."""
    platform = FakePlatform()
    adapter = _adapter(platform)
    assert adapter.load(b"PAYLOAD", dry_run=False).ok is True
    platform.running_image = b"PAYLOAD"
    result = adapter.verify()
    assert result.ok is True
    assert result.state == "override-active"
    assert result.details["code"] == "VERIFY_MATCH"


def test_dry_run_ticket_rejects_payload_hash_mismatch_with_zero_writes() -> None:
    """Changing the payload after the preview invalidates the ticket."""
    platform = FakePlatform()
    adapter = _adapter(platform)
    adapter.configure_payload(b"PAYLOAD")
    assert isinstance(adapter.dry_run(), ApplyPreview)
    adapter.payload = b"TAMPERED"
    result = adapter.execute()
    assert result.ok is False
    assert result.details["code"] == "CONFIRMATION_MISMATCH"
    assert platform.writable_opens == 0
    assert platform.key.mutations == []
    assert platform.restarted == []
