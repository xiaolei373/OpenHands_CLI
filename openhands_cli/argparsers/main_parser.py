"""Main argument parser for the headless OpenHands CLI."""

import argparse

from openhands_cli import __version__
from openhands_cli.argparsers.util import (
    add_confirmation_mode_args,
    add_env_override_args,
)


def create_main_parser() -> argparse.ArgumentParser:
    """Create the headless CLI argument parser.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="OpenHands CLI - headless task runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
                openhands --task "Fix the failing test"
                openhands --file task.md
                openhands --resume <conversation-id> --task "continue"
                openhands --llm-approve --task "Refactor module"
        """,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"OpenHands CLI {__version__}",
        help="Show the version number and exit",
    )

    parser.add_argument(
        "-t",
        "--task",
        type=str,
        help="Task text to run",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to a file whose contents will be used as the task",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Conversation ID to resume",
    )

    # Confirmation mode options (mutually exclusive)
    confirmation_group = parser.add_mutually_exclusive_group()
    add_confirmation_mode_args(confirmation_group)

    # Environment variable override option
    add_env_override_args(parser)

    return parser
