"""Isolated provider-free protocol tests; no production permissions."""
from dataclasses import replace
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

import pytest

from reverse_agent.platform_v1 import owner_grant_preparer as grants
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.native_owner_dialog import confirm_scope as real_confirm


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    store = TaskStore(str(tmp_path / "fixture.sqlite"))
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "Fixture only", "repository": "owner/repo", "idempotency_key": "fixture",
                         "executor_kind": "codex", "binding_ref": "pinned",
                         "orchestration_mode": "single"})
    goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{
        "id": "ONE", "title": "Fixture", "instruction": "Read fixture"}]).goal
    monkeypatch.setattr(grants, "resolve_repository_workspace", lambda repository:
                        SimpleNamespace(repository=repository, repo_dir=tmp_path))
    seen = []
    # Platform callback exists ONLY here; no preparer API accepts one.
    original = real_confirm
    monkeypatch.setattr(grants.native_owner_dialog, "confirm_scope", lambda scope:
                        original(scope, platform_dialog=lambda text: seen.append(text) or True))
    host = grants.TestOnlyHostGrantPreparer(control, grants.FixturePolicy("owner/repo", "pinned"))
    yield host, control, goal, seen
    store._conn.close()


def test_snapshot_and_one_use(fixture):
    host, control, goal, seen = fixture
    token = host.prepare_for_test(goal.id)
    assert len(token) >= 43
    preview = host.consume_for_test(token, goal_id=goal.id)
    assert preview.snapshot_json in seen[0]
    assert '"max_minutes":30' in seen[0] and '"max_retries":0' in seen[0]
    assert '"instruction":"Read fixture"' in seen[0]
    assert control.get_goal(goal.id) == goal
    assert not control.list_goal_tasks(goal.id)
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id=goal.id)


@pytest.mark.parametrize("change", ["revision", "executor_kind", "binding_ref", "objective"])
def test_stored_mutation_burns_grant(fixture, monkeypatch, change):
    host, control, goal, _ = fixture
    token = host.prepare_for_test(goal.id)
    changed = replace(goal, **{change: goal.revision + 1 if change == "revision" else "substitution"})
    monkeypatch.setattr(control, "get_goal", lambda _: changed)
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id=goal.id)
    monkeypatch.setattr(control, "get_goal", lambda _: goal)
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id=goal.id)


def test_wrong_goal_forgery_and_other_host(fixture):
    host, control, goal, _ = fixture
    token = host.prepare_for_test(goal.id)
    other = grants.TestOnlyHostGrantPreparer(control, grants.FixturePolicy("owner/repo", "pinned"))
    with pytest.raises(ValueError):
        other.consume_for_test(token, goal_id=goal.id)
    with pytest.raises(ValueError):
        host.consume_for_test("browser-forged", goal_id=goal.id)
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id="wrong-goal")
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id=goal.id)


def test_expiry(fixture, monkeypatch):
    host, _, goal, _ = fixture
    now = [100.0]
    monkeypatch.setattr(grants.time, "monotonic", lambda: now[0])
    token = host.prepare_for_test(goal.id)
    now[0] += 30
    with pytest.raises(ValueError):
        host.consume_for_test(token, goal_id=goal.id)


@pytest.mark.parametrize("mode", ["no", "headless", "slow", "mutation"])
def test_dialog_denial_and_races(fixture, monkeypatch, mode):
    host, control, goal, _ = fixture
    now = [100.0]
    monkeypatch.setattr(grants.time, "monotonic", lambda: now[0])
    native = grants.native_owner_dialog
    def dialog(scope):
        if mode == "slow":
            now[0] += 30
        if mode == "mutation":
            monkeypatch.setattr(control, "get_goal", lambda _: replace(goal, objective="changed"))
        if mode == "headless":
            def fail(_):
                raise OSError("headless")
            return original(scope, platform_dialog=fail)
        return original(scope, platform_dialog=lambda _: mode != "no")
    original = real_confirm
    monkeypatch.setattr(native, "confirm_scope", dialog)
    if mode in {"slow", "mutation"}:
        with pytest.raises(ValueError):
            host.prepare_for_test(goal.id)
    else:
        assert host.prepare_for_test(goal.id) is None
    assert not host._pending


def test_invalid_scope_never_prompts(fixture, monkeypatch):
    host, control, goal, _ = fixture
    monkeypatch.setattr(control, "get_goal", lambda _: replace(goal, executor_kind="opencode"))
    monkeypatch.setattr(grants.native_owner_dialog, "confirm_scope", lambda _: pytest.fail("prompted"))
    with pytest.raises(ValueError):
        host.prepare_for_test(goal.id)


def test_parallel_consumption_has_one_winner(fixture, monkeypatch):
    host, control, goal, _ = fixture
    token = host.prepare_for_test(goal.id)
    # SQLite is thread-affine; use the immutable record loaded above.
    monkeypatch.setattr(control, "get_goal", lambda _: goal)
    def consume(_):
        try:
            return host.consume_for_test(token, goal_id=goal.id)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(item is not None for item in pool.map(consume, range(2))) == 1


def test_new_selection_revokes_previous(fixture):
    host, _, goal, _ = fixture
    first = host.prepare_for_test(goal.id)
    second = host.prepare_for_test(goal.id)
    with pytest.raises(ValueError):
        host.consume_for_test(first, goal_id=goal.id)
    assert host.consume_for_test(second, goal_id=goal.id)


def test_repository_failure_never_prompts(fixture, monkeypatch):
    host, _, goal, _ = fixture
    def fail(_):
        raise ValueError("unverified_repository")
    monkeypatch.setattr(grants, "resolve_repository_workspace", fail)
    monkeypatch.setattr(grants.native_owner_dialog, "confirm_scope", lambda _: pytest.fail("prompted"))
    with pytest.raises(ValueError):
        host.prepare_for_test(goal.id)
