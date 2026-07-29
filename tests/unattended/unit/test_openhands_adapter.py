from __future__ import annotations

import socket
from pathlib import Path
from typing import Any, Mapping

import pytest

from reverse_agent.unattended import (
    AmbiguousConversationStart,
    ExecutionHandle,
    OpenHandsAdapter,
    OpenHandsAdapterError,
    TaskSubmission,
    conversation_id_for,
    prepare_bounded_workspace,
)


class FakeTransport:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, Mapping[str, Any] | None]] = []

    def request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> tuple[int, Mapping[str, Any]]:
        self.calls.append((method, path, payload))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


def _handle() -> ExecutionHandle:
    return ExecutionHandle("unattended:dddd2024/reverse-agent:issue:76", 1)


def _submission() -> TaskSubmission:
    return TaskSubmission(_handle(), "Create only synthetic.txt", "/workspace/attempt-1")


def _request() -> dict[str, object]:
    return {
        "agent": {
            "kind": "Agent",
            "llm": {
                "kind": "LLM",
                "usage_id": "gate2",
                "model": "openai/unattended-v0",
                "base_url": "http://litellm:4000/v1",
                "api_key": "litellm-session-key",
            },
            "tools": [],
        },
        "max_iterations": 2,
    }


def test_conversation_id_is_deterministic_per_execution_handle() -> None:
    assert conversation_id_for(_handle()) == conversation_id_for(_handle())
    assert conversation_id_for(ExecutionHandle(_handle().workflow_id, 2)) != (
        conversation_id_for(_handle())
    )


def test_start_task_reconciles_existing_conversation_without_create() -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport([(200, {"id": expected})])
    bound = OpenHandsAdapter(transport).start_task(
        _submission(), conversation_request=_request()
    )
    assert bound.conversation_id == expected
    assert [call[:2] for call in transport.calls] == [
        ("GET", f"/api/conversations/{expected}")
    ]


def test_start_task_creates_and_runs_exactly_one_conversation() -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [(404, {}), (201, {"id": expected}), (200, {"success": True})]
    )
    bound = OpenHandsAdapter(transport).start_task(
        _submission(), conversation_request=_request()
    )
    assert bound.conversation_id == expected
    create = transport.calls[1]
    assert create[:2] == ("POST", "/api/conversations")
    assert create[2]["conversation_id"] == expected  # type: ignore[index]
    assert create[2]["workspace"] == {  # type: ignore[index]
        "kind": "LocalWorkspace",
        "working_dir": "/workspace/attempt-1",
    }
    assert create[2]["secrets"] == {}  # type: ignore[index]
    assert transport.calls[2][:2] == (
        "POST",
        f"/api/conversations/{expected}/run",
    )


def test_ambiguous_create_reconciles_before_any_retry() -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [(404, {}), socket.timeout(), (200, {"id": expected})]
    )
    bound = OpenHandsAdapter(transport).start_task(
        _submission(), conversation_request=_request()
    )
    assert bound.conversation_id == expected
    assert sum(call[0] == "POST" for call in transport.calls) == 1


def test_ambiguous_create_never_blindly_creates_again() -> None:
    transport = FakeTransport([(404, {}), socket.timeout(), (404, {})])
    with pytest.raises(AmbiguousConversationStart):
        OpenHandsAdapter(transport).start_task(
            _submission(), conversation_request=_request()
        )
    assert sum(call[0] == "POST" for call in transport.calls) == 1


@pytest.mark.parametrize("secret_key", ["GITHUB_TOKEN", "github_token", "Authorization"])
def test_github_secret_keys_are_rejected(secret_key: str) -> None:
    request = _request()
    request["secrets"] = {secret_key: "must-not-cross-boundary"}
    with pytest.raises(ValueError, match="github_secret_forbidden"):
        OpenHandsAdapter(FakeTransport([])).start_task(
            _submission(), conversation_request=request
        )


def test_get_status_cancel_and_collect_result_use_v137_endpoints() -> None:
    expected = conversation_id_for(_handle())
    handle = ExecutionHandle(_handle().workflow_id, 1, expected)
    transport = FakeTransport(
        [
            (200, {"execution_status": "running"}),
            (200, {"success": True}),
            (200, {"execution_status": "finished"}),
            (200, {"response": "agent says done"}),
        ]
    )
    adapter = OpenHandsAdapter(transport)
    assert adapter.get_status(handle) == "running"
    adapter.cancel(handle)
    result = adapter.collect_result(handle)
    assert result.accepted is False
    assert result.detail == "agent says done"
    assert [call[:2] for call in transport.calls] == [
        ("GET", f"/api/conversations/{expected}"),
        ("POST", f"/api/conversations/{expected}/interrupt"),
        ("GET", f"/api/conversations/{expected}"),
        ("GET", f"/api/conversations/{expected}/agent_final_response"),
    ]


def test_collect_result_rejects_agent_self_acceptance() -> None:
    expected = conversation_id_for(_handle())
    handle = ExecutionHandle(_handle().workflow_id, 1, expected)
    transport = FakeTransport(
        [
            (200, {"execution_status": "finished"}),
            (200, {"response": "ACCEPTED"}),
        ]
    )
    result = OpenHandsAdapter(transport).collect_result(handle)
    assert result.accepted is False


def test_health_checks_alive_and_health() -> None:
    transport = FakeTransport([(200, {}), (200, {})])
    assert OpenHandsAdapter(transport).health() == {
        "/alive": "PASS",
        "/health": "PASS",
    }


@pytest.mark.parametrize("relative", ["", ".", "..", "../escape", "/absolute", "a/../../b"])
def test_workspace_traversal_fails_closed(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError):
        prepare_bounded_workspace(tmp_path / "root", relative)


def test_workspace_is_created_below_bounded_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    workspace = prepare_bounded_workspace(root, "workflow/1")
    assert workspace.is_dir()
    assert workspace.is_relative_to(root.resolve())


def test_workspace_symlink_escape_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="symlink"):
        prepare_bounded_workspace(root, "link/attempt")


def test_unbound_or_mismatched_handle_rejected() -> None:
    adapter = OpenHandsAdapter(FakeTransport([]))
    with pytest.raises(ValueError, match="not_bound"):
        adapter.get_status(_handle())
    with pytest.raises(ValueError, match="conversation_id_mismatch"):
        adapter.start_task(
            TaskSubmission(
                ExecutionHandle(_handle().workflow_id, 1, "wrong"),
                "synthetic",
                "/workspace",
            ),
            conversation_request=_request(),
        )


def test_nonterminal_result_is_rejected() -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport([(200, {"execution_status": "running"})])
    with pytest.raises(OpenHandsAdapterError, match="not_terminal"):
        OpenHandsAdapter(transport).collect_result(
            ExecutionHandle(_handle().workflow_id, 1, expected)
        )
