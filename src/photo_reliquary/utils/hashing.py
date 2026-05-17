"""Hashing helpers for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_checksum(path: Path, algorithm: str = 'sha256', chunk_size: int = 1024 * 1024) -> str:
    """Calculate a file checksum.

    Parameters:
        path: The file to hash.
        algorithm: Hashlib algorithm name.
        chunk_size: Bytes per read chunk.
    """

    digest = hashlib.new(algorithm)
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_tail(checksum: str, tail_length: int = 5) -> str:
    """Return a human-friendly checksum tail."""

    if tail_length <= 0:
        raise ValueError('tail_length must be greater than zero.')
    return checksum[-tail_length:]
