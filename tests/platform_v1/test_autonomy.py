from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _payload(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "policy_id": "policy-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=2)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "open_draft_pr"],
        "max_concurrent_tasks": 2, "max_tasks": 8, "max_retries": 1,
        "confirmation": "ACTIVATE",
    }
    payload.update(overrides)
    return payload


def test_window_requires_owner_confirmation_and_bounded_policy():
    control = PlatformControlStore(TaskStore(":memory:"))
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    with pytest.raises(TaskStoreError, match="confirmation"):
        service.activate(_payload(confirmation=""))
    with pytest.raises(TaskStoreError, match="duration"):
        service.activate(_payload(expires_at=(datetime.now(timezone.utc) + timedelta(days=8)).isoformat()))
    active = service.activate(_payload())
    assert active.status == "ACTIVE"
    assert service.status()["autonomy_enabled"] is True


def test_policy_evaluation_is_server_side_and_receipted():
    control = PlatformControlStore(TaskStore(":memory:"))
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = service.activate(_payload())
    assert service.authorize(
        window_id=window.id, operation="execute_task", repository="dddd2024/reverse-agent",
        subject_id="task-1", input_payload={"task_id": "task-1"},
    )
    assert not service.authorize(
        window_id=window.id, operation="execute_task", repository="elsewhere/repo",
        subject_id="task-2", input_payload={"task_id": "task-2"},
    )
    summary = service.summary(window.id)
    assert summary["operations"] == {"allowed": 1, "denied": 1, "total": 2}
    assert all(receipt["input_digest"] and "task_id" not in receipt for receipt in summary["receipts"])
