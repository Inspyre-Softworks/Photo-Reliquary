"""Sidecar metadata fallback.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

import json
from pathlib import Path

from photo_reliquary.exceptions import MetadataError
from photo_reliquary.metadata.base import MetadataHandler
from photo_reliquary.models import IdentityStorageMode, PhotoMetadata


class SidecarMetadataHandler(MetadataHandler):
    """JSON sidecar metadata handler.

    Example Usage:
        photo.jpg.reliquary.json
    """

    def __init__(self, sidecar_suffix: str = '.reliquary.json') -> None:
        super().__init__()
        self._sidecar_suffix = sidecar_suffix

    def sidecar_path(self, path: Path) -> Path:
        """Return the sidecar path for *path*."""

        return path.with_name(f'{path.name}{self._sidecar_suffix}')

    def read_identity(self, path: Path) -> PhotoMetadata | None:
        """Read JSON sidecar metadata if it exists."""

        sidecar_path = self.sidecar_path(path)
        if not sidecar_path.exists():
            return None
        try:
            payload = json.loads(sidecar_path.read_text(encoding='utf-8'))
        except OSError as error:
            raise MetadataError(f'Unable to read sidecar metadata for {path}: {error}') from error
        except json.JSONDecodeError as error:
            raise MetadataError(f'Invalid JSON in sidecar metadata for {path}: {error}') from error
        return PhotoMetadata(
            photo_id=payload['photo_id'],
            checksum=payload['checksum'],
            checksum_algorithm=payload['checksum_algorithm'],
            checksum_tail=payload['checksum_tail'],
            created_at=payload['created_at'],
            updated_at=payload['updated_at'],
            identity_storage_mode=IdentityStorageMode.SIDECAR,
        )

    def write_identity(self, path: Path, metadata: PhotoMetadata) -> IdentityStorageMode:
        """Write a JSON sidecar file for *path*."""

        sidecar_path = self.sidecar_path(path)
        payload = {
            'photo_id': metadata.photo_id,
            'checksum': metadata.checksum,
            'checksum_algorithm': metadata.checksum_algorithm,
            'checksum_tail': metadata.checksum_tail,
            'created_at': metadata.created_at,
            'updated_at': metadata.updated_at,
        }
        try:
            sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
        except OSError as error:
            raise MetadataError(f'Unable to write sidecar metadata for {path}: {error}') from error
        self.log_device.debug(f'Used sidecar fallback for {path}: {sidecar_path}.')
        return IdentityStorageMode.SIDECAR
