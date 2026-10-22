# mypy: disable-error-code="no-untyped-def,no-untyped-call,type-arg,unused-ignore"
"""Offscreen GTK selftest: builds every view, checks a11y and writes screenshots."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import traceback
import uuid
from collections.abc import Sequence
from pathlib import Path

from vbios_studio import __version__


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG file")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def _capture(window, path: Path) -> None:
    import gi

    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk, Gtk

    paintable = Gtk.WidgetPaintable.new(window)
    width, height = window.get_width(), window.get_height()
    snapshot = Gtk.Snapshot.new()
    paintable.snapshot(snapshot, width, height)
    native = window.get_native()
    if native is None or width < 800 or height < 600:
        raise RuntimeError(f"window is not mapped yet ({width}x{height})")
    node = snapshot.to_node()
    if node is None:
        raise RuntimeError("GTK produced an empty snapshot")
    renderer = native.get_renderer()
    texture = renderer.render_texture(node, None)
    if texture is None:
        raise RuntimeError("GTK renderer returned no texture")
    pixbuf = Gdk.pixbuf_get_from_texture(texture)
    path.parent.mkdir(parents=True, exist_ok=True)
    pixbuf.savev(str(path), "png", [], [])


def _assert_a11y(window) -> None:
    from vbios_studio.ui.a11y import accessible_label, focusable_widgets

    missing = [
        type(widget).__name__
        for widget in focusable_widgets(window)
        if not accessible_label(widget)
    ]
    if missing:
        raise AssertionError(f"interactive widgets without accessible label: {missing}")


def _check_focus_order(window) -> None:
    from vbios_studio.ui.a11y import tab_chain, widget_order

    chain = tab_chain(window)
    if len(chain) < 6:
        raise AssertionError(f"focus chain too short: {len(chain)}")
    open_index = next(
        (index for index, widget in enumerate(chain) if widget is window.header.open_button), None
    )
    nav_index = next(
        (index for index, widget in enumerate(chain) if widget is window.sidebar.rows["info"]), None
    )
    if open_index is None or nav_index is None or open_index > nav_index:
        raise AssertionError("Tab order must start at the toolbar and then reach navigation")
    order = widget_order(window)
    if not (
        order.index(window.sidebar)
        < order.index(window.field_table)
        < order.index(window.log_panel)
    ):
        raise AssertionError("layout order must be navigation -> fields -> log")


def _headless_selftest() -> int:
    """Fallback used by CI when PyGObject or a display is unavailable."""
    from vbios_studio.domain.models import EditPreview
    from vbios_studio.domain.risk import RISK_LEVELS, max_risk

    assert len(RISK_LEVELS) == 4, "risk model must define T0-T3"
    assert max_risk(["T1", "T3", "T2"]) == "T3"
    assert EditPreview().batch_risk == "T0"
    print(f"vbios-studio {__version__} selftest: ok (headless, GTK unavailable)")
    return 0


def run_selftest(screenshots: Path | None = None) -> int:
    """Run the offscreen selftest with a watchdog and a unique app identity.

    Concurrency matters here: two test processes must not fight over the same
    GApplication id (which silently exits the second instance) or over the same
    PNG files.  Explicit ``screenshots`` directories are written in place;
    the default docs-assets directory receives atomically replaced files.
    """
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, Gdk, GLib
    except (ImportError, RuntimeError, ValueError):
        return _headless_selftest()
    if Gdk.Display.get_default() is None:
        return _headless_selftest()

    from vbios_studio.i18n import set_language
    from vbios_studio.ui.demo import demo_controller
    from vbios_studio.ui.main_window import MainWindow
    from vbios_studio.ui.theme import RISK_COLORS, install_css

    default_target = screenshots is None
    target = screenshots or _repo_root() / "docs-assets" / "screenshots"
    if default_target:
        target.parent.mkdir(parents=True, exist_ok=True)
        workdir = Path(tempfile.mkdtemp(prefix=".vbios-selftest-", dir=target.parent))
    else:
        workdir = target
        workdir.mkdir(parents=True, exist_ok=True)

    set_language("en")
    controller = demo_controller()
    controller.open_path(Path("/tmp/vbios-studio-demo.rom"))
    app_id = f"io.github.vbios_studio.selftest.p{os.getpid()}x{uuid.uuid4().hex[:8]}"
    app = Adw.Application(application_id=app_id, flags=0)
    result = {"code": 1}
    failure: list[str] = []
    watchdog: list[int] = []
    activated = {"value": False}

    def fail(message: str) -> None:
        failure.append(message)
        print(f"selftest: FAIL: {message}", file=sys.stderr)
        result["code"] = 1
        app.quit()

    def finish() -> None:
        if watchdog:
            GLib.source_remove(watchdog.pop())
        if default_target and result["code"] == 0:
            target.mkdir(parents=True, exist_ok=True)
            for name in ("01-main-window.png", "02-fields-risk.png", "03-apply-panel.png"):
                os.replace(workdir / name, target / name)
            shutil.rmtree(workdir, ignore_errors=True)
        elif workdir != target:
            shutil.rmtree(workdir, ignore_errors=True)

    def activate(_app) -> None:
        activated["value"] = True
        try:
            install_css()
            window = MainWindow(app, controller)
            window.set_default_size(1280, 840)
            window.present()

            if RISK_COLORS != {
                "T0": "#6B7280",
                "T1": "#2563EB",
                "T2": "#D97706",
                "T3": "#DC2626",
            }:
                fail("risk colour constants drifted")
                return
            controller.set_value("power_min_w", "120")
            controller.set_value("gpc_offset_max_mhz", "250")
            if not controller.can_undo:
                fail("undo stack did not record edits")
                return
            controller.undo()
            if controller.value_of(controller.find_field("gpc_offset_max_mhz")) != "200":  # type: ignore[arg-type]
                fail("undo did not restore the previous value")
                return
            controller.redo()

            frames: list = []

            def step(delay: int, callback) -> None:
                frames.append(callback)
                GLib.timeout_add(delay, lambda: (frames.pop(0)(), False)[1])

            def capture_or_retry(path: Path, callback, attempt: int = 0) -> None:
                try:
                    _capture(window, path)
                except Exception as exc:
                    if attempt < 20 and ("empty snapshot" in str(exc) or "not mapped" in str(exc)):
                        step(100, lambda: capture_or_retry(path, callback, attempt + 1))
                        return
                    traceback.print_exc()
                    fail(str(exc))
                    return
                callback()

            def capture_main() -> None:
                try:
                    if len(window.field_table.store) == 0:
                        raise AssertionError("field table is empty")
                    _assert_a11y(window)
                except Exception as exc:
                    traceback.print_exc()
                    fail(str(exc))
                    return

                def after_main() -> None:
                    controller.set_section("power")
                    controller.set_view_mode("form")
                    step(250, capture_form)

                capture_or_retry(workdir / "01-main-window.png", after_main)

            def capture_form() -> None:
                def after_form() -> None:
                    window.navigate("apply")
                    window.apply_panel.dry_run()
                    step(250, capture_apply)

                capture_or_retry(workdir / "02-fields-risk.png", after_form)

            def capture_apply() -> None:
                def after_apply() -> None:
                    try:
                        for name in (
                            "01-main-window.png",
                            "02-fields-risk.png",
                            "03-apply-panel.png",
                        ):
                            size = _png_size(workdir / name)
                            if size[0] < 800 or size[1] < 600:
                                raise AssertionError(f"{name} is too small: {size}")
                    except Exception as exc:
                        traceback.print_exc()
                        fail(str(exc))
                        return
                    print(
                        f"vbios-studio {__version__} selftest: ok "
                        "(window, a11y, undo/redo, 3 screenshots)"
                    )
                    result["code"] = 0
                    app.quit()

                capture_or_retry(workdir / "03-apply-panel.png", after_apply)

            def ready(attempt: int = 0) -> None:
                if window.get_native() is None or window.get_width() < 800:
                    if attempt >= 20:
                        fail("window did not map within 5 s")
                        return
                    step(250, lambda: ready(attempt + 1))
                    return
                capture_main()

            step(250, ready)

            def _watchdog() -> bool:
                fail("timed out after 20 s; window/screenshot pipeline stalled")
                return False

            watchdog.append(GLib.timeout_add(20_000, _watchdog))
        except Exception as exc:
            traceback.print_exc()
            fail(f"activate failed: {exc}")

    app.connect("activate", activate)
    try:
        run_code = app.run([])
    except Exception as exc:
        traceback.print_exc()
        print(f"selftest: FAIL: {exc}", file=sys.stderr)
        finish()
        return 1
    if result["code"] != 0 and not failure:
        print(
            "selftest: FAIL: application exited without a successful run "
            f"(run()={run_code}, activated={activated['value']})",
            file=sys.stderr,
        )
    finish()
    return result["code"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vbios-studio --selftest")
    parser.add_argument("--screenshots", metavar="DIR")
    args = parser.parse_args(list(argv or []))
    return run_selftest(Path(args.screenshots) if args.screenshots else None)
