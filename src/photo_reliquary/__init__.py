"""Photo Reliquary package.

Taylor B. | Inspyre-Softworks

Description:
    Photo Reliquary preserves stable photo identity, user tags, and machine
    annotations even when image files are renamed or moved outside the app.
"""

from inspy_logger import start_logger

from photo_reliquary.config import PhotoReliquaryConfig
from photo_reliquary.identity import PhotoIdentityService, generate_photo_id
from photo_reliquary.scanner import PhotoScanner
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore
from photo_reliquary.tags.manager import TagManager

start_logger()

__all__ = [
    'PhotoIdentityService',
    'PhotoReliquaryConfig',
    'PhotoScanner',
    'SQLitePhotoStore',
    'TagManager',
    'generate_photo_id',
]

__version__ = '0.1.0'
