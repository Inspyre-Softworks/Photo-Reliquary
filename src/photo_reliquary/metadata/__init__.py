"""Metadata handlers for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from photo_reliquary.metadata.base import MetadataCoordinator, MetadataHandler
from photo_reliquary.metadata.embedded import EmbeddedMetadataHandler
from photo_reliquary.metadata.sidecar import SidecarMetadataHandler

__all__ = [
    'EmbeddedMetadataHandler',
    'MetadataCoordinator',
    'MetadataHandler',
    'SidecarMetadataHandler',
]
