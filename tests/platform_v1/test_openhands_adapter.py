"""Tests for the OpenHands event adapter.

Covers:
- ingest_events with required binding parameters (repository, base_sha,
  head_sha, pr_number, required_workflows)
- ingest_events sets collection_mode="fixture" and provenance="agent_event_stream"
- file_write event extraction
- command_run event extraction
- completion_claim extraction (not trusted)
- conversation.end detection
- unknown event types are ignored
- empty events produce empty evidence
- LifecycleTransport Protocol / FakeTransport / OpenHandsLifecycle wrapper
"""

from __future__ import annotations

from reverse_agent.platform_v1.openhands_adapter import (
    FakeTransport,
    LifecycleTransport,
    OpenHandsLifecycle,
    ingest_events,
    is_conversation_complete,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"


def _ingest(events, execution_id="exec-1", **overrides):
    """Call ingest_events with the required binding parameters."""

    kwargs = {
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "head_sha": VALID_HEAD_SHA,
        "pr_number": 97,
        "required_workflows": ["CI"],
    }
    kwargs.update(overrides)
    return ingest_events(events, execution_id, **kwargs)


# ---------------------------------------------------------------------------
# ingest_events
# ---------------------------------------------------------------------------

class TestIngestEvents:
    def test_empty_events_produce_empty_evidence(self) -> None:
        evidence = _ingest([], "exec-1")
        assert evidence.execution_id == "exec-1"
        assert evidence.changed_paths == ()
        assert evidence.agent_completion_claim == ""
        assert evidence.git_diff_check_passed is False
        assert evidence.ci_checks == ()
        assert evidence.collection_mode == "fixture"
        assert evidence.provenance == "agent_event_stream"
        assert evidence.repository == "dddd2024/reverse-agent"
        assert evidence.base_sha == VALID_BASE_SHA
        assert evidence.head_sha == VALID_HEAD_SHA
        assert evidence.pr_number == 97
        assert evidence.required_workflows == ("CI",)

    def test_file_write_events_extract_paths(self) -> None:
        events = [
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/__init__.py"},
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/cli.py"},
            {"type": "workspace.file_write", "path": "reverse_agent/platform_v1/__init__.py"},  # dup
        ]
        evidence = _ingest(events, "exec-1")
        assert evidence.changed_paths == (
            "reverse_agent/platform_v1/__init__.py",
            "reverse_agent/platform_v1/cli.py",
        )

    def test_command_run_events_extract_results(self) -> None:
        events = [
            {"type": "workspace.command_run", "command": "pytest", "exit_code": 0},
            {"type": "workspace.command_run", "command": "git diff --check", "exit_code": 1},
        ]
        evidence = _ingest(events, "exec-1")
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
        evidence = _ingest(events, "exec-1")
        assert evidence.agent_completion_claim == "final claim"

    def test_completion_claim_empty_when_no_claim_event(self) -> None:
        events = [
            {"type": "workspace.file_write", "path": "a.py"},
            {"type": "workspace.command_run", "command": "ls", "exit_code": 0},
        ]
        evidence = _ingest(events, "exec-1")
        assert evidence.agent_completion_claim == ""

    def test_unknown_event_types_ignored(self) -> None:
        events = [
            {"type": "unknown.event", "path": "should-not-appear.py"},
            {"type": "another.unknown", "claim": "should-not-appear"},
        ]
        evidence = _ingest(events, "exec-1")
        assert evidence.changed_paths == ()
        assert evidence.agent_completion_claim == ""

    def test_event_without_type_ignored(self) -> None:
        events = [
            {"path": "no-type.py"},
            {"claim": "no-type-claim"},
        ]
        evidence = _ingest(events, "exec-1")
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
        evidence = _ingest(events, "exec-1")
        assert evidence.changed_paths == ("a.py",)
        assert evidence.agent_completion_claim == "done"
        assert len(evidence.test_results["commands"]) == 1

    def test_evidence_is_never_live(self) -> None:
        # ingest_events always produces fixture evidence — never live-ready.
        evidence = _ingest([], "exec-1")
        assert evidence.is_live is False
        assert evidence.collection_mode == "fixture"

    def test_binding_fields_propagate(self) -> None:
        evidence = ingest_events(
            [],
            "exec-99",
            repository="other/repo",
            base_sha="0" * 40,
            head_sha="1" * 40,
            pr_number=42,
            required_workflows=["CI", "Lint"],
        )
        assert evidence.execution_id == "exec-99"
        assert evidence.repository == "other/repo"
        assert evidence.base_sha == "0" * 40
        assert evidence.head_sha == "1" * 40
        assert evidence.pr_number == 42
        assert evidence.required_workflows == ("CI", "Lint")


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


# ---------------------------------------------------------------------------
# FakeTransport
# ---------------------------------------------------------------------------

class TestFakeTransport:
    def test_start_returns_session_id_and_records_call(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "do the thing")
        assert session_id.startswith("fake-session-")
        assert ("start", ("exec-1", "do the thing")) in transport.calls

    def test_get_status_returns_running_after_start(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "prompt")
        assert transport.get_status(session_id) == "RUNNING"

    def test_get_status_unknown_for_missing_session(self) -> None:
        transport = FakeTransport()
        assert transport.get_status("no-such-session") == "UNKNOWN"

    def test_collect_events_returns_initial_event(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "prompt")
        events = transport.collect_events(session_id)
        assert len(events) >= 1
        assert events[0]["type"] == "conversation.start"

    def test_collect_events_empty_for_missing_session(self) -> None:
        transport = FakeTransport()
        assert transport.collect_events("no-such-session") == ()

    def test_cancel_marks_session_cancelled(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "prompt")
        assert transport.cancel(session_id) is True
        assert transport.get_status(session_id) == "CANCELLED"

    def test_cancel_returns_false_for_missing_session(self) -> None:
        transport = FakeTransport()
        assert transport.cancel("no-such-session") is False

    def test_collect_result_returns_session_state(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "prompt")
        result = transport.collect_result(session_id)
        assert result["session_id"] == session_id
        assert result["status"] == "RUNNING"
        assert result["execution_id"] == "exec-1"

    def test_collect_result_unknown_for_missing_session(self) -> None:
        transport = FakeTransport()
        result = transport.collect_result("no-such-session")
        assert result["status"] == "UNKNOWN"

    def test_complete_session_helper_marks_completed(self) -> None:
        transport = FakeTransport()
        session_id = transport.start("exec-1", "prompt")
        transport.complete_session(session_id)
        assert transport.get_status(session_id) == "COMPLETED"
        events = transport.collect_events(session_id)
        assert any(e["type"] == "conversation.end" for e in events)

    def test_fake_transport_satisfies_lifecycle_protocol(self) -> None:
        # FakeTransport should be usable where LifecycleTransport is expected.
        transport = FakeTransport()
        assert isinstance(transport, LifecycleTransport)


# ---------------------------------------------------------------------------
# OpenHandsLifecycle
# ---------------------------------------------------------------------------

class TestOpenHandsLifecycle:
    def test_is_fake_true_for_fake_transport(self) -> None:
        lifecycle = OpenHandsLifecycle(FakeTransport())
        assert lifecycle.is_fake is True

    def test_is_fake_false_for_non_fake_transport(self) -> None:
        class RealTransport:
            def start(self, execution_id, prompt):
                return "real-session"

            def get_status(self, session_id):
                return "RUNNING"

            def collect_events(self, session_id):
                return ()

            def cancel(self, session_id):
                return True

            def collect_result(self, session_id):
                return {"status": "RUNNING"}

        lifecycle = OpenHandsLifecycle(RealTransport())
        assert lifecycle.is_fake is False

    def test_transport_property_returns_underlying_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        assert lifecycle.transport is transport

    def test_start_delegates_to_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "prompt")
        assert session_id.startswith("fake-session-")
        assert ("start", ("exec-1", "prompt")) in transport.calls

    def test_get_status_delegates_to_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "prompt")
        assert lifecycle.get_status(session_id) == "RUNNING"

    def test_collect_events_delegates_to_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "prompt")
        events = lifecycle.collect_events(session_id)
        assert len(events) >= 1

    def test_cancel_delegates_to_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "prompt")
        assert lifecycle.cancel(session_id) is True
        assert lifecycle.get_status(session_id) == "CANCELLED"

    def test_collect_result_delegates_to_transport(self) -> None:
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "prompt")
        result = lifecycle.collect_result(session_id)
        assert result["session_id"] == session_id
        assert result["execution_id"] == "exec-1"

    def test_full_lifecycle_flow_with_fake_transport(self) -> None:
        # End-to-end flow: start -> collect_events -> complete -> collect_result
        transport = FakeTransport()
        lifecycle = OpenHandsLifecycle(transport)
        session_id = lifecycle.start("exec-1", "do work")
        assert lifecycle.get_status(session_id) == "RUNNING"

        events_before = lifecycle.collect_events(session_id)
        assert any(e["type"] == "conversation.start" for e in events_before)

        transport.complete_session(session_id)
        assert lifecycle.get_status(session_id) == "COMPLETED"

        events_after = lifecycle.collect_events(session_id)
        assert any(e["type"] == "conversation.end" for e in events_after)

        result = lifecycle.collect_result(session_id)
        assert result["status"] == "COMPLETED"
