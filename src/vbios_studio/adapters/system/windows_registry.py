"""Windows registry override adapter.

The protocol is the one used by ``nvidia-windows-vbios-vix-loader``: ``vbios``
(REG_BINARY), ``EnableGpuFirmware=0x11`` (REG_DWORD), a first-load backup in
``VixLoaderPreviousEnableGpuFirmware`` (REG_SZ), deletion of legacy
``romOverride00``-``romOverrideFF`` values and a ``pnputil`` device restart.

The adapter only writes through an injected :class:`WindowsPlatform`; tests use
an in-memory backend. Dry-run is the default and performs zero writes.
"""

from __future__ import annotations

import hashlib
import logging

from vbios_studio.domain.errors import ELEVATION_REQUIRED, IO_ERROR
from vbios_studio.domain.models import ApplyPreview, ApplyResult, DeviceStatus, OverrideState

from ._base import CommandRunner, SubprocessRunner
from .windows_plan import (
    ABSENT,
    ENABLE_GPU_FIRMWARE_VALUE,
    FIRMWARE_OVERRIDE,
    OVERRIDE_VALUE_NAME,
    PREVIOUS_VALUE_NAME,
    REG_BINARY,
    REG_DWORD,
    REG_SZ,
    REGISTRY_CLASS_KEY,
    RegistryKey,
    RegistryPlan,
    WindowsAdapterInfo,
    WindowsPlatform,
    error,
    plan_load,
    plan_unload,
    preview,
    readback_load,
    readback_unload,
)

__all__ = [
    "ABSENT",
    "ENABLE_GPU_FIRMWARE_VALUE",
    "FIRMWARE_OVERRIDE",
    "OVERRIDE_VALUE_NAME",
    "PREVIOUS_VALUE_NAME",
    "REGISTRY_CLASS_KEY",
    "REG_BINARY",
    "REG_DWORD",
    "REG_SZ",
    "WindowsAdapterInfo",
    "WindowsPlatform",
    "WindowsRegistryAdapter",
]
_LOGGER = logging.getLogger(__name__)


class WindowsRegistryAdapter:
    """Controlled Windows override implementation with dry-run and rollback."""

    def __init__(
        self,
        platform: WindowsPlatform | None = None,
        runner: CommandRunner | None = None,
        *,
        adapter_index: int = 0,
        payload: bytes | None = None,
        restart: bool = True,
    ) -> None:
        if platform is None:
            try:
                from .windows_winreg import WinregPlatform

                platform = WinregPlatform(runner or SubprocessRunner())
            except Exception:
                platform = None
        self.platform = platform
        self.runner = runner or SubprocessRunner()
        self.adapter_index = adapter_index
        self.payload = bytes(payload) if payload is not None else None
        self.restart = restart

    # ------------------------------------------------------------- port API
    def device_status(self) -> DeviceStatus:
        """Return the selected GPU and override state without writing."""
        adapter = self._select()
        if adapter is None:
            return DeviceStatus(0, "No NVIDIA GPU", "", None, "unknown", False)
        state: OverrideState = "unknown"
        if self.platform is not None:
            try:
                key = self.platform.open_key(adapter)
                try:
                    state = (
                        "override-active"
                        if key.get(OVERRIDE_VALUE_NAME) is not None
                        else "no-override"
                    )
                finally:
                    key.close()
            except OSError:
                state = "unknown"
        return DeviceStatus(
            adapter.index,
            adapter.name,
            adapter.pci_id,
            adapter.driver_version,
            state,
            adapter.supports_payload,
        )

    def verify(self, running_image: bytes | None = None) -> ApplyResult:
        """Compare the stored override with the driver's actual running image.

        ``running_image`` must be read from the driver by the caller; this
        adapter never invents a running image. The returned state follows the
        upstream protocol: ``no-override``, ``override-active`` (byte-identical)
        or ``override-not-active`` (different).
        """
        adapter = self._select()
        if adapter is None:
            return error(
                "DEVICE_NOT_FOUND",
                "No NVIDIA GPU driver key was found.",
                "Check the GPU and driver.",
            )
        if self.platform is None:
            return error(
                "PLATFORM_UNAVAILABLE",
                "The Windows registry backend is unavailable.",
                "Run on Windows.",
            )
        key: RegistryKey | None = None
        try:
            key = self.platform.open_key(adapter)
            stored = key.get(OVERRIDE_VALUE_NAME)
        except OSError as exc:
            return error(IO_ERROR, f"Cannot read the GPU driver key: {exc}", "Check permissions.")
        finally:
            if key is not None:
                key.close()
        if stored is None:
            return ApplyResult(
                True, "no-override", "No override is stored.", {"code": "NO_OVERRIDE"}
            )
        if running_image is None:
            return ApplyResult(
                False,
                "unknown",
                "No running VBIOS image was supplied for verification.",
                {"code": "VERIFY_UNAVAILABLE", "hint": "Read the active driver image and retry."},
            )
        active = bytes(stored[1]) if stored[0] == REG_BINARY else b""
        match = active == running_image
        return ApplyResult(
            True,
            "override-active" if match else "override-not-active",
            "Running VBIOS matches the stored override."
            if match
            else "Running VBIOS differs from the stored override.",
            {
                "code": "VERIFY_MATCH" if match else "VERIFY_MISMATCH",
                "override_sha256": hashlib.sha256(active).hexdigest(),
                "running_sha256": hashlib.sha256(running_image).hexdigest(),
            },
        )

    def set_payload(self, payload: bytes) -> None:
        """Set the payload used by the port-style ``dry_run``/``execute`` calls."""
        self.payload = bytes(payload)

    def dry_run(self) -> ApplyPreview:
        """Return the exact load plan without touching the registry."""
        if self.payload is None:
            return ApplyPreview(
                "load", "", {"error": "no payload configured"}, 0, False, ("Set a payload first.",)
            )
        result = self.load(self.payload, dry_run=True)
        return (
            result
            if isinstance(result, ApplyPreview)
            else ApplyPreview("load", "", {"error": result.message}, 0, False, (result.message,))
        )

    def execute(self) -> ApplyResult:
        """Execute the configured load action."""
        if self.payload is None:
            return error(
                "NO_PAYLOAD", "No payload is configured.", "Export a loader payload first."
            )
        result = self.load(self.payload, dry_run=False)
        return (
            result if isinstance(result, ApplyResult) else error("UNEXPECTED", "Unexpected result.")
        )

    def restore(self) -> ApplyResult:
        """Remove the override and restore the pre-load firmware value."""
        result = self.unload(dry_run=False)
        return (
            result if isinstance(result, ApplyResult) else error("UNEXPECTED", "Unexpected result.")
        )

    # ------------------------------------------------------------- loading
    def load(self, payload: bytes, *, dry_run: bool = True) -> ApplyPreview | ApplyResult:
        """Plan or write the override payload."""
        if not isinstance(payload, (bytes, bytearray)) or not payload:
            return error(
                "INVALID_PAYLOAD", "The payload must be non-empty bytes.", "Export a payload first."
            )
        adapter = self._select()
        if adapter is None:
            return error(
                "DEVICE_NOT_FOUND",
                "No NVIDIA GPU driver key was found.",
                "Check the GPU and driver.",
            )
        if self.platform is None:
            return error(
                "PLATFORM_UNAVAILABLE",
                "The Windows registry backend is unavailable.",
                "Run on Windows.",
            )
        planned = plan_load(self.platform, adapter, bytes(payload), restart=self.restart)
        if isinstance(planned, ApplyResult):
            return planned
        if dry_run:
            return preview(planned)
        denied = self._admin_error()
        if denied is not None:
            return denied
        return self._apply(planned)

    def _apply(self, planned: RegistryPlan) -> ApplyResult:
        assert self.platform is not None
        key: RegistryKey | None = None
        try:
            key = self.platform.open_key(planned.adapter, write=True)
            for step in planned.steps:
                if step.operation == "set":
                    key.set(step.name, step.kind, step.value)
                else:
                    key.delete(step.name)
            key.flush()
            problem = readback_load(key, planned)
        except OSError as exc:
            return error(
                IO_ERROR,
                f"Registry write failed: {exc}",
                "Run as Administrator and retry; then unload.",
            )
        finally:
            if key is not None:
                key.close()
        if problem is not None:
            return problem
        restart_error = self._restart(planned.adapter)
        if restart_error is not None:
            return restart_error
        _LOGGER.info(
            "registry load: target=HKLM\\%s payload_sha256=%s size=%s",
            planned.adapter.driver_key,
            planned.values.get("vbios", {}).get("sha256"),
            planned.bytes_written,
        )
        return ApplyResult(
            True,
            "override-active",
            "Override written, verified and the device was restarted.",
            {
                "target": f"HKLM\\{planned.adapter.driver_key}",
                "payload_sha256": planned.values.get("vbios", {}).get("sha256")
                if isinstance(planned.values.get("vbios"), dict)
                else None,
                "payload_size": planned.bytes_written,
            },
        )

    # ------------------------------------------------------------- unload
    def unload(self, *, dry_run: bool = False) -> ApplyPreview | ApplyResult:
        """Plan or perform the restore path."""
        adapter = self._select()
        if adapter is None:
            return error(
                "DEVICE_NOT_FOUND",
                "No NVIDIA GPU driver key was found.",
                "Check the GPU and driver.",
            )
        if self.platform is None:
            return error(
                "PLATFORM_UNAVAILABLE",
                "The Windows registry backend is unavailable.",
                "Run on Windows.",
            )
        planned = plan_unload(self.platform, adapter, restart=self.restart)
        if isinstance(planned, ApplyResult):
            return planned
        if dry_run:
            return preview(planned)
        denied = self._admin_error()
        if denied is not None:
            return denied
        return self._apply_unload(planned)

    def _apply_unload(self, planned: RegistryPlan) -> ApplyResult:
        assert self.platform is not None
        key: RegistryKey | None = None
        try:
            key = self.platform.open_key(planned.adapter, write=True)
            for step in planned.steps:
                if step.operation == "set":
                    key.set(step.name, step.kind, step.value)
                else:
                    key.delete(step.name)
            key.flush()
            problem = readback_unload(key, planned)
        except OSError as exc:
            return error(
                IO_ERROR, f"Registry restore failed: {exc}", "Run as Administrator and retry."
            )
        finally:
            if key is not None:
                key.close()
        if problem is not None:
            return problem
        restart_error = self._restart(planned.adapter)
        if restart_error is not None:
            return restart_error
        return ApplyResult(
            True,
            "no-override",
            "Override removed and the previous firmware value restored.",
            {"target": f"HKLM\\{planned.adapter.driver_key}"},
        )

    # ------------------------------------------------------------- helpers
    def _select(self) -> WindowsAdapterInfo | None:
        if self.platform is None:
            return None
        try:
            adapters = list(self.platform.adapters())
        except OSError:
            return None
        return adapters[self.adapter_index] if 0 <= self.adapter_index < len(adapters) else None

    def _admin_error(self) -> ApplyResult | None:
        if self.platform is None:
            return error(
                "PLATFORM_UNAVAILABLE",
                "The Windows registry backend is unavailable.",
                "Run on Windows.",
            )
        try:
            elevated = bool(self.platform.is_admin())
        except OSError:
            elevated = False
        if elevated:
            return None
        return error(
            ELEVATION_REQUIRED,
            "Administrator rights are required to change the GPU driver key.",
            "Run VBIOS Studio as Administrator, then retry.",
        )

    def _restart(self, adapter: WindowsAdapterInfo) -> ApplyResult | None:
        if not self.restart or self.platform is None:
            return None
        try:
            code, output = self.platform.restart_device(adapter.instance_id)
        except OSError as exc:
            return error(
                "RESTART_FAILED", f"Device restart failed: {exc}", "Restart Windows manually."
            )
        if code == 0:
            return None
        detail = (
            "pnputil did not report an exit code" if code is None else f"pnputil exited with {code}"
        )
        return ApplyResult(
            False,
            "restart-failed",
            f"The registry values were written but the device restart failed ({detail}). "
            "Restart Windows.",
            {
                "code": "RESTART_FAILED",
                "hint": "Restart Windows to apply the override.",
                "output": output,
            },
        )
