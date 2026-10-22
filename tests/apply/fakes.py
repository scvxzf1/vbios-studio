"""In-memory fakes for the Windows registry and subprocess tests."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from vbios_studio.adapters.system._base import CommandResult
from vbios_studio.adapters.system.windows_plan import WindowsAdapterInfo


@dataclass
class FakeKey:
    """A tiny registry key that records every mutation."""

    values: dict[str, tuple[int, Any]] = field(default_factory=dict)
    drop_writes: bool = False

    def __post_init__(self) -> None:
        self.mutations: list[tuple[str, str]] = []
        self.flushes = 0
        self.closed = 0

    def get(self, name: str) -> tuple[int, Any] | None:
        """Read a value."""
        return self.values.get(name)

    def set(self, name: str, kind: int, value: Any) -> None:
        """Record a write and optionally apply it."""
        self.mutations.append(("set", name))
        if not self.drop_writes:
            self.values[name] = (kind, value)

    def delete(self, name: str) -> bool:
        """Record a delete and optionally apply it."""
        self.mutations.append(("delete", name))
        if self.drop_writes:
            return name in self.values
        return self.values.pop(name, None) is not None

    def flush(self) -> None:
        """Record a flush."""
        self.flushes += 1

    def close(self) -> None:
        """Record a close."""
        self.closed += 1


class FakePlatform:
    """Fake Windows platform backed by a single in-memory driver key."""

    def __init__(
        self,
        values: dict[str, tuple[int, Any]] | None = None,
        *,
        admin: bool = True,
        restart_code: int | None = 0,
        restart_output: str = "",
        name: str = "NVIDIA GeForce RTX 4090",
        pci_id: str = "10de:2684",
    ) -> None:
        self.key = FakeKey(dict(values or {}))
        self.admin = admin
        self.restart_code = restart_code
        self.restart_output = restart_output
        self.restarted: list[str] = []
        self.writable_opens = 0
        self._adapter = WindowsAdapterInfo(
            index=0,
            name=name,
            pci_id=pci_id,
            driver_version="32.0.16.1656",
            instance_id=r"PCI\VEN_10DE&DEV_2684&SUBSYS_00000000&REV_A1\4&0",
            driver_key=r"{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
        )

    def adapters(self) -> Sequence[WindowsAdapterInfo]:
        """Return the fake NVIDIA adapter."""
        return [self._adapter]

    def open_key(self, adapter: WindowsAdapterInfo, write: bool = False) -> FakeKey:
        """Return the fake key and count writable opens."""
        self.writable_opens += int(write)
        return self.key

    def is_admin(self) -> bool:
        """Return the configured elevation state."""
        return self.admin

    def restart_device(self, instance_id: str) -> tuple[int | None, str]:
        """Record a device restart."""
        self.restarted.append(instance_id)
        return self.restart_code, self.restart_output


class FakeRunner:
    """Command runner that records argument lists and returns a fixed result."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.calls: list[list[str]] = []

    def run(self, command: Sequence[str], *, timeout: float = 60.0) -> CommandResult:
        """Record one list command."""
        assert isinstance(command, list), f"command must be a list: {command!r}"
        assert all(isinstance(part, str) for part in command), command
        self.calls.append(list(command))
        return CommandResult(self.returncode, self.stdout, self.stderr)
