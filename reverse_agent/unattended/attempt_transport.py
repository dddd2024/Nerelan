"""Fixed Docker-exec JSON transport for one deterministic Attempt container."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import ExecutionHandle
from .readiness import (
    ALIVE_OBSERVATION,
    ReadinessObservation,
    retryable_observation,
    terminal_observation,
)
from .sandbox import DockerCommandRunner, container_name_for

_MAX_REQUEST_BYTES = 64 * 1024
_MAX_RESPONSE_BYTES = 1024 * 1024
_FIXED_PYTHON = "/usr/local/bin/python"
_CONVERSATION_ID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z"
)
_EXEC_CLIENT = r"""
import json
import sys
import urllib.error
import urllib.request

method = sys.argv[1]
path = sys.argv[2]
request_limit = int(sys.argv[3])
response_limit = int(sys.argv[4])
body = sys.stdin.buffer.read(request_limit + 1)
if len(body) > request_limit:
    raise SystemExit(3)
headers = {"Accept": "application/json"}
if body:
    headers["Content-Type"] = "application/json"
request = urllib.request.Request(
    "http://127.0.0.1:8000" + path,
    data=body or None,
    headers=headers,
    method=method,
)
try:
    response = urllib.request.urlopen(request, timeout=30)
except urllib.error.HTTPError as error:
    response = error
except TimeoutError:
    raise SystemExit(8)
except OSError:
    raise SystemExit(9)
with response:
    raw = response.read(response_limit + 1)
    if len(raw) > response_limit:
        raise SystemExit(5)
try:
    payload = json.loads(raw) if raw else {}
except Exception:
    raise SystemExit(6)
if not isinstance(payload, dict):
    raise SystemExit(7)
sys.stdout.write(json.dumps({"status": response.status, "payload": payload}))
""".strip()


class AttemptTransportError(RuntimeError):
    """Sanitized transport failure without Docker or HTTP response material."""


class AttemptTransportStartupUnavailable(AttemptTransportError):
    """A bounded startup-only transport state."""

    def __init__(self, state: str) -> None:
        if state not in {"connection_refused", "timeout"}:
            raise ValueError("invalid_startup_transport_state")
        super().__init__(state)
        self.state = state


class AttemptJsonTransport:
    """Expose only the audited Agent Server API for one ExecutionHandle."""

    def __init__(
        self,
        runner: DockerCommandRunner,
        handle: ExecutionHandle,
        *,
        sensitive_values: Sequence[str] = (),
    ) -> None:
        values = tuple(sensitive_values)
        if any(
            not isinstance(value, str) or not value or "\x00" in value
            for value in values
        ):
            raise ValueError("sensitive_value_invalid")
        self._runner = runner
        self._container_name = container_name_for(handle)
        self._conversation_id = handle.executor_id
        self._sensitive_values = values

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> tuple[int, Mapping[str, Any]]:
        self._validate_target(method, path, payload)
        encoded = (
            b""
            if payload is None
            else json.dumps(
                payload,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if len(encoded) > _MAX_REQUEST_BYTES:
            raise AttemptTransportError("attempt_request_too_large")

        result = self._runner.run(
            (
                "docker",
                "container",
                "exec",
                "--interactive",
                self._container_name,
                _FIXED_PYTHON,
                "-c",
                _EXEC_CLIENT,
                method,
                path,
                str(_MAX_REQUEST_BYTES),
                str(_MAX_RESPONSE_BYTES),
            ),
            input_text=encoded.decode("utf-8"),
        )
        if result.returncode == 8:
            raise AttemptTransportStartupUnavailable("timeout")
        if result.returncode == 9:
            raise AttemptTransportStartupUnavailable("connection_refused")
        if result.returncode != 0:
            raise AttemptTransportError("attempt_transport_failed")
        raw = result.stdout
        if len(raw.encode("utf-8", "surrogateescape")) > _MAX_RESPONSE_BYTES:
            raise AttemptTransportError("attempt_response_too_large")
        if any(value in raw for value in self._sensitive_values):
            raise AttemptTransportError("attempt_response_sensitive")
        try:
            envelope = json.loads(raw)
            status = envelope["status"]
            response = envelope["payload"]
            if (
                isinstance(status, bool)
                or not isinstance(status, int)
                or not isinstance(response, Mapping)
            ):
                raise ValueError("invalid_envelope")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise AttemptTransportError("attempt_response_malformed") from error
        return status, response

    def probe_readiness(self) -> ReadinessObservation:
        """Classify only the fixed loopback /alive startup operation."""

        try:
            status, _ = self.request("GET", "/alive")
        except AttemptTransportStartupUnavailable as error:
            return retryable_observation(error.state)
        except AttemptTransportError as error:
            category = str(error)
            if category == "attempt_response_malformed":
                return terminal_observation("malformed_bounded_response")
            if category in {
                "attempt_request_too_large",
                "attempt_response_too_large",
            }:
                return terminal_observation("transport_protocol_violation")
            if category == "attempt_response_sensitive":
                return terminal_observation("credential_leakage_signal")
            return terminal_observation("unexpected_terminal_failure")
        if status == 200:
            return ALIVE_OBSERVATION
        if status in {425, 429, 503}:
            return retryable_observation("HTTP_not_ready_status")
        if status in {401, 403}:
            return terminal_observation("unexpected_authentication_requirement")
        return terminal_observation("unexpected_terminal_failure")

    def _validate_target(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None,
    ) -> None:
        if not isinstance(method, str) or not isinstance(path, str):
            raise ValueError("attempt_endpoint_invalid")
        allowed: dict[tuple[str, str], bool] = {
            ("GET", "/alive"): False,
            ("GET", "/health"): False,
            ("POST", "/api/conversations"): True,
        }
        conversation = self._conversation_id
        if _CONVERSATION_ID.fullmatch(conversation) is None:
            raise ValueError("attempt_conversation_id_invalid")
        for selected_method, suffix, accepts_payload in (
            ("GET", "", False),
            ("POST", "/run", False),
            ("POST", "/interrupt", False),
            ("DELETE", "", False),
            ("GET", "/agent_final_response", False),
            ("GET", "/events", False),
        ):
            allowed[
                (
                    selected_method,
                    f"/api/conversations/{conversation}{suffix}",
                )
            ] = accepts_payload
        accepts_payload = allowed.get((method, path))
        if accepts_payload is None:
            raise ValueError("attempt_endpoint_forbidden")
        if accepts_payload is False and payload is not None:
            raise ValueError("attempt_payload_forbidden")
        if accepts_payload is True and not isinstance(payload, Mapping):
            raise ValueError("attempt_payload_required")
