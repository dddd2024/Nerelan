"""Agent profiles learned from real task outcomes (provider-free)."""
from __future__ import annotations

import pytest

from reverse_agent.platform_v1 import durable_execution as de
from reverse_agent.platform_v1.model_profiles import compute_agent_profiles, recommended_timeout_seconds
from reverse_agent.platform_v1.run_store import TaskStore


def _task(store, binding, status, classification="", *, start=None, end=None, tokens=None, kind="opencode",
          start_event="EXECUTOR_RUNNING"):
    task = store.create_task(title="t", executor_kind=kind, binding_ref=binding, repository="o/r")
    store._conn.execute("UPDATE tasks SET status = ?, failure_classification = ? WHERE id = ?",
                        (status, classification, task.id))
    for seq, (kind_, stamp) in enumerate(((start_event, start), ("EXECUTOR_FINISHED", end))):
        if stamp:
            store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                                "VALUES (?, ?, ?, ?, '', '', '', '{}')", (f"ev-{task.id}-{seq}", task.id, kind_, stamp))
    if tokens is not None:
        store._conn.execute(
            "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, role, model_id, "
            "provider_id, source_kind, source_id, status, input_units, output_units, payload_digest, created_at) "
            "VALUES (?, ?, '', 0, 'e', 'executor', 'm', 'p', 's', ?, 'OBSERVED', ?, 0, '', '')",
            (f"u-{task.id}", task.id, f"src-{task.id}", tokens))
    store._conn.commit()
    return task


def test_profile_reports_rates_durations_tokens_and_failure_kinds():
    store = TaskStore(":memory:")
    _task(store, "glm", "READY_FOR_REVIEW", start="2026-10-13T06:00:00Z", end="2026-10-13T06:14:00Z", tokens=1000)
    _task(store, "glm", "READY_FOR_REVIEW", start="2026-10-13T07:00:00Z", end="2026-10-13T07:12:00Z", tokens=3000)
    _task(store, "glm", "FAILED", "timeout", start="2026-10-13T08:00:00Z", end="2026-10-13T08:10:00Z")
    _task(store, "glm", "FAILED", "provider_rate_limited:429")
    _task(store, "glm", "QUEUED")  # not finished: not an attempt
    profile = compute_agent_profiles(store)["glm"]
    assert (profile["attempts"], profile["ok"], profile["failed"], profile["timeouts"], profile["rate_limited"]) == (4, 2, 2, 1, 1)
    assert profile["success_rate"] == 0.5
    assert profile["median_ok_seconds"] == 780 and profile["p90_ok_seconds"] == 840
    assert profile["median_ok_tokens"] == 2000
    assert profile["failure_kinds"] == {"timeout": 1, "provider_rate_limited": 1}


def test_observed_tokens_total_every_finished_attempt_that_reported_them():
    store = TaskStore(":memory:")
    _task(store, "glm", "READY_FOR_REVIEW", tokens=1000)
    _task(store, "glm", "FAILED", "timeout", tokens=500)  # a failed turn still spent tokens
    _task(store, "glm", "FAILED", "timeout")  # nothing reported: adds nothing, not a guess
    _task(store, "glm", "QUEUED", tokens=9999)  # not finished: not an attempt
    assert compute_agent_profiles(store)["glm"]["observed_tokens"] == 1500


def test_native_runs_are_timed_from_workspace_ready():
    store = TaskStore(":memory:")
    for minute in (1, 2):
        _task(store, "sonnet", "READY_FOR_REVIEW", kind="claude_code", start_event="WORKSPACE_READY",
              start=f"2026-10-13T06:0{minute}:00Z", end=f"2026-10-13T06:0{minute}:50Z")
    profile = compute_agent_profiles(store)["sonnet"]
    assert profile["median_ok_seconds"] == 50 and profile["executor_kind"] == "claude_code"


def _fresh_recommendation(store, binding):
    store._agent_profile_cache = None  # profiles are cached for a minute; these steps add rows in between
    return recommended_timeout_seconds(store, binding)


def test_recommended_timeout_fits_slow_productive_agents_within_bounds():
    store = TaskStore(":memory:")
    assert _fresh_recommendation(store, "glm") is None  # no evidence yet
    _task(store, "cutoff", "FAILED", "timeout", start="2026-10-13T06:00:00Z", end="2026-10-13T06:10:00Z")
    assert _fresh_recommendation(store, "cutoff") == de.MAX_EXECUTOR_TIMEOUT_SECONDS  # only ever cut off
    for hour in (6, 7):
        _task(store, "fast", "READY_FOR_REVIEW", start=f"2026-10-13T0{hour}:00:00Z", end=f"2026-10-13T0{hour}:01:00Z")
    assert _fresh_recommendation(store, "fast") == de.DEFAULT_EXECUTOR_TIMEOUT_SECONDS  # never below the default
    for hour in (6, 7):
        _task(store, "slow", "READY_FOR_REVIEW", start=f"2026-10-13T0{hour}:00:00Z", end=f"2026-10-13T0{hour}:09:00Z")
    assert _fresh_recommendation(store, "slow") == 756  # p90 9 min x 1.4


@pytest.mark.parametrize("binding,expected", [("slow", 756), ("fresh", 600)])
def test_execution_uses_the_learned_turn_limit(monkeypatch, binding, expected):
    monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raising=False)
    store = TaskStore(":memory:")
    for hour in (6, 7):
        _task(store, "slow", "READY_FOR_REVIEW", start=f"2026-10-13T0{hour}:00:00Z", end=f"2026-10-13T0{hour}:09:00Z")
    task = store.create_task(title="next", executor_kind="opencode", binding_ref=binding, repository="o/r")
    service = de.DurableExecutionService.__new__(de.DurableExecutionService)
    service.store, service.binding_resolver, service.lease_provider = store, None, None
    assert service._build_executor_kwargs(task)["timeout"] == expected


def test_an_explicit_host_timeout_is_not_raised_by_learning(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", "300")
    store = TaskStore(":memory:")
    for hour in (6, 7):
        _task(store, "slow", "READY_FOR_REVIEW", start=f"2026-10-13T0{hour}:00:00Z", end=f"2026-10-13T0{hour}:09:00Z")
    task = store.create_task(title="next", executor_kind="opencode", binding_ref="slow", repository="o/r")
    service = de.DurableExecutionService.__new__(de.DurableExecutionService)
    service.store, service.binding_resolver, service.lease_provider = store, None, None
    assert service._build_executor_kwargs(task)["timeout"] == 300


def test_profiles_are_cached_for_a_minute():
    store = TaskStore(":memory:")
    assert recommended_timeout_seconds(store, "cutoff") is None
    _task(store, "cutoff", "FAILED", "timeout", start="2026-10-13T06:00:00Z", end="2026-10-13T06:10:00Z")
    assert recommended_timeout_seconds(store, "cutoff") is None  # cached profile, no new scan
    assert _fresh_recommendation(store, "cutoff") == de.MAX_EXECUTOR_TIMEOUT_SECONDS


def test_best_pairing_needs_evidence_and_prefers_success_then_speed():
    from reverse_agent.platform_v1.model_profiles import best_pairing
    profiles = {
        "glm@opencode": {"attempts": 10, "success_rate": 0.5, "median_ok_seconds": 840},
        "glm@claude": {"attempts": 4, "success_rate": 0.75, "median_ok_seconds": 120},
        "glm@thin": {"attempts": 2, "success_rate": 1.0, "median_ok_seconds": 10},  # too little evidence
        "glm@same": {"attempts": 5, "success_rate": 0.5, "median_ok_seconds": 300},
    }
    assert best_pairing(profiles, "glm@opencode", ["glm@claude", "glm@thin"]) == "glm@claude"
    assert best_pairing(profiles, "glm@opencode", ["glm@thin"]) == "glm@opencode"
    assert best_pairing(profiles, "glm@opencode", ["glm@same"]) == "glm@same"  # same rate, faster
    assert best_pairing({}, "glm@opencode", ["glm@claude"]) == "glm@opencode"  # no evidence: keep the choice
    # A sibling never displaces a configured route that has no comparable record yet,
    # least of all one already known to fail every task.
    failing = {"glm@claude": {"attempts": 3, "success_rate": 0.0, "median_ok_seconds": None},
               "glm@opencode": {"attempts": 1, "success_rate": 1.0, "median_ok_seconds": 60}}
    assert best_pairing(failing, "glm@opencode", ["glm@claude"]) == "glm@opencode"
    assert best_pairing({"glm@claude": profiles["glm@claude"]}, "glm@opencode", ["glm@claude"]) == "glm@opencode"


def test_a_planner_is_never_swapped_to_an_executor_that_cannot_plan():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    store = TaskStore(":memory:")
    for hour in (1, 2, 3):  # the OpenCode sibling is measured much better than the Claude Code binding
        _task(store, "glm-opencode", "READY_FOR_REVIEW", start=f"2026-10-13T0{hour}:00:00Z", end=f"2026-10-13T0{hour}:01:00Z")
        _task(store, "glm-claude", "FAILED", "deterministic_validation_failure", kind="claude_code")
    bindings = [{"binding_id": "glm-claude", "executor_id": "claude_code", "connection_id": "c", "model_id": "glm", "enabled": True},
                {"binding_id": "glm-opencode", "executor_id": "opencode", "connection_id": "c", "model_id": "glm", "enabled": True}]
    model_store = SimpleNamespace(list_bindings_public=lambda: bindings,
                                  list_executors_public=lambda: [{"executor_id": e, "operational": True} for e in ("claude_code", "opencode")])
    host = SimpleNamespace(_store=model_store, _task_store=store, ROLE_EXECUTORS=CombinedTrustedHost.ROLE_EXECUTORS)
    pick = lambda role: CombinedTrustedHost._prefer_measured_pairing(host, role, "claude_code", "glm-claude")
    assert pick("planner") == ("claude_code", "glm-claude")  # OpenCode cannot plan
    assert pick("coder") == ("opencode", "glm-opencode")  # other roles follow the measurements


def test_native_token_counts_come_from_the_completion_event():
    store = TaskStore(":memory:")
    task = _task(store, "sonnet", "READY_FOR_REVIEW", kind="claude_code", start_event="WORKSPACE_READY",
                 start="2026-10-13T06:00:00Z", end="2026-10-13T06:00:50Z")
    store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                        "VALUES (?, ?, 'EXECUTOR_COMPLETED', '2026-10-13T06:00:50Z', '', '', '', ?)",
                        (f"done-{task.id}", task.id, '{"token_usage": {"input_tokens": 1200, "cached_input_tokens": 900, "output_tokens": 300}}'))
    store._conn.commit()
    assert compute_agent_profiles(store)["sonnet"]["median_ok_tokens"] == 1500


def test_MODEL_UNAVAILABLE_classification_is_not_capability_evidence():
    store = TaskStore(":memory:")
    _task(store, "glm", "READY_FOR_REVIEW", start="2026-10-13T06:00:00Z", end="2026-10-13T06:10:00Z")
    _task(store, "glm", "FAILED", "MODEL_UNAVAILABLE:model_not_supported")
    _task(store, "glm", "FAILED", "MODEL_UNAVAILABLE:model_not_found")
    _task(store, "glm", "FAILED", "MODEL_UNAVAILABLE:not_allowed")
    _task(store, "glm", "FAILED", "MODEL_UNAVAILABLE:invalid_api_key")
    profile = compute_agent_profiles(store)["glm"]
    assert profile["attempts"] == 1
    assert profile["ok"] == 1
    assert profile["failed"] == 0
    assert profile["failure_kinds"] == {}


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(("code", "message", "reason"), [
    ("invalid_api_key", "Request failed", "invalid_api_key"),
    ("authentication_error", "Request failed", "authentication_error"),
    ("not_allowed", "not allowed for user type", "not_allowed_for_user_type"),
])
def test_real_error_classification_preserves_entitlement_exclusion(nested, code, message, reason):
    from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor
    payload = {"code": code, "message": message, "statusCode": 403}
    event = {"type": "error", "error": {"data": payload} if nested else payload}
    classification = OpenCodeExecutor(model_id="fixture/model")._classify_exit(1, [event])
    assert classification == "MODEL_UNAVAILABLE:" + reason
    store = TaskStore(":memory:")
    try:
        _task(store, "fixture", "READY_FOR_REVIEW")
        _task(store, "fixture", "FAILED", classification)
        profile = compute_agent_profiles(store)["fixture"]
        assert (profile["attempts"], profile["ok"], profile["failed"]) == (1, 1, 0)
        assert profile["success_rate"] == 1.0
        assert profile["failure_kinds"] == {}
    finally:
        store._conn.close()
