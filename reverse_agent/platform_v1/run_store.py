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
    "INTERRUPTED",
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
        "INTERRUPTED",
    ),
    "RUNNING": (
        "VALIDATING",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
        "INTERRUPTED",
    ),
    "RUNNING_FIXTURE": (
        "VALIDATING",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
        "INTERRUPTED",
    ),
    "VALIDATING": (
        "READY_FOR_REVIEW",
        "READY_FOR_REVIEW_FIXTURE",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
        "INTERRUPTED",
    ),
    "INTERRUPTED": (
        "RUNNING",
        "RUNNING_FIXTURE",
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
    binding_ref: str
    permission_profile: str
    policy_ref: str
    workspace: str
    branch: str
    created_at: str
    updated_at: str
    orchestration_mode: str = "single"
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
        binding_ref=row["binding_ref"],
        permission_profile=row["permission_profile"],
        policy_ref=row["policy_ref"],
        workspace=row["workspace"],
        branch=row["branch"],
        orchestration_mode=row["orchestration_mode"] or "single",
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
                binding_ref TEXT NOT NULL DEFAULT '',
                permission_profile TEXT NOT NULL,
                policy_ref TEXT NOT NULL,
                workspace TEXT NOT NULL,
                branch TEXT NOT NULL,
                orchestration_mode TEXT NOT NULL DEFAULT 'single',
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
            CREATE TABLE IF NOT EXISTS durable_runs (
                run_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                execution_id TEXT NOT NULL,
                execution_authority_sha TEXT NOT NULL DEFAULT '',
                planning_sha TEXT NOT NULL DEFAULT '',
                repository_base_sha TEXT NOT NULL DEFAULT '',
                worktree_path TEXT NOT NULL,
                worktree_head_sha TEXT NOT NULL DEFAULT '',
                worktree_prepared_at TEXT NOT NULL DEFAULT '',
                current_role TEXT NOT NULL DEFAULT '',
                role_attempt INTEGER NOT NULL DEFAULT 1,
                accepted_checkpoint TEXT NOT NULL DEFAULT '',
                planner_handoff_digest TEXT NOT NULL DEFAULT '',
                coder_product_diff_digest TEXT NOT NULL DEFAULT '',
                reviewer_handoff_digest TEXT NOT NULL DEFAULT '',
                partial_coder_diff_digest TEXT NOT NULL DEFAULT '',
                validation_command_id TEXT NOT NULL DEFAULT '',
                validation_exit_code INTEGER,
                validation_output_digest TEXT NOT NULL DEFAULT '',
                lease_owner TEXT NOT NULL DEFAULT '',
                lease_epoch INTEGER NOT NULL DEFAULT 0,
                heartbeat_at_ms INTEGER NOT NULL DEFAULT 0,
                lease_expiry_ms INTEGER NOT NULL DEFAULT 0,
                recovery_classification TEXT NOT NULL DEFAULT 'normal',
                interrupted_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS durable_checkpoint_history (
                checkpoint_id TEXT NOT NULL,
                run_id TEXT NOT NULL REFERENCES durable_runs(run_id),
                checkpoint_name TEXT NOT NULL,
                artifact_digest TEXT NOT NULL,
                role_attempt INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                seq INTEGER PRIMARY KEY AUTOINCREMENT
            );
            CREATE TABLE IF NOT EXISTS durable_external_operations (
                operation_id TEXT PRIMARY KEY,
                operation_key TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                request_digest TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'PENDING',
                external_operation_id TEXT NOT NULL DEFAULT '',
                result_state TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        task_columns = {
            row["name"] for row in self._conn.execute("PRAGMA table_info(tasks)")
        }
        if "binding_ref" not in task_columns:
            self._conn.execute(
                "ALTER TABLE tasks ADD COLUMN binding_ref TEXT NOT NULL DEFAULT ''"
            )
        if "orchestration_mode" not in task_columns:
            self._conn.execute(
                "ALTER TABLE tasks ADD COLUMN orchestration_mode TEXT NOT NULL DEFAULT 'single'"
            )

        run_columns = {
            row["name"] for row in self._conn.execute("PRAGMA table_info(durable_runs)")
        }
        for col, dtype in [
            ("execution_authority_sha", "TEXT NOT NULL DEFAULT ''"),
            ("planning_sha", "TEXT NOT NULL DEFAULT ''"),
            ("worktree_head_sha", "TEXT NOT NULL DEFAULT ''"),
            ("worktree_prepared_at", "TEXT NOT NULL DEFAULT ''"),
            ("partial_coder_diff_digest", "TEXT NOT NULL DEFAULT ''"),
        ]:
            if col not in run_columns:
                self._conn.execute(f"ALTER TABLE durable_runs ADD COLUMN {col} {dtype}")

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
        binding_ref: str = "",
        permission_profile: str = "ASK_FOR_APPROVAL",
        policy_ref: str = "",
        workspace: str = "",
        branch: str = "",
        idempotency_key: str = "",
        orchestration_mode: str = "single",
    ) -> Task:
        with self._lock:
            return self._create_task_impl(
                title=title,
                repository=repository,
                executor_kind=executor_kind,
                model_profile_ref=model_profile_ref,
                binding_ref=binding_ref,
                permission_profile=permission_profile,
                policy_ref=policy_ref,
                workspace=workspace,
                branch=branch,
                idempotency_key=idempotency_key,
                orchestration_mode=orchestration_mode,
            )

    def _create_task_impl(
        self,
        *,
        title: str,
        repository: str,
        executor_kind: str,
        model_profile_ref: str,
        binding_ref: str,
        permission_profile: str,
        policy_ref: str,
        workspace: str,
        branch: str,
        idempotency_key: str,
        orchestration_mode: str = "single",
    ) -> Task:
        if orchestration_mode not in ("single", "sequential_team"):
            raise TaskStoreError(f"unsupported_orchestration_mode:{orchestration_mode}")
        if orchestration_mode == "sequential_team" and executor_kind != "opencode":
            raise TaskStoreError(
                "sequential_team_requires_opencode_executor"
            )
        if binding_ref and executor_kind != "opencode":
            raise TaskStoreError("binding_ref_requires_opencode_executor")
        if idempotency_key:
            existing = self._conn.execute(
                "SELECT keys_table.task_id, keys_table.title, keys_table.repository, "
                "keys_table.executor_kind, tasks.binding_ref, tasks.orchestration_mode "
                "FROM idempotency_keys "
                "AS keys_table JOIN tasks ON tasks.id = keys_table.task_id "
                "WHERE keys_table.key = ? LIMIT 1",
                (idempotency_key,),
            ).fetchone()
            if existing:
                if (
                    existing["title"] == title
                    and existing["repository"] == repository
                    and existing["executor_kind"] == executor_kind
                    and existing["binding_ref"] == binding_ref
                    and existing["orchestration_mode"] == orchestration_mode
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
                model_profile_ref, binding_ref, permission_profile, policy_ref, workspace,
                branch, orchestration_mode, created_at, updated_at, failure_classification,
                failure_detail, validation_command_id, validation_exit_code,
                validation_output_digest, idempotency_key
            ) VALUES (?, ?, ?, 'QUEUED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', NULL, '', ?)
            """,
            (
                task_id,
                title,
                repository,
                executor_kind,
                execution_id,
                model_profile_ref,
                binding_ref,
                permission_profile,
                policy_ref,
                workspace,
                branch,
                orchestration_mode,
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
        task = self.create_task(**create_kwargs)
        self.transition_to(task.id, "PREPARING_WORKSPACE")
        self.transition_to(task.id, "RUNNING_FIXTURE")
        self.add_event(
            task.id,
            event_type="EXECUTOR_RUNNING",
            title="Executor running",
            description=f"Executor {task.executor_kind} started",
            metadata={"executor_kind": task.executor_kind},
        )
        result = executor_runner(task.id, self)
        self.add_event(
            task.id,
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

    # ------------------------------------------------------------------
    # Durable run management (Level-1)
    # ------------------------------------------------------------------

    def _acquire_durable_lease(
        self,
        *,
        task_id: str,
        execution_id: str,
        lease_owner: str,
        repository_base_sha: str = "",
        worktree_path: str = "",
    ) -> Any:
        """Acquire a new durable lease with epoch=1.

        Creates the durable_run record and returns a LeaseHandle-like dict.
        Fails closed if an active run already exists for the task.
        """
        with self._lock:
            task = self.get_task(task_id)
            existing = self._find_active_durable_run(task_id)
            if existing is not None:
                raise TaskStoreError(
                    f"durable_run_already_active:{task_id}"
                )
            now = _utc_now()
            now_ms = _utc_now_ms()
            run_id = f"run-{task_id}-{_short_uuid()}"
            self._conn.execute(
                "INSERT INTO durable_runs "
                "(run_id, task_id, execution_id, execution_authority_sha, planning_sha, "
                "repository_base_sha, worktree_path, worktree_head_sha, worktree_prepared_at, "
                "current_role, role_attempt, accepted_checkpoint, "
                "planner_handoff_digest, coder_product_diff_digest, reviewer_handoff_digest, "
                "partial_coder_diff_digest, "
                "validation_command_id, validation_exit_code, validation_output_digest, "
                "lease_owner, lease_epoch, heartbeat_at_ms, lease_expiry_ms, "
                "recovery_classification, interrupted_at, created_at, updated_at) "
                "VALUES (?, ?, ?, '', '', ?, ?, '', '', ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id, task_id, execution_id, repository_base_sha, worktree_path,
                    "", 1, "", "", "", "",
                    "", None, "", lease_owner, 1, now_ms, now_ms + 300000,
                    "normal", "", now, now,
                ),
            )
            self._update_task_fields(task_id, {"status": "RUNNING"})
            return self._lease_handle_from_row(
                self._conn.execute(
                    "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
                ).fetchone()
            )

    def _find_active_durable_run(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT dr.*, t.status FROM durable_runs dr "
                "JOIN tasks t ON t.id = dr.task_id "
                "WHERE dr.task_id = ? "
                "AND t.status NOT IN ('READY_FOR_REVIEW', 'READY_FOR_REVIEW_FIXTURE', "
                "'FAILED', 'BLOCKED', 'CANCELLED') "
                "ORDER BY dr.created_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
            if row is None:
                return None
            return dict(row)

    def _get_durable_run(self, run_id: str) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            return _row_to_durable_run(row)

    def _recover_durable_lease(
        self, run_id: str, lease_owner: str
    ) -> Any:
        """Recover a durable lease with a strictly larger epoch.

        Every recovery creates a strictly newer epoch, even if the owner
        label matches the previous owner. Owner-label equality is NOT proof
        that the worker is the same instance. Epoch is the fencing token.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            existing_epoch = int(row["lease_epoch"])
            new_epoch = existing_epoch + 1
            now_ms = _utc_now_ms()
            self._conn.execute(
                "UPDATE durable_runs SET "
                "lease_owner = ?, lease_epoch = ?, heartbeat_at_ms = ?, "
                "lease_expiry_ms = ?, updated_at = ? "
                "WHERE run_id = ?",
                (lease_owner, new_epoch, now_ms, now_ms + 300000, _utc_now(), run_id),
            )
            return self._lease_handle_from_row(
                self._conn.execute(
                    "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
                ).fetchone()
            )

    def _validate_durable_lease(
        self, run_id: str, owner: str, epoch: int
    ) -> None:
        """Validate that the given owner/epoch is still the active lease.

        Raises TaskStoreError if the lease has been superseded (stale fencing).
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            current_epoch = int(row["lease_epoch"])
            current_owner = row["lease_owner"]
            if current_epoch != epoch or current_owner != owner:
                raise TaskStoreError(
                    f"lease_fenced:{run_id}:owner={owner}:epoch={epoch} "
                    f"current_owner={current_owner}:current_epoch={current_epoch}"
                )

    def _heartbeat_durable_lease(
        self, run_id: str, owner: str, epoch: int
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            now_ms = _utc_now_ms()
            self._conn.execute(
                "UPDATE durable_runs SET heartbeat_at_ms = ?, "
                "lease_expiry_ms = ?, updated_at = ? "
                "WHERE run_id = ?",
                (now_ms, now_ms + 300000, _utc_now(), run_id),
            )

    def _release_durable_lease(self, run_id: str) -> None:
        """Release active ownership. MUST NOT reset or decrease epoch.

        The highest epoch for a durable run is monotonic for the run's
        lifetime. Release only clears active ownership; the epoch remains
        so that any late-arriving old worker is fenced.
        """
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET lease_owner = '', "
                "lease_expiry_ms = 0, updated_at = ? WHERE run_id = ?",
                (_utc_now(), run_id),
            )

    def _accept_checkpoint(
        self,
        run_id: str,
        checkpoint_name: str,
        artifact_digest: str,
        role_attempt: int,
        owner: str,
        epoch: int,
    ) -> Any:
        """Accept a checkpoint (append-only, idempotent). Never overwrite a completed checkpoint.

        Idempotency: if the same checkpoint already exists in history with
        the same accepted state, return the existing record without inserting
        a duplicate. Backward checkpoints always fail. Forward progression
        always inserts a new record.
        """
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            run_row = self._conn.execute(
                "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
            ).fetchone()
            if run_row is None:
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            current_accepted = run_row["accepted_checkpoint"]
            current_rank = _CHECKPOINT_INDEX.get(current_accepted, -1)
            new_rank = _CHECKPOINT_INDEX.get(checkpoint_name, -1)
            if new_rank < 0:
                raise TaskStoreError(f"invalid_checkpoint_name:{checkpoint_name}")
            if new_rank < current_rank:
                raise TaskStoreError(
                    f"checkpoint_sequence_regression:"
                    f"{current_accepted}->{checkpoint_name}"
                )
            if new_rank > current_rank + 1 and current_rank >= 0:
                raise TaskStoreError(
                    f"checkpoint_sequence_jump:"
                    f"{current_accepted}->{checkpoint_name}"
                )

            # Idempotency: if already accepted at this rank, return existing record
            if new_rank == current_rank:
                existing = self._conn.execute(
                    "SELECT * FROM durable_checkpoint_history "
                    "WHERE run_id = ? AND checkpoint_name = ? "
                    "ORDER BY seq DESC LIMIT 1",
                    (run_id, checkpoint_name),
                ).fetchone()
                if existing is not None:
                    return DurableCheckpoint(
                        checkpoint_id=existing["checkpoint_id"],
                        run_id=existing["run_id"],
                        checkpoint_name=existing["checkpoint_name"],
                        artifact_digest=existing["artifact_digest"],
                        role_attempt=int(existing["role_attempt"]),
                        created_at=existing["created_at"],
                    )

            cp_id = f"cp-{run_id}-{_short_uuid()}"
            self._conn.execute(
                "INSERT INTO durable_checkpoint_history "
                "(checkpoint_id, run_id, checkpoint_name, artifact_digest, "
                "role_attempt, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (cp_id, run_id, checkpoint_name, artifact_digest, role_attempt, _utc_now()),
            )

            self._conn.execute(
                "UPDATE durable_runs SET "
                "accepted_checkpoint = ?, "
                "current_role = ?, "
                "updated_at = ? "
                "WHERE run_id = ?",
                (
                    checkpoint_name,
                    _checkpoint_to_role(checkpoint_name),
                    _utc_now(),
                    run_id,
                ),
            )

            return DurableCheckpoint(
                checkpoint_id=cp_id,
                run_id=run_id,
                checkpoint_name=checkpoint_name,
                artifact_digest=artifact_digest,
                role_attempt=role_attempt,
                created_at=_utc_now(),
            )

    def _get_durable_checkpoints(self, run_id: str) -> tuple[Any, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM durable_checkpoint_history "
                "WHERE run_id = ? ORDER BY seq ASC",
                (run_id,),
            ).fetchall()
            return tuple(
                DurableCheckpoint(
                    checkpoint_id=r["checkpoint_id"],
                    run_id=r["run_id"],
                    checkpoint_name=r["checkpoint_name"],
                    artifact_digest=r["artifact_digest"],
                    role_attempt=int(r["role_attempt"]),
                    created_at=r["created_at"],
                )
                for r in rows
            )

    def _set_planner_handoff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET planner_handoff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_coder_product_diff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET coder_product_diff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_reviewer_handoff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET reviewer_handoff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_role_attempt(
        self, run_id: str, role: str, attempt: int,
        owner: str, epoch: int,
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET current_role = ?, role_attempt = ?, "
                "updated_at = ? WHERE run_id = ?",
                (role, attempt, _utc_now(), run_id),
            )

    def _set_recovery_classification(
        self, run_id: str, classification: str, owner: str, epoch: int
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET recovery_classification = ?, "
                "updated_at = ? WHERE run_id = ?",
                (classification, _utc_now(), run_id),
            )

    def _set_validation_result(
        self,
        run_id: str,
        *,
        command_id: str,
        exit_code: int,
        output_digest: str,
        owner: str,
        epoch: int,
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET "
                "validation_command_id = ?, validation_exit_code = ?, "
                "validation_output_digest = ?, updated_at = ? "
                "WHERE run_id = ?",
                (command_id, exit_code, output_digest, _utc_now(), run_id),
            )

    def _external_operation_prevents_dispatch(
        self, idempotency_key: str, request_digest: str
    ) -> bool:
        """Return True if dispatch should be prevented (operation already exists/succeeded).

        This implements idempotency semantics: if an operation with the same
        idempotency key already reached SUCCESS or RECONCILED state, prevent
        duplicate dispatch. If the key doesn't exist, dispatch is allowed.
        """
        with self._lock:
            if not idempotency_key:
                return False
            row = self._conn.execute(
                "SELECT state, request_digest FROM durable_external_operations "
                "WHERE idempotency_key = ? ORDER BY created_at DESC LIMIT 1",
                (idempotency_key,),
            ).fetchone()
            if row is None:
                return False
            if row["request_digest"] != request_digest:
                return False
            return row["state"] in ("SUCCESS", "RECONCILED")

    def _record_external_operation(
        self,
        *,
        operation_key: str,
        idempotency_key: str,
        request_digest: str,
    ) -> Any:
        """Record an external operation BEFORE dispatch.

        If an existing operation with the same idempotency key is found,
        return it (idempotency).
        """
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM durable_external_operations "
                "WHERE idempotency_key = ? AND request_digest = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (idempotency_key, request_digest),
            ).fetchone()
            if existing is not None:
                return _row_to_external_operation(dict(existing))
            now = _utc_now()
            op_id = f"op-{_short_uuid()}"
            self._conn.execute(
                "INSERT INTO durable_external_operations "
                "(operation_id, operation_key, idempotency_key, request_digest, "
                "state, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'PENDING', ?, ?)",
                (op_id, operation_key, idempotency_key, request_digest, now, now),
            )
            row = self._conn.execute(
                "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                (op_id,),
            ).fetchone()
            return _row_to_external_operation(dict(row))

    def _reconcile_external_operation(
        self,
        *,
        operation_id: str,
        external_operation_id: str,
        result_state: str,
    ) -> Any:
        """Reconcile an external operation with the result of a dispatch."""
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"external_operation_not_found:{operation_id}")
            self._conn.execute(
                "UPDATE durable_external_operations SET "
                "external_operation_id = ?, result_state = ?, "
                "state = ?, updated_at = ? "
                "WHERE operation_id = ?",
                (
                    external_operation_id, result_state,
                    "SUCCESS" if result_state == "success" else "RECONCILED",
                    _utc_now(), operation_id,
                ),
            )
            updated = self._conn.execute(
                "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            return _row_to_external_operation(dict(updated))

    def _reconcile_expired_runs(
        self,
        *,
        now_ms: int,
        max_age_ms: int,
    ) -> tuple[dict[str, Any], ...]:
        """Find expired active run leases, mark stale tasks INTERRUPTED.

        Does NOT automatically launch models. Returns reconciliation records.
        """
        with self._lock:
            runs = self._conn.execute(
                "SELECT dr.*, t.status as task_status FROM durable_runs dr "
                "JOIN tasks t ON t.id = dr.task_id "
                "WHERE dr.lease_expiry_ms > 0 "
                "AND dr.lease_expiry_ms < ? "
                "AND t.status IN ('PREPARING_WORKSPACE', 'RUNNING', "
                "'RUNNING_FIXTURE', 'VALIDATING') "
                "ORDER BY dr.created_at ASC",
                (now_ms,),
            ).fetchall()
            records: list[dict[str, Any]] = []
            for row in runs:
                run_id = row["run_id"]
                task_id = row["task_id"]
                task_status = row["task_status"]
                self._conn.execute(
                    "UPDATE durable_runs SET "
                    "recovery_classification = 'orphan_stale_lease', "
                    "interrupted_at = ?, updated_at = ? "
                    "WHERE run_id = ?",
                    (_utc_now(), _utc_now(), run_id),
                )
                try:
                    self._update_task_fields(task_id, {"status": "INTERRUPTED"})
                    self._append_event(
                        task_id=task_id,
                        event_type="EXECUTOR_FINISHED",
                        title="Durable run interrupted",
                        description=f"lease expired, reconciled to INTERRUPTED",
                        metadata={
                            "run_id": run_id,
                            "recovery_classification": "orphan_stale_lease",
                            "previous_status": task_status,
                        },
                    )
                except (InvalidTransitionError, TaskStoreError):
                    pass
                records.append({
                    "run_id": run_id,
                    "task_id": task_id,
                    "previous_status": task_status,
                    "recovery_classification": "orphan_stale_lease",
                })
            return tuple(records)

    def _lease_handle_from_row(self, row: sqlite3.Row) -> Any:
        return LeaseHandle(
            run_id=row["run_id"],
            task_id=row["task_id"],
            execution_id=row["execution_id"],
            owner=row["lease_owner"],
            epoch=int(row["lease_epoch"]),
            expiry_ms=int(row["lease_expiry_ms"]),
            worktree_path=row["worktree_path"],
            repository_base_sha=row["repository_base_sha"],
        )

    def _set_worktree_identity(
        self, run_id: str, worktree_path: str, worktree_head_sha: str,
        owner: str, epoch: int,
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET "
                "worktree_path = ?, worktree_head_sha = ?, "
                "worktree_prepared_at = ?, updated_at = ? "
                "WHERE run_id = ?",
                (worktree_path, worktree_head_sha, _utc_now(), _utc_now(), run_id),
            )

    def _set_authority_identity(
        self, run_id: str, execution_authority_sha: str,
        planning_sha: str, owner: str, epoch: int,
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET "
                "execution_authority_sha = ?, planning_sha = ?, "
                "updated_at = ? WHERE run_id = ?",
                (execution_authority_sha, planning_sha, _utc_now(), run_id),
            )

    def _set_partial_coder_diff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int,
    ) -> None:
        self._validate_durable_lease(run_id, owner, epoch)
        with self._lock:
            self._conn.execute(
                "UPDATE durable_runs SET partial_coder_diff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )


class LeaseHandle:
    """Immutable lease handle returned by durable lease operations."""
    __slots__ = (
        "run_id", "task_id", "execution_id", "owner", "epoch",
        "expiry_ms", "worktree_path", "repository_base_sha",
    )
    def __init__(
        self,
        *,
        run_id: str,
        task_id: str,
        execution_id: str,
        owner: str,
        epoch: int,
        expiry_ms: int,
        worktree_path: str,
        repository_base_sha: str,
    ) -> None:
        self.run_id = run_id
        self.task_id = task_id
        self.execution_id = execution_id
        self.owner = owner
        self.epoch = epoch
        self.expiry_ms = expiry_ms
        self.worktree_path = worktree_path
        self.repository_base_sha = repository_base_sha


class DurableCheckpoint:
    """Immutable durable checkpoint record."""
    __slots__ = (
        "checkpoint_id", "run_id", "checkpoint_name",
        "artifact_digest", "role_attempt", "created_at",
    )
    def __init__(
        self,
        *,
        checkpoint_id: str,
        run_id: str,
        checkpoint_name: str,
        artifact_digest: str,
        role_attempt: int,
        created_at: str,
    ) -> None:
        self.checkpoint_id = checkpoint_id
        self.run_id = run_id
        self.checkpoint_name = checkpoint_name
        self.artifact_digest = artifact_digest
        self.role_attempt = role_attempt
        self.created_at = created_at


# ---------------------------------------------------------------------------
# Durable run row helpers
# ---------------------------------------------------------------------------

_ACCEPTED_CHECKPOINTS = frozenset({
    "PRE_PLANNER", "POST_PLANNER", "POST_CODER",
    "POST_REVIEWER", "POST_VALIDATION",
})
_CHECKPOINT_INDEX: dict[str, int] = {
    "PRE_PLANNER": 0, "POST_PLANNER": 1, "POST_CODER": 2,
    "POST_REVIEWER": 3, "POST_VALIDATION": 4,
}

def _checkpoint_to_role(checkpoint_name: str) -> str:
    role_map = {
        "PRE_PLANNER": "planner",
        "POST_PLANNER": "coder",
        "POST_CODER": "reviewer",
        "POST_REVIEWER": "verifier",
        "POST_VALIDATION": "complete",
    }
    return role_map.get(checkpoint_name, "")


def _row_to_durable_run(row: sqlite3.Row) -> Any:
    from dataclasses import dataclass
    cols = set(row.keys())
    @dataclass(frozen=True)
    class DurableRun:
        run_id: str
        task_id: str
        execution_id: str
        execution_authority_sha: str
        planning_sha: str
        repository_base_sha: str
        worktree_path: str
        worktree_head_sha: str
        worktree_prepared_at: str
        current_role: str
        role_attempt: int
        accepted_checkpoint: str
        planner_handoff_digest: str
        coder_product_diff_digest: str
        reviewer_handoff_digest: str
        partial_coder_diff_digest: str
        validation_command_id: str
        validation_exit_code: int | None
        validation_output_digest: str
        lease_owner: str
        lease_epoch: int
        heartbeat_at_ms: int
        lease_expiry_ms: int
        recovery_classification: str
        interrupted_at: str
        created_at: str
        updated_at: str
    return DurableRun(
        run_id=row["run_id"],
        task_id=row["task_id"],
        execution_id=row["execution_id"],
        execution_authority_sha=row["execution_authority_sha"] if "execution_authority_sha" in cols else "",
        planning_sha=row["planning_sha"] if "planning_sha" in cols else "",
        repository_base_sha=row["repository_base_sha"],
        worktree_path=row["worktree_path"],
        worktree_head_sha=row["worktree_head_sha"] if "worktree_head_sha" in cols else "",
        worktree_prepared_at=row["worktree_prepared_at"] if "worktree_prepared_at" in cols else "",
        current_role=row["current_role"],
        role_attempt=int(row["role_attempt"]),
        accepted_checkpoint=row["accepted_checkpoint"],
        planner_handoff_digest=row["planner_handoff_digest"],
        coder_product_diff_digest=row["coder_product_diff_digest"],
        reviewer_handoff_digest=row["reviewer_handoff_digest"],
        partial_coder_diff_digest=row["partial_coder_diff_digest"] if "partial_coder_diff_digest" in cols else "",
        validation_command_id=row["validation_command_id"],
        validation_exit_code=row["validation_exit_code"],
        validation_output_digest=row["validation_output_digest"],
        lease_owner=row["lease_owner"],
        lease_epoch=int(row["lease_epoch"]),
        heartbeat_at_ms=int(row["heartbeat_at_ms"]),
        lease_expiry_ms=int(row["lease_expiry_ms"]),
        recovery_classification=row["recovery_classification"],
        interrupted_at=row["interrupted_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_external_operation(row: dict[str, Any]) -> Any:
    from dataclasses import dataclass
    @dataclass(frozen=True)
    class ExternalOperation:
        operation_id: str
        operation_key: str
        idempotency_key: str
        request_digest: str
        state: str
        external_operation_id: str
        result_state: str
        created_at: str
        updated_at: str
    return ExternalOperation(
        operation_id=row["operation_id"],
        operation_key=row["operation_key"],
        idempotency_key=row["idempotency_key"],
        request_digest=row["request_digest"],
        state=row["state"],
        external_operation_id=row["external_operation_id"],
        result_state=row["result_state"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _checkpoint_rank_lookup(value: str) -> int:
    return _CHECKPOINT_INDEX.get(value, -1)


def json_dumps_stable(obj: Any) -> str:
    """Deterministic, compact JSON serialization for SQLite storage."""

    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_loads_stable(raw: str) -> Any:
    import json

    return json.loads(raw) if raw else {}
