"""Logging helpers built on Inspy-Logger.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from inspy_logger import Loggable, Logger, start_logger

ROOT_LOGGER = Logger('PhotoReliquary')


def init_logging() -> None:
    """Initialize Inspy-Logger for user-facing application entry points."""

    start_logger()


class ReliquaryLoggable(Loggable):
    """Project-specific Loggable base with a stable parent logger."""

    def __init__(self, parent_log_device: Logger | None = None, **kwargs) -> None:
        super().__init__(parent_log_device=parent_log_device or ROOT_LOGGER, **kwargs)
