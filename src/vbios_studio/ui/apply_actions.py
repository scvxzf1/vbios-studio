"""Apply-session actions shared by the GTK-free controller.

Keeping these operations out of ``controller.py`` preserves the 400-line
contract and makes the payload/ticket/verify boundary independently testable.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal, cast

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import ApplyPreview, ApplyResult, DeviceStatus, SaveResult
from vbios_studio.ports.apply import ApplyPort, Operation
from vbios_studio.ports.editor import EditorPort


class ApplyActions:
    """Mixin with the controller's save/apply port calls and payload hand-off."""

    apply_port: ApplyPort | None
    editor: EditorPort
    snapshot: object | None
    last_saved: SaveResult | None

    def log(self, message: str, level: str = "INFO") -> None:
        """Append a log entry; implemented by the concrete controller."""

    def _notify(self, reason: str) -> None:
        """Notify controller listeners; implemented by the concrete controller."""

    def _require_apply(self) -> ApplyPort:
        if self.apply_port is None:
            raise DomainError(
                "APPLY_UNAVAILABLE", "Applying is not available.", "Check the installation."
            )
        return self.apply_port

    def save_as(self, path: Path) -> SaveResult:
        """Save a new ROM and attach its loader payload to this apply session."""
        if self.snapshot is None:
            raise DomainError("NO_DOCUMENT", "Open a ROM first.", "Use File → Open.")
        result = self.editor.save_as(Path(path))
        self.last_saved = result
        self._configure_saved_payload(result)
        self.log(f"Saved new VBIOS to {result.path} (sha256 {result.sha256[:12]}…)")
        self._notify("saved")
        return result

    def _configure_saved_payload(self, result: SaveResult) -> None:
        """Attach the saved loader payload to the apply session, when supported."""
        if self.apply_port is None or not result.payload_paths:
            return
        configure = getattr(self.apply_port, "configure_payload", None)
        if configure is None:
            return
        path = result.payload_paths[0]
        try:
            payload = path.read_bytes()
            try:
                configure(payload, source=path)
            except TypeError:
                configure(payload)
        except OSError as exc:
            self.log(f"Could not attach apply payload: {exc}", "ERROR")

    def device_status(self) -> DeviceStatus:
        return self._require_apply().device_status()

    def apply_dry_run(self) -> ApplyPreview:
        return self._require_apply().dry_run()

    def describe_apply_operations(
        self, action: Literal["load", "restore"]
    ) -> tuple[Operation, ...]:
        """Return the port's exact operation list for a confirmation dialog."""
        return self._require_apply().describe_operations(action)

    def apply_verify(self, running_image: bytes | None = None) -> ApplyResult:
        """Run the port's read-only byte comparison against the running image."""
        port = self._require_apply()
        verify = getattr(port, "verify", None)
        if verify is None:
            return ApplyResult(
                False,
                "unknown",
                "This apply backend does not implement verification.",
                {"code": "VERIFY_UNAVAILABLE"},
            )
        verify_call = cast(Callable[[bytes | None], ApplyResult], verify)
        result = verify_call(running_image)
        self.log(f"Verify: {result.state}", "INFO" if result.ok else "ERROR")
        self._notify("apply")
        return result

    def apply_execute(self) -> ApplyResult:
        result = self._require_apply().execute()
        self.log(f"Apply: {result.state}", "INFO" if result.ok else "ERROR")
        self._notify("apply")
        return result

    def apply_restore(self) -> ApplyResult:
        result = self._require_apply().restore()
        self.log(f"Restore: {result.state}", "INFO" if result.ok else "ERROR")
        self._notify("apply")
        return result
