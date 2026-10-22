"""Pure ROM structure scanning and additive checksum balancing.

This module deliberately re-implements the small PCIR/NPDS container walk needed
by the domain layer instead of importing the vendored editor. The parser is
bounded by image headers and never assumes that the file starts at offset zero:
NVIDIA dumps can carry an ``NVGI`` envelope or several duplicate banks.

Two rules are enforced here and reused by the editing adapters:

* an image is valid only when every byte of the image sums to ``0`` modulo 256;
* rebalancing a modified image rewrites exactly one byte, its last byte.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise

from .errors import (
    CHECKSUM_OVERLAP,
    CROSS_IMAGE_EDIT,
    OVERLAPPING_EDITS,
    STRUCTURE_INVALID,
    DomainError,
)

_SUPPORTED_SIGNATURES = (b"\x55\xaa", b"VN")
_IMAGE_HEADER_MAGIC = {b"\x55\xaa": b"PCIR", b"VN": b"NPDS"}


@dataclass(frozen=True, slots=True)
class RomImage:
    """One bounded image in a PCI/NPDS chain."""

    index: int
    kind: str
    offset: int
    size: int
    checksum: int
    checksum_ok: bool
    is_last: bool
    vendor: int
    device: int
    image_type: int
    header_offset: int
    chain: int

    @property
    def end(self) -> int:
        """Offset of the first byte after this image."""
        return self.offset + self.size

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible image record."""
        return {
            "index": self.index,
            "kind": self.kind,
            "offset": self.offset,
            "size": self.size,
            "checksum": self.checksum,
            "checksum_ok": self.checksum_ok,
            "is_last": self.is_last,
            "vendor": f"{self.vendor:04x}",
            "device": f"{self.device:04x}",
            "image_type": self.image_type,
            "header_offset": self.header_offset,
            "chain": self.chain,
        }


@dataclass(frozen=True, slots=True)
class RomIssue:
    """A structural problem found while walking image signatures."""

    code: str
    message: str
    offset: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible issue record."""
        result: dict[str, object] = {"code": self.code, "message": self.message}
        if self.offset is not None:
            result["offset"] = self.offset
        return result


@dataclass(frozen=True, slots=True)
class RomStructure:
    """Bounded structural report for one ROM blob."""

    images: tuple[RomImage, ...]
    issues: tuple[RomIssue, ...]
    chains: int

    @property
    def balanced(self) -> bool:
        """Whether every parsed image has an additive checksum of zero."""
        return bool(self.images) and all(image.checksum_ok for image in self.images)

    @property
    def valid(self) -> bool:
        """Whether the structure is complete, non-overlapping and balanced."""
        return self.balanced and not self.issues

    def image_at(self, offset: int) -> RomImage | None:
        """Return the image containing ``offset`` or ``None``."""
        return next((image for image in self.images if image.offset <= offset < image.end), None)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible structural report."""
        return {
            "valid": self.valid,
            "balanced": self.balanced,
            "chains": self.chains,
            "images": [image.to_dict() for image in self.images],
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class ByteEdit:
    """One requested byte replacement, tagged with its field key."""

    offset: int
    data: bytes
    field: str = ""


@dataclass(frozen=True, slots=True)
class ChecksumRepair:
    """A last-byte checksum repair performed for one modified image."""

    image_index: int
    image_offset: int
    checksum_offset: int
    before: int
    after: int

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible repair record."""
        return {
            "kind": "additive_checksum",
            "image_index": self.image_index,
            "image_offset": self.image_offset,
            "checksum_offset": self.checksum_offset,
            "before": self.before,
            "after": self.after,
            "method": "last-byte-balance",
        }


@dataclass(frozen=True, slots=True)
class EditOutcome:
    """Verified result of applying byte edits and balancing each touched image."""

    blob: bytes
    modified_images: tuple[int, ...]
    checksum_repairs: tuple[ChecksumRepair, ...]


def _kind(signature: bytes, image_type: int) -> str:
    if signature == b"\x55\xaa":
        return {0: "legacy", 3: "efi"}.get(image_type, f"pci-{image_type:02x}")
    return {0xE0: "npds-data", 0x70: "npds-70"}.get(image_type, f"npds-{image_type:02x}")


def scan_rom(blob: bytes) -> RomStructure:
    """Walk every 512-byte-aligned PCI/NPDS image and verify its 8-bit sum.

    Unknown or truncated structures become issues in the report instead of
    exceptions so the caller can render a read-only structural report.
    """
    data = bytes(blob)
    images: list[RomImage] = []
    issues: list[RomIssue] = []
    stop = max(0, len(data) - 0x1A + 1)
    for start in range(0, stop, 512):
        signature = data[start : start + 2]
        if signature not in _SUPPORTED_SIGNATURES:
            continue
        if start + 0x1A > len(data):
            issues.append(RomIssue("INVALID_IMAGE_HEADER", "image signature at end of file", start))
            continue
        header = start + struct.unpack_from("<H", data, start + 0x18)[0]
        if data[header : header + 4] != _IMAGE_HEADER_MAGIC[signature]:
            continue
        if header < start + 0x1A or header + 0x18 > len(data):
            issues.append(RomIssue("INVALID_IMAGE_HEADER", "image header outside file", start))
            continue
        vendor, device, _, header_size = struct.unpack_from("<HHHH", data, header + 4)
        blocks = struct.unpack_from("<H", data, header + 0x10)[0]
        size = blocks * 512
        end = start + size
        if header_size < 0x18 or not size or end > len(data) or header + header_size > end:
            issues.append(
                RomIssue("TRUNCATED_IMAGE", "image length is invalid or exceeds the file", start)
            )
            continue
        checksum = sum(data[start:end]) & 0xFF
        image_type = data[header + 0x14]
        images.append(
            RomImage(
                index=0,
                kind=_kind(signature, image_type),
                offset=start,
                size=size,
                checksum=checksum,
                checksum_ok=checksum == 0,
                is_last=bool(data[header + 0x15] & 0x80),
                vendor=vendor,
                device=device,
                image_type=image_type,
                header_offset=header,
                chain=0,
            )
        )
    images.sort(key=lambda image: image.offset)
    numbered: list[RomImage] = []
    chain = -1
    previous_end = -1
    for index, image in enumerate(images):
        if image.offset != previous_end:
            chain += 1
        numbered.append(
            RomImage(
                index=index,
                kind=image.kind,
                offset=image.offset,
                size=image.size,
                checksum=image.checksum,
                checksum_ok=image.checksum_ok,
                is_last=image.is_last,
                vendor=image.vendor,
                device=image.device,
                image_type=image.image_type,
                header_offset=image.header_offset,
                chain=chain,
            )
        )
        previous_end = image.end
    for left, right in pairwise(numbered):
        if left.end > right.offset:
            issues.append(
                RomIssue(
                    "OVERLAPPING_IMAGES",
                    f"image {left.index} overlaps image {right.index}",
                    right.offset,
                )
            )
    return RomStructure(tuple(numbered), tuple(issues), chain + 1 if numbered else 0)


def rebalance_image(blob: bytes, image: RomImage) -> bytes:
    """Return ``blob`` with only ``image``'s last byte adjusted to sum to zero."""
    data = bytearray(blob)
    data[image.end - 1] = (data[image.end - 1] - sum(data[image.offset : image.end])) & 0xFF
    return bytes(data)


def _owner(images: tuple[RomImage, ...], start: int, end: int) -> RomImage:
    owners = [image for image in images if image.offset <= start and end <= image.end]
    if len(owners) != 1:
        raise DomainError(
            CROSS_IMAGE_EDIT,
            "an edit must lie inside exactly one image",
            "split the change or refuse it before writing",
            {"start": start, "end": end},
        )
    return owners[0]


def apply_byte_edits(blob: bytes, edits: Iterable[ByteEdit]) -> EditOutcome:
    """Apply bounded edits, then repair each modified image's checksum byte.

    Edits that overlap each other, cross an image boundary or touch a checksum
    byte are refused without producing a partial result. Untouched images are
    returned byte-for-byte unchanged.
    """
    original = bytes(blob)
    structure = scan_rom(original)
    if not structure.images or structure.issues:
        raise DomainError(
            STRUCTURE_INVALID,
            "cannot edit an image chain with structural problems",
            "open the file as a read-only structural report",
            {"issues": [issue.to_dict() for issue in structure.issues]},
        )
    requested = list(edits)
    occupied: list[tuple[int, int]] = []
    touched: dict[int, list[ByteEdit]] = {}
    for edit in requested:
        if not edit.data:
            continue
        start, end = edit.offset, edit.offset + len(edit.data)
        image = _owner(structure.images, start, end)
        if start <= image.end - 1 < end:
            raise DomainError(
                CHECKSUM_OVERLAP,
                f"{edit.field or 'edit'} writes the image checksum byte",
                "the checksum byte is repaired automatically and is never an editable field",
                {"offset": start, "image": image.index},
            )
        for other_start, other_end in occupied:
            if start < other_end and other_start < end:
                raise DomainError(
                    OVERLAPPING_EDITS,
                    "requested changes overlap",
                    "choose one representation for a shared byte range",
                    {"offset": start},
                )
        occupied.append((start, end))
        touched.setdefault(image.index, []).append(edit)
    target = bytearray(original)
    for edit in requested:
        if edit.data:
            target[edit.offset : edit.offset + len(edit.data)] = edit.data
    repairs: list[ChecksumRepair] = []
    for image in structure.images:
        if image.index not in touched:
            continue
        before = sum(target[image.offset : image.end]) & 0xFF
        target[image.end - 1] = (target[image.end - 1] - before) & 0xFF
        repairs.append(ChecksumRepair(image.index, image.offset, image.end - 1, image.checksum, 0))
    result = bytes(target)
    after = scan_rom(result)
    if len(after.images) != len(structure.images) or after.issues:
        raise DomainError(
            STRUCTURE_INVALID,
            "an edit changed the image boundaries",
            "only table bytes inside one existing image may be edited",
        )
    if any(not image.checksum_ok for image in after.images if image.index in touched):
        raise DomainError(CHECKSUM_OVERLAP, "checksum repair failed", "refusing the edited bytes")
    return EditOutcome(result, tuple(sorted(touched)), tuple(repairs))
