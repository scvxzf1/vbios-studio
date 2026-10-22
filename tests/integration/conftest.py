"""Make shared synthetic-ROM and fake-registry fixtures importable."""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS = Path(__file__).resolve().parents[1]
for _folder in ("core", "apply"):
    _path = str(_TESTS / _folder)
    if _path not in sys.path:
        sys.path.insert(0, _path)
