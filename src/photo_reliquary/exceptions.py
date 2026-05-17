"""Custom exceptions for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

class PhotoReliquaryError(Exception):
    """Base exception for Photo Reliquary failures."""


class ConfigurationError(PhotoReliquaryError):
    """Raised when project configuration is invalid."""


class StorageError(PhotoReliquaryError):
    """Raised when SQLite storage operations fail."""


class MetadataError(PhotoReliquaryError):
    """Raised when metadata cannot be read or written safely."""


class UnsupportedEmbeddedMetadataError(MetadataError):
    """Raised when embedded metadata support is unavailable or unsafe."""


class DuplicatePhotoError(PhotoReliquaryError):
    """Raised when duplicate photo identity data is detected."""


class PluginError(PhotoReliquaryError):
    """Raised when plugin loading or analysis fails."""


class ScanError(PhotoReliquaryError):
    """Raised when a scan cannot complete successfully."""
