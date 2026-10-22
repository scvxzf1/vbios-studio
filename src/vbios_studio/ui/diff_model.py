"""Pure comparison of two document snapshots (no GTK, no I/O)."""

from __future__ import annotations

from typing import Any

from vbios_studio.domain.models import DocumentSnapshot, FieldSnapshot, ImageSnapshot


def _image_checksum(image: ImageSnapshot) -> str:
    value = getattr(image, "checksum", None)
    if value:
        return str(value)
    return "balanced" if image.checksum_ok else "unbalanced"


def _field_value(field: FieldSnapshot | None) -> str | None:
    return None if field is None else field.current


def compare(left: DocumentSnapshot, right: DocumentSnapshot) -> dict[str, Any]:
    """Return the frozen t14 diff structure.

    ``field_diffs`` and ``image_diffs`` are empty when the two snapshots describe the
    same document; otherwise every differing field/image is listed.
    """
    left_fields = {field.key: field for field in left.fields}
    right_fields = {field.key: field for field in right.fields}
    keys = list(left_fields) + [key for key in right_fields if key not in left_fields]
    field_diffs: list[dict[str, Any]] = []
    for key in keys:
        lf, rf = left_fields.get(key), right_fields.get(key)
        lv, rv = _field_value(lf), _field_value(rf)
        if lf is not None and rf is not None and lv == rv:
            continue
        field = lf if lf is not None else rf
        if field is None:
            continue
        field_diffs.append(
            {
                "key": key,
                "label": field.label,
                "left": lv,
                "right": rv,
                "risk": field.risk,
                "changed": True,
            }
        )
    left_images = {image.index: image for image in left.images}
    right_images = {image.index: image for image in right.images}
    image_diffs: list[dict[str, Any]] = []
    for index in sorted(set(left_images) | set(right_images)):
        li, ri = left_images.get(index), right_images.get(index)
        if li is not None and ri is not None:
            equal = (
                _image_checksum(li) == _image_checksum(ri)
                and li.size == ri.size
                and li.kind == ri.kind
            )
        else:
            equal = False
        if equal:
            continue
        image = li if li is not None else ri
        if image is None:
            continue
        image_diffs.append(
            {
                "index": index,
                "type": image.kind,
                "size": image.size,
                "checksum_left": _image_checksum(li) if li else None,
                "checksum_right": _image_checksum(ri) if ri else None,
                "equal": equal,
            }
        )
    return {"field_diffs": field_diffs, "image_diffs": image_diffs}
