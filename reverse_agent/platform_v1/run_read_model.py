"""Agent Runs: a bounded read model derived from TaskStore truth.

The module has no runtime state machine and never writes to either store. It
projects only persisted task/event fields and a deliberately small durable-run
observation. Raw logs and unrestricted event metadata never cross this boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Callable, Mapping, Sequence

from .control_store import PlatformControlStore
from .run_store import TaskStore, TaskStoreError

MAX_RUNS = 100
MAX_ACTIVITY = 5
MAX_DETAIL_EVENTS = 100
STALE_AFTER_SECONDS = 600

BACKEND_STATUS_TO_FRONTEND_STATE: dict[str, str] = {
    "QUEUED": "WAITING_FOR_OWNER",
    "PREPARING_WORKSPACE": "RUNNING",
    "RUNNING": "RUNNING",
    "RUNNING_FIXTURE": "RUNNING",
    "VALIDATING": "RUNNING",
    "READY_FOR_REVIEW": "READY_FOR_HUMAN",
    "READY_FOR_REVIEW_FIXTURE": "READY_FOR_HUMAN",
    "BLOCKED": "BLOCKED_EXTERNAL",
    "FAILED": "FAILED_TERMINAL",
    "CANCELLED": "FAILED_TERMINAL",
}

ACTIVITY_CATEGORIES = frozenset({
    "PLAN", "READ", "SEARCH", "EDIT", "COMMAND", "TEST", "VERIFY",
    "AGENT_STARTED", "AGENT_WAITING", "AGENT_COMPLETED", "CHECKPOINT",
    "RECOVERY", "BLOCKED", "OWNER_ACTION_REQUIRED", "PUBLICATION",
})
AGENT_ROLES = frozenset({
    "planner", "coder", "reviewer", "verifier", "executor", "test", "complete",
})
WORKER_EVENT_TYPES = frozenset({
    "WORKSPACE_READY", "EXECUTOR_RUNNING", "EXECUTOR_FINISHED", "LOCAL_VALIDATED",
})
LIVENESS_STATES = frozenset({
    "ACTIVE", "WAITING", "VALIDATING", "BLOCKED", "OWNER_ACTION_REQUIRED",
    "STALE", "TERMINAL", "UNKNOWN",
})
_SENSITIVE_RE = re.compile(
    r"(?i)(authorization|bearer|api[_-]?key|access[_-]?token|password|secret|"
    r"credential|private[_-]?key|chain[_-]?of[_-]?thought|prompt|response|"
    r"tool[_-]?payload|environment|worktree|checkpoint[_-]?db|lease[_-]?owner|"
    r"authority[_-]?payload)"
)
_OPAQUE_SECRET_RE = re.compile(
    r"(?i)(?:"
    r"(?<![a-z0-9])(?:sk|rk|pk|gh[pousr]|github_pat|xox[baprs])[-_][a-z0-9_-]{8,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?:https?|ssh)://[^/\s:@]+:[^/\s@]+@"
    r")"
)
_MAX_TEXT = 256
_MAX_PATH = 512
_MAX_METADATA_JSON = 4096
_TRUSTED_COMMAND_IDS = frozenset({
    "git_diff_check", "git_status_porcelain", "append_to_file", "write_file",
})
_METADATA_KEYS = frozenset({
    "activity_kind", "category", "status", "role", "agent_id", "worker_id",
    "execution_id", "path", "file", "validation_command_id",
    "validation_exit_code", "exit_code", "changed_file_count", "failure_classification",
    "waiting_reason", "checkpoint", "recovery_classification", "mutation_command_id",
    "fixture_path",
})


def backend_status_to_frontend_state(status: str) -> str:
    return BACKEND_STATUS_TO_FRONTEND_STATE.get(status, "WAITING_FOR_OWNER")


def _safe_text(value: Any, *, limit: int = _MAX_TEXT) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or _SENSITIVE_RE.search(value) or _OPAQUE_SECRET_RE.search(value):
        return ""
    return value[:limit]


def _safe_int(value: Any) -> int | None:
    if type(value) is bool:
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _safe_role(value: Any) -> str:
    role = _safe_text(value, limit=32).lower()
    return role if role in AGENT_ROLES else ""


def _safe_path(value: Any) -> str:
    path = _safe_text(value, limit=_MAX_PATH)
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    if (
        normalized.startswith(("/", "//"))
        or re.match(r"^[A-Za-z]:/", normalized)
        or "://" in normalized
        or any(part == ".." for part in normalized.split("/"))
    ):
        return ""
    return normalized


def _safe_reference(value: Any) -> str:
    reference = _safe_text(value, limit=128)
    if not reference or not re.fullmatch(r"[A-Za-z0-9._:/#-]+", reference):
        return ""
    return reference


def _derived_agent_id(execution_id: str, role: str) -> str:
    if not execution_id:
        return ""
    return f"{execution_id}:{role}" if role else execution_id


def _hashed_agent_id(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    identity = value.strip()
    if not identity or len(identity) > 512:
        return ""
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"agent-{digest}"


def _safe_command_id(value: Any) -> str:
    command_id = _safe_text(value, limit=64)
    return command_id if command_id in _TRUSTED_COMMAND_IDS else ""


def _metadata(event: Mapping[str, Any]) -> dict[str, Any]:
    raw = event.get("metadata", {})
    if isinstance(raw, Mapping):
        source = raw
    elif isinstance(raw, str):
        if len(raw) > _MAX_METADATA_JSON:
            return {}
        try:
            decoded = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        source = decoded if isinstance(decoded, Mapping) else {}
    else:
        return {}
    return {key: source[key] for key in _METADATA_KEYS if key in source}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _time_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _checkpoint_stage(checkpoint: str, role: str) -> str:
    if role == "planner" or checkpoint == "PRE_PLANNER":
        return "PLAN"
    if role == "coder" or checkpoint == "POST_PLANNER":
        return "EXECUTE"
    if role in {"reviewer", "verifier"} or checkpoint in {"POST_CODER", "POST_REVIEWER"}:
        return "VERIFY"
    if checkpoint == "POST_VALIDATION" or role == "complete":
        return "VERIFY"
    return ""


def _status_for_event(
    category: str,
    metadata: Mapping[str, Any],
    event_type: str = "",
) -> str:
    if event_type == "QUEUE_CANCELLED":
        return "COMPLETED"
    explicit = _safe_text(metadata.get("status"), limit=32).upper()
    if explicit in {"ACTIVE", "WAITING", "RUNNING", "COMPLETED", "PASS", "FAIL", "BLOCKED"}:
        return explicit
    exit_code = _safe_int(metadata.get("validation_exit_code"))
    if exit_code is None:
        exit_code = _safe_int(metadata.get("exit_code"))
    if category in {"TEST", "VERIFY"} and exit_code is not None:
        return "PASS" if exit_code == 0 else "FAIL"
    return {
        "AGENT_STARTED": "ACTIVE",
        "AGENT_WAITING": "WAITING",
        "AGENT_COMPLETED": "COMPLETED",
        "BLOCKED": "BLOCKED",
        "OWNER_ACTION_REQUIRED": "WAITING",
    }.get(category, "UNKNOWN")


def _category_for_event(event_type: str, metadata: Mapping[str, Any]) -> str:
    if event_type == "QUEUE_CANCELLED":
        return "CHECKPOINT"
    explicit = _safe_text(
        metadata.get("activity_kind", metadata.get("category", "")), limit=64
    ).upper()
    if explicit in ACTIVITY_CATEGORIES:
        return explicit
    if _safe_text(metadata.get("checkpoint")):
        return "CHECKPOINT"
    if _safe_text(metadata.get("recovery_classification")):
        return "RECOVERY"
    if _safe_text(metadata.get("waiting_reason")):
        return "AGENT_WAITING"
    if _safe_text(metadata.get("failure_classification")):
        return "BLOCKED"
    if event_type == "DISCOVERED":
        return "PLAN"
    if event_type == "WORKSPACE_READY":
        return "AGENT_STARTED"
    if event_type == "EXECUTOR_RUNNING":
        return "AGENT_STARTED"
    if event_type == "LOCAL_VALIDATED":
        return "TEST"
    if event_type == "VALIDATED":
        return "VERIFY"
    if event_type == "EXECUTOR_FINISHED":
        if _safe_command_id(metadata.get("validation_command_id")):
            return "TEST"
        if _safe_command_id(metadata.get("mutation_command_id")) or _safe_path(metadata.get("fixture_path")):
            return "EDIT"
        return "AGENT_COMPLETED"
    return "AGENT_COMPLETED"


def _event_stage(
    event_type: str, category: str, metadata: Mapping[str, Any]
) -> str:
    if event_type == "QUEUE_CANCELLED":
        return "PLAN"
    if category == "PLAN" or event_type == "DISCOVERED":
        return "PLAN"
    if category == "PUBLICATION":
        return "PUBLISH"
    if category == "CHECKPOINT":
        return _checkpoint_stage(
            _safe_text(metadata.get("checkpoint"), limit=64),
            _safe_role(metadata.get("role")),
        ) or "UNKNOWN"
    if category in {"TEST", "VERIFY"} or event_type in {"LOCAL_VALIDATED", "VALIDATED"}:
        return "VERIFY"
    if category in {
        "READ", "SEARCH", "EDIT", "COMMAND", "AGENT_STARTED",
        "AGENT_WAITING", "AGENT_COMPLETED",
    } or event_type in {"WORKSPACE_READY", "EXECUTOR_RUNNING", "EXECUTOR_FINISHED"}:
        return "EXECUTE"
    return "UNKNOWN"


def _activity_title(category: str) -> str:
    return {
        "PLAN": "Task planned",
        "READ": "Repository read",
        "SEARCH": "Repository search",
        "EDIT": "Repository change",
        "COMMAND": "Approved command",
        "TEST": "Validation command",
        "VERIFY": "Validation result",
        "AGENT_STARTED": "Agent started",
        "AGENT_WAITING": "Agent waiting",
        "AGENT_COMPLETED": "Agent completed",
        "CHECKPOINT": "Checkpoint accepted",
        "RECOVERY": "Recovery activity",
        "BLOCKED": "Run blocked",
        "OWNER_ACTION_REQUIRED": "Owner action required",
        "PUBLICATION": "Publication activity",
    }.get(category, "Run activity")


def _event_projection(event: Mapping[str, Any], *, task: Any) -> dict[str, Any]:
    metadata = _metadata(event)
    event_type = _safe_text(event.get("type"), limit=64)
    category = _category_for_event(event_type, metadata)
    worker_originated = event_type in WORKER_EVENT_TYPES
    role = _safe_role(metadata.get("role"))
    persisted_agent_identity = metadata.get(
        "agent_id", metadata.get("worker_id", metadata.get("execution_id"))
    )
    agent_id = _hashed_agent_id(persisted_agent_identity)
    if not agent_id and worker_originated:
        execution_id = _safe_text(getattr(task, "execution_id", ""), limit=128)
        agent_id = _derived_agent_id(execution_id, role)
    path = _safe_path(
        metadata.get("path", metadata.get("file", metadata.get("fixture_path", ""))),
    )
    command = _safe_command_id(
        metadata.get("validation_command_id", metadata.get("mutation_command_id", ""))
    )
    exit_code = _safe_int(metadata.get("validation_exit_code"))
    if exit_code is None:
        exit_code = _safe_int(metadata.get("exit_code"))
    agent = {
        "agent_id": agent_id,
        "role": role,
        "display_name": _display_name(role, agent_id),
    } if agent_id or role else None
    file_payload = {
        "path": path,
        "status": "modified",
        "additions": 0,
        "deletions": 0,
    } if path else None
    test_payload = {
        "summary": command,
        "status": _status_for_event(category, metadata, event_type),
        "exit_code": exit_code,
    } if category == "TEST" else None
    command_payload = {
        "summary": command,
        "status": _status_for_event(category, metadata, event_type),
        "exit_code": exit_code,
    } if command else None
    return {
        "id": _safe_text(event.get("id"), limit=128),
        "task_id": _safe_text(event.get("task_id", getattr(task, "id", "")), limit=128),
        "type": event_type,
        "timestamp": _time_text(event.get("timestamp")),
        "title": (
            "Queued task cancelled"
            if event_type == "QUEUE_CANCELLED"
            else _activity_title(category)
        ),
        "description": "",
        "category": category,
        "status": _status_for_event(category, metadata, event_type),
        "stage": _event_stage(event_type, category, metadata),
        "agent_id": agent_id,
        "role": role,
        "agent": agent,
        "path": path,
        "command_summary": command,
        "file": file_payload,
        "command": command_payload,
        "test": test_payload,
        "evidence_ref": "",
    }


def _display_name(role: str, agent_id: str) -> str:
    labels = {
        "planner": "Planner", "coder": "Coder", "reviewer": "Reviewer",
        "verifier": "Verifier", "test": "Test Agent", "executor": "Executor",
    }
    return labels.get(role, role or agent_id)


def _durable_agent(durable_run: Any | None) -> dict[str, Any] | None:
    if durable_run is None:
        return None
    role = _safe_role(getattr(durable_run, "current_role", ""))
    execution_id = _safe_text(getattr(durable_run, "execution_id", ""), limit=128)
    agent_id = _derived_agent_id(execution_id, role)
    if not agent_id and not role:
        return None
    return {
        "agent_id": agent_id,
        "role": role,
        "display_name": _display_name(role, agent_id),
    }


def _activity_time(
    events: Sequence[Mapping[str, Any]], task: Any, durable_run: Any | None
) -> tuple[datetime | None, str]:
    candidates: list[tuple[datetime, str]] = []
    for event in events:
        parsed = _parse_time(event.get("timestamp"))
        if parsed is not None:
            candidates.append((parsed, "event"))
    task_updated = _parse_time(getattr(task, "updated_at", ""))
    if task_updated is not None:
        candidates.append((task_updated, "task_update"))
    heartbeat_ms = _safe_int(getattr(durable_run, "heartbeat_at_ms", 0)) if durable_run else None
    if heartbeat_ms and heartbeat_ms > 0:
        try:
            candidates.append((datetime.fromtimestamp(heartbeat_ms / 1000, tz=timezone.utc), "heartbeat"))
        except (OverflowError, OSError, ValueError):
            pass
    if not candidates:
        return None, ""
    priority = {"event": 3, "task_update": 2, "heartbeat": 1}
    return max(candidates, key=lambda item: (item[0], priority[item[1]]))


def _liveness(
    task: Any,
    events: Sequence[Mapping[str, Any]],
    durable_run: Any | None,
    now: datetime,
    *,
    stale_after: int,
) -> dict[str, Any]:
    status = _safe_text(getattr(task, "status", ""), limit=64)
    activity_at, source = _activity_time(events, task, durable_run)
    heartbeat_at = ""
    expiry_at = ""
    heartbeat_ms = _safe_int(getattr(durable_run, "heartbeat_at_ms", 0)) if durable_run else None
    expiry_ms = _safe_int(getattr(durable_run, "lease_expiry_ms", 0)) if durable_run else None
    if heartbeat_ms and heartbeat_ms > 0:
        try:
            heartbeat_at = datetime.fromtimestamp(heartbeat_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            pass
    if expiry_ms and expiry_ms > 0:
        try:
            expiry_at = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            pass
    state = "UNKNOWN"
    reason = ""
    now_utc = now.astimezone(timezone.utc)
    live_statuses = {"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING"}
    if (
        status in live_statuses
        and expiry_ms
        and expiry_ms > 0
        and expiry_ms <= int(now_utc.timestamp() * 1000)
    ):
        state = "STALE"
        reason = "lease_expired"
    elif status in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
        state = "OWNER_ACTION_REQUIRED"
    elif status == "BLOCKED":
        state = "BLOCKED"
    elif status in {"FAILED", "CANCELLED"}:
        state = "TERMINAL"
    elif status == "VALIDATING":
        state = "VALIDATING"
    elif status in {"QUEUED", "PREPARING_WORKSPACE"}:
        state = "WAITING"
    elif status == "INTERRUPTED":
        state = "STALE"
        reason = "interrupted"
    elif status in {"RUNNING", "RUNNING_FIXTURE"}:
        if activity_at is None:
            state = "UNKNOWN"
            reason = "no_persisted_activity"
        else:
            age = max(0, int((now_utc - activity_at).total_seconds()))
            state = "STALE" if age >= stale_after else "ACTIVE"
            if state == "STALE":
                reason = "no_recent_activity"
    age_seconds = None
    if activity_at is not None:
        age_seconds = max(0, int((now_utc - activity_at).total_seconds()))
    return {
        "state": state if state in LIVENESS_STATES else "UNKNOWN",
        "last_activity_at": activity_at.isoformat().replace("+00:00", "Z") if activity_at else "",
        "last_activity_source": source,
        "seconds_since_activity": age_seconds,
        "stale_after_seconds": stale_after,
        "stale_reason": reason,
        "heartbeat_at": heartbeat_at,
        "lease_expires_at": expiry_at,
    }


class RunReadModel:
    """Derived listing/detail over TaskStore; read-only by construction."""

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore,
        clock: Callable[[], datetime] | None = None,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
    ) -> None:
        self.store = store
        self.control_store = control_store
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stale_after_seconds = max(1, int(stale_after_seconds))

    def list_runs(self, *, limit: int = MAX_RUNS) -> dict[str, Any]:
        bounded = max(1, min(limit, MAX_RUNS))
        tasks = self.store.list_tasks(limit=bounded, event_limit=MAX_DETAIL_EVENTS)
        runs = [self._run_summary(task) for task in tasks]
        return {"runs": runs, "total": self.store.count_tasks()}

    def run_detail(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id, event_limit=MAX_DETAIL_EVENTS)
        detail = self._run_summary(task)
        projected_events = [
            _event_projection(event, task=task)
            for event in task.events
        ]
        detail["events"] = projected_events
        detail["event_count"] = task.event_count
        detail["events_truncated"] = task.event_count > len(projected_events)
        detail["activity"] = projected_events[-MAX_ACTIVITY:]
        detail["activity_total"] = task.event_count
        detail["changed_files"] = self._changed_files(task.changed_files)
        detail["controls"] = {
            "cancel": self.store.queue_cancel_capability(task.id),
        }
        return detail

    def _durable_run(self, task_id: str) -> Any | None:
        reader = getattr(self.store, "get_latest_durable_run_observation", None)
        if not callable(reader):
            return None
        try:
            return reader(task_id)
        except TaskStoreError:
            return None

    def _run_summary(self, task: Any) -> dict[str, Any]:
        goal_id = ""
        goal_title = ""
        window_id = ""
        try:
            goal_id = self.control_store.goal_id_for_task(task.id)
            goal = self.control_store.get_goal(goal_id)
            goal_title = goal.title
            window_id = goal.window_id
        except TaskStoreError:
            pass
        publication = self.control_store.get_publication(task.id)
        budget = None
        if window_id:
            try:
                budget = self.control_store.window_budget_summary(window_id)
            except TaskStoreError:
                budget = None
        durable_run = self._durable_run(task.id)
        stage = self._stage(task, durable_run, publication)
        projected_events = [
            _event_projection(event, task=task)
            for event in task.events
        ]
        liveness = _liveness(
            task, task.events, durable_run, self._clock(),
            stale_after=self._stale_after_seconds,
        )
        current_activity = projected_events[-1] if projected_events else None
        validation = self._validation(task)
        return {
            "task_id": task.id,
            "title": _safe_text(task.title),
            "repository": _safe_text(task.repository),
            "status": task.status,
            "state": backend_status_to_frontend_state(task.status),
            "executor_kind": task.executor_kind,
            "orchestration_mode": task.orchestration_mode,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "failure_classification": _safe_text(task.failure_classification),
            "goal_id": goal_id,
            "goal_title": _safe_text(goal_title),
            "window_id": window_id,
            "usage": self.store.usage_summary(task.id),
            "budget": budget,
            "publication": (
                {
                    "status": _safe_text(publication.status, limit=32),
                    "branch": _safe_text(publication.branch, limit=256),
                    "pr_number": publication.pr_number,
                    "pr_url": _safe_text(publication.pr_url, limit=512),
                    "commit_sha": _safe_reference(publication.commit_sha),
                }
                if publication is not None
                else None
            ),
            "run_id": _safe_text(getattr(durable_run, "run_id", ""), limit=128),
            "stage": stage,
            "liveness": liveness["state"],
            "liveness_detail": liveness,
            "last_activity_at": liveness["last_activity_at"],
            "current_activity": current_activity,
            "current_agent": self._current_agent(current_activity, durable_run),
            "agents": self._agents(projected_events, durable_run),
            "activity": projected_events[-MAX_ACTIVITY:],
            "activity_total": task.event_count,
            "change_summary": self._change_summary(
                self._changed_files(task.changed_files)
            ),
            "validation": validation,
        }

    @staticmethod
    def _stage(task: Any, durable_run: Any | None, publication: Any | None) -> str:
        if publication is not None:
            return "PUBLISH"
        if durable_run is not None:
            checkpoint_stage = _checkpoint_stage(
                _safe_text(getattr(durable_run, "accepted_checkpoint", "")),
                _safe_text(getattr(durable_run, "current_role", "")),
            )
            if checkpoint_stage:
                return checkpoint_stage
        return {
            "QUEUED": "PLAN", "PREPARING_WORKSPACE": "PLAN",
            "RUNNING": "EXECUTE", "RUNNING_FIXTURE": "EXECUTE",
            "VALIDATING": "VERIFY", "READY_FOR_REVIEW": "VERIFY",
            "READY_FOR_REVIEW_FIXTURE": "VERIFY",
        }.get(_safe_text(getattr(task, "status", "")), "UNKNOWN")

    @staticmethod
    def _change_summary(files: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        counts = {"added": 0, "modified": 0, "deleted": 0, "renamed": 0}
        additions = 0
        deletions = 0
        for file in files:
            status = _safe_text(file.get("status", "modified"), limit=16).lower()
            if status not in counts:
                status = "modified"
            counts[status] += 1
            additions += max(0, _safe_int(file.get("additions")) or 0)
            deletions += max(0, _safe_int(file.get("deletions")) or 0)
        return {
            "file_count": len(files), "additions": additions,
            "deletions": deletions, "status_counts": counts,
        }

    @staticmethod
    def _changed_files(
        files: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        projected: list[dict[str, Any]] = []
        for changed in files:
            path = _safe_path(changed.get("path", ""))
            if not path:
                continue
            status = _safe_text(changed.get("status", "modified"), limit=16).lower()
            if status not in {"added", "modified", "deleted", "renamed"}:
                status = "modified"
            projected.append({
                "path": path,
                "status": status,
                "additions": max(0, _safe_int(changed.get("additions")) or 0),
                "deletions": max(0, _safe_int(changed.get("deletions")) or 0),
            })
        return projected

    @staticmethod
    def _agents(events: Sequence[Mapping[str, Any]], durable_run: Any | None) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for event in events:
            agent_id = _safe_text(event.get("agent_id"), limit=128)
            role = _safe_role(event.get("role"))
            if not agent_id and not role:
                continue
            grouped[(agent_id, role)] = {
                "agent_id": agent_id, "role": role,
                "display_name": _display_name(role, agent_id),
                "status": event.get("status", "UNKNOWN"), "attempt": 1,
                "last_activity_at": event.get("timestamp", ""),
            }
        if durable_run is not None:
            role = _safe_role(getattr(durable_run, "current_role", ""))
            execution_id = _safe_text(
                getattr(durable_run, "execution_id", ""), limit=128
            )
            agent_id = _derived_agent_id(execution_id, role)
            if role or agent_id:
                grouped.pop((execution_id, ""), None)
                current = grouped.setdefault((agent_id, role), {
                    "agent_id": agent_id, "role": role, "status": "UNKNOWN",
                    "display_name": _display_name(role, agent_id),
                    "attempt": 1, "last_activity_at": "",
                })
                current["attempt"] = max(1, _safe_int(getattr(durable_run, "role_attempt", 1)) or 1)
        return [grouped[key] for key in sorted(grouped)]

    @staticmethod
    def _current_agent(
        current_activity: Mapping[str, Any] | None,
        durable_run: Any | None,
    ) -> dict[str, Any] | None:
        event_agent = current_activity.get("agent") if current_activity else None
        if isinstance(event_agent, Mapping) and event_agent.get("role"):
            return dict(event_agent)
        return _durable_agent(durable_run) or (
            dict(event_agent) if isinstance(event_agent, Mapping) else None
        )

    @staticmethod
    def _validation(task: Any) -> dict[str, Any] | None:
        command_id = _safe_command_id(getattr(task, "validation_command_id", ""))
        exit_code = _safe_int(getattr(task, "validation_exit_code", None))
        if not command_id and exit_code is None:
            return None
        if exit_code is None:
            status = "RUNNING" if getattr(task, "status", "") == "VALIDATING" else "PENDING"
        else:
            status = "SUCCESS" if exit_code == 0 else "FAILURE"
        return {"command_id": command_id, "status": status, "exit_code": exit_code}
