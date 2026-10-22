"""Pure field filtering for the GUI (no GTK, easy to test)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from vbios_studio.domain.models import FieldSnapshot


@dataclass(frozen=True)
class FilterState:
    query: str = ""
    only_modified: bool = False
    only_t3: bool = False
    only_current_section: bool = False

    def with_query(self, query: str) -> FilterState:
        return replace(self, query=query)

    def toggled(self, name: str, value: bool) -> FilterState:
        if name == "only_modified":
            return replace(self, only_modified=bool(value))
        if name == "only_t3":
            return replace(self, only_t3=bool(value))
        if name == "only_current_section":
            return replace(self, only_current_section=bool(value))
        raise ValueError(f"unknown filter: {name}")

    @property
    def active_count(self) -> int:
        return sum((self.only_modified, self.only_t3, self.only_current_section))


def matches_query(field: FieldSnapshot, query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    haystacks = (field.key, field.label, field.description or "")
    return any(needle in text.casefold() for text in haystacks)


def filter_fields(
    fields: Sequence[FieldSnapshot],
    changes: Mapping[str, str],
    filters: FilterState,
    current_section: str,
) -> list[FieldSnapshot]:
    """Filter visible fields; the returned length is the counter shown in the UI."""
    result: list[FieldSnapshot] = []
    for field in fields:
        if not matches_query(field, filters.query):
            continue
        if filters.only_modified and field.key not in changes:
            continue
        if filters.only_t3 and field.risk != "T3":
            continue
        if filters.only_current_section and field.section != current_section:
            continue
        result.append(field)
    return result


def section_counts(fields: Iterable[FieldSnapshot]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in fields:
        counts[field.section] = counts.get(field.section, 0) + 1
    return counts
