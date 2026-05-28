from __future__ import annotations

from pathlib import Path

from ..analyze import DreamReportCard, build_report_card
from ..artifact import load_artifact


def handle(artifact_dir: Path) -> DreamReportCard:
    artifact = load_artifact(Path(artifact_dir))
    return build_report_card(artifact)
