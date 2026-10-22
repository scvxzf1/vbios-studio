"""Shared GTK fixtures for the UI tests (starts Xvfb when CI has no display)."""

from __future__ import annotations

import atexit
import os
import subprocess
import time
from pathlib import Path

import pytest

_display_process = None
if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    for _number in range(90, 110):
        _display = f":{_number}"
        if not Path(f"/tmp/.X11-unix/X{_number}").exists():
            _display_process = subprocess.Popen(
                ["Xvfb", _display, "-screen", "0", "1400x900x24", "-nolisten", "tcp"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.environ["DISPLAY"] = _display
            time.sleep(0.8)
            break
    atexit.register(lambda: _display_process.terminate() if _display_process else None)

gi = pytest.importorskip("gi")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from vbios_studio.i18n import set_language  # noqa: E402
from vbios_studio.ui.demo import demo_controller  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def gtk_initialised() -> None:
    """Initialise GTK/Adw once per test session."""
    Adw.init()
    assert Gtk.is_initialized()


@pytest.fixture(autouse=True)
def english_ui():
    """Every test starts in English; language-switch tests opt in themselves."""
    set_language("en")
    yield
    set_language("en")


@pytest.fixture
def controller():
    """A controller backed by the in-memory demo ports with one ROM open."""
    instance = demo_controller()
    instance.open_path(Path("/tmp/vbios-studio-test.rom"))
    return instance
