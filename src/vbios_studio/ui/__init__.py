"""GTK4 presentation layer (skeleton for t4).

The UI package may import PyGObject/GTK, but only lazily inside the GUI entry
point. It renders immutable domain DTOs and calls ports; it must never import
``vbios_studio.adapters`` or touch the filesystem, registry or subprocesses
directly.
"""
