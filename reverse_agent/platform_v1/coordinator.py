"""Durable side-effect coordinator for one bounded Platform V1 execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .issue_task import LoadedIssueTask
from .run_store import RunRecord, RunState, SQLiteRunStore, TERMINAL_STATES


class PlatformV1Coordinator:
    def __init__(
        self,
        *,
        store: SQLiteRunStore,
        workspace_manager: Any,
        executor: Any,
        validator: Any,
        publisher: Any,
        workflow_observer: Any,
    ) -> None:
        self.store = store
        self.workspace_manager = workspace_manager
        self.executor = executor
        self.validator = validator
        self.publisher = publisher
        self.workflow_observer = workflow_observer

    def run(self, task: LoadedIssueTask) -> RunRecord:
        path = Path(self.workspace_manager.path) if hasattr(self.workspace_manager, "path") else Path(getattr(self.workspace_manager, "workspace_root", ".")) / task.execution_id
        record = self.store.get_or_create(task, str(path))
        if record.state in TERMINAL_STATES:
            if hasattr(self.publisher, "publish_evidence"):
                self.publisher.publish_evidence(record, task)
            return record
        if record.state == RunState.REWORK_REQUIRED:
            if record.attempt > task.max_rework_attempts:
                record = self.store.update(record.execution_id, failure_classification="REWORK_LIMIT_EXHAUSTED")
                return self.store.transition(record.execution_id, RunState.FAILED_TERMINAL)
            record = self.store.update(record.execution_id, attempt=record.attempt + 1)
            record = self.store.transition(record.execution_id, RunState.WORKSPACE_READY)
        if record.state == RunState.DISCOVERED:
            record = self.store.transition(record.execution_id, RunState.VALIDATED)
        if record.state == RunState.VALIDATED:
            worktree = self.workspace_manager.prepare(record.execution_id, record.branch, record.base_sha)
            record = self.store.update(record.execution_id, worktree_path=str(worktree))
            record = self.store.transition(record.execution_id, RunState.WORKSPACE_READY)
        worktree = Path(record.worktree_path)
        if record.state == RunState.EXECUTOR_RUNNING:
            if self.workspace_manager.has_changes(worktree):
                record = self.store.transition(
                    record.execution_id,
                    RunState.EXECUTOR_FINISHED,
                    detail={"reconciled": "existing_workspace_changes"},
                )
            else:
                record = self.store.transition(
                    record.execution_id,
                    RunState.WORKSPACE_READY,
                    detail={"reconciled": "executor_interrupted_without_changes"},
                )
        if record.state == RunState.WORKSPACE_READY:
            record = self.store.transition(record.execution_id, RunState.EXECUTOR_RUNNING)
            result = self.executor.execute(task, worktree, 1800)
            record = self.store.update(record.execution_id, executor_reference=result.executor_reference or f"output:{result.output_sha256[:16]}")
            if result.timed_out or result.exit_code != 0 or result.malformed:
                classification = "INFRASTRUCTURE_TIMEOUT" if result.timed_out else "PRODUCT_TEST_FAILURE"
                record = self.store.update(record.execution_id, failure_classification=classification)
                return self.store.transition(
                    record.execution_id,
                    RunState.REWORK_REQUIRED,
                    detail={
                        "executor": {
                            "exit_code": result.exit_code,
                            "timed_out": result.timed_out,
                            "elapsed_seconds": result.elapsed_seconds,
                            "output_sha256": result.output_sha256,
                            "summary": result.summary[:2000],
                            "malformed": result.malformed,
                        }
                    },
                )
            record = self.store.transition(record.execution_id, RunState.EXECUTOR_FINISHED)
        if record.state == RunState.EXECUTOR_FINISHED:
            checks = self.validator.run(task.work_item.required_checks, worktree, 1800)
            failures = [check for check in checks if check.classification != "SUCCESS"]
            if failures:
                record = self.store.update(record.execution_id, failure_classification=failures[0].classification)
                return self.store.transition(record.execution_id, RunState.REWORK_REQUIRED, detail={"checks": [check.to_mapping() for check in failures]})
            record = self.store.transition(record.execution_id, RunState.LOCAL_VALIDATED, detail={"checks": [check.to_mapping() for check in checks]})
        if record.state == RunState.LOCAL_VALIDATED:
            commit_sha = self.publisher.commit(worktree, task)
            record = self.store.update(record.execution_id, commit_sha=commit_sha, head_sha=commit_sha)
            record = self.store.transition(record.execution_id, RunState.COMMITTED)
        if record.state == RunState.COMMITTED:
            head_sha = self.publisher.push(worktree, task.work_item.target_branch)
            record = self.store.update(record.execution_id, head_sha=head_sha)
            record = self.store.transition(record.execution_id, RunState.PUSHED)
        if record.state == RunState.PUSHED:
            pr_number = self.publisher.ensure_draft_pr(task, record.head_sha)
            record = self.store.update(record.execution_id, pr_number=pr_number)
            record = self.store.transition(record.execution_id, RunState.DRAFT_PR_OPEN)
        if record.state in {RunState.DRAFT_PR_OPEN, RunState.WORKFLOWS_OBSERVED}:
            observations = self.workflow_observer.observe(task.work_item.repository, record.head_sha)
            record = self.store.update(record.execution_id, workflow_observations=observations)
            record = self.store.transition(record.execution_id, RunState.WORKFLOWS_OBSERVED)
        if record.state == RunState.WORKFLOWS_OBSERVED:
            classifications = {str(item.get("classification", "")) for item in record.workflow_observations}
            if "KNOWN_EXTERNAL_GATE_BLOCKER" in classifications:
                record = self.store.update(record.execution_id, failure_classification="KNOWN_EXTERNAL_GATE_BLOCKER")
                record = self.store.transition(record.execution_id, RunState.BLOCKED_EXTERNAL)
                if hasattr(self.publisher, "publish_evidence"):
                    self.publisher.publish_evidence(record, task)
                return record
            if classifications and classifications <= {"SUCCESS"}:
                record = self.store.update(record.execution_id, failure_classification="SUCCESS")
                record = self.store.transition(record.execution_id, RunState.READY_FOR_HUMAN)
                if hasattr(self.publisher, "publish_evidence"):
                    self.publisher.publish_evidence(record, task)
                return record
            if "PRODUCT_TEST_FAILURE" in classifications:
                record = self.store.update(record.execution_id, failure_classification="PRODUCT_TEST_FAILURE")
                return self.store.transition(record.execution_id, RunState.REWORK_REQUIRED)
            if "POLICY_GATE_FAILURE" in classifications or "TERMINAL_POLICY_VIOLATION" in classifications:
                record = self.store.update(record.execution_id, failure_classification="POLICY_GATE_FAILURE")
                record = self.store.transition(record.execution_id, RunState.FAILED_TERMINAL)
                if hasattr(self.publisher, "publish_evidence"):
                    self.publisher.publish_evidence(record, task)
                return record
            return record
        return record
