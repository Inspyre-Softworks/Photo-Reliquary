"""Structured analyzer models.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AnnotationRegion:
    """Bounding-box style annotation region."""

    x: float
    y: float
    width: float
    height: float


@dataclass(slots=True)
class Annotation:
    """Structured machine annotation."""

    namespace: str
    label: str
    confidence: float | None = None
    value: str | None = None
    region: AnnotationRegion | None = None
    plugin_name: str | None = None
    plugin_version: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    created_at: str | None = None


@dataclass(slots=True)
class AnalysisResult:
    """Result returned by a plugin analysis run."""

    photo_id: str
    plugin_name: str
    plugin_version: str
    annotations: list[Annotation] = field(default_factory=list)
    model_name: str | None = None
    model_version: str | None = None


@dataclass(slots=True)
class AnalysisRun:
    """Metadata for an analyzer execution."""

    plugin_name: str
    plugin_version: str
    target_path: str
    started_at: str
    completed_at: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    run_id: int | None = None
