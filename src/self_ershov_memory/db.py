from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .context import AuditContext


def connect_db(context: AuditContext, log):
    if not context.state_db.exists():
        log(f"ERROR: state.db not found at {context.state_db}")
        return None
    conn = sqlite3.connect(str(context.state_db))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_messages(conn, days=1, roles=("user",)):
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    placeholders = ",".join("?" for _role in roles)
    cursor = conn.execute(
        f"""
        SELECT m.content, m.timestamp, m.role, s.title
        FROM messages m
        JOIN sessions s ON m.session_id = s.id
        WHERE s.source='telegram'
          AND m.role IN ({placeholders})
          AND s.started_at > ?
        ORDER BY m.timestamp DESC
    """,
        (*roles, cutoff),
    )
    return [row for row in cursor.fetchall() if row["content"]]


def fetch_user_messages(conn, days=1):
    return fetch_messages(conn, days=days, roles=("user",))
