"""Core data models for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class IdentityStorageMode(str, Enum):
    """Supported identity persistence modes."""

    EMBEDDED = 'embedded'
    SIDECAR = 'sidecar'
    DATABASE = 'database'


class ScanIssueType(str, Enum):
    """Structured scan issues detected during reconciliation."""

    DUPLICATE_PHOTO_ID = 'duplicate_photo_id'
    DUPLICATE_CHECKSUM = 'duplicate_checksum'
    METADATA_WRITE_FAILURE = 'metadata_write_failure'
    UNSUPPORTED_FILE = 'unsupported_file'


@dataclass(slots=True)
class PhotoMetadata:
    """Identity data stored in embedded or sidecar metadata."""

    photo_id: str
    checksum: str
    checksum_algorithm: str
    checksum_tail: str
    created_at: str
    updated_at: str
    identity_storage_mode: IdentityStorageMode


@dataclass(slots=True)
class PhotoRecord:
    """A photo tracked by Photo Reliquary."""

    photo_id: str
    current_path: Path
    checksum: str
    checksum_algorithm: str
    checksum_tail: str
    size_bytes: int
    mtime_ns: int
    first_seen_at: str
    last_seen_at: str
    missing_since: str | None
    identity_storage_mode: IdentityStorageMode


@dataclass(slots=True)
class ScanIssue:
    """Structured issue captured during scanning or reconciliation."""

    issue_type: ScanIssueType
    details: dict[str, Any]
    photo_id: str | None = None
    related_photo_id: str | None = None
    checksum: str | None = None
    path: Path | None = None
    created_at: str | None = None


@dataclass(slots=True)
class ScanSummary:
    """Summary of a completed scan."""

    scanned_paths: list[Path] = field(default_factory=list)
    imported_photo_ids: list[str] = field(default_factory=list)
    reconciled_photo_ids: list[str] = field(default_factory=list)
    missing_photo_ids: list[str] = field(default_factory=list)
    issues: list[ScanIssue] = field(default_factory=list)

    @property
    def touched_photo_ids(self) -> list[str]:
        """Return imported and reconciled photo IDs in scan order."""

        return [*self.imported_photo_ids, *self.reconciled_photo_ids]
