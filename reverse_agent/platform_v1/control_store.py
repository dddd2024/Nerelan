"""Durable product-control records stored beside TaskStore task truth.

This module deliberately reuses the existing TaskStore SQLite connection.  It
adds goal, autonomous-window, receipt, coordinator-claim and publication
tables to the same database; it does not introduce a second state store.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .run_store import TaskStore, TaskStoreError


GOAL_STATES = frozenset(
    {"DRAFT", "PLANNED", "APPROVED", "RUNNING", "COMPLETED", "BLOCKED", "INVALIDATED"}
)
WINDOW_STATES = frozenset({"ACTIVE", "COMPLETED", "EXPIRED", "STOPPED", "BLOCKED"})
PUBLICATION_STATES = frozenset({"PENDING", "COMMIT_CREATED", "PUSHED", "COMPLETE", "FAILED"})
INBOX_STATES = frozenset({"CAPTURED", "PROMOTED", "DISMISSED"})
SENSITIVE_KEY_PARTS = ("secret", "token", "password", "authorization", "api_key", "apikey")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


def _id(prefix: str) -> str:
    return f"{prefix}-{_utc_now_ms()}-{uuid.uuid4().hex[:12]}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def reject_sensitive_keys(value: Any, *, path: str = "$") -> None:
    """Reject secret-shaped fields before they can enter durable control state."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                raise TaskStoreError(f"sensitive_control_field_rejected:{path}.{key}")
            reject_sensitive_keys(child, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            reject_sensitive_keys(child, path=f"{path}[{index}]")


@dataclass(frozen=True)
class GoalRecord:
    id: str
    title: str
    objective: str
    repository: str
    status: str
    revision: int
    spec_markdown: str
    plan_markdown: str
    tasks: tuple[Mapping[str, Any], ...]
    acceptance_criteria: tuple[str, ...]
    artifact_digest: str
    executor_kind: str
    orchestration_mode: str
    binding_ref: str
    policy_ref: str
    window_id: str
    idempotency_key: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AutonomousWindowRecord:
    id: str
    policy_id: str
    policy_revision: int
    policy_digest: str
    owner_identity: str
    confirmation: str
    starts_at: str
    expires_at: str
    status: str
    repositories: tuple[str, ...]
    capabilities: tuple[str, ...]
    max_concurrent_tasks: int
    max_tasks: int
    max_retries: int
    tasks_started: int
    tasks_completed: int
    retries_used: int
    stop_reason: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class OperationReceipt:
    id: str
    window_id: str
    operation_type: str
    capability: str
    repository: str
    subject_id: str
    decision: str
    reason: str
    input_digest: str
    external_id: str
    result: str
    remaining_tasks: int
    created_at: str


@dataclass(frozen=True)
class PublicationRecord:
    id: str
    task_id: str
    repository: str
    base_branch: str
    branch: str
    status: str
    commit_sha: str
    pr_number: int
    pr_url: str
    request_digest: str
    failure_classification: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class InboxItemRecord:
    """Display-only capture state; grants no execution authority."""

    id: str
    title: str
    objective: str
    repository: str
    status: str
    promoted_goal_id: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RoadmapPhaseRecord:
    """Display metadata only; status is always derived from member goals."""

    id: str
    title: str
    position: int
    description: str
    created_at: str
    updated_at: str


class PlatformControlStore:
    """Control-plane extension backed by the exact TaskStore SQLite database."""

    def __init__(self, task_store: TaskStore) -> None:
        self.task_store = task_store
        self._conn = task_store._conn
        self._lock = task_store._lock
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS platform_goals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    spec_markdown TEXT NOT NULL,
                    plan_markdown TEXT NOT NULL,
                    tasks_json TEXT NOT NULL,
                    acceptance_json TEXT NOT NULL,
                    artifact_digest TEXT NOT NULL,
                    executor_kind TEXT NOT NULL,
                    orchestration_mode TEXT NOT NULL,
                    binding_ref TEXT NOT NULL,
                    policy_ref TEXT NOT NULL,
                    window_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_goal_task_links (
                    goal_id TEXT NOT NULL REFERENCES platform_goals(id),
                    goal_revision INTEGER NOT NULL,
                    plan_task_id TEXT NOT NULL,
                    task_id TEXT NOT NULL REFERENCES tasks(id),
                    dependencies_json TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    PRIMARY KEY(goal_id, goal_revision, plan_task_id),
                    UNIQUE(task_id)
                );
                CREATE TABLE IF NOT EXISTS platform_autonomous_windows (
                    id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    policy_revision INTEGER NOT NULL,
                    policy_digest TEXT NOT NULL,
                    owner_identity TEXT NOT NULL,
                    confirmation TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    repositories_json TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    max_concurrent_tasks INTEGER NOT NULL,
                    max_tasks INTEGER NOT NULL,
                    max_retries INTEGER NOT NULL,
                    tasks_started INTEGER NOT NULL DEFAULT 0,
                    tasks_completed INTEGER NOT NULL DEFAULT 0,
                    retries_used INTEGER NOT NULL DEFAULT 0,
                    stop_reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(policy_id, policy_revision)
                );
                CREATE TABLE IF NOT EXISTS platform_operation_receipts (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    window_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    input_digest TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    remaining_tasks INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_coordinator_claims (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(id),
                    window_id TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    epoch INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_publications (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id),
                    repository TEXT NOT NULL,
                    base_branch TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    status TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    pr_url TEXT NOT NULL,
                    request_digest TEXT NOT NULL,
                    failure_classification TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_inbox_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    repository TEXT NOT NULL DEFAULT 'dddd2024/reverse-agent',
                    status TEXT NOT NULL DEFAULT 'CAPTURED',
                    promoted_goal_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_roadmap_phases (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_roadmap_phase_goals (
                    phase_id TEXT NOT NULL REFERENCES platform_roadmap_phases(id),
                    goal_id TEXT NOT NULL REFERENCES platform_goals(id),
                    attached_at TEXT NOT NULL,
                    PRIMARY KEY(phase_id, goal_id)
                );
                """
            )

    # Goal records -----------------------------------------------------

    def create_goal(
        self,
        *,
        title: str,
        objective: str,
        repository: str,
        idempotency_key: str,
        executor_kind: str = "opencode",
        orchestration_mode: str = "sequential_team",
        binding_ref: str = "",
        policy_ref: str = "",
        window_id: str = "",
    ) -> GoalRecord:
        title = title.strip()
        objective = objective.strip()
        repository = repository.strip()
        idempotency_key = idempotency_key.strip()
        if not title or not objective or "/" not in repository or not idempotency_key:
            raise TaskStoreError("invalid_goal_identity")
        if executor_kind not in {"opencode", "deterministic_fixture"}:
            raise TaskStoreError(f"unsupported_executor_kind:{executor_kind}")
        if orchestration_mode not in {"single", "sequential_team"}:
            raise TaskStoreError(f"unsupported_orchestration_mode:{orchestration_mode}")
        if orchestration_mode == "sequential_team" and executor_kind != "opencode":
            raise TaskStoreError("sequential_team_requires_opencode_executor")
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM platform_goals WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                if (
                    existing["title"] == title
                    and existing["objective"] == objective
                    and existing["repository"] == repository
                    and existing["executor_kind"] == executor_kind
                    and existing["orchestration_mode"] == orchestration_mode
                    and existing["binding_ref"] == binding_ref
                ):
                    return self._row_to_goal(existing)
                raise TaskStoreError("goal_idempotency_key_reused_with_different_request")
            now = _utc_now()
            goal_id = _id("goal")
            self._conn.execute(
                "INSERT INTO platform_goals VALUES (?, ?, ?, ?, 'DRAFT', 1, '', '', '[]', '[]', '', ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    goal_id,
                    title,
                    objective,
                    repository,
                    executor_kind,
                    orchestration_mode,
                    binding_ref,
                    policy_ref,
                    window_id,
                    idempotency_key,
                    now,
                    now,
                ),
            )
            return self.get_goal(goal_id)

    def get_goal(self, goal_id: str) -> GoalRecord:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_goals WHERE id = ?", (goal_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"goal_not_found:{goal_id}")
            return self._row_to_goal(row)

    def list_goals(self, *, limit: int = 100) -> tuple[GoalRecord, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_goals ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 500)),)
            ).fetchall()
            return tuple(self._row_to_goal(row) for row in rows)

    def list_window_goals(self, window_id: str) -> tuple[GoalRecord, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_goals WHERE window_id = ? ORDER BY created_at ASC",
                (window_id,),
            ).fetchall()
            return tuple(self._row_to_goal(row) for row in rows)

    def save_goal_plan(
        self,
        goal_id: str,
        *,
        expected_revision: int,
        spec_markdown: str,
        plan_markdown: str,
        tasks: Sequence[Mapping[str, Any]],
        acceptance_criteria: Sequence[str],
    ) -> GoalRecord:
        payload = {
            "goal_id": goal_id,
            "revision": expected_revision,
            "spec_markdown": spec_markdown,
            "plan_markdown": plan_markdown,
            "tasks": list(tasks),
            "acceptance_criteria": list(acceptance_criteria),
        }
        reject_sensitive_keys(payload)
        digest = sha256_json(payload)
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_goals SET status = 'PLANNED', spec_markdown = ?, plan_markdown = ?, "
                "tasks_json = ?, acceptance_json = ?, artifact_digest = ?, updated_at = ? "
                "WHERE id = ? AND revision = ? AND status IN ('DRAFT', 'PLANNED')",
                (
                    spec_markdown,
                    plan_markdown,
                    canonical_json(list(tasks)),
                    canonical_json(list(acceptance_criteria)),
                    digest,
                    _utc_now(),
                    goal_id,
                    expected_revision,
                ),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("goal_revision_or_state_mismatch")
            return self.get_goal(goal_id)

    def approve_goal(self, goal_id: str, *, expected_revision: int, policy_ref: str = "") -> GoalRecord:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_goals SET status = 'APPROVED', policy_ref = CASE WHEN ? = '' THEN policy_ref ELSE ? END, "
                "updated_at = ? WHERE id = ? AND revision = ? AND status = 'PLANNED' AND artifact_digest <> ''",
                (policy_ref, policy_ref, _utc_now(), goal_id, expected_revision),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("goal_not_approvable")
            return self.get_goal(goal_id)

    def amend_goal(self, goal_id: str, *, expected_revision: int, objective: str) -> GoalRecord:
        objective = objective.strip()
        if not objective:
            raise TaskStoreError("goal_objective_required")
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_goals SET objective = ?, status = 'DRAFT', revision = revision + 1, "
                "spec_markdown = '', plan_markdown = '', tasks_json = '[]', acceptance_json = '[]', "
                "artifact_digest = '', updated_at = ? WHERE id = ? AND revision = ? AND status <> 'RUNNING'",
                (objective, _utc_now(), goal_id, expected_revision),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("goal_revision_mismatch")
            return self.get_goal(goal_id)

    def link_goal_task(
        self,
        goal_id: str,
        *,
        goal_revision: int,
        plan_task_id: str,
        task_id: str,
        dependencies: Sequence[str],
        seq: int,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO platform_goal_task_links "
                "(goal_id, goal_revision, plan_task_id, task_id, dependencies_json, seq) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (goal_id, goal_revision, plan_task_id, task_id, canonical_json(list(dependencies)), seq),
            )

    def mark_goal_running(self, goal_id: str, *, revision: int, window_id: str) -> GoalRecord:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_goals SET status = 'RUNNING', window_id = ?, updated_at = ? "
                "WHERE id = ? AND revision = ? AND status = 'APPROVED'",
                (window_id, _utc_now(), goal_id, revision),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("goal_not_launchable")
            return self.get_goal(goal_id)

    def list_goal_tasks(self, goal_id: str) -> tuple[Mapping[str, Any], ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT l.goal_revision, l.plan_task_id, l.task_id, l.dependencies_json, l.seq, "
                "t.title, t.status, t.repository, t.orchestration_mode, t.failure_classification "
                "FROM platform_goal_task_links l JOIN tasks t ON t.id = l.task_id "
                "JOIN platform_goals g ON g.id = l.goal_id AND g.revision = l.goal_revision "
                "WHERE l.goal_id = ? ORDER BY l.seq ASC",
                (goal_id,),
            ).fetchall()
            return tuple(
                {
                    **dict(row),
                    "dependencies": tuple(json.loads(row["dependencies_json"] or "[]")),
                }
                for row in rows
            )

    def goal_id_for_task(self, task_id: str) -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT goal_id FROM platform_goal_task_links WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"goal_link_not_found:{task_id}")
            return str(row["goal_id"])

    def runnable_tasks(self, window_id: str, *, limit: int = 100) -> tuple[str, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT l.goal_id, l.goal_revision, l.plan_task_id, l.task_id, l.dependencies_json, l.seq "
                "FROM platform_goal_task_links l "
                "JOIN platform_goals g ON g.id = l.goal_id AND g.revision = l.goal_revision "
                "JOIN tasks t ON t.id = l.task_id "
                "WHERE g.window_id = ? AND g.status = 'RUNNING' AND t.status IN ('QUEUED', 'INTERRUPTED') "
                "ORDER BY g.created_at ASC, l.seq ASC LIMIT ?",
                (window_id, max(1, min(limit, 500))),
            ).fetchall()
            runnable: list[str] = []
            for row in rows:
                deps = tuple(json.loads(row["dependencies_json"] or "[]"))
                blocked = False
                for dep in deps:
                    dep_row = self._conn.execute(
                        "SELECT t.status FROM platform_goal_task_links l JOIN tasks t ON t.id = l.task_id "
                        "WHERE l.goal_id = ? AND l.goal_revision = ? AND l.plan_task_id = ?",
                        (row["goal_id"], row["goal_revision"], dep),
                    ).fetchone()
                    if dep_row is None or dep_row["status"] not in {
                        "READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"
                    }:
                        blocked = True
                        break
                if not blocked:
                    runnable.append(row["task_id"])
            return tuple(runnable)

    def refresh_goal_status(self, goal_id: str) -> GoalRecord:
        links = self.list_goal_tasks(goal_id)
        if not links:
            return self.get_goal(goal_id)
        statuses = {str(link["status"]) for link in links}
        if statuses <= {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
            status = "COMPLETED"
        elif statuses & {"FAILED", "BLOCKED", "CANCELLED"}:
            status = "BLOCKED"
        else:
            status = "RUNNING"
        with self._lock:
            self._conn.execute(
                "UPDATE platform_goals SET status = ?, updated_at = ? WHERE id = ?",
                (status, _utc_now(), goal_id),
            )
        return self.get_goal(goal_id)

    # Autonomous windows and receipts ---------------------------------

    def activate_window(self, payload: Mapping[str, Any], *, confirmation: str) -> AutonomousWindowRecord:
        reject_sensitive_keys(payload)
        if confirmation.strip() != "ACTIVATE":
            raise TaskStoreError("owner_activation_confirmation_required")
        digest = sha256_json(payload)
        window_id = str(payload.get("window_id") or _id("window"))
        now = _utc_now()
        repositories = tuple(str(v) for v in payload.get("repositories", ()))
        capabilities = tuple(str(v) for v in payload.get("capabilities", ()))
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO platform_autonomous_windows VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?, 0, 0, 0, '', ?, ?)",
                    (
                        window_id,
                        str(payload["policy_id"]),
                        int(payload["policy_revision"]),
                        digest,
                        str(payload["owner_identity"]),
                        "ACTIVATE",
                        str(payload["starts_at"]),
                        str(payload["expires_at"]),
                        canonical_json(list(repositories)),
                        canonical_json(list(capabilities)),
                        int(payload["max_concurrent_tasks"]),
                        int(payload["max_tasks"]),
                        int(payload.get("max_retries", 0)),
                        now,
                        now,
                    ),
                )
            except Exception as exc:
                existing = self._conn.execute(
                    "SELECT * FROM platform_autonomous_windows WHERE policy_id = ? AND policy_revision = ?",
                    (str(payload["policy_id"]), int(payload["policy_revision"])),
                ).fetchone()
                if existing is not None and existing["policy_digest"] == digest:
                    return self._row_to_window(existing)
                raise TaskStoreError(f"window_activation_failed:{exc}") from exc
        return self.get_window(window_id)

    def get_window(self, window_id: str) -> AutonomousWindowRecord:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_autonomous_windows WHERE id = ?", (window_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"window_not_found:{window_id}")
            return self._row_to_window(row)

    def list_windows(self, *, limit: int = 100) -> tuple[AutonomousWindowRecord, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_autonomous_windows ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
            return tuple(self._row_to_window(row) for row in rows)

    def active_window(self, *, now: str | None = None) -> AutonomousWindowRecord | None:
        current = now or _utc_now()
        with self._lock:
            self._conn.execute(
                "UPDATE platform_autonomous_windows SET status = 'EXPIRED', stop_reason = 'window_expired', updated_at = ? "
                "WHERE status = 'ACTIVE' AND expires_at <= ?",
                (_utc_now(), current),
            )
            row = self._conn.execute(
                "SELECT * FROM platform_autonomous_windows WHERE status = 'ACTIVE' "
                "AND starts_at <= ? AND expires_at > ? ORDER BY created_at DESC LIMIT 1",
                (current, current),
            ).fetchone()
            return self._row_to_window(row) if row is not None else None

    def stop_window(self, window_id: str, *, reason: str = "owner_stopped") -> AutonomousWindowRecord:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_autonomous_windows SET status = 'STOPPED', stop_reason = ?, updated_at = ? "
                "WHERE id = ? AND status = 'ACTIVE'",
                (reason[:200], _utc_now(), window_id),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("window_not_active")
        return self.get_window(window_id)

    def claim_task(
        self,
        *,
        window_id: str,
        task_id: str,
        owner: str,
        lease_ms: int,
    ) -> tuple[int, AutonomousWindowRecord]:
        with self._lock:
            return self._claim_task_locked(
                window_id=window_id,
                task_id=task_id,
                owner=owner,
                lease_ms=lease_ms,
            )

    def _claim_task_locked(
        self,
        *,
        window_id: str,
        task_id: str,
        owner: str,
        lease_ms: int,
    ) -> tuple[int, AutonomousWindowRecord]:
        now_ms = _utc_now_ms()
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            window = cur.execute(
                "SELECT * FROM platform_autonomous_windows WHERE id = ?", (window_id,)
            ).fetchone()
            if window is None or window["status"] != "ACTIVE":
                raise TaskStoreError("window_not_active")
            if str(window["expires_at"]) <= _utc_now():
                cur.execute(
                    "UPDATE platform_autonomous_windows SET status = 'EXPIRED', stop_reason = 'window_expired', updated_at = ? WHERE id = ?",
                    (_utc_now(), window_id),
                )
                raise TaskStoreError("window_expired")
            active_count = cur.execute(
                "SELECT COUNT(*) AS c FROM platform_coordinator_claims WHERE window_id = ? AND status = 'ACTIVE' AND expires_at_ms > ?",
                (window_id, now_ms),
            ).fetchone()["c"]
            if int(active_count) >= int(window["max_concurrent_tasks"]):
                raise TaskStoreError("window_wip_limit_reached")
            if int(window["tasks_started"]) >= int(window["max_tasks"]):
                raise TaskStoreError("window_task_budget_exhausted")
            task = cur.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if task is None or task["status"] not in {"QUEUED", "INTERRUPTED"}:
                raise TaskStoreError("task_not_claimable")
            if task["status"] == "INTERRUPTED" and int(window["retries_used"]) >= int(window["max_retries"]):
                raise TaskStoreError("window_retry_budget_exhausted")
            existing = cur.execute(
                "SELECT * FROM platform_coordinator_claims WHERE task_id = ?", (task_id,)
            ).fetchone()
            if existing is not None and existing["status"] == "ACTIVE" and int(existing["expires_at_ms"]) > now_ms:
                raise TaskStoreError("task_already_claimed")
            epoch = int(existing["epoch"]) + 1 if existing is not None else 1
            if existing is None:
                cur.execute(
                    "INSERT INTO platform_coordinator_claims VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)",
                    (task_id, window_id, owner, epoch, now_ms + lease_ms, _utc_now(), _utc_now()),
                )
            else:
                cur.execute(
                    "UPDATE platform_coordinator_claims SET window_id = ?, owner = ?, epoch = ?, expires_at_ms = ?, status = 'ACTIVE', updated_at = ? WHERE task_id = ?",
                    (window_id, owner, epoch, now_ms + lease_ms, _utc_now(), task_id),
                )
            if task["status"] == "INTERRUPTED":
                cur.execute(
                    "UPDATE platform_autonomous_windows SET tasks_started = tasks_started + 1, "
                    "retries_used = retries_used + 1, updated_at = ? WHERE id = ?",
                    (_utc_now(), window_id),
                )
            else:
                cur.execute(
                    "UPDATE platform_autonomous_windows SET tasks_started = tasks_started + 1, updated_at = ? WHERE id = ?",
                    (_utc_now(), window_id),
                )
            cur.execute("COMMIT")
            return epoch, self.get_window(window_id)
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
            raise TaskStoreError(f"coordinator_claim_failed:{exc}") from exc

    def abandon_task_claim(
        self,
        *,
        window_id: str,
        task_id: str,
        owner: str,
        epoch: int,
        reason: str,
    ) -> None:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_coordinator_claims SET status = 'FAILED', updated_at = ? "
                "WHERE task_id = ? AND window_id = ? AND owner = ? AND epoch = ? AND status = 'ACTIVE'",
                (_utc_now(), task_id, window_id, owner, epoch),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("coordinator_claim_fenced")
        self.append_receipt(
            window_id=window_id,
            operation_type="task_execution",
            capability="execute_task",
            repository=self.task_store.get_task(task_id).repository,
            subject_id=task_id,
            decision="allowed",
            reason="coordinator_execution_failed",
            input_payload={"task_id": task_id, "claim_epoch": epoch},
            result=reason[:300],
        )

    def complete_task_claim(
        self,
        *,
        window_id: str,
        task_id: str,
        owner: str,
        epoch: int,
        result: str,
    ) -> None:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_coordinator_claims SET status = 'COMPLETE', updated_at = ? "
                "WHERE task_id = ? AND window_id = ? AND owner = ? AND epoch = ? AND status = 'ACTIVE'",
                (_utc_now(), task_id, window_id, owner, epoch),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("coordinator_claim_fenced")
            self._conn.execute(
                "UPDATE platform_autonomous_windows SET tasks_completed = tasks_completed + 1, updated_at = ? WHERE id = ?",
                (_utc_now(), window_id),
            )
        self.append_receipt(
            window_id=window_id,
            operation_type="task_execution",
            capability="execute_task",
            repository=self.task_store.get_task(task_id).repository,
            subject_id=task_id,
            decision="allowed",
            reason="coordinator_claim_completed",
            input_payload={"task_id": task_id, "claim_epoch": epoch},
            result=result,
        )

    def append_receipt(
        self,
        *,
        window_id: str,
        operation_type: str,
        capability: str,
        repository: str,
        subject_id: str,
        decision: str,
        reason: str,
        input_payload: Mapping[str, Any],
        external_id: str = "",
        result: str = "",
    ) -> OperationReceipt:
        reject_sensitive_keys(input_payload)
        window = self.get_window(window_id)
        receipt_id = _id("receipt")
        with self._lock:
            self._conn.execute(
                "INSERT INTO platform_operation_receipts "
                "(id, window_id, operation_type, capability, repository, subject_id, decision, reason, "
                "input_digest, external_id, result, remaining_tasks, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt_id,
                    window_id,
                    operation_type,
                    capability,
                    repository,
                    subject_id,
                    decision,
                    reason[:300],
                    sha256_json(input_payload),
                    external_id,
                    result[:300],
                    max(0, window.max_tasks - window.tasks_started),
                    _utc_now(),
                ),
            )
        return self.list_receipts(window_id=window_id, limit=1)[0]

    def list_receipts(self, *, window_id: str, limit: int = 200) -> tuple[OperationReceipt, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_operation_receipts WHERE window_id = ? ORDER BY seq DESC LIMIT ?",
                (window_id, max(1, min(limit, 1000))),
            ).fetchall()
            return tuple(self._row_to_receipt(row) for row in rows)

    # Publication state ------------------------------------------------

    def get_publication(self, task_id: str) -> PublicationRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_publications WHERE task_id = ?", (task_id,)
            ).fetchone()
            return self._row_to_publication(row) if row is not None else None

    def upsert_publication(
        self,
        *,
        task_id: str,
        repository: str,
        base_branch: str,
        branch: str,
        status: str,
        request_digest: str,
        commit_sha: str = "",
        pr_number: int = 0,
        pr_url: str = "",
        failure_classification: str = "",
    ) -> PublicationRecord:
        if status not in PUBLICATION_STATES:
            raise TaskStoreError(f"invalid_publication_status:{status}")
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM platform_publications WHERE task_id = ?", (task_id,)
            ).fetchone()
            now = _utc_now()
            if existing is None:
                self._conn.execute(
                    "INSERT INTO platform_publications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        _id("publication"), task_id, repository, base_branch, branch,
                        status, commit_sha, pr_number, pr_url, request_digest,
                        failure_classification, now, now,
                    ),
                )
            else:
                if existing["request_digest"] != request_digest:
                    raise TaskStoreError("publication_request_digest_mismatch")
                self._conn.execute(
                    "UPDATE platform_publications SET status = ?, commit_sha = ?, pr_number = ?, pr_url = ?, "
                    "failure_classification = ?, updated_at = ? WHERE task_id = ?",
                    (status, commit_sha, pr_number, pr_url, failure_classification, now, task_id),
                )
        result = self.get_publication(task_id)
        assert result is not None
        return result

    def durable_workspace(self, task_id: str) -> Mapping[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT run_id, repository_base_sha, worktree_path, worktree_head_sha, accepted_checkpoint "
                "FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
            if row is None:
                raise TaskStoreError("publication_requires_durable_run")
            return dict(row)

    # Inbox display state ----------------------------------------------

    def capture_inbox_item(
        self,
        *,
        title: str,
        objective: str,
        repository: str = "dddd2024/reverse-agent",
    ) -> InboxItemRecord:
        title = title.strip()
        objective = objective.strip()
        repository = repository.strip() or "dddd2024/reverse-agent"
        if not title or not objective:
            raise TaskStoreError("inbox_item_title_and_objective_required")
        reject_sensitive_keys({"title": title, "objective": objective})
        now = _utc_now()
        item_id = _id("inbox")
        with self._lock:
            self._conn.execute(
                "INSERT INTO platform_inbox_items "
                "(id, title, objective, repository, status, promoted_goal_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'CAPTURED', '', ?, ?)",
                (item_id, title, objective, repository, now, now),
            )
        return self.get_inbox_item(item_id)

    def get_inbox_item(self, item_id: str) -> InboxItemRecord:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_inbox_items WHERE id = ?", (item_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"inbox_item_not_found:{item_id}")
            return self._row_to_inbox_item(row)

    def list_inbox_items(
        self, *, status: str | None = None, limit: int = 200
    ) -> tuple[InboxItemRecord, ...]:
        with self._lock:
            if status is not None:
                if status not in INBOX_STATES:
                    raise TaskStoreError(f"invalid_inbox_status:{status}")
                rows = self._conn.execute(
                    "SELECT * FROM platform_inbox_items WHERE status = ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (status, max(1, min(limit, 500))),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM platform_inbox_items ORDER BY created_at DESC LIMIT ?",
                    (max(1, min(limit, 500)),),
                ).fetchall()
            return tuple(self._row_to_inbox_item(row) for row in rows)

    def mark_inbox_item_promoted(self, item_id: str, *, goal_id: str) -> InboxItemRecord:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_inbox_items SET status = 'PROMOTED', promoted_goal_id = ?, "
                "updated_at = ? WHERE id = ? AND status = 'CAPTURED'",
                (goal_id, _utc_now(), item_id),
            )
            if cur.rowcount != 1:
                existing = self.get_inbox_item(item_id)
                if existing.status == "PROMOTED" and existing.promoted_goal_id == goal_id:
                    return existing
                raise TaskStoreError(f"inbox_item_not_promotable:{item_id}:{existing.status}")
        return self.get_inbox_item(item_id)

    def dismiss_inbox_item(self, item_id: str) -> InboxItemRecord:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE platform_inbox_items SET status = 'DISMISSED', updated_at = ? "
                "WHERE id = ? AND status = 'CAPTURED'",
                (_utc_now(), item_id),
            )
            if cur.rowcount != 1:
                existing = self.get_inbox_item(item_id)
                if existing.status == "DISMISSED":
                    return existing
                raise TaskStoreError(f"inbox_item_not_dismissable:{item_id}:{existing.status}")
        return self.get_inbox_item(item_id)

    # Roadmap display metadata -----------------------------------------

    def create_roadmap_phase(
        self,
        *,
        title: str,
        position: int,
        description: str = "",
    ) -> RoadmapPhaseRecord:
        title = title.strip()
        description = description.strip()
        if not title:
            raise TaskStoreError("roadmap_phase_title_required")
        reject_sensitive_keys({"title": title, "description": description})
        now = _utc_now()
        phase_id = _id("phase")
        with self._lock:
            self._conn.execute(
                "INSERT INTO platform_roadmap_phases "
                "(id, title, position, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (phase_id, title, int(position), description, now, now),
            )
        return self.get_roadmap_phase(phase_id)

    def get_roadmap_phase(self, phase_id: str) -> RoadmapPhaseRecord:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_roadmap_phases WHERE id = ?", (phase_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError(f"roadmap_phase_not_found:{phase_id}")
            return self._row_to_roadmap_phase(row)

    def list_roadmap_phases(self, *, limit: int = 100) -> tuple[RoadmapPhaseRecord, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_roadmap_phases ORDER BY position ASC, created_at ASC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
            return tuple(self._row_to_roadmap_phase(row) for row in rows)

    def attach_goal_to_phase(self, phase_id: str, goal_id: str) -> None:
        self.get_roadmap_phase(phase_id)
        self.get_goal(goal_id)
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO platform_roadmap_phase_goals (phase_id, goal_id, attached_at) "
                "VALUES (?, ?, ?)",
                (phase_id, goal_id, _utc_now()),
            )

    def detach_goal_from_phase(self, phase_id: str, goal_id: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM platform_roadmap_phase_goals WHERE phase_id = ? AND goal_id = ?",
                (phase_id, goal_id),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("roadmap_phase_goal_not_attached")

    def list_phase_goal_ids(self, phase_id: str) -> tuple[str, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT goal_id FROM platform_roadmap_phase_goals WHERE phase_id = ? "
                "ORDER BY attached_at ASC",
                (phase_id,),
            ).fetchall()
            return tuple(str(row["goal_id"]) for row in rows)

    # Serialization ----------------------------------------------------

    @staticmethod
    def _row_to_goal(row: Any) -> GoalRecord:
        return GoalRecord(
            id=row["id"], title=row["title"], objective=row["objective"], repository=row["repository"],
            status=row["status"], revision=int(row["revision"]), spec_markdown=row["spec_markdown"],
            plan_markdown=row["plan_markdown"], tasks=tuple(json.loads(row["tasks_json"] or "[]")),
            acceptance_criteria=tuple(json.loads(row["acceptance_json"] or "[]")),
            artifact_digest=row["artifact_digest"], executor_kind=row["executor_kind"],
            orchestration_mode=row["orchestration_mode"], binding_ref=row["binding_ref"],
            policy_ref=row["policy_ref"], window_id=row["window_id"], idempotency_key=row["idempotency_key"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_window(row: Any) -> AutonomousWindowRecord:
        return AutonomousWindowRecord(
            id=row["id"], policy_id=row["policy_id"], policy_revision=int(row["policy_revision"]),
            policy_digest=row["policy_digest"], owner_identity=row["owner_identity"],
            confirmation=row["confirmation"], starts_at=row["starts_at"], expires_at=row["expires_at"],
            status=row["status"], repositories=tuple(json.loads(row["repositories_json"] or "[]")),
            capabilities=tuple(json.loads(row["capabilities_json"] or "[]")),
            max_concurrent_tasks=int(row["max_concurrent_tasks"]), max_tasks=int(row["max_tasks"]),
            max_retries=int(row["max_retries"]), tasks_started=int(row["tasks_started"]),
            tasks_completed=int(row["tasks_completed"]), retries_used=int(row["retries_used"]),
            stop_reason=row["stop_reason"], created_at=row["created_at"], updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_receipt(row: Any) -> OperationReceipt:
        return OperationReceipt(
            id=row["id"], window_id=row["window_id"], operation_type=row["operation_type"],
            capability=row["capability"], repository=row["repository"], subject_id=row["subject_id"],
            decision=row["decision"], reason=row["reason"], input_digest=row["input_digest"],
            external_id=row["external_id"], result=row["result"], remaining_tasks=int(row["remaining_tasks"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_publication(row: Any) -> PublicationRecord:
        return PublicationRecord(
            id=row["id"], task_id=row["task_id"], repository=row["repository"], base_branch=row["base_branch"],
            branch=row["branch"], status=row["status"], commit_sha=row["commit_sha"],
            pr_number=int(row["pr_number"]), pr_url=row["pr_url"], request_digest=row["request_digest"],
            failure_classification=row["failure_classification"], created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_inbox_item(row: Any) -> InboxItemRecord:
        return InboxItemRecord(
            id=row["id"], title=row["title"], objective=row["objective"], repository=row["repository"],
            status=row["status"], promoted_goal_id=row["promoted_goal_id"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_roadmap_phase(row: Any) -> RoadmapPhaseRecord:
        return RoadmapPhaseRecord(
            id=row["id"], title=row["title"], position=int(row["position"]),
            description=row["description"], created_at=row["created_at"], updated_at=row["updated_at"],
        )
