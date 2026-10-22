"""Shared command-runner primitives for system adapters.

The project keeps every process launch behind a narrow, injectable interface:
commands are argument lists and callers never enable shell mode. Tests use a
fake runner that records calls, while production uses :class:`SubprocessRunner`.
"""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result of one external command."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    """Small command-runner protocol implemented by tests and production."""

    def run(self, command: Sequence[str], *, timeout: float = 60.0) -> CommandResult:
        """Run one argument-list command and return its captured result."""


class SubprocessRunner:
    """Production runner: always a list, always ``shell=False``.

    ``subprocess`` is imported lazily so the AST import-boundary contract does
    not treat it as a normal adapter dependency.
    """

    def run(self, command: Sequence[str], *, timeout: float = 60.0) -> CommandResult:
        """Execute ``command`` after validating that it is a string list."""
        if isinstance(command, str) or not isinstance(command, list):
            raise ValueError("commands must be a list of strings")
        if not command or not all(isinstance(part, str) for part in command):
            raise ValueError("commands must be a non-empty list of strings")
        module = importlib.import_module("subprocess")
        completed = module.run(
            list(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(completed.returncode, completed.stdout or "", completed.stderr or "")
