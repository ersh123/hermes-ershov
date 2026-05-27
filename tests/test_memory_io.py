from __future__ import annotations

from pathlib import Path

import pytest

import hermes_dreaming.memory_io as mio


def test_parse_entries_basic():
    text = "- Entry one.\n- Entry two.\n"
    assert mio._parse_entries(text) == ["- Entry one.", "- Entry two."]


def test_read_counts_memory_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    memory_md = tmp_path / "MEMORY.md"
    memory_md.write_text("- Entry one.\n- Entry two.\n", encoding="utf-8")
    monkeypatch.setattr(mio, "MEMORY_MD", memory_md)
    monkeypatch.setattr(mio, "MEMORY_MD_LIMIT", 123)

    mf = mio.read("memory")

    assert mf.target == "memory"
    assert mf.path == memory_md
    assert mf.char_count == len(memory_md.read_text(encoding="utf-8"))
    assert mf.char_limit == 123
    assert mf.entries == ["- Entry one.", "- Entry two."]


def test_read_prefers_uppercase_live_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lower = tmp_path / "memory.md"
    upper = tmp_path / "MEMORY.md"
    upper.write_text("- Uppercase live file.\n", encoding="utf-8")
    monkeypatch.setattr(mio, "MEMORY_MD", lower)
    monkeypatch.setattr(mio, "MEMORY_MD_LIMIT", 123)

    mf = mio.read("memory")

    assert mf.path == upper
    assert mf.entries == ["- Uppercase live file."]


def test_apply_add_is_idempotent(tmp_path: Path):
    path = tmp_path / "MEMORY.md"
    path.write_text("- Existing entry.\n", encoding="utf-8")

    first = mio.apply_add(path, "- New entry.")
    second = mio.apply_add(path, "- New entry.")

    assert first.ok
    assert second.ok
    assert path.read_text(encoding="utf-8") == "- Existing entry.\n- New entry.\n"


def test_apply_replace_rejects_partial_anchor(tmp_path: Path):
    path = tmp_path / "MEMORY.md"
    path.write_text("- Entry one.\n", encoding="utf-8")

    result = mio.apply_replace(path, "Entry one", "- Entry one updated.")

    assert not result.ok
    assert "exactly match" in result.error


def test_apply_remove_rejects_ambiguous_anchor(tmp_path: Path):
    path = tmp_path / "MEMORY.md"
    path.write_text("- Duplicate.\n- Duplicate.\n", encoding="utf-8")

    result = mio.apply_remove(path, "Duplicate.")

    assert not result.ok
    assert "ambiguous" in result.error


def test_backup_target_always_creates_fresh_backup(tmp_path: Path):
    """backup_target() must overwrite a stale backup, not return it as-is."""
    live = tmp_path / "live"
    live.mkdir()
    memory = live / "memory.md"
    memory.write_text("- Entry one.\n", encoding="utf-8")

    backup_root = tmp_path / "backups"

    # First backup — file is now "- Entry one."
    first = mio.backup_target(memory, backup_root, target="memory")
    assert first.read_text(encoding="utf-8") == "- Entry one.\n"

    # Mutate the live file
    memory.write_text("- Entry one.\n- Entry two.\n", encoding="utf-8")

    # Second backup — must reflect the NEW state, not the old snapshot
    second = mio.backup_target(memory, backup_root, target="memory")
    assert second == first  # same path
    assert second.read_text(encoding="utf-8") == "- Entry one.\n- Entry two.\n"
