"""Durable provider-free scheduled-Goal occurrence admission.

Only Nerelan-specific trigger identity, missed-occurrence policy and Goal
admission live here. Mechanical scheduling, approval and execution remain
outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import uuid
from typing import Any, Mapping

from .control_store import PlatformControlStore, reject_sensitive_keys
from .goal_service import GoalService
from .run_store import TaskStore, TaskStoreError


ONE_TIME = "ONE_TIME"
FIXED_INTERVAL = "FIXED_INTERVAL"
ENABLED = "ENABLED"
DISABLED = "DISABLED"
SKIP = "SKIP"
LATEST_ONLY = "LATEST_ONLY"
CREATED = "CREATED"
SKIPPED_MISSED = "SKIPPED_MISSED"
SKIPPED_ACTIVE_BACKLOG = "SKIPPED_ACTIVE_BACKLOG"
NOT_DUE = "NOT_DUE"

_TRIGGER_KINDS = frozenset({ONE_TIME, FIXED_INTERVAL})
_TRIGGER_STATES = frozenset({ENABLED, DISABLED})
_MISSED_POLICIES = frozenset({SKIP, LATEST_ONLY})
_PERSISTED_OUTCOMES = frozenset({CREATED, SKIPPED_MISSED, SKIPPED_ACTIVE_BACKLOG})
_ACTIVE_GOAL_STATES = ("DRAFT", "PLANNED", "APPROVED", "RUNNING")
_ALLOWED_FIELDS = frozenset(
    {
        "idempotency_key", "kind", "title", "objective", "repository",
        "start_at_utc", "interval_seconds", "missed_policy",
        "max_lateness_seconds", "executor_kind", "orchestration_mode",
        "binding_ref", "policy_ref",
    }
)
_MIN_INTERVAL_SECONDS = 60
_MAX_INTERVAL_SECONDS = 2_678_400
_MAX_LATENESS_SECONDS = 604_800
_MAX_READ_LIMIT = 200
_RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(domain: str, value: Mapping[str, Any]) -> str:
    raw = domain.encode() + b"\0" + _canonical_json(value).encode()
    return hashlib.sha256(raw).hexdigest()


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise TaskStoreError("goal_trigger_naive_datetime")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime:
    raw = str(value).strip()
    if not _RFC3339_UTC_RE.fullmatch(raw):
        raise TaskStoreError("goal_trigger_start_at_must_be_rfc3339_utc")
    try:
        return datetime.fromisoformat(raw[:-1] + "+00:00").astimezone(timezone.utc).replace(microsecond=0)
    except ValueError as exc:
        raise TaskStoreError("goal_trigger_start_at_invalid") from exc


def _now_utc() -> str:
    return _format_utc(datetime.now(timezone.utc))


def _exact_int(value: Any, field: str) -> int:
    if type(value) is not int:
        raise TaskStoreError(f"goal_trigger_{field}_must_be_integer")
    return value


def _read_limit(limit: Any) -> int:
    value = _exact_int(limit, "limit")
    if not 1 <= value <= _MAX_READ_LIMIT:
        raise TaskStoreError("goal_trigger_limit_out_of_range")
    return value


@dataclass(frozen=True)
class GoalTriggerRecord:
    id: str
    idempotency_key: str
    status: str
    kind: str
    title: str
    objective: str
    repository: str
    start_at_utc: str
    interval_seconds: int
    missed_policy: str
    max_lateness_seconds: int
    executor_kind: str
    orchestration_mode: str
    binding_ref: str
    policy_ref: str
    definition_digest: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class GoalTriggerInvocation:
    trigger_id: str
    occurrence_digest: str
    scheduled_for_utc: str
    outcome: str
    goal_id: str
    reason_code: str
    created_at: str
    persisted: bool


class GoalTriggerService:
    """Compile due trigger occurrences into existing DRAFT Goal truth."""

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore | None = None,
        goal_service: GoalService | None = None,
    ) -> None:
        inherited = getattr(goal_service, "control_store", None)
        self.store = store
        self.control_store = control_store or inherited or PlatformControlStore(store)
        self.goal_service = goal_service or GoalService(store=store, control_store=self.control_store)
        if self.control_store.task_store is not store:
            raise TaskStoreError("goal_trigger_control_store_mismatch")
        if self.goal_service.store is not store or self.goal_service.control_store.task_store is not store:
            raise TaskStoreError("goal_trigger_goal_service_store_mismatch")
        self._conn, self._lock = store._conn, store._lock
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS platform_goal_triggers (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    start_at_utc TEXT NOT NULL,
                    interval_seconds INTEGER NOT NULL,
                    missed_policy TEXT NOT NULL,
                    max_lateness_seconds INTEGER NOT NULL,
                    executor_kind TEXT NOT NULL,
                    orchestration_mode TEXT NOT NULL,
                    binding_ref TEXT NOT NULL,
                    policy_ref TEXT NOT NULL,
                    definition_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS platform_goal_trigger_invocations (
                    trigger_id TEXT NOT NULL REFERENCES platform_goal_triggers(id),
                    occurrence_digest TEXT NOT NULL,
                    scheduled_for_utc TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    goal_id TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(trigger_id, occurrence_digest)
                );
                """
            )

    def create(self, payload: Mapping[str, Any]) -> GoalTriggerRecord:
        definition, idempotency_key = self._normalize_definition(payload)
        definition_digest = _digest("nerelan.goal-trigger.definition.v1", definition)
        with self._write():
            row = self._conn.execute(
                "SELECT * FROM platform_goal_triggers WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if row is not None:
                if row["definition_digest"] != definition_digest:
                    raise TaskStoreError(
                        "goal_trigger_idempotency_key_reused_with_different_definition"
                    )
                return self._row_to_trigger(row)

            now, trigger_id = _now_utc(), f"trigger-{uuid.uuid4().hex}"
            self._conn.execute(
                """
                INSERT INTO platform_goal_triggers (
                    id, idempotency_key, status, kind, title, objective, repository,
                    start_at_utc, interval_seconds, missed_policy, max_lateness_seconds,
                    executor_kind, orchestration_mode, binding_ref, policy_ref,
                    definition_digest, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trigger_id, idempotency_key, ENABLED, definition["kind"],
                    definition["title"], definition["objective"], definition["repository"],
                    definition["start_at_utc"], definition["interval_seconds"],
                    definition["missed_policy"], definition["max_lateness_seconds"],
                    definition["executor_kind"], definition["orchestration_mode"],
                    definition["binding_ref"], definition["policy_ref"], definition_digest,
                    now, now,
                ),
            )
            return self._row_to_trigger(
                self._conn.execute(
                    "SELECT * FROM platform_goal_triggers WHERE id = ?", (trigger_id,)
                ).fetchone()
            )

    def get(self, trigger_id: str) -> GoalTriggerRecord:
        trigger_id = str(trigger_id).strip()
        if not trigger_id:
            raise TaskStoreError("goal_trigger_id_required")
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_goal_triggers WHERE id = ?", (trigger_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError("goal_trigger_not_found")
            return self._row_to_trigger(row)

    def list(self, *, limit: int = 100) -> tuple[GoalTriggerRecord, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_goal_triggers "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (_read_limit(limit),),
            ).fetchall()
            return tuple(self._row_to_trigger(row) for row in rows)

    def list_invocations(
        self, trigger_id: str, *, limit: int = 100
    ) -> tuple[GoalTriggerInvocation, ...]:
        trigger_id = str(trigger_id).strip()
        if not trigger_id:
            raise TaskStoreError("goal_trigger_id_required")
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_goal_trigger_invocations WHERE trigger_id = ? "
                "ORDER BY created_at DESC, scheduled_for_utc DESC, occurrence_digest DESC LIMIT ?",
                (trigger_id, _read_limit(limit)),
            ).fetchall()
            return tuple(self._row_to_invocation(row) for row in rows)

    def disable(self, trigger_id: str) -> GoalTriggerRecord:
        trigger_id = str(trigger_id).strip()
        with self._write():
            row = self._conn.execute(
                "SELECT * FROM platform_goal_triggers WHERE id = ?", (trigger_id,)
            ).fetchone()
            if row is None:
                raise TaskStoreError("goal_trigger_not_found")
            if row["status"] == ENABLED:
                self._conn.execute(
                    "UPDATE platform_goal_triggers SET status = ?, updated_at = ? "
                    "WHERE id = ? AND status = ?",
                    (DISABLED, _now_utc(), trigger_id, ENABLED),
                )
                row = self._conn.execute(
                    "SELECT * FROM platform_goal_triggers WHERE id = ?", (trigger_id,)
                ).fetchone()
            return self._row_to_trigger(row)

    def fire_due(self, trigger_id: str, *, now: datetime) -> GoalTriggerInvocation:
        now = self._normalize_now(now)
        now_epoch = int(now.timestamp())
        with self._write():
            row = self._conn.execute(
                "SELECT * FROM platform_goal_triggers WHERE id = ?",
                (str(trigger_id).strip(),),
            ).fetchone()
            if row is None:
                raise TaskStoreError("goal_trigger_not_found")
            trigger = self._row_to_trigger(row)
            if trigger.status == DISABLED:
                return self._transient(trigger.id, DISABLED, "TRIGGER_DISABLED")

            scheduled_epoch = self._latest_due_epoch(trigger, now_epoch)
            if scheduled_epoch is None:
                return self._transient(trigger.id, NOT_DUE, "BEFORE_START")

            scheduled_for = _format_utc(
                datetime.fromtimestamp(scheduled_epoch, tz=timezone.utc)
            )
            occurrence_digest = _digest(
                "nerelan.goal-trigger.occurrence.v1",
                {"trigger_id": trigger.id, "scheduled_for_utc": scheduled_for},
            )
            existing = self._conn.execute(
                "SELECT * FROM platform_goal_trigger_invocations "
                "WHERE trigger_id = ? AND occurrence_digest = ?",
                (trigger.id, occurrence_digest),
            ).fetchone()
            if existing is not None:
                return self._row_to_invocation(existing)

            if (
                trigger.missed_policy == SKIP
                and now_epoch - scheduled_epoch > trigger.max_lateness_seconds
            ):
                return self._insert_invocation(
                    trigger.id, occurrence_digest, scheduled_for,
                    SKIPPED_MISSED, "", "MISSED_LATENESS_EXCEEDED"
                )
            if trigger.kind == FIXED_INTERVAL and self._has_active_backlog(trigger.id):
                return self._insert_invocation(
                    trigger.id, occurrence_digest, scheduled_for,
                    SKIPPED_ACTIVE_BACKLOG, "", "ACTIVE_TRIGGER_GOAL_EXISTS"
                )

            goal = self.goal_service.create(
                {
                    "title": trigger.title,
                    "objective": trigger.objective,
                    "repository": trigger.repository,
                    "idempotency_key": f"goal-trigger:{trigger.id}:{occurrence_digest}",
                    "executor_kind": trigger.executor_kind,
                    "orchestration_mode": trigger.orchestration_mode,
                    "binding_ref": trigger.binding_ref,
                    "policy_ref": trigger.policy_ref,
                }
            )
            if goal.status != "DRAFT":
                raise TaskStoreError("goal_trigger_created_goal_not_draft")
            return self._insert_invocation(
                trigger.id, occurrence_digest, scheduled_for,
                CREATED, goal.id, "DRAFT_GOAL_CREATED"
            )

    def _normalize_definition(
        self, payload: Mapping[str, Any]
    ) -> tuple[dict[str, Any], str]:
        if not isinstance(payload, Mapping):
            raise TaskStoreError("goal_trigger_payload_must_be_object")
        reject_sensitive_keys(payload)
        if set(map(str, payload.keys())) - _ALLOWED_FIELDS:
            raise TaskStoreError("goal_trigger_unknown_field")

        idempotency_key = str(payload.get("idempotency_key", "")).strip()
        kind = str(payload.get("kind", "")).strip().upper()
        missed_policy = str(payload.get("missed_policy", LATEST_ONLY)).strip().upper()
        executor_kind = str(payload.get("executor_kind", "opencode")).strip()
        orchestration_mode = str(payload.get("orchestration_mode", "sequential_team")).strip()
        interval = _exact_int(payload.get("interval_seconds", 0), "interval_seconds")
        lateness = _exact_int(payload.get("max_lateness_seconds", 0), "max_lateness_seconds")
        objective = str(payload.get("objective", "")).strip()
        repository = str(payload.get("repository", "")).strip()

        if not idempotency_key:
            raise TaskStoreError("goal_trigger_idempotency_key_required")
        if len(idempotency_key) > 256:
            raise TaskStoreError("goal_trigger_idempotency_key_too_long")
        if not objective:
            raise TaskStoreError("goal_trigger_objective_required")
        if not repository or "/" not in repository:
            raise TaskStoreError("goal_trigger_repository_invalid")
        if kind not in _TRIGGER_KINDS:
            raise TaskStoreError("goal_trigger_kind_unsupported")
        if missed_policy not in _MISSED_POLICIES:
            raise TaskStoreError("goal_trigger_missed_policy_unsupported")
        if executor_kind not in {"opencode", "deterministic_fixture"}:
            raise TaskStoreError("goal_trigger_executor_kind_unsupported")
        if orchestration_mode not in {"single", "sequential_team"}:
            raise TaskStoreError("goal_trigger_orchestration_mode_unsupported")
        if orchestration_mode == "sequential_team" and executor_kind != "opencode":
            raise TaskStoreError("goal_trigger_sequential_team_requires_opencode")
        if kind == ONE_TIME and interval != 0:
            raise TaskStoreError("goal_trigger_one_time_interval_must_be_zero")
        if kind == FIXED_INTERVAL and not _MIN_INTERVAL_SECONDS <= interval <= _MAX_INTERVAL_SECONDS:
            raise TaskStoreError("goal_trigger_interval_out_of_range")
        if not 0 <= lateness <= _MAX_LATENESS_SECONDS:
            raise TaskStoreError("goal_trigger_max_lateness_out_of_range")

        definition = {
            "kind": kind,
            "title": str(payload.get("title", "")).strip(),
            "objective": objective,
            "repository": repository,
            "start_at_utc": _format_utc(_parse_utc(payload.get("start_at_utc", ""))),
            "interval_seconds": interval,
            "missed_policy": missed_policy,
            "max_lateness_seconds": lateness,
            "executor_kind": executor_kind,
            "orchestration_mode": orchestration_mode,
            "binding_ref": str(payload.get("binding_ref", "")).strip(),
            "policy_ref": str(payload.get("policy_ref", "")).strip(),
        }
        return definition, idempotency_key

    def _has_active_backlog(self, trigger_id: str) -> bool:
        placeholders = ",".join("?" for _ in _ACTIVE_GOAL_STATES)
        return self._conn.execute(
            f"""
            SELECT 1 FROM platform_goal_trigger_invocations AS i
            JOIN platform_goals AS g ON g.id = i.goal_id
            WHERE i.trigger_id = ? AND i.outcome = ?
              AND g.status IN ({placeholders})
            LIMIT 1
            """,
            (trigger_id, CREATED, *_ACTIVE_GOAL_STATES),
        ).fetchone() is not None

    @staticmethod
    def _latest_due_epoch(trigger: GoalTriggerRecord, now_epoch: int) -> int | None:
        start = int(_parse_utc(trigger.start_at_utc).timestamp())
        if now_epoch < start:
            return None
        if trigger.kind == ONE_TIME:
            return start
        return start + ((now_epoch - start) // trigger.interval_seconds) * trigger.interval_seconds

    @staticmethod
    def _normalize_now(now: datetime) -> datetime:
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise TaskStoreError("goal_trigger_now_must_be_timezone_aware")
        return now.astimezone(timezone.utc).replace(microsecond=0)

    def _insert_invocation(
        self,
        trigger_id: str,
        occurrence_digest: str,
        scheduled_for: str,
        outcome: str,
        goal_id: str,
        reason_code: str,
    ) -> GoalTriggerInvocation:
        self._conn.execute(
            "INSERT INTO platform_goal_trigger_invocations "
            "(trigger_id, occurrence_digest, scheduled_for_utc, outcome, goal_id, reason_code, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trigger_id, occurrence_digest, scheduled_for, outcome, goal_id, reason_code, _now_utc()),
        )
        row = self._conn.execute(
            "SELECT * FROM platform_goal_trigger_invocations "
            "WHERE trigger_id = ? AND occurrence_digest = ?",
            (trigger_id, occurrence_digest),
        ).fetchone()
        if row is None:
            raise TaskStoreError("goal_trigger_invocation_write_failed")
        return self._row_to_invocation(row)

    @staticmethod
    def _transient(trigger_id: str, outcome: str, reason: str) -> GoalTriggerInvocation:
        return GoalTriggerInvocation(trigger_id, "", "", outcome, "", reason, "", False)

    class _Write:
        def __init__(self, service: "GoalTriggerService") -> None:
            self.service = service

        def __enter__(self) -> None:
            self.service._lock.acquire()
            if self.service._conn.in_transaction:
                self.service._lock.release()
                raise TaskStoreError("goal_trigger_nested_write_transaction")
            try:
                self.service._conn.execute("BEGIN IMMEDIATE")
            except BaseException:
                self.service._lock.release()
                raise

        def __exit__(self, exc_type, exc, tb) -> bool:
            try:
                if exc_type is None:
                    self.service._conn.execute("COMMIT")
                elif self.service._conn.in_transaction:
                    self.service._conn.execute("ROLLBACK")
            finally:
                self.service._lock.release()
            return False

    def _write(self) -> "_Write":
        return self._Write(self)

    @staticmethod
    def _row_to_trigger(row: Any) -> GoalTriggerRecord:
        if row is None:
            raise TaskStoreError("goal_trigger_corrupt_row")
        if row["status"] not in _TRIGGER_STATES or row["kind"] not in _TRIGGER_KINDS:
            raise TaskStoreError("goal_trigger_corrupt_state")
        if row["missed_policy"] not in _MISSED_POLICIES:
            raise TaskStoreError("goal_trigger_corrupt_missed_policy")
        return GoalTriggerRecord(
            id=str(row["id"]),
            idempotency_key=str(row["idempotency_key"]),
            status=str(row["status"]),
            kind=str(row["kind"]),
            title=str(row["title"]),
            objective=str(row["objective"]),
            repository=str(row["repository"]),
            start_at_utc=str(row["start_at_utc"]),
            interval_seconds=int(row["interval_seconds"]),
            missed_policy=str(row["missed_policy"]),
            max_lateness_seconds=int(row["max_lateness_seconds"]),
            executor_kind=str(row["executor_kind"]),
            orchestration_mode=str(row["orchestration_mode"]),
            binding_ref=str(row["binding_ref"]),
            policy_ref=str(row["policy_ref"]),
            definition_digest=str(row["definition_digest"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _row_to_invocation(row: Any) -> GoalTriggerInvocation:
        if row is None or row["outcome"] not in _PERSISTED_OUTCOMES:
            raise TaskStoreError("goal_trigger_corrupt_invocation")
        return GoalTriggerInvocation(
            trigger_id=str(row["trigger_id"]),
            occurrence_digest=str(row["occurrence_digest"]),
            scheduled_for_utc=str(row["scheduled_for_utc"]),
            outcome=str(row["outcome"]),
            goal_id=str(row["goal_id"]),
            reason_code=str(row["reason_code"]),
            created_at=str(row["created_at"]),
            persisted=True,
        )
