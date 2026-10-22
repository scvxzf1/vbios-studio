"""File-dialog glue for preset JSON files.

The domain validates the preset (schema, architecture, bounds); this module only
moves the already-validated mapping between a path and the UI.  ROM bytes never
pass through here.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def write_profile(path: Path, data: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("preset root must be a JSON object")
    return payload
