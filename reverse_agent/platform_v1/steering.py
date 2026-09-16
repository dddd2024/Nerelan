"""Provider-free durable steering identity and safe-point queue semantics.

This module records bounded steering intent against exact existing Goal/Task/Run
truth. It deliberately performs no model call, executor action, lifecycle
transition, replan, approval, or authority expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping

from .control_store import PlatformControlStore
from .run_store import TaskStore, TaskStoreError, TERMINAL_STATUSES


ADVISORY_GUIDANCE = "ADVISORY_GUIDANCE"
PRIORITY_HINT = "PRIORITY_HINT"
OUTPUT_PREFERENCE = "OUTPUT_PREFERENCE"
CORRECTION_REQUEST = "CORRECTION_REQUEST"
REQUIREMENT_CHANGE_REQUEST = "REQUIREMENT_CHANGE_REQUEST"
OWNER_DECISION = "OWNER_DECISION"

QUEUED_FOR_SAFE_POINT = "QUEUED_FOR_SAFE_POINT"
PAUSE_AND_REPLAN_REQUIRED = "PAUSE_AND_REPLAN_REQUIRED"
NEW_AUTHORITY_REQUIRED = "NEW_AUTHORITY_REQUIRED"
APPLIED = "APPLIED"

_KINDS = frozenset({
    ADVISORY_GUIDANCE,
    PRIORITY_HINT,
    OUTPUT_PREFERENCE,
    CORRECTION_REQUEST,
    REQUIREMENT_CHANGE_REQUEST,
    OWNER_DECISION,
})
_STATUSES = frozenset({
    QUEUED_FOR_SAFE_POINT,
    PAUSE_AND_REPLAN_REQUIRED,
    NEW_AUTHORITY_REQUIRED,
    APPLIED,
})
_ACTIVE_TASK_STATUSES = frozenset({
    "PREPARING_WORKSPACE",
    "RUNNING",
    "RUNNING_FIXTURE",
    "VALIDATING",
    "INTERRUPTED",
})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,511}$")
_MAX_READ_LIMIT = 200


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _bounded_text(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise TaskStoreError(f"steering_{field}_invalid")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise TaskStoreError(f"steering_{field}_invalid")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise TaskStoreError(f"steering_{field}_invalid")
    return normalized


def _positive_revision(value: Any) -> int:
    if type(value) is not int or value < 1:
        raise TaskStoreError("steering_goal_revision_invalid")
    return value


def _read_limit(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= _MAX_READ_LIMIT:
        raise TaskStoreError("steering_limit_out_of_range")
    return value


def _disposition(kind: str) -> tuple[str, str]:
    if kind in {ADVISORY_GUIDANCE, PRIORITY_HINT, OUTPUT_PREFERENCE}:
        return QUEUED_FOR_SAFE_POINT, "IN_SCOPE_GUIDANCE_QUEUED"
    if kind == CORRECTION_REQUEST:
        return PAUSE_AND_REPLAN_REQUIRED, "MATERIAL_CORRECTION_REQUIRES_REPLAN"
    return NEW_AUTHORITY_REQUIRED, "MATERIAL_CHANGE_REQUIRES_NEW_AUTHORITY"


@dataclass(frozen=True, slots=True)
class SteeringRecord:
    steering_id: str
    goal_id: str
    goal_revision: int
    task_id: str
    run_id: str
    execution_id: str
    observed_checkpoint: str
    kind: str
    content_ref: str
    content_digest: str
    status: str
    reason_code: str
    sequence: int
    created_at: str
    applied_at_checkpoint: str


class SteeringService:
    """Durable, authority-neutral steering queue over exact current run truth."""

    def __init__(self, store: TaskStore) -> None:
        self.store = store
        self._conn = store._conn
        self._lock = store._lock
        # Initialize/reuse the canonical Goal tables on the same TaskStore DB.
        self._control = PlatformControlStore(store)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS platform_run_steering (
                    steering_id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    goal_revision INTEGER NOT NULL,
                    task_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    observed_checkpoint TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content_ref TEXT NOT NULL,
                    content_digest TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    applied_at_checkpoint TEXT NOT NULL DEFAULT '',
                    UNIQUE(run_id, sequence)
                );
                CREATE INDEX IF NOT EXISTS idx_platform_run_steering_run_seq
                    ON platform_run_steering(run_id, sequence);
                """
            )

    def submit(self, payload: Mapping[str, Any]) -> SteeringRecord:
        normalized = self._normalize_payload(payload)
        with self._write():
            existing = self._conn.execute(
                "SELECT * FROM platform_run_steering WHERE steering_id = ?",
                (normalized["steering_id"],),
            ).fetchone()
            if existing is not None:
                record = self._row_to_record(existing)
                if self._semantic_tuple(record) != self._payload_tuple(normalized):
                    raise TaskStoreError(
                        "steering_id_reused_with_different_request"
                    )
                return record

            self._validate_target(
                goal_id=normalized["goal_id"],
                goal_revision=normalized["goal_revision"],
                task_id=normalized["task_id"],
                run_id=normalized["run_id"],
                execution_id=normalized["execution_id"],
                expected_checkpoint=normalized["observed_checkpoint"],
            )
            status, reason = _disposition(normalized["kind"])
            row = self._conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS seq "
                "FROM platform_run_steering WHERE run_id = ?",
                (normalized["run_id"],),
            ).fetchone()
            sequence = int(row["seq"]) + 1
            self._conn.execute(
                """
                INSERT INTO platform_run_steering (
                    steering_id, goal_id, goal_revision, task_id, run_id,
                    execution_id, observed_checkpoint, kind, content_ref,
                    content_digest, status, reason_code, sequence, created_at,
                    applied_at_checkpoint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '')
                """,
                (
                    normalized["steering_id"],
                    normalized["goal_id"],
                    normalized["goal_revision"],
                    normalized["task_id"],
                    normalized["run_id"],
                    normalized["execution_id"],
                    normalized["observed_checkpoint"],
                    normalized["kind"],
                    normalized["content_ref"],
                    normalized["content_digest"],
                    status,
                    reason,
                    sequence,
                    _utc_now(),
                ),
            )
            return self._load_record(normalized["steering_id"])

    def mark_applied(
        self,
        steering_id: str,
        *,
        run_id: str,
        execution_id: str,
        expected_current_checkpoint: str,
        applied_at_checkpoint: str,
    ) -> SteeringRecord:
        sid = _bounded_text(steering_id, "id", maximum=240)
        run = _bounded_text(run_id, "run_id", maximum=240)
        execution = _bounded_text(execution_id, "execution_id", maximum=240)
        expected = _bounded_text(
            expected_current_checkpoint, "expected_checkpoint", maximum=160
        )
        applied = _bounded_text(
            applied_at_checkpoint, "applied_checkpoint", maximum=160
        )
        if applied != expected:
            raise TaskStoreError("steering_application_checkpoint_mismatch")

        with self._write():
            row = self._conn.execute(
                "SELECT * FROM platform_run_steering WHERE steering_id = ?",
                (sid,),
            ).fetchone()
            if row is None:
                raise TaskStoreError("steering_not_found")
            record = self._row_to_record(row)
            if record.run_id != run or record.execution_id != execution:
                raise TaskStoreError("steering_application_identity_mismatch")
            if record.status == APPLIED:
                if record.applied_at_checkpoint != applied:
                    raise TaskStoreError("steering_application_identity_mismatch")
                return record
            if record.status != QUEUED_FOR_SAFE_POINT:
                raise TaskStoreError("steering_disposition_not_applicable")
            if record.observed_checkpoint != expected:
                raise TaskStoreError("steering_checkpoint_stale")

            self._validate_target(
                goal_id=record.goal_id,
                goal_revision=record.goal_revision,
                task_id=record.task_id,
                run_id=record.run_id,
                execution_id=record.execution_id,
                expected_checkpoint=expected,
            )
            cur = self._conn.execute(
                "UPDATE platform_run_steering SET status = ?, reason_code = ?, "
                "applied_at_checkpoint = ? WHERE steering_id = ? AND status = ?",
                (
                    APPLIED,
                    "APPLIED_AT_SAFE_POINT",
                    applied,
                    sid,
                    QUEUED_FOR_SAFE_POINT,
                ),
            )
            if cur.rowcount != 1:
                raise TaskStoreError("steering_application_conflict")
            return self._load_record(sid)

    def get(self, steering_id: str) -> SteeringRecord:
        sid = _bounded_text(steering_id, "id", maximum=240)
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_run_steering WHERE steering_id = ?",
                (sid,),
            ).fetchone()
            if row is None:
                raise TaskStoreError("steering_not_found")
            return self._row_to_record(row)

    def list_for_run(
        self, run_id: str, *, limit: int = 100
    ) -> tuple[SteeringRecord, ...]:
        run = _bounded_text(run_id, "run_id", maximum=240)
        bounded = _read_limit(limit)
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM platform_run_steering WHERE run_id = ? "
                "ORDER BY sequence ASC LIMIT ?",
                (run, bounded),
            ).fetchall()
            return tuple(self._row_to_record(row) for row in rows)

    def _normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise TaskStoreError("steering_payload_must_be_object")
        allowed = {
            "steering_id",
            "goal_id",
            "goal_revision",
            "task_id",
            "run_id",
            "execution_id",
            "observed_checkpoint",
            "kind",
            "content_ref",
            "content_digest",
        }
        if set(map(str, payload.keys())) - allowed:
            raise TaskStoreError("steering_unknown_field")

        kind = _bounded_text(payload.get("kind"), "kind", maximum=64).upper()
        if kind not in _KINDS:
            raise TaskStoreError("steering_kind_unsupported")
        content_ref = _bounded_text(
            payload.get("content_ref"), "content_ref", maximum=512
        )
        if not _OPAQUE_REF_RE.fullmatch(content_ref):
            raise TaskStoreError("steering_content_ref_invalid")
        digest = _bounded_text(
            payload.get("content_digest"), "content_digest", maximum=64
        )
        if not _DIGEST_RE.fullmatch(digest):
            raise TaskStoreError("steering_content_digest_invalid")

        return {
            "steering_id": _bounded_text(
                payload.get("steering_id"), "id", maximum=240
            ),
            "goal_id": _bounded_text(payload.get("goal_id"), "goal_id", maximum=240),
            "goal_revision": _positive_revision(payload.get("goal_revision")),
            "task_id": _bounded_text(payload.get("task_id"), "task_id", maximum=240),
            "run_id": _bounded_text(payload.get("run_id"), "run_id", maximum=240),
            "execution_id": _bounded_text(
                payload.get("execution_id"), "execution_id", maximum=240
            ),
            "observed_checkpoint": _bounded_text(
                payload.get("observed_checkpoint"),
                "observed_checkpoint",
                maximum=160,
            ),
            "kind": kind,
            "content_ref": content_ref,
            "content_digest": digest,
        }

    def _validate_target(
        self,
        *,
        goal_id: str,
        goal_revision: int,
        task_id: str,
        run_id: str,
        execution_id: str,
        expected_checkpoint: str,
    ) -> None:
        goal = self._conn.execute(
            "SELECT revision FROM platform_goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if goal is None:
            raise TaskStoreError("steering_goal_not_found")
        if int(goal["revision"]) != goal_revision:
            raise TaskStoreError("steering_goal_revision_stale")

        link = self._conn.execute(
            "SELECT 1 FROM platform_goal_task_links "
            "WHERE goal_id = ? AND goal_revision = ? AND task_id = ? LIMIT 1",
            (goal_id, goal_revision, task_id),
        ).fetchone()
        if link is None:
            raise TaskStoreError("steering_task_goal_binding_mismatch")

        task = self._conn.execute(
            "SELECT status, execution_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if task is None:
            raise TaskStoreError("steering_task_not_found")
        task_status = str(task["status"])
        if task_status in TERMINAL_STATUSES or task_status not in _ACTIVE_TASK_STATUSES:
            raise TaskStoreError("steering_task_not_active")
        if str(task["execution_id"]) != execution_id:
            raise TaskStoreError("steering_task_execution_mismatch")

        run = self._conn.execute(
            "SELECT task_id, execution_id, accepted_checkpoint "
            "FROM durable_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if run is None:
            raise TaskStoreError("steering_run_not_found")
        if str(run["task_id"]) != task_id or str(run["execution_id"]) != execution_id:
            raise TaskStoreError("steering_run_identity_mismatch")
        if str(run["accepted_checkpoint"]) != expected_checkpoint:
            raise TaskStoreError("steering_checkpoint_stale")

    class _Write:
        def __init__(self, service: "SteeringService") -> None:
            self.service = service

        def __enter__(self) -> None:
            self.service._lock.acquire()
            if self.service._conn.in_transaction:
                self.service._lock.release()
                raise TaskStoreError("steering_nested_write_transaction")
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

    def _load_record(self, steering_id: str) -> SteeringRecord:
        row = self._conn.execute(
            "SELECT * FROM platform_run_steering WHERE steering_id = ?",
            (steering_id,),
        ).fetchone()
        if row is None:
            raise TaskStoreError("steering_write_failed")
        return self._row_to_record(row)

    @staticmethod
    def _semantic_tuple(record: SteeringRecord) -> tuple[Any, ...]:
        return (
            record.steering_id,
            record.goal_id,
            record.goal_revision,
            record.task_id,
            record.run_id,
            record.execution_id,
            record.observed_checkpoint,
            record.kind,
            record.content_ref,
            record.content_digest,
        )

    @staticmethod
    def _payload_tuple(payload: Mapping[str, Any]) -> tuple[Any, ...]:
        return (
            payload["steering_id"],
            payload["goal_id"],
            payload["goal_revision"],
            payload["task_id"],
            payload["run_id"],
            payload["execution_id"],
            payload["observed_checkpoint"],
            payload["kind"],
            payload["content_ref"],
            payload["content_digest"],
        )

    @staticmethod
    def _row_to_record(row: Any) -> SteeringRecord:
        if row is None or row["kind"] not in _KINDS or row["status"] not in _STATUSES:
            raise TaskStoreError("steering_corrupt_record")
        return SteeringRecord(
            steering_id=str(row["steering_id"]),
            goal_id=str(row["goal_id"]),
            goal_revision=int(row["goal_revision"]),
            task_id=str(row["task_id"]),
            run_id=str(row["run_id"]),
            execution_id=str(row["execution_id"]),
            observed_checkpoint=str(row["observed_checkpoint"]),
            kind=str(row["kind"]),
            content_ref=str(row["content_ref"]),
            content_digest=str(row["content_digest"]),
            status=str(row["status"]),
            reason_code=str(row["reason_code"]),
            sequence=int(row["sequence"]),
            created_at=str(row["created_at"]),
            applied_at_checkpoint=str(row["applied_at_checkpoint"]),
        )
