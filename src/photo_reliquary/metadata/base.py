"""Metadata abstraction layer.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from photo_reliquary.exceptions import MetadataError
from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.models import IdentityStorageMode, PhotoMetadata


class MetadataHandler(ReliquaryLoggable, ABC):
    """Abstract metadata handler.

    Methods:
        read_identity: Read Photo Reliquary metadata from an image.
        write_identity: Persist Photo Reliquary metadata for an image.
    """

    @abstractmethod
    def read_identity(self, path: Path) -> PhotoMetadata | None:
        """Read identity metadata from *path*."""

    @abstractmethod
    def write_identity(self, path: Path, metadata: PhotoMetadata) -> IdentityStorageMode:
        """Write identity metadata for *path*."""


class MetadataCoordinator(ReliquaryLoggable):
    """Coordinate metadata handlers with ordered read/write fallback."""

    def __init__(self, handlers: Iterable[MetadataHandler], allow_database_only_fallback: bool = True) -> None:
        super().__init__()
        self._handlers = list(handlers)
        self._allow_database_only_fallback = allow_database_only_fallback

    def read_identity(self, path: Path) -> PhotoMetadata | None:
        """Return the first identity payload found for *path*."""

        for handler in self._handlers:
            metadata = handler.read_identity(path)
            if metadata is not None:
                self.log_device.debug(f'Read identity for {path} using {handler.__class__.__name__}.')
                return metadata
        self.log_device.debug(f'No existing metadata identity found for {path}.')
        return None

    def write_identity(self, path: Path, metadata: PhotoMetadata) -> IdentityStorageMode:
        """Write identity metadata using the first successful handler."""

        last_error: MetadataError | None = None
        for handler in self._handlers:
            try:
                mode = handler.write_identity(path, metadata)
                self.log_device.debug(f'Wrote metadata for {path} using {handler.__class__.__name__}.')
                return mode
            except MetadataError as error:
                last_error = error
                self.log_device.warning(f'Metadata write failed for {path}: {error}')
        if self._allow_database_only_fallback:
            self.log_device.warning(f'Falling back to database-only identity storage for {path}.')
            return IdentityStorageMode.DATABASE
        raise MetadataError(f'Unable to persist metadata for {path}.') from last_error
