"""Lazy command package exports for hermes_dreaming.

Keep this package import-light to avoid circular imports between analyze and
command handlers. Public names are loaded on first access.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "CompactResult",
    "compact",
    "DigestResult",
    "DigestWeeklyRollup",
    "build_digest",
    "render_digest",
    "DEFAULT_SCHEDULE",
    "JOB_NAME",
    "install_cron",
    "report_card",
    "review",
    "DEFAULT_BRANCH",
    "DEFAULT_REMOTE",
    "UpdateResult",
    "update",
    "render_update_result",
]

_ATTRS: dict[str, tuple[str, str]] = {
    "CompactResult": ("compact", "CompactResult"),
    "compact": ("compact", "handle"),
    "DigestResult": ("digest", "DigestResult"),
    "DigestWeeklyRollup": ("digest", "DigestWeeklyRollup"),
    "build_digest": ("digest", "build_digest"),
    "render_digest": ("digest", "render_digest"),
    "DEFAULT_SCHEDULE": ("install_cron", "DEFAULT_SCHEDULE"),
    "JOB_NAME": ("install_cron", "JOB_NAME"),
    "install_cron": ("install_cron", "handle"),
    "report_card": ("report_card", "handle"),
    "review": ("review", "handle"),
    "DEFAULT_BRANCH": ("update", "DEFAULT_BRANCH"),
    "DEFAULT_REMOTE": ("update", "DEFAULT_REMOTE"),
    "UpdateResult": ("update", "UpdateResult"),
    "update": ("update", "handle"),
    "render_update_result": ("update", "render_update_result"),
}


def __getattr__(name: str) -> Any:
    if name not in _ATTRS:
        raise AttributeError(name)
    module_name, attr_name = _ATTRS[name]
    module = import_module(f".{module_name}", __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
