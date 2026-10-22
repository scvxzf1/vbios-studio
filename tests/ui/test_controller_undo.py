"""Undo/redo contract: 25 steps, empty stacks and redo invalidation."""

from __future__ import annotations

import pytest

from vbios_studio.ui.controller import T3LockedError, UiController


def test_empty_stacks_are_no_ops(controller: UiController) -> None:
    assert controller.can_undo is False
    assert controller.can_redo is False
    assert controller.undo() is False
    assert controller.redo() is False


def test_twenty_five_edits_undo_and_redo_exactly(controller: UiController) -> None:
    values = [str(value) for value in range(101, 126)]
    for value in values:
        preview = controller.set_value("power_min_w", value)
        assert not preview.errors
    assert controller.can_undo
    assert controller.change_count == 1
    assert controller.UNDO_LIMIT >= 20

    undo_states = []
    for _ in range(len(values)):
        assert controller.undo() is True
        undo_states.append(controller.value_of(controller.find_field("power_min_w")))  # type: ignore[arg-type]
    assert undo_states == [str(value) for value in range(124, 99, -1)]
    assert controller.value_of(controller.find_field("power_min_w")) == "100"  # type: ignore[arg-type]

    redo_states = []
    for _ in range(len(values)):
        assert controller.redo() is True
        redo_states.append(controller.value_of(controller.find_field("power_min_w")))  # type: ignore[arg-type]
    assert redo_states == values


def test_new_edit_after_undo_clears_redo(controller: UiController) -> None:
    for value in ("101", "102", "103"):
        controller.set_value("power_min_w", value)
    assert controller.undo() is True
    assert controller.can_redo is True
    controller.set_value("power_min_w", "150")
    assert controller.can_redo is False
    assert controller.value_of(controller.find_field("power_min_w")) == "150"  # type: ignore[arg-type]


def test_undo_capacity_is_at_least_twenty(controller: UiController) -> None:
    assert controller.UNDO_LIMIT >= 20
    for value in range(101, 126):
        controller.set_value("power_min_w", str(value))
    for _ in range(25):
        assert controller.undo() is True
    assert controller.value_of(controller.find_field("power_min_w")) == "100"  # type: ignore[arg-type]
    assert controller.undo() is False


def test_undo_history_survives_replay_validation(controller: UiController) -> None:
    controller.set_value("power_min_w", "120")
    assert controller.undo() is True
    assert controller.changes == {}
    assert controller.redo() is True
    assert controller.changes == {"power_min_w": "120"}


def test_t3_locked_never_enters_history(controller: UiController) -> None:
    with pytest.raises(T3LockedError):
        controller.set_value("power_max_w", "300")
    assert controller.changes == {}
    assert controller.can_undo is False
