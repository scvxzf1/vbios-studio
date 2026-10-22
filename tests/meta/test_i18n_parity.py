"""Meta-tests: i18n and upstream-parity checks must reject broken inputs."""

from __future__ import annotations

from pathlib import Path

from tools.checks.i18n_audit import catalog_findings, hardcoded_ui_literals
from tools.checks.parity import COMMON_ATTRIBUTES, compare_catalogs, metadata_attribute_issues

from vbios_studio.domain.models import FieldSnapshot


def _po(path: Path, entries: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ['msgid ""', 'msgstr ""', ""]
    for key, value in entries.items():
        body.extend([f'msgid "{key}"', f'msgstr "{value}"', ""])
    path.write_text("\n".join(body), encoding="utf-8")


def _field(**overrides: object) -> FieldSnapshot:
    values: dict[str, object] = {
        "key": "power_max_w",
        "label": "Board power ceiling",
        "section": "power",
        "unit": "W",
        "current": "70",
        "default": "70",
        "minimum": "30",
        "maximum": "100",
        "risk": "T3",
        "offset": 16,
        "editable": True,
        "opt_in": False,
        "experimental": False,
        "description": "derived",
        "depends_on": None,
    }
    values.update(overrides)
    return FieldSnapshot(**values)  # type: ignore[arg-type]


def _upstream(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "key": "power_max_w",
        "label": "Board power ceiling",
        "units": "W",
        "current": 70,
        "factory_default": 70,
        "bounds": {"minimum": 30, "maximum": 100},
        "editable": True,
        "offsets": [16],
        "opt_in": False,
        "depends_on": None,
    }
    values.update(overrides)
    return values


def test_missing_translation_is_detected(tmp_path: Path) -> None:
    """A msgid present in English but absent from Chinese must be reported."""
    english = tmp_path / "en.po"
    chinese = tmp_path / "zh.po"
    _po(english, {"fields.title": "Fields", "fields.unit": "Unit"})
    _po(chinese, {"fields.title": "字段"})
    findings = catalog_findings(english, chinese, source=tmp_path / "src")
    assert any(finding.kind == "missing-msgid" for finding in findings)


def test_hardcoded_visible_label_is_detected(tmp_path: Path) -> None:
    """A raw ``Gtk.Label(label="Hello")`` must be flagged."""
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "widget.py").write_text('"""Widget."""\n\nGtk.Label(label="Hello")\n', encoding="utf-8")
    findings = hardcoded_ui_literals(ui)
    assert any(finding.kind == "hardcoded-ui-string" for finding in findings)


def test_translated_visible_label_is_accepted(tmp_path: Path) -> None:
    """A label routed through ``_()`` must not be flagged."""
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "widget.py").write_text(
        '"""Widget."""\n\nGtk.Label(label=_("fields.title"))\n', encoding="utf-8"
    )
    assert hardcoded_ui_literals(ui) == ()


def test_common_value_drift_is_detected() -> None:
    """Changing a common field value must produce a parity issue."""
    issues = compare_catalogs([_upstream()], [_field(current="99")])
    assert any(issue.attribute == "current" for issue in issues)


def test_missing_field_is_detected() -> None:
    """Dropping an upstream field from our catalogue must fail parity."""
    issues = compare_catalogs([_upstream()], [])
    assert any(issue.kind == "missing-field" for issue in issues)


def test_undeclared_extra_field_is_detected() -> None:
    """Adding a non-canonical field must be rejected."""
    issues = compare_catalogs([_upstream()], [_field(key="mystery_field")])
    assert any(issue.kind == "undeclared-extra-field" for issue in issues)


def test_undeclared_metadata_attribute_is_detected() -> None:
    """A new FieldSnapshot attribute must be declared in EXTRA_METADATA_KEYS."""
    fake = type(
        "SneakyField", (), {"__dataclass_fields__": dict(FieldSnapshot.__dataclass_fields__)}
    )
    fake.__dataclass_fields__["sneaky"] = object()
    assert metadata_attribute_issues(fake) == ("sneaky",)


def test_declared_metadata_differences_are_allowed() -> None:
    """Section/risk/description/experimental may differ without breaking parity."""
    altered = _field(section="fan", risk="T0", description="extra metadata", experimental=True)
    assert compare_catalogs([_upstream()], [altered]) == ()


def test_parity_projection_covers_every_common_attribute() -> None:
    """The mapping itself stays explicit and stable."""
    assert set(COMMON_ATTRIBUTES) == {
        "key",
        "label",
        "unit",
        "current",
        "default",
        "minimum",
        "maximum",
        "editable",
        "offset",
        "opt_in",
        "depends_on",
    }
