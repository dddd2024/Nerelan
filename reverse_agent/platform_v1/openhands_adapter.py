"""OpenHands event adapter: ingest events without trusting the agent's claim.

This adapter normalizes OpenHands/Agent Server events into the platform's
internal ``ExecutionEvidence`` representation. It never trusts the agent's
"completion" or "success" claim — all evidence is derived from Git and CI
state, not from agent self-reporting.
"""

from __future__ import annotations

from typing import Any, Sequence

from .contracts import ExecutionEvidence


# ---------------------------------------------------------------------------
# Event types (from OpenHands Agent Server / WebSocket)
# ---------------------------------------------------------------------------

_EVENT_TYPES = frozenset({
    "conversation.start",
    "conversation.message",
    "conversation.action",
    "conversation.observation",
    "conversation.end",
    "agent.state_change",
    "workspace.file_write",
    "workspace.command_run",
    "agent.completion_claim",  # not trusted
})


def _safe_str(value: Any, default: str = "") -> str:
    return str(value) if isinstance(value, str) and value else default


def _extract_changed_paths(events: Sequence[dict[str, Any]]) -> tuple[str, ...]:
    """Extract file paths from workspace.file_write events."""

    paths: list[str] = []
    for event in events:
        if event.get("type") != "workspace.file_write":
            continue
        path = _safe_str(event.get("path"))
        if path:
            paths.append(path)
    return tuple(dict.fromkeys(paths))


def _extract_completion_claim(events: Sequence[dict[str, Any]]) -> str:
    """Extract the agent's completion claim (not trusted)."""

    for event in reversed(events):
        if event.get("type") == "agent.completion_claim":
            return _safe_str(event.get("claim"))
    return ""


def _extract_command_results(events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Extract command execution results from workspace.command_run events."""

    results: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "workspace.command_run":
            continue
        results.append({
            "command": _safe_str(event.get("command")),
            "exit_code": event.get("exit_code"),
            "success": event.get("exit_code") == 0,
        })
    return {"commands": results}


def ingest_events(
    events: Sequence[dict[str, Any]],
    execution_id: str,
) -> ExecutionEvidence:
    """Ingest OpenHands events and produce untrusted ExecutionEvidence.

    The evidence is "untrusted" because it comes from the agent's event
    stream. The deterministic accepter (``acceptance.py``) will override
    this with Git-truth and CI-truth before making a final decision.
    """

    # Validate event types
    for event in events:
        event_type = event.get("type", "")
        if event_type and event_type not in _EVENT_TYPES:
            # Unknown events are ignored, not trusted
            continue

    changed_paths = _extract_changed_paths(events)
    completion_claim = _extract_completion_claim(events)
    command_results = _extract_command_results(events)

    return ExecutionEvidence(
        execution_id=execution_id,
        changed_paths=changed_paths,
        test_results=command_results,
        git_diff_check_passed=False,  # must be set by evidence_adapter
        agent_completion_claim=completion_claim,
        ci_checks=(),  # must be set by evidence_adapter
        collected_at="",
    )


def is_conversation_complete(events: Sequence[dict[str, Any]]) -> bool:
    """Return True only when a conversation.end event is present."""

    return any(event.get("type") == "conversation.end" for event in events)
