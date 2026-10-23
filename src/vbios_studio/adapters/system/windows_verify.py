"""Read-only verification for the Windows registry override.

The running VBIOS is supplied by the platform (NvAPI in the upstream loader).
If the platform cannot read it, verification fails closed instead of claiming
that the stored override is active.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable

from vbios_studio.domain.errors import IO_ERROR
from vbios_studio.domain.models import ApplyResult, DeviceStatus, OverrideState

from .windows_plan import (
    OVERRIDE_VALUE_NAME,
    REG_BINARY,
    WindowsAdapterInfo,
    WindowsPlatform,
)


def verify_override(
    platform: WindowsPlatform,
    adapter: WindowsAdapterInfo,
    running_image: bytes | None,
    reader: Callable[[WindowsAdapterInfo], bytes | None] | None = None,
) -> ApplyResult:
    """Compare the stored override with a running image, byte for byte."""
    if running_image is None and reader is not None:
        try:
            running_image = reader(adapter)
        except Exception as exc:
            return ApplyResult(
                False,
                "unknown",
                f"Cannot read the running VBIOS image: {exc}",
                {
                    "code": "VERIFY_UNAVAILABLE",
                    "hint": "Check the NVIDIA driver or retry as Administrator.",
                },
            )
    key = None
    try:
        key = platform.open_key(adapter)
        stored = key.get(OVERRIDE_VALUE_NAME)
    except OSError as exc:
        return ApplyResult(
            False,
            "unknown",
            f"Cannot read the GPU driver key: {exc}",
            {"code": IO_ERROR, "hint": "Check permissions."},
        )
    finally:
        if key is not None:
            key.close()
    if stored is None:
        return ApplyResult(True, "no-override", "No override is stored.", {"code": "NO_OVERRIDE"})
    if running_image is None:
        return ApplyResult(
            False,
            "unknown",
            "No running VBIOS image was supplied for verification.",
            {"code": "VERIFY_UNAVAILABLE", "hint": "Read the active driver image and retry."},
        )
    active = bytes(stored[1]) if stored[0] == REG_BINARY else b""
    matches = active == running_image
    return ApplyResult(
        True,
        "override-active" if matches else "override-not-active",
        "Running VBIOS matches the stored override."
        if matches
        else "Running VBIOS differs from the stored override.",
        {
            "code": "VERIFY_MATCH" if matches else "VERIFY_MISMATCH",
            "override_sha256": hashlib.sha256(active).hexdigest(),
            "running_sha256": hashlib.sha256(running_image).hexdigest(),
        },
    )


def read_device_status(platform: WindowsPlatform, adapter: WindowsAdapterInfo) -> DeviceStatus:
    """Read the selected adapter's override state without writing."""
    state: OverrideState = "unknown"
    try:
        key = platform.open_key(adapter)
        try:
            state = "override-active" if key.get(OVERRIDE_VALUE_NAME) is not None else "no-override"
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
