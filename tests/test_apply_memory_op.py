from __future__ import annotations

from pathlib import Path
import json

import hermes_dreaming.memory_io as mio
import hermes_dreaming.state as state_module
from hermes_dreaming.tools.apply_memory_op import handler


def _params(**overrides):
    params = {
        "op": "add",
        "target": "memory",
        "new_text": "- Keep updates short and concrete.",
        "reason": "test",
        "sources": ["sess-1"],
        "score": 0.91,
        "dry_run": True,
    }
    params.update(overrides)
    return params


def test_handler_dry_run_does_not_mutate(tmp_path: Path):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n", encoding="utf-8")

    result = handler(_params(), live_root=live_root, backup_root=tmp_path / "backups")

    assert result["proposed"] is True
    assert result["applied"] is False
    assert memory.read_text(encoding="utf-8") == "- Existing entry.\n"


def test_handler_live_add_writes_backup_and_applies(tmp_path: Path):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n", encoding="utf-8")
    backup_root = tmp_path / "backups"

    result = handler(_params(dry_run=False), live_root=live_root, backup_root=backup_root)

    assert result["applied"] is True
    assert memory.read_text(encoding="utf-8").endswith("- Keep updates short and concrete.\n")
    backup_file = backup_root / "memory" / "memory.md"
    assert backup_file.exists()
    assert backup_file.read_text(encoding="utf-8") == "- Existing entry.\n"


def test_handler_skips_duplicate_live_add(tmp_path: Path):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n- Keep updates short and concrete.\n", encoding="utf-8")

    result = handler(_params(dry_run=False), live_root=live_root, backup_root=tmp_path / "backups")

    assert result.get("skipped") is True
    assert "idempotent" in result.get("reason", "")
    assert memory.read_text(encoding="utf-8") == "- Existing entry.\n- Keep updates short and concrete.\n"


def test_handler_blocks_low_score(tmp_path: Path):
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("- Existing entry.\n", encoding="utf-8")

    result = handler(_params(score=0.5, dry_run=False), live_root=live_root, backup_root=tmp_path / "backups")

    assert result["applied"] is False
    assert "threshold" in result.get("error", "").lower()


def test_handler_rejects_secret_like_live_text(tmp_path: Path):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n", encoding="utf-8")

    result = handler(
        _params(new_text="- api_key = 'ghp_12...cdef'", dry_run=False),
        live_root=live_root,
        backup_root=tmp_path / "backups",
    )

    assert result["applied"] is False
    assert "secret" in result.get("error", "").lower()
    assert memory.read_text(encoding="utf-8") == "- Existing entry.\n"


def test_handler_live_add_rolls_back_when_verification_fails(tmp_path: Path, monkeypatch):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    original = "- Existing entry.\n"
    memory.write_text(original, encoding="utf-8")
    backup_root = tmp_path / "backups"

    def fake_apply_add(path: Path, new_text: str):
        path.write_text("- corrupted write\n", encoding="utf-8")
        return mio.MutationResult(ok=True, new_text=original + "- Keep updates short and concrete.\n", char_delta=1)

    monkeypatch.setattr(mio, "apply_add", fake_apply_add)

    result = handler(_params(dry_run=False), live_root=live_root, backup_root=backup_root)

    assert result["applied"] is False
    assert "verification" in result.get("error", "").lower()
    assert memory.read_text(encoding="utf-8") == original
    backup_file = backup_root / "memory" / "memory.md"
    assert backup_file.exists()
    assert backup_file.read_text(encoding="utf-8") == original


def test_handler_live_success_updates_state(tmp_path: Path, monkeypatch):
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n", encoding="utf-8")
    backup_root = tmp_path / "backups"

    state_path = tmp_path / "state.json"
    ledger_path = tmp_path / "runs.jsonl"
    diary_path = tmp_path / "DREAMS.md"
    monkeypatch.setattr(state_module, "STATE_JSON", state_path)
    monkeypatch.setattr(state_module, "RUN_LEDGER_JSONL", ledger_path)
    monkeypatch.setattr(state_module, "DREAMS_MD_PATH", diary_path)

    result = handler(_params(dry_run=False), live_root=live_root, backup_root=backup_root)

    assert result["applied"] is True
    assert memory.read_text(encoding="utf-8").endswith("- Keep updates short and concrete.\n")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_run"]["command"] == "apply_memory_op"
    assert state["last_successful_run"]["command"] == "apply_memory_op"
    assert state["run_count"] == 1
    assert state["successful_run_count"] == 1


def test_handler_capacity_gate_blocks_oversized_live_write(tmp_path: Path, monkeypatch):
    """Live writes that would exceed the char limit must be rejected."""
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("- Existing entry.\n", encoding="utf-8")

    # Temporarily shrink the limit so even a small add trips the gate.
    monkeypatch.setattr(mio, "MEMORY_MD_LIMIT", 30)

    result = handler(_params(dry_run=False), live_root=live_root, backup_root=tmp_path / "backups")

    assert result["applied"] is False
    assert "capacity gate" in result.get("error", "")
    # Live file must be untouched.
    assert memory.read_text(encoding="utf-8") == "- Existing entry.\n"
