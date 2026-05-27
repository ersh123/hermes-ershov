from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import dreams_md as dreams_md_module
from .. import state as state_module
from ..analyze import list_artifacts


@dataclass(slots=True)
class StatusSnapshot:
    artifact_root: Path
    artifact_count: int
    artifact_state_counts: dict[str, int]
    last_run: dict[str, Any] | None
    last_successful_run: dict[str, Any] | None
    run_count: int
    successful_run_count: int
    memory_usage: dict[str, int]
    state_path: Path
    ledger_path: Path
    diary_path: Path


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def _format_run(record: dict[str, Any] | None) -> str:
    if not record:
        return "none"
    timestamp = str(record.get("timestamp", "unknown time"))
    command = str(record.get("command", "unknown"))
    outcome = "success" if record.get("success") else "failure"
    parts = [f"{timestamp} — {command} ({outcome})"]

    artifact_id = record.get("artifact_id")
    if artifact_id:
        parts.append(f"artifact={artifact_id}")

    artifact_status = record.get("artifact_status")
    if artifact_status:
        parts.append(f"status={artifact_status}")

    summary = record.get("summary")
    if summary:
        parts.append(str(summary))

    return " | ".join(parts)


def _artifact_state_counts(artifacts: list) -> dict[str, int]:
    counts = Counter(artifact.status for artifact in artifacts)
    return dict(sorted(counts.items()))


def _coerce_int(value: Any, default: int) -> int:
    return value if isinstance(value, int) else default


def build_status_snapshot(
    *,
    artifact_root: Path,
    state_path: Path | None = None,
    ledger_path: Path | None = None,
    diary_path: Path | None = None,
) -> StatusSnapshot:
    artifact_root = Path(artifact_root)
    state_path = Path(state_path) if state_path is not None else state_module.STATE_JSON
    ledger_path = Path(ledger_path) if ledger_path is not None else state_module.RUN_LEDGER_JSONL
    diary_path = Path(diary_path) if diary_path is not None else dreams_md_module.DREAMS_MD_PATH

    state = state_module.read(state_path=state_path)
    runs = state_module.read_run_ledger(ledger_path=ledger_path)
    artifacts = list_artifacts(artifact_root)

    last_run = state.get("last_run") if isinstance(state.get("last_run"), dict) else None
    if last_run is None and runs:
        last_run = runs[-1]

    last_successful_run = state.get("last_successful_run") if isinstance(state.get("last_successful_run"), dict) else None
    if last_successful_run is None:
        for record in reversed(runs):
            if record.get("success"):
                last_successful_run = record
                break

    run_count = _coerce_int(state.get("run_count"), len(runs))
    successful_run_count = _coerce_int(state.get("successful_run_count"), sum(1 for record in runs if record.get("success")))

    return StatusSnapshot(
        artifact_root=artifact_root,
        artifact_count=len(artifacts),
        artifact_state_counts=_artifact_state_counts(artifacts),
        last_run=last_run,
        last_successful_run=last_successful_run,
        run_count=run_count,
        successful_run_count=successful_run_count,
        memory_usage={
            "state": _file_size(state_path),
            "ledger": _file_size(ledger_path),
            "diary": _file_size(diary_path),
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )


def render_status(snapshot: StatusSnapshot) -> str:
    lines = [
        "# Hermes Dreaming status",
        "",
        f"Artifact root: {snapshot.artifact_root}",
        f"Artifacts: {snapshot.artifact_count} total",
    ]
    if snapshot.artifact_state_counts:
        artifact_state = ", ".join(f"{status}={count}" for status, count in snapshot.artifact_state_counts.items())
        lines.append(f"Artifact state: {artifact_state}")
    else:
        lines.append("Artifact state: none")

    lines.extend(
        [
            "",
            f"Run ledger: {snapshot.run_count} run(s), {snapshot.successful_run_count} successful",
            f"Last run: {_format_run(snapshot.last_run)}",
            f"Last successful run: {_format_run(snapshot.last_successful_run)}",
            "",
            "Memory usage:",
            f"- state.json: {snapshot.memory_usage['state']} B",
            f"- runs.jsonl: {snapshot.memory_usage['ledger']} B",
            f"- DREAMS.md: {snapshot.memory_usage['diary']} B",
        ]
    )
    return "\n".join(lines) + "\n"
