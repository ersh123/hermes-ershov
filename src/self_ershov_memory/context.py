from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def default_skill_topics() -> dict[str, dict[str, str]]:
    return {
        "vibe-coding": {"skill": "vibe-coding", "label": "Vibe Coding"},
        "opencode": {"skill": "opencode-setup", "label": "OpenCode Setup"},
        "ресерч": {"skill": "deep-research", "label": "Deep Research"},
        "скиллы": {"skill": "skill-quality", "label": "Skill Quality"},
        "deepseek": {"skill": "deepseek-setup", "label": "DeepSeek Setup"},
    }


@dataclass(frozen=True)
class AuditContext:
    state_db: Path
    user_md: Path
    memory_md: Path
    snapshot_dir: Path
    skills_dir: Path
    error_bank_dir: Path | None = None
    context_dir: Path | None = None
    user_limit: int = 4000
    memory_limit: int = 8000
    skill_topics: dict[str, dict[str, str]] = field(
        default_factory=default_skill_topics
    )

    def __post_init__(self) -> None:
        if self.error_bank_dir is None:
            object.__setattr__(
                self,
                "error_bank_dir",
                self.memory_md.parent / "error-bank",
            )
        if self.context_dir is None:
            object.__setattr__(
                self,
                "context_dir",
                self.memory_md.parent.parent / "context",
            )

    @classmethod
    def from_home(cls, home: Path | None = None) -> "AuditContext":
        home = Path.home() if home is None else Path(home)
        memories = home / ".hermes" / "memories"
        return cls(
            state_db=home / ".hermes" / "state.db",
            user_md=memories / "USER.md",
            memory_md=memories / "MEMORY.md",
            error_bank_dir=memories / "error-bank",
            context_dir=home / ".hermes" / "context",
            snapshot_dir=memories / "snapshots",
            skills_dir=home / ".hermes" / "skills",
        )
