from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


PRIMARY_COMMAND = "mnemos"
LEGACY_NIGHTMEM_COMMAND = "nightmem"
LEGACY_COMMAND = "dreaming"
PRODUCT_NAME = "Hermes Mnemos"


def _run_night_memory(args: argparse.Namespace) -> int:
    from hermes_dreaming.cli import main as dreaming_main

    dream_args = list(getattr(args, "dreaming_args", []) or [])
    if dream_args[:1] == ["--"]:
        dream_args = dream_args[1:]
    if not dream_args:
        dream_args = ["--help"]

    try:
        result = dreaming_main(dream_args)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 0 if code in (None, "") else 1

    return int(result or 0)


def _setup_dreaming_cli(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "dreaming_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the Mnemos CLI.",
    )


def register(ctx) -> None:
    for name, help_text in (
        (PRIMARY_COMMAND, "Run the personal Hermes Mnemos engine"),
        (LEGACY_NIGHTMEM_COMMAND, "Run the legacy mnemos compatibility command"),
        (LEGACY_COMMAND, "Run the legacy mnemos compatibility command"),
    ):
        ctx.register_cli_command(
            name=name,
            help=help_text,
            setup_fn=_setup_dreaming_cli,
            handler_fn=_run_night_memory,
            description=(
                f"Expose the standalone {PRODUCT_NAME} CLI inside Hermes. "
                "Use it to create, inspect, validate, apply, or discard staged personal memory artifacts."
            ),
        )

    skill_md = ROOT / "skills" / "hermes-mnemos" / "SKILL.md"
    if skill_md.exists():
        ctx.register_skill("mnemos", skill_md)
        ctx.register_skill(LEGACY_NIGHTMEM_COMMAND, skill_md)
        ctx.register_skill(LEGACY_COMMAND, skill_md)
