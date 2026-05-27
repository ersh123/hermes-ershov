from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Iterable

from .artifact import DreamArtifact, DreamProposal, VALID_MODES, VALID_TARGET_KINDS

SECRET_PATTERNS = [
    re.compile(r"\b(sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{8,}|xox[baprs]-[A-Za-z0-9-]{8,}|AIza[0-9A-Za-z_-]{10,})\b"),
    re.compile(r"\b(api[_-]?key|secret|password|token|bearer)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-/.]{8,}", re.IGNORECASE),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
]


def _secret_like(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _safe_relative_path(path_text: str) -> bool:
    path = PurePosixPath(path_text.replace("\\", "/"))
    if path.is_absolute():
        return False
    return all(part not in {"..", ""} for part in path.parts)


def _proposal_errors(proposal: DreamProposal) -> list[str]:
    errors: list[str] = []
    if proposal.target_kind not in VALID_TARGET_KINDS:
        errors.append(f"proposal {proposal.id} has unsupported target kind {proposal.target_kind!r}")
    if proposal.mode not in VALID_MODES:
        errors.append(f"proposal {proposal.id} has unsupported mode {proposal.mode!r}")
    if not proposal.summary.strip():
        errors.append(f"proposal {proposal.id} is missing a summary")
    if not proposal.provenance:
        errors.append(f"proposal {proposal.id} is missing provenance")
    if not proposal.target_path.strip() or not _safe_relative_path(proposal.target_path):
        errors.append(f"proposal {proposal.id} has an unsafe target path {proposal.target_path!r}")
    if _secret_like(proposal.summary) or _secret_like(proposal.proposed_text):
        errors.append(f"proposal {proposal.id} contains secret-like content")
    if proposal.mode == "jsonl_append":
        try:
            parsed = json.loads(proposal.proposed_text)
        except json.JSONDecodeError:
            errors.append(f"proposal {proposal.id} has malformed JSONL payload")
        else:
            if not isinstance(parsed, dict):
                errors.append(f"proposal {proposal.id} must serialize a JSON object for jsonl_append")
    return errors


def validate_artifact(artifact: DreamArtifact, *, live_root: Path | str) -> list[str]:
    errors: list[str] = []
    live_root = Path(live_root)

    if not artifact.proposals:
        errors.append("artifact contains no proposals")

    seen_targets: dict[str, str] = {}
    for source in artifact.sources:
        if _secret_like(source.content):
            errors.append(f"source {source.path} contains secret-like content")

    for proposal in artifact.proposals:
        errors.extend(_proposal_errors(proposal))
        existing = seen_targets.get(proposal.target_path)
        if existing is not None and existing != proposal.proposed_text:
            errors.append(f"conflicting proposals target the same path {proposal.target_path!r}")
        else:
            seen_targets[proposal.target_path] = proposal.proposed_text

    if not live_root.exists():
        errors.append(f"live root does not exist: {live_root}")

    return errors


def validate_memory_op(
    *,
    op: str,
    target: str,
    old_text: str | None,
    new_text: str | None,
    reason: str,
    sources: Iterable[str],
    score: float,
    supersession_confidence: float = 0.0,
) -> list[str]:
    """Validate a live memory mutation before score gating and write attempts."""
    errors: list[str] = []

    if target not in VALID_TARGET_KINDS:
        errors.append(f"unsupported target kind {target!r}")
    if op not in {"add", "replace", "remove"}:
        errors.append(f"unsupported operation {op!r}")
    if not reason.strip():
        errors.append("reason is required")
    sources_list = [str(source) for source in sources]
    if not sources_list or any(not source.strip() for source in sources_list):
        errors.append("sources are required")

    if _secret_like(reason):
        errors.append("reason contains secret-like content")
    if old_text and _secret_like(old_text):
        errors.append("old_text contains secret-like content")
    if new_text and _secret_like(new_text):
        errors.append("new_text contains secret-like content")

    if op in {"add", "replace"}:
        if new_text is None or not new_text.strip():
            errors.append(f"{op} requires new_text")
        elif not new_text.strip().startswith("-"):
            errors.append(f"{op} new_text must be a bullet entry")
    if op in {"replace", "remove"} and (old_text is None or not old_text.strip()):
        errors.append(f"{op} requires old_text")

    if op == "replace" and supersession_confidence < 0.75:
        errors.append("replace requires supersession confidence >= 0.75")
    if op == "remove" and supersession_confidence < 0.85:
        errors.append("remove requires supersession confidence >= 0.85")

    if score < 0.0 or score > 1.0:
        errors.append(f"score must be between 0.0 and 1.0, got {score!r}")

    return errors
