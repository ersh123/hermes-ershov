from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_changelog_provider_list_matches_public_provider_surface() -> None:
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "three built-in providers" not in text

    provider_line = next(line for line in text.splitlines() if "`ershov providers list`" in line)
    for provider in ("offline-marker", "openai-compatible", "deepseek", "openrouter", "ollama"):
        assert provider in provider_line
