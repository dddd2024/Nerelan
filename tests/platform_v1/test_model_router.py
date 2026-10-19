"""Provider-free per-task router and trusted-host integration tests."""
from types import SimpleNamespace
import json

import pytest

from reverse_agent.platform_v1.agent_planner import extract_plan
from reverse_agent.platform_v1.goal_service import GoalService, PlannedTask
from reverse_agent.platform_v1.model_router import capability, prior_tier, select_model
from reverse_agent.platform_v1.model_profiles import compute_agent_profiles
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


def candidate(ref, model, cost="free", executor="opencode", **extra):
    return dict(binding_id=ref, model_id=model, cost_class=cost, executor_id=executor,
                enabled=True, **extra)


def choose(candidates, **kwargs):
    return select_model(candidates, difficulty=kwargs.pop("difficulty", 2),
                        kind=kwargs.pop("kind", "code"), **kwargs)


@pytest.mark.parametrize("model,tier,unproven", [
    ("gpt-6.1-sol", 5, False), ("claude-sonnet-4-6", 5, False),
    ("kimi-k3", 4, False), ("deepseek-v4-pro", 4, False),
    ("glm-5.3", 3, False), ("gemini-flash", 3, False),
    ("gemini-flash-lite", 2, False), ("new-small", 2, True),
])
def test_priors(model, tier, unproven):
    assert prior_tier(model) == (tier, unproven)


def test_measurements_override_only_with_enough_kind_and_difficulty_samples():
    bucket = {"attempts": 2, "success_rate": 1., "timeouts": 0}
    profile = {"task_buckets": {"analysis:4": bucket}}
    assert capability("unknown", profile, "analysis", 4) == (2, True)
    bucket["attempts"] = 3
    assert capability("unknown", profile, "analysis", 4) == (4, False)
    assert capability("unknown", profile, "code", 4) == (2, True)
    bucket.update(success_rate=.9, timeouts=2)
    assert capability("gpt-6-sol", profile, "analysis", 4) == (3, False)


def test_cheapest_qualifying_and_underpowered():
    pool = [candidate("small", "flash-lite"), candidate("large", "opus", "subscription"),
            candidate("api", "gpt-6-sol", "paid_api")]
    assert choose(pool)["binding_ref"] == "small"
    assert choose(pool, difficulty=4)["binding_ref"] == "large"
    result = choose(pool[:1], difficulty=5)
    assert result["reason"] == "underpowered" and result["underpowered"]
    json.dumps(result, allow_nan=False)


def test_success_then_speed_break_ties_and_quota_headroom_scales_cost():
    pool = [candidate("a", "opus", "subscription"), candidate("b", "sonnet", "subscription")]
    profiles = {"a": {"success_rate": .8, "median_ok_seconds": 10},
                "b": {"success_rate": .9, "median_ok_seconds": 50}}
    assert choose(pool, profiles=profiles)["binding_ref"] == "b"
    profiles["a"]["success_rate"] = .9
    assert choose(pool, profiles=profiles)["binding_ref"] == "a"
    pool[0]["quota_headroom"] = .2
    assert choose(pool, profiles=profiles)["binding_ref"] == "b"


def test_exploration_budget_is_injected_and_bounded_to_easy_tasks():
    pool = [candidate("known", "flash-lite"), candidate("new", "unknown")]
    assert choose(pool, exploration_draw=.05)["reason"] == "exploration"
    assert choose(pool, exploration_draw=.1)["reason"] != "exploration"
    assert choose(pool, exploration_draw=0, exploration_budget=0)["reason"] != "exploration"
    assert choose(pool, difficulty=3, exploration_draw=0)["reason"] != "exploration"


@pytest.mark.parametrize("decision", ["switch", "warn"])
def test_quota_short_candidates_are_skipped_even_for_pins(decision):
    pool = [candidate("a", "flash-lite", quota={"decision": decision}), candidate("b", "opus")]
    assert choose(pool)["binding_ref"] == "b"
    with pytest.raises(ValueError, match="pinned_model_unavailable"):
        choose(pool, pin="a")


def test_fitness_review_model_identity_and_pin_precedence():
    pool = [candidate("a", "opus"), candidate("sibling", "opus", executor="codex"),
            candidate("b", "sonnet", "paid_api", "claude_code")]
    assert choose(pool, kind="review", author_model="opus")["binding_ref"] == "b"
    assert choose(pool, role="planner")["binding_ref"] == "sibling"
    assert choose(pool, pin="b")["reason"] == "pin"
    assert choose(pool, pin="b")["binding_ref"] == "b"
    pool[0]["runnable"] = False
    pool[1]["enabled"] = False
    assert choose(pool)["binding_ref"] == "b"


def test_escalation_prefers_higher_then_distinct_same_tier_model():
    pool = [candidate("a", "flash-lite"), candidate("sibling", "flash-lite"),
            candidate("b", "glm-5.3"), candidate("c", "opus", "paid_api")]
    result = choose(pool, failed_model="flash-lite", failed_tier=2)
    assert result["binding_ref"] == "b"
    assert choose(pool, failed_model="opus", failed_tier=5)["binding_ref"] != "c"
    same = [candidate("a", "opus"), candidate("b", "sonnet")]
    assert choose(same, failed_model="opus", failed_tier=5)["binding_ref"] == "b"
    assert choose(same[:1], failed_model="opus", failed_tier=5)["binding_ref"] == "a"


@pytest.mark.parametrize("field,value", [("difficulty", True), ("difficulty", 0), ("difficulty", 6),
                                        ("difficulty", "2"), ("difficulty", 2.5),
                                        ("kind", "coding"), ("kind", None)])
def test_planner_and_saved_plans_strictly_validate(field, value):
    task = {"id": "T001", "title": "t", "instruction": "i", field: value}
    with pytest.raises(TaskStoreError, match="invalid_task_"):
        extract_plan(json.dumps({"tasks": [task]}))
    with pytest.raises(TaskStoreError, match="invalid_task_"):
        GoalService._normalize_task(task, seq=0)


@pytest.mark.parametrize("role,difficulty", [("simple", 2), ("coder", 3), ("complex", 4)])
def test_legacy_roles_map_to_difficulty(role, difficulty):
    task = {"id": "T001", "title": "t", "instruction": "i", "agent_role": role}
    assert extract_plan(json.dumps({"tasks": [task]}))["tasks"][0]["difficulty"] == difficulty
    assert GoalService._normalize_task(task, seq=0).difficulty == difficulty


def fixture_host(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _models
    monkeypatch.setattr("random.random", lambda: 1.)
    host = object.__new__(CombinedTrustedHost)
    host._store = _models(tmp_path)
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "mid", "strong"})
    monkeypatch.setattr(host, "_quota_check", lambda binding: None)
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {})
    monkeypatch.setattr(host, "_usage_profiles", lambda: {})
    return host


def test_host_routes_goal_tasks_records_events_and_learns_outcomes(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    host = fixture_host(monkeypatch, tmp_path)
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({"objective": "Route by task difficulty", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "router", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team"})
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "Small", "instruction": "Edit", "difficulty": 2, "kind": "code"},
        {"id": "T002", "title": "Hard", "instruction": "Design", "difficulty": 4, "kind": "analysis"}])
    goals.approve(goal.id, expected_revision=1)
    window = autonomy.activate(_window_payload(goal.repository))
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    tasks = [store.get_task(link["task_id"]) for link in control.list_goal_tasks(goal.id)]
    assert [task.binding_ref for task in tasks] == ["cheap", "strong"]
    for task, difficulty in zip(tasks, (2, 4)):
        [event] = [e for e in store.get_events(task.id) if e.type == "MODEL_SELECTED"]
        assert event.metadata["difficulty"] == difficulty
        assert event.metadata["binding_ref"] == task.binding_ref
        assert event.metadata["candidates"]
    from reverse_agent.platform_v1.run_read_model import RunReadModel
    detail = RunReadModel(store=store, control_store=control).run_detail(tasks[0].id)
    [selected] = [event for event in detail["events"] if event["type"] == "MODEL_SELECTED"]
    assert selected["title"] == "Model selected" and "difficulty 2" in selected["description"]
    assert "cheap" in selected["description"] and "cost 0" in selected["description"]
    # Retry takes a higher tier from the full catalog, without a role roster.
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='timeout' WHERE id=?", (tasks[0].id,))
    store._conn.commit()
    [retry] = goals.escalate_failed_tasks(goal.id)
    retried = store.get_task(retry["to_task_id"])
    assert retried.binding_ref == "strong"
    assert any(e.type == "MODEL_SELECTED" for e in store.get_events(retried.id))
    profile = compute_agent_profiles(store)["cheap"]["task_buckets"]["code:2"]
    assert profile["attempts"] == 1 and profile["timeouts"] == 1 and profile["success_rate"] == 0
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert len([e for e in store.get_events(tasks[1].id) if e.type == "MODEL_SELECTED"]) == 1


def test_host_goal_pin_and_roster_pin_and_optional_planner(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    task = PlannedTask("T001", "t", "i", difficulty=2)
    assert host._resolve_task_model(task, goal=SimpleNamespace(binding_ref="strong"))["binding_ref"] == "strong"
    host._store.put_agent_roster({"roles": {"coder": {"binding_id": "strong", "pin": True}}})
    task = PlannedTask("T001", "t", "i", agent_role="coder", difficulty=2)
    assert host._resolve_task_model(task)["reason"] == "pin"
    assert host._resolve_agent_role("planner") == ("claude_code", "strong")
    from reverse_agent.model_access.store import ModelProfileStore
    reloaded = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    assert reloaded.get_agent_roster_public()["roles"]["coder"]["pin"] is True


def test_review_resolves_author_before_selection_even_in_reordered_plan(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    host = fixture_host(monkeypatch, tmp_path)
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({"objective": "Review an artifact", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "review-router", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team"})
    checks = [{"profile_id": "python_pytest", "working_directory": "."}]
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T002", "title": "Review", "instruction": "Review", "difficulty": 2, "kind": "review",
         "dependencies": ["T001"], "artifact_input": {"plan_task_id": "T001"}, "validation_checks": checks},
        {"id": "T001", "title": "Edit", "instruction": "Edit", "difficulty": 2, "kind": "code",
         "validation_checks": checks}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate(_window_payload(goal.repository)).id)
    tasks = {link["plan_task_id"]: store.get_task(link["task_id"]) for link in control.list_goal_tasks(goal.id)}
    assert tasks["T001"].binding_ref == "cheap"
    author_model = host._store.get_binding_public(tasks["T001"].binding_ref)["model_id"]
    reviewer_model = host._store.get_binding_public(tasks["T002"].binding_ref)["model_id"]
    assert reviewer_model != author_model
    assert control.get_goal(goal.id).tasks[0]["capability"] == "validate_task"
    with pytest.raises(TaskStoreError, match="review_author_binding_required"):
        host._resolve_task_model(PlannedTask("review", "review", "review", kind="review"))


def test_host_quota_skip_uses_other_qualifying_catalog_binding(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    host._store.upsert_binding({"binding_id": "magpie-new", "name": "New discovered model", "executor_id": "opencode",
                                "connection_id": "free-api", "model_id": "deepseek-v4-pro", "enabled": True})
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "strong", "magpie-new"})
    monkeypatch.setattr(host, "_quota_check", lambda b: {"decision": "switch", "reason": "observed_exhausted"}
                        if b["binding_id"] == "strong" else None)
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=4))
    assert result["binding_ref"] == "magpie-new" and not result["underpowered"]
    host._store.put_agent_roster({"roles": {"complex": {"binding_id": "cheap", "pin": True}}})
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=4))
    assert result["binding_ref"] == "cheap" and result["underpowered"] and result["reason"] == "pin"
    host._store.put_agent_roster({"roles": {"complex": {"binding_id": "cheap", "pin": False}}})
    assert host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=4))["binding_ref"] == "magpie-new"


def test_provider_aliases_cannot_evade_review_or_retry_model_identity():
    pool = [candidate("a", "opus"), candidate("same", "anthropic/opus:free"),
            candidate("other", "sonnet", "paid_api")]
    assert choose(pool, kind="review", author_model="opus")["binding_ref"] == "other"
    assert choose(pool, failed_model="opus", failed_tier=5)["binding_ref"] == "other"


def test_unknown_quota_observations_do_not_block_routing(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    def unavailable():
        raise OSError("fixture observation unavailable")
    monkeypatch.setattr(host, "_subscription_quotas", unavailable)
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=4))
    assert result["binding_ref"] == "strong"


def test_retry_compares_against_recorded_tier_before_new_failure_evidence(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.setattr(host, "_usage_profiles", lambda: {
        "cheap": {"task_buckets": {"code:2": {"attempts": 3, "success_rate": 0, "timeouts": 3}}}})
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=2),
                                      failed_binding="cheap", failed_tier=2)
    assert result["binding_ref"] == "strong" and result["tier"] > 2


@pytest.mark.parametrize("difficulty,role,binding", [(2, "simple", "strong"), (4, "complex", "cheap")])
def test_difficulty_only_plans_honor_corresponding_legacy_role_pins(monkeypatch, tmp_path, difficulty, role, binding):
    host = fixture_host(monkeypatch, tmp_path)
    host._store.put_agent_roster({"roles": {role: {"binding_id": binding, "pin": True}}})
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=difficulty))
    assert result["binding_ref"] == binding and result["reason"] == "pin"
