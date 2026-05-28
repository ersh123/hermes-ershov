from __future__ import annotations

import sys
import types
from pathlib import Path

from hermes_dreaming.analyze import DreamRunConfig, create_dream_artifact


class _FakeResponses:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **_kwargs):
        return types.SimpleNamespace(output_text=self._text)


class _FakeOpenAI:
    output_text = ""

    def __init__(self, **_kwargs) -> None:
        self.responses = _FakeResponses(self.output_text)


def _install_fake_openai(monkeypatch, text: str) -> None:
    _FakeOpenAI.output_text = text
    fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_module)


def test_create_dream_artifact_writes_failure_artifact_for_invalid_provider_output(
    monkeypatch, tmp_path: Path
) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
    source_root = tmp_path / "sources"
    source_root.mkdir()
    (source_root / "session.md").write_text(
        "DREAM: user: Keep the output short.\n",
        encoding="utf-8",
    )
    artifact_root = tmp_path / "artifacts"

    _install_fake_openai(
        monkeypatch,
        """{
  "report": "Report body",
  "proposals": [
    {
      "id": "invalid",
      "target_kind": "user",
      "target_path": "user.md",
      "mode": "append_text",
      "summary": "Keep the output short.",
      "provenance": ["sources/session.md:1"],
      "proposed_text": "- Keep the output short.",
      "approved": true
    }
  ],
  "notes": []
}""",
    )

    result = create_dream_artifact(
        DreamRunConfig(
            live_root=live_root,
            artifact_root=artifact_root,
            source_paths=[source_root],
            provider_name="openai-compatible",
        )
    )

    assert result.artifact.status == "invalid"
    assert result.validation_errors
    assert "provider output invalid" in result.validation_errors[0].lower()
    assert result.artifact.proposals == []
    assert result.artifact_dir.exists()
    assert (result.artifact_dir / "manifest.json").exists()
    assert (result.artifact_dir / "proposals.jsonl").read_text(encoding="utf-8") == ""
    assert (result.artifact_dir / "REPORT.md").read_text(encoding="utf-8").startswith("# Hermes Dreaming Report")
    report = (result.artifact_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "Provider failure" in report
    assert "Payload hash" in report
