"""Runtime language switching updates visible text without restarting."""

from __future__ import annotations

import pytest

from tests.ui.support import pump_events
from vbios_studio.i18n import gettext as _
from vbios_studio.i18n import set_language
from vbios_studio.ui.controller import UiController
from vbios_studio.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def restore_english():
    yield
    set_language("en")


def test_language_switch_updates_visible_labels(gtk_initialised, controller: UiController) -> None:
    set_language("en")
    window = MainWindow(None, controller)
    window.present()
    pump_events(4)
    assert window.field_toolbar.title.get_text() == "Fields"
    set_language("zh_CN")
    window.retranslate()
    pump_events(4)
    assert window.field_toolbar.title.get_text() == "字段"
    assert window.header.search_entry.get_placeholder_text() == "搜索字段…"
    assert window.field_table.view.get_columns()[1].get_title() == "当前值"
    assert window.status_bar.file_label.get_text() == "vbios-studio-test.rom"
    window.destroy()


def test_gettext_has_chinese_for_risk_and_fields() -> None:
    set_language("zh_CN")
    assert _("risk.t3") == "T3 高风险"
    assert _("fields.column.current") == "当前值"
    set_language("en")
    assert _("risk.t3") == "T3 High"
