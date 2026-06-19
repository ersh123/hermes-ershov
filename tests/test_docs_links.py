from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
INLINE_MARKDOWN_TARGET_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def _markdown_files() -> list[Path]:
    roots = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "SECURITY.md",
        REPO_ROOT / "CODE_OF_CONDUCT.md",
        REPO_ROOT / "brief.md",
        REPO_ROOT / "after-install.md",
    ]
    roots.extend(sorted((REPO_ROOT / "docs").glob("*.md")))
    roots.extend(sorted((REPO_ROOT / "examples").glob("**/*.md")))
    roots.extend(sorted((REPO_ROOT / "research").glob("*.md")))
    roots.extend(sorted((REPO_ROOT / "reviews").glob("*.md")))
    roots.extend(sorted((REPO_ROOT / "specs").glob("*.md")))
    return [path for path in roots if path.exists()]


def _local_target(path: Path, raw_target: str) -> Path | None:
    parsed = urlparse(raw_target.strip())
    if not raw_target.strip() or parsed.scheme in EXTERNAL_SCHEMES:
        return None
    if parsed.scheme or parsed.netloc:
        return None
    target = unquote(parsed.path)
    if not target:
        return None
    return (path.parent / target).resolve()


def test_local_markdown_links_and_images_point_to_existing_files() -> None:
    missing: list[str] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        for raw_target in INLINE_MARKDOWN_TARGET_RE.findall(text):
            resolved = _local_target(path, raw_target)
            if resolved is None:
                continue
            try:
                resolved.relative_to(REPO_ROOT)
            except ValueError:
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {raw_target} escapes repo")
                continue
            if not resolved.exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {raw_target}")

    assert missing == []
