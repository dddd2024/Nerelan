"""Durable active-cancel intent fencing over existing TaskStore truth.

This module owns no executor/process control. It records an Owner cancel intent
against one exact durable lease generation and lets a caller confirm that intent
only at an already-accepted durable checkpoint. Runtime wiring (API,
DurableExecutionService, coordinator and UI) is deliberately separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from .run_store import TaskStore, TaskStoreError


REQUEST_EVENT_TYPE = "ACTIVE_CANCEL_REQUESTED"
CONFIRM_EVENT_TYPE = "ACTIVE_CANCEL_SAFE_BOUNDARY_CONFIRMED"

ACTIVE_STATUSES = frozenset(
    {"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING"}
)
SAFE_CHECKPOINTS = frozenset(
    {"PRE_PLANNER", "POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"}
)
_DOMAIN = "nerelan.active-cancel.generation.v1"


@dataclass(frozen=True)
class ActiveCancelState:
    request_id: str
    task_id: str
    run_id: str
    lease_epoch: int
    generation_digest: str
    phase: str
    requested_at: str
    confirmed_at: str = ""
    checkpoint: str = ""
    current: bool = False


@dataclass(frozen=True)
class ActiveCancelOutcome:
    status: str
    reason_code: str
    state: ActiveCancelState | None = None


class ActiveCancelController:
    """Persist and inspect cancellation intent without changing execution state."""

    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def request_active_cancel(self, task_id: str) -> ActiveCancelOutcome:
        """Bind one Owner cancel request to the exact current durable generation."""
        with self.store._lock:
            cur = self.store._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                task = self._task_row_locked(cur, task_id)
                status = str(task["status"])
                if status not in ACTIVE_STATUSES:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="STATUS_NOT_ACTIVE",
                    )

                run = self._latest_run_locked(cur, task_id)
                if run is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="NO_DURABLE_RUN",
                    )
                if not str(run["lease_owner"]) or int(run["lease_epoch"]) <= 0:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="NO_LIVE_DURABLE_LEASE",
                    )

                digest = generation_digest(
                    task_id=task_id,
                    run_id=str(run["run_id"]),
                    lease_epoch=int(run["lease_epoch"]),
                )
                request_id = _request_id(digest)
                existing = self._request_event_locked(cur, digest)
                if existing is not None:
                    state = self._state_from_request_locked(
                        cur, existing, current_digest=digest
                    )
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status=(
                            "ALREADY_CONFIRMED"
                            if state.phase == "CONFIRMED"
                            else "ALREADY_REQUESTED"
                        ),
                        reason_code=(
                            "ACTIVE_CANCEL_ALREADY_CONFIRMED"
                            if state.phase == "CONFIRMED"
                            else "ACTIVE_CANCEL_ALREADY_REQUESTED"
                        ),
                        state=state,
                    )

                now = _utc_now()
                metadata = {
                    "request_id": request_id,
                    "run_id": str(run["run_id"]),
                    "lease_epoch": int(run["lease_epoch"]),
                    "generation_digest": digest,
                    "phase": "REQUESTED",
                }
                cur.execute(
                    "INSERT INTO task_events "
                    "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, '', ?)",
                    (
                        _request_event_id(digest),
                        task_id,
                        REQUEST_EVENT_TYPE,
                        now,
                        "Active cancel requested",
                        "Owner cancel intent recorded for the current durable generation.",
                        _canonical_json(metadata),
                    ),
                )
                cur.execute(
                    "UPDATE tasks SET updated_at = ? WHERE id = ?",
                    (now, task_id),
                )
                cur.execute("COMMIT")
                return ActiveCancelOutcome(
                    status="REQUESTED",
                    reason_code="ACTIVE_CANCEL_REQUESTED",
                    state=ActiveCancelState(
                        request_id=request_id,
                        task_id=task_id,
                        run_id=str(run["run_id"]),
                        lease_epoch=int(run["lease_epoch"]),
                        generation_digest=digest,
                        phase="REQUESTED",
                        requested_at=now,
                        current=True,
                    ),
                )
            except TaskStoreError:
                _rollback(cur)
                raise
            except Exception as exc:
                _rollback(cur)
                raise TaskStoreError("active_cancel_request_failed") from exc

    def current_state(self, task_id: str) -> ActiveCancelState | None:
        """Read the newest request and classify it against current run generation."""
        with self.store._lock:
            self._task_row_locked(self.store._conn, task_id)
            request = self.store._conn.execute(
                "SELECT id, task_id, timestamp, metadata FROM task_events "
                "WHERE task_id = ? AND type = ? ORDER BY seq DESC LIMIT 1",
                (task_id, REQUEST_EVENT_TYPE),
            ).fetchone()
            if request is None:
                return None
            metadata = _decode_event_metadata(request["metadata"])
            run = self._latest_run_locked(self.store._conn, task_id)
            current_digest = ""
            if run is not None:
                current_digest = generation_digest(
                    task_id=task_id,
                    run_id=str(run["run_id"]),
                    lease_epoch=int(run["lease_epoch"]),
                )
            return self._state_from_request_locked(
                self.store._conn,
                request,
                current_digest=current_digest,
                metadata=metadata,
            )

    def auto_resume_allowed(self, task_id: str) -> bool:
        """Advisory coordinator predicate: current Owner cancel intent holds resume."""
        state = self.current_state(task_id)
        return state is None or not state.current

    def confirm_safe_boundary(
        self,
        task_id: str,
        *,
        run_id: str,
        lease_owner: str,
        lease_epoch: int,
        checkpoint: str,
    ) -> ActiveCancelOutcome:
        """Confirm a current request at an exact accepted fenced checkpoint.

        This method intentionally does not transition Task status or release a
        lease. A future runtime integration must stop at this confirmation
        result and perform its separately-governed state transition.
        """
        with self.store._lock:
            cur = self.store._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                task = self._task_row_locked(cur, task_id)
                if str(task["status"]) not in ACTIVE_STATUSES:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="STATUS_NOT_ACTIVE",
                    )

                run = self._latest_run_locked(cur, task_id)
                if run is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="NO_DURABLE_RUN",
                    )
                current_run_id = str(run["run_id"])
                current_epoch = int(run["lease_epoch"])
                current_owner = str(run["lease_owner"])
                if (
                    run_id != current_run_id
                    or lease_epoch != current_epoch
                    or not lease_owner
                    or lease_owner != current_owner
                ):
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="LEASE_FENCED",
                    )
                if checkpoint not in SAFE_CHECKPOINTS:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="CHECKPOINT_UNSAFE",
                    )
                accepted_checkpoint = str(run["accepted_checkpoint"])
                if accepted_checkpoint != checkpoint:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="CHECKPOINT_MISMATCH",
                    )

                digest = generation_digest(
                    task_id=task_id,
                    run_id=current_run_id,
                    lease_epoch=current_epoch,
                )
                request = self._request_event_locked(cur, digest)
                if request is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="UNAVAILABLE",
                        reason_code="NO_CANCEL_REQUEST",
                    )
                request_metadata = _decode_event_metadata(request["metadata"])
                if str(request_metadata.get("generation_digest", "")) != digest:
                    cur.execute("ROLLBACK")
                    raise TaskStoreError("active_cancel_request_identity_mismatch")

                existing_confirm = self._confirmation_event_locked(cur, digest)
                if existing_confirm is not None:
                    state = self._state_from_request_locked(
                        cur, request, current_digest=digest, metadata=request_metadata
                    )
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome(
                        status="ALREADY_CONFIRMED",
                        reason_code="ACTIVE_CANCEL_ALREADY_CONFIRMED",
                        state=state,
                    )

                now = _utc_now()
                metadata = {
                    "request_id": str(request_metadata["request_id"]),
                    "run_id": current_run_id,
                    "lease_epoch": current_epoch,
                    "generation_digest": digest,
                    "phase": "CONFIRMED",
                    "checkpoint": checkpoint,
                }
                cur.execute(
                    "INSERT INTO task_events "
                    "(id, task_id, type, timestamp, title, description, raw_log, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?, '', ?)",
                    (
                        _confirm_event_id(digest),
                        task_id,
                        CONFIRM_EVENT_TYPE,
                        now,
                        "Active cancel reached safe boundary",
                        "Current Owner cancel intent confirmed at an accepted checkpoint.",
                        _canonical_json(metadata),
                    ),
                )
                cur.execute(
                    "UPDATE tasks SET updated_at = ? WHERE id = ?",
                    (now, task_id),
                )
                cur.execute("COMMIT")
                return ActiveCancelOutcome(
                    status="CONFIRMED",
                    reason_code="ACTIVE_CANCEL_SAFE_BOUNDARY_CONFIRMED",
                    state=ActiveCancelState(
                        request_id=str(request_metadata["request_id"]),
                        task_id=task_id,
                        run_id=current_run_id,
                        lease_epoch=current_epoch,
                        generation_digest=digest,
                        phase="CONFIRMED",
                        requested_at=str(request["timestamp"]),
                        confirmed_at=now,
                        checkpoint=checkpoint,
                        current=True,
                    ),
                )
            except TaskStoreError:
                _rollback(cur)
                raise
            except Exception as exc:
                _rollback(cur)
                raise TaskStoreError("active_cancel_confirmation_failed") from exc

    @staticmethod
    def _task_row_locked(conn: Any, task_id: str) -> Any:
        row = conn.execute(
            "SELECT id, status FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise TaskStoreError(f"task_not_found:{task_id}")
        return row

    @staticmethod
    def _latest_run_locked(conn: Any, task_id: str) -> Any | None:
        return conn.execute(
            "SELECT dr.run_id, dr.lease_owner, dr.lease_epoch, "
            "dr.accepted_checkpoint, dr.recovery_classification "
            "FROM durable_runs dr WHERE dr.task_id = ? "
            "ORDER BY dr.created_at DESC, dr.rowid DESC LIMIT 1",
            (task_id,),
        ).fetchone()

    @staticmethod
    def _request_event_locked(conn: Any, digest: str) -> Any | None:
        return conn.execute(
            "SELECT id, task_id, timestamp, metadata FROM task_events "
            "WHERE id = ? AND type = ? ORDER BY seq DESC LIMIT 1",
            (_request_event_id(digest), REQUEST_EVENT_TYPE),
        ).fetchone()

    @staticmethod
    def _confirmation_event_locked(conn: Any, digest: str) -> Any | None:
        return conn.execute(
            "SELECT id, task_id, timestamp, metadata FROM task_events "
            "WHERE id = ? AND type = ? ORDER BY seq DESC LIMIT 1",
            (_confirm_event_id(digest), CONFIRM_EVENT_TYPE),
        ).fetchone()

    def _state_from_request_locked(
        self,
        conn: Any,
        request: Any,
        *,
        current_digest: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ActiveCancelState:
        request_metadata = (
            dict(metadata)
            if metadata is not None
            else _decode_event_metadata(request["metadata"])
        )
        _validate_request_metadata(request_metadata)
        digest = str(request_metadata["generation_digest"])
        current = bool(current_digest and digest == current_digest)
        confirmation = self._confirmation_event_locked(conn, digest)
        if confirmation is not None:
            confirmation_metadata = _decode_event_metadata(confirmation["metadata"])
            _validate_confirmation_metadata(confirmation_metadata)
            if str(confirmation_metadata["generation_digest"]) != digest:
                raise TaskStoreError("active_cancel_confirmation_identity_mismatch")
            phase = "CONFIRMED" if current else "STALE"
            confirmed_at = str(confirmation["timestamp"])
            checkpoint = str(confirmation_metadata["checkpoint"])
        else:
            phase = "REQUESTED" if current else "STALE"
            confirmed_at = ""
            checkpoint = ""
        return ActiveCancelState(
            request_id=str(request_metadata["request_id"]),
            task_id=str(request["task_id"]),
            run_id=str(request_metadata["run_id"]),
            lease_epoch=int(request_metadata["lease_epoch"]),
            generation_digest=digest,
            phase=phase,
            requested_at=str(request["timestamp"]),
            confirmed_at=confirmed_at,
            checkpoint=checkpoint,
            current=current,
        )


def generation_digest(*, task_id: str, run_id: str, lease_epoch: int) -> str:
    payload = {
        "domain": _DOMAIN,
        "task_id": str(task_id),
        "run_id": str(run_id),
        "lease_epoch": int(lease_epoch),
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _request_id(digest: str) -> str:
    return f"active-cancel-{digest[:24]}"


def _request_event_id(digest: str) -> str:
    return f"event-active-cancel-request-{digest}"


def _confirm_event_id(digest: str) -> str:
    return f"event-active-cancel-confirm-{digest}"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _decode_event_metadata(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        raise TaskStoreError("active_cancel_event_metadata_invalid")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise TaskStoreError("active_cancel_event_metadata_invalid") from exc
    if not isinstance(value, dict):
        raise TaskStoreError("active_cancel_event_metadata_invalid")
    return value


def _validate_request_metadata(metadata: Mapping[str, Any]) -> None:
    expected = {
        "request_id",
        "run_id",
        "lease_epoch",
        "generation_digest",
        "phase",
    }
    if set(metadata) != expected or metadata.get("phase") != "REQUESTED":
        raise TaskStoreError("active_cancel_request_metadata_invalid")
    if (
        not isinstance(metadata.get("request_id"), str)
        or not isinstance(metadata.get("run_id"), str)
        or type(metadata.get("lease_epoch")) is not int
        or int(metadata["lease_epoch"]) <= 0
        or not isinstance(metadata.get("generation_digest"), str)
        or len(str(metadata["generation_digest"])) != 64
    ):
        raise TaskStoreError("active_cancel_request_metadata_invalid")


def _validate_confirmation_metadata(metadata: Mapping[str, Any]) -> None:
    expected = {
        "request_id",
        "run_id",
        "lease_epoch",
        "generation_digest",
        "phase",
        "checkpoint",
    }
    if set(metadata) != expected or metadata.get("phase") != "CONFIRMED":
        raise TaskStoreError("active_cancel_confirmation_metadata_invalid")
    if (
        not isinstance(metadata.get("request_id"), str)
        or not isinstance(metadata.get("run_id"), str)
        or type(metadata.get("lease_epoch")) is not int
        or int(metadata["lease_epoch"]) <= 0
        or not isinstance(metadata.get("generation_digest"), str)
        or len(str(metadata["generation_digest"])) != 64
        or metadata.get("checkpoint") not in SAFE_CHECKPOINTS
    ):
        raise TaskStoreError("active_cancel_confirmation_metadata_invalid")


def _rollback(cur: Any) -> None:
    try:
        cur.execute("ROLLBACK")
    except Exception:
        pass


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
