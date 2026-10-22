"""Small generated ROM images for the nvflash guard tests (no vendor bytes)."""

from __future__ import annotations

import struct


def _image(
    signature: bytes,
    magic: bytes,
    image_type: int,
    last: bool,
    *,
    vendor: int = 0x10DE,
    device: int = 0x28B0,
) -> bytes:
    size = 2048
    data = bytearray(b"\xff" * size)
    data[0:2] = signature
    struct.pack_into("<H", data, 0x18, 0x20)
    data[0x20:0x24] = magic
    struct.pack_into("<HHHH", data, 0x24, vendor, device, 0, 0x18)
    struct.pack_into("<H", data, 0x30, 4)
    data[0x34] = image_type
    data[0x35] = 0x80 if last else 0
    data[size - 1] = -sum(data[: size - 1]) & 0xFF
    return bytes(data)


def make_rom(*, balanced: bool = True) -> bytes:
    """Build a two-image legacy + NPDS chain with a 512-byte prefix."""
    chain = _image(b"\x55\xaa", b"PCIR", 0, False) + _image(b"VN", b"NPDS", 0xE0, True)
    data = bytearray(b"\xff" * 512 + chain)
    if not balanced:
        data[512 + 2048 + 100] ^= 0xFF
    return bytes(data)
