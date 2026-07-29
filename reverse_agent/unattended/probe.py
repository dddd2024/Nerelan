"""Bounded live compatibility probes for the selected Temporal stack."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio.client import Client
from temporalio.worker import Replayer

from .identifiers import TASK_QUEUE
from .worker import build_worker
from .workflows import UnattendedGate2Workflow


async def run_temporal_probe(
    *,
    address: str,
    namespace: str,
    probe_workflow_id: str = "unattended:gate2/synthetic:issue:76",
) -> dict[str, Any]:
    """Execute one Activity and replay the resulting Workflow history."""

    client = await Client.connect(address, namespace=namespace)
    async with build_worker(client):
        result = await client.execute_workflow(
            UnattendedGate2Workflow.run,
            "synthetic-gate2",
            id=probe_workflow_id,
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(minutes=2),
        )
    handle = client.get_workflow_handle(probe_workflow_id)
    history = await handle.fetch_history()
    await Replayer(workflows=[UnattendedGate2Workflow]).replay_workflow(history)
    return {
        "temporal_connection": "PASS",
        "activity_execution": "PASS" if result == "activity:synthetic-gate2" else "FAIL",
        "workflow_replay": "PASS",
        "result": result,
    }
