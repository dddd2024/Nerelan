"""OpenHands event adapter: ingest events without trusting the agent's claim.

This adapter normalizes OpenHands/Agent Server events into the platform's
internal ``ExecutionEvidence`` representation. It never trusts the agent's
"completion" or "success" claim — all evidence is derived from Git and CI
state, not from agent self-reporting.

The module also provides a minimal, injectable lifecycle interface
(``LifecycleTransport`` / ``OpenHandsLifecycle``) for start, get_status,
collect_events, cancel, and collect_result. Tests use ``FakeTransport``;
real calls are only permitted through an explicit opt-in runner on a
trusted host — never from repository code.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

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
    repository: str,
    base_sha: str,
    head_sha: str,
    pr_number: int,
    required_workflows: Sequence[str] = (),
) -> ExecutionEvidence:
    """Ingest OpenHands events and produce untrusted ExecutionEvidence.

    The evidence is "untrusted" because it comes from the agent's event
    stream. The deterministic accepter (``acceptance.py``) will override
    this with Git-truth and CI-truth before making a final decision.

    The binding fields (``repository``, ``base_sha``, ``head_sha``,
    ``pr_number``, ``required_workflows``) are required so that
    ``validate_binding`` can verify the evidence belongs to the right
    Work Item. ``collection_mode`` is ``"fixture"`` and ``provenance`` is
    ``"agent_event_stream"`` — this evidence can never be live-ready.
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
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        pr_number=pr_number,
        required_workflows=tuple(required_workflows),
        changed_paths=changed_paths,
        test_results=command_results,
        git_diff_check_passed=False,  # must be set by evidence_adapter
        agent_completion_claim=completion_claim,
        ci_checks=(),  # must be set by evidence_adapter
        collected_at="",
        collection_mode="fixture",
        provenance="agent_event_stream",
    )


def is_conversation_complete(events: Sequence[dict[str, Any]]) -> bool:
    """Return True only when a conversation.end event is present."""

    return any(event.get("type") == "conversation.end" for event in events)


# ---------------------------------------------------------------------------
# Minimal injectable lifecycle (start / get_status / collect_events
# / cancel / collect_result)
# ---------------------------------------------------------------------------
#
# Tests use ``FakeTransport``. Real calls to OpenHands Agent Server or Codex
# ACP are only permitted through an explicit opt-in runner on a trusted host.
# Repository code never makes real network calls or touches credentials.

@runtime_checkable
class LifecycleTransport(Protocol):
    """Injectable transport for the OpenHands/ACP minimal lifecycle.

    A real implementation would talk to the OpenHands Agent Server over
    WebSocket or HTTP. Repository code does NOT implement a real transport;
    tests use ``FakeTransport``.
    """

    def start(self, execution_id: str, prompt: str) -> str: ...

    def get_status(self, session_id: str) -> str: ...

    def collect_events(self, session_id: str) -> tuple[dict[str, Any], ...]: ...

    def cancel(self, session_id: str) -> bool: ...

    def collect_result(self, session_id: str) -> dict[str, Any]: ...


class FakeTransport:
    """Provider-free fake transport for tests.

    Records calls and returns canned responses. Never makes network calls
    or touches credentials. ``live`` defaults to ``False`` so that any
    acceptance result derived from this transport cannot be live-ready.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self._sessions: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._results: dict[str, dict[str, Any]] = {}
        self._next_id = 1

    def start(self, execution_id: str, prompt: str) -> str:
        session_id = f"fake-session-{self._next_id}"
        self._next_id += 1
        self.calls.append(("start", (execution_id, prompt)))
        self._sessions[session_id] = {
            "execution_id": execution_id,
            "status": "RUNNING",
        }
        self._events[session_id] = [
            {"type": "conversation.start", "execution_id": execution_id},
        ]
        return session_id

    def get_status(self, session_id: str) -> str:
        self.calls.append(("get_status", (session_id,)))
        session = self._sessions.get(session_id)
        if session is None:
            return "UNKNOWN"
        return str(session.get("status", "UNKNOWN"))

    def collect_events(self, session_id: str) -> tuple[dict[str, Any], ...]:
        self.calls.append(("collect_events", (session_id,)))
        return tuple(self._events.get(session_id, []))

    def cancel(self, session_id: str) -> bool:
        self.calls.append(("cancel", (session_id,)))
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session["status"] = "CANCELLED"
        return True

    def collect_result(self, session_id: str) -> dict[str, Any]:
        self.calls.append(("collect_result", (session_id,)))
        session = self._sessions.get(session_id)
        if session is None:
            return {"status": "UNKNOWN"}
        status = str(session.get("status", "UNKNOWN"))
        return {
            "session_id": session_id,
            "status": status,
            "execution_id": session.get("execution_id", ""),
        }

    # Test-helper methods (not part of the Protocol) ----

    def complete_session(self, session_id: str) -> None:
        """Mark a session as COMPLETED and add a conversation.end event."""
        session = self._sessions.get(session_id)
        if session is not None:
            session["status"] = "COMPLETED"
        events = self._events.setdefault(session_id, [])
        events.append({"type": "conversation.end", "session_id": session_id})


class OpenHandsLifecycle:
    """Thin lifecycle wrapper around an injectable ``LifecycleTransport``.

    This class does NOT implement an agent loop, executor, sandbox, or
    frontend. It delegates every call to the transport so that tests can
    inject ``FakeTransport`` and real deployments can inject a trusted-host
    runner transport.

    ``live`` is ``True`` only when the transport is not a ``FakeTransport``.
    A fake transport can never produce a live merge-ready result.
    """

    def __init__(self, transport: LifecycleTransport) -> None:
        self._transport = transport

    @property
    def transport(self) -> LifecycleTransport:
        return self._transport

    @property
    def is_fake(self) -> bool:
        return isinstance(self._transport, FakeTransport)

    def start(self, execution_id: str, prompt: str) -> str:
        return self._transport.start(execution_id, prompt)

    def get_status(self, session_id: str) -> str:
        return self._transport.get_status(session_id)

    def collect_events(self, session_id: str) -> tuple[dict[str, Any], ...]:
        return self._transport.collect_events(session_id)

    def cancel(self, session_id: str) -> bool:
        return self._transport.cancel(session_id)

    def collect_result(self, session_id: str) -> dict[str, Any]:
        return self._transport.collect_result(session_id)
