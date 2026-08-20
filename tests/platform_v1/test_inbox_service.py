"""Inbox contract tests: capture is inert display state; promotion reuses
GoalService exactly once per item; dismissal never deletes history."""

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.inbox_service import InboxService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


@pytest.fixture()
def inbox():
    store = TaskStore()
    control = PlatformControlStore(store)
    goal_service = GoalService(store=store, control_store=control)
    return InboxService(control_store=control, goal_service=goal_service), control


def test_capture_stores_captured_display_state_only(inbox) -> None:
    service, control = inbox
    item = service.capture({"title": "Idea", "objective": "做一个无人值守平台"})
    assert item.status == "CAPTURED"
    assert item.promoted_goal_id == ""
    assert control.list_goals() == ()


def test_capture_requires_objective(inbox) -> None:
    service, _ = inbox
    with pytest.raises(TaskStoreError):
        service.capture({"title": "empty"})


def test_capture_rejects_secret_shaped_fields(inbox) -> None:
    service, _ = inbox
    with pytest.raises(TaskStoreError):
        service.capture({"objective": "x", "api_key": "k" * 20})


def test_promotion_creates_exactly_one_draft_goal_through_goal_service(inbox) -> None:
    service, control = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    first = service.promote(item.id)
    goal_id = first["goal"]["id"]
    assert first["goal"]["status"] == "DRAFT"
    assert first["item"]["status"] == "PROMOTED"
    assert first["item"]["promoted_goal_id"] == goal_id
    assert control.get_goal(goal_id).idempotency_key == f"inbox:{item.id}"


def test_repeated_promotion_is_idempotent_and_never_creates_second_goal(inbox) -> None:
    service, control = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    first = service.promote(item.id)
    for _ in range(3):
        again = service.promote(item.id)
        assert again["goal"]["id"] == first["goal"]["id"]
    assert len(control.list_goals()) == 1


def test_promotion_idempotency_survives_crash_between_goal_and_mark(inbox) -> None:
    """If the item is still CAPTURED after goal creation, promotion retry
    must reuse the same idempotency key and the same goal."""
    service, _ = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    first = service.promote(item.id)
    # Simulate the crash window: reset item to CAPTURED, keep the goal.
    service.control_store._conn.execute(
        "UPDATE platform_inbox_items SET status = 'CAPTURED', promoted_goal_id = '' WHERE id = ?",
        (item.id,),
    )
    retried = service.promote(item.id)
    assert retried["goal"]["id"] == first["goal"]["id"]
    assert retried["item"]["promoted_goal_id"] == first["goal"]["id"]


def test_dismissal_marks_dismissed_and_keeps_history(inbox) -> None:
    service, _ = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    dismissed = service.dismiss(item.id)
    assert dismissed.status == "DISMISSED"
    history = service.list_items()
    assert [entry.id for entry in history] == [item.id]
    assert service.get_item(item.id).status == "DISMISSED"


def test_dismissed_item_cannot_be_promoted(inbox) -> None:
    service, _ = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    service.dismiss(item.id)
    with pytest.raises(TaskStoreError):
        service.promote(item.id)


def test_promoted_item_cannot_be_dismissed(inbox) -> None:
    service, _ = inbox
    item = service.capture({"title": "Idea", "objective": "目标描述"})
    service.promote(item.id)
    with pytest.raises(TaskStoreError):
        service.dismiss(item.id)


def test_promoted_goal_follows_ordinary_goal_lifecycle(inbox) -> None:
    """A promoted goal is an ordinary goal: it must plan/approve through the
    unchanged GoalService path, never bypassing it."""
    service, control = inbox
    from reverse_agent.platform_v1.goal_service import GoalService
    from reverse_agent.platform_v1.run_store import TaskStore

    item = service.capture({"title": "Idea", "objective": "目标描述"})
    promoted = service.promote(item.id)
    goal_id = promoted["goal"]["id"]

    goal_service = GoalService(
        store=service.goal_service.store, control_store=control
    )
    planned = goal_service.plan(
        goal_id,
        expected_revision=1,
        tasks=[{"id": "T001", "title": "step", "instruction": "do"}],
    )
    assert planned.goal.status == "PLANNED"
    approved = goal_service.approve(goal_id, expected_revision=1)
    assert approved.status == "APPROVED"
    assert isinstance(service.goal_service.store, TaskStore)
