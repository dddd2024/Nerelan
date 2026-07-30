from __future__ import annotations

import inspect

import pytest

from reverse_agent.unattended.activities import (
    cleanup_attempt,
    collect_openhands_result,
    launch_or_reconcile_attempt,
    start_openhands_conversation,
    wait_attempt_server,
)
from reverse_agent.unattended.cli import doctor_report
from reverse_agent.unattended.controller_worker import build_controller_worker
from reverse_agent.unattended.worker import build_worker
from reverse_agent.unattended.workflows import UnattendedGate2Workflow


def test_workflow_source_contains_no_io_or_nondeterministic_calls() -> None:
    source = inspect.getsource(__import__(
        "reverse_agent.unattended.workflows.gate2",
        fromlist=["UnattendedGate2Workflow"],
    ))
    for forbidden in (
        "asyncio.",
        "datetime.now",
        "open(",
        "os.",
        "pathlib",
        "requests",
        "subprocess",
        "urllib",
    ):
        assert forbidden not in source
    assert "maximum_attempts=2" in source
    assert "start_to_close_timeout" in source
    assert "finally:" in source
    assert '"cleanup_attempt"' in source
    assert "SANDBOX_CONTROLLER_TASK_QUEUE" in source


def test_ordinary_worker_registers_workflow_without_docker_activities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeWorker:
        def __init__(self, client: object, **kwargs: object) -> None:
            captured["client"] = client
            captured.update(kwargs)

    monkeypatch.setattr("reverse_agent.unattended.worker.Worker", FakeWorker)
    client = object()
    worker = build_worker(client)  # type: ignore[arg-type]
    assert isinstance(worker, FakeWorker)
    assert captured["task_queue"] == "reverse-agent-unattended-v0"
    assert captured["workflows"] == [UnattendedGate2Workflow]
    assert captured["activities"] == []


def test_controller_worker_registers_only_fixed_activities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeWorker:
        def __init__(self, client: object, **kwargs: object) -> None:
            captured["client"] = client
            captured.update(kwargs)

    monkeypatch.setattr(
        "reverse_agent.unattended.controller_worker.Worker", FakeWorker
    )
    client = object()
    worker = build_controller_worker(client)  # type: ignore[arg-type]
    assert isinstance(worker, FakeWorker)
    assert captured["task_queue"] == "reverse-agent-sandbox-controller-v0"
    assert captured["workflows"] == []
    assert captured["activities"] == [
        launch_or_reconcile_attempt,
        wait_attempt_server,
        start_openhands_conversation,
        collect_openhands_result,
        cleanup_attempt,
    ]


def test_activity_names_are_fixed() -> None:
    assert [
        getattr(activity, "__temporal_activity_definition").name
        for activity in (
            launch_or_reconcile_attempt,
            wait_attempt_server,
            start_openhands_conversation,
            collect_openhands_result,
            cleanup_attempt,
        )
    ] == [
        "launch_or_reconcile_attempt",
        "wait_attempt_server",
        "start_openhands_conversation",
        "collect_openhands_result",
        "cleanup_attempt",
    ]


def test_doctor_passes_static_boundary_checks() -> None:
    report = doctor_report()
    assert report["status"] == "PASS"
    assert report["temporalio_version"] == "1.30.0"
    assert all(report["checks"].values())
