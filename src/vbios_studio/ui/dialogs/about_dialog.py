"""Help → About, including the honest testing disclaimer."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

Translate = Callable[[str], str]


def show_about(parent: Gtk.Window, _: Translate) -> Adw.AboutDialog:
    from vbios_studio import __version__

    dialog = Adw.AboutDialog(
        application_name="VBIOS Studio",
        application_icon="io.github.vbios_studio",
        developer_name="VBIOS Studio contributors",
        version=str(__version__),
        comments=_("about.comments"),
        website="https://github.com/scvxzf1/vbios-studio",
        issue_url="https://github.com/scvxzf1/vbios-studio/issues",
        license_type=Gtk.License.GPL_3_0,
    )
    dialog.set_copyright("GPL-3.0-or-later · based on Panchovix nvidia-vbios-vix-editor")
    dialog.add_credit_section(_("about.upstream"), ["Panchovix"])
    dialog.present(parent)
    return dialog
