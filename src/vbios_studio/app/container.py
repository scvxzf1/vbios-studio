"""Composition root for VBIOS Studio.

Concrete adapters are constructed here and injected as ports. The GUI path gets
one fully wired ``UiController``; the CLI/version paths never import GTK or
open a device.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from vbios_studio.ui.controller import UiController

from vbios_studio.ports.apply import ApplyPort
from vbios_studio.ports.diff import DiffPort
from vbios_studio.ports.editor import EditorPort
from vbios_studio.ports.profile import ProfilePort


def build_editor_port() -> EditorPort:
    """Create the upstream-backed editor adapter."""
    from vbios_studio.adapters.upstream import UpstreamEditorAdapter

    return UpstreamEditorAdapter()


def build_diff_port(editor: EditorPort | None = None) -> DiffPort:
    """Create the production diff adapter using the pure UI-neutral comparator."""
    from vbios_studio.adapters.diff import UpstreamDiffAdapter
    from vbios_studio.adapters.upstream import UpstreamEditorAdapter
    from vbios_studio.ui.diff_model import compare

    concrete = (
        cast(UpstreamEditorAdapter, editor) if editor is not None else UpstreamEditorAdapter()
    )
    return UpstreamDiffAdapter(concrete, compare)


def build_profile_port(editor: EditorPort | None = None) -> ProfilePort:
    """Create the production profile adapter backed by the editor port."""
    from vbios_studio.adapters.profile import UpstreamProfileAdapter
    from vbios_studio.adapters.upstream import UpstreamEditorAdapter

    concrete = (
        cast(UpstreamEditorAdapter, editor) if editor is not None else UpstreamEditorAdapter()
    )
    return UpstreamProfileAdapter(concrete)


def build_apply_port() -> ApplyPort:
    """Create the platform-specific apply adapter.

    Linux gets a fail-closed, guidance-only loader adapter; Windows gets the
    controlled registry adapter. Unsupported platforms get the Windows adapter
    so its platform error remains explicit rather than silently succeeding.
    """
    if sys.platform.startswith("linux"):
        from vbios_studio.adapters.system.linux_loader import LinuxLoaderAdapter

        return LinuxLoaderAdapter()
    from vbios_studio.adapters.system.windows_registry import WindowsRegistryAdapter

    return WindowsRegistryAdapter()


def build_gui_controller(
    *,
    editor: EditorPort | None = None,
    diff: DiffPort | None = None,
    profile: ProfilePort | None = None,
    apply: ApplyPort | None = None,
) -> UiController:
    """Build a fully wired real ``UiController`` for the GTK front end.

    Optional ports are injection points for integration tests; production uses
    the upstream editor, production diff/profile adapters and the controlled
    system apply adapter.
    """
    from vbios_studio.ui.controller import UiController

    concrete_editor = editor or build_editor_port()
    concrete_diff = diff or build_diff_port(concrete_editor)
    concrete_profile = profile or build_profile_port(concrete_editor)
    concrete_apply = apply or build_apply_port()
    return UiController(concrete_editor, concrete_diff, concrete_profile, concrete_apply)
