"""Issue #1248: provider-free routing, observations and refusal redispatch."""
import json
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.magpie import parse_models
from reverse_agent.platform_v1 import routing_inputs
from reverse_agent.platform_v1.agent_planner import extract_plan
from reverse_agent.platform_v1.goal_service import GoalService, PlannedTask
from reverse_agent.platform_v1.model_profiles import compute_agent_profiles
from reverse_agent.platform_v1.run_store import TaskStoreError
from tests.platform_v1.test_model_router import candidate, choose, fixture_host


def test_context_prior_precedence_modalities_and_exclusion_evidence():
    pool = [candidate("small", "unknown"), candidate("large", "gemini-flash")]
    result = choose(pool, context_need=300_000)
    assert result["binding_ref"] == "large"
    assert result["excluded_candidates"] == [{"binding_id": "small", "model_id": "unknown", "filter": "context_window"}]
    pool[0]["metadata"] = {"context_window": 1_000_000, "input_modalities": ["text", "image"]}
    assert choose(pool, context_need=300_000, needs=["vision"])["binding_ref"] == "small"
    profiles = {"small": {"context_window": 128_000}}
    assert choose(pool, context_need=300_000, profiles=profiles)["binding_ref"] == "large"
    assert choose(pool, context_need=300_000, profiles=profiles,
                  overrides={"small": {"context_window": 1_000_000}}, pin="small")["binding_ref"] == "small"
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("override", [{"exclude": True}, {"max_difficulty": 1},
                                        {"denied_content": ["security_simulation"]},
                                        {"allowed_content": ["writing"]}])
def test_owner_filters_even_pin(override):
    result = choose([candidate("a", "opus"), candidate("b", "sonnet")],
                    needs=["security_simulation"], overrides={"a": override})
    assert result["binding_ref"] == "b"
    assert result["excluded_candidates"][0]["filter"] == "owner_override"


def test_penalties_change_choice_and_unproven_security_is_eligible():
    pool = [candidate("a", "opus"), candidate("b", "sonnet")]
    assert choose(pool)["binding_ref"] == "a"
    assert choose(pool, needs=["tool_use"], profiles={"a": {"tool_reliability": .1}})["binding_ref"] == "b"
    profiles = {"a": {"refusal_rates": {"security_simulation": .4}},
                "b": {"refusal_rates": {"security_simulation": .1}}}
    assert choose(pool, needs=["security_simulation"], profiles=profiles)["binding_ref"] == "b"
    profiles["a"]["refusal_rates"]["security_simulation"] = .8
    result = choose(pool, needs=["security_simulation"], profiles=profiles)
    assert result["excluded_candidates"][0]["filter"] == "refusal_rate"
    assert choose(pool[:1], needs=["security_simulation"])["binding_ref"] == "a"
    assert choose(pool, needs=["low_latency"], profiles={"a": {"median_ok_seconds": 90}})["binding_ref"] == "b"
    pool[1]["metadata"] = {"context_window": 1_000_000}
    assert choose(pool, needs=["long_context"])["binding_ref"] == "b"
    pool[0].update(cost_class="subscription", quota_headroom=.05)
    pool[1].update(cost_class="subscription", quota_headroom=.9)
    assert choose(pool)["binding_ref"] == "b"


@pytest.mark.parametrize("field,value", [("context_need", -1), ("context_need", True),
                                        ("needs", "vision"), ("needs", ["unknown"])])
def test_planner_and_saved_requirements_validate(field, value):
    raw = {"id": "T001", "title": "Task", "instruction": "Do", field: value}
    with pytest.raises(TaskStoreError, match="invalid_task_"):
        extract_plan(json.dumps({"tasks": [raw]}))
    with pytest.raises(TaskStoreError, match="invalid_task_"):
        GoalService._normalize_task(raw, seq=0)


def test_planner_round_trip_and_security_scope():
    raw = {"id": "T001", "title": "Task", "instruction": "Experiment scope: local model only",
           "context_need": 300_000, "needs": ["security_simulation", "tool_use"]}
    task = GoalService._normalize_task(extract_plan(json.dumps({"tasks": [raw]}))["tasks"][0], seq=0)
    assert task.context_need == 300_000 and "tool_use" in task.needs
    title = GoalService._execution_title(SimpleNamespace(title="Research"), task)
    assert "No third-party system is targeted" in title and raw["instruction"] in title


@pytest.mark.parametrize("text,refused", [
    ("I cannot help with that request.", True),
    ("I'm sorry, I can't assist with this experiment.", True),
    ("I will not provide attack instructions.", True),
    ("Implemented the requested feature.", False),
    ("I cannot reproduce the bug; tests pass.", False),
    ('The test checks the string "I cannot help".', False),
])
def test_refusal_messages(text, refused):
    assert routing_inputs.model_refused(text) is refused
    assert not routing_inputs.model_refused(text, changed_files=[{"path": "code.py"}])
    assert routing_inputs.model_refused("", policy_refusal=True)


def announcement(**extra):
    return {"state": "PLAN_ONLY", "expected_reset_at": 100_000,
            "announcement_id": "official-1", "validated": True, **extra}


def test_reset_drains_to_buffer_and_short_window_still_binds():
    pool = [candidate("codex", "gpt-6", "subscription", "codex", quota_headroom=.1, weekly_headroom=.1),
            candidate("claude", "sonnet", "subscription", "claude_code", quota_headroom=.8)]
    assert choose(pool)["binding_ref"] == "claude"
    result = choose(pool, reset_signal=announcement(), now=90_000)
    assert result["binding_ref"] == "codex"
    assert result["reset"]["cost_adjustment"] == pytest.approx(-.9)
    assert result["reset"]["drain_target"] == .03
    assert result["reset"]["announcement_id"] == "official-1"
    assert result["reset"]["target_per_short_window"] == pytest.approx(.07)
    pool[0]["quota"] = {"reason": "observed_exhausted", "window": "5h"}
    result = choose(pool, reset_signal=announcement(), now=90_000)
    assert result["binding_ref"] == "claude"
    assert result["excluded_candidates"][0]["filter"] == "quota_exhausted"
    pool[0]["quota"] = {}
    pool[0]["weekly_headroom"] = .03
    result = choose(pool, reset_signal=announcement(), now=90_000)
    assert result["excluded_candidates"][0]["filter"] == "reset_buffer"


@pytest.mark.parametrize("signal", [None, {"state": "UNKNOWN"}, {"state": "STALE"},
                                    announcement(expected_reset_at=None), announcement(validated=False),
                                    announcement(expected_reset_at="soon")])
def test_unknown_tease_stale_neutral(signal):
    result = choose([candidate("a", "gpt-6", "subscription", "codex", quota_headroom=.1, weekly_headroom=.1)],
                    reset_signal=signal, now=90_000)
    assert result["reset"]["cost_adjustment"] == 0
    assert result["reset"]["drain_target"] is None


def test_after_reset_reread_unreliable_and_no_filler():
    before = routing_inputs.reset_decision(announcement(), now=90_000, weekly_remaining=.2, demand=False)
    assert before["demand"] == "NO_DEMAND" and not before["drain"]
    after = routing_inputs.reset_decision(announcement(), now=101_000, weekly_remaining=.02)
    assert after["refresh_quota"] and after["source_unreliable"] and not after["drain"]
    result = choose([candidate("a", "gpt-6", "subscription", "codex", quota_headroom=.02, weekly_headroom=.02)],
                    reset_signal=announcement(), now=101_000)
    assert result["reset"]["source_unreliable"] and result["reset"]["cost_adjustment"] == 0
    with pytest.raises(ValueError):
        choose([], reset_signal=announcement(), now=90_000)


def test_host_refresh_never_assumes_capacity(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    host._reset_signal_reader = lambda: {"state": "REFRESH_QUOTA"}
    reads = []
    monkeypatch.setattr(host, "_subscription_quotas", lambda: reads.append(1) or {})
    monkeypatch.setattr(host, "_quota_check", lambda binding: {"reason": "observed_exhausted"})
    with pytest.raises(TaskStoreError, match="no_runnable_model"):
        host._resolve_task_model(PlannedTask("T1", "t", "i"))
    assert reads
    monkeypatch.setattr(host, "_quota_check", lambda binding: None)
    assert host._resolve_task_model(PlannedTask("T1", "t", "i"))["binding_ref"]
    host._reset_signal_reader = lambda: 1 / 0
    assert host._routing_reset_signal() == {"state": "UNKNOWN"}


def test_magpie_fixture():
    [model] = parse_models({"object": "list", "data": [{"id": "lab/model", "context_window": 512_000,
        "max_output_tokens": 16_000, "reasoning": True, "input_modalities": ["text", "image"]}]})
    assert model["context_window"] == 512_000
    assert model["max_output_tokens"] == 16_000
    assert model["input_modalities"] == ["text", "image"] and model["reasoning"]


def test_owner_file_and_host_context(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps({"bindings": {"cheap": {"exclude": True, "notes": "Owner"}}}))
    result = host._resolve_task_model(PlannedTask("T1", "t", "i", context_need=10))
    assert result["binding_ref"] != "cheap"
    assert result["context_need"] > 10
    assert result["excluded_candidates"][0]["filter"] == "owner_override"


@pytest.mark.parametrize("config", [
    {"models": {"m": {"cost_class": "bogus"}}},
    {"models": {"m": 123}},
    {"models": {"m": {}}},
    {"models": "free"},
    {"models": {"": "free"}},
    {"connections": {"c": {"cost_class": "paid"}}},
    {"connections": {"c": 1}},
    {"connections": []},
    {"bindings": {"b": {"cost_class": "cheap"}}},
    {"paid_api_windows": [1]},
    {"reset_buffer": "high"},
])
def test_malformed_cost_configuration_is_rejected(tmp_path, config):
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
        routing_inputs.read_overrides(tmp_path / "model_setup_state.json")


def test_malformed_cost_configuration_blocks_host_selection(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    (tmp_path / "model_routing_overrides.json").write_text(
        json.dumps({"connections": {"c": {"cost_class": "bogus"}}}), encoding="utf-8")
    with pytest.raises(TaskStoreError, match="invalid_model_routing_overrides"):
        host._resolve_task_model(PlannedTask("T1", "t", "i"))


def test_model_level_cost_override_round_trips_and_beats_connection(tmp_path):
    config = {"models": {"workbuddy/glm-5.3": {"cost_class": "free"}},
              "connections": {"magpie": {"cost_class": "paid_api"}}}
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps(config), encoding="utf-8")
    owner = routing_inputs.read_overrides(tmp_path / "model_setup_state.json")
    row = {"binding_id": "b", "connection_id": "magpie", "model_id": "workbuddy/glm-5.3"}
    assert routing_inputs.binding_cost_class(row, {"auth_method": "api_key"}, owner) == "free"
    row["model_id"] = "workbuddy/other"
    assert routing_inputs.binding_cost_class(row, {"auth_method": "api_key"}, owner) == "paid_api"


def test_refusal_retry_same_difficulty_distinct_model_and_all_refuse(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    host = fixture_host(monkeypatch, tmp_path)
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({"objective": "Local experiment", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "refusal", "executor_kind": "opencode", "orchestration_mode": "agent_team"})
    goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T1", "title": "Experiment", "instruction": "local only",
                 "difficulty": 2, "needs": ["security_simulation"]}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate({**_window_payload(goal.repository), "max_retries": 5}).id)
    tried = []
    for _ in range(4):
        task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
        task = store.get_task(task_id)
        assert task.binding_ref not in tried
        tried.append(task.binding_ref)
        store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='MODEL_REFUSED' WHERE id=?", (task_id,))
        store._conn.commit()
        profile = compute_agent_profiles(store)[task.binding_ref]
        assert profile["attempts"] == 0
        assert profile["refusal_rates"]["security_simulation"] == 1
        retries = goals.escalate_failed_tasks(goal.id)
        if not retries:
            assert store.get_task(task_id).status == "BLOCKED"
            assert store.get_task(task_id).failure_classification == "no_willing_model"
            assert len(json.loads(store.get_task(task_id).failure_detail)["refusals"]) == len(tried)
            break
        retry = store.get_task(retries[0]["to_task_id"])
        event = next(e for e in store.get_events(retry.id) if e.type == "MODEL_SELECTED")
        assert event.metadata["difficulty"] == 2
        assert event.metadata["reason"] == "refusal_redispatch"
    else:
        pytest.fail("refusals must terminate")
