"""GTK4 application entry point and window lifecycle."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence

from vbios_studio.i18n import set_language
from vbios_studio.ui.controller import UiController


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vbios-studio-gui", add_help=True)
    parser.add_argument("rom", nargs="?", help="ROM image to open at startup")
    parser.add_argument("--lang", choices=("en", "zh_CN"), help="UI language")
    parser.add_argument("--theme", choices=("system", "light", "dark"), default="system")
    parser.add_argument("--demo", action="store_true", help="start with in-memory demo data")
    parser.add_argument("--selftest", action="store_true", help="run the offscreen UI selftest")
    parser.add_argument("--screenshots", metavar="DIR", help="write selftest screenshots to DIR")
    return parser.parse_args(list(argv))


class VbiosApplication:
    """Thin wrapper that keeps the GTK import lazy for CLI users."""

    def __init__(self, controller: UiController, *, theme: str, initial_rom: str | None) -> None:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw

        from vbios_studio.ui.main_window import MainWindow
        from vbios_studio.ui.theme import apply_theme, install_css

        self._MainWindow = MainWindow
        self.theme = theme
        self.initial_rom = initial_rom
        self.controller = controller
        self.app = Adw.Application(application_id="io.github.vbios_studio", flags=0)
        self.app.connect("activate", self._on_activate)
        install_css()
        apply_theme(theme)
        self.window: MainWindow | None = None

    def _on_activate(self, _app: object) -> None:
        if self.window is not None:
            self.window.present()
            return
        self.window = self._MainWindow(
            self.app,
            self.controller,
            on_language=self.change_language,
            on_theme=self.change_theme,
        )
        self.window.present()
        if self.initial_rom:
            from pathlib import Path

            self.window.open_path(Path(self.initial_rom))

    def change_language(self, language: str) -> None:
        set_language(language)
        self.rebuild_window()

    def change_theme(self, theme: str) -> None:
        from vbios_studio.ui.theme import apply_theme

        self.theme = theme
        apply_theme(theme)

    def rebuild_window(self) -> None:
        """Recreate the window so every generated label uses the new catalogue."""
        if self.window is None:
            return
        old = self.window
        self.window = self._MainWindow(
            self.app,
            self.controller,
            on_language=self.change_language,
            on_theme=self.change_theme,
        )
        self.window.present()
        old.destroy()

    def run(self, argv: Sequence[str] | None = None) -> int:
        return int(self.app.run(list(argv or [])))


def run_gui(
    controller: UiController,
    *,
    argv: Sequence[str] | None = None,
    theme: str = "system",
    initial_rom: str | None = None,
) -> int:
    """Run the GTK application with an injected, fully wired controller."""
    application = VbiosApplication(controller, theme=theme, initial_rom=initial_rom)
    return application.run(argv)


def main(
    argv: Sequence[str] | None = None,
    controller_factory: Callable[[], UiController] | None = None,
) -> int:
    """Entry point used by ``python -m vbios_studio.ui`` and the GUI script."""
    args = _parse(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        from vbios_studio.ui.selftest import main as selftest_main

        extra = ["--screenshots", args.screenshots] if args.screenshots else []
        return selftest_main(extra)
    if args.lang:
        set_language(args.lang)
    if controller_factory is None:
        if not args.demo:
            print(
                "The GUI needs the application composition root; run `vbios-studio --gui` "
                "or pass --demo for the in-memory preview.",
                file=sys.stderr,
            )
            return 2
        from vbios_studio.ui.demo import demo_controller

        controller = demo_controller()
    else:
        controller = controller_factory()
    return run_gui(controller, argv=[], theme=args.theme, initial_rom=args.rom)
