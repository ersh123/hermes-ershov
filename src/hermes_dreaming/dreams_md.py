from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

DREAMS_MD_PATH = Path.home() / ".hermes" / "dreaming" / "DREAMS.md"


def _resolve_diary_path(diary_path: Path | None = None) -> Path:
    return Path(diary_path) if diary_path is not None else DREAMS_MD_PATH


def _format_record_value(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return ", ".join(_format_record_value(item) for item in value) if value else "[]"
    return str(value)


def render_dream_entry(record: dict[str, Any]) -> list[str]:
    timestamp = _format_record_value(record.get("timestamp", "unknown time"))
    command = _format_record_value(record.get("command", "unknown"))
    outcome = "success" if record.get("success") else "failure"
    lines = [f"## {timestamp} — {command} ({outcome})", ""]

    summary = record.get("summary")
    if summary:
        lines.append(f"- Summary: {_format_record_value(summary)}")

    artifact_id = record.get("artifact_id")
    if artifact_id:
        lines.append(f"- Artifact: `{_format_record_value(artifact_id)}`")

    artifact_status = record.get("artifact_status")
    if artifact_status:
        lines.append(f"- Artifact status: `{_format_record_value(artifact_status)}`")

    artifact_dir = record.get("artifact_dir")
    if artifact_dir:
        lines.append(f"- Artifact dir: `{_format_record_value(artifact_dir)}`")

    live_root = record.get("live_root")
    if live_root:
        lines.append(f"- Live root: `{_format_record_value(live_root)}`")

    errors = record.get("errors")
    if errors:
        lines.append("- Errors:")
        if isinstance(errors, list):
            for error in errors:
                lines.append(f"  - {_format_record_value(error)}")
        else:
            lines.append(f"  - {_format_record_value(errors)}")

    lines.append("")
    return lines


def render_dreams_md(records: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# DREAMS.md",
        "",
        "Hermes Dreaming run diary, newest entries last.",
        "",
    ]
    if not records:
        lines.extend(["_No runs recorded yet._", ""])
        return "\n".join(lines)

    for record in records:
        lines.extend(render_dream_entry(record))
    return "\n".join(lines).rstrip() + "\n"


def write_dreams_md(records: Sequence[dict[str, Any]], *, diary_path: Path | None = None) -> Path:
    path = _resolve_diary_path(diary_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dreams_md(records), encoding="utf-8")
    return path
