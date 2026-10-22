"""i18n completeness and hard-coded user-visible string scanners."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

MSGID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")
VISIBLE_METHODS: Final[frozenset[str]] = frozenset(
    {
        "set_text",
        "set_label",
        "set_title",
        "set_subtitle",
        "set_tooltip_text",
        "set_placeholder_text",
        "set_markup",
    }
)
VISIBLE_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "label",
        "title",
        "subtitle",
        "text",
        "tooltip_text",
        "placeholder_text",
        "heading",
        "body",
        "message",
        "detail",
        "description",
    }
)
ALLOWED_LITERALS: Final[frozenset[str]] = frozenset(
    {"", "-", "—", "–", "…", "T0", "T1", "T2", "T3", "N/A"}
)
_HAS_LETTER = re.compile(r"[A-Za-z\u4e00-\u9fff]")


@dataclass(frozen=True, slots=True)
class I18nFinding:
    """A missing translation or an untranslated literal in the UI layer."""

    path: str
    line: int
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.kind}: {self.detail}"


def _decode_po_strings(lines: list[str]) -> str:
    parts = [ast.literal_eval(line.strip()) for line in lines]
    return "".join(parts)


def parse_po(path: Path) -> dict[str, str]:
    """Parse a gettext ``.po`` file without requiring Babel at test time."""
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


def source_msgids(source: Path) -> set[str]:
    """Collect dotted message ids referenced as string literals in Python."""
    found: set[str] = set()
    for path in sorted(source.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and MSGID_PATTERN.fullmatch(node.value)
                and not node.value.startswith("io.github")
                and not node.value.endswith("_")
            ):
                found.add(node.value)
    return found


def catalog_findings(
    english_po: Path,
    chinese_po: Path,
    *,
    source: Path,
) -> tuple[I18nFinding, ...]:
    """Check msgid parity, non-empty translations and source coverage."""
    findings: list[I18nFinding] = []
    english = parse_po(english_po)
    chinese = parse_po(chinese_po)
    if not english:
        findings.append(I18nFinding(str(english_po), 1, "empty-catalog", "English catalogue empty"))
    if not chinese:
        findings.append(I18nFinding(str(chinese_po), 1, "empty-catalog", "Chinese catalogue empty"))
    for key in sorted(set(english) - set(chinese)):
        findings.append(I18nFinding(str(chinese_po), 1, "missing-msgid", key))
    for key in sorted(set(chinese) - set(english)):
        findings.append(I18nFinding(str(english_po), 1, "missing-msgid", key))
    for path, messages in ((english_po, english), (chinese_po, chinese)):
        for key, value in sorted(messages.items()):
            if not value.strip():
                findings.append(I18nFinding(str(path), 1, "empty-translation", key))
    translated = set(english) & set(chinese)
    for key in sorted(source_msgids(source) - translated):
        findings.append(I18nFinding(str(source), 1, "untranslated-source-msgid", key))
    return tuple(findings)


def _callee_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_translation_call(node: ast.expr) -> bool:
    return isinstance(node, ast.Call) and _callee_name(node.func) in {
        "_",
        "gettext",
        "ngettext",
    }


def _literal(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = [
            value.value
            for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
        return "".join(parts) if parts else None
    return None


def _visible_candidates(tree: ast.AST) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        method = _callee_name(node.func)
        if method in VISIBLE_METHODS and node.args:
            text = _literal(node.args[0])
            if text is not None:
                candidates.append((getattr(node, "lineno", 1), text))
        for keyword in node.keywords:
            if keyword.arg in VISIBLE_KEYWORDS and not _is_translation_call(keyword.value):
                text = _literal(keyword.value)
                if text is not None:
                    candidates.append((getattr(keyword, "lineno", 1), text))
    return candidates


def hardcoded_ui_literals(ui_root: Path) -> tuple[I18nFinding, ...]:
    """Find user-visible literals that bypass the gettext ``_()`` helper.

    ``demo_data.py`` is synthetic document data rather than UI chrome, and the
    semantic values are intentionally language-neutral input fixtures.
    """
    findings: list[I18nFinding] = []
    for path in sorted(ui_root.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "demo_data.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for line, text in _visible_candidates(tree):
            stripped = text.strip()
            if not stripped or stripped in ALLOWED_LITERALS or not _HAS_LETTER.search(stripped):
                continue
            if (
                "{" in stripped
                and "}" in stripped
                and not _HAS_LETTER.search(re.sub(r"\{[^}]*\}", "", stripped))
            ):
                continue
            findings.append(
                I18nFinding(
                    str(path),
                    line,
                    "hardcoded-ui-string",
                    f"untranslated visible literal: {stripped!r}",
                )
            )
    return tuple(findings)


def translated_msgids(path: Path) -> Iterable[str]:
    """Convenience helper: sorted msgids in one catalogue."""
    return sorted(parse_po(path))
