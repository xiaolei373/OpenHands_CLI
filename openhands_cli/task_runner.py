"""Minimal headless runner.

Drives the OpenHands SDK directly to solve a single task and then exits.
No Textual UI is involved; agent events are streamed to stdout via the SDK's
DefaultConversationVisualizer, which is well suited for container logs.
"""

import uuid

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from openhands.sdk import Message, TextContent
from openhands.sdk.security.confirmation_policy import (
    ConfirmationPolicyBase,
    ConfirmRisky,
    NeverConfirm,
)
from openhands.sdk.security.risk import SecurityRisk
from openhands_cli.setup import setup_conversation
from openhands_cli.shared import extract_conversation_summary


console = Console()


def _select_confirmation_policy(llm_approve: bool) -> ConfirmationPolicyBase:
    """Pick the confirmation policy for headless execution.

    Headless mode never blocks on interactive confirmation, so the default is
    NeverConfirm (auto-approve). With --llm-approve, only LLM-predicted high-risk
    actions are gated (still non-interactive in practice).
    """
    if llm_approve:
        return ConfirmRisky(threshold=SecurityRisk.HIGH)
    return NeverConfirm()


def _print_summary(conversation) -> None:
    """Print a compact end-of-run summary."""
    count, last_agent_message = extract_conversation_summary(conversation.state.events)
    console.print(Rule("CONVERSATION SUMMARY", style="#277dff"))
    console.print(f"Agent messages: {count}", style="#ffffff")
    console.print(Panel(last_agent_message, border_style="#277dff"))


def run_task(
    task: str,
    resume_id: str | None = None,
    *,
    llm_approve: bool = False,
    env_overrides_enabled: bool = False,
) -> uuid.UUID:
    """Run a single task to completion in headless mode.

    Args:
        task: The task text (already resolved from --task/--file).
        resume_id: Optional existing conversation ID to resume.
        llm_approve: Use the LLM-based risk analyzer instead of auto-approve.
        env_overrides_enabled: Allow env vars to override stored LLM settings.

    Returns:
        The conversation UUID.

    Raises:
        MissingAgentSpec: If no agent settings are configured.
    """
    conversation_id = uuid.UUID(resume_id) if resume_id else uuid.uuid4()
    policy = _select_confirmation_policy(llm_approve)

    conversation = setup_conversation(
        conversation_id,
        confirmation_policy=policy,
        # visualizer=DefaultConversationVisualizer,
        visualizer=None,
        env_overrides_enabled=env_overrides_enabled,
        enable_security_analyzer=llm_approve,
    )

    console.print("Agent is working", style="#ffffff")
    conversation.send_message(Message(role="user", content=[TextContent(text=task)]))
    conversation.run()
    console.print("Agent finished", style="#ffe165")

    _print_summary(conversation)
    return conversation_id
