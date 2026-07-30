"""Bounded live compatibility probes for the selected Temporal stack."""

from __future__ import annotations

import base64
from datetime import timedelta
from typing import Any

from temporalio.client import Client
from temporalio.worker import Replayer

from .contracts import ExecutionHandle
from .identifiers import TASK_QUEUE, executor_id, workspace_id
from .temporal_contracts import Gate2WorkflowResult
from .workflows import UnattendedGate2Workflow

_FORBIDDEN_HISTORY_MARKERS = (
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "LITELLM_MASTER_KEY",
    "OH_SESSION_API_KEYS_0",
    "OPENAI_API_KEY",
    "SESSION_API_KEY",
)


def _history_secret_scan(
    rendered_history: str,
    *,
    sensitive_values: tuple[str, ...],
) -> bool:
    if any(marker in rendered_history for marker in _FORBIDDEN_HISTORY_MARKERS):
        return False
    for value in sensitive_values:
        if not value:
            return False
        encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
        if value in rendered_history or encoded in rendered_history:
            return False
    return True


async def run_temporal_probe(
    *,
    address: str,
    namespace: str,
    probe_workflow_id: str = "unattended:gate2/synthetic:issue:82",
    sensitive_values: tuple[str, ...] = (),
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
        result_type=Gate2WorkflowResult,
    )
    handle = client.get_workflow_handle(probe_workflow_id)
    history = await handle.fetch_history()
    secret_scan = _history_secret_scan(
        history.to_json(),
        sensitive_values=sensitive_values,
    )
    await Replayer(workflows=[UnattendedGate2Workflow]).replay_workflow(history)
    submission = result.submission
    return {
        "temporal_connection": "PASS",
        "activity_execution": (
            "PASS"
            if submission.verdict == "PROVIDER_FREE_RUNTIME_PROOF"
            else "FAIL"
        ),
        "workflow_history_secret_scan": "PASS" if secret_scan else "FAIL",
        "workflow_replay": "PASS",
        "cleanup": (
            "PASS"
            if result.cleanup.attempt_container_absent
            and result.cleanup.attempt_workspace_absent
            else "FAIL"
        ),
        "result": {
            "verdict": submission.verdict,
            "changed_paths": submission.changed_paths,
            "commands_executed": submission.commands_executed,
            "test_evidence": submission.test_evidence,
            "limitations": submission.limitations,
            "result_label": result.result_label,
        },
    }
