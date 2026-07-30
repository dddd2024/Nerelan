"""Bounded live compatibility probes for the selected Temporal stack."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio.client import Client
from temporalio.worker import Replayer

from .contracts import ExecutionHandle, TaskSubmission
from .identifiers import TASK_QUEUE, executor_id, workspace_id
from .workflows import UnattendedGate2Workflow


async def run_temporal_probe(
    *,
    address: str,
    namespace: str,
    probe_workflow_id: str = "unattended:gate2/synthetic:issue:82",
) -> dict[str, Any]:
    """Execute the fixed lifecycle and replay the resulting Workflow history."""

    client = await Client.connect(address, namespace=namespace)
    execution = ExecutionHandle(
        workflow_id=probe_workflow_id,
        attempt=1,
        workspace_id=workspace_id(probe_workflow_id),
        executor_id=executor_id(probe_workflow_id, 1),
        started_at="2026-07-30T00:00:00+00:00",
    )
    result = await client.execute_workflow(
        UnattendedGate2Workflow.run,
        execution,
        id=probe_workflow_id,
        task_queue=TASK_QUEUE,
        execution_timeout=timedelta(minutes=15),
        result_type=TaskSubmission,
    )
    handle = client.get_workflow_handle(probe_workflow_id)
    history = await handle.fetch_history()
    await Replayer(workflows=[UnattendedGate2Workflow]).replay_workflow(history)
    return {
        "temporal_connection": "PASS",
        "activity_execution": (
            "PASS"
            if result.verdict == "PROVIDER_FREE_RUNTIME_PROOF"
            else "FAIL"
        ),
        "workflow_replay": "PASS",
        "result": {
            "verdict": result.verdict,
            "changed_paths": result.changed_paths,
            "commands_executed": result.commands_executed,
            "test_evidence": result.test_evidence,
            "limitations": result.limitations,
        },
    }
