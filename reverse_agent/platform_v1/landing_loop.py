"""Durable publication and independent review orchestration.

Claims record intent. Bounded ticks enforce review, current checks, Ready
and pre-merge verdict transitions against current external observations.
"""
from __future__ import annotations

import json
from typing import Any

from .autonomy import AutonomyService
from .control_store import PlatformControlStore
from .github_adapter import LandingGitHubAdapter
from .run_store import TaskStoreError
from . import artifact_handoff as artifacts, model_review


class LandingLoopController:
    def __init__(self, *, control_store: PlatformControlStore,
                 autonomy: AutonomyService, github: LandingGitHubAdapter, owner_decisions=None) -> None:
        self.control_store = control_store
        self.autonomy = autonomy
        self.github = github
        self.owner_decisions = owner_decisions or (lambda state: ())

    def publish_and_review(self, task_id: str, *, window_id: str,
                           publication, goals, execution, workspace_root: str):
        """Advance one linked validate-only review using its routed executor.

        Task execution and repair admission remain owned by GoalService and the
        durable execution service, including their existing window budgets.
        """
        store = self.control_store.task_store
        goal_id = self.control_store.goal_id_for_task(task_id)
        goal = self.control_store.get_goal(goal_id)
        if goal.window_id != window_id:
            raise TaskStoreError("publication_window_mismatch")
        record = publication.publish_artifact(task_id, window_id=window_id, goal_id=goal_id)
        producer = store.get_task(task_id)
        if artifacts._load_evidence(producer, "ReviewRepair", producer.execution_id) is not None:
            goals._repair_rejected_reviews(goal_id)
        links = {row["plan_task_id"]: row for row in self.control_store.list_goal_tasks(goal_id)
                 if row["goal_revision"] == goal.revision}
        source = next((key for key, row in links.items() if row["task_id"] == task_id), None)
        reviews = [raw for raw in goal.tasks if raw.get("kind") == "review"
                   and raw.get("artifact_input") == {"plan_task_id": source}]
        if len(reviews) != 1:
            raise TaskStoreError("landing_requires_one_planned_review")
        review = store.get_task(links[reviews[0]["id"]]["task_id"])
        if not artifacts.model_review_input(review):
            raise TaskStoreError("landing_requires_validate_only_review")
        accepted = artifacts._load_evidence(store.get_task(task_id), artifacts.ACCEPTED_CATEGORY,
            store.get_task(task_id).execution_id)
        if not accepted or accepted["commit"] != record.commit_sha:
            raise TaskStoreError("landing_review_head_mismatch")
        history = self.control_store.list_task_escalations(goal_id)
        review_round = 1 + sum(row["goal_revision"] == goal.revision
            and row["plan_task_id"] == source and row["reason"].startswith("model_review_repair:")
            for row in history)
        state = self.control_store.ensure_landing(repository=goal.repository, goal_id=goal_id,
            pr_number=record.pr_number, head_sha=record.commit_sha, review_round=review_round)
        if review_round > goals.max_review_rounds:
            self.control_store.schedule_landing(state["identity"], expected_phase=state["phase"], phase="BLOCKED")
            raise TaskStoreError("model_review_round_limit")
        # The task's binding is the router's selected executor. Never construct a
        # preferred executor here; durable execution includes the host relay path.
        self.control_store.schedule_landing(state["identity"], expected_phase=state["phase"], phase="WAITING")
        if not any(row.get("category") == model_review.CATEGORY and row.get("label") == review.execution_id
                   for row in review.evidence_refs):
            from .unattended_coordinator import UnattendedCoordinator
            coordinator = UnattendedCoordinator(store=store, control_store=self.control_store,
                autonomy=self.autonomy, router=getattr(execution, "router", None),
                workspace_root=workspace_root, owner="landing-review-" + state["identity"],
                task_executor=lambda task_id: execution.execute_durable_single(
                    task_id=task_id, workspace_root=workspace_root))
            try:
                if not self.autonomy.authorize(window_id=window_id, operation="validate_task",
                        repository=goal.repository, subject_id=review.id, input_payload=state):
                    raise TaskStoreError("review_denied_by_window")
                epoch, _ = self.control_store.claim_task(window_id=window_id,
                    task_id=review.id, owner=coordinator.owner, lease_ms=coordinator.claim_lease_ms)
            except TaskStoreError as exc:
                store.add_event(review.id, event_type="EXECUTOR_PROGRESS", title="Landing review parked",
                    metadata={"reason": str(exc), "landing_identity": state["identity"]})
                return self.control_store.schedule_landing(state["identity"], expected_phase="WAITING", phase="BLOCKED")
            outcome = coordinator._execute_with_claim_renewal(window_id, review.id, epoch)
            self.control_store.complete_task_claim(window_id=window_id, task_id=review.id,
                owner=coordinator.owner, epoch=epoch,
                result=getattr(outcome, "failure_classification", "") or "review_execution_finished")
            completed = store.get_task(review.id)
            if not any(row.get("category") == model_review.CATEGORY and row.get("label") == completed.execution_id
                       for row in completed.evidence_refs):
                reason = getattr(outcome, "failure_classification", "") or "model_review_evidence_required"
                store.add_event(review.id, event_type="EXECUTOR_PROGRESS", title="Landing review parked",
                    metadata={"reason": reason, "landing_identity": state["identity"]})
                return self.control_store.schedule_landing(state["identity"], expected_phase="WAITING", phase="BLOCKED")
        comment = self.post_review(state["identity"], review.id, window_id=window_id)
        if not comment or comment["status"] != "SUCCEEDED":
            return self.control_store.get_landing(state["identity"])
        current = store.get_task(review.id)
        evidence_row = next(row for row in current.evidence_refs if row.get("category") == model_review.CATEGORY)
        if json.loads(evidence_row["detail"])["result"]["verdict"] == "REJECT":
            goals._repair_rejected_reviews(goal_id)
            if store.get_task(review.id).status == "BLOCKED":
                self.control_store.schedule_landing(state["identity"], expected_phase="WAITING", phase="BLOCKED")
        return self.control_store.get_landing(state["identity"])

    def post_review(self, identity: str, review_task_id: str, *, window_id: str):
        """Only host-verified retained evidence may produce a trusted marker.

        Model text stays in local evidence, never in a trusted GitHub comment.
        Reconcile the durable claim before any retry, including after a crash
        between remote creation and local receipt completion.
        """
        state = self.control_store.get_landing(identity)
        self._authorize(state, window_id, "review_comment")
        store = self.control_store.task_store
        task = store.get_task(review_task_id)
        binding = artifacts.bind_consumer_input(store, task.id, allow_create=False)
        if (binding["goal_id"] != state["goal_id"]
                or binding["producer"]["commit"] != state["head_sha"]):
            raise TaskStoreError("landing_review_head_mismatch")
        rows = [row for row in task.evidence_refs if row.get("category") == model_review.CATEGORY
                and row.get("label") == task.execution_id]
        if len(rows) != 1:
            raise TaskStoreError("model_review_evidence_required")
        run = store._get_durable_run(json.loads(rows[0]["detail"])["run_id"])
        evidence = model_review.verified_evidence(store, task, run, require_accept=False)
        pending = store._conn.execute("SELECT * FROM platform_coordinator_claims WHERE task_id=? AND window_id=? AND status='ACTIVE'",
            (task.id, window_id)).fetchone()
        if (pending is not None and pending["owner"] == "landing-review-" + identity
                and (task.status == "READY_FOR_REVIEW" or task.status == "FAILED"
                     and task.failure_classification == "model_review_rejected")):
            self.control_store.complete_task_claim(window_id=window_id, task_id=task.id,
                owner=pending["owner"], epoch=pending["epoch"], result="retained_review_reconciled")
        if evidence["head"] != state["head_sha"]:
            raise TaskStoreError("landing_review_head_mismatch")
        observed = self.github.observe_pr(state)
        if observed.get("head_sha") != state["head_sha"]:
            raise TaskStoreError("landing_review_stale_head")
        claim = self.control_store.landing_operation(identity, "review_comment")
        if claim is not None:
            resolved = self.reconcile(identity, "review_comment", window_id=window_id)
            if resolved["status"] != "ABSENT":
                return resolved
        claim_id = self.claim(identity, "review_comment", window_id=window_id)
        if not claim_id:
            return self.control_store.landing_operation(identity, "review_comment")
        result = evidence["result"]
        # Every byte is host-generated, so credentials and trusted markers in
        # model findings cannot be laundered through the host's GitHub identity.
        body = (f"Independent review: {len(result['findings'])} retained findings.\n"
                f"<!-- nerelan-operation:{claim_id} -->\n"
                f"Nerelan-Review: {result['verdict']} {state['head_sha']}")
        self.github.post_review_comment(state, claim_id, body)
        return self.reconcile(identity, "review_comment", window_id=window_id)

    def _authorize(self, state: dict[str, Any], window_id: str, operation: str = "") -> None:
        capability = "land_reviewed_pr"
        if operation == "review_comment" and "open_draft_pr" in self.control_store.get_window(window_id).capabilities:
            capability = "open_draft_pr"
        if not self.autonomy.authorize(
                window_id=window_id, operation=capability,
                repository=state["repository"], subject_id=state["goal_id"],
                input_payload=state):
            raise TaskStoreError("landing_denied_by_window")

    def claim(self, identity: str, operation: str, *, window_id: str) -> str | None:
        state = self.control_store.get_landing(identity)
        self._authorize(state, window_id, operation)
        return self.control_store.claim_landing_operation(identity, operation, window_id=window_id)

    def reconcile(self, identity: str, operation: str, *, window_id: str,
                  next_attempt_ms: int = 0) -> dict[str, Any]:
        state = self.control_store.get_landing(identity)
        self._authorize(state, window_id, operation)
        claim = self.control_store.landing_operation(identity, operation)
        if claim is None:
            raise TaskStoreError("landing_operation_not_found")
        if claim["status"] not in {"CLAIMED", "UNKNOWN"}:
            return claim
        observed = (self.github.reconcile_review_comment(state, claim["claim_id"])
                    if operation == "review_comment" else
                    self.github.reconcile_operation(state, operation, claim["claim_id"]))
        if (observed.get("identity") != identity
                or observed.get("claim_id") != claim["claim_id"]
                or observed.get("operation") != operation):
            raise TaskStoreError("landing_observation_mismatch")
        self.control_store.record_landing_outcome(
            identity, operation, claim["claim_id"], outcome=observed.get("outcome", "UNKNOWN"),
            evidence=observed, next_attempt_ms=next_attempt_ms)
        return self.control_store.landing_operation(identity, operation)

    def tick(self, identity: str, *, window_id: str):
        """One bounded transition; retry time and write intent survive restart."""
        from .control_store import _utc_now_ms
        from .github_adapter import GitHubAdapterError
        import fnmatch
        now = _utc_now_ms()
        store = self.control_store
        if not store.lease_landing_tick(identity, now):
            return store.get_landing(identity)
        state = store.get_landing(identity)
        lease = now + 300000
        def guard():
            if store.get_landing(identity)["tick_lease_ms"] != lease or _utc_now_ms() >= lease:
                raise TaskStoreError("landing_tick_lease_lost")
            self._authorize(state, window_id)
        def finish(phase, reason="", delay=30000):
            return store.finish_landing_tick(identity, phase, reason, _utc_now_ms() + delay, lease=lease)
        def observe():
            guard()
            pr = self.github.observe_pr(state)
            if pr.get("repository") != state["repository"] or pr.get("base_branch") != "main":
                raise TaskStoreError("landing_scope_changed")
            if pr.get("head_sha") != state["head_sha"]:
                raise TaskStoreError("landing_head_race")
            if not pr.get("main_sha"):
                raise TaskStoreError("landing_main_unknown")
            return pr
        try:
            guard()
            pending_update = store.landing_operation(identity, "update_branch")
            if pending_update:
                resolved = self.reconcile(identity, "update_branch", window_id=window_id)
                updated = self.github.observe_pr(state)
                if resolved["status"] == "SUCCEEDED" and updated.get("head_sha") != state["head_sha"]:
                    store.ensure_landing(repository=state["repository"], goal_id=state["goal_id"],
                        pr_number=state["pr_number"], head_sha=updated["head_sha"], review_round=state["review_round"] + 1)
                    return finish("SUPERSEDED", delay=0)
            pr = observe()
            if pr.get("merged"):
                claim = store.landing_operation(identity, "merge")
                if not claim or not pr.get("merge_commit"):
                    return finish("BLOCKED", "unrecorded_merge")
                result = self.reconcile(identity, "merge", window_id=window_id)
                if result["status"] == "SUCCEEDED" and pr["main_sha"] == pr["merge_commit"]:
                    return finish("COMPLETE", delay=0)
                return finish("RECONCILING", "main_merge_not_confirmed")
            if pr.get("state") != "OPEN":
                return finish("BLOCKED", "pull_request_closed")
            paths = pr.get("changed_paths")
            if not isinstance(paths, list) or not paths:
                return finish("BLOCKED", "changed_paths_required")
            # Sensitive operations are never authorized by repository delegation.
            if any(any(part in {".aws", ".ssh", "secrets", "credentials"} for part in p.lower().split("/"))
                   or p.lower().endswith((".pem", ".key")) for p in paths):
                return finish("BLOCKED", "r3_action_specific_owner_authorization_required")
            r2 = any(any(fnmatch.fnmatchcase(p, pattern) for pattern in (
                "AGENTS.md", "docs/agents/*", ".github/workflows/*", "reverse_agent/landing_review.py",
                "requirements*.txt", "pyproject.toml", "frontend/package.json", "frontend/package-lock.json")) for p in paths)
            decisions = tuple(d for d in self.owner_decisions(state) if d and d in pr.get("body", ""))
            if r2 and not decisions:
                return finish("BLOCKED", "r2_trusted_owner_decision_required")
            checks = self.github.observe_checks(state).get("checks", {})
            required = ["baseline", "state-gate"] + ([] if pr.get("draft") else ["landing-state-gate"])
            if not all(checks.get(name, {}).get("head_sha") == state["head_sha"]
                       and checks[name].get("status") == "completed"
                       and checks[name].get("conclusion") == "success"
                       and checks[name].get("fresh") is True for name in required):
                return finish("WAITING", "fresh_current_head_checks_required")
            operation = "update_branch" if pr.get("behind") else ("mark_ready" if pr.get("draft") else "merge")
            verdict = self.github.invoke_verdict(state, "assessment")
            if not verdict.get("passed"):
                reason = verdict.get("reason", "review_required")
                if "reject" in reason:
                    return finish("BLOCKED", reason)
                if not pr.get("behind"):
                    return finish("WAITING", reason)
            if not pr.get("behind") and r2 and not set(decisions).intersection(verdict.get("confirmed_decisions", ())):
                return finish("WAITING", "r2_independent_gate_confirmation_required")
            if self.github.observe_checks(state).get("checks", {}) != checks:
                return finish("WAITING", "checks_changed_during_assessment")
            prior = store.landing_operation(identity, operation)
            if prior:
                resolved = self.reconcile(identity, operation, window_id=window_id)
                if resolved["status"] != "ABSENT":
                    return finish("RECONCILING", "operation_" + resolved["status"].lower())
            claim = self.claim(identity, operation, window_id=window_id)
            if not claim:
                return finish("WAITING", "operation_claimed")
            fresh = observe()
            if fresh.get("main_sha") != pr.get("main_sha"):
                # This claim has not reached a remote write. Its absence is
                # known, so a later tick can reassess and merge-update main.
                store.record_landing_outcome(identity, operation, claim, outcome="ABSENT",
                    evidence={"reason": "main_moved_before_write", "head": state["head_sha"]})
                return finish("WAITING", "main_moved_reassess")
            if fresh != pr:
                return finish("BLOCKED", "landing_observation_changed")
            guard()
            if operation == "merge":
                # No API/subprocess operation may intervene between these calls.
                verdict = self.github.invoke_verdict(state, claim)
                if not verdict.get("passed"):
                    return finish("BLOCKED", verdict.get("reason", "premerge_verdict_rejected"))
                guard()
                self.github.merge_head_matched(state, claim)
            elif operation == "mark_ready":
                self.github.mark_ready(state, claim)
            else:
                self.github.update_branch(state, claim)
            result = self.reconcile(identity, operation, window_id=window_id)
            if operation == "update_branch" and result["status"] == "SUCCEEDED":
                updated = self.github.observe_pr(state)
                if updated.get("head_sha") != state["head_sha"]:
                    store.ensure_landing(repository=state["repository"], goal_id=state["goal_id"],
                        pr_number=state["pr_number"], head_sha=updated["head_sha"], review_round=state["review_round"] + 1)
                    return finish("SUPERSEDED", delay=0)
            return finish("RECONCILING", "external_result_" + result["status"].lower())
        except TaskStoreError as exc:
            return finish("BLOCKED", str(exc))
        except (GitHubAdapterError, OSError, ValueError, TimeoutError):
            return finish("WAITING", "github_api_backoff", delay=60000)
