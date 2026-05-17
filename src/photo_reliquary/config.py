"""Configuration models for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from photo_reliquary.constants import (
    DEFAULT_CHECKSUM_ALGORITHM,
    DEFAULT_SIDECAR_SUFFIX,
    DEFAULT_SUPPORTED_SUFFIXES,
)
from photo_reliquary.utils.paths import default_database_path


@dataclass(slots=True)
class PhotoReliquaryConfig:
    """Application configuration.

    Parameters:
        database_path: SQLite database location.
        checksum_algorithm: Hashing algorithm used for reconciliation.
        supported_suffixes: Image file suffixes scanned by the app.
        sidecar_suffix: Sidecar extension used for fallback metadata storage.
        allow_database_only_fallback: Permit DB-only identity persistence when metadata writes fail.
    """

    database_path: Path = field(default_factory=default_database_path)
    checksum_algorithm: str = DEFAULT_CHECKSUM_ALGORITHM
    supported_suffixes: tuple[str, ...] = DEFAULT_SUPPORTED_SUFFIXES
    sidecar_suffix: str = DEFAULT_SIDECAR_SUFFIX
    allow_database_only_fallback: bool = True

    def __post_init__(self) -> None:
        self.database_path = Path(self.database_path).expanduser().resolve(strict=False)
