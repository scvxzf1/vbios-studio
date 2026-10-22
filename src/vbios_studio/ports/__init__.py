"""Abstract ports (Protocols) consumed by the UI and implemented by adapters.

Ports depend only on the pure domain package. They must never import GTK,
concrete adapters, the UI, the application layer or upstream ``nvidia_vbios``
code; see the ``ports-no-implementations`` import-linter contract.
"""

from .apply import ApplyPort
from .diff import DiffPort
from .editor import EditorPort
from .profile import ProfilePort

__all__ = ["ApplyPort", "DiffPort", "EditorPort", "ProfilePort"]
