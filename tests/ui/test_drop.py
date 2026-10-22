"""Drag-and-drop validation rules: one local file, never a folder or a list."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbios_studio.domain.errors import DomainError
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.demo import DemoEditor
from vbios_studio.ui.drop_rules import DropError, validate_drop
from vbios_studio.ui.main_window import MainWindow


def test_single_file_is_accepted() -> None:
    path = Path("/tmp/rtx5090.rom")
    assert validate_drop([path], is_directory=[False]) == path


def test_empty_payload_is_rejected() -> None:
    with pytest.raises(DropError) as raised:
        validate_drop([], is_directory=[])
    assert raised.value.code == "DROP_EMPTY"


def test_multiple_files_are_rejected() -> None:
    with pytest.raises(DropError) as raised:
        validate_drop([Path("/tmp/a.rom"), Path("/tmp/b.rom")], is_directory=[False, False])
    assert raised.value.code == "DROP_MULTIPLE_FILES"


def test_folder_is_rejected() -> None:
    with pytest.raises(DropError) as raised:
        validate_drop([Path("/tmp")], is_directory=[True])
    assert raised.value.code == "DROP_NOT_A_FILE"


def test_valid_rom_path_triggers_load(controller) -> None:
    path = Path("/tmp/rtx5090.rom")
    accepted = validate_drop([path], is_directory=[False])
    controller.open_path(accepted)
    assert controller.snapshot is not None
    assert controller.snapshot.display_name == "rtx5090.rom"


def test_non_rom_shows_error_without_crash(gtk_initialised, controller) -> None:
    class RejectingEditor(DemoEditor):
        def open(self, path: Path):
            raise DomainError("ROM_INVALID", "Not a VBIOS ROM.", "Choose a .rom file.")

    controller = UiController(RejectingEditor(), None, None, None)
    window = MainWindow(None, controller)
    window.open_path(Path("/tmp/not-a-rom.txt"))
    assert controller.snapshot is None
    window.destroy()
