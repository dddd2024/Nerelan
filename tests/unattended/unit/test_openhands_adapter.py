from __future__ import annotations

import shutil
import socket
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import pytest

from reverse_agent.unattended import (
    AmbiguousConversationStart,
    ExecutionHandle,
    OpenHandsAdapter,
    OpenHandsAdapterError,
    conversation_id_for,
    executor_id,
    prepare_bounded_workspace,
    workspace_id,
    workspace_path,
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


def _handle(attempt: int = 1) -> ExecutionHandle:
    identifier = "unattended:dddd2024/reverse-agent:issue:76"
    return ExecutionHandle(
        identifier,
        attempt,
        workspace_id(identifier),
        executor_id(identifier, attempt),
        "2026-07-29T08:00:00+00:00",
    )


def _attempt_workspace(handle: ExecutionHandle | None = None) -> str:
    selected = handle or _handle()
    return (
        PurePosixPath(workspace_path(selected.workflow_id, selected.attempt))
        .relative_to(".var/unattended")
        .as_posix()
    )


def _adapter(transport: FakeTransport, tmp_path: Path) -> OpenHandsAdapter:
    return OpenHandsAdapter(
        transport,
        host_workspace_root=(tmp_path / "host-workspaces").absolute(),
        executor_api_key="synthetic-executor-material",
    )


def _start(
    adapter: OpenHandsAdapter,
    handle: ExecutionHandle | None = None,
    *,
    attempt_workspace: str | None = None,
    max_iterations: int = 20,
) -> ExecutionHandle:
    selected = handle or _handle()
    return adapter.start_task(
        selected,
        instruction="Create only synthetic.txt",
        attempt_workspace=attempt_workspace or _attempt_workspace(selected),
        max_iterations=max_iterations,
    )


def test_conversation_id_is_deterministic_per_execution_handle() -> None:
    assert conversation_id_for(_handle()) == conversation_id_for(_handle())
    assert conversation_id_for(_handle(2)) != conversation_id_for(_handle())


@pytest.mark.parametrize("execution_status", ["running", "finished", "error", "stuck"])
def test_start_task_reconciles_started_conversation_without_create_or_run(
    tmp_path: Path, execution_status: str
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [(200, {"id": expected, "execution_status": execution_status})]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    assert [call[:2] for call in transport.calls] == [
        ("GET", f"/api/conversations/{expected}")
    ]


def test_existing_idle_conversation_is_run_only_after_observation(
    tmp_path: Path,
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"id": expected, "execution_status": "idle"}),
            (200, {"success": True}),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    assert [call[:2] for call in transport.calls] == [
        ("GET", f"/api/conversations/{expected}"),
        ("POST", f"/api/conversations/{expected}/run"),
        ("GET", f"/api/conversations/{expected}"),
    ]


def test_start_task_creates_and_runs_exactly_one_conversation(tmp_path: Path) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (404, {}),
            (201, {"id": expected, "execution_status": "idle"}),
            (200, {"success": True}),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    create = transport.calls[1]
    assert create[:2] == ("POST", "/api/conversations")
    assert create[2]["conversation_id"] == expected  # type: ignore[index]
    assert create[2]["workspace"] == {  # type: ignore[index]
        "kind": "LocalWorkspace",
        "working_dir": "/workspace/attempt",
    }
    assert create[2]["secrets"] == {}  # type: ignore[index]
    assert create[2] == {  # type: ignore[comparison-overlap]
        "agent": {
            "kind": "Agent",
            "llm": {
                "kind": "LLM",
                "usage_id": "unattended-v0",
                "model": "openai/unattended-v0",
                "base_url": "http://litellm-executor:4000/v1",
                "api_key": "synthetic-executor-material",
            },
            "tools": [{"name": "terminal"}, {"name": "file_editor"}],
        },
        "tool_module_qualnames": {
            "terminal": "openhands.tools.terminal.definition",
            "file_editor": "openhands.tools.file_editor.definition",
        },
        "conversation_id": expected,
        "workspace": {
            "kind": "LocalWorkspace",
            "working_dir": "/workspace/attempt",
        },
        "worktree": False,
        "initial_message": {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Execute only this bounded synthetic task inside the "
                        "assigned Attempt Workspace. Do not access secrets, "
                        "external repositories, remote MCP servers, callbacks, "
                        "or paths outside that workspace.\n\n"
                        "Task: Create only synthetic.txt"
                    ),
                }
            ],
            "run": False,
        },
        "max_iterations": 20,
        "stuck_detection": True,
        "secrets": {},
        "secrets_encrypted": False,
        "client_tools": [],
        "agent_definitions": [],
        "plugins": None,
        "hook_config": None,
        "autotitle": False,
    }
    assert [call[:2] for call in transport.calls[2:]] == [
        ("POST", f"/api/conversations/{expected}/run"),
        ("GET", f"/api/conversations/{expected}"),
    ]


def test_create_response_without_status_is_reconciled_before_run(
    tmp_path: Path,
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (404, {}),
            (201, {"id": expected}),
            (200, {"id": expected, "execution_status": "idle"}),
            (200, {}),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()


def test_ambiguous_create_reconciles_and_runs_existing_idle(
    tmp_path: Path,
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (404, {}),
            socket.timeout(),
            (200, {"id": expected, "execution_status": "idle"}),
            (200, {}),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    assert sum(
        call[:2] == ("POST", "/api/conversations") for call in transport.calls
    ) == 1


def test_ambiguous_create_never_blindly_creates_again(tmp_path: Path) -> None:
    transport = FakeTransport([(404, {}), socket.timeout(), (404, {})])
    with pytest.raises(AmbiguousConversationStart):
        _start(_adapter(transport, tmp_path))
    assert sum(
        call[:2] == ("POST", "/api/conversations") for call in transport.calls
    ) == 1


def test_ambiguous_run_reconciles_running_without_retry(tmp_path: Path) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"id": expected, "execution_status": "idle"}),
            socket.timeout(),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    assert sum(call[0] == "POST" for call in transport.calls) == 1


def test_ambiguous_run_retries_once_only_after_observed_idle(tmp_path: Path) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"id": expected, "execution_status": "idle"}),
            socket.timeout(),
            (200, {"id": expected, "execution_status": "idle"}),
            (200, {}),
            (200, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path)) == _handle()
    assert sum(call[0] == "POST" for call in transport.calls) == 2


def test_ambiguous_run_remaining_idle_after_one_retry_is_blocked(
    tmp_path: Path,
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"id": expected, "execution_status": "idle"}),
            socket.timeout(),
            (200, {"id": expected, "execution_status": "idle"}),
            socket.timeout(),
            (200, {"id": expected, "execution_status": "idle"}),
        ]
    )
    with pytest.raises(AmbiguousConversationStart, match="single_retry"):
        _start(_adapter(transport, tmp_path))
    assert sum(call[0] == "POST" for call in transport.calls) == 2


def test_successful_run_that_remains_idle_is_blocked(tmp_path: Path) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"id": expected, "execution_status": "idle"}),
            (200, {}),
            (200, {"id": expected, "execution_status": "idle"}),
        ]
    )
    with pytest.raises(OpenHandsAdapterError, match="run_not_started"):
        _start(_adapter(transport, tmp_path))


@pytest.mark.parametrize(
    ("status", "message"),
    [
        ("paused", "status_unsafe"),
        ("waiting_for_confirmation", "status_unsafe"),
        ("deleting", "status_unsafe"),
        ("cancelled", "status_unsafe"),
        ("mystery", "status_unknown"),
    ],
)
def test_unsafe_or_unknown_existing_status_fails_closed(
    tmp_path: Path, status: str, message: str
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [(200, {"id": expected, "execution_status": status})]
    )
    with pytest.raises(OpenHandsAdapterError, match=message):
        _start(_adapter(transport, tmp_path))


def test_missing_or_mismatched_existing_identity_fails_closed(tmp_path: Path) -> None:
    expected = conversation_id_for(_handle())
    for payload, message in [
        ({"id": expected}, "status_missing"),
        ({"id": "wrong", "execution_status": "running"}, "mismatch"),
    ]:
        with pytest.raises(OpenHandsAdapterError, match=message):
            _start(_adapter(FakeTransport([(200, payload)]), tmp_path))


@pytest.mark.parametrize(
    "field",
    [
        "conversation_request",
        "model",
        "base_url",
        "api_key",
        "tools",
        "remote_mcp",
        "callback_url",
        "workspace",
        "conversation_id",
        "initial_message",
        "worktree",
        "secrets",
        "unknown_security_field",
    ],
)
def test_start_task_rejects_all_request_authority_overrides(
    tmp_path: Path, field: str
) -> None:
    adapter = _adapter(FakeTransport([]), tmp_path)
    kwargs: dict[str, object] = {
        "instruction": "Create only synthetic.txt",
        "attempt_workspace": _attempt_workspace(),
        field: {"caller": "controlled"},
    }
    with pytest.raises(TypeError, match="unexpected keyword"):
        adapter.start_task(_handle(), **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [True, False, -1, 0, 21, "2", 2.0, object()],
)
def test_max_iterations_rejects_bool_negative_string_and_coercion(
    tmp_path: Path, value: object
) -> None:
    with pytest.raises(ValueError, match="max_iterations"):
        _start(_adapter(FakeTransport([]), tmp_path), max_iterations=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [1, 20])
def test_max_iterations_accepts_only_explicit_bounded_integers(
    tmp_path: Path, value: int
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (404, {}),
            (201, {"id": expected, "execution_status": "running"}),
        ]
    )
    assert _start(_adapter(transport, tmp_path), max_iterations=value) == _handle()
    assert transport.calls[1][2]["max_iterations"] == value  # type: ignore[index]


def test_get_status_cancel_and_collect_result_use_v137_endpoints(
    tmp_path: Path,
) -> None:
    expected = conversation_id_for(_handle())
    transport = FakeTransport(
        [
            (200, {"execution_status": "running"}),
            (200, {"success": True}),
            (200, {"execution_status": "finished"}),
            (200, {"response": "agent says done"}),
        ]
    )
    adapter = _adapter(transport, tmp_path)
    assert adapter.get_status(_handle()) == "running"
    adapter.cancel(_handle())
    result = adapter.collect_result(_handle())
    assert result.verdict == "EVIDENCE_ONLY"
    assert result.summary == "agent says done"
    assert [call[:2] for call in transport.calls] == [
        ("GET", f"/api/conversations/{expected}"),
        ("POST", f"/api/conversations/{expected}/interrupt"),
        ("GET", f"/api/conversations/{expected}"),
        ("GET", f"/api/conversations/{expected}/agent_final_response"),
    ]


def test_collect_result_rejects_agent_self_acceptance(tmp_path: Path) -> None:
    transport = FakeTransport(
        [
            (200, {"execution_status": "finished"}),
            (200, {"response": "ACCEPTED"}),
        ]
    )
    result = _adapter(transport, tmp_path).collect_result(_handle())
    assert result.verdict == "EVIDENCE_ONLY"
    assert "platform acceptance" in result.limitations[0]


def test_health_checks_alive_and_health(tmp_path: Path) -> None:
    transport = FakeTransport([(200, {}), (200, {})])
    assert _adapter(transport, tmp_path).health() == {
        "/alive": "PASS",
        "/health": "PASS",
    }


@pytest.mark.parametrize(
    "relative",
    ["", ".", "..", "../escape", "/absolute", "C:\\escape", "a/../../b", "a\x00b"],
)
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


@pytest.mark.parametrize(
    "supplied",
    ["/etc", "C:\\escape", "../escape", "a/../../b", "sibling/1", "a\x00b"],
)
def test_start_task_rejects_untrusted_workspace_paths(
    tmp_path: Path, supplied: str
) -> None:
    with pytest.raises(ValueError):
        _start(
            _adapter(FakeTransport([]), tmp_path),
            attempt_workspace=supplied,
        )


def test_start_task_rejects_attempt_mismatch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="attempt_mismatch"):
        _start(
            _adapter(FakeTransport([]), tmp_path),
            handle=_handle(2),
            attempt_workspace=_attempt_workspace(_handle(1)),
        )


def test_start_task_rejects_symlink_in_attempt_workspace(tmp_path: Path) -> None:
    root = tmp_path / "host-workspaces"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    first = PurePosixPath(_attempt_workspace()).parts[0]
    try:
        (root / first).symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="symlink"):
        _start(
            OpenHandsAdapter(
                FakeTransport([]),
                host_workspace_root=root.absolute(),
                executor_api_key="synthetic-executor-material",
            )
        )


def test_post_validation_symlink_replacement_is_rejected(tmp_path: Path) -> None:
    root = (tmp_path / "host-workspaces").absolute()
    outside = tmp_path / "outside"
    outside.mkdir()
    expected = conversation_id_for(_handle())

    class ReplacingTransport(FakeTransport):
        def request(
            self, method: str, path: str, payload: Mapping[str, Any] | None = None
        ) -> tuple[int, Mapping[str, Any]]:
            response = super().request(method, path, payload)
            if method == "GET" and path.endswith(expected):
                target = root.joinpath(*PurePosixPath(_attempt_workspace()).parts)
                shutil.rmtree(target)
                try:
                    target.symlink_to(outside, target_is_directory=True)
                except OSError:
                    pytest.skip("symlink creation unavailable")
            return response

    with pytest.raises(ValueError, match="symlink"):
        _start(
            OpenHandsAdapter(
                ReplacingTransport([(404, {})]),
                host_workspace_root=root,
                executor_api_key="synthetic-executor-material",
            )
        )


def test_symlink_workspace_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    root = tmp_path / "root"
    try:
        root.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="root_symlink"):
        _start(
            OpenHandsAdapter(
                FakeTransport([]),
                host_workspace_root=root.absolute(),
                executor_api_key="synthetic-executor-material",
            )
        )


def test_nonterminal_result_is_rejected(tmp_path: Path) -> None:
    transport = FakeTransport([(200, {"execution_status": "running"})])
    with pytest.raises(OpenHandsAdapterError, match="not_terminal"):
        _adapter(transport, tmp_path).collect_result(_handle())
