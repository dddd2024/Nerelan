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
    # A rate limit is the account's answer: shown, but neither an attempt nor a failure.
    assert (profile["attempts"], profile["ok"], profile["failed"], profile["timeouts"], profile["rate_limited"]) == (3, 2, 1, 1, 1)
    assert profile["success_rate"] == 0.67
    assert profile["median_ok_seconds"] == 780 and profile["p90_ok_seconds"] == 840
    assert profile["median_ok_tokens"] == 2000
    assert profile["failure_kinds"] == {"timeout": 1}
    assert profile["neutral_failures"] == {"quota_or_rate_limit": 1}


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


def test_PROVIDER_QUOTA_LIMIT_classification_is_not_capability_evidence():
    store = TaskStore(":memory:")
    # The successful attempt and the quota-limited attempt were routed different content
    # classes, so an attempt-count of one proves only the success was counted.
    done = _task(store, "glm", "READY_FOR_REVIEW", start="2026-10-13T06:00:00Z", end="2026-10-13T06:10:00Z")
    store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                        "VALUES (?, ?, 'MODEL_SELECTED', '2026-10-13T06:00:01Z', '', '', '', ?)",
                        (f"sel-{done.id}", done.id, '{"content_class": "docs"}'))
    limited = _task(store, "glm", "FAILED", "provider_quota_limit", tokens=400)
    # The attempt was routed a content class and a task trait before it was cut off.
    store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                        "VALUES (?, ?, 'MODEL_SELECTED', '2026-10-13T06:11:00Z', '', '', '', ?)",
                        (f"sel-{limited.id}", limited.id, '{"kind": "code", "difficulty": 3, "content_class": "code"}'))
    store._conn.commit()
    _task(store, "glm", "FAILED", "provider_quota_limit")  # nothing reported: adds nothing, not a guess
    profile = compute_agent_profiles(store)["glm"]
    # Provider capacity is excluded before any content, task-bucket or capability counting.
    assert (profile["attempts"], profile["ok"], profile["failed"]) == (1, 1, 0)
    assert profile["rate_limited"] == 0 and profile["failure_kinds"] == {}
    assert profile["content_attempts"] == {"docs": {"attempts": 1, "refusals": 0}}
    assert "task_buckets" not in profile and "overloaded" not in profile
    assert profile["provider_quota_limited"] == 2
    assert profile["observed_tokens"] == 400  # the tokens the attempt did spend
    assert profile["success_rate"] == 1.0
    store._conn.close()


@pytest.mark.parametrize("detail", ["", "message=quota exhausted; previous status=402",
                                         "status=4020 message=quota exhausted"])
def test_account_quota_and_provider_quota_are_not_interchangeable(detail):
    from reverse_agent.platform_v1.quota_guard import ACCOUNT_LIMIT, LIMIT_HIT
    store = TaskStore(":memory:")
    _task(store, "glm", "READY_FOR_REVIEW", start="2026-10-13T06:00:00Z", end="2026-10-13T06:10:00Z")
    _task(store, "glm", "FAILED", "provider_quota_limit", tokens=300)
    exhausted = _task(store, "glm", "FAILED", "quota_exhausted")
    store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (detail, exhausted.id))
    store._conn.commit()
    profile = compute_agent_profiles(store)["glm"]
    # Only the account's own answer counts as a rate limit; like every quota answer it
    # is availability evidence, never an attempt or a failure of the model.
    assert (profile["attempts"], profile["failed"], profile["rate_limited"]) == (1, 0, 1)
    assert profile["failure_kinds"] == {} and profile["neutral_failures"] == {"quota_or_rate_limit": 1}
    assert profile["provider_quota_limited"] == 1
    assert not ACCOUNT_LIMIT.search("provider_quota_limit") and not LIMIT_HIT.search("provider_quota_limit")
    store._conn.close()


@pytest.mark.parametrize("status,message", [
    (402, "OpenRouter: Insufficient credits. This account never purchased credits"),
    (429, "WorkBuddy AI: Credits exhausted. Please purchase add-on packs"),
    (402, "Payment required"),
])
def test_billing_error_is_not_counted_as_a_model_failure(status, message):
    from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor, _bounded_error_diagnostic

    events = [{"type": "error", "error": {"name": "APIError", "data": {
        "statusCode": status, "message": message}}}]
    classification = OpenCodeExecutor(model_id="fixture/model")._classify_exit(1, events)
    assert classification == "quota_exhausted"
    detail = "opencode_nonzero:exit=1:quota_exhausted " + _bounded_error_diagnostic(events)
    store = TaskStore(":memory:")
    try:
        _task(store, "billing", "READY_FOR_REVIEW", tokens=100)
        for tokens in (40, None):
            refused = _task(store, "billing", "FAILED", classification, tokens=tokens)
            store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (detail, refused.id))
            store._conn.execute(
                "INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                "VALUES (?, ?, 'MODEL_SELECTED', '2026-11-16T08:00:00Z', '', '', '', ?)",
                (f"sel-{refused.id}", refused.id,
                 '{"kind":"code","difficulty":3,"content_class":"private"}'))
        store._conn.commit()
        profile = compute_agent_profiles(store)["billing"]
        assert (profile["attempts"], profile["ok"], profile["failed"]) == (1, 1, 0)
        assert profile["success_rate"] == 1.0
        assert profile["failure_kinds"] == {} and profile["rate_limited"] == 0
        assert profile["content_attempts"] == {"code": {"attempts": 1, "refusals": 0}}
        assert "task_buckets" not in profile
        assert profile["observed_tokens"] == 140  # missing usage is not guessed
        assert profile["billing_refused"] == 2
        assert store._conn.execute("SELECT COUNT(*) FROM tasks WHERE status='FAILED'").fetchone()[0] == 2
    finally:
        store._conn.close()


@pytest.mark.parametrize("classification,detail,cause", [
    ("executor_stalled", "opencode_stalled:900", "executor_stalled"),
    ("executor_terminated", "", None),  # already skipped before any counting
    ("host_version_changed", "", None),
    ("orphaned_preparation", "interrupted before anything was dispatched", "orphaned_preparation"),
    ("api_error_429", "", "quota_or_rate_limit"),
    ("quota_exhausted:limit_hit", "", "quota_or_rate_limit"),
    ("codex_usage_limit", "", "quota_or_rate_limit"),
    ("model_review_abandoned_no_reply", "model_review_abandoned_no_reply:timeout: reviewer call op-1 ended with no reply",
     "model_review_abandoned_no_reply"),
    ("review_not_independent", "review_not_independent", "review_not_independent"),
    ("ambiguous_external_operation", "external operation already recorded", "ambiguous_external_operation"),
    ("executor_dispatch_failed", "executor_dispatch_failed", "executor_dispatch_failed"),
    ("cleanup_unconfirmed", "opencode_cleanup_unconfirmed", "cleanup_unconfirmed"),
    ("review_diff_too_large", "review_diff_too_large", "review_diff_too_large"),
    ("codex_frame_limit_exceeded", "codex_frame_limit_exceeded", "codex_frame_limit_exceeded"),
    ("claude_code_frame_limit_exceeded", "", "claude_code_frame_limit_exceeded"),
    ("deterministic_validation_failure", "functional_base_mismatch", "functional_base_mismatch"),
    ("deterministic_validation_failure", "functional_worktree_root_required", "functional_worktree_root_required"),
    ("deterministic_validation_failure", "functional_contract_invalid_or_stale", "functional_contract_invalid_or_stale"),
    ("deterministic_validation_failure", "functional_observation_failed:OSError", "functional_observation_failed"),
    # 2026-11-19 live (#1551): host-side failures that had spent the goal's max_retries.
    ("executor_nonzero", 'opencode_nonzero:exit=1:executor_nonzero name=UnknownError message={"message":"x: rpm '
     'exhausted (429: you can retry your request)","type":"api_error"', "quota_or_rate_limit"),
    ("executor_nonzero", 'opencode_nonzero:exit=1:executor_nonzero name=UnknownError message={"message":"x: '
     'inference exceeds tpm/rpm limit (429: you can retry your request)"', "quota_or_rate_limit"),
    ("executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero name=APIError status=429 message=slow down",
     "quota_or_rate_limit"),
    ("executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero message=OpenCode Zen Free: Free usage limit reached",
     "quota_or_rate_limit"),
    ("executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero message=(out of its allowance: not asked again before 07:06 UTC-4)",
     "quota_or_rate_limit"),
    ("executor_nonzero", "opencode_nonzero:exit=1073807364:executor_nonzero", "executor_terminated"),
    ("owner_window_binding_outside_confirmed_pool", "owner_window_binding_outside_confirmed_pool",
     "owner_window_binding_outside_confirmed_pool"),
    ("stream_budget_abort_confirmed", "stream_budget_abort_confirmed", "stream_budget_abort_confirmed"),
    ("stream_budget_abort_unknown", "stream_budget_abort_unknown", "stream_budget_abort_unknown"),
    ("stream_budget_usage_unknown_before_dispatch", "stream_budget_usage_unknown_before_dispatch",
     "stream_budget_usage_unknown_before_dispatch"),
    ("stream_budget_exhausted_before_dispatch", "stream_budget_exhausted_before_dispatch",
     "stream_budget_exhausted_before_dispatch"),
    ("server_budget_snapshot_unavailable", "server_budget_snapshot_unavailable",
     "server_budget_snapshot_unavailable"),
    ("server_budget_snapshot_invalid", "server_budget_snapshot_invalid", "server_budget_snapshot_invalid"),
    ("server_transport_failed", "server_transport_failed", "server_transport_failed"),
    ("server_transport_internal_failure", "server_transport_internal_failure", "server_transport_internal_failure"),
    ("server_stream_stalled", "server_stream_stalled", "server_stream_stalled"),
    ("server_event_too_large", "server_event_too_large", "server_event_too_large"),
    ("server_event_disconnected", "server_event_disconnected", "server_event_disconnected"),
    ("server_http_request_failed", "server_http_request_failed", "server_http_request_failed"),
    ("server_process_exited_before_health", "server_process_exited_before_health",
     "server_process_exited_before_health"),
    ("server_health_timeout", "server_health_timeout", "server_health_timeout"),
])
def test_host_and_quota_failures_are_neither_attempts_nor_failures(classification, detail, cause):
    """Live 2026-11-17: stalls and the #1526 base mismatch demoted GLM-5.3 from tier 4 to 2."""
    store = TaskStore(":memory:")
    for _ in range(3):
        _task(store, "glm", "READY_FOR_REVIEW")
    for _ in range(3):
        failed = _task(store, "glm", "FAILED", classification, tokens=200)
        store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (detail, failed.id))
    store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                        "SELECT 'sel-' || id, id, 'MODEL_SELECTED', '', '', '', '', "
                        "'{\"kind\": \"code\", \"difficulty\": 3}' FROM tasks")
    store._conn.commit()
    profile = compute_agent_profiles(store)["glm"]
    assert (profile["attempts"], profile["ok"], profile["failed"]) == (3, 3, 0)
    assert profile["failure_kinds"] == {} and profile["success_rate"] == 1.0
    assert profile["task_buckets"]["code:3"]["attempts"] == 3
    assert profile["content_attempts"] == {"code": {"attempts": 3, "refusals": 0}}
    if cause is not None:
        assert profile["neutral_failures"] == {cause: 3}
        assert profile["observed_tokens"] == 600  # tokens spent are still counted
    store._conn.close()


@pytest.mark.parametrize("classification,detail,kind", [
    ("deterministic_validation_failure", "functional_check_failed", "deterministic_validation_failure"),
    ("deterministic_validation_failure", "functional_implementation_missing", "deterministic_validation_failure"),
    # The patch the model left broke hygiene (e.g. test artifacts in the tree): its work.
    ("deterministic_validation_failure", "functional_patch_hygiene_failed", "deterministic_validation_failure"),
    # The model ended its turn without changing the product: its work.
    ("codex_no_product_changes", "", "codex_no_product_changes"),
    ("timeout", "opencode_timeout:3600", "timeout"),
    ("executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero", "executor_nonzero"),
    # A message that only mentions a number is not a rate limit; other API errors stay the model's.
    ("executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero name=APIError status=500 message=line 1429",
     "executor_nonzero"),
    ("codex_event_limit_exceeded", "", "codex_event_limit_exceeded"),
    ("model_review_invalid_output", "", "model_review_invalid_output"),
])
def test_real_model_failures_still_count(classification, detail, kind):
    store = TaskStore(":memory:")
    _task(store, "glm", "READY_FOR_REVIEW")
    failed = _task(store, "glm", "FAILED", classification)
    store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (detail, failed.id))
    store._conn.commit()
    profile = compute_agent_profiles(store)["glm"]
    assert (profile["attempts"], profile["ok"], profile["failed"]) == (2, 1, 1)
    assert profile["failure_kinds"] == {kind: 1} and "neutral_failures" not in profile
    store._conn.close()


def test_neutral_classes_reuse_the_host_definitions():
    from reverse_agent.platform_v1 import goal_service, model_profiles, model_review
    assert goal_service.HOST_RETRY_CLASSES is model_profiles.HOST_RETRY_CLASSES
    assert model_review.ABANDONED_NO_REPLY in model_profiles.HOST_PLUMBING_CLASSES


def test_provider_rate_limit_reply_recognizes_free_usage_limit_and_allowance():
    from reverse_agent.platform_v1.model_availability import no_credits_error, provider_rate_limit_reply
    magpie_msg = (
        "AI_APICallError: OpenCode Zen Free: Free usage limit reached. Free models work in OpenCode "
        "(https://opencode.ai); subscribe to OpenCode Go to keep going: https://opencode.ai/go "
        "(out of its allowance: not asked again before 07:06 UTC-4)"
    )
    assert provider_rate_limit_reply("Free usage limit reached") is True
    assert provider_rate_limit_reply("out of its allowance") is True
    assert provider_rate_limit_reply(magpie_msg) is True
    assert no_credits_error(magpie_msg) is None
    assert provider_rate_limit_reply("HTTP 429 Credits exhausted") is False
    assert provider_rate_limit_reply("status=429 insufficient credits") is False
    assert provider_rate_limit_reply("Internal server error 500") is False


def test_server_budget_and_transport_classes_remain_non_agent_failures():
    from reverse_agent.platform_v1 import goal_service
    server_plumbing = (
        "stream_budget_abort_confirmed",
        "stream_budget_abort_unknown",
        "stream_budget_usage_unknown_before_dispatch",
        "stream_budget_exhausted_before_dispatch",
        "server_budget_snapshot_unavailable",
        "server_budget_snapshot_invalid",
        "server_transport_failed",
        "server_transport_internal_failure",
    )
    for cls in server_plumbing:
        assert goal_service._NON_AGENT_FAILURE.search(cls), cls
