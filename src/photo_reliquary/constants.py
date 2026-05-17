"""Project constants for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from pathlib import Path

PHOTO_ID_PREFIX = 'pr'
DEFAULT_CHECKSUM_ALGORITHM = 'sha256'
DEFAULT_SUPPORTED_SUFFIXES = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif', '.webp')
DEFAULT_SIDECAR_SUFFIX = '.reliquary.json'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_DATA_DIRECTORY_NAME = 'photo-reliquary'
DEFAULT_DATABASE_FILENAME = 'photo-reliquary.db'
DEFAULT_ANALYSIS_NAMESPACE = 'reliquary'
PACKAGE_ROOT = Path(__file__).resolve().parent
