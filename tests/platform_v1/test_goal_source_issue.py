from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess

import pytest

from reverse_agent.platform_v1.goal_source_issue import GoalSourceIssues, source_issue
from reverse_agent.platform_v1.publication_controller import CommandResult, PublicationController
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from test_chaos_liveness import BY_NAME, bed

REPOSITORY = "dddd2024/Nerelan"
NUMBER = 1525
URL = f"https://github.com/{REPOSITORY}/issues/{NUMBER}"


def _plan(bed):
    objective = f"Resolve {URL}\n\n# Billing refusal"
    digest = hashlib.sha256(objective.encode()).hexdigest()[:16]
    goal = bed.goals.create({
        "objective": objective, "repository": REPOSITORY, "executor_kind": "opencode",
        "orchestration_mode": "agent_team",
        "idempotency_key": f"quick-start:{REPOSITORY}:issue-{NUMBER}:{digest}:1",
    })
    bed.goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "Implement", "instruction": "Fix the issue", "agent_role": "coder"},
    ])
    return bed.goals.approve(goal.id, expected_revision=1)


def _issue(state):
    return {"number": NUMBER, "url": URL, "state": state}


def test_source_uses_legacy_quick_start_identity_and_bound_objective(bed):
    goal = _plan(bed)
    assert source_issue(goal) == NUMBER
    assert source_issue(replace(goal, idempotency_key="plain-text")) is None
    assert source_issue(replace(goal, objective=f"Mention {URL} as context")) is None
    assert source_issue(replace(goal, objective=goal.objective + "\nDifferent request")) is None
    assert source_issue(replace(goal, repository="another/repo")) is None


def test_uncertain_or_wrong_issue_read_never_stops(bed):
    goal = _plan(bed)

    def timeout(*_):
        raise subprocess.TimeoutExpired("gh", 5)

    assert not GoalSourceIssues(timeout).closed(goal)
    assert not GoalSourceIssues(lambda *_: {**_issue("CLOSED"), "url": URL.replace("Nerelan", "Other")}).closed(goal)
    assert not GoalSourceIssues(lambda *_: {**_issue("CLOSED"), "number": 99}).closed(goal)


def test_closed_issue_is_terminal_before_launch(bed):
    goal = _plan(bed)
    bed.goals.source_issues = GoalSourceIssues(lambda *_: _issue("CLOSED"))
    with pytest.raises(TaskStoreError, match="goal_source_issue_closed"):
        bed.goals.launch(goal.id, expected_revision=1, window_id=bed.window.id)
    assert bed.control.refresh_goal_status(goal.id).status == "SUPERSEDED"
    assert bed.control.list_goal_tasks(goal.id) == ()
    assert bed.goals.timeline_snapshot(goal.id)["stop_reason"] == "source_issue_closed"


def test_cache_and_fresh_check_stop_retry_and_claim_without_losing_history(bed):
    goal = _plan(bed)
    reads = []

    def read(repository, number):
        reads.append((repository, number))
        return _issue("OPEN" if len(reads) == 1 else "CLOSED")

    bed.goals.source_issues = GoalSourceIssues(read)
    bed.goals.launch(goal.id, expected_revision=1, window_id=bed.window.id)
    [task_id] = bed.control.runnable_tasks(bed.window.id)
    assert not bed.goals.stop_if_source_closed(goal.id)
    assert len(reads) == 1
    assert bed.goals.stop_if_source_closed(goal.id, fresh=True)
    assert bed.goals.escalate_failed_tasks(goal.id) == ()
    assert bed.control.refresh_goal_status(goal.id).status == "SUPERSEDED"
    assert bed.control.runnable_tasks(bed.window.id) == ()
    with pytest.raises(TaskStoreError, match="goal_source_issue_closed"):
        bed.control.claim_task(window_id=bed.window.id, task_id=task_id, owner="fixture", lease_ms=10000)
    assert bed.store.get_task(task_id).status == "QUEUED"
    assert reads == [(REPOSITORY, NUMBER)] * 2


def test_pr_create_checks_source_after_looking_for_existing_draft(bed):
    goal = _plan(bed)
    states = iter(["OPEN", "CLOSED"])
    bed.goals.source_issues = GoalSourceIssues(lambda *_: _issue(next(states)))
    commands = []

    def run(args, _):
        commands.append(tuple(args))
        return CommandResult(0, "[]")

    publication = PublicationController(store=bed.store, control_store=bed.control, autonomy=bed.autonomy,
                                        runner=run, source_issue_closed=bed.goals.stop_if_source_closed)
    publication._require_open_source(goal.id)
    with pytest.raises(TaskStoreError, match="goal_source_issue_closed"):
        publication._find_or_create_draft_pr(
            workspace=Path.cwd(), repository=REPOSITORY, branch="fixture", base_branch="main",
            title="Fixture", body="", before_create=lambda: publication._require_open_source(goal.id, fresh=True),
        )
    assert [args[:3] for args in commands] == [("gh", "pr", "list")]


def test_closed_source_blocks_dispatch_in_normal_coordinator_tick(bed, tmp_path):
    goal = _plan(bed)
    bed.goals.launch(goal.id, expected_revision=1, window_id=bed.window.id)
    bed.goals.source_issues = GoalSourceIssues(lambda *_: _issue("CLOSED"))
    coordinator = UnattendedCoordinator(
        store=bed.store, control_store=bed.control, autonomy=bed.autonomy,
        router=ExecutorRouter(), workspace_root=str(tmp_path), goals=bed.goals,
        task_executor=lambda _: pytest.fail("superseded goal dispatched"),
    )
    assert coordinator.tick() == 0
    assert bed.control.get_goal(goal.id).status == "SUPERSEDED"


def test_escalation_observes_issue_closure_before_routing(bed):
    goal = _plan(bed)
    bed.goals.launch(goal.id, expected_revision=1, window_id=bed.window.id)
    [task_id] = bed.control.runnable_tasks(bed.window.id)
    BY_NAME["rate_limit_429"].apply(bed.store, bed.store.get_task(task_id))
    bed.store._conn.commit()
    bed.goals.source_issues = GoalSourceIssues(lambda *_: _issue("CLOSED"))
    assert bed.goals.escalate_failed_tasks(goal.id) == ()
    assert bed.control.get_goal(goal.id).status == "SUPERSEDED"
    assert not bed.control.list_task_escalations(goal.id)
