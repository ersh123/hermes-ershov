from __future__ import annotations

from pathlib import Path


def _review_files() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    return sorted((repo_root / "reviews").glob("*.md"))


def test_review_docs_do_not_expose_active_stop_verdicts() -> None:
    offenders: list[str] = []
    for path in _review_files():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.startswith("Verdict: STOP"):
                offenders.append(f"{path.relative_to(path.parents[1])}:{line_number}")

    assert offenders == []


def test_historical_stop_reviews_show_current_status() -> None:
    offenders: list[str] = []
    for path in _review_files():
        text = path.read_text(encoding="utf-8")
        if "Historical verdict: STOP" not in text:
            continue
        header = "\n".join(text.splitlines()[:12])
        if "Current status: RESOLVED." not in header or "Resolved by:" not in header:
            offenders.append(str(path.relative_to(path.parents[1])))

    assert offenders == []


def test_final_sanity_uses_current_release_posture() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "reviews" / "final-sanity.md").read_text(encoding="utf-8")

    assert "Ready to ship" not in text
    assert "ship-ready" not in text
    assert "public beta / release-candidate review" in text
    assert "hermes ershov soak --strict-systemd" in text
