"""Thin OpenHands Agent Server v1.37.0 lifecycle adapter."""

from __future__ import annotations

import json
import socket
import uuid
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import AcceptanceResult, ExecutionHandle, TaskSubmission

_CONVERSATION_NAMESPACE = uuid.UUID("f1ea8fb8-d944-54c7-8706-3e3ef71b030d")
_TERMINAL_STATUSES = frozenset({"finished", "error", "stuck", "paused"})
_GITHUB_SECRET_KEYS = frozenset(
    {"github_token", "gh_token", "github_pat", "authorization"}
)


class OpenHandsAdapterError(RuntimeError):
    pass


class AmbiguousConversationStart(OpenHandsAdapterError):
    pass


class JsonTransport(Protocol):
    def request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> tuple[int, Mapping[str, Any]]: ...


class UrllibJsonTransport:
    """Small JSON transport that exposes only the OpenHands session key."""

    def __init__(
        self, base_url: str, *, session_api_key: str | None = None, timeout: float = 30
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session_api_key = session_api_key
        self._timeout = timeout

    def request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> tuple[int, Mapping[str, Any]]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self._session_api_key:
            headers["X-Session-API-Key"] = self._session_api_key
        request = Request(
            f"{self._base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                decoded = json.loads(raw) if raw else {}
                return response.status, decoded
        except HTTPError as error:
            raw = error.read()
            decoded = json.loads(raw) if raw else {}
            return error.code, decoded


def conversation_id_for(handle: ExecutionHandle) -> str:
    """Derive the sole conversation UUID for one ExecutionHandle."""

    return str(
        uuid.uuid5(
            _CONVERSATION_NAMESPACE,
            f"{handle.workflow_id}:attempt:{handle.attempt}",
        )
    )


def prepare_bounded_workspace(root: Path, relative: str) -> Path:
    """Create a workspace below root, rejecting traversal and symlinks."""

    root.mkdir(parents=True, exist_ok=True)
    root_resolved = root.resolve(strict=True)
    if root.is_symlink():
        raise ValueError("workspace_root_symlink")
    normalized = relative.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized == "."
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("workspace_path_escape")
    candidate = root.joinpath(*path.parts)
    current = root
    for part in path.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("workspace_symlink_escape")
    candidate.mkdir(parents=True, exist_ok=True)
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved):
        raise ValueError("workspace_path_escape")
    return resolved


def _contains_github_secret(payload: object) -> bool:
    if isinstance(payload, Mapping):
        return any(
            str(key).strip().lower() in _GITHUB_SECRET_KEYS
            or _contains_github_secret(value)
            for key, value in payload.items()
        )
    if isinstance(payload, (list, tuple)):
        return any(_contains_github_secret(value) for value in payload)
    return False


class OpenHandsAdapter:
    """Map one ExecutionHandle to one v1.37.0 conversation lifecycle."""

    def __init__(self, transport: JsonTransport) -> None:
        self._transport = transport

    def health(self) -> dict[str, str]:
        checks: dict[str, str] = {}
        for endpoint in ("/alive", "/health"):
            status, _ = self._transport.request("GET", endpoint)
            checks[endpoint] = "PASS" if status == 200 else "FAIL"
        return checks

    def start_task(
        self,
        submission: TaskSubmission,
        *,
        conversation_request: Mapping[str, Any],
    ) -> ExecutionHandle:
        if not submission.instruction.strip() or len(submission.instruction) > 32768:
            raise ValueError("instruction_out_of_bounds")
        if _contains_github_secret(conversation_request):
            raise ValueError("github_secret_forbidden")

        expected_id = conversation_id_for(submission.handle)
        if (
            submission.handle.conversation_id is not None
            and submission.handle.conversation_id != expected_id
        ):
            raise ValueError("conversation_id_mismatch")

        status, existing = self._transport.request(
            "GET", f"/api/conversations/{expected_id}"
        )
        if status == 200:
            if str(existing.get("id")) != expected_id:
                raise OpenHandsAdapterError("conversation_reconciliation_mismatch")
            return replace(submission.handle, conversation_id=expected_id)
        if status != 404:
            raise OpenHandsAdapterError(f"conversation_reconciliation_http_{status}")

        request_payload = dict(conversation_request)
        request_payload.update(
            {
                "conversation_id": expected_id,
                "workspace": {
                    "kind": "LocalWorkspace",
                    "working_dir": submission.workspace,
                },
                "worktree": False,
                "initial_message": {
                    "role": "user",
                    "content": [{"kind": "TextContent", "text": submission.instruction}],
                    "run": False,
                },
                "max_iterations": min(
                    int(request_payload.get("max_iterations", 20)), 20
                ),
                "secrets": {},
            }
        )
        if _contains_github_secret(request_payload):
            raise ValueError("github_secret_forbidden")

        try:
            status, created = self._transport.request(
                "POST", "/api/conversations", request_payload
            )
        except (TimeoutError, socket.timeout, OSError) as error:
            reconcile_status, reconciled = self._transport.request(
                "GET", f"/api/conversations/{expected_id}"
            )
            if reconcile_status == 200 and str(reconciled.get("id")) == expected_id:
                return replace(submission.handle, conversation_id=expected_id)
            raise AmbiguousConversationStart(
                "ambiguous_start_not_reconciled; refusing duplicate create"
            ) from error
        if status not in {200, 201} or str(created.get("id")) != expected_id:
            raise OpenHandsAdapterError(f"conversation_create_http_{status}")

        run_status, _ = self._transport.request(
            "POST", f"/api/conversations/{expected_id}/run"
        )
        if run_status not in {200, 409}:
            raise OpenHandsAdapterError(f"conversation_run_http_{run_status}")
        return replace(submission.handle, conversation_id=expected_id)

    def get_status(self, handle: ExecutionHandle) -> str:
        conversation_id = self._bound_id(handle)
        status, payload = self._transport.request(
            "GET", f"/api/conversations/{conversation_id}"
        )
        if status != 200:
            raise OpenHandsAdapterError(f"conversation_status_http_{status}")
        execution_status = str(payload.get("execution_status") or "").lower()
        if not execution_status:
            raise OpenHandsAdapterError("conversation_status_missing")
        return execution_status

    def cancel(self, handle: ExecutionHandle, *, delete: bool = False) -> None:
        conversation_id = self._bound_id(handle)
        status, _ = self._transport.request(
            "POST", f"/api/conversations/{conversation_id}/interrupt"
        )
        if status not in {200, 400}:
            raise OpenHandsAdapterError(f"conversation_interrupt_http_{status}")
        if delete:
            delete_status, _ = self._transport.request(
                "DELETE", f"/api/conversations/{conversation_id}"
            )
            if delete_status not in {200, 400, 404}:
                raise OpenHandsAdapterError(
                    f"conversation_delete_http_{delete_status}"
                )

    def collect_result(self, handle: ExecutionHandle) -> AcceptanceResult:
        conversation_id = self._bound_id(handle)
        status = self.get_status(handle)
        if status not in _TERMINAL_STATUSES:
            raise OpenHandsAdapterError("conversation_not_terminal")
        response_status, payload = self._transport.request(
            "GET",
            f"/api/conversations/{conversation_id}/agent_final_response",
        )
        if response_status != 200:
            raise OpenHandsAdapterError(
                f"conversation_result_http_{response_status}"
            )
        response = str(payload.get("response") or "")
        return AcceptanceResult(
            accepted=False,
            checks=("agent_output_collected",),
            detail=response,
        )

    @staticmethod
    def _bound_id(handle: ExecutionHandle) -> str:
        expected_id = conversation_id_for(handle)
        if handle.conversation_id != expected_id:
            raise ValueError("execution_handle_not_bound_to_expected_conversation")
        return expected_id
