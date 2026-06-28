from __future__ import annotations

import sqlite3
from pathlib import Path

from self_ershov_memory import audit


def _context(tmp_path: Path) -> audit.AuditContext:
    return audit.AuditContext(
        state_db=tmp_path / "state.db",
        user_md=tmp_path / "memories" / "USER.md",
        memory_md=tmp_path / "memories" / "MEMORY.md",
        snapshot_dir=tmp_path / "memories" / "snapshots",
        skills_dir=tmp_path / "skills",
        context_dir=tmp_path / "context",
    )


def _messages():
    return [
        {
            "role": "user",
            "content": "запомни: всегда сохраняй /tmp/project/main.py и порт 1933",
            "timestamp": 1,
        },
        {
            "role": "assistant",
            "content": "pytest failed. Решение: берём MiMo rebuild. Root cause: summary loses exact literals. Fix: checkpoint.md.",
            "timestamp": 2,
        },
        {
            "role": "user",
            "content": "[Your active task list was preserved across context compression]\n- [>] stale task",
            "timestamp": 3,
        },
        {
            "role": "user",
            "content": "Historical Task Snapshot\nстарый мусор",
            "timestamp": 4,
        },
        {
            "role": "user",
            "content": "внедри через loop skill, без зоопарка OpenViking https://example.com/docs",
            "timestamp": 5,
        },
    ]


def test_checkpoint_writes_all_mimo_sections_and_preserves_literals(
    tmp_path: Path, capsys
) -> None:
    context = _context(tmp_path)
    content = audit.build_checkpoint("s/1", _messages())

    for title in audit.SECTION_TITLES:
        assert f"## {title}" in content
    assert "внедри через loop skill" in content
    assert "Historical Task Snapshot" not in content
    assert "stale task" not in content
    assert "`/tmp/project/main.py`" in content
    assert "`1933`" in content
    assert "https://example.com/docs" in content
    assert "error_bank" in content

    path = audit.write_checkpoint(context, "s/1", _messages(), dry_run=True)
    assert path == context.context_dir / "sessions" / "s-1" / "checkpoint.md"
    assert not path.exists()
    assert "DRY-RUN" in capsys.readouterr().out

    audit.write_checkpoint(context, "s/1", _messages(), dry_run=False)
    assert "Session checkpoint" in path.read_text(encoding="utf-8")


def test_rebuild_packet_caps_sections_and_reads_context_files(tmp_path: Path) -> None:
    context = _context(tmp_path)
    audit.write_checkpoint(
        context, "sid", _messages(), dry_run=False, log=lambda _msg: None
    )
    notes = audit.session_notes_path(context, "sid")
    notes.write_text("note " * 500, encoding="utf-8")
    project_memory = context.context_dir / "projects" / "p1" / "MEMORY.md"
    project_memory.parent.mkdir(parents=True)
    project_memory.write_text("project memory about MiMo", encoding="utf-8")

    packet = audit.rebuild_packet(context, "sid", _messages(), budget=5_000)

    assert packet.startswith("[CONTROLLED CONTEXT REBUILD]")
    assert packet.rstrip().endswith("[/CONTROLLED CONTEXT REBUILD]")
    assert "## Active intent" in packet
    assert "внедри через loop skill" in packet
    assert "project memory about MiMo" in packet
    assert "...[truncated]" in packet


def test_context_fts_indexes_and_searches_markdown(tmp_path: Path) -> None:
    context = _context(tmp_path)
    (context.context_dir / "sessions" / "sid").mkdir(parents=True)
    (context.context_dir / "sessions" / "sid" / "checkpoint.md").write_text(
        "MiMo checkpoint exact literal", encoding="utf-8"
    )
    (context.context_dir / "global").mkdir(parents=True)
    (context.context_dir / "global" / "MEMORY.md").write_text(
        "OpenViking optional retrieval", encoding="utf-8"
    )

    assert audit.search_context(context, "MiMo") == []
    assert audit.index_context(context) == 2
    assert audit.context_fts_db(context).exists()
    results = audit.search_context(context, "MiMo optional", limit=5)

    assert [doc.scope for doc in results] == ["global", "sessions"]
    assert any("checkpoint exact" in doc.body for doc in results)
    assert audit.search_context(context, "") == []


def test_fetch_session_messages_respects_active_column(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, title TEXT)")
    conn.execute(
        "CREATE TABLE messages (session_id TEXT, role TEXT, content TEXT, timestamp REAL, active INTEGER)"
    )
    conn.execute("INSERT INTO sessions VALUES ('s1', 'title')")
    conn.execute("INSERT INTO messages VALUES ('s1', 'user', 'old', 1, 0)")
    conn.execute("INSERT INTO messages VALUES ('s1', 'user', 'new', 2, 1)")
    conn.commit()

    assert [row["content"] for row in audit.fetch_session_messages(conn, "s1")] == [
        "old",
        "new",
    ]
    assert [
        row["content"]
        for row in audit.fetch_session_messages(conn, "s1", active_only=True)
    ] == ["new"]
    conn.close()


def test_context_cli_commands(tmp_path: Path, monkeypatch, capsys) -> None:
    context = _context(tmp_path)
    conn = sqlite3.connect(context.state_db)
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, title TEXT)")
    conn.execute(
        "CREATE TABLE messages (session_id TEXT, role TEXT, content TEXT, timestamp REAL)"
    )
    conn.execute("INSERT INTO sessions VALUES ('sid', 'title')")
    conn.execute("INSERT INTO messages VALUES ('sid', 'user', 'сделай checkpoint', 1)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(audit, "current_context", lambda: context)
    assert audit.main(["checkpoint", "--session", "sid"]) == 0
    assert audit.session_checkpoint_path(context, "sid").exists()
    assert audit.main(["rebuild", "--session", "sid", "--budget", "1200"]) == 0
    assert "CONTROLLED CONTEXT REBUILD" in capsys.readouterr().out
    assert audit.main(["fts-index"]) == 0
    assert audit.main(["fts-search", "checkpoint"]) == 0
    assert audit.main(["checkpoint"]) == 1
    assert "--session" in capsys.readouterr().out


def test_checkpoint_defensive_empty_and_missing_db_paths(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    context = _context(tmp_path)
    assert "no user intent" in audit.build_checkpoint("empty", [])
    from self_ershov_memory import checkpoint

    assert checkpoint._first_line("") == "(empty)"
    assert "no assistant work yet" in audit.build_checkpoint(
        "user-only", [{"role": "user", "content": "intent"}]
    )
    assert "no user intent" in audit.build_checkpoint("bad", [object()])
    assert audit.rebuild_packet(context, "missing", [], budget=1000).startswith(
        "[CONTROLLED CONTEXT REBUILD]"
    )
    monkeypatch.setattr(audit, "current_context", lambda: context)
    assert audit.main(["rebuild", "--session", "sid"]) == 1
    assert audit.main(["rebuild", "--session"]) == 1
    assert "state.db not found" in capsys.readouterr().out
