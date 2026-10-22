"""Executable upstream-parity assertion for the field catalogue.

The vendored ``nvidia_vbios`` parser is the source of truth for common fields.
Our ``FieldSnapshot`` is a projection plus deliberately added metadata, so the
comparison maps each upstream key onto the attribute that must preserve it and
declares every extra attribute explicitly.  Any value drift, missing field or
undeclared metadata key becomes a :class:`ParityIssue`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Final, Protocol

from vbios_studio.domain.catalog import CANONICAL_FIELD_KEYS, format_value

# Our attribute -> how to read the corresponding upstream descriptor value.
# ``experimental`` is intentionally absent: upstream uses it as an evidence
# marker while ours is derived from the T0-T3 risk registry (a new metadata key).
COMMON_ATTRIBUTES: Final[dict[str, str]] = {
    "key": "key",
    "label": "label",
    "unit": "units",
    "current": "current",
    "default": "factory_default",
    "minimum": "minimum",
    "maximum": "maximum",
    "editable": "editable",
    "offset": "offset",
    "opt_in": "opt_in",
    "depends_on": "depends_on",
}
EXTRA_METADATA_KEYS: Final[frozenset[str]] = frozenset(
    {"section", "risk", "description", "experimental"}
)


class FieldView(Protocol):
    """Minimal attribute surface of ``FieldSnapshot`` used by the comparator."""

    key: str
    label: str
    unit: str
    current: str | None
    default: str | None
    minimum: str | None
    maximum: str | None
    editable: bool
    offset: int | None
    opt_in: bool
    depends_on: Mapping[str, Any] | None


@dataclass(frozen=True, slots=True)
class ParityIssue:
    """One difference between the upstream descriptor and our catalogue."""

    key: str
    attribute: str
    upstream: Any
    ours: Any
    kind: str = "value-drift"

    def __str__(self) -> str:
        return f"{self.key}.{self.attribute}: upstream={self.upstream!r} ours={self.ours!r}"


def _number(value: Any) -> str | None:
    """Canonicalise numbers so 70, 70.0 and Decimal('70.0') compare equal."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "1" if value else "0"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    if not amount.is_finite():
        return str(value)
    if amount == amount.to_integral_value():
        return str(int(amount))
    return format(amount.normalize(), "f")


def _upstream_value(descriptor: Mapping[str, Any], attribute: str) -> Any:
    if attribute == "unit":
        return str(descriptor.get("units") or "")
    if attribute in {"current", "default"}:
        source = "current" if attribute == "current" else "factory_default"
        return format_value(descriptor.get(source))
    if attribute in {"minimum", "maximum"}:
        bounds = descriptor.get("bounds") or {}
        return format_value(bounds.get(attribute))
    if attribute == "editable":
        return bool(descriptor.get("editable"))
    if attribute == "offset":
        offsets = descriptor.get("offsets") or ()
        return int(offsets[0]) if offsets else None
    if attribute == "opt_in":
        return bool(descriptor.get("opt_in"))
    if attribute == "depends_on":
        raw = descriptor.get("depends_on")
        return dict(raw) if isinstance(raw, Mapping) else None
    value = descriptor.get(attribute)
    return str(value) if attribute in {"key", "label"} and value is not None else value


def _our_value(field: FieldView, attribute: str) -> Any:
    value = getattr(field, attribute)
    if attribute in {"key", "label"}:
        return str(value)
    if attribute == "unit":
        return str(value)
    if attribute == "depends_on":
        return dict(value) if isinstance(value, Mapping) else None
    return value


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float, Decimal)) or isinstance(right, (int, float, Decimal)):
        return _number(left) == _number(right)
    return left == right


def compare_catalogs(
    upstream_fields: Sequence[Mapping[str, Any]],
    our_fields: Sequence[FieldView],
) -> tuple[ParityIssue, ...]:
    """Compare every common field attribute and validate catalogue extensions."""
    upstream = {str(item["key"]): item for item in upstream_fields}
    ours = {field.key: field for field in our_fields}
    issues: list[ParityIssue] = []
    for key, descriptor in upstream.items():
        field = ours.get(key)
        if field is None:
            issues.append(ParityIssue(key, "key", key, None, "missing-field"))
            continue
        for attribute in COMMON_ATTRIBUTES:
            upstream_value = _upstream_value(descriptor, attribute)
            our_value = _our_value(field, attribute)
            if not _same(upstream_value, our_value):
                issues.append(ParityIssue(key, attribute, upstream_value, our_value))
    common_order = [field.key for field in our_fields if field.key in upstream]
    if common_order != list(upstream):
        issues.append(ParityIssue("*", "order", list(upstream), common_order, "field-order-drift"))
    for key in sorted(set(ours) - set(upstream)):
        field = ours[key]
        if key not in CANONICAL_FIELD_KEYS:
            issues.append(ParityIssue(key, "key", None, key, "undeclared-extra-field"))
        elif field.current is not None or field.editable or field.offset is not None:
            issues.append(
                ParityIssue(key, "placeholder", None, field.current, "extra-field-not-read-only")
            )
    return tuple(issues)


def metadata_attribute_issues(field_type: type[object]) -> tuple[str, ...]:
    """Return FieldSnapshot attributes that are neither common nor declared extra."""
    names = set(getattr(field_type, "__dataclass_fields__", {}))
    declared = set(COMMON_ATTRIBUTES) | EXTRA_METADATA_KEYS
    return tuple(sorted(names - declared))
