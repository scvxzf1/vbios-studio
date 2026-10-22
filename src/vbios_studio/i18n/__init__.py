"""gettext-based UI catalogue with runtime language switching.

All user-visible strings in :mod:`vbios_studio.ui` are written as English msgids and
translated through this module.  ``en`` and ``zh_CN`` catalogues are kept complete;
``tests/i18n/test_catalog.py`` enforces that both contain the same msgid set.
"""

from __future__ import annotations

import gettext as _gettext
import os
from pathlib import Path

from .catalog import (
    DEFAULT_LANGUAGE,
    language_from_environment,
    normalize_language,
)
from .catalog import (
    SUPPORTED_LANGUAGES as SUPPORTED_LANGUAGES,
)

DOMAIN = "vbios_studio"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"
LANGUAGES: tuple[str, ...] = ("en", "zh_CN")
LANGUAGE_NAMES = {"en": "English", "zh_CN": "中文（简体）"}

_current_language = "en"
_catalogue: _gettext.NullTranslations = _gettext.NullTranslations()


def _detect_language() -> str:
    override = os.environ.get("VBIOS_STUDIO_LANG", "")
    if override in LANGUAGES:
        return override
    return language_from_environment()


def set_language(language: str) -> str:
    """Select a catalogue and return the effective language code."""
    global _current_language, _catalogue
    if language not in LANGUAGES:
        language = "en"
    _current_language = language
    try:
        _catalogue = _gettext.translation(
            DOMAIN, str(LOCALE_DIR), languages=[language], fallback=True
        )
    except OSError:  # pragma: no cover - a broken installation falls back to msgids
        _catalogue = _gettext.NullTranslations()
    return language


def get_language() -> str:
    return _current_language


def gettext(message: str) -> str:
    return _catalogue.gettext(message)


def ngettext(singular: str, plural: str, count: int) -> str:
    return _catalogue.ngettext(singular, plural, count)


def available_languages() -> tuple[str, ...]:
    return LANGUAGES


def language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, language)


# Initialise from the environment (the app may override with --lang before building the window).
set_language(_detect_language())


__all__ = [
    "DEFAULT_LANGUAGE",
    "DOMAIN",
    "LANGUAGES",
    "LOCALE_DIR",
    "available_languages",
    "get_language",
    "gettext",
    "language_from_environment",
    "language_name",
    "ngettext",
    "normalize_language",
    "set_language",
]
