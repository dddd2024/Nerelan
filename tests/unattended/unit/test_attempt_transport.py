from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

import pytest

from reverse_agent.unattended.attempt_transport import (
    AttemptJsonTransport,
    AttemptTransportError,
    AttemptTransportStartupUnavailable,
)
from reverse_agent.unattended.contracts import ExecutionHandle
from reverse_agent.unattended.identifiers import executor_id, workspace_id
from reverse_agent.unattended.sandbox import DockerCommandResult, container_name_for

_WORKFLOW = "unattended:dddd2024/reverse-agent:issue:82"
_SECRET = "sk-synthetic-executor-secret"


def _handle() -> ExecutionHandle:
    return ExecutionHandle(
        _WORKFLOW,
        1,
        workspace_id(_WORKFLOW),
        executor_id(_WORKFLOW, 1),
        "2026-07-30T00:00:00+00:00",
    )


class RecordingRunner:
    def __init__(self, result: DockerCommandResult) -> None:
        self.result = result
        self.calls: list[
            tuple[tuple[str, ...], Mapping[str, str] | None, str | None]
        ] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
        input_text: str | None = None,
    ) -> DockerCommandResult:
        self.calls.append((tuple(argv), environment, input_text))
        return self.result


def _runner(
    *, status: int = 200, payload: Mapping[str, object] | None = None
) -> RecordingRunner:
    return RecordingRunner(
        DockerCommandResult(
            0,
            json.dumps({"status": status, "payload": payload or {}}),
            "untrusted docker diagnostics",
        )
    )


def test_fixed_transport_uses_stdin_and_deterministic_container() -> None:
    runner = _runner(status=201, payload={"id": _handle().executor_id})
    transport = AttemptJsonTransport(
        runner, _handle(), sensitive_values=(_SECRET,)
    )

    status, response = transport.request(
        "POST",
        "/api/conversations",
        {"agent": {"llm": {"api_key": _SECRET}}},
    )

    argv, environment, input_text = runner.calls[0]
    assert status == 201
    assert response["id"] == _handle().executor_id
    assert argv[:5] == (
        "docker",
        "container",
        "exec",
        "--interactive",
        container_name_for(_handle()),
    )
    assert "127.0.0.1:8000" in argv[7]
    assert _SECRET not in "\n".join(argv)
    assert environment is None
    assert input_text is not None and _SECRET in input_text


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    (
        ("PATCH", "/api/conversations", {}),
        ("GET", "http://attacker.invalid/", None),
        ("GET", "/api/bash/execute_bash_command", None),
        ("GET", "/api/conversations/not-the-fixed-id", None),
        ("GET", "/alive", {}),
        ("POST", "/api/conversations", None),
    ),
)
def test_method_path_and_payload_matrix_fails_before_docker(
    method: str, path: str, payload: Mapping[str, object] | None
) -> None:
    runner = _runner()
    transport = AttemptJsonTransport(runner, _handle())
    with pytest.raises(ValueError):
        transport.request(method, path, payload)
    assert runner.calls == []


def test_oversized_payload_fails_before_docker() -> None:
    runner = _runner()
    transport = AttemptJsonTransport(runner, _handle())
    with pytest.raises(AttemptTransportError, match="request_too_large"):
        transport.request(
            "POST",
            "/api/conversations",
            {"instruction": "x" * (64 * 1024)},
        )
    assert runner.calls == []


@pytest.mark.parametrize(
    ("result", "message"),
    (
        (DockerCommandResult(125, "raw", "raw"), "transport_failed"),
        (DockerCommandResult(0, "not-json", ""), "response_malformed"),
        (
            DockerCommandResult(
                0,
                json.dumps({"status": 200, "payload": {"echo": _SECRET}}),
                "",
            ),
            "response_sensitive",
        ),
    ),
)
def test_docker_and_response_failures_are_sanitized(
    result: DockerCommandResult, message: str
) -> None:
    runner = RecordingRunner(result)
    transport = AttemptJsonTransport(
        runner, _handle(), sensitive_values=(_SECRET,)
    )
    with pytest.raises(AttemptTransportError, match=message) as captured:
        transport.request("GET", "/alive")
    assert "raw" not in str(captured.value)
    assert _SECRET not in str(captured.value)


@pytest.mark.parametrize(
    ("returncode", "state"),
    ((8, "timeout"), (9, "connection_refused")),
)
def test_startup_transport_states_are_finite_and_retryable(
    returncode: int,
    state: str,
) -> None:
    transport = AttemptJsonTransport(
        RecordingRunner(DockerCommandResult(returncode, "raw", "raw")),
        _handle(),
    )
    with pytest.raises(AttemptTransportStartupUnavailable) as captured:
        transport.request("GET", "/alive")
    assert captured.value.state == state
    assert "raw" not in str(captured.value)
    observation = transport.probe_readiness()
    assert observation.state == state
    assert observation.retryable is True
    assert observation.alive is False


@pytest.mark.parametrize(
    ("status", "state", "retryable", "alive"),
    (
        (200, "alive", False, True),
        (425, "HTTP_not_ready_status", True, False),
        (429, "HTTP_not_ready_status", True, False),
        (503, "HTTP_not_ready_status", True, False),
        (401, "unexpected_authentication_requirement", False, False),
        (403, "unexpected_authentication_requirement", False, False),
        (500, "unexpected_terminal_failure", False, False),
    ),
)
def test_readiness_http_status_classification_is_finite(
    status: int,
    state: str,
    retryable: bool,
    alive: bool,
) -> None:
    observation = AttemptJsonTransport(
        _runner(status=status),
        _handle(),
    ).probe_readiness()
    assert (observation.state, observation.retryable, observation.alive) == (
        state,
        retryable,
        alive,
    )


@pytest.mark.parametrize(
    ("result", "state"),
    (
        (DockerCommandResult(0, "not-json", ""), "malformed_bounded_response"),
        (
            DockerCommandResult(
                0,
                json.dumps({"status": 200, "payload": {"echo": _SECRET}}),
                "",
            ),
            "credential_leakage_signal",
        ),
        (DockerCommandResult(4, "raw", "raw"), "unexpected_terminal_failure"),
    ),
)
def test_readiness_transport_contract_failures_are_terminal(
    result: DockerCommandResult,
    state: str,
) -> None:
    observation = AttemptJsonTransport(
        RecordingRunner(result),
        _handle(),
        sensitive_values=(_SECRET,),
    ).probe_readiness()
    assert observation.state == state
    assert observation.retryable is False
    assert observation.alive is False
