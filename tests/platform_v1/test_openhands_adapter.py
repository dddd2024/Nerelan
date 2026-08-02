"""Tests for the OpenHands event adapter.

Covers:
- file_write event extraction
- command_run event extraction
- completion_claim extraction (not trusted)
- conversation.end detection
- unknown event types are ignored
- empty events produce empty evidence
"""

from __future__ import annotations

from reverse_agent.platform_v1.openhands_adapter import (
    ingest_events,
    is_conversation_complete,
)


# ---------------------------------------------------------------------------
# ingest_events
# ---------------------------------------------------------------------------

class TestIngestEvents:
    def test_empty_events_produce_empty_evidence(self) -> None:
        evidence = ingest_events([], "exec-1")
        assert evidence.execution_id == "exec-1"
        assert evidence.changed_paths == ()
        assert evidence.agent_completion_claim == ""
        assert evidence.git_diff_check_passed is False
        assert evidence.ci_checks == ()

    def test_file_write_events_extract_paths(self) -> None:
        events = [
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/__init__.py"},
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/cli.py"},
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/__init__.py"},  # dup
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.changed_paths == (
            "reverse_agent/platform_v1/__init__.py",
            "reverse_agent/platform_v1/cli.py",
        )

    def test_command_run_events_extract_results(self) -> None:
        events = [
            {"type": "workspace.command_run", "command": "pytest", "exit_code": 0},
            {"type": "workspace.command_run", "command": "git diff --check", "exit_code": 1},
        ]
        evidence = ingest_events(events, "exec-1")
        commands = evidence.test_results["commands"]
        assert len(commands) == 2
        assert commands[0]["command"] == "pytest"
        assert commands[0]["success"] is True
        assert commands[1]["command"] == "git diff --check"
        assert commands[1]["success"] is False

    def test_completion_claim_extracted_from_last_event(self) -> None:
        events = [
            {"type": "agent.completion_claim", "claim": "first claim"},
            {"type": "agent.completion_claim", "claim": "final claim"},
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.agent_completion_claim == "final claim"

    def test_completion_claim_empty_when_no_claim_event(self) -> None:
        events = [
            {"type": "workspace.file_write", "path": "a.py"},
            {"type": "workspace.command_run", "command": "ls", "exit_code": 0},
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.agent_completion_claim == ""

    def test_unknown_event_types_ignored(self) -> None:
        events = [
            {"type": "unknown.event", "path": "should-not-appear.py"},
            {"type": "another.unknown", "claim": "should-not-appear"},
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.changed_paths == ()
        assert evidence.agent_completion_claim == ""

    def test_event_without_type_ignored(self) -> None:
        events = [
            {"path": "no-type.py"},
            {"claim": "no-type-claim"},
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.changed_paths == ()
        assert evidence.agent_completion_claim == ""

    def test_mixed_events(self) -> None:
        events = [
            {"type": "conversation.start"},
            {"type": "conversation.message", "content": "hello"},
            {"type": "workspace.file_write", "path": "a.py"},
            {"type": "workspace.command_run", "command": "pytest", "exit_code": 0},
            {"type": "agent.completion_claim", "claim": "done"},
            {"type": "conversation.end"},
        ]
        evidence = ingest_events(events, "exec-1")
        assert evidence.changed_paths == ("a.py",)
        assert evidence.agent_completion_claim == "done"
        assert len(evidence.test_results["commands"]) == 1


# ---------------------------------------------------------------------------
# is_conversation_complete
# ---------------------------------------------------------------------------

class TestIsConversationComplete:
    def test_returns_true_when_conversation_end_present(self) -> None:
        events = [
            {"type": "conversation.start"},
            {"type": "conversation.end"},
        ]
        assert is_conversation_complete(events) is True

    def test_returns_false_when_no_conversation_end(self) -> None:
        events = [
            {"type": "conversation.start"},
            {"type": "conversation.message"},
        ]
        assert is_conversation_complete(events) is False

    def test_returns_false_for_empty_events(self) -> None:
        assert is_conversation_complete([]) is False
