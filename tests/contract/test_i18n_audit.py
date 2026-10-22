"""i18n contract: catalog parity, source coverage and no hard-coded UI text."""

from __future__ import annotations

from pathlib import Path

from tools.checks.i18n_audit import catalog_findings, hardcoded_ui_literals, parse_po

ROOT = Path(__file__).resolve().parents[2]
LOCALE = ROOT / "src" / "vbios_studio" / "i18n" / "locale"
UI = ROOT / "src" / "vbios_studio" / "ui"


def test_catalogs_are_complete_and_identical() -> None:
    """en/zh_CN msgid sets match, every translation is non-empty and source-covered."""
    findings = catalog_findings(
        LOCALE / "en" / "LC_MESSAGES" / "vbios_studio.po",
        LOCALE / "zh_CN" / "LC_MESSAGES" / "vbios_studio.po",
        source=ROOT / "src" / "vbios_studio",
    )
    assert not findings, "i18n defects:\n" + "\n".join(map(str, findings))


def test_catalogs_have_substantial_message_sets() -> None:
    """Both catalogues actually ship the full UI vocabulary (not a stub)."""
    english = parse_po(LOCALE / "en" / "LC_MESSAGES" / "vbios_studio.po")
    chinese = parse_po(LOCALE / "zh_CN" / "LC_MESSAGES" / "vbios_studio.po")
    assert len(english) >= 250
    assert set(english) == set(chinese)


def test_ui_layer_has_no_hardcoded_visible_strings() -> None:
    """Visible literals must go through gettext ``_()`` rather than raw strings."""
    findings = hardcoded_ui_literals(UI)
    assert not findings, "hard-coded UI text:\n" + "\n".join(map(str, findings))
