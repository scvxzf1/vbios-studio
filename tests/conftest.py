"""Shared synthetic-ROM fixtures; no real firmware is ever checked in."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_FIXTURE_MODULE = Path(__file__).resolve().parent / "core" / "rom_fixtures.py"


def _load_fixture_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vbios_studio_test_rom_fixtures", _FIXTURE_MODULE)
    if spec is None or spec.loader is None:  # pragma: no cover - import machinery invariant
        raise RuntimeError(f"cannot load synthetic ROM fixtures from {_FIXTURE_MODULE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


synthetic_rom: Callable[..., bytes] = _load_fixture_module().synthetic_rom


@pytest.fixture(scope="session")
def synthetic_rom_factory() -> Callable[..., bytes]:
    """Return the deterministic synthetic ROM builder used by core tests."""
    return synthetic_rom


@pytest.fixture(scope="session")
def synthetic_ada_rom() -> bytes:
    """A two-copy synthetic Ada ROM with the standard table shapes."""
    return synthetic_rom(family="ada", copies=2)


@pytest.fixture(scope="session")
def synthetic_ampere_rom() -> bytes:
    """A two-copy synthetic Ampere ROM for family-specific parity checks."""
    return synthetic_rom(family="ampere", copies=2)
