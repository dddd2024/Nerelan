"""Server-owned SQLite task and event store for Platform V1.

Task/run truth lives in the trusted loopback Task API, not in the React Query
cache. Every task carries a server-generated id, and every lifecycle change
is recorded as an append-only event so the task can be re-read after a
crash or server restart and still reconstruct its full history.

Idempotency keys are enforced at the store layer: creating a task with an
idempotency key that already exists returns the existing task instead of
creating a duplicate.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Mapping, Sequence


TASK_STATUS_ORDER = (
    "QUEUED",
    "PREPARING_WORKSPACE",
    "RUNNING",
    "RUNNING_FIXTURE",
    "VALIDATING",
    "READY_FOR_REVIEW",
    "READY_FOR_REVIEW_FIXTURE",
    "BLOCKED",
    "FAILED",
    "CANCELLED",
)
TERMINAL_STATUSES = frozenset({
    "READY_FOR_REVIEW",
    "READY_FOR_REVIEW_FIXTURE",
    "BLOCKED",
    "FAILED",
    "CANCELLED",
})

VALID_EVENT_TYPES = frozenset({
    "DISCOVERED",
    "VALIDATED",
    "WORKSPACE_READY",
    "EXECUTOR_RUNNING",
    "EXECUTOR_FINISHED",
    "LOCAL_VALIDATED",
})

TRANSITION_RULES: dict[str, tuple[str, ...]] = {
    "QUEUED": (
        "PREPARING_WORKSPACE",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ),
    "PREPARING_WORKSPACE": (
        "RUNNING",
        "RUNNING_FIXTURE",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ),
    "RUNNING": (
        "VALIDATING",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ),
    "RUNNING_FIXTURE": (
        "VALIDATING",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ),
    "VALIDATING": (
        "READY_FOR_REVIEW",
        "READY_FOR_REVIEW_FIXTURE",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


def _short_uuid() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Task:
    id: str
    title: str
    repository: str
    status: str
    executor_kind: str
    execution_id: str
    model_profile_ref: str
    permission_profile: str
    policy_ref: str
    workspace: str
    branch: str
    created_at: str
    updated_at: str
    failure_classification: str = ""
    failure_detail: str = ""
    validation_command_id: str = ""
    validation_exit_code: int | None = None
    validation_output_digest: str = ""
    idempotency_key: str = ""
    changed_files: tuple[Mapping[str, Any], ...] = ()
    evidence_refs: tuple[Mapping[str, Any], ...] = ()
    events: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class TaskEvent:
    id: str
    task_id: str
    type: str
    timestamp: str
    title: str
    description: str
    raw_log: str
    metadata: Mapping[str, Any]


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class TaskStoreError(Exception):
    """Raised on store-level failures (schema, integrity, invalid transitions)."""


class DuplicateTaskError(TaskStoreError):
    """Raised when an idempotency key collides with a different task request."""


class InvalidTransitionError(TaskStoreError):
    """Raised when a requested status transition is not allowed."""


def _row_to_task(conn: sqlite3.Connection, row: sqlite3.Row) -> Task:
    events = [dict(r) for r in conn.execute(
        "SELECT id, task_id, type, timestamp, title, description, raw_log, "
        "metadata FROM task_events WHERE task_id = ? ORDER BY seq ASC",
        (row["id"],),
    )]
    changed_files = [dict(r) for r in conn.execute(
        "SELECT path, status, additions, deletions, diff_digest FROM task_changed_files "
        "WHERE task_id = ? ORDER BY seq ASC",
        (row["id"],),
    )]
    evidence = [dict(r) for r in conn.execute(
        "SELECT id, category, label, value, status, detail, raw_json_digest FROM "
        "task_evidence WHERE task_id = ? ORDER BY seq ASC",
        (row["id"],),
    )]
    return Task(
        id=row["id"],
        title=row["title"],
        repository=row["repository"],
        status=row["status"],
        executor_kind=row["executor_kind"],
        execution_id=row["execution_id"],
        model_profile_ref=row["model_profile_ref"],
        permission_profile=row["permission_profile"],
        policy_ref=row["policy_ref"],
        workspace=row["workspace"],
        branch=row["branch"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        failure_classification=row["failure_classification"] or "",
        failure_detail=row["failure_detail"] or "",
        validation_command_id=row["validation_command_id"] or "",
        validation_exit_code=row["validation_exit_code"],
        validation_output_digest=row["validation_output_digest"] or "",
        idempotency_key=row["idempotency_key"] or "",
        changed_files=changed_files,
        evidence_refs=evidence,
        events=events,
    )


class TaskStore:
    """Append-only, server-owned task state in SQLite."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._path = db_path
        self._conn = sqlite3.connect(
            db_path if db_path != ":memory:" else "",
            uri=(db_path == ":memory:"),
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._lock = RLock()
        self._init_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                repository TEXT NOT NULL,
                status TEXT NOT NULL,
                executor_kind TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                model_profile_ref TEXT NOT NULL,
                permission_profile TEXT NOT NULL,
                policy_ref TEXT NOT NULL,
                workspace TEXT NOT NULL,
                branch TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                failure_classification TEXT NOT NULL,
                failure_detail TEXT NOT NULL,
                validation_command_id TEXT NOT NULL,
                validation_exit_code INTEGER,
                validation_output_digest TEXT NOT NULL,
                idempotency_key TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                repository TEXT NOT NULL,
                executor_kind TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_events (
                id TEXT NOT NULL,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_log TEXT NOT NULL,
                metadata TEXT NOT NULL,
                seq INTEGER PRIMARY KEY AUTOINCREMENT
            );
            CREATE TABLE IF NOT EXISTS task_changed_files (
                task_id TEXT NOT NULL REFERENCES tasks(id),
                path TEXT NOT NULL,
                status TEXT NOT NULL,
                additions INTEGER NOT NULL,
                deletions INTEGER NOT NULL,
                diff_digest TEXT NOT NULL,
                seq INTEGER PRIMARY KEY AUTOINCREMENT
            );
            CREATE TABLE IF NOT EXISTS task_evidence (
                id TEXT NOT NULL,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                value TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                raw_json_digest TEXT NOT NULL,
                seq INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """
        )

    @property
    def db_path(self) -> str:
        return self._path

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    def create_task(
        self,
        *,
        title: str,
        repository: str = "dddd2024/reverse-agent",
        executor_kind: str = "deterministic_fixture",
        model_profile_ref: str = "",
        permission_profile: str = "ASK_FOR_APPROVAL",
        policy_ref: str = "",
        workspace: str = "",
        branch: str = "",
        idempotency_key: str = "",
    ) -> Task:
        with self._lock:
            return self._create_task_impl(
                title=title,
                repository=repository,
                executor_kind=executor_kind,
                model_profile_ref=model_profile_ref,
                permission_profile=permission_profile,
                policy_ref=policy_ref,
                workspace=workspace,
                branch=branch,
                idempotency_key=idempotency_key,
            )

    def _create_task_impl(
        self,
        *,
        title: str,
        repository: str,
        executor_kind: str,
        model_profile_ref: str,
        permission_profile: str,
        policy_ref: str,
        workspace: str,
        branch: str,
        idempotency_key: str,
    ) -> Task:
        if idempotency_key:
            existing = self._conn.execute(
                "SELECT task_id, title, repository, executor_kind FROM "
                "idempotency_keys WHERE key = ? LIMIT 1",
                (idempotency_key,),
            ).fetchone()
            if existing:
                if (
                    existing["title"] == title
                    and existing["repository"] == repository
                    and existing["executor_kind"] == executor_kind
                ):
                    return self.get_task(existing["task_id"])
                raise DuplicateTaskError(
                    f"idempotency_key_reused_with_different_request:{idempotency_key}"
                )

        now = _utc_now()
        now_ms = _utc_now_ms()
        task_id = f"task-{now_ms}-{_short_uuid()}"
        execution_id = f"exec-{task_id}"
        self._conn.execute(
            """
            INSERT INTO tasks (
                id, title, repository, status, executor_kind, execution_id,
                model_profile_ref, permission_profile, policy_ref, workspace,
                branch, created_at, updated_at, failure_classification,
                failure_detail, validation_command_id, validation_exit_code,
                validation_output_digest, idempotency_key
            ) VALUES (?, ?, ?, 'QUEUED', ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', NULL, '', ?)
            """,
            (
                task_id,
                title,
                repository,
                executor_kind,
                execution_id,
                model_profile_ref,
                permission_profile,
                policy_ref,
                workspace,
                branch,
                now,
                now,
                idempotency_key,
            ),
        )
        if idempotency_key:
            self._conn.execute(
                "INSERT INTO idempotency_keys "
                "(key, task_id, title, repository, executor_kind, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    idempotency_key,
                    task_id,
                    title,
                    repository,
                    executor_kind,
                    now,
                ),
            )

        self._append_event(
            task_id=task_id,
            event_type="DISCOVERED",
            title="Task queued",
            description=f"Task created for {repository}",
            metadata={"executor_kind": executor_kind, "status": "QUEUED"},
        )
        return _row_to_task(self._conn, self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,),
        ).fetchone())

    def create_task_and_execute(
        self,
        *,
        create_kwargs: dict[str, Any],
        executor_runner: Any,
    ) -> tuple[Task, Any]:
        with self._lock:
            task = self.create_task(**create_kwargs)
            self.transition_to(task.id, "PREPARING_WORKSPACE")
            self.transition_to(task.id, "RUNNING_FIXTURE")
            self._append_event(
                task_id=task.id,
                event_type="EXECUTOR_RUNNING",
                title="Executor running",
                description=f"Executor {task.executor_kind} started",
                metadata={"executor_kind": task.executor_kind},
            )
            result = executor_runner(task.id, self)
            self._append_event(
                task_id=task.id,
                event_type="EXECUTOR_FINISHED",
                title="Executor finished",
                description="Executor completed",
                metadata={
                    "success": bool(result.get("success")) if isinstance(result, dict) else False,
                },
            )
            return task, result

    def get_task(self, task_id: str) -> Task:
        with self._lock:
            try:
                row = self._conn.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,),
                ).fetchone()
            except sqlite3.ProgrammingError as exc:
                raise TaskStoreError(f"task_lookup_error:{task_id}") from exc
            if row is None:
                raise TaskStoreError(f"task_not_found:{task_id}")
            return _row_to_task(self._conn, row)

    def list_tasks(self, limit: int = 100, offset: int = 0) -> list[Task]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [_row_to_task(self._conn, r) for r in rows]

    def count_tasks(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()
            return int(row["c"])

    def find_by_idempotency_key(self, key: str) -> Task | None:
        with self._lock:
            if not key:
                return None
            row = self._conn.execute(
                "SELECT ik.task_id FROM idempotency_keys ik "
                "WHERE ik.key = ? LIMIT 1",
                (key,),
            ).fetchone()
            if row is None:
                return None
            return self.get_task(row["task_id"])

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def set_state(self, task_id: str, status: str) -> Task:
        with self._lock:
            if status not in TASK_STATUS_ORDER:
                raise TaskStoreError(f"invalid_status:{status}")
            self._update_task_fields(task_id, {"status": status})
            return self.get_task(task_id)

    def transition_to(self, task_id: str, status: str) -> Task:
        with self._lock:
            if status not in TASK_STATUS_ORDER:
                raise TaskStoreError(f"invalid_status:{status}")
            current = self.get_task(task_id)
            if current.status == status:
                return current
            allowed = TRANSITION_RULES.get(current.status, ())
            if status not in allowed:
                raise InvalidTransitionError(
                    f"invalid_transition:{current.status}->{status} "
                    f"allowed={allowed}"
                )
            if current.status in TERMINAL_STATUSES:
                raise InvalidTransitionError(
                    f"terminal_status:{current.status}"
                )
            self._update_task_fields(task_id, {"status": status})
            return self.get_task(task_id)

    def classify_failure(
        self,
        task_id: str,
        *,
        classification: str,
        detail: str = "",
    ) -> Task:
        with self._lock:
            task = self.get_task(task_id)
            if task.status in TERMINAL_STATUSES:
                raise TaskStoreError(f"terminal_status:{task.status}")
            self._update_task_fields(
                task_id,
                {
                    "failure_classification": classification,
                    "failure_detail": detail,
                },
            )
            target = "BLOCKED" if classification == "blocked" else "FAILED"
            if task.status != target:
                self._update_task_fields(task_id, {"status": target})
            self._append_event(
                task_id=task_id,
            event_type="EXECUTOR_FINISHED",
            title="Executor failed",
            description=f"failure_classification={classification}",
            metadata={"failure_classification": classification, "detail": detail},
        )
        return self.get_task(task_id)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def add_event(
        self,
        task_id: str,
        *,
        event_type: str,
        title: str,
        description: str = "",
        raw_log: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> TaskEvent:
        with self._lock:
            self.get_task(task_id)
            return self._append_event(
                task_id=task_id,
                event_type=event_type,
                title=title,
                description=description,
                raw_log=raw_log,
                metadata=metadata,
            )

    def get_events(self, task_id: str) -> list[TaskEvent]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, task_id, type, timestamp, title, description, raw_log, "
                "metadata FROM task_events WHERE task_id = ? ORDER BY seq ASC",
                (task_id,),
            ).fetchall()
            return [
                TaskEvent(
                    id=r["id"],
                    task_id=r["task_id"],
                    type=r["type"],
                    timestamp=r["timestamp"],
                    title=r["title"],
                    description=r["description"],
                    raw_log=r["raw_log"],
                    metadata=dict(self._decode_json(r["metadata"])),
                )
                for r in rows
            ]

    def _append_event(
        self,
        *,
        task_id: str,
        event_type: str,
        title: str,
        description: str,
        raw_log: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> TaskEvent:
        if event_type not in VALID_EVENT_TYPES:
            raise TaskStoreError(f"invalid_event_type:{event_type}")
        now = _utc_now()
        event_id = f"event-{task_id}-{_short_uuid()}"
        meta_json = json_dumps_stable(metadata or {})
        self._conn.execute(
            "INSERT INTO task_events "
            "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, task_id, event_type, now, title, description, raw_log, meta_json),
        )
        self._update_task_fields(task_id, {"updated_at": now})
        return TaskEvent(
            id=event_id,
            task_id=task_id,
            type=event_type,
            timestamp=now,
            title=title,
            description=description,
            raw_log=raw_log,
            metadata=dict(metadata or {}),
        )

    # ------------------------------------------------------------------
    # Changed files and evidence
    # ------------------------------------------------------------------

    def set_changed_files(self, task_id: str, files: Sequence[Mapping[str, Any]]) -> Task:
        with self._lock:
            self.get_task(task_id)
            self._conn.execute("DELETE FROM task_changed_files WHERE task_id = ?", (task_id,))
            for idx, f in enumerate(files, start=1):
                self._conn.execute(
                    "INSERT INTO task_changed_files "
                    "(task_id, path, status, additions, deletions, diff_digest) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        str(f.get("path", "")),
                        str(f.get("status", "modified")),
                        int(f.get("additions", 0)),
                        int(f.get("deletions", 0)),
                        str(f.get("diff_digest", "")),
                    ),
                )
            self._update_task_fields(task_id, {"updated_at": _utc_now()})
            return self.get_task(task_id)

    def add_evidence(
        self,
        task_id: str,
        *,
        category: str,
        label: str,
        value: str,
        status: str,
        detail: str = "",
        raw_json_digest: str = "",
    ) -> Task:
        with self._lock:
            self.get_task(task_id)
            ev_id = f"ev-{task_id}-{_short_uuid()}"
            self._conn.execute(
                "INSERT INTO task_evidence "
                "(id, task_id, category, label, value, status, detail, raw_json_digest) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ev_id, task_id, category, label, value, status, detail, raw_json_digest),
            )
            self._update_task_fields(task_id, {"updated_at": _utc_now()})
            return self.get_task(task_id)

    def set_validation_result(
        self,
        task_id: str,
        *,
        command_id: str,
        exit_code: int,
        output_digest: str,
    ) -> Task:
        with self._lock:
            self.get_task(task_id)
            self._update_task_fields(
                task_id,
                {
                    "validation_command_id": command_id,
                    "validation_exit_code": exit_code,
                    "validation_output_digest": output_digest,
                },
            )
            return self.get_task(task_id)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _update_task_fields(self, task_id: str, fields: Mapping[str, Any]) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [
            _utc_now(),
            task_id,
        ]
        self._conn.execute(
            f"UPDATE tasks SET {sets}, updated_at = ? WHERE id = ?",
            values,
        )

    def _decode_json(self, raw: str) -> dict[str, Any]:
        if not raw:
            return {}
        return json_loads_stable(raw)


def json_dumps_stable(obj: Any) -> str:
    """Deterministic, compact JSON serialization for SQLite storage."""

    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_loads_stable(raw: str) -> Any:
    import json

    return json.loads(raw) if raw else {}
