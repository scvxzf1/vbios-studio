"""Installed GUI console-script entry point.

The package script must not call ``ui.application.main`` directly: that entry
point has no production controller factory and therefore returns exit code 2
when it is started without ``--demo``. This app-layer wrapper supplies the real
composition root and delegates argument parsing/GTK startup to the UI.
"""

from __future__ import annotations

from collections.abc import Sequence

from vbios_studio.app.container import build_gui_controller
from vbios_studio.ui.application import main as gui_main


def main(argv: Sequence[str] | None = None) -> int:
    """Run the GTK application with the production controller factory."""
    return gui_main(argv, controller_factory=build_gui_controller)
