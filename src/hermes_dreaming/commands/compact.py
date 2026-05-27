from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from ..analyze import list_artifacts

TERMINAL_STATUSES = {"applied", "discarded"}


@dataclass(slots=True)
class CompactResult:
    artifact_root: Path
    archive_root: Path
    moved: list[tuple[str, str]]
    kept: list[str]


def handle(*, artifact_root: Path, archive_root: Path) -> CompactResult:
    """Archive terminal artifacts and leave active staged artifacts in place."""

    artifact_root = Path(artifact_root)
    archive_root = Path(archive_root)
    moved: list[tuple[str, str]] = []
    kept: list[str] = []

    for artifact in list_artifacts(artifact_root):
        source_dir = artifact_root / artifact.artifact_id
        if artifact.status not in TERMINAL_STATUSES or not source_dir.exists():
            kept.append(artifact.artifact_id)
            continue

        destination = archive_root / artifact.artifact_id
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(source_dir), str(destination))
        moved.append((artifact.artifact_id, artifact.status))

    return CompactResult(artifact_root=artifact_root, archive_root=archive_root, moved=moved, kept=kept)
