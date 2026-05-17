"""Manual tag management.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore


class TagManager(ReliquaryLoggable):
    """Manage manual tags keyed by photo ID."""

    def __init__(self, store: SQLitePhotoStore) -> None:
        super().__init__()
        self._store = store

    def add_tag(self, photo_reference: str, tag: str) -> None:
        """Add *tag* to a photo."""

        photo = self._store.resolve_photo(photo_reference)
        self._store.add_tag(photo.photo_id, tag)

    def remove_tag(self, photo_reference: str, tag: str) -> None:
        """Remove *tag* from a photo."""

        photo = self._store.resolve_photo(photo_reference)
        self._store.remove_tag(photo.photo_id, tag)

    def list_tags(self, photo_reference: str) -> list[str]:
        """List tags for a photo."""

        photo = self._store.resolve_photo(photo_reference)
        return self._store.list_tags(photo.photo_id)

    def find_photos_by_tag(self, tag: str):
        """Return photo records matching *tag*."""

        return self._store.find_photos_by_tag(tag)
