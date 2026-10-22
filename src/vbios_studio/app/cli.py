"""Command-line entry point for ``vbios-studio`` and ``python -m vbios_studio``.

``--version`` and ``--selftest`` never import GTK. The GUI path is imported
lazily so the CLI works on headless build machines.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from vbios_studio import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="vbios-studio",
        description="GTK4 NVIDIA VBIOS editor and controlled loader-override suite.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the headless self-test and exit",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="start the GTK4 interface",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="start the GTK4 interface with in-memory preview data",
    )
    parser.add_argument(
        "rom",
        nargs="?",
        help="optional ROM image to open in the GUI",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch to the CLI or GTK front end."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        from vbios_studio.ui.selftest import main as selftest_main

        return selftest_main([])
    if args.gui or args.rom:
        from vbios_studio.app.container import build_gui_controller
        from vbios_studio.ui.application import main as gui_main

        gui_args = [args.rom] if args.rom else []
        if args.demo:
            gui_args.append("--demo")
        return gui_main(
            gui_args,
            controller_factory=None if args.demo else build_gui_controller,
        )
    parser.print_help(sys.stdout)
    return 0
