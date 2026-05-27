from __future__ import annotations

from ..analyze import DreamCreationResult, DreamRunConfig, create_dream_artifact


def handle(config: DreamRunConfig) -> DreamCreationResult:
    """Create and validate a staged artifact without applying it."""

    return create_dream_artifact(config)
