"""Deterministic Gate 2 Workflow coordinating controller-only Activities."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from reverse_agent.unattended.contracts import ExecutionHandle
    from reverse_agent.unattended.identifiers import SANDBOX_CONTROLLER_TASK_QUEUE
    from reverse_agent.unattended.temporal_contracts import (
        AttemptReadinessResult,
        CleanupResult,
        Gate2WorkflowResult,
        LaunchAttemptResult,
        OpenHandsLifecycleResult,
        TaskSubmissionEvidence,
    )


@workflow.defn
class UnattendedGate2Workflow:
    @workflow.run
    async def run(self, handle: ExecutionHandle) -> Gate2WorkflowResult:
        """Run fixed lifecycle Activities; perform no I/O in Workflow code."""

        retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=2,
        )
        cleanup_required = True
        cleanup_completed = False
        try:
            launch = await workflow.execute_activity(
                "launch_or_reconcile_attempt",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
                result_type=LaunchAttemptResult,
            )
            if launch.state != "running":
                raise RuntimeError("attempt_launch_not_running")
            readiness = await workflow.execute_activity(
                "wait_attempt_server",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=retry,
                result_type=AttemptReadinessResult,
            )
            if not readiness.alive or not readiness.health:
                raise RuntimeError("attempt_readiness_failed")
            lifecycle = await workflow.execute_activity(
                "start_openhands_conversation",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
                result_type=OpenHandsLifecycleResult,
            )
            if lifecycle.conversation_id != handle.executor_id:
                raise RuntimeError("conversation_identity_mismatch")
            submission = await workflow.execute_activity(
                "collect_openhands_result",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=retry,
                result_type=TaskSubmissionEvidence,
            )
            cleanup = await workflow.execute_activity(
                "cleanup_attempt",
                handle,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
                result_type=CleanupResult,
            )
            cleanup_completed = (
                cleanup.attempt_container_absent
                and cleanup.attempt_workspace_absent
            )
            if not cleanup_completed:
                raise RuntimeError("attempt_cleanup_incomplete")
            return Gate2WorkflowResult(
                submission=submission,
                cleanup=cleanup,
                result_label="PROVIDER_FREE_RUNTIME_PROOF",
            )
        finally:
            if cleanup_required and not cleanup_completed:
                await workflow.execute_activity(
                    "cleanup_attempt",
                    handle,
                    task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry,
                    result_type=CleanupResult,
                )
