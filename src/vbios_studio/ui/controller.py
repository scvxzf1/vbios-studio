"""GTK-free presentation controller: staged edits, undo/redo, filters and ports calls."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from vbios_studio.domain.errors import DomainError
from vbios_studio.domain.models import (
    DocumentSnapshot,
    EditPreview,
    FieldSnapshot,
    RomDiff,
    SaveResult,
)
from vbios_studio.ports.apply import ApplyPort
from vbios_studio.ports.diff import DiffPort
from vbios_studio.ports.editor import EditorPort
from vbios_studio.ports.profile import ProfilePort
from vbios_studio.ui.apply_actions import ApplyActions
from vbios_studio.ui.controller_errors import ConfirmationRequired as ConfirmationRequired
from vbios_studio.ui.controller_errors import T3LockedError as T3LockedError
from vbios_studio.ui.filtering import FilterState, filter_fields, section_counts
from vbios_studio.ui.profile_controller import ProfileControllerMixin

Listener = Callable[[str], None]


@dataclass
class LogEntry:
    level: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class UiController(ApplyActions, ProfileControllerMixin):
    """Owns every piece of mutable UI state; talks to ports only."""

    UNDO_LIMIT = 100

    def __init__(
        self,
        editor: EditorPort,
        diff: DiffPort | None = None,
        profile: ProfilePort | None = None,
        apply: ApplyPort | None = None,
    ) -> None:
        self.editor = editor
        self.diff_port = diff
        self.profile_port = profile
        self.apply_port = apply
        self.snapshot: DocumentSnapshot | None = None
        self.changes: dict[str, str] = {}
        self.preview: EditPreview | None = None
        self.filters = FilterState()
        self.current_section = "info"
        self.view_mode = "table"
        self.experimental_unlocked = False
        self.last_saved: SaveResult | None = None
        self.last_diff: RomDiff | None = None
        self._undo: list[dict[str, str]] = []
        self._redo: list[dict[str, str]] = []
        self._listeners: list[Listener] = []
        self.log_entries: list[LogEntry] = []

    # -- observers ---------------------------------------------------------
    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def _notify(self, reason: str) -> None:
        for listener in tuple(self._listeners):
            listener(reason)

    # -- logging -----------------------------------------------------------
    def log(self, message: str, level: str = "INFO") -> None:
        self.log_entries.append(LogEntry(level=level, message=message))
        del self.log_entries[:-500]
        self._notify("log")

    # -- document ----------------------------------------------------------
    def open_path(self, path: Path) -> DocumentSnapshot:
        snapshot = self.editor.open(Path(path))
        self.snapshot = snapshot
        self.changes = {}
        self.preview = None
        self.last_saved = None
        self.last_diff = None
        self._undo.clear()
        self._redo.clear()
        self.current_section = "info"
        self.filters = FilterState()
        self.log(f"Opened {snapshot.display_name} ({snapshot.architecture})")
        self._notify("document")
        return snapshot

    def close(self) -> None:
        self.snapshot = None
        self.changes = {}
        self.preview = None
        self.last_saved = None
        self.last_diff = None
        self._undo.clear()
        self._redo.clear()
        self.current_section = "info"
        self._notify("document")

    @property
    def has_document(self) -> bool:
        return self.snapshot is not None

    @property
    def all_checksums_ok(self) -> bool:
        if self.snapshot is None:
            return False
        return all(image.checksum_ok for image in self.snapshot.images)

    # -- fields ------------------------------------------------------------
    @property
    def visible_fields(self) -> list[FieldSnapshot]:
        if self.snapshot is None:
            return []
        return [f for f in self.snapshot.fields if self.experimental_unlocked or f.risk != "T3"]

    @property
    def filtered_fields(self) -> list[FieldSnapshot]:
        return filter_fields(self.visible_fields, self.changes, self.filters, self.current_section)

    def fields_for_section(self, section: str) -> list[FieldSnapshot]:
        return [f for f in self.visible_fields if f.section == section]

    def section_counts(self) -> dict[str, int]:
        if self.snapshot is None:
            return {}
        return section_counts(self.snapshot.fields)

    def find_field(self, key: str) -> FieldSnapshot | None:
        if self.snapshot is None:
            return None
        return next((f for f in self.snapshot.fields if f.key == key), None)

    def value_of(self, field: FieldSnapshot) -> str | None:
        return self.changes.get(field.key, field.current)

    def is_modified(self, key: str) -> bool:
        return key in self.changes

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def dirty(self) -> bool:
        return bool(self.changes)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    # -- editing -----------------------------------------------------------
    def set_filter(self, **kwargs: Any) -> None:
        self.filters = replace(self.filters, **kwargs)
        self._notify("filters")

    def toggle_filter(self, name: str, value: bool) -> None:
        self.filters = self.filters.toggled(name, value)
        self._notify("filters")

    def set_section(self, section: str) -> None:
        self.current_section = section
        self._notify("section")

    def set_view_mode(self, mode: str) -> None:
        if mode not in ("table", "form"):
            raise ValueError(mode)
        self.view_mode = mode
        self._notify("view")

    def set_experimental_unlocked(self, unlocked: bool) -> None:
        self.experimental_unlocked = bool(unlocked)
        self.log("Experimental fields unlocked" if unlocked else "Experimental fields locked")
        self._notify("experimental")

    def set_value(self, key: str, new_value: str, *, t3_confirmed: bool = False) -> EditPreview:
        """Stage one edit through the domain port. Errors leave the state untouched."""
        if self.snapshot is None:
            raise DomainError("NO_DOCUMENT", "Open a ROM first.", "Use File → Open.")
        field = self.find_field(key)
        if field is None:
            raise DomainError("UNKNOWN_FIELD", f"Unknown field: {key}", "Reload the document.")
        if field.risk == "T3" and not self.experimental_unlocked:
            raise T3LockedError(key)
        if not field.editable:
            raise DomainError(
                "FIELD_READ_ONLY", f"{field.label} is read-only.", "Choose an editable field."
            )
        current = self.value_of(field)
        if current is not None and str(current) == str(new_value):
            return self.preview or EditPreview((), (), "T0", False)
        if field.risk == "T3" and not t3_confirmed:
            raise ConfirmationRequired(field, current, str(new_value))

        candidate = dict(self.changes)
        if field.current is not None and str(new_value) == str(field.current):
            candidate.pop(key, None)
        else:
            candidate[key] = str(new_value)
        preview = self.editor.stage(candidate)
        self.preview = preview
        if preview.errors:
            self.log(f"Rejected {field.key}: {preview.errors[0].message}", "ERROR")
            self._notify("preview")
            return preview
        previous = dict(self.changes)
        if candidate != previous:
            self._push_undo(previous)
            self._redo.clear()
        self.changes = candidate
        self.log(f"Staged {field.key}: {current!r} → {new_value!r}")
        self._notify("changes")
        return preview

    def _push_undo(self, previous: Mapping[str, str]) -> None:
        self._undo.append(dict(previous))
        if len(self._undo) > self.UNDO_LIMIT:
            del self._undo[0]
        self._notify("undo")

    def reset_changes(self) -> None:
        if not self.changes:
            return
        previous = dict(self.changes)
        self.editor.reset()
        preview = self.editor.stage({})
        self.changes = {}
        self.preview = preview
        self._push_undo(previous)
        self._redo.clear()
        self.log("Discarded all staged changes")
        self._notify("changes")

    def undo(self) -> bool:
        if not self._undo:
            return False
        current = dict(self.changes)
        previous = self._undo.pop()
        if not self._apply_change_set(previous):
            self._undo.append(previous)
            return False
        self._redo.append(current)
        self._notify("changes")
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        current = dict(self.changes)
        target = self._redo.pop()
        if not self._apply_change_set(target):
            self._redo.append(target)
            return False
        self._undo.append(current)
        self._notify("changes")
        return True

    def _apply_change_set(self, target: Mapping[str, str]) -> bool:
        """Replay a change set through the domain, as the ports contract requires."""
        try:
            self.editor.reset()
            preview = self.editor.stage(dict(target))
        except DomainError as exc:
            self.log(f"Replay failed: {exc.message}", "ERROR")
            return False
        self.preview = preview
        if preview.errors:
            self.log(f"Replay rejected: {preview.errors[0].message}", "ERROR")
            return False
        self.changes = dict(target)
        return True

    # -- diff --------------------------------------------------------------
    def compare(self, path: Path) -> RomDiff:
        if self.diff_port is None:
            raise DomainError(
                "DIFF_UNAVAILABLE", "ROM comparison is not available.", "Check the installation."
            )
        self.last_diff = self.diff_port.diff_against(Path(path))
        self.log(f"Compared with {Path(path).name}")
        self._notify("diff")
        return self.last_diff
