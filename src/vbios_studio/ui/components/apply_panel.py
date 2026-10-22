# mypy: disable-error-code="misc"
# ruff: noqa: E402
"""Device card, dry-run preview and guarded apply/restore actions."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from vbios_studio.domain.models import ApplyPreview, ApplyResult
from vbios_studio.ui.a11y import set_accessible
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.dialogs.confirm_dialog import ConfirmationRules, ConfirmDialog
from vbios_studio.ui.theme import add_class

Translate = Callable[[str], str]
ConfirmCallback = Callable[[str, str, Callable[[], None]], None]


class ApplyPanel(Gtk.Box):
    def __init__(
        self,
        _: Translate,
        controller: UiController,
        on_error: Callable[[str, Exception], None],
        confirm: ConfirmCallback | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._ = _
        self.controller = controller
        self.on_error = on_error
        self.confirm = confirm
        self.last_preview: ApplyPreview | None = None
        self.apply_calls = 0
        self.restore_calls = 0

        header = Gtk.Box(spacing=12)
        title = Gtk.Label(label=_("apply.title"), xalign=0)
        title.add_css_class("vb-page-title")
        header.append(title)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        self.refresh_button = Gtk.Button(label=_("apply.refresh"))
        self.refresh_button.connect("clicked", lambda _b: self.refresh())
        set_accessible(self.refresh_button, _("apply.refresh"))
        header.append(self.refresh_button)
        self.append(header)

        warning = Gtk.Label(label=_("apply.warning"), xalign=0, wrap=True)
        warning.add_css_class("vb-warning")
        self.append(warning)

        self.device_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.device_card.add_css_class("vb-card")
        self.device_card.set_margin_top(4)
        self.append(self.device_card)

        actions = Gtk.Box(spacing=8)
        self.dry_button = Gtk.Button(label=_("apply.dry_run"))
        self.apply_button = Gtk.Button(label=_("apply.execute"))
        self.apply_button.add_css_class("destructive-action")
        self.verify_button = Gtk.Button(label=_("apply.verify"))
        self.restore_button = Gtk.Button(label=_("apply.restore"))
        for button, msgid in (
            (self.dry_button, "apply.dry_run"),
            (self.apply_button, "apply.execute"),
            (self.verify_button, "apply.verify"),
            (self.restore_button, "apply.restore"),
        ):
            set_accessible(button, _(msgid))
            actions.append(button)
        self.dry_button.connect("clicked", lambda _b: self.dry_run())
        self.apply_button.connect("clicked", lambda _b: self.request_execute())
        self.restore_button.connect("clicked", lambda _b: self.request_restore())
        self.verify_button.connect("clicked", lambda _b: self.verify())
        self.append(actions)

        self.preview_title = Gtk.Label(label=_("apply.preview"), xalign=0)
        self.preview_title.add_css_class("vb-section-title")
        self.append(self.preview_title)
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.preview_box.add_css_class("vb-card")
        self.preview_box.set_margin_top(2)
        self.append(self.preview_box)
        self.status_label = Gtk.Label(label=_("apply.not_run"), xalign=0)
        self.status_label.add_css_class("vb-dim")
        self.append(self.status_label)

    def refresh(self) -> None:
        self._clear(self.device_card)
        try:
            status = self.controller.device_status()
        except Exception as exc:
            self.device_card.append(self._line("apply.device.unavailable", str(exc)))
            return
        heading = Gtk.Label(label=self._("apply.device"), xalign=0)
        heading.add_css_class("vb-section-title")
        heading.set_margin_top(10)
        heading.set_margin_start(14)
        self.device_card.append(heading)
        rows = (
            ("apply.device.gpu", status.name),
            ("apply.device.pci", status.pci_id),
            ("apply.device.driver", status.driver_version or self._("common.unknown")),
            (
                "apply.device.override",
                self._("apply.override." + status.override_state.replace("-", "_")),
            ),
        )
        for msgid, value in rows:
            row = Gtk.Box(spacing=12)
            row.set_margin_start(14)
            row.set_margin_end(14)
            key = Gtk.Label(label=self._(msgid), xalign=0)
            key.add_css_class("vb-dim")
            key.set_size_request(150, -1)
            value_label = Gtk.Label(label=str(value), xalign=0)
            value_label.add_css_class("vb-field-label")
            row.append(key)
            row.append(value_label)
            self.device_card.append(row)
        tail = Gtk.Box()
        tail.set_size_request(-1, 10)
        self.device_card.append(tail)

    def _line(self, msgid: str, value: str) -> Gtk.Widget:
        label = Gtk.Label(label=f"{self._(msgid)}: {value}", xalign=0, wrap=True)
        label.add_css_class("vb-dim")
        label.set_margin_top(10)
        label.set_margin_bottom(10)
        label.set_margin_start(14)
        label.set_margin_end(14)
        return label

    @staticmethod
    def _clear(box: Gtk.Box) -> None:
        while (child := box.get_first_child()) is not None:
            box.remove(child)

    def dry_run(self) -> ApplyPreview | None:
        try:
            preview = self.controller.apply_dry_run()
        except Exception as exc:
            self.on_error(self._("apply.title"), exc)
            return None
        self.last_preview = preview
        self._render_preview(preview)
        self.status_label.set_text(self._("apply.dry_run_done"))
        return preview

    def _render_preview(self, preview: ApplyPreview) -> None:
        self._clear(self.preview_box)
        data: list[tuple[str, str]] = [
            (self._("apply.preview.target"), preview.target),
            (self._("apply.preview.action"), preview.action),
            (self._("apply.preview.bytes"), str(preview.bytes_written)),
            (
                self._("apply.preview.restart"),
                self._("common.yes") if preview.restart_required else self._("common.no"),
            ),
        ]
        for key, value in data:
            row = Gtk.Box(spacing=10)
            row.set_margin_start(12)
            row.set_margin_end(12)
            row.set_margin_top(2)
            row.set_margin_bottom(2)
            label = Gtk.Label(label=key, xalign=0)
            label.add_css_class("vb-dim")
            label.set_size_request(150, -1)
            value_label = Gtk.Label(label=value, xalign=0)
            add_class(value_label, "vb-mono")
            row.append(label)
            row.append(value_label)
            self.preview_box.append(row)
        for key, value in preview.values.items():
            row = Gtk.Box(spacing=10)
            row.set_margin_start(12)
            row.set_margin_end(12)
            row.set_margin_top(2)
            row.set_margin_bottom(2)
            label = Gtk.Label(label=str(key), xalign=0)
            label.add_css_class("vb-dim")
            label.set_size_request(150, -1)
            value_label = Gtk.Label(label=str(value), xalign=0)
            value_label.add_css_class("vb-mono")
            value_label.set_selectable(True)
            row.append(label)
            row.append(value_label)
            self.preview_box.append(row)
        for warning in preview.warnings:
            label = Gtk.Label(label=warning, xalign=0, wrap=True)
            label.add_css_class("vb-note")
            self.preview_box.append(label)

    def request_execute(self) -> None:
        def run() -> None:
            self.apply_calls += 1
            try:
                result = self.controller.apply_execute()
            except Exception as exc:
                self.on_error(self._("apply.title"), exc)
                return
            self._show_result(result)

        self._confirm(self._("apply.confirm.title"), self._("apply.confirm.body"), run)

    def request_restore(self) -> None:
        def run() -> None:
            self.restore_calls += 1
            try:
                result = self.controller.apply_restore()
            except Exception as exc:
                self.on_error(self._("apply.title"), exc)
                return
            self._show_result(result)

        self._confirm(
            self._("apply.restore_confirm.title"), self._("apply.restore_confirm.body"), run
        )

    def _confirm(self, title: str, body: str, run: Callable[[], None]) -> None:
        if self.confirm is not None:
            self.confirm(title, body, run)
            return
        dialog = ConfirmDialog(
            self.get_root(),
            title,
            body,
            rules=ConfirmationRules(require_checkbox=True, required_word=""),
            confirm_label=self._("common.confirm"),
            cancel_label=self._("common.cancel"),
            checkbox_label=self._("apply.confirm.checkbox"),
            on_confirm=run,
        )
        dialog.present()

    def _show_result(self, result: ApplyResult) -> None:
        self.status_label.set_text(result.message or result.state)
        if result.ok:
            self.status_label.remove_css_class("vb-bad")
            self.status_label.add_css_class("vb-ok")
        else:
            self.status_label.remove_css_class("vb-ok")
            self.status_label.add_css_class("vb-bad")

    def verify(self) -> None:
        try:
            status = self.controller.device_status()
        except Exception as exc:
            self.on_error(self._("apply.verify"), exc)
            return
        self.status_label.set_text(
            self._("apply.verify_state").format(
                state=self._("apply.override." + status.override_state.replace("-", "_"))
            )
        )

    def retranslate(self, _: Translate) -> None:
        self._ = _
        self.refresh_button.set_label(_("apply.refresh"))
        self.dry_button.set_label(_("apply.dry_run"))
        self.apply_button.set_label(_("apply.execute"))
        self.verify_button.set_label(_("apply.verify"))
        self.restore_button.set_label(_("apply.restore"))
        self.preview_title.set_text(_("apply.preview"))
        self.refresh()
