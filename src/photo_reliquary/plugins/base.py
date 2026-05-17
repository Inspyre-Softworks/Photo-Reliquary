"""Plugin base classes.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from photo_reliquary.analysis.models import AnalysisResult
from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.models import PhotoRecord


class PhotoAnalyzerPlugin(ReliquaryLoggable, ABC):
    """Base class for analyzer plugins.

    Subclasses must define:
        name: Human-readable plugin identifier.
        version: Plugin version string.
        supported_file_types: Lowercase file suffixes with leading dots.
    """

    name: str
    version: str
    supported_file_types: tuple[str, ...]

    @abstractmethod
    def analyze(self, photo_record: PhotoRecord) -> AnalysisResult:
        """Analyze *photo_record* and return structured annotations."""

    def supports(self, path: Path) -> bool:
        """Return whether the plugin supports *path*."""

        return path.suffix.lower() in {suffix.lower() for suffix in self.supported_file_types}
