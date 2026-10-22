"""Module entry point for ``python -m vbios_studio``."""

from __future__ import annotations

from .app.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
