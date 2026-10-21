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
                review_connection={"auth_method": "api_key", "relay_required": True, "native_endpoint": "/chat/completions"},
                review_lease_provider=lambda r: None, enabled=True, availability={"state": "AVAILABLE", "reason": "fixture"}, **extra)


# Explicit fixture capability judgments; production has no name-based tier prior.
FIXTURE_TIERS = {"gpt-6.1-sol": 5, "gpt-6-sol": 5, "gpt-6": 5, "claude-sonnet-4-6": 5,
                 "opus": 5, "sonnet": 5, "kimi-k3": 4, "deepseek-v4-pro": 4,
                 "glm-5.3": 3, "gemini-flash": 3, "flash-lite": 2, "gemini-flash-lite": 2}
FIXTURE_TABLE = {model: {"tiers": {kind: tier for kind in ("code", "analysis", "writing", "review", "research_design")}}
                 for model, tier in FIXTURE_TIERS.items()}


def choose(candidates, **kwargs):
    kwargs.setdefault("capability_table", FIXTURE_TABLE)
    kwargs.setdefault("allow_paid", True)
    if "profiles" not in kwargs:
        kind = kwargs.get("kind", "code")
        kwargs["profiles"] = {row["binding_id"]: {"task_buckets": {
            f"{kind}:{FIXTURE_TIERS[row['model_id']]}": {"attempts": 3, "success_rate": 1., "timeouts": 0}}}
            for row in candidates if row["model_id"] in FIXTURE_TIERS}
    return select_model(candidates, difficulty=kwargs.pop("difficulty", 2),
                        kind=kwargs.pop("kind", "code"), **kwargs)


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "claude-sonnet-4-6", "kimi-k3", "deepseek-v4-pro",
                                   "glm-5.3", "gemini-flash", "gemini-flash-lite", "new-small"])
def test_priors(model):
    assert prior_tier(model) == (2, True)


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
def test_unconfirmed_quota_shortfall_remains_eligible_with_penalty(decision):
    pool = [candidate("a", "flash-lite", quota={"decision": decision, "reason": "estimated_shortfall"})]
    result = choose(pool)
    assert result["binding_ref"] == "a"
    assert result["candidates"][0]["quota_penalty"] == 1
    assert result["candidates"][0]["score"][0] == 1
    assert choose(pool, pin="a")["binding_ref"] == "a"
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("reason", ["limit_hit", "limit_reached", "observed_exhausted"])
def test_confirmed_quota_exhaustion_is_unavailable_even_for_pins(reason):
    exhausted = candidate("a", "flash-lite", quota={"decision": "switch", "reason": reason})
    with pytest.raises(ValueError, match="no_runnable_model"):
        choose([exhausted])
    with pytest.raises(ValueError, match="pinned_model_unavailable"):
        choose([exhausted, candidate("b", "opus")], pin="a")


@pytest.mark.parametrize("decision", ["warn", "switch"])
def test_quota_ok_candidate_preferred_over_cheaper_shortfall(decision):
    result = choose([candidate("cheap", "flash-lite", quota={"decision": decision}),
                     candidate("ok", "opus", "paid_api", quota={"decision": "ok"})])
    assert result["binding_ref"] == "ok"
    assert [item["quota_penalty"] for item in result["candidates"]] == [0, 1]



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
    # Only weaker distinct models: retry the top-tier model rather than downgrade (#1280).
    assert choose(pool, failed_model="opus", failed_tier=5)["binding_ref"] == "c"
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
    import random
    monkeypatch.setattr(random, "random", lambda: 1.)
    host = object.__new__(CombinedTrustedHost)
    host._store = _models(tmp_path)
    monkeypatch.setattr(host, "_lease_provider_factory", lambda: lambda r: None)
    (tmp_path / "model_capabilities.json").write_text(json.dumps({"version": 1, "models": FIXTURE_TABLE}))
    monkeypatch.setattr(host, "_routing_availability", lambda *args, **kwargs: {"state": "AVAILABLE", "reason": "fixture"})
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "mid", "strong"})
    monkeypatch.setattr(host, "_quota_check", lambda binding: None)
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {})
    def measured_profiles():
        return {row["binding_id"]: {"task_buckets": {
            f"{kind}:{FIXTURE_TIERS[row['model_id']]}": {"attempts": 3, "success_rate": 1., "timeouts": 0}
            for kind in ("code", "analysis", "writing", "review", "research_design")}}
            for row in host._store.list_bindings_public() if row["model_id"] in FIXTURE_TIERS}
    monkeypatch.setattr(host, "_usage_profiles", measured_profiles)
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
    original_connections = host._store.list_connections_public
    monkeypatch.setattr(host._store, "list_connections_public", lambda: [
        {**c, "auth_method": "api_key"} for c in original_connections()])
    monkeypatch.setattr(host, "_routing_paid_allowed", lambda *a: True)
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
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        host._resolve_task_model(PlannedTask("review", "review", "review", kind="review",
                                               artifact_input={"plan_task_id": "T001"}))


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
    profiles = host._usage_profiles()
    profiles["cheap"] = {"task_buckets": {"code:2": {"attempts": 3, "success_rate": 0, "timeouts": 3}}}
    monkeypatch.setattr(host, "_usage_profiles", lambda: profiles)
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=2),
                                      failed_binding="cheap", failed_tier=2)
    assert result["binding_ref"] == "strong" and result["tier"] > 2


@pytest.mark.parametrize("difficulty,role,binding", [(2, "simple", "strong"), (4, "complex", "cheap")])
def test_difficulty_only_plans_honor_corresponding_legacy_role_pins(monkeypatch, tmp_path, difficulty, role, binding):
    host = fixture_host(monkeypatch, tmp_path)
    host._store.put_agent_roster({"roles": {role: {"binding_id": binding, "pin": True}}})
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=difficulty))
    assert result["binding_ref"] == binding and result["reason"] == "pin"


@pytest.mark.parametrize("traits", [{"agent_role": "reviewer"}, {"kind": "review"}])
def test_reviewer_without_artifact_input_fails_closed(monkeypatch, tmp_path, traits):
    host = fixture_host(monkeypatch, tmp_path)
    with pytest.raises(TaskStoreError, match="model_review_artifact_input_required"):
        host._resolve_task_model(PlannedTask("review", "Review", "Review", **traits))


@pytest.mark.parametrize("role", ["coder", "complex", "planner", "reviewer"])
def test_legacy_roles_can_route_with_only_prior(role):
    from reverse_agent.platform_v1 import model_router
    difficulty, kind = model_router.task_traits({"agent_role": role})
    result = model_router.select_model([candidate("a", "unknown", executor="codex")],
                                      difficulty=difficulty, kind=kind, role=role)
    assert result["reason"] == "prior_only_unproven"
    assert result["underpowered"] and result["tier_source"] == "prior"


@pytest.mark.parametrize("source", ["measured", "owner_table", "owner_override"])
def test_proven_candidate_preferred_to_cheap_prior(source):
    from reverse_agent.platform_v1 import model_router
    kwargs = {}
    if source == "measured":
        kwargs["profiles"] = {"proven": {"task_buckets": {
            "code:4": {"attempts": 3, "success_rate": 1., "timeouts": 0}}}}
    elif source == "owner_table":
        kwargs["capability_table"] = {"known": {"tiers": {"code": 4}}}
    else:
        kwargs["overrides"] = {"proven": {"tiers": {"code": 4}}}
    result = model_router.select_model([candidate("prior", "unknown"),
        candidate("proven", "known", "subscription")], difficulty=4, kind="code", **kwargs)
    assert result["binding_ref"] == "proven" and not result["underpowered"]
    assert result["tier_source"] == source
    assert not next(c for c in result["candidates"] if c["binding_id"] == "proven")["unproven"]


def test_binding_tier_precedence_and_pinned_hard_limit():
    from reverse_agent.platform_v1 import model_router
    pool = [candidate("a", "known"), candidate("b", "unknown")]
    kwargs = dict(difficulty=4, kind="code",
        profiles={"a": {"task_buckets": {"code:4": {
            "attempts": 3, "success_rate": 0., "timeouts": 0}}}},
        capability_table={"known": {"tiers": {"code": 1}}},
        overrides={"a": {"tiers": {"code": 5}}})
    result = model_router.select_model(pool, **kwargs)
    assert result["tier"] == 5 and result["tier_source"] == "owner_override"
    kwargs["overrides"]["a"]["max_difficulty"] = 3
    with pytest.raises(model_router.ModelSelectionError, match="pinned_model_unavailable") as caught:
        model_router.select_model(pool, pin="a", **kwargs)
    assert caught.value.decision["excluded_candidates"][0]["filter"] == "owner_override"


@pytest.mark.parametrize("tiers", [None, [], {"code": True}, {"code": 0},
                                    {"code": 6}, {"unknown": 4}])
def test_binding_tier_override_validation(tmp_path, tiers):
    from reverse_agent.platform_v1 import routing_inputs
    (tmp_path / "model_routing_overrides.json").write_text(
        json.dumps({"bindings": {"a": {"tiers": tiers}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
        routing_inputs.read_overrides(tmp_path / "model_setup_state.json")


def test_insufficient_measurements_fall_through_to_owner_then_prior():
    from reverse_agent.platform_v1 import routing_capabilities
    profile = {"task_buckets": {"code:4": {
        "attempts": 2, "success_rate": 0., "timeouts": 0}}}
    table = {"known": {"tiers": {"code": 4}}}
    assert routing_capabilities.tier_evidence("known", profile, "code", 4, table) == (4, False, "owner_table")
    assert routing_capabilities.tier_evidence("known", profile, "code", 4) == (2, True, "prior")
    profile["task_buckets"]["code:4"]["attempts"] = 3
    assert routing_capabilities.tier_evidence("known", profile, "code", 4, table) == (3, False, "measured")


def test_valid_binding_tiers_round_trip_and_lower_measured_tier(tmp_path):
    from reverse_agent.platform_v1 import routing_inputs, model_router
    config = {"bindings": {"a": {"tiers": {"code": 1, "review": 5}}}}
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps(config), encoding="utf-8")
    overrides = routing_inputs.read_overrides(tmp_path / "model_setup_state.json")["bindings"]
    result = model_router.select_model([candidate("a", "known")], difficulty=4, kind="code",
        overrides=overrides, profiles={"a": {"task_buckets": {
            "code:5": {"attempts": 3, "success_rate": 1., "timeouts": 0}}}})
    assert result["tier"] == 1 and result["underpowered"]
    assert result["tier_source"] == "owner_override"


@pytest.mark.parametrize("extra,expected", [
    ({"availability": {"state": "UNAVAILABLE", "reason": "model_not_supported"}}, "availability:model_not_supported"),
    ({"quota": {"reason": "observed_exhausted"}}, "quota_exhausted"),
    ({"runnable": False}, "executor_fitness"),
])
def test_prior_fallback_pin_does_not_bypass_hard_gates(extra, expected):
    from reverse_agent.platform_v1 import model_router
    blocked = candidate("blocked", "unknown")
    blocked.update(extra)
    with pytest.raises(model_router.ModelSelectionError, match="pinned_model_unavailable") as caught:
        model_router.select_model([blocked, candidate("other", "another")],
                                  difficulty=4, kind="code", pin="blocked")
    assert caught.value.decision["excluded_candidates"][0]["filter"] == expected


@pytest.mark.parametrize("pin", ["", "alias"])
def test_chain_authors_excluded_for_pins_and_underpowered_fallback(pin):
    from reverse_agent.platform_v1.model_router import ModelSelectionError
    pool = [candidate("alias", "gateway/vendor/Opus-free:free"), candidate("other", "flash-lite")]
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose(pool, kind="review", difficulty=4, author_models=["opus", "glm-5.3"], pin=pin)
    result = choose(pool, kind="review", author_models=["vendor/opus:free", "glm-5.3"])
    assert result["binding_ref"] == "other"
    assert result["excluded_candidates"][0]["filter"] == "reviewer_is_author"


def test_review_ancestry_shared_ancestors_and_missing_required_source():
    planned = {name: PlannedTask(name, name, name, dependencies=deps) for name, deps in
               [("A", ()), ("B", ("A",)), ("C", ("A",)), ("D", ("B", "C"))]}
    review = PlannedTask("R", "R", "R", kind="review", artifact_input={"plan_task_id": "D"})
    assert GoalService._review_ancestry(review, planned) == ("A", "B", "C", "D")
    del planned["A"]
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        GoalService._review_ancestry(review, planned)


def test_review_retry_retains_only_qualifying_independent_model():
    result = choose([candidate("author", "opus"), candidate("reviewer", "gpt-6-sol"),
                     candidate("weak", "flash-lite")], kind="review", difficulty=4,
                    author_models=["opus"], failed_model="gpt-6-sol", failed_tier=5)
    assert result["binding_ref"] == "reviewer" and not result["underpowered"]


def test_review_missing_chain_binding_cannot_grant_independence(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    task = PlannedTask("R", "Review", "Review", kind="review", difficulty=2,
                       artifact_input={"plan_task_id": "P"})
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        host._resolve_task_model(task, author_models=["opus"], author_bindings=["deleted-author"])
