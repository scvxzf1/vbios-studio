"""Best-effort production Windows registry backend.

The real backend is imported only when :class:`WindowsRegistryAdapter` is
constructed without an injected platform. It uses ``winreg`` through
``importlib`` so the adapter layer stays importable on Linux, and it never
touches a GPU beyond the driver's registry key.
"""

from __future__ import annotations

import importlib
import os
import re
from collections.abc import Sequence
from typing import Any

from ._base import CommandRunner, SubprocessRunner
from .windows_plan import (
    ENABLE_GPU_FIRMWARE_VALUE,
    OVERRIDE_VALUE_NAME,
    PREVIOUS_VALUE_NAME,
    REGISTRY_CLASS_KEY,
    WindowsAdapterInfo,
)


class WinregKey:
    """Thin wrapper around a ``winreg`` key handle."""

    def __init__(self, key: Any, module: Any) -> None:
        self._key = key
        self._winreg = module

    def get(self, name: str) -> tuple[int, Any] | None:
        """Return a value and its registry type, or ``None``."""
        try:
            value, kind = self._winreg.QueryValueEx(self._key, name)
        except FileNotFoundError:
            return None
        return int(kind), value

    def set(self, name: str, kind: int, value: Any) -> None:
        """Write one value."""
        self._winreg.SetValueEx(self._key, name, 0, kind, value)

    def delete(self, name: str) -> bool:
        """Delete one value, returning whether it existed."""
        try:
            self._winreg.DeleteValue(self._key, name)
        except FileNotFoundError:
            return False
        return True

    def flush(self) -> None:
        """Flush the key."""
        self._winreg.FlushKey(self._key)

    def close(self) -> None:
        """Close the key."""
        self._winreg.CloseKey(self._key)


class WinregPlatform:
    """Production platform using the Windows registry and ``pnputil``."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._winreg = importlib.import_module("winreg")
        self.runner = runner or SubprocessRunner()

    def adapters(self) -> Sequence[WindowsAdapterInfo]:
        """Enumerate display-class subkeys and keep NVIDIA adapters."""
        result: list[WindowsAdapterInfo] = []
        class_root = self._winreg.OpenKey(
            self._winreg.HKEY_LOCAL_MACHINE, REGISTRY_CLASS_KEY, 0, self._winreg.KEY_READ
        )
        try:
            index = 0
            while True:
                try:
                    subkey = self._winreg.EnumKey(class_root, index)
                except OSError:
                    break
                index += 1
                if not re.fullmatch(r"\d{4}", subkey):
                    continue
                try:
                    key = self._winreg.OpenKey(class_root, subkey, 0, self._winreg.KEY_READ)
                except OSError:
                    continue
                try:
                    info = self._adapter_from_key(key, subkey, len(result))
                finally:
                    self._winreg.CloseKey(key)
                if info is not None:
                    result.append(info)
        finally:
            self._winreg.CloseKey(class_root)
        return result

    def _adapter_from_key(self, key: Any, subkey: str, index: int) -> WindowsAdapterInfo | None:
        def value(name: str) -> Any:
            try:
                return self._winreg.QueryValueEx(key, name)[0]
            except FileNotFoundError:
                return None

        name = value("DriverDesc")
        provider = value("ProviderName")
        matching = value("MatchingDeviceId") or ""
        if not isinstance(name, str) or not isinstance(matching, str):
            return None
        if "NVIDIA" not in str(name) and "NVIDIA" not in str(provider or ""):
            return None
        match = re.search(r"VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})", matching, re.I)
        if match is None:
            return None
        vendor, device = match.groups()
        instance = value("DeviceInstanceID") or matching or f"PCI\\VEN_{vendor}&DEV_{device}"
        return WindowsAdapterInfo(
            index=index,
            name=name,
            pci_id=f"{vendor.lower()}:{device.lower()}",
            driver_version=str(value("DriverVersion") or "") or None,
            instance_id=str(instance),
            driver_key=f"{REGISTRY_CLASS_KEY}\\{subkey}",
        )

    def open_key(self, adapter: WindowsAdapterInfo, write: bool = False) -> WinregKey:
        """Open one driver key."""
        access = self._winreg.KEY_READ | (self._winreg.KEY_WRITE if write else 0)
        key = self._winreg.OpenKey(self._winreg.HKEY_LOCAL_MACHINE, adapter.driver_key, 0, access)
        return WinregKey(key, self._winreg)

    def is_admin(self) -> bool:
        """Return whether the process is elevated."""
        if os.name != "nt":
            return False
        try:
            ctypes = importlib.import_module("ctypes")
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    def restart_device(self, instance_id: str) -> tuple[int | None, str]:
        """Restart one device through ``pnputil``."""
        result = self.runner.run(["pnputil", "/restart-device", instance_id])
        return result.returncode, (result.stdout + result.stderr).strip()

    def vbios_image(self, adapter: WindowsAdapterInfo) -> bytes | None:
        """Return ``None`` until an NvAPI readback provider is injected.

        The upstream Windows loader reads the active image through NvAPI; this
        build keeps that optional boundary explicit so Verify fails closed rather
        than comparing the stored override with itself.
        """
        del adapter
        return None


# Imported for re-export convenience; keeps the adapter module's public names stable.
__all__ = [
    "ENABLE_GPU_FIRMWARE_VALUE",
    "OVERRIDE_VALUE_NAME",
    "PREVIOUS_VALUE_NAME",
    "WinregKey",
    "WinregPlatform",
]
