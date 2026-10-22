"""Catalog completeness: en and zh_CN msgids must match exactly."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from vbios_studio.i18n import gettext as _
from vbios_studio.i18n import set_language

ROOT = Path(__file__).resolve().parents[2]
LOCALE = ROOT / "src" / "vbios_studio" / "i18n" / "locale"
SOURCE = ROOT / "src" / "vbios_studio"
MSGID = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")


def _decode_po_strings(lines: list[str]) -> str:
    """Decode one or more quoted PO string fragments."""
    parts = [ast.literal_eval(line.strip()) for line in lines]
    return "".join(parts)


def parse_po(path: Path) -> dict[str, str]:
    """Minimal .po reader (Babel is not a runtime test dependency)."""
    messages: dict[str, str] = {}
    msgid: list[str] | None = None
    msgstr: list[str] | None = None
    for raw in [*path.read_text(encoding="utf-8").splitlines(), ""]:
        line = raw.strip()
        if line.startswith("msgid ") and msgid is None:
            msgid, msgstr = [line[6:]], None
        elif line.startswith("msgstr ") and msgid is not None:
            msgstr = [line[7:]]
        elif line.startswith('"') and msgid is not None and msgstr is None:
            msgid.append(line)
        elif line.startswith('"') and msgstr is not None:
            msgstr.append(line)
        elif not line and msgid is not None:
            if msgstr is not None:
                key = _decode_po_strings(msgid)
                if key:
                    messages[key] = _decode_po_strings(msgstr)
            msgid, msgstr = None, None
    return messages


def source_msgids() -> set[str]:
    found: set[str] = set()
    for path in SOURCE.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                if (
                    MSGID.fullmatch(value)
                    and not value.startswith("io.github")
                    and not value.endswith("_")
                ):
                    found.add(value)
    return found


def test_catalogs_have_identical_msgid_sets() -> None:
    english = parse_po(LOCALE / "en" / "LC_MESSAGES" / "vbios_studio.po")
    chinese = parse_po(LOCALE / "zh_CN" / "LC_MESSAGES" / "vbios_studio.po")
    assert english, "English catalogue is empty"
    assert set(english) == set(chinese)
    assert all(value for value in english.values())
    assert all(value for value in chinese.values())


def test_every_source_msgid_is_translated() -> None:
    english = parse_po(LOCALE / "en" / "LC_MESSAGES" / "vbios_studio.po")
    chinese = parse_po(LOCALE / "zh_CN" / "LC_MESSAGES" / "vbios_studio.po")
    missing_en = sorted(source_msgids() - set(english))
    missing_zh = sorted(source_msgids() - set(chinese))
    assert not missing_en, f"missing English msgids: {missing_en}"
    assert not missing_zh, f"missing Chinese msgids: {missing_zh}"


def test_runtime_switching_works() -> None:
    set_language("en")
    assert _("fields.title") == "Fields"
    set_language("zh_CN")
    assert _("fields.title") == "字段"
    set_language("en")


def test_compiled_catalog_exists() -> None:
    for language in ("en", "zh_CN"):
        assert (LOCALE / language / "LC_MESSAGES" / "vbios_studio.mo").exists()
