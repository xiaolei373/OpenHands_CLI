#!/usr/bin/env python3
"""Entry point for the headless OpenHands CLI.

This build only supports headless task execution:

    openhands --task "Fix the failing test"
    openhands --file task.md
    openhands --resume <conversation-id> --task "continue"
"""

import logging
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from openhands_cli.argparsers.main_parser import create_main_parser
from openhands_cli.setup import MissingAgentSpec
from openhands_cli.stores import (
    MissingEnvironmentVariablesError,
    check_and_warn_env_vars,
)
from openhands_cli.utils import create_seeded_instructions_from_args


console = Console()


env_path = Path.cwd() / ".env"
if env_path.is_file():
    load_dotenv(dotenv_path=str(env_path), override=False)


debug_env = os.getenv("DEBUG", "false").lower()
if debug_env != "1" and debug_env != "true":
    logging.disable(logging.WARNING)
    warnings.filterwarnings("ignore")


def main() -> None:
    """Run a single task in headless mode and exit."""
    parser = create_main_parser()
    args = parser.parse_args()

    seeded_inputs = create_seeded_instructions_from_args(args)
    if not seeded_inputs:
        parser.error("--task or --file is required")

    task = seeded_inputs[0]
    env_overrides_enabled = getattr(args, "override_with_envs", False)

    if not env_overrides_enabled:
        check_and_warn_env_vars()

    try:
        from openhands_cli.headless_runner import run_headless

        conversation_id = run_headless(
            task,
            resume_id=args.resume,
            llm_approve=args.llm_approve,
            env_overrides_enabled=env_overrides_enabled,
        )
        console.print("Goodbye! 👋", style="#ffe165")
        console.print(
            f"Conversation ID: {conversation_id.hex}",
            style="#277dff",
        )
        console.print(
            f"Hint: run openhands --resume {conversation_id} "
            "to resume this conversation.",
            style="#ffffff",
        )
    except KeyboardInterrupt:
        console.print("\nGoodbye! 👋", style="#ffe165")
    except (MissingEnvironmentVariablesError, MissingAgentSpec) as e:
        console.print(f"[#ff6b6b]Error:[/#ff6b6b] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"Error: {str(e)}", style="#ff6b6b", markup=False)
        # Only dump the full traceback in debug mode; otherwise the concise
        # message above is enough and we avoid printing the stack twice.
        if os.getenv("DEBUG", "false").lower() in ("1", "true"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
