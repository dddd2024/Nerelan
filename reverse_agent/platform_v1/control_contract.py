"""CLI-1 versioned CONTROL REQUEST SCHEMA, without authority or transport.

Parsing a valid request NEVER authorizes, dispatches, or changes a Goal/Task.
An authenticated host implementation must supply the principal and enforce
authorization in GoalService/ControlStore; wire fields are untrusted claims.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping

PROTOCOL = "nerelan-control/v1"
MAX_REQUEST_BYTES = 8192
_NOT_CONNECTED = "authenticated_control_transport_not_implemented"

# All operation names are reserved for the shared GUI/CLI/scheduler contract.
# No handlers for these operations are exposed by this module.
_REQUIRED: dict[str, frozenset[str]] = {
    "doctor": frozenset(),
    "status": frozenset(),
    "goal.create": frozenset({"repository", "objective", "executor_kind", "idempotency_key"}),
    "goal.inspect": frozenset({"goal_id"}),
    "goal.plan": frozenset({"goal_id", "expected_revision", "idempotency_key"}),
    "goal.approve": frozenset({"goal_id", "expected_revision", "idempotency_key"}),
    "goal.launch": frozenset({
        "goal_id", "expected_revision", "window_id", "repository",
        "executor_kind", "binding_ref", "policy_digest", "idempotency_key",
    }),
    "task.list": frozenset(),
    "task.inspect": frozenset({"task_id"}),
    "run.status": frozenset({"run_id"}),
    "run.watch": frozenset({"run_id"}),
    "run.stop": frozenset({"run_id", "idempotency_key"}),
    "window.status": frozenset(),
}
_READ_ONLY = frozenset({
    "doctor", "status", "goal.inspect", "task.list", "task.inspect",
    "run.status", "run.watch", "window.status",
})
_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@/+-]{0,127}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTORS = frozenset({"codex", "opencode", "claude_code"})
_STRING_FIELDS = frozenset({
    "goal_id", "task_id", "run_id", "window_id", "idempotency_key",
    "repository", "objective", "executor_kind", "binding_ref", "policy_digest",
})


class ControlContractError(ValueError):
    """Sanitized schema failure (never contains the caller's payload)."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ControlRequest:
    """Immutable *untrusted* request; it does NOT carry an authenticated principal."""

    operation: str
    request_id: str
    arguments: tuple[tuple[str, str | int], ...]
    protocol: str = PROTOCOL

    @property
    def requires_authority(self) -> bool:
        # Even private reads require authenticated identity; doctor is an
        # explicitly public health-only operation, not the private doctor API.
        return self.operation != "doctor"

    @property
    def mutating(self) -> bool:
        return self.operation not in _READ_ONLY


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ControlContractError("duplicate_json_key")
        obj[key] = value
    return obj


def _bad_constant(_: str) -> None:
    raise ControlContractError("invalid_json")


def _validate_value(field: str, value: object) -> str | int:
    if field == "expected_revision":
        if type(value) is not int or not (0 <= value <= 2**31 - 1):
            raise ControlContractError("invalid_argument")
        return value
    if type(value) is not str:
        raise ControlContractError("invalid_argument")
    if field == "objective":
        # Objective is untrusted natural language, never an authorization
        # statement. Bound its size and reject controls.
        if not (1 <= len(value) <= 2048) or any(ord(c) < 32 for c in value):
            raise ControlContractError("invalid_argument")
    elif field == "repository":
        if not _REPOSITORY.fullmatch(value) or any(part in {".", ".."} for part in value.split("/")):
            raise ControlContractError("invalid_argument")
    elif field == "executor_kind":
        if value not in _EXECUTORS:
            raise ControlContractError("invalid_argument")
    elif field == "policy_digest":
        if not _SHA.fullmatch(value):
            raise ControlContractError("invalid_argument")
    elif field in _STRING_FIELDS and not _PATTERN.fullmatch(value):
        raise ControlContractError("invalid_argument")
    return value


def parse_request(raw: bytes) -> ControlRequest:
    """Decode a bounded, duplicate-free, strictly whitelisted wire envelope.

    Caller-supplied principal, capabilities, tokens, budgets, methods, URLs or
    extra policy fields are unconditionally rejected. A valid schema cannot
    grant permission; only future authenticated host IPC can enforce it.
    """
    if type(raw) is not bytes or len(raw) > MAX_REQUEST_BYTES or not raw:
        raise ControlContractError("invalid_request_size")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_bad_constant,
        )
    except ControlContractError:
        raise
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
        raise ControlContractError("invalid_json") from None

    if type(data) is not dict or set(data) != {"protocol", "operation", "request_id", "args"}:
        raise ControlContractError("invalid_envelope")
    if data["protocol"] != PROTOCOL:
        raise ControlContractError("unsupported_protocol")
    operation = data["operation"]
    if type(operation) is not str or operation not in _REQUIRED:
        raise ControlContractError("not_supported")
    request_id = data["request_id"]
    if type(request_id) is not str or not _PATTERN.fullmatch(request_id):
        raise ControlContractError("invalid_request_id")
    args = data["args"]
    if type(args) is not dict or set(args) != _REQUIRED[operation]:
        raise ControlContractError("invalid_arguments")
    values = tuple(sorted((k, _validate_value(k, v)) for k, v in args.items()))
    return ControlRequest(operation=operation, request_id=request_id, arguments=values)


def unavailable_response(request: ControlRequest) -> dict[str, Any]:
    """Never present schema validation as authorization or execution success."""
    if not isinstance(request, ControlRequest):
        raise ControlContractError("invalid_envelope")
    return {
        "protocol": PROTOCOL,
        "status": "WAITING",
        "code": _NOT_CONNECTED,
        "authenticated": False,
        "dispatch_permitted": False,
        "execution_started": False,
    }
