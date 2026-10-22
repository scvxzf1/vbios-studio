"""Regression: installed GUI entry point must inject the production controller."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

from vbios_studio.app import gui as gui_entry


def _script_target() -> str:
    root = Path(__file__).resolve().parents[2]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["scripts"]["vbios-studio-gui"])


def test_gui_entrypoint_target_imports_and_is_app_layer() -> None:
    """The script points at an importable app-layer function, never ui.application."""
    target = _script_target()
    assert target != "vbios_studio.ui.application:main"
    module_name, separator, attribute = target.partition(":")
    assert separator == ":"
    module = importlib.import_module(module_name)
    assert callable(getattr(module, attribute))
    assert module_name == "vbios_studio.app.gui"


def test_gui_main_passes_the_real_controller_factory(monkeypatch) -> None:
    """Calling the app entry point always supplies build_gui_controller."""
    captured: dict[str, object] = {}

    def fake_gui_main(argv, *, controller_factory):
        captured["argv"] = argv
        captured["controller_factory"] = controller_factory
        return 0

    monkeypatch.setattr(gui_entry, "gui_main", fake_gui_main)
    assert gui_entry.main(["--selftest"]) == 0
    assert captured["argv"] == ["--selftest"]
    assert captured["controller_factory"] is gui_entry.build_gui_controller
    assert captured["controller_factory"] is not None
