"""Durable active-cancel intent fencing over existing TaskStore truth.

This module owns no process control. It records one Owner cancel intent against
an exact live durable lease generation and confirms it only at an unambiguous,
already-accepted durable checkpoint. Runtime/API/UI wiring is separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import time
from typing import Any, Mapping

from .run_store import TaskStore, TaskStoreError

REQUEST_EVENT_TYPE = "ACTIVE_CANCEL_REQUESTED"
CONFIRM_EVENT_TYPE = "ACTIVE_CANCEL_SAFE_BOUNDARY_CONFIRMED"
ACTIVE_STATUSES = frozenset({"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING"})
SAFE_CHECKPOINTS = frozenset({"PRE_PLANNER", "POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"})
_DOMAIN = "nerelan.active-cancel.generation.v1"
_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ActiveCancelState:
    request_id: str
    task_id: str
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


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def generation_digest(*, task_id: str, run_id: str, lease_epoch: int) -> str:
    return hashlib.sha256(_json({
        "domain": _DOMAIN,
        "task_id": str(task_id),
        "run_id": str(run_id),
        "lease_epoch": int(lease_epoch),
    }).encode("utf-8")).hexdigest()


def _request_id(digest: str) -> str:
    return f"active-cancel-{digest[:24]}"


def _request_event_id(digest: str) -> str:
    return f"event-active-cancel-request-{digest}"


def _confirm_event_id(digest: str) -> str:
    return f"event-active-cancel-confirm-{digest}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


def _rollback(cur: Any) -> None:
    try:
        cur.execute("ROLLBACK")
    except Exception:
        pass


def _decode(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        raise TaskStoreError("active_cancel_event_metadata_invalid")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise TaskStoreError("active_cancel_event_metadata_invalid") from exc
    if not isinstance(value, dict):
        raise TaskStoreError("active_cancel_event_metadata_invalid")
    return value


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in _HEX for c in value)


def _validated_event_digest(
    event: Any,
    metadata: Mapping[str, Any],
    *,
    confirmation: bool,
    expected_task_id: str,
) -> str:
    keys = {"request_id", "generation_digest", "phase"}
    if confirmation:
        keys.add("checkpoint")
    expected_phase = "CONFIRMED" if confirmation else "REQUESTED"
    if set(metadata) != keys or metadata.get("phase") != expected_phase:
        raise TaskStoreError("active_cancel_confirmation_metadata_invalid" if confirmation else "active_cancel_request_metadata_invalid")
    digest = metadata.get("generation_digest")
    if (
        not isinstance(metadata.get("request_id"), str)
        or not metadata.get("request_id")
        or not _valid_sha(digest)
        or (confirmation and metadata.get("checkpoint") not in SAFE_CHECKPOINTS)
    ):
        raise TaskStoreError("active_cancel_confirmation_metadata_invalid" if confirmation else "active_cancel_request_metadata_invalid")
    identity_error = "active_cancel_confirmation_identity_mismatch" if confirmation else "active_cancel_request_identity_mismatch"
    event_id = _confirm_event_id(digest) if confirmation else _request_event_id(digest)
    if (
        str(event["task_id"]) != str(expected_task_id)
        or metadata["request_id"] != _request_id(digest)
        or str(event["id"]) != event_id
    ):
        raise TaskStoreError(identity_error)
    return digest


def _live_lease(run: Any, now_ms: int) -> bool:
    return bool(str(run["lease_owner"])) and int(run["lease_epoch"]) > 0 and int(run["lease_expiry_ms"]) > now_ms


class ActiveCancelController:
    """Persist/inspect cancellation intent without changing execution state."""

    def __init__(self, store: TaskStore) -> None:
        self.store = store

    @staticmethod
    def _task(conn: Any, task_id: str) -> Any:
        row = conn.execute("SELECT id,status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise TaskStoreError(f"task_not_found:{task_id}")
        return row

    @staticmethod
    def _run(conn: Any, task_id: str) -> Any | None:
        return conn.execute(
            "SELECT run_id,lease_owner,lease_epoch,lease_expiry_ms,accepted_checkpoint,recovery_classification "
            "FROM durable_runs WHERE task_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1",
            (task_id,),
        ).fetchone()

    @staticmethod
    def _event_by_id(conn: Any, event_id: str, event_type: str, ambiguous_code: str) -> Any | None:
        rows = conn.execute(
            "SELECT id,task_id,timestamp,metadata FROM task_events WHERE id=? AND type=? ORDER BY seq DESC LIMIT 2",
            (event_id, event_type),
        ).fetchall()
        if len(rows) > 1:
            raise TaskStoreError(ambiguous_code)
        return rows[0] if rows else None

    def _request(self, conn: Any, digest: str) -> Any | None:
        return self._event_by_id(conn, _request_event_id(digest), REQUEST_EVENT_TYPE, "active_cancel_request_event_ambiguous")

    def _confirmation(self, conn: Any, digest: str) -> Any | None:
        return self._event_by_id(conn, _confirm_event_id(digest), CONFIRM_EVENT_TYPE, "active_cancel_confirmation_event_ambiguous")

    @staticmethod
    def _checkpoint_count(conn: Any, run_id: str, checkpoint: str) -> int:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM durable_checkpoint_history WHERE run_id=? AND checkpoint_name=?",
            (run_id, checkpoint),
        ).fetchone()
        return int(row["c"])

    def request_active_cancel(self, task_id: str) -> ActiveCancelOutcome:
        with self.store._lock:
            cur = self.store._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                if str(self._task(cur, task_id)["status"]) not in ACTIVE_STATUSES:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "STATUS_NOT_ACTIVE")
                run = self._run(cur, task_id)
                if run is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "NO_DURABLE_RUN")
                if not _live_lease(run, _utc_now_ms()):
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "NO_LIVE_DURABLE_LEASE")
                digest = generation_digest(task_id=task_id, run_id=str(run["run_id"]), lease_epoch=int(run["lease_epoch"]))
                existing = self._request(cur, digest)
                if existing is not None:
                    state = self._state(cur, existing, digest, task_id)
                    cur.execute("ROLLBACK")
                    confirmed = state.phase == "CONFIRMED"
                    return ActiveCancelOutcome(
                        "ALREADY_CONFIRMED" if confirmed else "ALREADY_REQUESTED",
                        "ACTIVE_CANCEL_ALREADY_CONFIRMED" if confirmed else "ACTIVE_CANCEL_ALREADY_REQUESTED",
                        state,
                    )
                now = _utc_now()
                metadata = {
                    "request_id": _request_id(digest),
                    "generation_digest": digest,
                    "phase": "REQUESTED",
                }
                cur.execute(
                    "INSERT INTO task_events(id,task_id,type,timestamp,title,description,raw_log,metadata) VALUES(?,?,?,?,?,?,'',?)",
                    (_request_event_id(digest), task_id, REQUEST_EVENT_TYPE, now, "Active cancel requested", "Owner cancel intent recorded for the current durable generation.", _json(metadata)),
                )
                cur.execute("UPDATE tasks SET updated_at=? WHERE id=?", (now, task_id))
                cur.execute("COMMIT")
                return ActiveCancelOutcome("REQUESTED", "ACTIVE_CANCEL_REQUESTED", ActiveCancelState(
                    _request_id(digest), task_id, digest, "REQUESTED", now, current=True
                ))
            except TaskStoreError:
                _rollback(cur)
                raise
            except Exception as exc:
                _rollback(cur)
                raise TaskStoreError("active_cancel_request_failed") from exc

    def current_state(self, task_id: str) -> ActiveCancelState | None:
        with self.store._lock:
            self._task(self.store._conn, task_id)
            request = self.store._conn.execute(
                "SELECT id,task_id,timestamp,metadata FROM task_events WHERE task_id=? AND type=? ORDER BY seq DESC LIMIT 1",
                (task_id, REQUEST_EVENT_TYPE),
            ).fetchone()
            if request is None:
                return None
            metadata = _decode(request["metadata"])
            digest = _validated_event_digest(request, metadata, confirmation=False, expected_task_id=task_id)
            # Detect duplicate deterministic request IDs as ambiguous persisted evidence.
            self._request(self.store._conn, digest)
            run = self._run(self.store._conn, task_id)
            current = "" if run is None else generation_digest(task_id=task_id, run_id=str(run["run_id"]), lease_epoch=int(run["lease_epoch"]))
            return self._state(self.store._conn, request, current, task_id, metadata)

    def auto_resume_allowed(self, task_id: str) -> bool:
        state = self.current_state(task_id)
        return state is None or not state.current

    def _state(self, conn: Any, request: Any, current_digest: str, expected_task_id: str, metadata: Mapping[str, Any] | None = None) -> ActiveCancelState:
        request_meta = dict(metadata) if metadata is not None else _decode(request["metadata"])
        digest = _validated_event_digest(request, request_meta, confirmation=False, expected_task_id=expected_task_id)
        current = bool(current_digest and digest == current_digest)
        confirm = self._confirmation(conn, digest)
        if confirm is None:
            return ActiveCancelState(
                _request_id(digest), str(request["task_id"]), digest,
                "REQUESTED" if current else "STALE", str(request["timestamp"]), current=current
            )
        confirm_meta = _decode(confirm["metadata"])
        if _validated_event_digest(confirm, confirm_meta, confirmation=True, expected_task_id=expected_task_id) != digest:
            raise TaskStoreError("active_cancel_confirmation_identity_mismatch")
        return ActiveCancelState(
            _request_id(digest), str(request["task_id"]), digest,
            "CONFIRMED" if current else "STALE", str(request["timestamp"]), str(confirm["timestamp"]), str(confirm_meta["checkpoint"]), current,
        )

    def confirm_safe_boundary(self, task_id: str, *, run_id: str, lease_owner: str, lease_epoch: int, checkpoint: str) -> ActiveCancelOutcome:
        with self.store._lock:
            cur = self.store._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                if str(self._task(cur, task_id)["status"]) not in ACTIVE_STATUSES:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "STATUS_NOT_ACTIVE")
                run = self._run(cur, task_id)
                if run is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "NO_DURABLE_RUN")
                if run_id != str(run["run_id"]) or lease_epoch != int(run["lease_epoch"]) or not lease_owner or lease_owner != str(run["lease_owner"]):
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "LEASE_FENCED")
                if not _live_lease(run, _utc_now_ms()):
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "NO_LIVE_DURABLE_LEASE")
                if checkpoint not in SAFE_CHECKPOINTS:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "CHECKPOINT_UNSAFE")
                if str(run["accepted_checkpoint"]) != checkpoint:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "CHECKPOINT_MISMATCH")
                count = self._checkpoint_count(cur, run_id, checkpoint)
                if count != 1:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "CHECKPOINT_EVIDENCE_MISSING" if count == 0 else "CHECKPOINT_EVIDENCE_AMBIGUOUS")
                digest = generation_digest(task_id=task_id, run_id=run_id, lease_epoch=lease_epoch)
                request = self._request(cur, digest)
                if request is None:
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("UNAVAILABLE", "NO_CANCEL_REQUEST")
                request_meta = _decode(request["metadata"])
                if _validated_event_digest(request, request_meta, confirmation=False, expected_task_id=task_id) != digest:
                    raise TaskStoreError("active_cancel_request_identity_mismatch")
                existing = self._confirmation(cur, digest)
                if existing is not None:
                    state = self._state(cur, request, digest, task_id, request_meta)
                    cur.execute("ROLLBACK")
                    return ActiveCancelOutcome("ALREADY_CONFIRMED", "ACTIVE_CANCEL_ALREADY_CONFIRMED", state)
                now = _utc_now()
                metadata = {
                    "request_id": _request_id(digest),
                    "generation_digest": digest,
                    "phase": "CONFIRMED",
                    "checkpoint": checkpoint,
                }
                cur.execute(
                    "INSERT INTO task_events(id,task_id,type,timestamp,title,description,raw_log,metadata) VALUES(?,?,?,?,?,?,'',?)",
                    (_confirm_event_id(digest), task_id, CONFIRM_EVENT_TYPE, now, "Active cancel reached safe boundary", "Current Owner cancel intent confirmed at an accepted checkpoint.", _json(metadata)),
                )
                cur.execute("UPDATE tasks SET updated_at=? WHERE id=?", (now, task_id))
                cur.execute("COMMIT")
                return ActiveCancelOutcome("CONFIRMED", "ACTIVE_CANCEL_SAFE_BOUNDARY_CONFIRMED", ActiveCancelState(
                    _request_id(digest), task_id, digest, "CONFIRMED", str(request["timestamp"]), now, checkpoint, True
                ))
            except TaskStoreError:
                _rollback(cur)
                raise
            except Exception as exc:
                _rollback(cur)
                raise TaskStoreError("active_cancel_confirmation_failed") from exc
