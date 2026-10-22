"""Visual theme for VBIOS Studio: fixed risk colours, shared CSS and light/dark switching."""

from __future__ import annotations

from typing import Final

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

# The single source of truth for risk colours (docs/requirements.md FR-2.10).
RISK_COLORS: Final[dict[str, str]] = {
    "T0": "#6B7280",
    "T1": "#2563EB",
    "T2": "#D97706",
    "T3": "#DC2626",
}
RISK_CSS_CLASSES: Final[dict[str, str]] = {
    "T0": "risk-t0",
    "T1": "risk-t1",
    "T2": "risk-t2",
    "T3": "risk-t3",
}
GRID: Final[int] = 8
RISK_CSS: Final[str] = "\n".join(
    f".{RISK_CSS_CLASSES[risk]} {{ color: {color}; background-color: alpha({color}, 0.16); }}"
    for risk, color in RISK_COLORS.items()
)

CSS = (
    """
window, .vb-window { background-color: @theme_bg_color; }
.vb-header-title { font-weight: 800; font-size: 1.02em; }
.vb-header-sub { font-size: 0.76em; opacity: 0.60; }
.vb-card {
  background-color: alpha(currentColor, 0.035);
  border: 1px solid alpha(currentColor, 0.10);
  border-radius: 12px;
}
.vb-card-strong {
  background-color: alpha(currentColor, 0.055);
  border: 1px solid alpha(currentColor, 0.14);
  border-radius: 12px;
}
.vb-product { font-size: 1.30em; font-weight: 800; }
.vb-chip {
  font-size: 0.78em; font-weight: 600; padding: 2px 10px; border-radius: 999px;
  background-color: alpha(currentColor, 0.09);
}
.vb-chip-accent { color: #1c71d8; background-color: alpha(#3584e4, 0.14); }
.vb-dim { opacity: 0.64; font-size: 0.86em; }
.vb-mono, .vb-num {
  font-family: "DejaVu Sans Mono", "Noto Sans Mono", monospace;
  font-feature-settings: "tnum";
}
.vb-ok { color: #26a269; font-weight: 700; }
.vb-bad { color: #e5484d; font-weight: 700; }
.vb-section-title { font-weight: 800; font-size: 1.02em; }
.vb-page-title { font-weight: 800; font-size: 1.45em; }
.vb-page-sub { opacity: 0.66; font-size: 0.92em; }
.vb-statusbar {
  padding: 6px 14px; font-size: 0.82em;
  background-color: alpha(currentColor, 0.035);
  border-top: 1px solid alpha(currentColor, 0.10);
}
.vb-log {
  font-family: "DejaVu Sans Mono", "Noto Sans Mono", monospace;
  font-size: 0.80em;
  background-color: alpha(currentColor, 0.025);
}
.vb-nav-row { padding: 4px 10px; border-radius: 8px; } .navigation-sidebar row { min-height: 32px; }
.vb-nav-row:selected { background-color: alpha(#3584e4, 0.16); }
.vb-nav-count { font-size: 0.80em; opacity: 0.62; }
.vb-badge {
  font-size: 0.72em; font-weight: 800; padding: 1px 8px; border-radius: 999px;
}
.vb-badge-exp {
  font-size: 0.68em; font-weight: 700; padding: 1px 7px; border-radius: 999px;
  color: #7C3AED; background-color: alpha(#8B5CF6, 0.16);
}
.vb-entry-vbios { min-width: 108px; }
.vb-field-row { padding: 8px 12px; }
.vb-field-row:selected { background-color: alpha(#3584e4, 0.10); border-radius: 8px; }
.vb-table-head { padding: 4px 12px; font-size: 0.78em; font-weight: 700; opacity: 0.62; }
.vb-warning {
  padding: 10px 12px; border-radius: 10px;
  background-color: alpha(#DC2626, 0.09); border: 1px solid alpha(#DC2626, 0.25);
}
.vb-note {
  padding: 10px 12px; border-radius: 10px;
  background-color: alpha(#D97706, 0.08); border: 1px solid alpha(#D97706, 0.22);
}
.vb-empty-title { font-size: 1.55em; font-weight: 800; }
.vb-empty-sub { font-size: 0.98em; opacity: 0.68; }
.vb-kbd {
  font-family: "DejaVu Sans Mono", monospace; font-size: 0.82em;
  padding: 1px 6px; border-radius: 5px;
  background-color: alpha(currentColor, 0.10); border: 1px solid alpha(currentColor, 0.14);
}
.vb-diff-left { background-color: alpha(#DC2626, 0.05); }
.vb-diff-right { background-color: alpha(#2563EB, 0.05); }
.vb-footer-note { font-size: 0.78em; opacity: 0.58; }
"""
    + RISK_CSS
)

_css_installed = False
_desktop_theme: bool | None = None


def install_css() -> None:
    """Install the application stylesheet once per display."""
    global _css_installed
    if _css_installed:
        return
    display = Gdk.Display.get_default()
    if display is None:
        return
    provider = Gtk.CssProvider()
    provider.load_from_string(CSS)
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _css_installed = True


def apply_theme(theme: str | None) -> None:
    """Apply ``system``/``light``/``dark``; ``None`` restores the desktop choice."""

    global _desktop_theme
    settings = Gtk.Settings.get_default()
    if settings is None:
        return
    names = {prop.name for prop in Gtk.Settings.list_properties()}
    if "gtk-interface-color-scheme" in names and hasattr(Gtk, "InterfaceColorScheme"):
        import gi as _gi

        _gi.require_version("Gtk", "4.0")
        scheme = Gtk.InterfaceColorScheme
        if _desktop_theme is None:
            _desktop_theme = settings.get_property("gtk-interface-color-scheme") == scheme.DARK
        if theme is None or theme == "system":
            settings.set_property(
                "gtk-interface-color-scheme", scheme.DARK if _desktop_theme else scheme.LIGHT
            )
        else:
            settings.set_property(
                "gtk-interface-color-scheme", scheme.DARK if theme == "dark" else scheme.LIGHT
            )
        return
    key = "gtk-application-prefer-dark-theme"
    if _desktop_theme is None:
        _desktop_theme = bool(settings.get_property(key))
    if theme is None or theme == "system":
        settings.set_property(key, _desktop_theme)
    else:
        settings.set_property(key, theme == "dark")


def add_class(widget: Gtk.Widget, *names: str) -> Gtk.Widget:
    for name in names:
        widget.add_css_class(name)
    return widget
