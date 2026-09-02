"""Dedicated OPS-1 Resume read-model contract tests for #607."""

from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore


def _model():
    store = TaskStore()
    control = PlatformControlStore(store)
    return RunReadModel(store=store, control_store=control), store


def _resume(detail):
    return detail["controls"]["resume"]


def test_resume_control_is_zero_write_and_status_gated() -> None:
    model, store = _model()
    task = store.create_task(
        title="resume status gate",
        executor_kind="opencode",
        orchestration_mode="single",
    )
    before = store._conn.total_changes
    detail = model.run_detail(task.id)
    assert store._conn.total_changes == before
    assert _resume(detail) == {
        "action": "RESUME",
        "scope": "DURABLE_RECOVERY",
        "availability": "UNAVAILABLE",
        "reason_code": "STATUS_NOT_INTERRUPTED",
    }
    assert detail["controls"]["cancel"]["availability"] == "AVAILABLE"


def test_interrupted_supported_mode_without_durable_run_fails_closed() -> None:
    model, store = _model()
    task = store.create_task(
        title="resume missing durable run",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.set_state(task.id, "INTERRUPTED")

    assert _resume(model.run_detail(task.id)) == {
        "action": "RESUME",
        "scope": "DURABLE_RECOVERY",
        "availability": "UNAVAILABLE",
        "reason_code": "NO_DURABLE_RUN",
    }


@pytest.mark.parametrize("mode", ["single", "sequential_team"])
def test_interrupted_durable_supported_modes_are_advisory_available(mode: str) -> None:
    model, store = _model()
    task = store.create_task(
        title=f"resume durable {mode}",
        executor_kind="opencode",
        orchestration_mode=mode,
    )
    store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="resume-read-model-test",
        expiry_ms=60_000,
    )
    store.set_state(task.id, "INTERRUPTED")

    before = store._conn.total_changes
    detail = model.run_detail(task.id)
    assert store._conn.total_changes == before
    assert _resume(detail) == {
        "action": "RESUME",
        "scope": "DURABLE_RECOVERY",
        "availability": "AVAILABLE",
        "reason_code": "INTERRUPTED_DURABLE_READY",
    }
    assert detail["controls"]["cancel"]["availability"] == "UNAVAILABLE"
    assert detail["controls"]["cancel"]["reason_code"] == "STATUS_NOT_CANCELLABLE"


def test_unsupported_orchestration_precedes_status_and_missing_run() -> None:
    model, _store = _model()
    unsupported_running = SimpleNamespace(
        orchestration_mode="legacy_parallel",
        status="RUNNING",
    )
    unsupported_interrupted = SimpleNamespace(
        orchestration_mode="legacy_parallel",
        status="INTERRUPTED",
    )

    for task in (unsupported_running, unsupported_interrupted):
        control = model._resume_control(task, None)
        assert control["availability"] == "UNAVAILABLE"
        assert control["reason_code"] == "ORCHESTRATION_MODE_UNSUPPORTED"
