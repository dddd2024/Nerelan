"""Provider-free CLI-1 schema tests. No access to host, SQLite or model tools."""
from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from reverse_agent.platform_v1.control_contract import (
    PROTOCOL, MAX_REQUEST_BYTES, ControlContractError,
    parse_request, unavailable_response,
)


def wire(operation="status", args=None, **extra):
    envelope = {
        "protocol": PROTOCOL, "operation": operation,
        "request_id": "req-20261017-0123456789abcdef",
        "args": args if args is not None else {},
        **extra,
    }
    return json.dumps(envelope).encode("utf-8")


@pytest.mark.parametrize("operation,arguments,mutating", [
    ("doctor", {}, False),
    ("status", {}, False),
    ("goal.create", {
        "repository": "dddd2024/Nerelan", "objective": "Inspect one queued task",
        "executor_kind": "codex", "idempotency_key": "repeat-1234",
    }, True),
    ("goal.inspect", {"goal_id": "goal-1770000000000-abcdef012345"}, False),
    ("goal.plan", {
        "goal_id": "goal-1770000000000-abcdef012345",
        "expected_revision": 0, "idempotency_key": "plan-repeat-1",
    }, True),
    ("goal.approve", {
        "goal_id": "goal-1770000000000-abcdef012345",
        "expected_revision": 3, "idempotency_key": "approve-repeat-1",
    }, True),
    ("goal.launch", {
        "goal_id": "goal-1770000000000-abcdef012345",
        "expected_revision": 4, "window_id": "window-1770000000000-abcdef012345",
        "repository": "dddd2024/Nerelan", "executor_kind": "codex",
        "binding_ref": "binding-2026", "policy_digest": "b" * 64,
        "idempotency_key": "launch-repeat-1",
    }, True),
    ("task.list", {}, False),
    ("task.inspect", {"task_id": "task-1770000000000-abcdef012345"}, False),
    ("run.status", {"run_id": "run-1770000000000-abcdef012345"}, False),
    ("run.watch", {"run_id": "run-1770000000000-abcdef012345"}, False),
    ("run.stop", {"run_id": "run-1770000000000-abcdef012345", "idempotency_key": "stop-repeat-1"}, True),
    ("window.status", {}, False),
])
def test_known_operations_are_parsed_but_never_executed(operation, arguments, mutating):
    parsed = parse_request(wire(operation, arguments))
    assert parsed.operation == operation
    assert parsed.mutating is mutating
    assert parsed.requires_authority is (operation != "doctor")
    assert dict(parsed.arguments) == arguments
    reply = unavailable_response(parsed)
    assert reply == {
        "protocol": PROTOCOL,
        "status": "WAITING",
        "code": "authenticated_control_transport_not_implemented",
        "authenticated": False,
        "dispatch_permitted": False,
        "execution_started": False,
    }
    # Even valid schema has no principal or activation capability.
    assert not hasattr(parsed, "principal")
    with pytest.raises(FrozenInstanceError):
        parsed.operation = "goal.launch"


@pytest.mark.parametrize("raw,code", [
    (b"", "invalid_request_size"),
    (b"x" * (MAX_REQUEST_BYTES + 1), "invalid_request_size"),
    (b'{"protocol":', "invalid_json"),
    (b'[]', "invalid_envelope"),
    (b'null', "invalid_envelope"),
    (b'{"protocol":"nerelan-control/v1","operation":"status","request_id":"id-1234","args":{},"token":"secret"}', "invalid_envelope"),
    (b'{"protocol":"nerelan-control/v1","operation":"status","request_id":"id-1234","args":{},"principal":"owner"}', "invalid_envelope"),
    (b'{"protocol":"nerelan-control/v1","operation":"status","request_id":"id-1234","args":{},"operation":"goal.launch"}', "duplicate_json_key"),
    (b'{"protocol":"nerelan-control/v1","operation":"status","request_id":"id-1234","args":{"foo":1,"foo":2}}', "duplicate_json_key"),
    (b'{"protocol":"nerelan-control/v1","operation":"status","request_id":"id-1234","args":{"epoch":NaN}}', "invalid_json"),
])
def test_host_auth_fields_duplicates_nonjson_never_admitted(raw, code):
    with pytest.raises(ControlContractError) as err:
        parse_request(raw)
    assert err.value.code == code
    assert "secret" not in str(err.value)


@pytest.mark.parametrize("malformed,code", [
    ({"protocol": "nerelan-control/v0"}, "unsupported_protocol"),
    ({"operation": "goal.merge"}, "not_supported"),
    ({"request_id": "../payload"}, "invalid_request_id"),
    ({"request_id": "x" * 500}, "invalid_request_id"),
    ({"args": {"caller_principal": "owner"}}, "invalid_arguments"),
    ({"args": {"capability": "owner", "token": "secret"}}, "invalid_arguments"),
])
def test_suspicious_envelopes_fail_closed(malformed, code):
    data = json.loads(wire())
    data.update(malformed)
    with pytest.raises(ControlContractError) as err:
        parse_request(json.dumps(data).encode())
    assert err.value.code == code


def test_launch_must_explicitly_bind_exact_scope_and_revision():
    data = json.loads(wire("goal.launch", {
        "goal_id": "goal-1790000000000-abcdef012345",
        "expected_revision": 5, "window_id": "window-1790000000000-abcdef012345",
        "repository": "dddd2024/Nerelan", "executor_kind": "codex",
        "binding_ref": "binding-1", "policy_digest": "a" * 64,
        "idempotency_key": "launch-0001",
    }))
    for key in tuple(data["args"]):
        bad = json.loads(json.dumps(data))
        del bad["args"][key]
        with pytest.raises(ControlContractError) as err:
            parse_request(json.dumps(bad).encode())
        assert err.value.code == "invalid_arguments", key
    for value in (True, -1, "5", 2**50):
        bad = json.loads(json.dumps(data))
        bad["args"]["expected_revision"] = value
        with pytest.raises(ControlContractError) as err:
            parse_request(json.dumps(bad).encode())
        assert err.value.code == "invalid_argument"


@pytest.mark.parametrize("field,value", [
    ("repository", "../../taskstore"),
    ("repository", "root/.."),
    ("repository", "owner/"),
    ("executor_kind", "shell"),
    ("executor_kind", "codex;rm"),
    ("binding_ref", "api-key\nsecret"),
    ("policy_digest", "not-a-sha256"),
    ("idempotency_key", "secret token"),
])
def test_invalid_launch_scopes_rejected(field, value):
    payload = json.loads(wire("goal.launch", {
        "goal_id": "goal-1", "expected_revision": 1,
        "window_id": "window-1", "repository": "dddd2024/Nerelan",
        "executor_kind": "codex", "binding_ref": "bind-1",
        "policy_digest": "a" * 64, "idempotency_key": "repeat-1234",
    }))
    payload["args"][field] = value
    with pytest.raises(ControlContractError) as err:
        parse_request(json.dumps(payload).encode())
    assert err.value.code == "invalid_argument"


def test_unbounded_objective_and_control_character_are_rejected():
    for text in ("x" * 2049, "safe\nrun dangerous tool", ""):
        obj = {
            "repository": "dddd2024/Nerelan", "objective": text,
            "executor_kind": "codex", "idempotency_key": "retry-1",
        }
        with pytest.raises(ControlContractError) as err:
            parse_request(wire("goal.create", obj))
        assert err.value.code == "invalid_argument"


def test_parse_never_uses_io_even_on_valid_mutator(monkeypatch):
    import socket
    import sqlite3
    from urllib import request

    def forbidden(*args, **kwargs):
        raise AssertionError("contract parser must never access IO or external authority")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(request, "urlopen", forbidden)
    parsed = parse_request(wire("run.stop", {
        "run_id": "run-123456", "idempotency_key": "stop-12345"
    }))
    assert unavailable_response(parsed)["dispatch_permitted"] is False
