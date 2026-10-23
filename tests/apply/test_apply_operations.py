"""Operation-list tests: the confirmation source and the writer share one plan."""

from __future__ import annotations

import pytest
from fakes import FakePlatform, FakeRunner

from vbios_studio.adapters.system.windows_plan import (
    ENABLE_GPU_FIRMWARE_VALUE,
    OVERRIDE_VALUE_NAME,
    PREVIOUS_VALUE_NAME,
    REG_BINARY,
    REG_DWORD,
    REG_SZ,
)
from vbios_studio.adapters.system.windows_registry import WindowsRegistryAdapter
from vbios_studio.domain.errors import DomainError
from vbios_studio.ports.apply import Operation

PAYLOAD = b"PAYLOAD"


def _adapter(platform: FakePlatform) -> WindowsRegistryAdapter:
    adapter = WindowsRegistryAdapter(platform=platform, runner=FakeRunner())
    adapter.configure_payload(PAYLOAD)
    return adapter


def _pairs(operations: tuple[Operation, ...]) -> list[tuple[str, str]]:
    return [(operation.op, operation.name) for operation in operations]


def _mutations(platform: FakePlatform) -> list[tuple[str, str]]:
    return list(platform.key.mutations)


def _find(operation: tuple[Operation, ...], name: str) -> Operation:
    return next(item for item in operation if item.name == name)


def test_load_without_backup_reports_conditional_previous_set() -> None:
    """A first load reports the conditional VixLoaderPrevious... set."""
    platform = FakePlatform({ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12)})
    adapter = _adapter(platform)
    operations = adapter.describe_operations("load")
    previous = _find(operations, PREVIOUS_VALUE_NAME)
    assert previous.op == "set"
    assert previous.source == "previous"
    assert _find(operations, OVERRIDE_VALUE_NAME).source == "payload"
    assert _find(operations, ENABLE_GPU_FIRMWARE_VALUE).source == "constant"

    assert adapter.load(PAYLOAD, dry_run=False).ok is True
    assert _pairs(operations) == _mutations(platform)


def test_load_with_backup_omits_previous_set() -> None:
    """An existing backup marker is not written again."""
    platform = FakePlatform(
        {
            ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12),
            PREVIOUS_VALUE_NAME: (REG_SZ, "0x00000012"),
        }
    )
    adapter = _adapter(platform)
    operations = adapter.describe_operations("load")
    assert all(item.name != PREVIOUS_VALUE_NAME for item in operations)
    assert adapter.load(PAYLOAD, dry_run=False).ok is True
    assert _pairs(operations) == _mutations(platform)


def test_load_with_existing_override_reports_legacy_deletes() -> None:
    """Legacy romOverride values are visible in the operation list and are deleted."""
    platform = FakePlatform(
        {
            ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x12),
            "romOverride00": (REG_BINARY, b"old"),
        }
    )
    adapter = _adapter(platform)
    operations = adapter.describe_operations("load")
    legacy = _find(operations, "romOverride00")
    assert legacy.op == "delete"
    assert legacy.source == "legacy"
    assert adapter.load(PAYLOAD, dry_run=False).ok is True
    assert _pairs(operations) == _mutations(platform)


def test_restore_without_override_lists_independent_cleanup() -> None:
    """Restore can be described before any preview and matches its actual mutations."""
    platform = FakePlatform()
    adapter = WindowsRegistryAdapter(platform=platform, runner=FakeRunner())
    operations = adapter.describe_operations("restore")
    assert _pairs(operations) == [("delete", OVERRIDE_VALUE_NAME)]
    assert adapter.restore().ok is True
    assert _pairs(operations) == _mutations(platform)


def test_restore_with_backup_and_override_reports_restore_and_deletes() -> None:
    """Restore exposes the backup value source and all cleanup operations."""
    platform = FakePlatform(
        {
            ENABLE_GPU_FIRMWARE_VALUE: (REG_DWORD, 0x11),
            PREVIOUS_VALUE_NAME: (REG_SZ, "0x00000012"),
            OVERRIDE_VALUE_NAME: (REG_BINARY, PAYLOAD),
            "romOverride00": (REG_BINARY, b"old"),
        }
    )
    adapter = WindowsRegistryAdapter(platform=platform, runner=FakeRunner())
    operations = adapter.describe_operations("restore")
    restored = _find(operations, ENABLE_GPU_FIRMWARE_VALUE)
    assert restored.op == "set"
    assert restored.source == "backup"
    assert _find(operations, OVERRIDE_VALUE_NAME).op == "delete"
    assert _find(operations, "romOverride00").op == "delete"
    assert adapter.restore().ok is True
    assert _pairs(operations) == _mutations(platform)


def test_describe_load_without_payload_fails_closed() -> None:
    """The read-only query cannot invent a load payload."""
    platform = FakePlatform()
    adapter = WindowsRegistryAdapter(platform=platform, runner=FakeRunner())
    with pytest.raises(DomainError) as raised:
        adapter.describe_operations("load")
    assert raised.value.code == "NO_PAYLOAD"
    assert platform.key.mutations == []


def test_describe_rejects_unknown_action() -> None:
    """Only load and restore are valid operation-list actions."""
    adapter = _adapter(FakePlatform())
    with pytest.raises(DomainError) as raised:
        adapter.describe_operations("flash")
    assert raised.value.code == "INVALID_ACTION"
