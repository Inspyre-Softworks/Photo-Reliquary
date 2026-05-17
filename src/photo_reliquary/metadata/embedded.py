"""Embedded metadata support.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from pathlib import Path

from photo_reliquary.exceptions import UnsupportedEmbeddedMetadataError
from photo_reliquary.metadata.base import MetadataHandler
from photo_reliquary.models import IdentityStorageMode, PhotoMetadata


class EmbeddedMetadataHandler(MetadataHandler):
    """Conservative placeholder for future EXIF/XMP support."""

    def read_identity(self, path: Path) -> PhotoMetadata | None:
        """Return None until embedded metadata support is implemented."""

        self.log_device.debug(f'Embedded metadata reads are not yet implemented for {path}.')
        return None

    def write_identity(self, path: Path, metadata: PhotoMetadata) -> IdentityStorageMode:
        """Raise a safe unsupported error so sidecar fallback can be used."""

        raise UnsupportedEmbeddedMetadataError(
            f'Embedded metadata writes are not yet implemented for {path}; using sidecar fallback.'
        )
