from __future__ import annotations

from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.attention import (
    AttentionKind,
    AttentionReadModel,
    AttentionReadModelError,
    AttentionSeverity,
)
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore


class FakeControlStore:
    def __init__(self, goals=()):
        self.goals = list(goals)

    def list_goals(self, *, limit=100):
        return tuple(self.goals[:limit])


class FakeRunReadModel:
    def __init__(self, runs=()):
        self.runs = list(runs)
        self.requested_limits = []

    def list_runs(self, *, limit=100, cursor=None):
        self.requested_limits.append(limit)
        return {
            "runs": self.runs[:limit],
            "total": len(self.runs),
            "next_cursor": None,
        }


def goal(*, status="PLANNED", revision=1, goal_id="goal-1", title="Goal", updated_at="2026-09-12T08:00:00Z"):
    return SimpleNamespace(
        id=goal_id,
        title=title,
        status=status,
        revision=revision,
        updated_at=updated_at,
    )


def run(
    *,
    task_id="task-1",
    goal_id="goal-1",
    title="Run",
    status="RUNNING",
    liveness="ACTIVE",
    updated_at="2026-09-12T08:00:00Z",
    run_id="run-1",
    validation=None,
    publication=None,
):
    return {
        "task_id": task_id,
        "goal_id": goal_id,
        "title": title,
        "status": status,
        "liveness": liveness,
        "updated_at": updated_at,
        "run_id": run_id,
        "validation": validation,
        "publication": publication,
    }


def model(*, goals=(), runs=()):
    fake_runs = FakeRunReadModel(runs)
    return (
        AttentionReadModel(
            store=object(),
            control_store=FakeControlStore(goals),
            run_read_model=fake_runs,
        ),
        fake_runs,
    )


def test_planned_goal_emits_approval_and_stable_identity():
    read_model, _ = model(goals=[goal()])
    first = read_model.list_items()
    second = read_model.list_items()
    assert len(first) == 1
    item = first[0]
    assert item.kind is AttentionKind.APPROVAL_REQUIRED
    assert item.severity is AttentionSeverity.MEDIUM
    assert item.deep_link == "/approvals?goal=goal-1"
    assert item.attention_id == second[0].attention_id


@pytest.mark.parametrize("status", ["DRAFT", "APPROVED", "RUNNING", "COMPLETED", "INVALIDATED"])
def test_non_actionable_goal_states_are_not_attention(status):
    read_model, _ = model(goals=[goal(status=status)])
    assert read_model.list_items() == ()


def test_goal_revision_changes_attention_generation():
    first, _ = model(goals=[goal(revision=1)])
    second, _ = model(goals=[goal(revision=2)])
    assert first.list_items()[0].attention_id != second.list_items()[0].attention_id


@pytest.mark.parametrize(
    ("status", "expected_kind"),
    [
        ("FAILED", AttentionKind.RUN_FAILED),
        ("BLOCKED", AttentionKind.RUN_BLOCKED),
        ("INTERRUPTED", AttentionKind.RECOVERY_REQUIRED),
    ],
)
def test_terminal_or_interrupted_run_attention(status, expected_kind):
    read_model, _ = model(runs=[run(status=status, liveness="TERMINAL")])
    item = read_model.list_items()[0]
    assert item.kind is expected_kind
    assert item.severity is AttentionSeverity.HIGH


def test_active_stale_run_is_attention_but_healthy_active_run_is_not():
    stale, _ = model(runs=[run(status="RUNNING", liveness="STALE")])
    healthy, _ = model(runs=[run(status="RUNNING", liveness="ACTIVE")])
    assert stale.list_items()[0].kind is AttentionKind.RUN_STALLED
    assert healthy.list_items() == ()


@pytest.mark.parametrize("validation_status", ["FAILURE", "UNVERIFIED"])
def test_verification_failure_is_attention(validation_status):
    read_model, _ = model(
        runs=[
            run(
                status="VALIDATING",
                liveness="ACTIVE",
                validation={
                    "command_id": "approved_functional_checks",
                    "status": validation_status,
                    "exit_code": 1,
                },
            )
        ]
    )
    item = read_model.list_items()[0]
    assert item.kind is AttentionKind.VERIFICATION_FAILED
    assert item.severity is AttentionSeverity.HIGH


def test_publication_failure_has_highest_run_precedence():
    read_model, _ = model(
        runs=[
            run(
                status="FAILED",
                liveness="TERMINAL",
                validation={"status": "FAILURE", "command_id": "git_diff_check", "exit_code": 1},
                publication={"status": "FAILED", "pr_number": 0, "pr_url": "", "commit_sha": ""},
            )
        ]
    )
    items = read_model.list_items()
    assert len(items) == 1
    assert items[0].kind is AttentionKind.PUBLICATION_FAILED


def test_complete_publication_is_draft_pr_ready_and_safe_url_is_exposed():
    read_model, _ = model(
        runs=[
            run(
                status="READY_FOR_REVIEW",
                liveness="TERMINAL",
                publication={
                    "status": "COMPLETE",
                    "pr_number": 123,
                    "pr_url": "https://github.com/owner/repo/pull/123",
                    "commit_sha": "a" * 40,
                },
            )
        ]
    )
    item = read_model.list_items()[0]
    assert item.kind is AttentionKind.DRAFT_PR_READY
    assert item.external_url == "https://github.com/owner/repo/pull/123"


@pytest.mark.parametrize(
    "unsafe_url",
    [
        "http://github.com/owner/repo/pull/123",
        "https://user:pass@github.com/owner/repo/pull/123",
        "https://evil.example/owner/repo/pull/123",
        "https://github.com/owner/repo/pull/123?token=secret",
    ],
)
def test_unsafe_publication_url_is_never_exposed(unsafe_url):
    read_model, _ = model(
        runs=[
            run(
                status="READY_FOR_REVIEW",
                liveness="TERMINAL",
                publication={
                    "status": "COMPLETE",
                    "pr_number": 123,
                    "pr_url": unsafe_url,
                    "commit_sha": "a" * 40,
                },
            )
        ]
    )
    item = read_model.list_items()[0]
    assert item.kind is AttentionKind.DRAFT_PR_READY
    assert item.external_url == ""


@pytest.mark.parametrize("status", ["READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"])
def test_ready_for_review_falls_back_to_review_attention(status):
    read_model, _ = model(runs=[run(status=status, liveness="TERMINAL")])
    item = read_model.list_items()[0]
    assert item.kind is AttentionKind.REVIEW_REQUIRED
    assert item.severity is AttentionSeverity.MEDIUM


def test_one_run_emits_only_highest_precedence_item():
    read_model, _ = model(
        runs=[
            run(
                status="FAILED",
                liveness="STALE",
                validation={"status": "FAILURE", "command_id": "git_diff_check", "exit_code": 1},
                publication={"status": "COMPLETE", "pr_number": 123, "pr_url": "", "commit_sha": "b" * 40},
            )
        ]
    )
    items = read_model.list_items()
    assert len(items) == 1
    assert items[0].kind is AttentionKind.RUN_FAILED


def test_high_sort_precedes_medium_then_newest_with_stable_tie_break():
    read_model, _ = model(
        goals=[goal(updated_at="2026-09-12T09:00:00Z")],
        runs=[
            run(task_id="task-old", status="FAILED", updated_at="2026-09-12T07:00:00Z"),
            run(task_id="task-new", status="BLOCKED", updated_at="2026-09-12T08:00:00Z"),
            run(task_id="task-review", status="READY_FOR_REVIEW", updated_at="2026-09-12T10:00:00Z"),
        ],
    )
    items = read_model.list_items()
    assert [item.task_id for item in items[:2]] == ["task-new", "task-old"]
    assert all(item.severity is AttentionSeverity.HIGH for item in items[:2])
    assert all(item.severity is AttentionSeverity.MEDIUM for item in items[2:])


@pytest.mark.parametrize("limit", [0, -1, 101, True, "10"])
def test_invalid_limit_fails_closed(limit):
    read_model, _ = model()
    with pytest.raises(AttentionReadModelError, match="invalid_attention_limit"):
        read_model.list_items(limit=limit)


def test_source_reads_stay_bounded():
    read_model, fake_runs = model(
        goals=[goal(goal_id=f"goal-{index}") for index in range(150)],
        runs=[run(task_id=f"task-{index}") for index in range(150)],
    )
    read_model.list_items(limit=100)
    assert fake_runs.requested_limits == [100]


def test_sensitive_goal_title_and_run_fields_never_leak():
    sensitive = "Authorization Bearer sk-abcdefghijklmnop"
    read_model, _ = model(
        goals=[goal(title=sensitive)],
        runs=[
            run(
                task_id="task-secret",
                title=sensitive,
                status="FAILED",
            )
        ],
    )
    rendered = repr([item.to_dict() for item in read_model.list_items()])
    assert "sk-abcdefghijklmnop" not in rendered
    assert "Authorization" not in rendered
    assert "Goal needs approval" in rendered
    assert "Run needs attention" in rendered


def test_projection_does_not_copy_untrusted_run_fields():
    data = run(status="FAILED")
    data.update(
        {
            "failure_detail": "password=super-secret",
            "events": [{"raw_log": "api_key=leak"}],
            "current_activity": {"description": "prompt secret"},
            "workspace": "/private/worktree",
        }
    )
    read_model, _ = model(runs=[data])
    rendered = repr(read_model.list_items()[0].to_dict())
    for forbidden in ("super-secret", "api_key=leak", "prompt secret", "/private/worktree"):
        assert forbidden not in rendered


def test_real_store_projection_is_read_only_and_uses_existing_truth():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    task = store.create_task(title="Needs attention", repository="owner/repo")
    store.set_state(task.id, "FAILED")
    before = store._conn.total_changes

    read_model = AttentionReadModel(store=store, control_store=control)
    items = read_model.list_items()

    assert store._conn.total_changes == before
    assert len(items) == 1
    assert items[0].kind is AttentionKind.RUN_FAILED
    assert items[0].task_id == task.id


def test_real_planned_goal_projection_is_read_only():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    created = control.create_goal(
        title="Plan review",
        objective="objective-with-private-detail",
        repository="owner/repo",
        idempotency_key="attention-goal",
    )
    planned = control.save_goal_plan(
        created.id,
        expected_revision=created.revision,
        spec_markdown="spec",
        plan_markdown="plan",
        tasks=[{"id": "task-1", "title": "Do work", "dependencies": []}],
        acceptance_criteria=["passes"],
    )
    assert planned.status == "PLANNED"
    before = store._conn.total_changes

    read_model = AttentionReadModel(store=store, control_store=control)
    items = read_model.list_items()

    assert store._conn.total_changes == before
    assert len(items) == 1
    assert items[0].kind is AttentionKind.APPROVAL_REQUIRED
    assert "objective-with-private-detail" not in repr(items[0].to_dict())
