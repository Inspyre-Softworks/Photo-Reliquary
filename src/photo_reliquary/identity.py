"""Identity creation services for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from photo_reliquary.constants import PHOTO_ID_PREFIX
from photo_reliquary.logging_utils import ReliquaryLoggable


def generate_photo_id() -> str:
    """Generate a stable Photo Reliquary ID."""

    return f'{PHOTO_ID_PREFIX}_{uuid4().hex}'


@dataclass(slots=True)
class PhotoIdentity:
    """A generated photo identity payload."""

    photo_id: str


class PhotoIdentityService(ReliquaryLoggable):
    """Service object for generating Photo Reliquary identifiers."""

    def create_photo_identity(self) -> PhotoIdentity:
        """Generate and log a new photo identity."""

        photo_id = generate_photo_id()
        self.log_device.info(f'Generated Photo Reliquary ID: {photo_id}')
        return PhotoIdentity(photo_id=photo_id)
