"""Failed agent_team tasks escalate to a stronger distinct agent (provider-free)."""
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
import reverse_agent.platform_v1.goal_service as goal_service_module
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

BASE = "b" * 40
ROSTER = {"simple": ("opencode", "cheap"), "coder": ("opencode", "mid"), "complex": ("claude_code", "strong")}


def _window_payload(max_retries=3):
    now = datetime.now(timezone.utc)
    return {"policy_id": "owner-window-esc", "policy_revision": 1, "owner_identity": "owner@example",
            "starts_at": (now - timedelta(seconds=5)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
            "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": max_retries, "confirmation": "ACTIVATE"}


def _launched(monkeypatch, roster=ROSTER, role="simple", checks=None, max_retries=3):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    monkeypatch.setattr(goal_service_module, "resolve_repository_workspace", lambda repository: object())
    monkeypatch.setattr(goal_service_module, "repository_base", lambda repository: BASE)

    def resolve(name):
        if name not in roster:
            raise TaskStoreError(f"agent_role_unfilled:{name}")
        return roster[name]
    goals = GoalService(store=store, control_store=control, roster_resolver=resolve)
    goal = goals.create({"objective": "Escalate on failure", "repository": "dddd2024/Nerelan",
                         "idempotency_key": f"esc-{role}", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "Edit docs", "instruction": "Edit docs", "agent_role": role,
         **({"validation_checks": checks} if checks else {})},
        {"id": "T002", "title": "Follow up", "instruction": "Follow up", "dependencies": ["T001"], "agent_role": "simple"},
    ])
    goals.approve(goal.id, expected_revision=1)
    window = autonomy.activate(_window_payload(max_retries))
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    return store, control, goals, goal


def _fail(store, task_id, status="FAILED", classification="patch_hygiene_failed"):
    store._conn.execute("UPDATE tasks SET status = ?, failure_classification = ? WHERE id = ?",
                        (status, classification, task_id))
    store._conn.commit()


def _link(control, goal_id, plan_task_id):
    return next(link for link in control.list_goal_tasks(goal_id) if link["plan_task_id"] == plan_task_id)


def test_failed_task_climbs_the_ladder_once_per_step_and_keeps_history(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    first = _link(control, goal.id, "T001")["task_id"]
    _fail(store, first)
    control.refresh_goal_status(goal.id)
    [step1] = goals.escalate_failed_tasks(goal.id)
    assert (step1["from_role"], step1["to_role"], step1["step"]) == ("simple", "coder", 1)
    assert step1["reason"] == "failed:patch_hygiene_failed"
    second = store.get_task(step1["to_task_id"])
    assert (second.executor_kind, second.binding_ref, second.status) == ("opencode", "mid", "QUEUED")
    assert _link(control, goal.id, "T001")["task_id"] == second.id
    assert store.get_task(first).status == "FAILED"  # failed evidence stays in place
    assert control.goal_id_for_task(first) == goal.id
    assert control.get_goal(goal.id).status == "RUNNING"
    assert goals.escalate_failed_tasks(goal.id) == ()  # nothing failed now: idempotent

    _fail(store, second.id)
    [step2] = goals.escalate_failed_tasks(goal.id)
    third = store.get_task(step2["to_task_id"])
    assert (step2["from_role"], step2["to_role"], step2["step"]) == ("coder", "complex", 2)
    assert (third.executor_kind, third.binding_ref, third.branch) == ("claude_code", "strong", BASE)

    _fail(store, third.id)
    assert goals.escalate_failed_tasks(goal.id) == ()  # complex is the top
    control.refresh_goal_status(goal.id)
    assert control.get_goal(goal.id).status == "BLOCKED"
    assert [row["to_role"] for row in control.list_task_escalations(goal.id)] == ["coder", "complex"]


def test_failed_checks_at_the_top_get_one_retry_by_the_same_agent(monkeypatch):
    # #1164: Sonnet missed one test, with no stronger agent left the Goal blocked on a one-line fix.
    store, control, goals, goal = _launched(monkeypatch, role="complex")
    first = _link(control, goal.id, "T001")["task_id"]
    _fail(store, first, classification="deterministic_validation_failure")
    [retry] = goals.escalate_failed_tasks(goal.id)
    assert (retry["from_role"], retry["to_role"], retry["step"]) == ("complex", "complex", 1)
    assert retry["reason"] == "failed:deterministic_validation_failure"
    again = store.get_task(retry["to_task_id"])
    assert (again.executor_kind, again.binding_ref, again.status) == ("claude_code", "strong", "QUEUED")

    _fail(store, again.id, classification="deterministic_validation_failure")
    assert goals.escalate_failed_tasks(goal.id) == ()  # only one same-agent retry
    control.refresh_goal_status(goal.id)
    assert control.get_goal(goal.id).status == "BLOCKED"


def test_other_failures_at_the_top_still_block(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch, role="complex")
    _fail(store, _link(control, goal.id, "T001")["task_id"], classification="timeout")
    assert goals.escalate_failed_tasks(goal.id) == ()


@pytest.mark.parametrize("status", ["BLOCKED", "CANCELLED"])
def test_blocked_and_cancelled_tasks_never_escalate(monkeypatch, status):
    store, control, goals, goal = _launched(monkeypatch)
    _fail(store, _link(control, goal.id, "T001")["task_id"], status=status, classification="policy_denied")
    assert goals.escalate_failed_tasks(goal.id) == ()


def test_escalation_skips_a_role_mapped_to_the_same_agent(monkeypatch):
    roster = {"simple": ("opencode", "cheap"), "coder": ("opencode", "cheap"), "complex": ("claude_code", "strong")}
    store, control, goals, goal = _launched(monkeypatch, roster=roster)
    _fail(store, _link(control, goal.id, "T001")["task_id"])
    [step] = goals.escalate_failed_tasks(goal.id)
    assert step["to_role"] == "complex" and store.get_task(step["to_task_id"]).binding_ref == "strong"


def test_no_escalation_without_a_stronger_agent_or_outside_team_mode(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch, roster={"simple": ("opencode", "cheap"),
                                                                  "complex": ("opencode", "cheap")})
    _fail(store, _link(control, goal.id, "T001")["task_id"])
    assert goals.escalate_failed_tasks(goal.id) == ()
    plain = GoalService(store=store, control_store=control)  # no roster: never escalates
    assert plain.escalate_failed_tasks(goal.id) == ()


def test_coordinator_runs_the_escalator_after_refreshing_goals(monkeypatch):
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    store, control, goals, goal = _launched(monkeypatch)
    calls = []
    coordinator = UnattendedCoordinator(store=store, control_store=control,
                                        autonomy=AutonomyService(control_store=control, capabilities=CapabilityRegistry()),
                                        router=ExecutorRouter(), workspace_root=".", goal_escalator=calls.append)
    coordinator._refresh_claimed_goals((_link(control, goal.id, "T001")["task_id"],))
    assert calls == [goal.id]

    def broken(goal_id):
        raise RuntimeError("boom")
    coordinator.goal_escalator = broken
    coordinator._refresh_claimed_goals((_link(control, goal.id, "T001")["task_id"],))
    assert coordinator._last_error == "goal_escalation_failed:RuntimeError"
    coordinator.goal_escalator = calls.append
    coordinator._refresh_claimed_goals((_link(control, goal.id, "T001")["task_id"],))
    assert coordinator._last_error == ""  # a later clean refresh reports its own outcome


def test_escalated_task_keeps_the_launch_base_when_head_moves(monkeypatch):
    from reverse_agent.platform_v1.functional_validation import load_contract
    checks = [{"profile_id": "python_pytest", "working_directory": "."}]
    store, control, goals, goal = _launched(monkeypatch, checks=checks,
                                            roster={"simple": ("opencode", "cheap"), "coder": ("codex", "mid")})
    first = store.get_task(_link(control, goal.id, "T001")["task_id"])
    assert load_contract(first)["base_commit"] == BASE
    monkeypatch.setattr(goal_service_module, "repository_base", lambda repository: "c" * 40)  # HEAD moved
    _fail(store, first.id)
    [step] = goals.escalate_failed_tasks(goal.id)
    second = store.get_task(step["to_task_id"])
    assert second.branch == BASE and load_contract(second)["base_commit"] == BASE
    assert goals.escalate_failed_tasks(goal.id) == ()  # a re-run never conflicts with the frozen contract


@pytest.mark.parametrize("classification", ["auth_provider_route_failure", "cli_unavailable",
                                            "functional_contract_conflict", "budget_exhausted",
                                            "network_provider_failure", "workspace_missing",
                                            "claude_code_turn_failed:api_error_429", "claude_code_turn_failed:api_error"])
def test_infrastructure_failures_never_escalate(monkeypatch, classification):
    store, control, goals, goal = _launched(monkeypatch)
    _fail(store, _link(control, goal.id, "T001")["task_id"], classification=classification)
    assert goals.escalate_failed_tasks(goal.id) == ()


def test_escalations_spend_the_window_retry_budget(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch, max_retries=0)
    _fail(store, _link(control, goal.id, "T001")["task_id"])
    assert goals.escalate_failed_tasks(goal.id) == ()

    store, control, goals, goal = _launched(monkeypatch, max_retries=1)
    _fail(store, _link(control, goal.id, "T001")["task_id"])
    [step] = goals.escalate_failed_tasks(goal.id)
    _fail(store, step["to_task_id"])
    assert goals.escalate_failed_tasks(goal.id) == ()


def test_a_claim_still_in_recovery_does_not_escalate(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    _fail(store, _link(control, goal.id, "T001")["task_id"])
    monkeypatch.setattr(control, "can_complete_host_claim", lambda **kwargs: True)
    assert goals.escalate_failed_tasks(goal.id) == ()
