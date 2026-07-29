from __future__ import annotations

import asyncio
import inspect

import pytest

from reverse_agent.unattended.activities import run_synthetic_activity
from reverse_agent.unattended.cli import doctor_report
from reverse_agent.unattended.worker import build_worker
from reverse_agent.unattended.workflows import UnattendedGate2Workflow


def test_synthetic_activity_is_bounded() -> None:
    assert asyncio.run(run_synthetic_activity("probe")) == "activity:probe"
    with pytest.raises(ValueError, match="out_of_bounds"):
        asyncio.run(run_synthetic_activity(""))
    with pytest.raises(ValueError, match="out_of_bounds"):
        asyncio.run(run_synthetic_activity("x" * 257))


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


def test_worker_registers_only_gate2_workflow_and_activity(monkeypatch: pytest.MonkeyPatch) -> None:
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
    assert captured["activities"] == [run_synthetic_activity]


def test_doctor_passes_static_boundary_checks() -> None:
    report = doctor_report()
    assert report["status"] == "PASS"
    assert report["temporalio_version"] == "1.30.0"
    assert all(report["checks"].values())
