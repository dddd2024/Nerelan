"""Persisted account isolation must reach real host/router entry points."""

from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.goal_service import PlannedTask, _reroute_guard_skip
from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator
from reverse_agent.platform_v1.multi_account import dispatch
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
from tests.platform_v1.test_model_router import fixture_host


@pytest.fixture
def pool(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    host._task_store = TaskStore(":memory:")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    clock = [1_700_000_000.0]
    path = tmp_path / "brain.json"
    brain = MultiAccountOrchestrator(MultiAccountConfig(), clock=lambda: clock[0], store_path=path)
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: brain)
    monkeypatch.setattr(host, "_quota_check", CombinedTrustedHost._quota_check.__get__(host))
    monkeypatch.setattr(host, "_limit_hit_until", lambda connection: None)
    for ref, account in (("free-api", "shared"), ("sibling-api", "shared"), ("healthy-api", "healthy")):
        host._store.upsert_connection(dict(connection_id=ref, name=ref, provider="openai-compatible",
            base_url="https://example.invalid/v1", auth_method="none", enabled=True, account_ref=account))
    for ref, connection in (("sibling", "sibling-api"), ("healthy", "healthy-api")):
        host._store.upsert_binding(dict(binding_id=ref, name=ref, executor_id="opencode",
            connection_id=connection, model_id="flash-lite", enabled=True))
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "sibling", "healthy"})
    monkeypatch.setattr(host._store, "list_executors_public", lambda: [
        {"executor_id": "opencode", "operational": True}])
    brain.record_account_outcome("shared", ok=False, failure_kind="account_abnormal", now=clock[0])
    yield host, brain, clock, path
    host._task_store._conn.close()


def test_task_router_excludes_every_connection_on_the_isolated_account(pool):
    host, brain, clock, path = pool
    result = host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))
    assert result["binding_ref"] == "healthy"
    excluded = {row["binding_id"]: row for row in result["excluded_candidates"]}
    assert excluded["cheap"]["filter"] == "account_quarantined"
    assert excluded["sibling"]["filter"] == "account_quarantined"
    assert excluded["cheap"]["retry_at"] == brain.cooldowns.until("shared")


def test_role_fallback_uses_a_different_account_and_waits_if_all_are_isolated(pool):
    host, brain, clock, path = pool
    assert host._quota_guarded("simple", "opencode", "cheap", {}) == ("opencode", "healthy")
    brain.record_account_outcome("healthy", ok=False, failure_kind="account_abnormal", now=clock[0])
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:account_quarantined:no_alternative"):
        host._quota_guarded("simple", "opencode", "cheap", {})


def test_quota_held_goal_reroute_honours_isolation_without_a_new_observation(pool):
    host, brain, clock, path = pool
    service = SimpleNamespace(account_status_provider=lambda: [],
                              binding_account_resolver=lambda binding: "shared")
    assert _reroute_guard_skip(service, {"binding_ref": "sibling"}) == (True, "shared")


def test_expiry_restores_production_eligibility(pool):
    host, brain, clock, path = pool
    clock[0] = brain.cooldowns.until("shared") + 1
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


@pytest.mark.parametrize("owner", ["local", "magpie"])
def test_disabled_or_delegated_account_policy_does_not_veto_routes(pool, monkeypatch, owner):
    host, brain, clock, path = pool
    if owner == "local":
        monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED")
    else:
        brain.config.account_routing = "magpie"
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


def test_optional_policy_failure_preserves_the_legacy_route(pool, monkeypatch):
    host, brain, clock, path = pool
    def unavailable(*args, **kwargs):
        raise OSError("optional feedback unavailable")
    monkeypatch.setattr(dispatch, "get_orchestrator", unavailable)
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


def test_task_failure_quiet_time_is_not_a_global_account_isolation(pool):
    host, brain, clock, path = pool
    brain.cooldowns.clear("shared")
    brain.record_account_outcome("shared", ok=False, failure_kind="task_failed", now=clock[0])
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


def test_restarting_feedback_store_does_not_restore_a_bad_route(pool, monkeypatch):
    host, brain, clock, path = pool
    restored = MultiAccountOrchestrator(MultiAccountConfig(), clock=lambda: clock[0], store_path=path)
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: restored)
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "healthy"


def test_optional_policy_failure_still_runs_the_existing_quota_check(pool, monkeypatch):
    host, brain, clock, path = pool
    def unavailable(*args, **kwargs):
        raise OSError("optional feedback unavailable")
    monkeypatch.setattr(dispatch, "get_orchestrator", unavailable)
    monkeypatch.setattr(host, "_limit_hit_until", lambda connection: clock[0] + 1000)
    assert host._quota_check(host._store.get_binding_public("cheap"))["reason"] == "limit_hit"


def test_a_pinned_quarantined_binding_is_not_forced_onto_the_bad_account(pool):
    host, brain, clock, path = pool
    host._store.put_agent_roster({"roles": {"simple": {"binding_id": "cheap", "pin": True}}})
    with pytest.raises(TaskStoreError, match="pinned_model_unavailable"):
        host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))


@pytest.mark.parametrize("classification", ["server_session_error", "author_identity_unknown",
    "authorization_scope_denied", "review_session_missing", "server_basic_auth_required"])
def test_local_session_and_authority_failures_do_not_isolate_a_provider(pool, classification):
    host, brain, clock, path = pool
    brain.cooldowns.clear("shared")
    task = SimpleNamespace(id="fixture", binding_ref="cheap", failure_classification=classification)
    host._report_account_feedback_to_brain(task, success=False)
    assert brain.cooldowns.get("shared").tier == "transient"
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


@pytest.mark.parametrize("classification", ["auth_provider_route_failure",
    "MODEL_UNAVAILABLE:authentication_error", "MODEL_UNAVAILABLE:invalid_api_key", "api_error_401"])
def test_finite_provider_auth_failure_feedback_is_consumed_by_production_routing(pool, classification):
    host, brain, clock, path = pool
    brain.cooldowns.clear("shared")
    task = SimpleNamespace(id="fixture", binding_ref="cheap", failure_classification=classification)
    host._report_account_feedback_to_brain(task, success=False)
    assert brain.cooldowns.get("shared").tier == "quarantine"
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "healthy"


def test_host_wait_refusals_cannot_keep_renewing_account_isolation(pool):
    host, brain, clock, path = pool
    until = brain.cooldowns.until("shared")
    attempts = brain.scores.get("shared").attempts
    clock[0] += 100
    task = SimpleNamespace(id="fixture", binding_ref="cheap",
        failure_classification="QUOTA_WAIT:account_quarantined:no_alternative")
    host._report_account_feedback_to_brain(task, success=False)
    assert brain.cooldowns.until("shared") == until
    assert brain.scores.get("shared").attempts == attempts
    clock[0] = until + 1
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"
