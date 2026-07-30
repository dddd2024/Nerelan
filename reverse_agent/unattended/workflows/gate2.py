"""Deterministic Gate 2 Workflow coordinating controller-only Activities."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from reverse_agent.unattended.contracts import ExecutionHandle, TaskSubmission
    from reverse_agent.unattended.identifiers import SANDBOX_CONTROLLER_TASK_QUEUE


@workflow.defn
class UnattendedGate2Workflow:
    @workflow.run
    async def run(self, handle: ExecutionHandle) -> TaskSubmission:
        """Run fixed lifecycle Activities; perform no I/O in Workflow code."""

        retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=2,
        )
        launched = False
        try:
            await workflow.execute_activity(
                "launch_or_reconcile_attempt",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
                result_type=dict[str, object],
            )
            launched = True
            await workflow.execute_activity(
                "wait_attempt_server",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=retry,
                result_type=dict[str, bool],
            )
            await workflow.execute_activity(
                "start_openhands_conversation",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
                result_type=ExecutionHandle,
            )
            return await workflow.execute_activity(
                "collect_openhands_result",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=retry,
                result_type=TaskSubmission,
            )
        finally:
            if launched:
                await workflow.execute_activity(
                    "cleanup_attempt",
                    handle,
                    task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry,
                    result_type=dict[str, bool],
                )
