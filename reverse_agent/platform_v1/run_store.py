"""SQLite-backed durable execution state for Platform V1."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from .issue_task import LoadedIssueTask


class RunState(StrEnum):
    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    WORKSPACE_READY = "WORKSPACE_READY"
    EXECUTOR_RUNNING = "EXECUTOR_RUNNING"
    EXECUTOR_FINISHED = "EXECUTOR_FINISHED"
    LOCAL_VALIDATED = "LOCAL_VALIDATED"
    COMMITTED = "COMMITTED"
    PUSHED = "PUSHED"
    DRAFT_PR_OPEN = "DRAFT_PR_OPEN"
    WORKFLOWS_OBSERVED = "WORKFLOWS_OBSERVED"
    READY_FOR_HUMAN = "READY_FOR_HUMAN"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = frozenset({RunState.READY_FOR_HUMAN, RunState.BLOCKED_EXTERNAL, RunState.FAILED_TERMINAL, RunState.CANCELLED})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RunRecord:
    execution_id: str
    task_digest: str
    repository: str
    issue_number: int
    base_sha: str
    branch: str
    worktree_path: str
    state: RunState
    attempt: int
    executor_reference: str
    commit_sha: str
    head_sha: str
    pr_number: int
    workflow_observations: tuple[dict[str, Any], ...]
    failure_classification: str
    created_at: str
    updated_at: str

    def to_mapping(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data["state"] = self.state.value
        data["workflow_observations"] = list(self.workflow_observations)
        return data


@dataclass(frozen=True)
class StateEvent:
    event_id: int
    execution_id: str
    from_state: RunState | None
    to_state: RunState
    detail: dict[str, Any]
    created_at: str


class SQLiteRunStore:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.database_path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS executions (
                execution_id TEXT PRIMARY KEY,
                task_digest TEXT NOT NULL UNIQUE,
                repository TEXT NOT NULL,
                issue_number INTEGER NOT NULL,
                base_sha TEXT NOT NULL,
                branch TEXT NOT NULL,
                worktree_path TEXT NOT NULL,
                state TEXT NOT NULL,
                attempt INTEGER NOT NULL DEFAULT 1,
                executor_reference TEXT NOT NULL DEFAULT '',
                commit_sha TEXT NOT NULL DEFAULT '',
                head_sha TEXT NOT NULL DEFAULT '',
                pr_number INTEGER NOT NULL DEFAULT 0,
                workflow_observations TEXT NOT NULL DEFAULT '[]',
                failure_classification TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS state_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(execution_id) REFERENCES executions(execution_id)
            );
            CREATE INDEX IF NOT EXISTS executions_issue_idx ON executions(repository, issue_number, updated_at);
        """)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def _record(self, row: sqlite3.Row | None) -> RunRecord | None:
        if row is None:
            return None
        return RunRecord(
            execution_id=row["execution_id"], task_digest=row["task_digest"], repository=row["repository"],
            issue_number=row["issue_number"], base_sha=row["base_sha"], branch=row["branch"],
            worktree_path=row["worktree_path"], state=RunState(row["state"]), attempt=row["attempt"],
            executor_reference=row["executor_reference"], commit_sha=row["commit_sha"], head_sha=row["head_sha"],
            pr_number=row["pr_number"], workflow_observations=tuple(json.loads(row["workflow_observations"])),
            failure_classification=row["failure_classification"], created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def get_or_create(self, task: LoadedIssueTask, worktree_path: str) -> RunRecord:
        existing = self._db.execute("SELECT * FROM executions WHERE task_digest=?", (task.task_digest,)).fetchone()
        if existing is not None:
            return self._record(existing)  # type: ignore[return-value]
        now = _now()
        self._db.execute(
            "INSERT INTO executions (execution_id,task_digest,repository,issue_number,base_sha,branch,worktree_path,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (task.execution_id, task.task_digest, task.work_item.repository, task.work_item.source_issue_number,
             task.work_item.base_sha, task.work_item.target_branch, worktree_path, RunState.DISCOVERED.value, now, now),
        )
        self._db.execute(
            "INSERT INTO state_events (execution_id,from_state,to_state,detail,created_at) VALUES (?,?,?,?,?)",
            (task.execution_id, None, RunState.DISCOVERED.value, "{}", now),
        )
        self._db.commit()
        return self.get(task.execution_id)  # type: ignore[return-value]

    def get(self, execution_id: str) -> RunRecord | None:
        return self._record(self._db.execute("SELECT * FROM executions WHERE execution_id=?", (execution_id,)).fetchone())

    def find_by_issue(self, repository: str, issue_number: int) -> RunRecord | None:
        return self._record(self._db.execute(
            "SELECT * FROM executions WHERE repository=? AND issue_number=? ORDER BY updated_at DESC LIMIT 1",
            (repository, issue_number),
        ).fetchone())

    def count_runs(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM executions").fetchone()[0])

    def transition(self, execution_id: str, state: RunState, *, detail: dict[str, Any] | None = None) -> RunRecord:
        current = self.get(execution_id)
        if current is None:
            raise KeyError(execution_id)
        if current.state == state:
            return current
        now = _now()
        self._db.execute("UPDATE executions SET state=?,updated_at=? WHERE execution_id=?", (state.value, now, execution_id))
        self._db.execute(
            "INSERT INTO state_events (execution_id,from_state,to_state,detail,created_at) VALUES (?,?,?,?,?)",
            (execution_id, current.state.value, state.value, json.dumps(detail or {}, sort_keys=True, separators=(",", ":")), now),
        )
        self._db.commit()
        return self.get(execution_id)  # type: ignore[return-value]

    def update(self, execution_id: str, **values: Any) -> RunRecord:
        allowed = {"attempt", "executor_reference", "commit_sha", "head_sha", "pr_number", "workflow_observations", "failure_classification", "worktree_path"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown_run_fields:{','.join(sorted(unknown))}")
        if "workflow_observations" in values:
            values["workflow_observations"] = json.dumps(values["workflow_observations"], sort_keys=True, separators=(",", ":"))
        values["updated_at"] = _now()
        assignments = ",".join(f"{key}=?" for key in values)
        self._db.execute(f"UPDATE executions SET {assignments} WHERE execution_id=?", (*values.values(), execution_id))
        self._db.commit()
        return self.get(execution_id)  # type: ignore[return-value]

    def events(self, execution_id: str) -> tuple[StateEvent, ...]:
        rows = self._db.execute("SELECT * FROM state_events WHERE execution_id=? ORDER BY event_id", (execution_id,)).fetchall()
        return tuple(StateEvent(
            event_id=row["event_id"], execution_id=row["execution_id"],
            from_state=RunState(row["from_state"]) if row["from_state"] else None,
            to_state=RunState(row["to_state"]), detail=json.loads(row["detail"]), created_at=row["created_at"],
        ) for row in rows)

    def cancel(self, execution_id: str) -> RunRecord:
        current = self.get(execution_id)
        if current is None:
            raise KeyError(execution_id)
        if current.state == RunState.CANCELLED:
            return current
        if current.state in TERMINAL_STATES:
            raise ValueError(f"terminal_run_not_cancellable:{current.state.value}")
        return self.transition(execution_id, RunState.CANCELLED)
