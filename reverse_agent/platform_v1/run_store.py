"""Server-owned SQLite task and event store for Platform V1.

Task/run truth lives in the trusted loopback Task API, not in the React Query
cache. Every task carries a server-generated id, and every lifecycle change
is recorded as an append-only event so the task can be re-read after a
crash or server restart and still reconstruct its full history.

Idempotency keys are enforced at the store layer: creating a task with an
idempotency key that already exists returns the existing task instead of
creating a duplicate.

Durable-path mutations MUST be fenced: owner+epoch validation and the
actual mutation occur under the SAME TaskStore lock boundary. Public
non-durable APIs (transition_to, set_changed_files, add_event, etc.)
remain backward-compatible for single/normal execution paths.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
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


def _is_truthy_id(value: str | None) -> bool:
    return value is not None and value.strip() != ""


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


@dataclass(frozen=True)
class UsageObservation:
    """Sanitized numeric model-usage fact; never contains a raw executor event."""

    id: str
    task_id: str
    window_id: str
    claim_epoch: int
    execution_id: str
    role: str
    model_id: str
    provider_id: str
    source_kind: str
    source_id: str
    status: str
    input_units: int | None
    output_units: int | None
    reasoning_units: int | None
    cache_read_units: int | None
    cache_write_units: int | None
    cost_micro_units: int | None
    payload_digest: str
    created_at: str


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class TaskStoreError(Exception):
    """Raised on store-level failures (schema, integrity, invalid transitions)."""


class DuplicateTaskError(TaskStoreError):
    """Raised when an idempotency key collides with a different task request."""


class InvalidTransitionError(TaskStoreError):
    """Raised when a requested status transition is not allowed."""


def _with_store_lock(method):
    """Serialize one shared SQLite connection without covering executors.

    Durable helpers are private entry points called directly by
    ``DurableExecutionService``. They must obey the same TaskStore-owned
    connection boundary as public methods. The lock is re-entrant because
    fenced helpers intentionally call other locked store methods after their
    transaction commits.
    """

    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return locked


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
            CREATE TABLE IF NOT EXISTS task_usage_observations (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                window_id TEXT NOT NULL DEFAULT '',
                claim_epoch INTEGER NOT NULL DEFAULT 0,
                execution_id TEXT NOT NULL,
                role TEXT NOT NULL,
                model_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_units INTEGER,
                output_units INTEGER,
                reasoning_units INTEGER,
                cache_read_units INTEGER,
                cache_write_units INTEGER,
                cost_micro_units INTEGER,
                payload_digest TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_usage_task
                ON task_usage_observations(task_id, created_at, id);
            CREATE INDEX IF NOT EXISTS idx_task_usage_window
                ON task_usage_observations(window_id, task_id, claim_epoch);
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
                checkpoint_db_path TEXT NOT NULL DEFAULT '',
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
                run_id TEXT NOT NULL REFERENCES durable_runs(run_id),
                task_id TEXT NOT NULL REFERENCES tasks(id),
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

        # Backfill run_id + task_id for any pre-existing external ops rows.
        _ext_cols = {
            row["name"] for row in self._conn.execute(
                "PRAGMA table_info(durable_external_operations)"
            )
        }
        if "run_id" not in _ext_cols:
            self._conn.execute(
                "ALTER TABLE durable_external_operations "
                "ADD COLUMN run_id TEXT NOT NULL DEFAULT ''"
            )
        if "task_id" not in _ext_cols:
            self._conn.execute(
                "ALTER TABLE durable_external_operations "
                "ADD COLUMN task_id TEXT NOT NULL DEFAULT ''"
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
            ("checkpoint_db_path", "TEXT NOT NULL DEFAULT ''"),
        ]:
            if col not in run_columns:
                self._conn.execute(f"ALTER TABLE durable_runs ADD COLUMN {col} {dtype}")

        self._migrate_durable_runs_unique()

    def _migrate_durable_runs_unique(self) -> None:
        """Enforce SQLite-level one durable run per Task.

        Historical DBs may contain duplicate durable_runs rows for a single
        task from pre-v5 application-level race conditions. We DO NOT silently
        keep newest, delete old rows, or repair. If duplicates exist, fail
        closed with an explicit store/schema error.

        On a clean schema, a UNIQUE INDEX on durable_runs(task_id) is created
        so every future acquisition path is schema-enforced.
        """
        try:
            dup = self._conn.execute(
                "SELECT task_id, COUNT(*) AS c FROM durable_runs "
                "GROUP BY task_id HAVING c > 1 LIMIT 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return
        if dup is not None:
            raise TaskStoreError(
                f"durable_run_task_uniqueness_violation:"
                f"task_id={dup['task_id']}:run_count={dup['c']}:"
                "historical_duplicate_runs_not_repaired_fail_closed"
            )
        try:
            self._conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "idx_durable_runs_task_id ON durable_runs(task_id)"
            )
        except sqlite3.OperationalError as exc:
            raise TaskStoreError(
                f"durable_run_unique_index_migration_failed:{exc}"
            ) from exc

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

    # ------------------------------------------------------------------
    # Sanitized model usage observations
    # ------------------------------------------------------------------

    def append_usage_observation(
        self,
        task_id: str,
        *,
        observation_id: str,
        execution_id: str,
        role: str,
        model_id: str,
        provider_id: str,
        source_kind: str,
        source_id: str,
        status: str,
        input_units: int | None = None,
        output_units: int | None = None,
        reasoning_units: int | None = None,
        cache_read_units: int | None = None,
        cache_write_units: int | None = None,
        cost_micro_units: int | None = None,
    ) -> UsageObservation:
        """Append one numeric usage fact with replay-safe identity.

        Only the explicit scalar fields above can enter SQLite. The caller has
        no raw-event parameter, which keeps prompts, responses, tool payloads,
        headers and adjacent secret sentinels outside the persistence surface.
        """

        import hashlib
        import re

        labels = {
            "observation_id": observation_id,
            "execution_id": execution_id,
            "role": role,
            "model_id": model_id,
            "provider_id": provider_id,
            "source_kind": source_kind,
            "source_id": source_id,
        }
        safe_label = re.compile(r"^[A-Za-z0-9._:/@-]*$")
        for name, value in labels.items():
            if not isinstance(value, str) or len(value) > 256:
                raise TaskStoreError(f"invalid_usage_label:{name}")
            if name not in {"provider_id"} and not value:
                raise TaskStoreError(f"invalid_usage_label:{name}")
            if not safe_label.fullmatch(value) or "://" in value:
                raise TaskStoreError(f"invalid_usage_label:{name}")
        if status not in {"OBSERVED", "UNKNOWN"}:
            raise TaskStoreError("invalid_usage_status")
        metrics = {
            "input_units": input_units,
            "output_units": output_units,
            "reasoning_units": reasoning_units,
            "cache_read_units": cache_read_units,
            "cache_write_units": cache_write_units,
            "cost_micro_units": cost_micro_units,
        }
        if status == "OBSERVED":
            for name, value in metrics.items():
                if type(value) is not int or value < 0:
                    raise TaskStoreError(f"invalid_usage_metric:{name}")
        elif any(value is not None for value in metrics.values()):
            raise TaskStoreError("unknown_usage_must_not_carry_numeric_zero")

        digest_payload = {**labels, "status": status, **metrics}
        payload_digest = hashlib.sha256(
            json_dumps_stable(digest_payload).encode("utf-8")
        ).hexdigest()
        now = _utc_now()
        with self._lock:
            task = self._conn.execute(
                "SELECT id FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if task is None:
                raise TaskStoreError(f"task_not_found:{task_id}")
            window_id = ""
            claim_epoch = 0
            claims_table = self._conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' "
                "AND name = 'platform_coordinator_claims'"
            ).fetchone()
            if claims_table is not None:
                claim = self._conn.execute(
                    "SELECT window_id, epoch FROM platform_coordinator_claims "
                    "WHERE task_id = ? AND status = 'ACTIVE'",
                    (task_id,),
                ).fetchone()
                if claim is not None:
                    window_id = str(claim["window_id"])
                    claim_epoch = int(claim["epoch"])
            try:
                self._conn.execute(
                    "INSERT INTO task_usage_observations "
                    "(id, task_id, window_id, claim_epoch, execution_id, role, model_id, "
                    "provider_id, source_kind, source_id, status, input_units, output_units, "
                    "reasoning_units, cache_read_units, cache_write_units, cost_micro_units, "
                    "payload_digest, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        observation_id, task_id, window_id, claim_epoch,
                        execution_id, role, model_id, provider_id, source_kind,
                        source_id, status, input_units, output_units,
                        reasoning_units, cache_read_units, cache_write_units,
                        cost_micro_units, payload_digest, now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                existing = self._conn.execute(
                    "SELECT * FROM task_usage_observations WHERE id = ?",
                    (observation_id,),
                ).fetchone()
                if existing is None or existing["payload_digest"] != payload_digest:
                    raise TaskStoreError(
                        f"usage_observation_identity_collision:{observation_id}"
                    ) from exc
                return self._row_to_usage_observation(existing)
            row = self._conn.execute(
                "SELECT * FROM task_usage_observations WHERE id = ?",
                (observation_id,),
            ).fetchone()
            return self._row_to_usage_observation(row)

    def list_usage_observations(self, task_id: str) -> tuple[UsageObservation, ...]:
        with self._lock:
            if self._conn.execute(
                "SELECT 1 FROM tasks WHERE id = ?", (task_id,)
            ).fetchone() is None:
                raise TaskStoreError(f"task_not_found:{task_id}")
            rows = self._conn.execute(
                "SELECT * FROM task_usage_observations WHERE task_id = ? "
                "ORDER BY created_at ASC, id ASC",
                (task_id,),
            ).fetchall()
            return tuple(self._row_to_usage_observation(row) for row in rows)

    def usage_summary(self, task_id: str) -> dict[str, Any]:
        observations = self.list_usage_observations(task_id)
        totals = {
            "input_units": 0,
            "output_units": 0,
            "reasoning_units": 0,
            "cache_read_units": 0,
            "cache_write_units": 0,
            "cost_micro_units": 0,
        }
        roles: dict[str, dict[str, Any]] = {}
        unknown = 0
        for observation in observations:
            role_totals = roles.setdefault(
                observation.role,
                {
                    "role": observation.role,
                    **{key: 0 for key in totals},
                    "observation_count": 0,
                    "unknown_observation_count": 0,
                    "provenance_ids": [],
                },
            )
            role_totals["observation_count"] += 1
            role_totals["provenance_ids"].append(observation.id)
            if observation.status == "UNKNOWN":
                unknown += 1
                role_totals["unknown_observation_count"] += 1
                continue
            for key in totals:
                value = int(getattr(observation, key) or 0)
                totals[key] += value
                role_totals[key] += value
        return {
            "status": "USAGE_UNKNOWN" if unknown or not observations else "OBSERVED",
            **totals,
            "total_token_units": sum(
                totals[key] for key in (
                    "input_units", "output_units", "reasoning_units",
                    "cache_read_units", "cache_write_units",
                )
            ),
            "observation_count": len(observations),
            "unknown_observation_count": unknown,
            "provenance_ids": [observation.id for observation in observations],
            "per_role": [roles[key] for key in sorted(roles)],
        }

    def active_usage_budget_snapshot(self, task_id: str) -> dict[str, int]:
        """Return one numeric task/window budget snapshot for stream enforcement.

        Observations are summed across every retained claim epoch for the
        active task/window. This is the same window-wide accounting boundary
        used by final reservation reconciliation, so planner/coder/reviewer
        roles and retries cannot each receive the full reservation again.
        Direct/manual execution has no active coordinator claim and returns
        the closed zero snapshot.
        """

        zero = {
            "token_units": 0,
            "cost_micro_units": 0,
            "claim_epoch": 0,
            "observed_token_units": 0,
            "observed_cost_micro_units": 0,
            "unknown_observation_count": 0,
            "observation_count": 0,
        }
        with self._lock:
            tables = {
                str(row["name"])
                for row in self._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND "
                    "name IN ('platform_coordinator_claims', "
                    "'platform_budget_reservations')"
                ).fetchall()
            }
            if tables != {
                "platform_coordinator_claims",
                "platform_budget_reservations",
            }:
                return dict(zero)
            row = self._conn.execute(
                "SELECT reservation.reserved_token_units, "
                "reservation.reserved_cost_micro_units, claim.epoch, "
                "claim.window_id "
                "FROM platform_coordinator_claims AS claim "
                "JOIN platform_budget_reservations AS reservation "
                "ON reservation.task_id = claim.task_id "
                "AND reservation.window_id = claim.window_id "
                "AND reservation.claim_epoch = claim.epoch "
                "WHERE claim.task_id = ? AND claim.status = 'ACTIVE' "
                "AND reservation.state = 'ACTIVE'",
                (task_id,),
            ).fetchone()
            if row is None:
                return dict(zero)
            usage = self._conn.execute(
                "SELECT COUNT(*) AS observation_count, "
                "COALESCE(SUM(CASE WHEN status = 'UNKNOWN' THEN 1 ELSE 0 END), 0) "
                "AS unknown_count, "
                "COALESCE(SUM(CASE WHEN status = 'OBSERVED' THEN "
                "COALESCE(input_units, 0) + COALESCE(output_units, 0) + "
                "COALESCE(reasoning_units, 0) + COALESCE(cache_read_units, 0) + "
                "COALESCE(cache_write_units, 0) ELSE 0 END), 0) AS token_units, "
                "COALESCE(SUM(CASE WHEN status = 'OBSERVED' THEN "
                "COALESCE(cost_micro_units, 0) ELSE 0 END), 0) AS cost_units "
                "FROM task_usage_observations WHERE task_id = ? AND window_id = ?",
                (task_id, str(row["window_id"])),
            ).fetchone()
            return {
                "token_units": int(row["reserved_token_units"]),
                "cost_micro_units": int(row["reserved_cost_micro_units"]),
                "claim_epoch": int(row["epoch"]),
                "observed_token_units": int(usage["token_units"]),
                "observed_cost_micro_units": int(usage["cost_units"]),
                "unknown_observation_count": int(usage["unknown_count"]),
                "observation_count": int(usage["observation_count"]),
            }

    def active_usage_reservation(self, task_id: str) -> dict[str, int]:
        """Compatibility projection of the exact active reservation limits."""

        snapshot = self.active_usage_budget_snapshot(task_id)
        return {
            "token_units": snapshot["token_units"],
            "cost_micro_units": snapshot["cost_micro_units"],
            "claim_epoch": snapshot["claim_epoch"],
        }

    @staticmethod
    def _row_to_usage_observation(row: Any) -> UsageObservation:
        return UsageObservation(
            id=row["id"], task_id=row["task_id"], window_id=row["window_id"],
            claim_epoch=int(row["claim_epoch"]), execution_id=row["execution_id"],
            role=row["role"], model_id=row["model_id"], provider_id=row["provider_id"],
            source_kind=row["source_kind"], source_id=row["source_id"], status=row["status"],
            input_units=row["input_units"], output_units=row["output_units"],
            reasoning_units=row["reasoning_units"], cache_read_units=row["cache_read_units"],
            cache_write_units=row["cache_write_units"], cost_micro_units=row["cost_micro_units"],
            payload_digest=row["payload_digest"], created_at=row["created_at"],
        )

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

    @_with_store_lock
    def _acquire_durable_lease(
        self,
        *,
        task_id: str,
        execution_id: str,
        lease_owner: str,
        expiry_ms: int = 600000,
        execution_authority_sha: str = "",
        planning_sha: str = "",
        task_status: str | None = None,
        repository_base_sha: str = "",
        worktree_path: str = "",
        checkpoint_db_path: str = "",
    ) -> Any:
        """Atomically claim a durable lease in a single SQLite write transaction.

        Validates in ONE BEGIN IMMEDIATE transaction:
        - Task exists
        - Task.status == QUEUED (or matches the provided task_status override)
        - Task.executor_kind == "opencode"
        - Task.orchestration_mode == "sequential_team"
        - No durable run already exists for this task
        - Creates the run with empty worktree identity and transitions
          Task QUEUED -> PREPARING_WORKSPACE.

        Two concurrent TaskStore connections racing on the same SQLite file
        are serialized at the SQLite level: only one wins.
        """
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            task_row = cur.execute(
                "SELECT id, status, execution_id, executor_kind, "
                "orchestration_mode FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if task_row is None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"task_not_found:{task_id}")
            current_status = task_row["status"]
            current_executor_kind = task_row["executor_kind"]
            current_orchestration_mode = task_row["orchestration_mode"]
            if current_executor_kind not in ("opencode", "deterministic_fixture"):
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_claim_wrong_executor_kind:{task_id}:"
                    f"expected=opencode_or_deterministic_fixture:actual={current_executor_kind}"
                )
            if current_orchestration_mode not in ("sequential_team", "single"):
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_claim_wrong_orchestration_mode:{task_id}:"
                    f"expected=sequential_team_or_single:actual={current_orchestration_mode}"
                )
            if task_status is not None and current_status != task_status:
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_claim_wrong_task_status:{task_id}:"
                    f"expected={task_status}:actual={current_status}"
                )
            if task_status is None and current_status not in (
                "QUEUED", "PREPARING_WORKSPACE", "RUNNING",
                "RUNNING_FIXTURE", "VALIDATING",
            ):
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_claim_task_not_active:{task_id}:"
                    f"status={current_status}"
                )
            existing = cur.execute(
                "SELECT dr.run_id FROM durable_runs dr WHERE dr.task_id = ? "
                "LIMIT 1",
                (task_id,),
            ).fetchone()
            if existing is not None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_run_already_active:{task_id}"
                )
            now = _utc_now()
            now_ms = _utc_now_ms()
            run_id = f"run-{task_id}-{_short_uuid()}"
            cur.execute(
                "INSERT INTO durable_runs "
                "(run_id, task_id, execution_id, execution_authority_sha, planning_sha, "
                "repository_base_sha, worktree_path, worktree_head_sha, worktree_prepared_at, "
                "current_role, role_attempt, accepted_checkpoint, "
                "planner_handoff_digest, coder_product_diff_digest, reviewer_handoff_digest, "
                "partial_coder_diff_digest, "
                "validation_command_id, validation_exit_code, validation_output_digest, "
                "lease_owner, lease_epoch, heartbeat_at_ms, lease_expiry_ms, "
                "checkpoint_db_path, "
                "recovery_classification, interrupted_at, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, '', '', '', '', '', 1, '', '', '', '', '', '', "
                "NULL, '', ?, 1, ?, ?, '', 'normal', '', ?, ?)",
                (
                    run_id, task_id, execution_id,
                    execution_authority_sha or "",
                    planning_sha or "",
                    lease_owner, now_ms, now_ms + expiry_ms,
                    now, now,
                ),
            )
            cur.execute(
                "UPDATE tasks SET status = 'PREPARING_WORKSPACE', updated_at = ? "
                "WHERE id = ?",
                (now, task_id),
            )
            cur.execute("COMMIT")
            row = cur.execute(
                "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
            ).fetchone()
            return self._lease_handle_from_row(row)
        except TaskStoreError:
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"acquire_durable_lease_failed:{exc}"
            ) from exc

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

    @_with_store_lock
    def _atomic_fenced_update(
        self,
        run_id: str,
        owner: str,
        epoch: int,
        mutation_sql: str,
        mutation_params: tuple,
        *,
        allow_not_found: bool = False,
    ) -> int:
        """Atomically validate owner/epoch at SQLite level and apply mutation.

        Uses BEGIN IMMEDIATE to obtain a RESERVED write lock on the SQLite
        database. This guarantees that no other TaskStore instance pointing
        to the SAME SQLite file can modify the durable_runs row between our
        validation read and our mutation write. Two distinct TaskStore
        instances opening the same file are serialized at the SQLite level.

        Returns the rowcount of the mutation UPDATE.
        """
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            row = cur.execute(
                "SELECT lease_owner, lease_epoch FROM durable_runs "
                "WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                cur.execute("ROLLBACK")
                if allow_not_found:
                    return 0
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            current_epoch = int(row["lease_epoch"])
            current_owner = row["lease_owner"]
            if current_epoch != epoch or current_owner != owner:
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"lease_fenced:{run_id}:owner={owner}:epoch={epoch} "
                    f"current_owner={current_owner}:"
                    f"current_epoch={current_epoch}"
                )
            cur.execute(mutation_sql, mutation_params)
            rowcount = cur.rowcount
            cur.execute("COMMIT")
            return rowcount
        except TaskStoreError:
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"atomic_durable_mutation_failed:{exc}"
            ) from exc

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
        self, run_id: str, owner: str, epoch: int,
        expiry_ms: int,
    ) -> None:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                now_ms = _utc_now_ms()
                row = cur.execute(
                    "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"durable_run_not_found:{run_id}")
                if int(row["lease_epoch"]) != epoch or row["lease_owner"] != owner:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"lease_fenced:{run_id}:owner={owner}:epoch={epoch} "
                        f"current_owner={row['lease_owner']}:"
                        f"current_epoch={row['lease_epoch']}"
                    )
                cur.execute(
                    "UPDATE durable_runs SET heartbeat_at_ms = ?, "
                    "lease_expiry_ms = ?, updated_at = ? WHERE run_id = ?",
                    (now_ms, now_ms + expiry_ms, _utc_now(), run_id),
                )
                cur.execute("COMMIT")
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"heartbeat_durable_lease_failed:{exc}"
                ) from exc

    def _release_durable_lease(
        self, run_id: str, owner: str, epoch: int
    ) -> None:
        """Release active ownership with fenced semantics.

        Requires run_id, owner, and epoch. Release succeeds only when the
        supplied owner+epoch still equals the current active lease. A stale
        release (after another worker has taken over) MUST NOT clear the
        new worker's owner, expiry, or epoch.
        """
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                row = cur.execute(
                    "SELECT lease_owner, lease_epoch FROM durable_runs "
                    "WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"durable_run_not_found:{run_id}")
                current_epoch = int(row["lease_epoch"])
                current_owner = row["lease_owner"]
                if current_epoch != epoch or current_owner != owner:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"lease_fenced_release:{run_id}:"
                        f"owner={owner}:epoch={epoch} "
                        f"current_owner={current_owner}:"
                        f"current_epoch={current_epoch}"
                    )
                cur.execute(
                    "UPDATE durable_runs SET lease_owner = '', "
                    "lease_expiry_ms = 0, updated_at = ? "
                    "WHERE run_id = ? AND lease_owner = ? AND lease_epoch = ?",
                    (_utc_now(), run_id, owner, epoch),
                )
                if cur.rowcount == 0:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"lease_release_failed:{run_id}:"
                        "lease_changed_during_release"
                    )
                cur.execute("COMMIT")
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"lease_release_error:{exc}"
                ) from exc

    def _set_repository_base_sha(
        self, run_id: str, base_sha: str,
        owner: str, epoch: int,
    ) -> None:
        """Persist repository_base_sha exactly once, fenced and immutable.

        The repository base SHA must be empty before this call; if already
        set, the mutation is rejected. This guarantees repository_base_sha
        remains immutable for the run's lifetime.
        """
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                row = cur.execute(
                    "SELECT lease_owner, lease_epoch, repository_base_sha "
                    "FROM durable_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"durable_run_not_found:{run_id}")
                if int(row["lease_epoch"]) != epoch or row["lease_owner"] != owner:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"lease_fenced:{run_id}:owner={owner}:epoch={epoch}"
                    )
                if row["repository_base_sha"] and row["repository_base_sha"] != "":
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"repository_base_immutable:{run_id}:"
                        f"already_set={row['repository_base_sha']}"
                    )
                cur.execute(
                    "UPDATE durable_runs SET repository_base_sha = ?, "
                    "updated_at = ? WHERE run_id = ?",
                    (base_sha, _utc_now(), run_id),
                )
                cur.execute("COMMIT")
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"set_repository_base_failed:{exc}"
                ) from exc

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

        The owner+epoch validation and the checkpoint mutation are performed
        atomically at the SQLite level using BEGIN IMMEDIATE, so two
        TaskStore instances on the same file cannot race.
        """
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                run_row = cur.execute(
                    "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
                ).fetchone()
                if run_row is None:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"durable_run_not_found:{run_id}")
                if int(run_row["lease_epoch"]) != epoch or run_row["lease_owner"] != owner:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"lease_fenced:{run_id}:owner={owner}:epoch={epoch} "
                        f"current_owner={run_row['lease_owner']}:"
                        f"current_epoch={run_row['lease_epoch']}"
                    )
                current_accepted = run_row["accepted_checkpoint"]
                current_rank = _CHECKPOINT_INDEX.get(current_accepted, -1)
                new_rank = _CHECKPOINT_INDEX.get(checkpoint_name, -1)
                if new_rank < 0:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"invalid_checkpoint_name:{checkpoint_name}")
                if current_accepted == "" and checkpoint_name != "PRE_PLANNER":
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"checkpoint_first_must_be_pre_planner:"
                        f"run={run_id}:first_attempted={checkpoint_name}"
                    )
                if new_rank < current_rank:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"checkpoint_sequence_regression:"
                        f"{current_accepted}->{checkpoint_name}"
                    )
                if new_rank > current_rank + 1 and current_rank >= 0:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"checkpoint_sequence_jump:"
                        f"{current_accepted}->{checkpoint_name}"
                    )

                if new_rank == current_rank:
                    existing = cur.execute(
                        "SELECT * FROM durable_checkpoint_history "
                        "WHERE run_id = ? AND checkpoint_name = ? "
                        "ORDER BY seq DESC LIMIT 1",
                        (run_id, checkpoint_name),
                    ).fetchone()
                    if existing is not None:
                        stored_digest = existing["artifact_digest"]
                        stored_attempt = int(existing["role_attempt"])
                        if stored_digest != artifact_digest or stored_attempt != role_attempt:
                            cur.execute("ROLLBACK")
                            raise TaskStoreError(
                                f"conflicting_checkpoint_acceptance:"
                                f"run={run_id}:checkpoint={checkpoint_name}:"
                                f"stored_digest={stored_digest}:"
                                f"attempted_digest={artifact_digest}:"
                                f"stored_attempt={stored_attempt}:"
                                f"attempted_attempt={role_attempt}"
                            )
                        cur.execute("COMMIT")
                        return DurableCheckpoint(
                            checkpoint_id=existing["checkpoint_id"],
                            run_id=existing["run_id"],
                            checkpoint_name=existing["checkpoint_name"],
                            artifact_digest=existing["artifact_digest"],
                            role_attempt=stored_attempt,
                            created_at=existing["created_at"],
                        )

                cp_id = f"cp-{run_id}-{_short_uuid()}"
                cur.execute(
                    "INSERT INTO durable_checkpoint_history "
                    "(checkpoint_id, run_id, checkpoint_name, artifact_digest, "
                    "role_attempt, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (cp_id, run_id, checkpoint_name, artifact_digest, role_attempt, _utc_now()),
                )
                cur.execute(
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
                cur.execute("COMMIT")
                return DurableCheckpoint(
                    checkpoint_id=cp_id,
                    run_id=run_id,
                    checkpoint_name=checkpoint_name,
                    artifact_digest=artifact_digest,
                    role_attempt=role_attempt,
                    created_at=_utc_now(),
                )
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"accept_checkpoint_failed:{exc}"
                ) from exc

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
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET planner_handoff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_coder_product_diff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET coder_product_diff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_reviewer_handoff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET reviewer_handoff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_role_attempt(
        self, run_id: str, role: str, attempt: int,
        owner: str, epoch: int,
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET current_role = ?, role_attempt = ?, "
                "updated_at = ? WHERE run_id = ?",
                (role, attempt, _utc_now(), run_id),
            )

    def _set_recovery_classification(
        self, run_id: str, classification: str, owner: str, epoch: int
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
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
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET "
                "validation_command_id = ?, validation_exit_code = ?, "
                "validation_output_digest = ?, updated_at = ? "
                "WHERE run_id = ?",
                (command_id, exit_code, output_digest, _utc_now(), run_id),
            )

    def _set_worktree_identity(
        self, run_id: str, worktree_path: str, worktree_head_sha: str,
        owner: str, epoch: int,
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
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
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET "
                "execution_authority_sha = ?, planning_sha = ?, "
                "updated_at = ? WHERE run_id = ?",
                (execution_authority_sha, planning_sha, _utc_now(), run_id),
            )

    def _set_partial_coder_diff_digest(
        self, run_id: str, digest: str, owner: str, epoch: int,
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET partial_coder_diff_digest = ?, "
                "updated_at = ? WHERE run_id = ?",
                (digest, _utc_now(), run_id),
            )

    def _set_checkpoint_db_path(
        self, run_id: str, checkpoint_db_path: str,
        owner: str, epoch: int,
    ) -> None:
        with self._lock:
            self._atomic_fenced_update(
                run_id, owner, epoch,
                "UPDATE durable_runs SET checkpoint_db_path = ?, "
                "updated_at = ? WHERE run_id = ?",
                (checkpoint_db_path, _utc_now(), run_id),
            )

    @_with_store_lock
    def _recover_durable_lease(
        self, run_id: str, lease_owner: str,
        *, expiry_ms: int = 300000,
        require_interrupted: bool = False,
    ) -> Any:
        """Atomically recover a durable lease with a strictly larger epoch.

        In ONE BEGIN IMMEDIATE transaction:
        - Verify the durable run exists
        - Verify task status is INTERRUPTED (or matches the required recovery state)
        - Re-check orchestration_mode == "sequential_team"
        - Re-check executor_kind == "opencode"
        - Re-check valid recovery classification
        - Re-check current epoch has not already advanced (same durable run)
        - Advance epoch exactly once
        - Transition Task INTERRUPTED -> RUNNING
        - Set new owner and expiry

        Two concurrent TaskStore connections cannot produce the same epoch;
        only the first BEGIN IMMEDIATE holder wins.
        """
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            row = cur.execute(
                "SELECT dr.*, t.status as task_status, "
                "t.orchestration_mode, t.executor_kind FROM durable_runs dr "
                "JOIN tasks t ON t.id = dr.task_id "
                "WHERE dr.run_id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"durable_run_not_found:{run_id}")
            task_status = row["task_status"]
            if require_interrupted and task_status != "INTERRUPTED":
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_recover_wrong_task_status:{run_id}:"
                    f"expected=INTERRUPTED:actual={task_status}"
                )
            if row["orchestration_mode"] not in ("sequential_team", "single"):
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_recover_wrong_orchestration_mode:{run_id}:"
                    f"actual={row['orchestration_mode']}"
                )
            if row["executor_kind"] not in ("opencode", "deterministic_fixture"):
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_recover_wrong_executor_kind:{run_id}:"
                    f"actual={row['executor_kind']}"
                )
            recovery_class = row["recovery_classification"]
            allowed_recovery = ("orphan_stale_lease", "interrupted", "recovering")
            all_recovery = allowed_recovery + ("normal",)
            if require_interrupted:
                if recovery_class not in allowed_recovery:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"durable_recover_invalid_recovery_classification:{run_id}:"
                        f"actual={recovery_class}"
                    )
            else:
                if recovery_class not in all_recovery:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"durable_recover_invalid_recovery_classification:{run_id}:"
                        f"actual={recovery_class}"
                    )
            existing_epoch = int(row["lease_epoch"])
            new_epoch = existing_epoch + 1
            now_ms = _utc_now_ms()
            now = _utc_now()
            cur.execute(
                "UPDATE durable_runs SET "
                "lease_owner = ?, lease_epoch = ?, heartbeat_at_ms = ?, "
                "lease_expiry_ms = ?, updated_at = ? "
                "WHERE run_id = ? AND lease_epoch = ?",
                (lease_owner, new_epoch, now_ms, now_ms + expiry_ms, now, run_id, existing_epoch),
            )
            if cur.rowcount == 0:
                cur.execute("ROLLBACK")
                raise TaskStoreError(
                    f"durable_recover_lease_changed:{run_id}:"
                    f"epoch={existing_epoch}"
                )
            if require_interrupted:
                cur.execute(
                    "UPDATE tasks SET status = 'RUNNING', updated_at = ? "
                    "WHERE id = ? AND status = 'INTERRUPTED'",
                    (now, row["task_id"]),
                )
                if cur.rowcount == 0:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(
                        f"durable_recover_task_not_interrupted:{row['task_id']}"
                    )
            cur.execute("COMMIT")
            row2 = cur.execute(
                "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,),
            ).fetchone()
            return self._lease_handle_from_row(row2)
        except TaskStoreError:
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"recover_durable_lease_failed:{exc}"
            ) from exc
    def _external_operation_prevents_dispatch(
        self, idempotency_key: str, request_digest: str,
        run_id: str = "", owner: str = "", epoch: int = 0,
    ) -> bool:
        """Return True if dispatch should be prevented (operation already exists/succeeded).

        Validates run_id + owner + epoch under the same lock as the query.
        """
        with self._lock:
            if not idempotency_key:
                return False
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                if run_id:
                    run_row = cur.execute(
                        "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
                        (run_id,),
                    ).fetchone()
                    if run_row is None:
                        cur.execute("ROLLBACK")
                        return False
                    if (
                        int(run_row["lease_epoch"]) != epoch
                        or run_row["lease_owner"] != owner
                    ):
                        cur.execute("ROLLBACK")
                        return False
                row = cur.execute(
                    "SELECT state, request_digest FROM durable_external_operations "
                    "WHERE idempotency_key = ? AND request_digest = ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (idempotency_key, request_digest),
                ).fetchone()
                cur.execute("COMMIT")
                if row is None:
                    return False
                # PENDING is ambiguous: dispatch may or may not have completed.
                # Fail closed: prevent re-dispatch for ANY existing state.
                return True
            except Exception:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                return False

    def _record_external_operation(
        self,
        *,
        operation_key: str,
        idempotency_key: str,
        request_digest: str,
        run_id: str = "",
        task_id: str = "",
        owner: str = "",
        epoch: int = 0,
    ) -> Any:
        """Record an external operation BEFORE dispatch.

        Validates run_id + owner + epoch under the same lock as the INSERT.
        """
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                if run_id:
                    run_row = cur.execute(
                        "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
                        (run_id,),
                    ).fetchone()
                    if run_row is None:
                        cur.execute("ROLLBACK")
                        raise TaskStoreError(f"durable_run_not_found:{run_id}")
                    if (
                        int(run_row["lease_epoch"]) != epoch
                        or run_row["lease_owner"] != owner
                    ):
                        cur.execute("ROLLBACK")
                        raise TaskStoreError(
                            f"lease_fenced_external_op:{run_id}:"
                            f"owner={owner}:epoch={epoch} "
                            f"current_owner={run_row['lease_owner']}:"
                            f"current_epoch={run_row['lease_epoch']}"
                        )
                existing = cur.execute(
                    "SELECT * FROM durable_external_operations "
                    "WHERE idempotency_key = ? AND request_digest = ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (idempotency_key, request_digest),
                ).fetchone()
                if existing is not None:
                    cur.execute("COMMIT")
                    return _row_to_external_operation(dict(existing))
                now = _utc_now()
                op_id = f"op-{_short_uuid()}"
                cur.execute(
                    "INSERT INTO durable_external_operations "
                    "(operation_id, run_id, task_id, operation_key, idempotency_key, "
                    "request_digest, state, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                    (op_id, run_id, task_id, operation_key, idempotency_key, request_digest, now, now),
                )
                cur.execute("COMMIT")
                row = cur.execute(
                    "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                    (op_id,),
                ).fetchone()
                return _row_to_external_operation(dict(row))
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"record_external_operation_failed:{exc}"
                ) from exc

    def _reconcile_external_operation(
        self,
        *,
        operation_id: str,
        external_operation_id: str,
        result_state: str,
        run_id: str = "",
        owner: str = "",
        epoch: int = 0,
    ) -> Any:
        """Reconcile an external operation with the result of a dispatch.

        Validates run_id + owner + epoch under the same lock as the UPDATE.
        """
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                if run_id:
                    run_row = cur.execute(
                        "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
                        (run_id,),
                    ).fetchone()
                    if run_row is None:
                        cur.execute("ROLLBACK")
                        raise TaskStoreError(f"durable_run_not_found:{run_id}")
                    if (
                        int(run_row["lease_epoch"]) != epoch
                        or run_row["lease_owner"] != owner
                    ):
                        cur.execute("ROLLBACK")
                        raise TaskStoreError(
                            f"lease_fenced_external_op_reconcile:{run_id}:"
                            f"owner={owner}:epoch={epoch} "
                            f"current_owner={run_row['lease_owner']}:"
                            f"current_epoch={run_row['lease_epoch']}"
                        )
                if run_id:
                    row = cur.execute(
                        "SELECT * FROM durable_external_operations WHERE operation_id = ? "
                        "AND run_id = ?",
                        (operation_id, run_id),
                    ).fetchone()
                else:
                    row = cur.execute(
                        "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                        (operation_id,),
                    ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError(f"external_operation_not_found:{operation_id}")
                if run_id:
                    cur.execute(
                        "UPDATE durable_external_operations SET "
                        "external_operation_id = ?, result_state = ?, "
                        "state = ?, updated_at = ? "
                        "WHERE operation_id = ? AND run_id = ?",
                        (
                            external_operation_id, result_state,
                            "SUCCESS" if result_state == "success" else "RECONCILED",
                            _utc_now(), operation_id, run_id,
                        ),
                    )
                else:
                    cur.execute(
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
                cur.execute("COMMIT")
                updated = cur.execute(
                    "SELECT * FROM durable_external_operations WHERE operation_id = ?",
                    (operation_id,),
                ).fetchone()
                return _row_to_external_operation(dict(updated))
            except TaskStoreError:
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"reconcile_external_operation_failed:{exc}"
                ) from exc

    @_with_store_lock
    def _reconcile_expired_runs(
        self,
        *,
        now_ms: int,
        max_age_ms: int,
    ) -> tuple[dict[str, Any], ...]:
        """Atomically reconcile expired active run leases to INTERRUPTED.

        For each candidate stale run, re-checks expiry/epoch/task_status
        inside a BEGIN IMMEDIATE transaction. Only interrupts if the run
        is STILL expired and STILL in the same observed stale epoch/state.

        If heartbeat renewed the lease: NO OP.
        If another worker already owns a newer epoch: NO OP.
        If another reconciler already handled it: NO OP.

        This guarantees exactly one interruption event per stale run, even
        when two reconcilers run concurrently.
        """
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
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                recheck = cur.execute(
                    "SELECT dr.lease_expiry_ms, dr.lease_epoch, "
                    "dr.recovery_classification, t.status as task_status2 "
                    "FROM durable_runs dr "
                    "JOIN tasks t ON t.id = dr.task_id "
                    "WHERE dr.run_id = ?",
                    (run_id,),
                ).fetchone()
                if recheck is None:
                    cur.execute("ROLLBACK")
                    continue
                current_expiry = int(recheck["lease_expiry_ms"])
                if current_expiry >= now_ms:
                    cur.execute("ROLLBACK")
                    continue
                current_status = recheck["task_status2"]
                if current_status not in (
                    "PREPARING_WORKSPACE", "RUNNING",
                    "RUNNING_FIXTURE", "VALIDATING",
                ):
                    cur.execute("ROLLBACK")
                    continue
                cur.execute(
                    "UPDATE durable_runs SET "
                    "recovery_classification = 'orphan_stale_lease', "
                    "lease_owner = '', "
                    "interrupted_at = ?, updated_at = ? "
                    "WHERE run_id = ? "
                    "AND lease_expiry_ms < ? "
                    "AND recovery_classification IN ('normal', 'orphan_stale_lease')",
                    (_utc_now(), _utc_now(), run_id, now_ms),
                )
                if cur.rowcount == 0:
                    cur.execute("ROLLBACK")
                    continue
                cur.execute(
                    "UPDATE tasks SET status = 'INTERRUPTED', "
                    "updated_at = ? "
                    "WHERE id = ? AND status IN (?, ?, ?, ?)",
                    (_utc_now(), task_id,
                     "PREPARING_WORKSPACE", "RUNNING",
                     "RUNNING_FIXTURE", "VALIDATING"),
                )
                if cur.rowcount == 0:
                    cur.execute("ROLLBACK")
                    continue
                cur.execute(
                    "INSERT INTO task_events "
                    "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"event-{task_id}-{_short_uuid()}",
                        task_id, "EXECUTOR_FINISHED",
                        _utc_now(), "Durable run interrupted",
                        "lease expired, reconciled to INTERRUPTED",
                        "",
                        json_dumps_stable({
                            "run_id": run_id,
                            "recovery_classification": "orphan_stale_lease",
                            "previous_status": task_status,
                        }),
                    ),
                )
                cur.execute("COMMIT")
                records.append({
                    "run_id": run_id,
                    "task_id": task_id,
                    "previous_status": task_status,
                    "recovery_classification": "orphan_stale_lease",
                })
            except Exception:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                continue
        return tuple(records)

    def _lease_handle_from_row(self, row: sqlite3.Row) -> Any:
        cols = set(row.keys())
        return LeaseHandle(
            run_id=row["run_id"],
            task_id=row["task_id"],
            execution_id=row["execution_id"],
            owner=row["lease_owner"],
            epoch=int(row["lease_epoch"]),
            expiry_ms=int(row["lease_expiry_ms"]),
            worktree_path=row["worktree_path"],
            repository_base_sha=row["repository_base_sha"],
            checkpoint_db_path=row["checkpoint_db_path"] if "checkpoint_db_path" in cols else "",
        )

    # ------------------------------------------------------------------
    # Fenced durable-path Task/business mutations
    # ------------------------------------------------------------------

    @_with_store_lock
    def _fenced_transition_to(
        self,
        run_id: str,
        task_id: str,
        status: str,
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic: validate lease owner+epoch AND perform status transition
        under ONE BEGIN IMMEDIATE transaction. No TOCTOU window across processes."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            if status not in TASK_STATUS_ORDER:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"invalid_status:{status}")
            current_row = cur.execute(
                "SELECT status FROM tasks WHERE id = ?", (task_id,),
            ).fetchone()
            if current_row is None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"task_not_found:{task_id}")
            current_status = current_row["status"]
            if current_status == status:
                cur.execute("COMMIT")
                return self.get_task(task_id)
            allowed = TRANSITION_RULES.get(current_status, ())
            if status not in allowed:
                cur.execute("ROLLBACK")
                raise InvalidTransitionError(
                    f"invalid_transition:{current_status}->{status} allowed={allowed}"
                )
            if current_status in TERMINAL_STATUSES:
                cur.execute("ROLLBACK")
                raise InvalidTransitionError(f"terminal_status:{current_status}")
            cur.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, _utc_now(), task_id),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except (TaskStoreError, InvalidTransitionError):
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_transition_to_failed:{exc}"
            ) from exc

    @_with_store_lock
    def _fenced_set_changed_files(
        self,
        run_id: str,
        task_id: str,
        files: Sequence[Mapping[str, Any]],
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic fenced set_changed_files."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            cur.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            cur.execute("DELETE FROM task_changed_files WHERE task_id = ?", (task_id,))
            for f in files:
                cur.execute(
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
            cur.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (_utc_now(), task_id),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_set_changed_files_failed:{exc}"
            ) from exc

    @_with_store_lock
    def _fenced_add_event(
        self,
        run_id: str,
        task_id: str,
        *,
        event_type: str,
        title: str,
        description: str = "",
        raw_log: str = "",
        metadata: Mapping[str, Any] | None = None,
        owner: str,
        epoch: int,
    ) -> TaskEvent:
        """SQLite-atomic fenced add_event."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            cur.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            now = _utc_now()
            event_id = f"event-{task_id}-{_short_uuid()}"
            meta_json = json_dumps_stable(metadata or {})
            cur.execute(
                "INSERT INTO task_events "
                "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, task_id, event_type, now, title, description, raw_log, meta_json),
            )
            cur.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (now, task_id),
            )
            cur.execute("COMMIT")
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
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_add_event_failed:{exc}"
            ) from exc

    @_with_store_lock
    def _fenced_add_evidence(
        self,
        run_id: str,
        task_id: str,
        *,
        category: str,
        label: str,
        value: str,
        status: str,
        detail: str = "",
        raw_json_digest: str = "",
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic fenced add_evidence."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            cur.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            ev_id = f"ev-{task_id}-{_short_uuid()}"
            cur.execute(
                "INSERT INTO task_evidence "
                "(id, task_id, category, label, value, status, detail, raw_json_digest) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ev_id, task_id, category, label, value, status, detail, raw_json_digest),
            )
            cur.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (_utc_now(), task_id),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_add_evidence_failed:{exc}"
            ) from exc

    def _fenced_append_usage_observation(
        self,
        run_id: str,
        task_id: str,
        *,
        observation_id: str,
        execution_id: str,
        role: str,
        model_id: str,
        provider_id: str,
        source_kind: str,
        source_id: str,
        status: str,
        input_units: int | None = None,
        output_units: int | None = None,
        reasoning_units: int | None = None,
        cache_read_units: int | None = None,
        cache_write_units: int | None = None,
        cost_micro_units: int | None = None,
        owner: str,
        epoch: int,
    ) -> UsageObservation:
        """Atomically fence and append one sanitized usage observation."""

        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                self._fenced_validate_lease(cur, run_id, owner, epoch)
                bound = cur.execute(
                    "SELECT task_id FROM durable_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if bound is None or bound["task_id"] != task_id:
                    raise TaskStoreError("fenced_usage_task_mismatch")
                result = self.append_usage_observation(
                    task_id,
                    observation_id=observation_id,
                    execution_id=execution_id,
                    role=role,
                    model_id=model_id,
                    provider_id=provider_id,
                    source_kind=source_kind,
                    source_id=source_id,
                    status=status,
                    input_units=input_units,
                    output_units=output_units,
                    reasoning_units=reasoning_units,
                    cache_read_units=cache_read_units,
                    cache_write_units=cache_write_units,
                    cost_micro_units=cost_micro_units,
                )
                cur.execute("COMMIT")
                return result
            except TaskStoreError:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"fenced_append_usage_failed:{type(exc).__name__}"
                ) from exc

    def _fenced_active_usage_reservation(
        self,
        run_id: str,
        task_id: str,
        *,
        owner: str,
        epoch: int,
    ) -> dict[str, int]:
        """Read a reservation only while the durable owner/epoch is current."""

        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN")
                self._fenced_validate_lease(cur, run_id, owner, epoch)
                bound = cur.execute(
                    "SELECT task_id FROM durable_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if bound is None or bound["task_id"] != task_id:
                    raise TaskStoreError("fenced_usage_task_mismatch")
                result = self.active_usage_reservation(task_id)
                cur.execute("COMMIT")
                return result
            except TaskStoreError:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"fenced_usage_reservation_failed:{type(exc).__name__}"
                ) from exc

    def _fenced_active_usage_budget_snapshot(
        self,
        run_id: str,
        task_id: str,
        *,
        owner: str,
        epoch: int,
    ) -> dict[str, int]:
        """Read cumulative budget truth only for the current durable lease."""

        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN")
                self._fenced_validate_lease(cur, run_id, owner, epoch)
                bound = cur.execute(
                    "SELECT task_id FROM durable_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                if bound is None or bound["task_id"] != task_id:
                    raise TaskStoreError("fenced_usage_task_mismatch")
                result = self.active_usage_budget_snapshot(task_id)
                cur.execute("COMMIT")
                return result
            except TaskStoreError:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            except Exception as exc:
                try:
                    cur.execute("ROLLBACK")
                except Exception:
                    pass
                raise TaskStoreError(
                    f"fenced_usage_snapshot_failed:{type(exc).__name__}"
                ) from exc

    @_with_store_lock
    def _fenced_classify_failure(
        self,
        run_id: str,
        task_id: str,
        *,
        classification: str,
        detail: str = "",
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic fenced classify_failure."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            task_row = cur.execute(
                "SELECT status FROM tasks WHERE id = ?", (task_id,),
            ).fetchone()
            if task_row is None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"task_not_found:{task_id}")
            if task_row["status"] in TERMINAL_STATUSES:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"terminal_status:{task_row['status']}")
            target = "BLOCKED" if classification == "blocked" else "FAILED"
            cur.execute(
                "UPDATE tasks SET failure_classification = ?, failure_detail = ?, "
                "status = ?, updated_at = ? WHERE id = ?",
                (classification, detail, target, _utc_now(), task_id),
            )
            now = _utc_now()
            event_id = f"event-{task_id}-{_short_uuid()}"
            cur.execute(
                "INSERT INTO task_events "
                "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id, task_id, "EXECUTOR_FINISHED", now,
                    "Executor failed",
                    f"failure_classification={classification}",
                    "",
                    json_dumps_stable({"failure_classification": classification, "detail": detail}),
                ),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_classify_failure_failed:{exc}"
            ) from exc

    @_with_store_lock
    def _fenced_set_task_validation(
        self,
        run_id: str,
        task_id: str,
        *,
        command_id: str,
        exit_code: int,
        output_digest: str,
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic fenced set_task_validation."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            cur.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            cur.execute(
                "UPDATE tasks SET validation_command_id = ?, "
                "validation_exit_code = ?, validation_output_digest = ?, "
                "updated_at = ? WHERE id = ?",
                (command_id, exit_code, output_digest, _utc_now(), task_id),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_set_task_validation_failed:{exc}"
            ) from exc

    @_with_store_lock
    def _fenced_terminalize(
        self,
        run_id: str,
        task_id: str,
        *,
        terminal_status: str,
        validation_command_id: str,
        validation_exit_code: int,
        validation_output_digest: str,
        failure_classification: str,
        failure_detail: str,
        owner: str,
        epoch: int,
    ) -> Task:
        """SQLite-atomic fenced terminal publication."""
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._fenced_validate_lease(cur, run_id, owner, epoch)
            task_row = cur.execute(
                "SELECT status FROM tasks WHERE id = ?", (task_id,),
            ).fetchone()
            if task_row is None:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"task_not_found:{task_id}")
            if task_row["status"] in TERMINAL_STATUSES:
                cur.execute("COMMIT")
                return self.get_task(task_id)
            if terminal_status not in TERMINAL_STATUSES:
                cur.execute("ROLLBACK")
                raise TaskStoreError(f"invalid_terminal_status:{terminal_status}")
            cur.execute(
                "UPDATE tasks SET "
                "validation_command_id = ?, validation_exit_code = ?, "
                "validation_output_digest = ?, failure_classification = ?, "
                "failure_detail = ?, status = ?, updated_at = ? "
                "WHERE id = ?",
                (
                    validation_command_id, validation_exit_code,
                    validation_output_digest, failure_classification,
                    failure_detail, terminal_status, _utc_now(), task_id,
                ),
            )
            cur.execute("COMMIT")
            return self.get_task(task_id)
        except TaskStoreError:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise TaskStoreError(
                f"fenced_terminalize_failed:{exc}"
            ) from exc

    @staticmethod
    def _fenced_validate_lease(
        cur: Any, run_id: str, owner: str, epoch: int
    ) -> None:
        """Validate owner+epoch under the caller's BEGIN IMMEDIATE transaction.

        Must be called AFTER BEGIN IMMEDIATE and BEFORE any mutation.
        Raises TaskStoreError on mismatch (caller must ROLLBACK).
        """
        row = cur.execute(
            "SELECT lease_owner, lease_epoch FROM durable_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise TaskStoreError(f"durable_run_not_found:{run_id}")
        if int(row["lease_epoch"]) != epoch or row["lease_owner"] != owner:
            raise TaskStoreError(
                f"lease_fenced:{run_id}:owner={owner}:epoch={epoch} "
                f"current_owner={row['lease_owner']}:"
                f"current_epoch={row['lease_epoch']}"
            )

class LeaseHandle:
    """Immutable lease handle returned by durable lease operations."""
    __slots__ = (
        "run_id", "task_id", "execution_id", "owner", "epoch",
        "expiry_ms", "worktree_path", "repository_base_sha",
        "checkpoint_db_path",
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
        checkpoint_db_path: str = "",
    ) -> None:
        self.run_id = run_id
        self.task_id = task_id
        self.execution_id = execution_id
        self.owner = owner
        self.epoch = epoch
        self.expiry_ms = expiry_ms
        self.worktree_path = worktree_path
        self.repository_base_sha = repository_base_sha
        self.checkpoint_db_path = checkpoint_db_path


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
        checkpoint_db_path: str
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
        checkpoint_db_path=row["checkpoint_db_path"] if "checkpoint_db_path" in cols else "",
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
