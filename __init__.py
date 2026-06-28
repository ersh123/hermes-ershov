from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PRODUCT_COMMAND = "self-ershov-memory"
SELF_MEMORY_COMMAND = "self-memory"
SELF_AUDIT_COMMAND = "self-audit"
PRODUCT_NAME = "Self Ershov Memory"


def _run_self_audit(args: argparse.Namespace) -> int:
    from self_ershov_memory.audit import main as audit_main

    audit_args = list(getattr(args, "audit_args", []) or [])
    if audit_args[:1] == ["--"]:
        audit_args = audit_args[1:]
    if not audit_args:
        audit_args = ["--help"]

    try:
        result = audit_main(audit_args)
    except SystemExit as exc:
        code = exc.code
        code = code if isinstance(code, int) else 0 if code in (None, "") else 1
    else:
        code = int(result or 0)

    if code:
        raise SystemExit(code)
    return code


def _setup_self_audit_cli(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "audit_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the self-ershov-memory CLI.",
    )


def register(ctx) -> None:
    for name, help_text in (
        (PRODUCT_COMMAND, "Run the Self Ershov Memory engine"),
        (SELF_MEMORY_COMMAND, "Run the Self Ershov Memory engine"),
        (SELF_AUDIT_COMMAND, "Run the Self Ershov Memory engine"),
    ):
        ctx.register_cli_command(
            name=name,
            help=help_text,
            setup_fn=_setup_self_audit_cli,
            handler_fn=_run_self_audit,
            description=(
                f"Expose the standalone {PRODUCT_NAME} CLI inside Hermes. "
                "Dialog-driven self-audit engine — analyzes conversations, "
                "extracts corrections, updates USER.md/MEMORY.md."
            ),
        )

    skill_md = ROOT / "skills" / "self-ershov-memory" / "SKILL.md"
    if skill_md.exists():
        ctx.register_skill("self-ershov-memory", skill_md)
        ctx.register_skill("self-memory", skill_md)
        ctx.register_skill("self-audit", skill_md)
