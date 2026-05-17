"""Path helpers for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from photo_reliquary.constants import DEFAULT_DATA_DIRECTORY_NAME, DEFAULT_DATABASE_FILENAME


def normalize_path(path: Path | str) -> Path:
    """Return a normalized absolute path without requiring the target to exist."""

    return Path(path).expanduser().resolve(strict=False)


def ensure_parent_directory(path: Path) -> None:
    """Ensure the parent directory of *path* exists."""

    path.parent.mkdir(parents=True, exist_ok=True)


def iter_supported_files(root: Path, suffixes: Iterable[str]) -> list[Path]:
    """Return supported files beneath *root* in deterministic order."""

    normalized_suffixes = {suffix.lower() for suffix in suffixes}
    if root.is_file():
        return [root] if root.suffix.lower() in normalized_suffixes else []
    return sorted(
        path
        for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in normalized_suffixes
    )


def default_database_path() -> Path:
    """Return the default SQLite database path.

    Environment:
        PHOTO_RELIQUARY_DB: Overrides the default database location.
    """

    env_override = os.environ.get('PHOTO_RELIQUARY_DB')
    if env_override:
        return normalize_path(env_override)
    return normalize_path(Path.home() / '.local' / 'share' / DEFAULT_DATA_DIRECTORY_NAME / DEFAULT_DATABASE_FILENAME)
