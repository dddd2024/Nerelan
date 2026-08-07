"""Loopback-only trusted Task API service for Platform V1.

Task/run truth is server-owned in ``TaskStore``. The browser reads and creates
tasks through these endpoints; it never obtains shell authority, provider
secrets, or direct filesystem access.

Boundaries enforced at the HTTP layer:
- binds only to loopback (``validate_bind_host``);
- Origin fail-closed (``_check_origin``);
- bounded JSON body size;
- request body, Authorization, and credentials are never logged or echoed;
- error responses never leak stack traces, auth, or environment.
"""

from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
import json
import os
from threading import Thread
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlsplit
import tempfile

from .run_store import (
    DuplicateTaskError,
    InvalidTransitionError,
    TaskStore,
    TaskStoreError,
)
from .task_runtime import ExecutorRuntimeError, ExecutorRouter

_MAX_BODY_BYTES = 256 * 1024
_TASKS_LIMIT = 100


class _EventView:
    """Attribute-access wrapper around an event dict for uniform response formatting."""

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _mapping(obj: Any, name: str) -> Mapping[str, Any]:
    value = _attr(obj, name, {})
    if isinstance(value, str):
        return {"raw": value}
    if isinstance(value, dict):
        return value
    if isinstance(value, Mapping):
        return dict(value)
    return {}


class _TaskHandler(BaseHTTPRequestHandler):
    store: TaskStore
    router: ExecutorRouter
    allowed_origin: str
    live_enabled: bool

    server_version = "reverse-agent-task-service/1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        try:
            from .task_service_mapping import map_task_to_frontend
            segments = self._segments()
            if len(segments) == 2 and segments == ["api", "tasks"]:
                self._send_json(HTTPStatus.OK, self._list_tasks_response())
                return
            if (
                len(segments) == 4
                and segments[:2] == ["api", "tasks"]
                and segments[3] == "events"
            ):
                try:
                    task = self.store.get_task(segments[2])
                except TaskStoreError:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "task not found"})
                    return
                events_out = []
                for e in task.events:
                    meta = _attr(e, "metadata", "")
                    if isinstance(meta, str):
                        meta = {"raw": meta}
                    elif isinstance(meta, Mapping) and not isinstance(meta, dict):
                        meta = dict(meta)
                    events_out.append({
                        "id": _attr(e, "id", ""),
                        "task_id": _attr(e, "task_id", ""),
                        "type": _attr(e, "type", "EXECUTOR_FINISHED"),
                        "timestamp": _attr(e, "timestamp", ""),
                        "title": _attr(e, "title", ""),
                        "description": _attr(e, "description", ""),
                        "raw_log": _attr(e, "raw_log", ""),
                        "metadata": meta,
                    })
                self._send_json(
                    HTTPStatus.OK,
                    {"task_id": task.id, "events": events_out},
                )
                return
            if len(segments) == 3 and segments[:2] == ["api", "tasks"]:
                try:
                    task = self.store.get_task(segments[2])
                except TaskStoreError:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "task not found"})
                    return
                self._send_json(HTTPStatus.OK, self._task_response(task))
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except Exception:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal task service error"},
            )

    def do_POST(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        try:
            segments = self._segments()
            if segments == ["api", "tasks"]:
                payload = self._read_json()
                task = self._create_task_from_payload(payload)
                self._send_json(HTTPStatus.CREATED, self._task_response(task))
                return
            if (
                len(segments) == 4
                and segments[:2] == ["api", "tasks"]
                and segments[3] == "execute"
            ):
                workspace_root = os.environ.get(
                    "REVERSE_AGENT_TASK_WORKSPACE_ROOT", ""
                )
                payload = self._read_json(optional=True)
                command_id = str(payload.get("validation_command_id", "")) if payload else ""
                try:
                    task = self.store.get_task(segments[2])
                except TaskStoreError:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "task not found"})
                    return
                if task.status != "QUEUED":
                    self._send_json(
                        HTTPStatus.CONFLICT,
                        {"error": "task_not_queued:%s" % task.status},
                    )
                    return
                if not workspace_root:
                    try:
                        db_path = self.store.db_path
                        db_dir = os.path.dirname(db_path) or "."
                        workspace_root = os.path.join(db_dir, "task_workspaces")
                    except Exception:
                        workspace_root = os.path.join(
                            tempfile.gettempdir(), "issue128_task_workspaces"
                        )
                    os.makedirs(workspace_root, exist_ok=True)
                task = self.store.transition_to(task.id, "PREPARING_WORKSPACE")
                task = self.store.transition_to(task.id, "RUNNING_FIXTURE")
                task = self.store.transition_to(task.id, "VALIDATING")
                self.store.add_event(
                    task.id,
                    event_type="EXECUTOR_RUNNING",
                    title="Executor running",
                    description="Executor %s started" % task.executor_kind,
                    metadata={"executor_kind": task.executor_kind},
                )
                try:
                    result = self._run_executor(
                        task=task,
                        workspace_root=workspace_root,
                        validation_command_id=command_id or "git_diff_check",
                    )
                except ExecutorRuntimeError as exc:
                    self.store.classify_failure(
                        task.id,
                        classification="blocked",
                        detail=str(exc),
                    )
                    task = self.store.get_task(task.id)
                    self._send_json(HTTPStatus.BAD_REQUEST, self._task_response(task))
                    return
                if result["success"]:
                    task = self.store.transition_to(
                        task.id, "READY_FOR_REVIEW_FIXTURE"
                    )
                    self.store.add_event(
                        task.id,
                        event_type="VALIDATED",
                        title="Validation passed",
                        description=f"{result['validation_command_id']} passed",
                        metadata={"validation_exit_code": result["validation_exit_code"]},
                    )
                else:
                    classification = (
                        "blocked"
                        if "unapproved" in result.get("error", "")
                        else "failed"
                    )
                    self.store.classify_failure(
                        task.id,
                        classification=classification,
                        detail=result.get("error", "execution failed"),
                    )
                    self.store.add_event(
                        task.id,
                        event_type="EXECUTOR_FINISHED",
                        title="Executor finished",
                        description=result.get("error", "execution failed"),
                        metadata={
                            "validation_exit_code": result["validation_exit_code"],
                        },
                    )
                task = self.store.get_task(task.id)
                self._send_json(HTTPStatus.OK, self._task_response(task))
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except (DuplicateTaskError, InvalidTransitionError, TaskStoreError) as exc:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
        except ExecutorRuntimeError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal task service error"},
            )

    def _run_executor(
        self,
        *,
        task: Any,
        workspace_root: str,
        validation_command_id: str | None,
    ) -> dict[str, Any]:
        router = ExecutorRouter()
        if validation_command_id:
            from .task_runtime import DeterministicFixtureExecutor

            executor = DeterministicFixtureExecutor(
                validation_command_id=validation_command_id,
            )
        else:
            executor = router._registry["deterministic_fixture"]()
        result = executor.execute(
            task.id,
            self.store,
            workspace_root=workspace_root,
            event_callback=self._store_event_callback,
        )
        self.store.set_changed_files(task.id, result.changed_files)
        self.store.set_validation_result(
            task.id,
            command_id=result.validation_command_id,
            exit_code=result.validation_exit_code,
            output_digest=result.validation_output_digest,
        )
        self.store.add_evidence(
            task.id,
            category="Validation",
            label=result.validation_command_id,
            value=str(result.validation_exit_code),
            status="pass" if result.validation_exit_code == 0 else "fail",
            detail=result.validation_output_summary,
            raw_json_digest=result.validation_output_digest,
        )
        self.store.add_evidence(
            task.id,
            category="Executor",
            label="executor_kind",
            value=task.executor_kind,
            status="pass",
            detail="fixture/provider-free executor",
        )
        return {
            "success": result.success,
            "validation_command_id": result.validation_command_id,
            "validation_exit_code": result.validation_exit_code,
            "validation_output_digest": result.validation_output_digest,
            "changed_files": result.changed_files,
            "error": result.error,
        }

    def _store_event_callback(self, task_id: str, event: dict[str, Any]) -> None:
        try:
            self.store.add_event(
                task_id,
                event_type=event.get("type", "EXECUTOR_FINISHED"),
                title=event.get("title", "Executor event"),
                description=event.get("description", ""),
                raw_log=event.get("raw_log", ""),
                metadata=event.get("metadata"),
            )
        except Exception:
            pass

    def _create_task_from_payload(self, payload: dict[str, Any]) -> Any:
        title = str(payload.get("title", "")).strip()
        if not title:
            raise TaskStoreError("title_required")
        executor_kind = str(payload.get("executor_kind", "deterministic_fixture"))
        if executor_kind not in ("deterministic_fixture",):
            raise TaskStoreError(f"unsupported_executor_kind:{executor_kind}")
        return self.store.create_task(
            title=title,
            repository=str(payload.get("repository", "dddd2024/reverse-agent")),
            executor_kind=executor_kind,
            model_profile_ref=str(payload.get("model_profile_ref", "")),
            permission_profile=str(payload.get("permission_profile", "ASK_FOR_APPROVAL")),
            policy_ref=str(payload.get("policy_ref", "")),
            workspace=str(payload.get("workspace", "")),
            branch=str(payload.get("branch", "")),
            idempotency_key=str(payload.get("idempotency_key", "")),
        )

    def _list_tasks_response(self) -> dict[str, Any]:
        tasks = self.store.list_tasks(limit=_TASKS_LIMIT)
        return {
            "tasks": [self._task_response(t) for t in tasks],
            "total": self.store.count_tasks(),
        }

    def _task_response(self, task: Any) -> dict[str, Any]:
        from .task_service_mapping import (
            map_task_status_to_frontend_state,
            map_task_to_frontend,
        )
        events = task.events
        if events and isinstance(events[0], Mapping):
            events = [
                _EventView(**e) for e in events
            ]
        changed = task.changed_files
        if changed and isinstance(changed[0], Mapping):
            changed = [dict(f) for f in changed]
        evidence = task.evidence_refs
        if evidence and isinstance(evidence[0], Mapping):
            evidence = [dict(e) for e in evidence]
        return {
            "id": task.id,
            "title": task.title,
            "repository": task.repository,
            "status": task.status,
            "state": map_task_status_to_frontend_state(task.status),
            "executor_kind": task.executor_kind,
            "execution_id": task.execution_id,
            "model_profile_ref": task.model_profile_ref,
            "permission_profile": task.permission_profile,
            "policy_ref": task.policy_ref,
            "workspace": task.workspace,
            "branch": task.branch,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "failure_classification": task.failure_classification,
            "failure_detail": task.failure_detail,
            "validation_command_id": task.validation_command_id,
            "validation_exit_code": task.validation_exit_code,
            "validation_output_digest": task.validation_output_digest,
            "idempotency_key": task.idempotency_key,
            "changed_files": list(changed),
            "evidence": list(evidence),
            "events": self._events_response(events),
            "frontend_task": map_task_to_frontend(task),
        }

    def _events_response(self, events: Sequence[Any]) -> list[dict[str, Any]]:
        return [
            {
                "id": _attr(e, "id", ""),
                "task_id": _attr(e, "task_id", ""),
                "type": _attr(e, "type", "EXECUTOR_FINISHED"),
                "timestamp": _attr(e, "timestamp", ""),
                "title": _attr(e, "title", ""),
                "description": _attr(e, "description", ""),
                "raw_log": _attr(e, "raw_log", ""),
                "metadata": _mapping(e, "metadata"),
            }
            for e in events
        ]

    def _segments(self) -> list[str]:
        path = urlsplit(self.path).path
        return [unquote(part) for part in path.split("/") if part]

    def _read_json(self, *, optional: bool = False) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            if optional:
                return {}
            raise TaskStoreError("request body is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise TaskStoreError("invalid Content-Length") from exc
        if length < 0 or length > _MAX_BODY_BYTES:
            raise TaskStoreError("request body exceeds limit")
        if length == 0 and optional:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TaskStoreError("request body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise TaskStoreError("request JSON must be an object")
        return payload

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(
            payload, ensure_ascii=False, default=str, separators=(",", ":")
        ).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _send_forbidden(self) -> None:
        body = b'{"error":"forbidden"}'
        self.send_response(HTTPStatus.FORBIDDEN)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _check_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        if origin == self.allowed_origin:
            return True
        self._send_forbidden()
        return False

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin == self.allowed_origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")


def _handler_factory(
    store: TaskStore,
    router: ExecutorRouter,
    *,
    allowed_origin: str,
) -> type[_TaskHandler]:
    class ConfiguredHandler(_TaskHandler):
        pass

    ConfiguredHandler.store = store
    ConfiguredHandler.router = router
    ConfiguredHandler.allowed_origin = allowed_origin
    ConfiguredHandler.live_enabled = False
    return ConfiguredHandler


def validate_bind_host(host: str) -> str:
    normalized = host.strip()
    if normalized == "localhost":
        return normalized
    try:
        address = ip_address(normalized)
    except ValueError as exc:
        raise ValueError(
            "task service host must be a loopback address or localhost"
        ) from exc
    if not address.is_loopback:
        raise ValueError(
            "task service host must be a loopback address or localhost"
        )
    return normalized


class TaskService:
    """Convenience wrapper that starts the trusted loopback Task API."""

    def __init__(
        self,
        *,
        store: TaskStore | None = None,
        router: ExecutorRouter | None = None,
        allowed_origin: str = "http://localhost:4173",
    ) -> None:
        self.store = store or TaskStore()
        self.router = router or ExecutorRouter()
        self.allowed_origin = allowed_origin

    def start(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[ThreadingHTTPServer, Thread]:
        bind_host = validate_bind_host(
            host or os.environ.get("REVERSE_AGENT_TASK_SERVICE_HOST", "127.0.0.1")
        )
        bind_port = port or int(os.environ.get("REVERSE_AGENT_TASK_SERVICE_PORT", "8766"))
        server = ThreadingHTTPServer(
            (bind_host, bind_port),
            _handler_factory(
                self.store,
                self.router,
                allowed_origin=self.allowed_origin,
            ),
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread


def run_task_service(
    *,
    host: str | None = None,
    port: int | None = None,
    store: TaskStore | None = None,
    allowed_origin: str | None = None,
) -> None:
    bind_host = validate_bind_host(
        host or os.environ.get("REVERSE_AGENT_TASK_SERVICE_HOST", "127.0.0.1")
    )
    bind_port = port or int(os.environ.get("REVERSE_AGENT_TASK_SERVICE_PORT", "8766"))
    origin = allowed_origin or os.environ.get(
        "REVERSE_AGENT_TASK_SERVICE_ORIGIN", "http://localhost:4173"
    )
    server = ThreadingHTTPServer(
        (bind_host, bind_port),
        _handler_factory(
            store or TaskStore(),
            ExecutorRouter(),
            allowed_origin=origin,
        ),
    )
    server.serve_forever()


if __name__ == "__main__":
    run_task_service()
