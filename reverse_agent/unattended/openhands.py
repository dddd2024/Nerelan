"""Thin OpenHands Agent Server v1.37.0 lifecycle adapter."""

from __future__ import annotations

import json
import socket
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import ExecutionHandle, TaskSubmission
from .identifiers import executor_id, workspace_path

_NOT_STARTED_STATUSES = frozenset({"idle"})
_RUNNING_STATUSES = frozenset({"running"})
_TERMINAL_STATUSES = frozenset({"finished", "error", "stuck"})
_UNSAFE_STATUSES = frozenset(
    {"paused", "waiting_for_confirmation", "deleting", "cancelled"}
)
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

    expected = executor_id(handle.workflow_id, handle.attempt)
    if handle.executor_id != expected:
        raise ValueError("executor_id_mismatch")
    return expected


def prepare_bounded_workspace(root: Path, relative: str) -> Path:
    """Create a workspace below root, rejecting traversal and symlinks."""

    if "\x00" in relative:
        raise ValueError("workspace_path_nul")
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
        or PureWindowsPath(relative).is_absolute()
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

    def __init__(
        self,
        transport: JsonTransport,
        *,
        host_workspace_root: Path,
        agent_workspace_root: str = "/workspace",
    ) -> None:
        if not host_workspace_root.is_absolute():
            raise ValueError("host_workspace_root_must_be_absolute")
        agent_root = PurePosixPath(agent_workspace_root)
        if (
            not agent_root.is_absolute()
            or ".." in agent_root.parts
            or "\x00" in agent_workspace_root
        ):
            raise ValueError("agent_workspace_root_invalid")
        self._transport = transport
        self._host_workspace_root = host_workspace_root
        self._agent_workspace_root = agent_root

    def health(self) -> dict[str, str]:
        checks: dict[str, str] = {}
        for endpoint in ("/alive", "/health"):
            status, _ = self._transport.request("GET", endpoint)
            checks[endpoint] = "PASS" if status == 200 else "FAIL"
        return checks

    def start_task(
        self,
        handle: ExecutionHandle,
        *,
        instruction: str,
        attempt_workspace: str,
        conversation_request: Mapping[str, Any],
    ) -> ExecutionHandle:
        if not instruction.strip() or len(instruction) > 32768:
            raise ValueError("instruction_out_of_bounds")
        if _contains_github_secret(conversation_request):
            raise ValueError("github_secret_forbidden")

        relative, host_workspace, agent_workspace = self._bind_workspace(
            handle, attempt_workspace
        )
        expected_id = conversation_id_for(handle)

        status, existing = self._transport.request(
            "GET", f"/api/conversations/{expected_id}"
        )
        if status == 200:
            return self._reconcile_existing(
                handle,
                expected_id,
                existing,
                retry_ambiguous_run=True,
            )
        if status != 404:
            raise OpenHandsAdapterError(f"conversation_reconciliation_http_{status}")

        self._assert_workspace_still_bound(relative, host_workspace)
        request_payload = dict(conversation_request)
        request_payload.update(
            {
                "conversation_id": expected_id,
                "workspace": {
                    "kind": "LocalWorkspace",
                    "working_dir": agent_workspace,
                },
                "worktree": False,
                "initial_message": {
                    "role": "user",
                    "content": [{"kind": "TextContent", "text": instruction}],
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
            if reconcile_status == 200:
                return self._reconcile_existing(
                    handle,
                    expected_id,
                    reconciled,
                    retry_ambiguous_run=True,
                )
            raise AmbiguousConversationStart(
                "ambiguous_start_not_reconciled; refusing duplicate create"
            ) from error
        if status not in {200, 201} or str(created.get("id")) != expected_id:
            raise OpenHandsAdapterError(f"conversation_create_http_{status}")

        created_status = self._execution_status(created)
        if created_status is None:
            observed_status, observed = self._transport.request(
                "GET", f"/api/conversations/{expected_id}"
            )
            if observed_status != 200:
                raise OpenHandsAdapterError(
                    f"conversation_post_create_reconciliation_http_{observed_status}"
                )
            created = observed
        return self._reconcile_existing(
            handle,
            expected_id,
            created,
            retry_ambiguous_run=True,
        )

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

    def collect_result(self, handle: ExecutionHandle) -> TaskSubmission:
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
        return TaskSubmission(
            verdict="EVIDENCE_ONLY",
            summary=response or "OpenHands returned no final response",
            changed_paths=(),
            commands_executed=(),
            test_evidence=("openhands_terminal_response_collected",),
            limitations=(
                "OpenHands output is executor evidence, not platform acceptance",
            ),
            failure_reason=None if status == "finished" else status,
        )

    @staticmethod
    def _bound_id(handle: ExecutionHandle) -> str:
        return conversation_id_for(handle)

    def _bind_workspace(
        self, handle: ExecutionHandle, attempt_workspace: str
    ) -> tuple[str, Path, str]:
        if "\x00" in attempt_workspace:
            raise ValueError("workspace_path_nul")
        supplied = attempt_workspace.strip().replace("\\", "/")
        if PurePosixPath(supplied).is_absolute() or PureWindowsPath(
            attempt_workspace
        ).is_absolute():
            raise ValueError("workspace_path_escape")
        expected_full = PurePosixPath(workspace_path(handle.workflow_id, handle.attempt))
        expected = expected_full.relative_to(".var/unattended").as_posix()
        if supplied != expected:
            raise ValueError("workspace_attempt_mismatch")
        host_workspace = prepare_bounded_workspace(
            self._host_workspace_root, expected
        )
        agent_workspace = self._agent_workspace_root.joinpath(
            *PurePosixPath(expected).parts
        ).as_posix()
        return expected, host_workspace, agent_workspace

    def _assert_workspace_still_bound(
        self, relative: str, expected_workspace: Path
    ) -> None:
        observed = prepare_bounded_workspace(self._host_workspace_root, relative)
        if observed != expected_workspace or observed.is_symlink():
            raise ValueError("workspace_binding_changed")

    @staticmethod
    def _execution_status(payload: Mapping[str, Any]) -> str | None:
        raw = payload.get("execution_status")
        if not isinstance(raw, str) or not raw.strip():
            return None
        return raw.strip().lower()

    def _reconcile_existing(
        self,
        handle: ExecutionHandle,
        conversation_id: str,
        payload: Mapping[str, Any],
        *,
        retry_ambiguous_run: bool,
    ) -> ExecutionHandle:
        if str(payload.get("id")) != conversation_id:
            raise OpenHandsAdapterError("conversation_reconciliation_mismatch")
        status = self._execution_status(payload)
        if status is None:
            raise OpenHandsAdapterError("conversation_status_missing")
        if status in _RUNNING_STATUSES or status in _TERMINAL_STATUSES:
            return handle
        if status in _UNSAFE_STATUSES:
            raise OpenHandsAdapterError(f"conversation_status_unsafe:{status}")
        if status not in _NOT_STARTED_STATUSES:
            raise OpenHandsAdapterError(f"conversation_status_unknown:{status}")
        return self._run_verified_idle(
            handle,
            conversation_id,
            retry_ambiguous_run=retry_ambiguous_run,
        )

    def _run_verified_idle(
        self,
        handle: ExecutionHandle,
        conversation_id: str,
        *,
        retry_ambiguous_run: bool,
    ) -> ExecutionHandle:
        try:
            run_status, _ = self._transport.request(
                "POST", f"/api/conversations/{conversation_id}/run"
            )
        except (TimeoutError, socket.timeout, OSError) as error:
            observed_status, observed = self._transport.request(
                "GET", f"/api/conversations/{conversation_id}"
            )
            if observed_status != 200:
                raise AmbiguousConversationStart(
                    "ambiguous_run_not_reconciled"
                ) from error
            observed_execution = self._execution_status(observed)
            if observed_execution == "idle":
                if retry_ambiguous_run:
                    return self._run_verified_idle(
                        handle,
                        conversation_id,
                        retry_ambiguous_run=False,
                    )
                raise AmbiguousConversationStart(
                    "ambiguous_run_remained_idle_after_single_retry"
                ) from error
            try:
                return self._reconcile_existing(
                    handle,
                    conversation_id,
                    observed,
                    retry_ambiguous_run=False,
                )
            except OpenHandsAdapterError as reconcile_error:
                raise AmbiguousConversationStart(
                    "ambiguous_run_not_reconciled"
                ) from reconcile_error
        if run_status not in {200, 201, 409}:
            raise OpenHandsAdapterError(f"conversation_run_http_{run_status}")
        observed_status, observed = self._transport.request(
            "GET", f"/api/conversations/{conversation_id}"
        )
        if observed_status != 200:
            raise OpenHandsAdapterError(
                f"conversation_post_run_reconciliation_http_{observed_status}"
            )
        observed_execution = self._execution_status(observed)
        if observed_execution == "idle":
            raise OpenHandsAdapterError("conversation_run_not_started")
        return self._reconcile_existing(
            handle,
            conversation_id,
            observed,
            retry_ambiguous_run=False,
        )
