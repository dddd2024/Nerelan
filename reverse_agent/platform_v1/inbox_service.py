"""Human Inbox: captured ideas become ordinary Goals only through GoalService.

A captured item is inert display state. Promotion reuses the existing
GoalService authorization path; planning, approval and launch remain unchanged
and are never bypassed here.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from .control_store import InboxItemRecord, PlatformControlStore, reject_sensitive_keys
from .goal_service import GoalService, goal_to_dict
from .run_store import TaskStoreError


def inbox_item_to_dict(item: InboxItemRecord) -> dict[str, Any]:
    return asdict(item)


class InboxService:
    """Capture/promotion/dismiss lifecycle over display-only inbox state."""

    def __init__(self, *, control_store: PlatformControlStore, goal_service: GoalService) -> None:
        self.control_store = control_store
        self.goal_service = goal_service

    def capture(self, payload: Mapping[str, Any]) -> InboxItemRecord:
        reject_sensitive_keys(dict(payload))
        objective = str(payload.get("objective", "")).strip()
        title = str(payload.get("title", "")).strip() or objective[:77]
        repository = str(payload.get("repository", "")).strip() or "dddd2024/reverse-agent"
        return self.control_store.capture_inbox_item(
            title=title, objective=objective, repository=repository
        )

    def list_items(self, *, status: str | None = None) -> tuple[InboxItemRecord, ...]:
        return self.control_store.list_inbox_items(status=status)

    def get_item(self, item_id: str) -> InboxItemRecord:
        return self.control_store.get_inbox_item(item_id)

    def promote(self, item_id: str) -> dict[str, Any]:
        """Create exactly one DRAFT Goal through GoalService, idempotently.

        The idempotency key is deterministic in the item id, so repeated
        promotion (including a retry after a crash between goal creation and
        item marking) can never create a second goal.
        """

        item = self.control_store.get_inbox_item(item_id)
        if item.status == "PROMOTED" and item.promoted_goal_id:
            return {
                "item": inbox_item_to_dict(item),
                "goal": self._goal_payload(item.promoted_goal_id),
            }
        if item.status != "CAPTURED":
            raise TaskStoreError(f"inbox_item_not_promotable:{item_id}:{item.status}")
        goal = self.goal_service.create(
            {
                "title": item.title,
                "objective": item.objective,
                "repository": item.repository,
                "idempotency_key": f"inbox:{item_id}",
                "executor_kind": "deterministic_fixture",
                "orchestration_mode": "single",
            }
        )
        if goal.status != "DRAFT":
            raise TaskStoreError("inbox_promotion_goal_not_draft")
        updated = self.control_store.mark_inbox_item_promoted(item_id, goal_id=goal.id)
        return {"item": inbox_item_to_dict(updated), "goal": self._goal_payload(goal.id)}

    def dismiss(self, item_id: str) -> InboxItemRecord:
        return self.control_store.dismiss_inbox_item(item_id)

    def _goal_payload(self, goal_id: str) -> dict[str, Any]:
        goal = self.control_store.get_goal(goal_id)
        return goal_to_dict(goal, links=self.control_store.list_goal_tasks(goal_id))
