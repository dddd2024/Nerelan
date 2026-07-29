"""A deliberately small deterministic Workflow for Gate 2."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from reverse_agent.unattended.activities import run_synthetic_activity


@workflow.defn
class UnattendedGate2Workflow:
    @workflow.run
    async def run(self, synthetic_task: str) -> str:
        """Schedule one bounded Activity; perform no I/O in Workflow code."""

        return await workflow.execute_activity(
            run_synthetic_activity,
            synthetic_task,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_attempts=2,
            ),
        )
