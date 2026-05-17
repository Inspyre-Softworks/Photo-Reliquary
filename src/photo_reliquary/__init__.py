"""Photo Reliquary package.

Taylor B. | Inspyre-Softworks

Description:
    Photo Reliquary preserves stable photo identity, user tags, and machine
    annotations even when image files are renamed or moved outside the app.
"""

from photo_reliquary.config import PhotoReliquaryConfig
from photo_reliquary.identity import PhotoIdentityService, generate_photo_id
from photo_reliquary.logging_utils import init_logging
from photo_reliquary.scanner import PhotoScanner
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore
from photo_reliquary.tags.manager import TagManager

__all__ = [
    'PhotoIdentityService',
    'PhotoReliquaryConfig',
    'PhotoScanner',
    'SQLitePhotoStore',
    'TagManager',
    'generate_photo_id',
    'init_logging',
]

__version__ = '0.1.0'
