"""Pure planning helpers for the Windows registry override protocol.

This module builds the exact write/delete steps used by
:class:`vbios_studio.adapters.system.windows_registry.WindowsRegistryAdapter`.
It is deliberately separate so the adapter stays small and the steps can be
inspected by tests without opening a real registry.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from vbios_studio.domain.errors import IO_ERROR
from vbios_studio.domain.models import ApplyPreview, ApplyResult

REG_SZ = 1
REG_BINARY = 3
REG_DWORD = 4
REGISTRY_CLASS_KEY = (
    r"SYSTEM\CurrentControlSet\Control\Class"
    r"\{4d36e968-e325-11ce-bfc1-08002be10318}"
)
OVERRIDE_VALUE_NAME = "vbios"
ENABLE_GPU_FIRMWARE_VALUE = "EnableGpuFirmware"
PREVIOUS_VALUE_NAME = "VixLoaderPreviousEnableGpuFirmware"
FIRMWARE_OVERRIDE = 0x11
ABSENT = "absent"
PATCH_RECORDS = tuple(f"romOverride{i:02X}" for i in range(256))
TYPE_NAMES = {REG_SZ: "REG_SZ", REG_BINARY: "REG_BINARY", REG_DWORD: "REG_DWORD"}


@dataclass(frozen=True, slots=True)
class WindowsAdapterInfo:
    """One NVIDIA display adapter and its driver registry key."""

    index: int
    name: str
    pci_id: str
    driver_version: str | None
    instance_id: str
    driver_key: str
    supports_payload: bool = True


class RegistryKey(Protocol):
    """The subset of a registry key used by the override protocol."""

    def get(self, name: str) -> tuple[int, Any] | None:
        """Return ``(type, value)`` or ``None`` when absent."""

    def set(self, name: str, kind: int, value: Any) -> None:
        """Write one value."""

    def delete(self, name: str) -> bool:
        """Delete one value, returning whether it existed."""

    def flush(self) -> None:
        """Flush the key."""

    def close(self) -> None:
        """Close the key."""


class WindowsPlatform(Protocol):
    """Injected Windows platform boundary."""

    def adapters(self) -> Sequence[WindowsAdapterInfo]:
        """Return NVIDIA display adapters in stable order."""

    def open_key(self, adapter: WindowsAdapterInfo, write: bool = False) -> RegistryKey:
        """Open the adapter's driver key."""

    def is_admin(self) -> bool:
        """Return whether the current process is elevated."""

    def restart_device(self, instance_id: str) -> tuple[int | None, str]:
        """Restart one device and return ``(exit code, output)``."""


@dataclass(frozen=True, slots=True)
class Step:
    """One registry operation in a plan."""

    operation: str
    name: str
    kind: int = 0
    value: Any = None


@dataclass(frozen=True, slots=True)
class RegistryPlan:
    """A fully rendered load/unload plan."""

    action: str
    adapter: WindowsAdapterInfo
    steps: tuple[Step, ...]
    values: Mapping[str, Any]
    bytes_written: int
    warnings: tuple[str, ...] = ()
    restart_required: bool = True


def error(code: str, message: str, hint: str = "") -> ApplyResult:
    """Return a structured refusal without raising."""
    return ApplyResult(False, "refused", message, {"code": code, "hint": hint})


def as_dword(item: tuple[int, Any] | None) -> int | None:
    """Return a well-formed REG_DWORD integer, else ``None``."""
    return (
        item[1] if item is not None and item[0] == REG_DWORD and isinstance(item[1], int) else None
    )


def saved_previous(item: tuple[int, Any] | None) -> tuple[bool, int | str | None]:
    """Validate the saved previous-value marker."""
    if item is None:
        return True, None
    if item[0] != REG_SZ or not isinstance(item[1], str):
        return False, None
    if item[1] == ABSENT:
        return True, ABSENT
    try:
        return True, int(item[1], 16)
    except ValueError:
        return False, None


def override_names(key: RegistryKey) -> tuple[str, ...]:
    """Return existing romOverride00-FF value names."""
    return tuple(name for name in PATCH_RECORDS if key.get(name) is not None)


def _read_key(
    platform: WindowsPlatform, adapter: WindowsAdapterInfo
) -> tuple[tuple[int, Any] | None, tuple[int, Any] | None, tuple[str, ...]] | ApplyResult:
    key: RegistryKey | None = None
    try:
        key = platform.open_key(adapter)
        return key.get(ENABLE_GPU_FIRMWARE_VALUE), key.get(PREVIOUS_VALUE_NAME), override_names(key)
    except OSError as exc:
        return error(IO_ERROR, f"Cannot read the GPU driver key: {exc}", "Check permissions.")
    finally:
        if key is not None:
            key.close()


def plan_load(
    platform: WindowsPlatform,
    adapter: WindowsAdapterInfo,
    payload: bytes,
    *,
    restart: bool = True,
) -> RegistryPlan | ApplyResult:
    """Build the load write plan without changing the registry."""
    read = _read_key(platform, adapter)
    if isinstance(read, ApplyResult):
        return read
    firmware, backup, deletes = read
    valid, _saved = saved_previous(backup)
    if _saved is None and backup is not None:
        return error(
            "REGISTRY_INVALID",
            f"{PREVIOUS_VALUE_NAME} has an unexpected value.",
            "Run unload or inspect the key.",
        )
    if as_dword(firmware) is None and firmware is not None:
        return error(
            "REGISTRY_INVALID",
            "EnableGpuFirmware has an unexpected type.",
            "Inspect the driver key.",
        )
    previous = ABSENT if firmware is None else f"{as_dword(firmware):#010x}"
    warnings: list[str] = []
    if backup is not None:
        assert isinstance(backup[1], str)
        previous = backup[1]
    elif not valid:
        return error(
            "REGISTRY_INVALID",
            f"{PREVIOUS_VALUE_NAME} has an unexpected value.",
            "Run unload or inspect the key.",
        )
    elif deletes:
        warnings.append("An existing override is replaced; unload restores only EnableGpuFirmware.")
    steps: list[Step] = []
    if backup is None:
        steps.append(Step("set", PREVIOUS_VALUE_NAME, REG_SZ, previous))
    steps.extend(Step("delete", name) for name in deletes)
    steps.extend(
        [
            Step("set", OVERRIDE_VALUE_NAME, REG_BINARY, payload),
            Step("set", ENABLE_GPU_FIRMWARE_VALUE, REG_DWORD, FIRMWARE_OVERRIDE),
        ]
    )
    values: dict[str, Any] = {
        "target": f"HKLM\\{adapter.driver_key}",
        "device": adapter.name,
        "restart_device": adapter.instance_id,
        "vbios": {
            "type": "REG_BINARY",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "EnableGpuFirmware": {"type": "REG_DWORD", "value": FIRMWARE_OVERRIDE},
        "VixLoaderPreviousEnableGpuFirmware": {"type": "REG_SZ", "value": previous},
        "delete": list(deletes),
    }
    return RegistryPlan(
        "load", adapter, tuple(steps), values, len(payload), tuple(warnings), restart
    )


def plan_unload(
    platform: WindowsPlatform, adapter: WindowsAdapterInfo, *, restart: bool = True
) -> RegistryPlan | ApplyResult:
    """Build the unload plan without changing the registry."""
    read = _read_key(platform, adapter)
    if isinstance(read, ApplyResult):
        return read
    firmware, backup, deletes = read
    valid, saved = saved_previous(backup)
    if not valid:
        return error(
            "REGISTRY_INVALID",
            f"{PREVIOUS_VALUE_NAME} has an unexpected value.",
            "Inspect the key manually.",
        )
    steps: list[Step] = []
    warnings: list[str] = []
    restore: Any = "unchanged"
    if saved == ABSENT:
        steps.append(Step("delete", ENABLE_GPU_FIRMWARE_VALUE))
        restore = "delete"
    elif isinstance(saved, int):
        steps.append(Step("set", ENABLE_GPU_FIRMWARE_VALUE, REG_DWORD, saved))
        restore = saved
    elif backup is not None:
        warnings.append(
            "The previous-value marker is malformed; EnableGpuFirmware is left unchanged."
        )
    else:
        warnings.append("No previous-value marker exists; EnableGpuFirmware is left unchanged.")
    steps.extend(Step("delete", name) for name in deletes)
    steps.append(Step("delete", OVERRIDE_VALUE_NAME))
    if backup is not None:
        steps.append(Step("delete", PREVIOUS_VALUE_NAME))
    values: dict[str, Any] = {
        "target": f"HKLM\\{adapter.driver_key}",
        "device": adapter.name,
        "restart_device": adapter.instance_id,
        "delete": [step.name for step in steps if step.operation == "delete"],
        "EnableGpuFirmware": restore,
        "current_EnableGpuFirmware": as_dword(firmware),
    }
    return RegistryPlan("unload", adapter, tuple(steps), values, 0, tuple(warnings), restart)


def readback_load(key: RegistryKey, plan: RegistryPlan) -> ApplyResult | None:
    """Verify that every load write is visible in a fresh read."""
    payload = next((step.value for step in plan.steps if step.name == OVERRIDE_VALUE_NAME), None)
    if key.get(OVERRIDE_VALUE_NAME) != (REG_BINARY, payload):
        return error(
            "READBACK_MISMATCH",
            "The vbios value read back differs from what was written.",
            "Run unload and retry.",
        )
    if key.get(ENABLE_GPU_FIRMWARE_VALUE) != (REG_DWORD, FIRMWARE_OVERRIDE):
        return error(
            "READBACK_MISMATCH", "EnableGpuFirmware readback differs.", "Run unload and retry."
        )
    if key.get(PREVIOUS_VALUE_NAME) is None:
        return error(
            "READBACK_MISMATCH", "The previous-value marker is missing.", "Run unload and retry."
        )
    if any(key.get(name) is not None for name in PATCH_RECORDS):
        return error(
            "READBACK_MISMATCH",
            "romOverride records remain after the write.",
            "Run unload and retry.",
        )
    return None


def readback_unload(key: RegistryKey, plan: RegistryPlan) -> ApplyResult | None:
    """Verify that every unload write/delete is visible in a fresh read."""
    if key.get(OVERRIDE_VALUE_NAME) is not None or key.get(PREVIOUS_VALUE_NAME) is not None:
        return error(
            "READBACK_MISMATCH",
            "Override values remain after unload.",
            "Restart Windows and retry.",
        )
    remove = any(
        step.operation == "delete" and step.name == ENABLE_GPU_FIRMWARE_VALUE for step in plan.steps
    )
    restore = next(
        (
            step
            for step in plan.steps
            if step.operation == "set" and step.name == ENABLE_GPU_FIRMWARE_VALUE
        ),
        None,
    )
    if remove and key.get(ENABLE_GPU_FIRMWARE_VALUE) is not None:
        return error(
            "READBACK_MISMATCH", "EnableGpuFirmware should have been deleted.", "Run unload again."
        )
    if restore is not None and key.get(ENABLE_GPU_FIRMWARE_VALUE) != (REG_DWORD, restore.value):
        return error(
            "READBACK_MISMATCH", "EnableGpuFirmware was not restored.", "Run unload again."
        )
    if any(key.get(name) is not None for name in PATCH_RECORDS):
        return error(
            "READBACK_MISMATCH", "romOverride records remain after unload.", "Run unload again."
        )
    return None


def preview(plan: RegistryPlan) -> ApplyPreview:
    """Convert a plan into the UI-facing dry-run DTO."""
    return ApplyPreview(
        action="load" if plan.action == "load" else "unload",
        target=str(plan.values.get("target", "")),
        values=plan.values,
        bytes_written=plan.bytes_written,
        restart_required=plan.restart_required,
        warnings=plan.warnings,
    )
