from __future__ import annotations

import sys
import types
from pathlib import Path

from hermes_dreaming.analyze import DreamRunConfig, create_dream_artifact


class _FakeChatCompletions:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **_kwargs):
        message = types.SimpleNamespace(content=self._text)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


class _FakeChat:
    def __init__(self, text: str) -> None:
        self.completions = _FakeChatCompletions(text)


class _FakeOpenAI:
    output_text = ""

    def __init__(self, **_kwargs) -> None:
        self.chat = _FakeChat(self.output_text)


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
        "MEMORY: user: Keep the output short.\n",
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
    assert (result.artifact_dir / "REPORT.md").read_text(encoding="utf-8").startswith("# Hermes Mnemos Report")
    report = (result.artifact_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "Provider/preflight failure" in report
    assert "Payload hash" in report


def test_create_dream_artifact_preflights_secret_sources_before_provider_call(
    monkeypatch, tmp_path: Path
) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
    source_root = tmp_path / "sources"
    source_root.mkdir()
    (source_root / "session.md").write_text(
        "MEMORY: memory: api_key = 'ghp_1234567890abcdef'\n",
        encoding="utf-8",
    )
    artifact_root = tmp_path / "artifacts"
    calls = {"count": 0}

    class CountingCompletions:
        def create(self, **_kwargs):
            calls["count"] += 1
            raise AssertionError("provider should not be called for secret-like source content")

    class CountingChat:
        def __init__(self) -> None:
            self.completions = CountingCompletions()

    class CountingOpenAI:
        def __init__(self, **_kwargs) -> None:
            self.chat = CountingChat()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=CountingOpenAI))

    result = create_dream_artifact(
        DreamRunConfig(
            live_root=live_root,
            artifact_root=artifact_root,
            source_paths=[source_root],
            provider_name="openai-compatible",
        )
    )

    assert calls["count"] == 0
    assert result.artifact.status == "invalid"
    assert result.artifact.sources == []
    assert result.artifact.proposals == []
    assert result.validation_errors
    assert "secret-like content" in result.validation_errors[0]
    report = (result.artifact_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "source preflight blocked provider call" in report
    sources_file = (result.artifact_dir / "sources.jsonl").read_text(encoding="utf-8")
    assert "ghp_" not in sources_file
