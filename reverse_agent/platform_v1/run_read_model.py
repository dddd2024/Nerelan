"""Agent Runs: a pure read model derived from TaskStore task truth.

Every view here is computed from tasks, goal links and publication records.
The module holds no runtime state machine of its own and performs no writes.
"""

from __future__ import annotations

from typing import Any

from .control_store import PlatformControlStore
from .run_store import TaskStore, TaskStoreError

MAX_RUNS = 100

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


def backend_status_to_frontend_state(status: str) -> str:
    return BACKEND_STATUS_TO_FRONTEND_STATE.get(status, "WAITING_FOR_OWNER")


class RunReadModel:
    """Derived listing/detail over TaskStore; read-only by construction."""

    def __init__(self, *, store: TaskStore, control_store: PlatformControlStore) -> None:
        self.store = store
        self.control_store = control_store

    def list_runs(self, *, limit: int = MAX_RUNS) -> dict[str, Any]:
        bounded = max(1, min(limit, MAX_RUNS))
        tasks = self.store.list_tasks(limit=bounded)
        runs = [self._run_summary(task) for task in tasks]
        return {"runs": runs, "total": self.store.count_tasks()}

    def run_detail(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        detail = self._run_summary(task)
        detail["events"] = [
            {
                "id": event.get("id", ""),
                "task_id": event.get("task_id", task.id),
                "type": event.get("type", ""),
                "timestamp": event.get("timestamp", ""),
                "title": event.get("title", ""),
                "description": event.get("description", ""),
            }
            for event in task.events
        ]
        detail["changed_files"] = [
            {
                "path": changed.get("path", ""),
                "status": changed.get("status", "modified"),
                "additions": int(changed.get("additions", 0)),
                "deletions": int(changed.get("deletions", 0)),
            }
            for changed in task.changed_files
        ]
        return detail

    def _run_summary(self, task: Any) -> dict[str, Any]:
        goal_id = ""
        goal_title = ""
        try:
            goal_id = self.control_store.goal_id_for_task(task.id)
            goal_title = self.control_store.get_goal(goal_id).title
        except TaskStoreError:
            pass
        publication = self.control_store.get_publication(task.id)
        return {
            "task_id": task.id,
            "title": task.title,
            "repository": task.repository,
            "status": task.status,
            "state": backend_status_to_frontend_state(task.status),
            "executor_kind": task.executor_kind,
            "orchestration_mode": task.orchestration_mode,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "failure_classification": task.failure_classification,
            "goal_id": goal_id,
            "goal_title": goal_title,
            "publication": (
                {
                    "status": publication.status,
                    "branch": publication.branch,
                    "pr_number": publication.pr_number,
                    "pr_url": publication.pr_url,
                    "commit_sha": publication.commit_sha,
                }
                if publication is not None
                else None
            ),
        }
