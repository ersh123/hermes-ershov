from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .cleaner import clean_content
from .context import AuditContext
from .memory_store import snapshot


ERROR_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bTS\d{4}\b", "typescript", "typescript"),
    (r"\berror\[E\d{4}\]", "rust", "rust"),
    (
        r"\b(?:ModuleNotFoundError|ImportError|SyntaxError|TypeError|ValueError|AssertionError|KeyError)\b",
        "python",
        "python",
    ),
    (r"\b(?:pytest|mypy|ruff|eslint|tsc)\b", "tooling", "tooling"),
    (r"\b(?:sqlite3\.OperationalError|OperationalError)\b", "sqlite", "sqlite"),
)

FIX_MARKERS = (
    "root cause",
    "причин",
    "исправ",
    "почин",
    "fix:",
    "fixed",
    "решени",
    "решил",
    "learned",
    "prevention",
    "предотвращ",
)


@dataclass(frozen=True)
class ErrorBankEntry:
    code: str
    language: str
    title: str
    content: str

    @property
    def topic_key(self) -> str:
        return f"error_bank/{self.language}/{slugify(self.code)}"

    @property
    def relative_path(self) -> Path:
        return Path(self.language) / f"{slugify(self.code)}.md"


def slugify(text: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Zа-яА-ЯёЁ]+", "-", text.lower()).strip("-")
    return slug or "unknown"


def find_error_bank_entries(messages) -> list[ErrorBankEntry]:
    """Extract compact Error Bank candidates from fixed-error dialogue evidence."""
    entries: list[ErrorBankEntry] = []
    seen: set[str] = set()
    for message in messages:
        if _field(message, "role") != "assistant":
            continue
        text = clean_content(_field(message, "content", ""))
        if (
            "Historical Task Snapshot" in text
            or "Completed Actions" in text
            or text.count("[tool:") >= 3
        ):
            continue
        if len(text) < 30:
            continue
        code, language = _extract_error_code(text)
        if not code or not _looks_like_fixed_error(text, code):
            continue
        key = f"{language}:{code.lower()}"
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            _build_entry(text, code=code, language=language, message=message)
        )
    return entries


def write_error_bank_entries(
    context: AuditContext,
    entries: list[ErrorBankEntry],
    *,
    dry_run: bool,
    log=print,
) -> int:
    """Write Error Bank markdown files with snapshot-backed upsert semantics."""
    if not entries:
        return 0
    written = 0
    assert context.error_bank_dir is not None
    for entry in entries:
        path = context.error_bank_dir / entry.relative_path
        if dry_run:
            log(f"DRY-RUN: would upsert Error Bank {entry.topic_key}")
            written += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8") == entry.content:
            log(f"Error Bank up-to-date: {entry.topic_key}")
            continue
        if path.exists():
            snapshot(path, context=context, log=log)
        path.write_text(entry.content, encoding="utf-8")
        log(f"Error Bank upserted: {entry.topic_key}")
        written += 1
    return written


def _looks_like_fixed_error(text: str, code: str) -> bool:
    for match in re.finditer(re.escape(code), text, re.IGNORECASE):
        start = max(0, match.start() - 260)
        end = min(len(text), match.end() + 260)
        window = text[start:end].lower()
        if any(marker in window for marker in FIX_MARKERS):
            return True
    return False


def _extract_error_code(text: str) -> tuple[str, str]:
    for pattern, language, prefix in ERROR_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            code = match.group(0)
            if prefix == "tooling":
                code = code.lower()
            return code, language
    return "", ""


def _build_entry(text: str, *, code: str, language: str, message) -> ErrorBankEntry:
    title = _title_from_text(text, code)
    excerpt = _compact_excerpt(text)
    session = _field(message, "title") or "unknown session"
    ts = _field(message, "timestamp", 0)
    date = _format_timestamp(ts)
    content = (
        f"# {code}: {title}\n\n"
        f"**Type:** bugfix\n"
        f"**Topic key:** error_bank/{language}/{slugify(code)}\n"
        f"**Language:** {language}\n"
        f"**Source:** {session} @ {date}\n\n"
        "## What\n"
        f"{excerpt}\n\n"
        "## Why\n"
        "Captured from a completed/debugged Hermes dialogue. Keep only if the root cause is actually represented in the source excerpt.\n\n"
        "## Where\n"
        f"Session: {session}\n\n"
        "## Learned\n"
        "Before running the same compiler/test/tool again, search this Error Bank topic and apply the known fix first.\n"
    )
    return ErrorBankEntry(code=code, language=language, title=title, content=content)


def _title_from_text(text: str, code: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if code.lower() in line.lower():
            return _clean_title(line, code)
    return _clean_title(code, code)  # pragma: no cover - defensive fallback


def _clean_title(line: str, code: str) -> str:
    line = re.sub(r"[`*_>#]", "", line)
    line = re.sub(r"\s+", " ", line).strip(" -:|")
    if len(line) > 120:
        line = line[:117].rstrip() + "..."
    return line or code


def _compact_excerpt(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 600:
        return text[:597].rstrip() + "..."
    return text


def _format_timestamp(value) -> str:
    try:
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "unknown time"


def _field(message, name: str, default=None):
    if isinstance(message, dict):
        return message.get(name, default)
    try:
        keys = message.keys()
    except AttributeError:
        return default
    try:
        if name in keys:
            return message[name]
    except (KeyError, TypeError):  # pragma: no cover - defensive sqlite.Row guard
        return default
    return default
