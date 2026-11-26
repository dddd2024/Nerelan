from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.goal_source_issue import GoalSourceIssues, source_issue
from reverse_agent.platform_v1 import artifact_handoff
from reverse_agent.platform_v1.publication_controller import CommandResult, PublicationController
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from test_chaos_liveness import BY_NAME, _finish, bed

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


@pytest.mark.parametrize("already_stopped", [False, True])
def test_closed_source_does_not_starve_later_ready_goals(bed, monkeypatch, tmp_path, already_stopped):
    closed = _plan(bed)
    bed.goals.launch(closed.id, expected_revision=1, window_id=bed.window.id)
    open_id = bed.add_goal("later", [], steps=1)
    for goal_id in (closed.id, open_id):
        [link] = bed.control.list_goal_tasks(goal_id)
        _finish(bed.store, bed.store.get_task(link["task_id"]), "READY_FOR_REVIEW", "")
    bed.store._conn.commit()
    bed.goals.source_issues = GoalSourceIssues(lambda *_: _issue("CLOSED"))
    if already_stopped:
        assert bed.goals.stop_if_source_closed(closed.id)
    monkeypatch.setattr(artifact_handoff, "_load_evidence", lambda *args: {"retained": True})
    passed = []

    def publish_and_review(task_id, **_):
        goal_id = bed.control.goal_id_for_task(task_id)
        if bed.goals.stop_if_source_closed(goal_id):
            raise TaskStoreError("goal_source_issue_closed")
        passed.append(goal_id)

    coordinator = UnattendedCoordinator(
        store=bed.store, control_store=bed.control, autonomy=bed.autonomy, router=ExecutorRouter(),
        workspace_root=str(tmp_path), goals=bed.goals, publication=object(),
        landing_loop=SimpleNamespace(publish_and_review=publish_and_review),
    )
    coordinator._advance_landing(bed.window)
    assert passed == [open_id]
    assert bed.control.get_goal(closed.id).status == "SUPERSEDED"


def test_reconcile_closed_source_goals_covers_planned_and_inactive_windows_while_protecting_merged_goals(bed, tmp_path):
    def _plan_num(number):
        url = f"https://github.com/{REPOSITORY}/issues/{number}"
        objective = f"Resolve {url}\n\n# Billing refusal {number}"
        dig = hashlib.sha256(objective.encode()).hexdigest()[:16]
        goal = bed.goals.create({
            "objective": objective, "repository": REPOSITORY, "executor_kind": "opencode",
            "orchestration_mode": "agent_team",
            "idempotency_key": f"quick-start:{REPOSITORY}:issue-{number}:{dig}:1",
        })
        bed.goals.plan(goal.id, expected_revision=1, tasks=[
            {"id": "T001", "title": "Implement", "instruction": "Fix the issue", "agent_role": "coder"},
        ])
        return bed.goals.approve(goal.id, expected_revision=1)

    from datetime import datetime, timedelta, timezone

    planned = _plan_num(1525)  # PLANNED with empty window_id
    inactive_running = _plan_num(1526)
    bed.goals.launch(inactive_running.id, expected_revision=1, window_id=bed.window.id)
    merged_goal = _plan_num(1527)
    bed.goals.launch(merged_goal.id, expected_revision=1, window_id=bed.window.id)
    bed.control.stop_window(bed.window.id)
    now = datetime.now(timezone.utc)
    owner_win = bed.autonomy.activate({
        "policy_id": "owner-landing", "policy_revision": 1, "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": [REPOSITORY], "capabilities": ["land_reviewed_pr"], "confirmation": "ACTIVATE",
    })
    landing = bed.control.ensure_landing(
        repository=REPOSITORY, goal_id=merged_goal.id, pr_number=1999, head_sha="a" * 40, review_round=1,
    )
    claim_id = bed.control.claim_landing_operation(landing["identity"], "merge", window_id=owner_win.id)
    bed.control.record_landing_outcome(landing["identity"], "merge", claim_id, outcome="SUCCEEDED", evidence={"merge_commit": "b" * 40})
    bed.control.finish_landing_tick(landing["identity"], "COMPLETE", "", 0, lease=0)
    [merged_link] = bed.control.list_goal_tasks(merged_goal.id)
    _finish(bed.store, bed.store.get_task(merged_link["task_id"]), "READY_FOR_REVIEW", "")
    bed.store._conn.commit()
    bed.control.complete_merged_goal(merged_goal.id)
    bed.control.stop_window(owner_win.id)

    bed.goals.source_issues = GoalSourceIssues(lambda repo, num: {"number": num, "url": f"https://github.com/{repo}/issues/{num}", "state": "CLOSED"})
    coordinator = UnattendedCoordinator(
        store=bed.store, control_store=bed.control, autonomy=bed.autonomy,
        router=ExecutorRouter(), workspace_root=str(tmp_path), goals=bed.goals,
    )
    summary = coordinator.reconcile()
    assert f"closed_source_goal:{planned.id}" in summary
    assert f"closed_source_goal:{inactive_running.id}" in summary
    assert bed.control.get_goal(planned.id).status == "SUPERSEDED"
    assert bed.control.get_goal(inactive_running.id).status == "SUPERSEDED"
    assert len(bed.control.list_goal_tasks(inactive_running.id)) == 1
    assert bed.control.get_goal(merged_goal.id).status == "COMPLETED"
