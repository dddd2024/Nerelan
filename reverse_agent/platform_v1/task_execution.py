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
from typing import Any, Mapping

from pathlib import Path

from .binding_resolver import BindingResolver
from .opencode_executor import (
    RoleContext,
    _collect_product_diff,
    _collect_final_product_files,
    _handoff_digest,
    _remove_handoff,
    _validate_plan_handoff,
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
        1. loads the existing Task;
        2. requires status == QUEUED and executor_kind == opencode;
        3. reuses the existing Binding/model resolution path;
        4. obtains the configured OpenCode executor through ExecutorRouter.create_executor;
        5. prepares exactly ONE linked worktree;
        6. executes planner -> coder -> reviewer in that workspace, fail-closing on any
           role failure, handoff invalidity, or role product-mutation violation;
        7. records role-order and shared-workspace evidence;
        8. cleans up runtime handoff artifacts;
        9. persists final product changed_files only;
        10. reaches the existing review/failed terminal semantics.
        """
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
        prepared = executor.prepare_worktree_once(
            task_id, Path(workspace_root), self._store_event_callback
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

        roles = ("planner", "coder", "reviewer")
        roles_executed: list[str] = []
        role_results: list[dict[str, Any]] = []
        plan_digest = ""

        for idx, role in enumerate(roles):
            pre_role_product = _collect_product_diff(prepared.worktree)
            plan_path = handoff / "plan.md"
            role_context = RoleContext(
                role=role,
                task_id=task_id,
                workspace=prepared.worktree,
                plan_path=plan_path,
                plan_digest=plan_digest,
                role_order_index=idx,
            )
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)

            result = executor.execute_role_prepared(
                prepared,
                self.store,
                role_context=role_context,
                event_callback=self._store_event_callback,
            )
            role_results.append({
                "role": role,
                "success": result.success,
                "validation_exit_code": result.validation_exit_code,
                "execution_id": result.execution_id,
                "workspace": result.workspace,
                "changed_files": result.changed_files,
            })
            roles_executed.append(role)

            if not result.success:
                reasons = (f"{role}_failed", result.failure_classification or "role_failed")
                classification = result.failure_classification or "failed"
                self._complete_sequential_team_failure(
                    task_id,
                    result,
                    roles_executed,
                    role_results,
                    baseline_product,
                    plan_digest=plan_digest,
                    classification=classification,
                    reasons=reasons,
                )
                return self._build_sequential_team_outcome(
                    task_id,
                    success=False,
                    validation_exit_code=result.validation_exit_code,
                    validation_command_id=result.validation_command_id,
                    changed_files=result.changed_files,
                    roles_executed=roles_executed,
                    role_results=role_results,
                    plan_digest=plan_digest,
                    baseline_product=baseline_product,
                    before_evidence=before_evidence,
                    failure_classification=classification,
                    failure_detail=result.error,
                    reasons=reasons,
                )

            if role == "planner":
                invalid = _validate_plan_handoff(handoff / "plan.md")
                if invalid:
                    reasons = ("invalid_plan_handoff",)
                    classification = "failed"
                    self._complete_sequential_team_failure(
                        task_id,
                        result,
                        roles_executed,
                        role_results,
                        baseline_product,
                        plan_digest="",
                        classification=classification,
                        reasons=reasons,
                    )
                    return self._build_sequential_team_outcome(
                        task_id,
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        changed_files=result.changed_files,
                        roles_executed=roles_executed,
                        role_results=role_results,
                        plan_digest="",
                        baseline_product=baseline_product,
                        before_evidence=before_evidence,
                        failure_classification=classification,
                        failure_detail=invalid,
                        reasons=reasons,
                    )
                plan_digest = _handoff_digest(handoff / "plan.md")

                planner_post = _collect_product_diff(prepared.worktree)
                if planner_post != baseline_product:
                    reasons = ("planner_product_mutation",)
                    classification = "failed"
                    self._complete_sequential_team_failure(
                        task_id,
                        result,
                        roles_executed,
                        role_results,
                        baseline_product,
                        plan_digest=plan_digest,
                        classification=classification,
                        reasons=reasons,
                    )
                    return self._build_sequential_team_outcome(
                        task_id,
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        changed_files=planner_post,
                        roles_executed=roles_executed,
                        role_results=role_results,
                        plan_digest=plan_digest,
                        baseline_product=baseline_product,
                        before_evidence=before_evidence,
                        failure_classification=classification,
                        failure_detail="planner mutated product files",
                        reasons=reasons,
                    )

            if role == "coder":
                if not (handoff / "plan.md").is_file():
                    reasons = ("missing_plan_handoff",)
                    classification = "failed"
                    self._complete_sequential_team_failure(
                        task_id,
                        result,
                        roles_executed,
                        role_results,
                        baseline_product,
                        plan_digest=plan_digest,
                        classification=classification,
                        reasons=reasons,
                    )
                    return self._build_sequential_team_outcome(
                        task_id,
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        changed_files=result.changed_files,
                        roles_executed=roles_executed,
                        role_results=role_results,
                        plan_digest=plan_digest,
                        baseline_product=baseline_product,
                        before_evidence=before_evidence,
                        failure_classification=classification,
                        failure_detail="plan handoff missing when coder started",
                        reasons=reasons,
                    )
                if not _collect_product_diff(prepared.worktree):
                    reasons = ("no_coder_product_diff",)
                    classification = "failed"
                    self._complete_sequential_team_failure(
                        task_id,
                        result,
                        roles_executed,
                        role_results,
                        baseline_product,
                        plan_digest=plan_digest,
                        classification=classification,
                        reasons=reasons,
                    )
                    return self._build_sequential_team_outcome(
                        task_id,
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        changed_files=result.changed_files,
                        roles_executed=roles_executed,
                        role_results=role_results,
                        plan_digest=plan_digest,
                        baseline_product=baseline_product,
                        before_evidence=before_evidence,
                        failure_classification=classification,
                        failure_detail="coder did not produce a product diff",
                        reasons=reasons,
                    )

            if role == "reviewer":
                reviewer_pre = _collect_product_diff(prepared.worktree)
                reviewer_post = _collect_product_diff(prepared.worktree)
                if reviewer_post != reviewer_pre:
                    reasons = ("reviewer_product_mutation",)
                    classification = "failed"
                    self._complete_sequential_team_failure(
                        task_id,
                        result,
                        roles_executed,
                        role_results,
                        baseline_product,
                        plan_digest=plan_digest,
                        classification=classification,
                        reasons=reasons,
                    )
                    return self._build_sequential_team_outcome(
                        task_id,
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        changed_files=reviewer_post,
                        roles_executed=roles_executed,
                        role_results=role_results,
                        plan_digest=plan_digest,
                        baseline_product=baseline_product,
                        before_evidence=before_evidence,
                        failure_classification=classification,
                        failure_detail="reviewer mutated coder product diff",
                        reasons=reasons,
                    )

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
            role_results,
            plan_digest,
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
            role_results=role_results,
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
            self.store.classify_failure(
                task_id,
                classification=classification,
                detail="sequential team failed at role=%s" % roles_executed[-1],
            )
        except TaskStoreError:
            pass
        self.store.add_event(
            task_id,
            event_type="EXECUTOR_FINISHED",
            title="Sequential team failed",
            description=f"roles={','.join(roles_executed)}",
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
                "plan_digest=%s validation_exit=%d changed_files=%d"
                % (plan_digest[:12], val_exit, len(final_changed))
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
