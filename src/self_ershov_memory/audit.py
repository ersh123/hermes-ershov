#!/usr/bin/env python3
"""Compatibility facade for the self-ershov-memory CLI.

The implementation is split into focused modules:
- context.py: path/limit configuration
- db.py: SQLite reads
- cleaner.py: dialogue cleanup
- analyzer.py: correction extraction and dedup
- memory_store.py: USER.md/MEMORY.md IO and snapshots
- skills.py: skill sync
- runner.py: pipeline orchestration
"""

from __future__ import annotations

from pathlib import Path

from .analyzer import (
    classify_topic as classify_topic,
    find_corrections as find_corrections,
    format_corrections_entry as format_corrections_entry,
    is_duplicate as is_duplicate,
    normalize_for_dedup as normalize_for_dedup,
    semantic_tokens as semantic_tokens,
)
from .cleaner import clean_content as clean_content
from .cleaner import is_machine_noise_line as is_machine_noise_line
from .context import AuditContext, default_skill_topics
from .checkpoint import (
    SECTION_TITLES as SECTION_TITLES,
    build_checkpoint as build_checkpoint,
    context_fts_db as context_fts_db,
    fetch_session_messages as fetch_session_messages,
    index_context as index_context,
    rebuild_packet as rebuild_packet,
    search_context as search_context,
    session_checkpoint_path as session_checkpoint_path,
    session_notes_path as session_notes_path,
    write_checkpoint as write_checkpoint,
)
from .db import fetch_user_messages as _fetch_user_messages
from .db import connect_db as _connect_db
from .error_bank import (
    ErrorBankEntry as ErrorBankEntry,
    find_error_bank_entries as find_error_bank_entries,
    slugify as slugify,
    write_error_bank_entries as write_error_bank_entries,
)
from .memory_store import (
    compress_corrections_section as compress_corrections_section,
    find_antipatterns_section as find_antipatterns_section,
    find_corrections_section as find_corrections_section,
    parse_existing_corrections as parse_existing_corrections,
    read_memory_sections as read_memory_sections,
    write_sections as write_sections,
)
from .memory_store import snapshot as _snapshot
from .memory_store import validate_memory_files as _validate_memory_files
from .runner import run_pipeline as _run_pipeline
from .skills import sync_skills as _sync_skills

HOME = Path.home()
STATE_DB = HOME / ".hermes" / "state.db"
MEMORIES = HOME / ".hermes" / "memories"
USER_MD = MEMORIES / "USER.md"
MEMORY_MD = MEMORIES / "MEMORY.md"
SNAPSHOT_DIR = MEMORIES / "snapshots"
SKILLS_DIR = HOME / ".hermes" / "skills"
ERROR_BANK_DIR = MEMORIES / "error-bank"
CONTEXT_DIR = HOME / ".hermes" / "context"

USER_LIMIT = 4000
MEMORY_LIMIT = 8000
SKILL_TOPICS = default_skill_topics()


def log(msg):
    print(f"[self-audit] {msg}")


def current_context() -> AuditContext:
    """Build context from legacy module globals so old monkeypatch tests still work."""
    return AuditContext(
        state_db=STATE_DB,
        user_md=USER_MD,
        memory_md=MEMORY_MD,
        snapshot_dir=SNAPSHOT_DIR,
        skills_dir=SKILLS_DIR,
        error_bank_dir=ERROR_BANK_DIR,
        context_dir=CONTEXT_DIR,
        user_limit=USER_LIMIT,
        memory_limit=MEMORY_LIMIT,
        skill_topics=SKILL_TOPICS,
    )


def connect_db(context: AuditContext | None = None):
    return _connect_db(current_context() if context is None else context, log=log)


def fetch_user_messages(conn, days=1):
    return _fetch_user_messages(conn, days=days)


def snapshot(path, context: AuditContext | None = None):
    return _snapshot(
        path, context=current_context() if context is None else context, log=log
    )


def validate_memory_files(context: AuditContext | None = None):
    return _validate_memory_files(current_context() if context is None else context)


def sync_skills(corrections, dry_run=True, context: AuditContext | None = None):
    return _sync_skills(
        corrections,
        context=current_context() if context is None else context,
        dry_run=dry_run,
        log=log,
    )


def run_pipeline(mode="quick", dry_run=True, context: AuditContext | None = None):
    return _run_pipeline(
        current_context() if context is None else context,
        mode=mode,
        dry_run=dry_run,
        log=log,
    )


def main(argv=None):
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    args = set(argv)
    if "--help" in args or "-h" in args:
        print("self-ershov-memory — dialog-driven Hermes memory self-audit")
        print("Usage: self-ershov-memory [--dry-run|--execute] [--quick|--full]")
        print("       self-ershov-memory checkpoint --session <id> [--dry-run]")
        print("       self-ershov-memory rebuild --session <id> [--budget <chars>]")
        print("       self-ershov-memory fts-index")
        print("       self-ershov-memory fts-search <query>")
        print("Default: --dry-run --quick")
        return 0
    if argv and argv[0] in {"checkpoint", "rebuild", "fts-index", "fts-search"}:
        return _main_context_command(argv)
    mode = "full" if "--full" in args else "quick"
    dry_run = "--dry-run" in args or "--execute" not in args
    success = run_pipeline(mode=mode, dry_run=dry_run)
    return 0 if success else 1


def _main_context_command(argv):
    command = argv[0]
    context = current_context()
    if command == "fts-index":
        print(
            f"Indexed {index_context(context)} context docs into {context_fts_db(context)}"
        )
        return 0
    if command == "fts-search":
        query = " ".join(argv[1:]).strip()
        for doc in search_context(context, query):
            print(f"{doc.scope}: {doc.path}")
        return 0
    session_id = _option_value(argv, "--session")
    if not session_id:
        print("ERROR: --session <id> is required")
        return 1
    conn = connect_db(context)
    if conn is None:
        return 1
    try:
        messages = fetch_session_messages(conn, session_id)
    finally:
        conn.close()
    if command == "checkpoint":
        write_checkpoint(
            context, session_id, messages, dry_run="--dry-run" in argv, log=log
        )
        return 0
    budget_raw = _option_value(argv, "--budget")
    budget = int(budget_raw) if budget_raw else 48_000
    print(rebuild_packet(context, session_id, messages, budget=budget))
    return 0


def _option_value(argv, name: str) -> str:
    if name not in argv:
        return ""
    index = argv.index(name)
    if index + 1 >= len(argv):
        return ""
    return argv[index + 1]


if __name__ == "__main__":
    import sys

    sys.exit(main())
