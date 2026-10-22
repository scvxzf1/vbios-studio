"""Locale normalization and translation lookup.

The first release ships English and Simplified Chinese. Message catalogs live
under ``vbios_studio/i18n/locale/<lang>/LC_MESSAGES/`` and are loaded with the
standard ``gettext`` module; t4 adds the actual ``.po``/``.mo`` files.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "zh_CN")
DEFAULT_LANGUAGE = "en"


def normalize_language(locale: str | None) -> str:
    """Map a POSIX locale (``zh_CN.UTF-8``) to a supported language code."""
    if not locale:
        return DEFAULT_LANGUAGE
    normalized = locale.split(".", maxsplit=1)[0].replace("-", "_")
    if normalized.lower().startswith("zh"):
        return "zh_CN"
    if normalized.lower().startswith("en"):
        return "en"
    return DEFAULT_LANGUAGE


def language_from_environment(environ: Mapping[str, str] | None = None) -> str:
    """Return the UI language implied by ``LC_ALL``/``LC_MESSAGES``/``LANG``."""
    env = os.environ if environ is None else environ
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(name)
        if value:
            return normalize_language(value)
    return DEFAULT_LANGUAGE
