"""Contract tests for AST-level import boundaries.

These complement import-linter so the boundaries are also checked when the
developer only runs pytest.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "vbios_studio"

FORBIDDEN = {
    "domain": {
        "gi",
        "nvidia_vbios",
        "vbios_studio.adapters",
        "vbios_studio.ui",
        "vbios_studio.app",
        "vbios_studio.ports",
        "subprocess",
        "winreg",
    },
    "ports": {
        "gi",
        "nvidia_vbios",
        "vbios_studio.adapters",
        "vbios_studio.ui",
        "vbios_studio.app",
        "subprocess",
        "winreg",
    },
    "ui": {"nvidia_vbios", "vbios_studio.adapters", "vbios_studio.app", "subprocess", "winreg"},
    "i18n": {
        "gi",
        "nvidia_vbios",
        "vbios_studio.adapters",
        "vbios_studio.ui",
        "vbios_studio.app",
        "vbios_studio.ports",
        "subprocess",
        "winreg",
    },
    "adapters": {"vbios_studio.ui", "vbios_studio.app", "subprocess", "winreg"},
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def test_import_boundaries_hold_at_ast_level() -> None:
    """No owned module imports a module forbidden for its layer."""
    violations: list[str] = []
    for layer, forbidden in FORBIDDEN.items():
        for path in sorted((PACKAGE / layer).rglob("*.py")):
            for module in _imports(path):
                if module in forbidden:
                    violations.append(f"{path.relative_to(ROOT)} imports {module}")
    assert not violations, "import boundary violations: " + "; ".join(violations)
