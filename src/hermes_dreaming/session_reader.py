from __future__ import annotations

"""Recent Hermes session reader with a local-first fallback chain.

Strategy:
  1. Try ``hermes_state.SessionDB`` if available.
  2. Fall back to direct SQLite reads from ``~/.hermes/state.db``.
  3. Final fallback: pointer log from ``state.json`` (session IDs only).

The public API returns compact, deterministic digests suitable for prompt
injection into the Hermes Dreaming curation loop.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .state import read as read_state

logger = logging.getLogger(__name__)

_MAX_TURNS_PER_SESSION = 6
_MAX_CHARS_PER_TURN = 400
_MAX_CHARS_PER_SESSION = 1200


@dataclass(slots=True, eq=True)
class SessionDigest:
    session_id: str
    title: str | None
    started_at: float | None
    message_count: int
    source: str
    user_turns: list[str]

    @property
    def date_str(self) -> str:
        if self.started_at is None:
            return "unknown date"
        try:
            dt = datetime.fromtimestamp(self.started_at, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return "unknown date"
        return dt.strftime("%Y-%m-%d %H:%M UTC")

    def label(self) -> str:
        return self.title or f"Session {self.session_id[:8]}"

    def to_prompt_block(self) -> str:
        lines = [f"**{self.label()}** ({self.date_str}, {self.message_count} messages)"]
        for turn in self.user_turns:
            lines.append(f"  > {turn}")
        return "\n".join(lines)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _extract_user_turns(messages: list[dict[str, Any]]) -> list[str]:
    turns: list[str] = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content") or ""
        if isinstance(content, list):
            parts = [
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            content = " ".join(parts)
        content = str(content).strip()
        if not content or len(content) < 10:
            continue
        turns.append(_truncate(content, _MAX_CHARS_PER_TURN))
        if len(turns) >= _MAX_TURNS_PER_SESSION:
            break
    return turns


def _db_path(db_path: Path | None = None) -> Path:
    if db_path is not None:
        return Path(db_path)
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home()) / "state.db"
    except Exception:
        return Path.home() / ".hermes" / "state.db"


def _state_path(state_path: Path | None = None) -> Path:
    if state_path is not None:
        return Path(state_path)
    return Path.home() / ".hermes" / "dreaming" / "state.json"


# ---------------------------------------------------------------------------
# Primary path: hermes_state.SessionDB
# ---------------------------------------------------------------------------

def _read_via_session_db(limit: int) -> list[SessionDigest] | None:
    try:
        from hermes_state import SessionDB  # type: ignore

        db = SessionDB()
        rows = db.list_sessions_rich(limit=limit, order_by_last_active=True)
        digests: list[SessionDigest] = []
        for row in rows:
            sid = row.get("id", "")
            if not sid:
                continue
            messages: list[dict[str, Any]] = []
            try:
                messages = db.get_messages(sid)
            except Exception as exc:  # pragma: no cover - best-effort fallback
                logger.debug("dreaming: get_messages(%s) failed: %s", sid[:8], exc)
            digests.append(
                SessionDigest(
                    session_id=sid,
                    title=row.get("title"),
                    started_at=row.get("started_at"),
                    message_count=int(row.get("message_count", 0) or 0),
                    source=str(row.get("source", "") or "sessiondb"),
                    user_turns=_extract_user_turns(messages),
                )
            )
        return digests
    except Exception as exc:
        logger.debug("dreaming: SessionDB read failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Fallback 1: direct SQLite read
# ---------------------------------------------------------------------------

def _read_via_sqlite(limit: int, *, db_path: Path | None = None) -> list[SessionDigest] | None:
    db_file = _db_path(db_path)
    if not db_file.exists():
        return None
    try:
        with sqlite3.connect(str(db_file)) as conn:
            conn.row_factory = sqlite3.Row
            session_rows = conn.execute(
                """
                SELECT s.id, s.title, s.started_at, s.message_count, s.source
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id, MAX(timestamp) AS last_active
                    FROM messages GROUP BY session_id
                ) m ON m.session_id = s.id
                WHERE s.parent_session_id IS NULL OR EXISTS (
                    SELECT 1 FROM sessions p
                    WHERE p.id = s.parent_session_id AND p.end_reason = 'branched'
                )
                ORDER BY COALESCE(m.last_active, s.started_at) DESC, s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            digests: list[SessionDigest] = []
            for row in session_rows:
                sid = row["id"]
                msg_rows = conn.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp, id",
                    (sid,),
                ).fetchall()
                raw_msgs = [{"role": r["role"], "content": r["content"]} for r in msg_rows]
                digests.append(
                    SessionDigest(
                        session_id=sid,
                        title=row["title"],
                        started_at=row["started_at"],
                        message_count=int(row["message_count"] or 0),
                        source=str(row["source"] or "sqlite"),
                        user_turns=_extract_user_turns(raw_msgs),
                    )
                )
        return digests
    except Exception as exc:
        logger.debug("dreaming: direct SQLite read failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Fallback 2: pointer log from state.json
# ---------------------------------------------------------------------------

def _read_via_pointer_log(limit: int, *, state_path: Path | None = None) -> list[SessionDigest]:
    state = read_state(state_path=_state_path(state_path))
    ids = list(state.get("recent_session_ids", []))[-limit:]
    return [
        SessionDigest(
            session_id=sid,
            title=None,
            started_at=None,
            message_count=0,
            source="pointer-log",
            user_turns=[],
        )
        for sid in reversed(ids)
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_recent(
    limit: int = 14,
    *,
    db_path: Path | None = None,
    state_path: Path | None = None,
) -> list[SessionDigest]:
    """Return up to *limit* recent sessions, most recent first.

    Side-effect: if the primary read path (SessionDB or SQLite) succeeds,
    the returned session IDs are recorded into ``state.json`` as
    ``recent_session_ids`` so the pointer-log fallback stays populated for
    future low-degradation reads."""
    result = _read_via_session_db(limit)
    if result is not None:
        _record_pointer_ids(result, state_path=state_path)
        return result

    result = _read_via_sqlite(limit) if db_path is None else _read_via_sqlite(limit, db_path=db_path)
    if result is not None:
        _record_pointer_ids(result, state_path=state_path)
        return result

    logger.warning("dreaming: all session read paths failed; using pointer log only")
    return _read_via_pointer_log(limit) if state_path is None else _read_via_pointer_log(limit, state_path=state_path)


def _record_pointer_ids(
    digests: list[SessionDigest], *, state_path: Path | None = None
) -> None:
    """Best-effort: populate ``recent_session_ids`` from a successful read."""
    if not digests:
        return
    try:
        from .state import record_session_pointer

        for digest in digests:
            record_session_pointer(digest.session_id, state_path=state_path)
    except Exception:
        pass  # non-essential — pointer log is already the fallback of last resort


def format_for_prompt(sessions: list[SessionDigest]) -> str:
    """Render session digests for inclusion in an orchestration prompt."""
    if not sessions:
        return "No recent sessions found.\n"

    lines = [f"### Recent sessions ({len(sessions)} shown)", ""]
    for session in sessions:
        lines.append(_truncate(session.to_prompt_block(), _MAX_CHARS_PER_SESSION))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def read_recent_session_context(
    limit: int = 14,
    *,
    db_path: Path | None = None,
    state_path: Path | None = None,
) -> str:
    """Return a compact prompt block with recent session context."""
    return format_for_prompt(list_recent(limit=limit, db_path=db_path, state_path=state_path))
