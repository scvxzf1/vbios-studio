"""Immutable domain models shared by ports, adapters, UI and application.

The field names are frozen by ``docs/requirements.md`` appendix A and are used
directly by the GTK views. Keep them stable; add new optional fields with
defaults rather than renaming existing ones.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

RiskLevel = Literal["T0", "T1", "T2", "T3"]
OverrideState = Literal["override-active", "override-not-active", "no-override", "unknown"]
ApplyAction = Literal["load", "unload", "flash"]


@dataclass(frozen=True, slots=True)
class ImageSnapshot:
    """One image inside a VBIOS chain, as shown in the file information card."""

    index: int
    kind: str
    offset: int
    size: int
    checksum_ok: bool
    is_last: bool


@dataclass(frozen=True, slots=True)
class SectionSnapshot:
    """A navigation section (power, voltage, ...) for the main window."""

    id: str
    title: str
    order: int


@dataclass(frozen=True, slots=True)
class FieldSnapshot:
    """One editable or read-only field presented by the UI."""

    key: str
    label: str
    section: str
    unit: str
    current: str | None
    default: str | None
    minimum: str | None
    maximum: str | None
    risk: RiskLevel
    offset: int | None
    editable: bool
    opt_in: bool
    experimental: bool
    description: str
    depends_on: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class DocumentSnapshot:
    """Read-only snapshot of one opened ROM and its field catalog."""

    path: Path
    display_name: str
    sha256: str
    file_size: int
    architecture: str
    product_name: str | None
    pci_id: str | None
    bios_version: str | None
    images: tuple[ImageSnapshot, ...] = ()
    sections: tuple[SectionSnapshot, ...] = ()
    fields: tuple[FieldSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class FieldChange:
    """One staged change, including its risk level for previews and manifests."""

    key: str
    label: str
    old: str | None
    new: str
    unit: str
    risk: RiskLevel


@dataclass(frozen=True, slots=True)
class FieldError:
    """A validation error attached to a field key."""

    key: str
    code: str
    message: str
    hint: str


@dataclass(frozen=True, slots=True)
class EditPreview:
    """Result of staging one or more changes; the UI only renders this."""

    changed: tuple[FieldChange, ...] = ()
    errors: tuple[FieldError, ...] = ()
    batch_risk: RiskLevel = "T0"
    requires_t3_confirmation: bool = False


@dataclass(frozen=True, slots=True)
class ManifestView:
    """Manifest summary shown before and after saving a new ROM."""

    source_sha256: str
    tool_version: str
    upstream_pin: str
    changes: tuple[FieldChange, ...] = ()
    checksum_repairs: tuple[Mapping[str, Any], ...] = ()
    modified: bool = False


@dataclass(frozen=True, slots=True)
class SaveResult:
    """Result of an explicit save-as operation."""

    path: Path
    sha256: str
    manifest: ManifestView
    payload_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class FieldDiff:
    """Field-level difference between the open ROM and another ROM.

    ``left`` and ``right`` are always provided (``None`` means the field is
    absent on that side). ``changed`` is the single flag the GTK diff table
    renders, so the UI never has to infer it from a status enum.
    """

    key: str
    label: str
    left: str | None
    right: str | None
    risk: RiskLevel
    changed: bool

    @property
    def status(self) -> Literal["same", "different", "left_only", "right_only"]:
        """Backward-compatible derived status for non-GUI consumers."""
        if self.left is None and self.right is not None:
            return "right_only"
        if self.right is None and self.left is not None:
            return "left_only"
        return "different" if self.changed else "same"


@dataclass(frozen=True, slots=True)
class ImageDiff:
    """Image-level difference, carrying the metadata the diff table needs."""

    index: int
    kind: str
    size: int
    checksum_left: str | None
    checksum_right: str | None
    equal: bool

    @property
    def status(self) -> Literal["same", "different", "left_only", "right_only"]:
        """Backward-compatible derived status for non-GUI consumers."""
        if self.checksum_left is None and self.checksum_right is not None:
            return "right_only"
        if self.checksum_right is None and self.checksum_left is not None:
            return "left_only"
        return "same" if self.equal else "different"


@dataclass(frozen=True, slots=True)
class RomDiff:
    """Full field-level and image-level comparison of two ROMs."""

    field_diffs: tuple[FieldDiff, ...] = ()
    image_diffs: tuple[ImageDiff, ...] = ()
    summary: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeviceStatus:
    """Current state of one NVIDIA GPU as reported by the apply adapter."""

    gpu_index: int
    name: str
    pci_id: str
    driver_version: str | None
    override_state: OverrideState
    supports_payload: bool


@dataclass(frozen=True, slots=True)
class ApplyPreview:
    """Dry-run description of a load, unload or flash action."""

    action: ApplyAction
    target: str
    values: Mapping[str, Any]
    bytes_written: int
    restart_required: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ApplyResult:
    """Result of a load, unload or flash action."""

    ok: bool
    state: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)
