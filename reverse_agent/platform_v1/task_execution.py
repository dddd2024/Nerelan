"""Single trusted programmatic execution path for an already-created TaskStore task.

Both the HTTP Task API and LangGraph worker adapter call
:class:`TaskExecutionService.execute`. The service owns the entire lifecycle
from ``QUEUED`` through executor dispatch, validation persistence, evidence
recording, and terminal status. It never synthesizes a new executor kind.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .binding_resolver import BindingResolver
from .opencode_executor import (
    RoleContext,
    _collect_product_diff,
    _collect_final_product_files,
    _handoff_digest,
    _remove_handoff,
    _validate_plan_handoff,
    _validate_review_handoff,
    handoff_dir,
)
from .run_store import (
    InvalidTransitionError,
    TaskStore,
    TaskStoreError,
)
from .task_runtime import (
    ExecutorCallback,
    ExecutorRouter,
    ExecutorRuntimeError,
    LocalValidationRunner,
)


@dataclass(frozen=True)
class TaskExecutionOutcome:
    task_id: str
    execution_id: str
    success: bool
    validation_command_id: str
    validation_exit_code: int
    changed_files: tuple[Mapping[str, Any], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    failure_classification: str = ""
    failure_detail: str = ""


def _build_executor_kwargs(
    task: Mapping[str, Any],
    *,
    binding_resolver: Any | None = None,
    lease_provider: Any | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    executor_kind = str(_map_task_field(task, "executor_kind", ""))
    if executor_kind == "opencode":
        binding_ref = str(_map_task_field(task, "binding_ref", ""))
        if binding_ref:
            resolver = binding_resolver or BindingResolver()
            kwargs["binding_resolution"] = resolver.resolve(
                binding_ref, task_executor=executor_kind
            )
        else:
            model_id = str(
                _map_task_field(task, "model_profile_ref", "")
            ) or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
            kwargs["model_id"] = model_id
        kwargs["repo_dir"] = os.environ.get("REVERSE_AGENT_REPO_DIR", "")
        kwargs["base_ref"] = str(_map_task_field(task, "branch", ""))
        if lease_provider is not None:
            kwargs["lease_provider"] = lease_provider
    return kwargs


def _map_task_field(task: Mapping[str, Any], key: str, default: Any) -> Any:
    if isinstance(task, Mapping):
        return task.get(key, default)
    return getattr(task, key, default)


class TaskExecutionService:
    """Execute one already-QUEUED TaskStore task through the shared executor
    router and persist the full lifecycle (status transitions, events,
    changed files, validation result, evidence).
    """

    def __init__(
        self,
        *,
        store: TaskStore,
        router: ExecutorRouter,
        binding_resolver: Any | None = None,
        lease_provider: Any | None = None,
    ) -> None:
        self.store = store
        self.router = router
        self.binding_resolver = binding_resolver
        self.lease_provider = lease_provider

    def execute(
        self,
        task_id: str,
        *,
        workspace_root: str,
        validation_command_id: str = "git_diff_check",
    ) -> TaskExecutionOutcome:
        try:
            task = self.store.get_task(task_id)
        except TaskStoreError:
            raise TaskExecutionError(f"task_not_found:{task_id}")

        if task.status != "QUEUED":
            raise TaskExecutionError(
                f"task_not_queued:{task_id}:{task.status}"
            )

        executor_kind = task.executor_kind
        running_status = (
            "RUNNING_FIXTURE"
            if executor_kind == "deterministic_fixture"
            else "RUNNING"
        )
        review_status = (
            "READY_FOR_REVIEW_FIXTURE"
            if executor_kind == "deterministic_fixture"
            else "READY_FOR_REVIEW"
        )

        before_evidence = tuple(ev.get("id", "") for ev in task.evidence_refs)

        try:
            executor_kwargs = _build_executor_kwargs(
                task,
                binding_resolver=self.binding_resolver,
                lease_provider=self.lease_provider,
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=str(exc),
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(
                ev.get("id", "") for ev in final.evidence_refs
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id=validation_command_id,
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        self.store.transition_to(task_id, "PREPARING_WORKSPACE")
        self.store.transition_to(task_id, running_status)
        self.store.add_event(
            task_id,
            event_type="EXECUTOR_RUNNING",
            title="Executor running",
            description=f"Executor {executor_kind} started",
            metadata={"executor_kind": executor_kind},
        )

        try:
            exec_result = self._dispatch_executor(
                task=task,
                workspace_root=workspace_root,
                validation_command_id=validation_command_id,
                executor_kwargs=executor_kwargs,
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=str(exc),
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(
                ev.get("id", "")
                for ev in final.evidence_refs
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id=validation_command_id,
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        if exec_result["success"]:
            self.store.transition_to(task_id, "VALIDATING")
            self.store.transition_to(task_id, review_status)
            self.store.add_event(
                task_id,
                event_type="VALIDATED",
                title="Validation passed",
                description=f"{exec_result['validation_command_id']} passed",
                metadata={
                    "validation_exit_code": exec_result["validation_exit_code"],
                },
            )
        else:
            classification = (
                "blocked"
                if "unapproved" in exec_result.get("error", "")
                else exec_result.get("failure_classification", "failed")
            )
            if classification == "":
                classification = "failed"
            self.store.classify_failure(
                task_id,
                classification=classification,
                detail=exec_result.get("error", "execution failed"),
            )
            self.store.add_event(
                task_id,
                event_type="EXECUTOR_FINISHED",
                title="Executor finished",
                description=exec_result.get("error", "execution failed"),
                metadata={
                    "validation_exit_code": exec_result["validation_exit_code"],
                },
            )

        final = self.store.get_task(task_id)
        after_evidence = tuple(ev.get("id", "") for ev in final.evidence_refs)

        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=final.execution_id,
            success=exec_result["success"],
            validation_command_id=exec_result["validation_command_id"],
            validation_exit_code=exec_result["validation_exit_code"],
            changed_files=tuple(final.changed_files),
            evidence_ids=tuple(after_evidence[len(before_evidence):]),
            failure_classification=final.failure_classification,
            failure_detail=final.failure_detail,
        )

    def execute_sequential_team(
        self,
        task_id: str,
        *,
        workspace_root: str,
    ) -> TaskExecutionOutcome:
        """Execute ONE already-QUEUED OpenCode Task through planner->coder->reviewer
        sequentially inside a single shared worktree.

        The method:
        1. validates workspace_root before any path use;
        2. loads the existing Task;
        3. requires status == QUEUED and executor_kind == opencode;
        4. reuses the existing Binding/model resolution path;
        5. obtains the configured OpenCode executor through ExecutorRouter.create_executor;
        6. prepares exactly ONE linked worktree;
        7. delegates planner->coder->reviewer ordering to build_sequential_team_graph();
        8. uses a role worker adapter closure for executor calls, handoff validation,
           and workspace/product invariants;
        9. durably classifies any role failure or invariant violation;
        10. cleans up runtime handoff artifacts;
        11. persists final product changed_files only;
        12. reaches the existing review/failed terminal semantics.
        """
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise TaskExecutionError("workspace_root_invalid")

        try:
            task = self.store.get_task(task_id)
        except TaskStoreError:
            raise TaskExecutionError(f"task_not_found:{task_id}")

        if task.status != "QUEUED":
            raise TaskExecutionError(
                f"task_not_queued:{task_id}:{task.status}"
            )

        executor_kind = task.executor_kind
        if executor_kind != "opencode":
            raise TaskExecutionError(
                f"task_not_opencode:{task_id}:{executor_kind}"
            )

        before_evidence = tuple(ev.get("id", "") for ev in task.evidence_refs)

        try:
            executor_kwargs = _build_executor_kwargs(
                task,
                binding_resolver=self.binding_resolver,
                lease_provider=self.lease_provider,
            )
            executor = self.router.create_executor(
                executor_kind=executor_kind,
                **executor_kwargs,
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=str(exc),
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(ev.get("id", "") for ev in final.evidence_refs)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id="",
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        self.store.transition_to(task_id, "PREPARING_WORKSPACE")
        try:
            prepared = executor.prepare_worktree_once(
                task_id, Path(workspace_root), self._store_event_callback
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=f"worktree_preparation_failed:{exc}",
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(ev.get("id", "") for ev in final.evidence_refs)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id="",
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )
        handoff = handoff_dir(prepared.worktree)
        self.store.transition_to(task_id, "RUNNING")
        self.store.add_event(
            task_id,
            event_type="EXECUTOR_RUNNING",
            title="Sequential team execution",
            description="planner->coder->reviewer in shared worktree",
            metadata={
                "execution_id": prepared.execution_id,
                "executor_kind": executor_kind,
                "sequential_roles": ("planner", "coder", "reviewer"),
                "shared_worktree": str(prepared.worktree),
                "workspace": workspace_root,
            },
        )
        baseline_product = _collect_product_diff(prepared.worktree)
        self.store.set_changed_files(task_id, baseline_product)

        from reverse_agent.workflows.team_graph import (
            TeamGraphError,
            WorkerAssignment,
            WorkerExecutionResult,
            build_sequential_team_graph,
        )

        plan_digest = ""
        review_digest = ""
        coder_product_snapshot: tuple[dict[str, Any], ...] = ()
        _seq_worker_results: list[dict[str, Any]] = []
        _seq_roles_executed: list[str] = []

        def _make_role_worker(
            prepared_ctx: Any,
            handoff_dir_path: Path,
            baseline: tuple[dict[str, Any], ...],
        ):
            nonlocal plan_digest, review_digest, coder_product_snapshot

            def _role_worker(wa: "WorkerAssignment") -> "WorkerExecutionResult":
                nonlocal plan_digest, review_digest, coder_product_snapshot

                role = wa.role
                role_context = RoleContext(
                    role=role,
                    task_id=wa.task_id,
                    workspace=prepared_ctx.worktree,
                    plan_path=handoff_dir_path / "plan.md",
                    plan_digest=plan_digest,
                )

                if role == "planner":
                    handoff_dir_path.mkdir(parents=True, exist_ok=True)

                try:
                    result = executor.execute_role_prepared(
                        prepared_ctx,
                        self.store,
                        role_context=role_context,
                        event_callback=self._store_event_callback,
                    )
                except Exception as exc:
                    _seq_roles_executed.append(role)
                    _seq_worker_results.append({
                        "role": role,
                        "worker_id": wa.worker_id,
                        "task_id": wa.task_id,
                        "execution_id": "",
                        "success": False,
                        "validation_exit_code": -1,
                        "failure_classification": "executor_error",
                        "failure_detail": f"{exc.__class__.__name__}:{exc}",
                        "reasons": [f"executor_exception:{exc.__class__.__name__}"],
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id,
                        task_id=wa.task_id,
                        execution_id="",
                        success=False,
                        validation_exit_code=-1,
                        failure_classification="executor_error",
                        failure_detail=f"{exc.__class__.__name__}:{exc}",
                        reasons=(f"executor_exception:{exc.__class__.__name__}",),
                    )

                if not result.success:
                    _seq_roles_executed.append(role)
                    _seq_worker_results.append({
                        "role": role,
                        "worker_id": wa.worker_id,
                        "task_id": wa.task_id,
                        "execution_id": getattr(result, "execution_id", ""),
                        "success": False,
                        "validation_exit_code": result.validation_exit_code,
                        "failure_classification": result.failure_classification,
                        "failure_detail": result.error,
                        "reasons": [result.failure_classification or "role_failed"],
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id,
                        task_id=wa.task_id,
                        execution_id=getattr(result, "execution_id", ""),
                        success=False,
                        validation_exit_code=result.validation_exit_code,
                        evidence_ids=(),
                        failure_classification=result.failure_classification,
                        failure_detail=result.error,
                        reasons=(result.failure_classification or "role_failed",),
                    )

                if role == "planner":
                    invalid = _validate_plan_handoff(handoff_dir_path / "plan.md")
                    if invalid:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "invalid_plan_handoff",
                            "failure_detail": invalid,
                            "reasons": ["invalid_plan_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="invalid_plan_handoff",
                            failure_detail=invalid,
                            reasons=("invalid_plan_handoff",),
                        )
                    plan_digest = _handoff_digest(handoff_dir_path / "plan.md")
                    planner_post = _collect_product_diff(prepared_ctx.worktree)
                    if planner_post != baseline:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "planner_product_mutation",
                            "failure_detail": "planner mutated product files",
                            "reasons": ["planner_product_mutation"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="planner_product_mutation",
                            failure_detail="planner mutated product files",
                            reasons=("planner_product_mutation",),
                        )
                elif role == "coder":
                    if not (handoff_dir_path / "plan.md").is_file():
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "missing_plan_handoff",
                            "failure_detail": "plan handoff missing when coder started",
                            "reasons": ["missing_plan_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="missing_plan_handoff",
                            failure_detail="plan handoff missing when coder started",
                            reasons=("missing_plan_handoff",),
                        )
                    coder_product_snapshot = _collect_product_diff(
                        prepared_ctx.worktree
                    )
                    if not coder_product_snapshot:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "no_coder_product_diff",
                            "failure_detail": "coder did not produce a product diff",
                            "reasons": ["no_coder_product_diff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="no_coder_product_diff",
                            failure_detail="coder did not produce a product diff",
                            reasons=("no_coder_product_diff",),
                        )
                elif role == "reviewer":
                    invalid_review = _validate_review_handoff(
                        handoff_dir_path / "review.md"
                    )
                    if invalid_review:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "invalid_review_handoff",
                            "failure_detail": invalid_review,
                            "reasons": ["invalid_review_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="invalid_review_handoff",
                            failure_detail=invalid_review,
                            reasons=("invalid_review_handoff",),
                        )
                    review_digest = _handoff_digest(handoff_dir_path / "review.md")
                    reviewer_post = _collect_product_diff(prepared_ctx.worktree)
                    if reviewer_post != coder_product_snapshot:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role,
                            "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False,
                            "validation_exit_code": -1,
                            "failure_classification": "reviewer_product_mutation",
                            "failure_detail": "reviewer mutated coder product diff",
                            "reasons": ["reviewer_product_mutation"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False,
                            validation_exit_code=-1,
                            failure_classification="reviewer_product_mutation",
                            failure_detail="reviewer mutated coder product diff",
                            reasons=("reviewer_product_mutation",),
                        )

                _seq_roles_executed.append(role)
                _seq_worker_results.append({
                    "role": role,
                    "worker_id": wa.worker_id,
                    "task_id": wa.task_id,
                    "execution_id": result.execution_id,
                    "success": True,
                    "validation_exit_code": result.validation_exit_code,
                    "failure_classification": "",
                    "failure_detail": "",
                    "reasons": [],
                })
                return WorkerExecutionResult(
                    worker_id=wa.worker_id,
                    task_id=wa.task_id,
                    execution_id=result.execution_id,
                    success=True,
                    validation_exit_code=result.validation_exit_code,
                    evidence_ids=(),
                    failure_classification="",
                    failure_detail="",
                )

            return _role_worker

        role_worker = _make_role_worker(prepared, handoff, baseline_product)
        seq_graph = build_sequential_team_graph(worker=role_worker)
        base_assignment = WorkerAssignment(
            worker_id="sequential",
            role="planner",
            task_id=task_id,
            workspace_root=str(prepared.worktree),
        )

        try:
            graph_result = seq_graph.invoke({
                "assignments": [base_assignment.to_dict()],
            })
        except TeamGraphError as exc:
            failure_reason = str(exc)
            worker_results_raw = list(_seq_worker_results)
            roles_executed = list(_seq_roles_executed)
            last_failure_raw = None
            for wr in reversed(worker_results_raw):
                if not wr.get("success", True):
                    last_failure_raw = wr
                    break
            if last_failure_raw:
                classification = last_failure_raw.get(
                    "failure_classification", "failed"
                ) or "failed"
                failure_detail = last_failure_raw.get("failure_detail", failure_reason)
            else:
                classification = "failed"
                failure_detail = failure_reason

            self._complete_sequential_team_failure(
                task_id,
                None,
                roles_executed,
                worker_results_raw,
                baseline_product,
                plan_digest=plan_digest,
                classification=classification,
                reasons=(failure_reason, classification),
            )
            return self._build_sequential_team_outcome(
                task_id,
                success=False,
                validation_exit_code=-1,
                validation_command_id="",
                changed_files=baseline_product,
                roles_executed=roles_executed,
                role_results=worker_results_raw,
                plan_digest=plan_digest,
                baseline_product=baseline_product,
                before_evidence=before_evidence,
                failure_classification=classification,
                failure_detail=failure_detail,
                reasons=(failure_reason, classification),
            )

        team_result = graph_result.get("team_execution_result", {})
        worker_results_raw = list(team_result.get("worker_results", []))
        roles_executed = ["planner", "coder", "reviewer"]

        _remove_handoff(handoff)
        final_changed = _collect_final_product_files(prepared.worktree)
        self.store.set_changed_files(task_id, final_changed)

        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=str(prepared.worktree),
            )
        except ExecutorRuntimeError:
            val_exit, val_output, val_digest = -1, "", ""

        self.store.transition_to(task_id, "VALIDATING")
        if val_exit == 0:
            self.store.transition_to(task_id, "READY_FOR_REVIEW")
            self.store.add_event(
                task_id,
                event_type="VALIDATED",
                title="Sequential team validated",
                description="planner->coder->reviewer all succeeded",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": "git_diff_check",
                    "plan_digest": plan_digest,
                    "review_digest": review_digest,
                    "roles_executed": roles_executed,
                },
            )
            success = True
            classification = ""
            failure_detail = ""
        else:
            self.store.set_validation_result(
                task_id,
                command_id="git_diff_check",
                exit_code=val_exit,
                output_digest=val_digest,
            )
            self.store.add_evidence(
                task_id,
                category="Validation",
                label="git_diff_check",
                value=str(val_exit),
                status="fail",
                detail=val_output,
                raw_json_digest=val_digest,
            )
            self.store.transition_to(task_id, "FAILED")
            success = False
            classification = "deterministic_validation_failure"
            failure_detail = f"git_diff_check exit={val_exit}"
            self.store.add_event(
                task_id,
                event_type="EXECUTOR_FINISHED",
                title="Sequential team validation failed",
                description=failure_detail,
                metadata={"validation_exit_code": val_exit},
            )

        self._persist_sequential_team_evidence(
            task_id,
            success,
            val_exit,
            val_digest,
            roles_executed,
            worker_results_raw,
            plan_digest,
            review_digest,
            final_changed,
            baseline_product,
            classification,
            failure_detail,
        )

        return self._build_sequential_team_outcome(
            task_id=task_id,
            success=success,
            validation_exit_code=val_exit,
            validation_command_id="git_diff_check",
            changed_files=final_changed,
            roles_executed=roles_executed,
            role_results=worker_results_raw,
            plan_digest=plan_digest,
            baseline_product=baseline_product,
            before_evidence=before_evidence,
            failure_classification=classification,
            failure_detail=failure_detail,
            reasons=(),
        )

    def _complete_sequential_team_failure(
        self,
        task_id: str,
        result: Any,
        roles_executed: list[str],
        role_results: list[dict[str, Any]],
        baseline_product: tuple[dict[str, Any], ...],
        *,
        classification: str,
        reasons: tuple[str, ...],
        plan_digest: str = "",
    ) -> None:
        self.store.set_changed_files(task_id, baseline_product)
        try:
            last_role = roles_executed[-1] if roles_executed else "none"
            self.store.classify_failure(
                task_id,
                classification=classification,
                detail="sequential team failed at role=%s" % last_role,
            )
        except TaskStoreError:
            pass
        self.store.add_event(
            task_id,
            event_type="EXECUTOR_FINISHED",
            title="Sequential team failed",
            description=f"roles={','.join(roles_executed) if roles_executed else 'none'}",
            metadata={
                "roles_executed": roles_executed,
                "classification": classification,
                "reasons": list(reasons),
                "plan_digest": plan_digest,
            },
        )

    def _persist_sequential_team_evidence(
        self,
        task_id: str,
        success: bool,
        val_exit: int,
        val_digest: str,
        roles_executed: list[str],
        role_results: list[dict[str, Any]],
        plan_digest: str,
        review_digest: str,
        final_changed: list[dict[str, Any]],
        baseline_product: tuple[dict[str, Any], ...],
        classification: str,
        failure_detail: str,
    ) -> None:
        self.store.set_validation_result(
            task_id,
            command_id="git_diff_check",
            exit_code=val_exit,
            output_digest=val_digest,
        )
        self.store.add_evidence(
            task_id,
            category="Validation",
            label="git_diff_check",
            value=str(val_exit),
            status="pass" if val_exit == 0 else "fail",
            detail="git_diff_check after sequential team",
            raw_json_digest=val_digest,
        )
        self.store.add_evidence(
            task_id,
            category="Executor",
            label="executor_kind",
            value="opencode",
            status="pass",
            detail="sequential team executor_kind opencode",
            raw_json_digest="",
        )
        self.store.add_evidence(
            task_id,
            category="Executor",
            label="sequential_roles",
            value=",".join(roles_executed),
            status="pass" if success else "fail",
            detail=(
                "plan_digest=%s review_digest=%s validation_exit=%d changed_files=%d"
                % (plan_digest[:12], review_digest[:12], val_exit, len(final_changed))
            ),
            raw_json_digest="",
        )

    def _build_sequential_team_outcome(
        self,
        task_id: str,
        *,
        success: bool,
        validation_exit_code: int,
        validation_command_id: str,
        changed_files: list[dict[str, Any]],
        roles_executed: list[str],
        role_results: list[dict[str, Any]],
        plan_digest: str,
        baseline_product: tuple[dict[str, Any], ...],
        before_evidence: tuple[str, ...],
        failure_classification: str,
        failure_detail: str,
        reasons: tuple[str, ...],
    ) -> TaskExecutionOutcome:
        final = self.store.get_task(task_id)
        after_evidence = tuple(ev.get("id", "") for ev in final.evidence_refs)
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=final.execution_id,
            success=success,
            validation_command_id=validation_command_id,
            validation_exit_code=validation_exit_code,
            changed_files=tuple(final.changed_files),
            evidence_ids=tuple(after_evidence[len(before_evidence):]),
            failure_classification=final.failure_classification,
            failure_detail=final.failure_detail,
        )

    def _dispatch_executor(
        self,
        *,
        task: Any,
        workspace_root: str,
        validation_command_id: str,
        executor_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.router.dispatch_execute(
            task_id=task.id,
            store=self.store,
            executor_kind=task.executor_kind,
            workspace_root=workspace_root,
            event_callback=self._store_event_callback,
            **executor_kwargs,
        )
        self.store.set_changed_files(task.id, result.changed_files)
        self.store.set_validation_result(
            task.id,
            command_id=result.validation_command_id,
            exit_code=result.validation_exit_code,
            output_digest=result.validation_output_digest,
        )
        self.store.add_evidence(
            task.id,
            category="Validation",
            label=result.validation_command_id,
            value=str(result.validation_exit_code),
            status="pass" if result.validation_exit_code == 0 else "fail",
            detail=result.validation_output_summary,
            raw_json_digest=result.validation_output_digest,
        )
        executor_detail = (
            "fixture/provider-free executor"
            if task.executor_kind == "deterministic_fixture"
            else task.executor_kind
        )
        self.store.add_evidence(
            task.id,
            category="Executor",
            label="executor_kind",
            value=task.executor_kind,
            status="pass",
            detail=executor_detail,
        )
        return {
            "success": result.success,
            "validation_command_id": result.validation_command_id,
            "validation_exit_code": result.validation_exit_code,
            "validation_output_digest": result.validation_output_digest,
            "changed_files": result.changed_files,
            "error": result.error,
            "failure_classification": getattr(result, "failure_classification", ""),
        }

    def _store_event_callback(self, task_id: str, event: dict[str, Any]) -> None:
        try:
            self.store.add_event(
                task_id,
                event_type=event.get("type", "EXECUTOR_FINISHED"),
                title=event.get("title", "Executor event"),
                description=event.get("description", ""),
                raw_log=event.get("raw_log", ""),
                metadata=event.get("metadata"),
            )
        except Exception:
            pass


class TaskExecutionError(Exception):
    """Raised when the execution service cannot honor a request."""


def _resolve_workspace_root(store: TaskStore) -> str:
    try:
        db_path = store.db_path
        db_dir = os.path.dirname(db_path) or "."
        workspace_root = os.path.join(db_dir, "task_workspaces")
    except Exception:
        workspace_root = os.path.join(
            tempfile.gettempdir(), "issue151_task_workspaces"
        )
    os.makedirs(workspace_root, exist_ok=True)
    return workspace_root
