from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from .. import state as state_module
from ..artifact import SourceSnapshot, text_sha256
from ..session_reader import SessionDigest, list_recent

SECRET_PATTERNS = [
    re.compile(r"\b(sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{8,}|xox[baprs]-[A-Za-z0-9-]{8,}|AIza[0-9A-Za-z_-]{10,})\b"),
    re.compile(r"\b(api[_-]?key|secret|password|token|bearer)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-/.]{8,}", re.IGNORECASE),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
]


@dataclass(slots=True)
class HarvestResult:
    output_path: Path | None
    sessions: list[SessionDigest]
    content: str
    redaction_count: int


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def redact_text(text: str) -> tuple[str, int]:
    redactions = 0
    result = text
    for pattern in SECRET_PATTERNS:
        result, count = pattern.subn("[REDACTED]", result)
        redactions += count
    return result, redactions


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def render_harvest_bundle(
    sessions: list[SessionDigest],
    *,
    max_chars_per_session: int = 1200,
    max_chars: int = 8000,
) -> tuple[str, int]:
    lines = [
        "# Hermes Ershov recent session harvest",
        "",
        "This local source bundle was generated from recent Hermes sessions.",
        "It is bounded and redacted before providers see it.",
        "",
    ]
    redactions = 0
    if not sessions:
        lines.append("No recent sessions found.")
    for index, session in enumerate(sessions, start=1):
        block_lines = [
            f"## Session {index}: {session.label()}",
            "",
            f"- Session id: `{session.session_id}`",
            f"- Date: `{session.date_str}`",
            f"- Source: `{session.source}`",
            f"- Messages: `{session.message_count}`",
            "",
        ]
        context_lines = session.context_lines if session.context_lines is not None else session.user_turns
        if context_lines:
            block_lines.append("### Dialogue digest" if session.context_lines is not None else "### User turns")
            block_lines.append("")
            for turn in context_lines:
                safe, count = redact_text(turn)
                redactions += count
                block_lines.append(f"- {_clip(safe, 500)}")
        else:
            block_lines.append("- No user turns available from this fallback path.")
        block = _clip("\n".join(block_lines).rstrip(), max_chars_per_session)
        lines.extend([block, ""])
        current = "\n".join(lines)
        if len(current) >= max_chars:
            lines.append("[TRUNCATED: harvest bundle reached configured max_chars]")
            break
    content = _clip("\n".join(lines).rstrip() + "\n", max_chars)
    return content, redactions


def build_recent_source_snapshot(
    *,
    recent: int,
    db_path: Path | None = None,
    state_path: Path | None = None,
    max_chars: int = 8000,
    include_assistant: bool = False,
) -> tuple[SourceSnapshot, list[SessionDigest], int]:
    sessions = list_recent(limit=recent, db_path=db_path, state_path=state_path, include_assistant=include_assistant)
    content, redactions = render_harvest_bundle(sessions, max_chars=max_chars)
    snapshot = SourceSnapshot(
        path=f"recent-sessions-{recent}.md",
        kind="session",
        content=content,
        sha256=text_sha256(content),
        line_count=content.count("\n") + (0 if content.endswith("\n") else 1),
    )
    return snapshot, sessions, redactions


def build_recent_bundle(
    *,
    recent: int,
    db_path: Path | None = None,
    state_path: Path | None = None,
    max_chars: int = 8000,
    include_assistant: bool = False,
) -> HarvestResult:
    snapshot, sessions, redactions = build_recent_source_snapshot(
        recent=recent,
        db_path=db_path,
        state_path=state_path,
        max_chars=max_chars,
        include_assistant=include_assistant,
    )
    return HarvestResult(output_path=None, sessions=sessions, content=snapshot.content, redaction_count=redactions)


def default_output_path() -> Path:
    return state_module.STATE_ROOT / "harvest" / f"recent-sessions-{_now_slug()}.md"


def harvest_recent(
    *,
    recent: int,
    output_path: Path | None = None,
    db_path: Path | None = None,
    state_path: Path | None = None,
    max_chars: int = 8000,
    include_assistant: bool = False,
) -> HarvestResult:
    snapshot, sessions, redactions = build_recent_source_snapshot(
        recent=recent,
        db_path=db_path,
        state_path=state_path,
        max_chars=max_chars,
        include_assistant=include_assistant,
    )
    path = Path(output_path) if output_path is not None else None
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(snapshot.content, encoding="utf-8")
    return HarvestResult(output_path=path, sessions=sessions, content=snapshot.content, redaction_count=redactions)
