"""Policy revisions reuse the real atomic account-feedback transaction."""
import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator
from reverse_agent.platform_v1.multi_account.policy_lifecycle import advance_policy


def config(**values):
    return MultiAccountConfig(enable_policy_evolution=True, policy_min_new_attempts=3, **values)


def train(brain, start=0, count=3, *, ok=False, cost=None, latency=None, kind="account_abnormal"):
    for index in range(start, start + count):
        brain.record_account_outcome("account", ok=ok, cost_units=cost, wall_seconds=latency,
            failure_kind=kind, outcome_id=f"attempt:{index}")


def test_unique_terminal_feedback_changes_one_bounded_weight_and_is_auditable(tmp_path):
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json")
    train(brain, count=2)
    assert brain.account_policy_view()["revision"] == 0
    brain.record_account_outcome("account", ok=False, failure_kind="account_abnormal", outcome_id="attempt:1")
    assert brain.account_policy_view()["revision"] == 0
    train(brain, start=2, count=1)
    view = brain.account_policy_view()
    assert view["revision"] == 1 and view["effective"]["reliability_weight"] == 13.2
    assert view["history"][-1]["evidence"]["source_ids"] == ["attempt:0", "attempt:1", "attempt:2"]
    assert view["history"][-1]["evidence"]["cost_per_executor_success"] is None


def test_failed_storage_commits_neither_policy_nor_feedback(tmp_path, monkeypatch):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(config(), store_path=path)
    train(brain, count=2)
    saved = path.read_bytes()
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("fixture write failure")
        patch.setattr("reverse_agent.platform_v1.multi_account.evolution.os.replace", fail)
        with pytest.raises(OSError):
            train(brain, start=2, count=1)
    assert path.read_bytes() == saved
    assert brain.scores.get("account").attempts == 2 and brain.account_policy_view()["revision"] == 0
    train(brain, start=2, count=1)
    assert brain.scores.get("account").attempts == 3 and brain.account_policy_view()["revision"] == 1


def test_rollback_is_a_new_revision_and_narrower_limits_reject_old_target(tmp_path):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(config(), store_path=path)
    train(brain)
    result = brain.rollback_account_policy(0, expected_revision=1)
    assert result["revision"] == 2 and result["effective"]["reliability_weight"] == 12
    assert result["history"][0]["after"]["reliability_weight"] == 13.2
    strict = MultiAccountOrchestrator(config(policy_max_weight_drift_ratio=.025), store_path=path)
    saved = path.read_bytes()
    with pytest.raises(ValueError, match="outside_current_bounds"):
        strict.rollback_account_policy(1, expected_revision=2)
    assert path.read_bytes() == saved
    assert strict.account_policy_view()["effective"]["reliability_weight"] == 12


def test_disabled_evolution_ignores_persisted_weights_without_deleting_history(tmp_path):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(config(), store_path=path)
    train(brain)
    saved = path.read_bytes()
    disabled = MultiAccountOrchestrator(MultiAccountConfig(), store_path=path)
    view = disabled.account_policy_view()
    assert view["effective"]["reliability_weight"] == 12 and len(view["history"]) == 1
    assert path.read_bytes() == saved


def test_known_zero_cost_reference_still_detects_later_positive_cost(tmp_path):
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json")
    train(brain, ok=True, cost=0)
    assert brain.account_policy_view()["revision"] == 0
    train(brain, start=3, ok=True, cost=1)
    view = brain.account_policy_view()
    assert view["revision"] == 1 and view["effective"]["cost_weight"] == 11


def test_unknown_cost_and_anonymous_samples_do_not_invent_pressure(tmp_path):
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json")
    for _ in range(5):
        brain.record_account_outcome("account", ok=False, failure_kind="task_failed")
    assert brain.account_policy_view()["revision"] == 0
    train(brain, ok=True, cost=None)
    assert brain.account_policy_view()["revision"] == 0
    assert brain.account_policy_view()["last_assessment"]["cost_per_executor_success"] is None


def test_pruned_rollback_target_and_stale_expected_revision_are_rejected(tmp_path):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(config(policy_audit_limit=2), store_path=path)
    train(brain, count=9)
    view = brain.account_policy_view()
    assert view["revision"] == 3 and len(view["history"]) == 2
    assert view["effective"]["reliability_weight"] == 15
    saved = path.read_bytes()
    with pytest.raises(ValueError, match="not_retained"):
        brain.rollback_account_policy(1, expected_revision=3)
    with pytest.raises(ValueError, match="revision_changed"):
        brain.rollback_account_policy(0, expected_revision=2)
    assert path.read_bytes() == saved


def test_proposal_transition_is_pure_and_extreme_finite_values_stay_json_safe():
    cfg = config(reliability_weight=1e308)
    state = {}
    for index in range(3):
        previous = copy.deepcopy(state)
        result = advance_policy(state, cfg, outcome={"ok": False, "failure_kind": "account_abnormal",
            "cost_units": 1e308, "wall_seconds": 1e308}, outcome_id=str(index), now=1000 + index)
        assert state == previous
        state = result
    assert state["effective"]["reliability_weight"] > 1e308
    assert state["last_assessment"]["cost_per_executor_success"] is None
    json.dumps(state, allow_nan=False)


def test_invalid_optional_policy_keeps_real_account_isolation_and_records_error(tmp_path):
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json")
    brain.store.patch("account_policy", {"invalid": "fixture"})
    brain.record_account_outcome("account", ok=False, failure_kind="account_abnormal", outcome_id="receipt")
    assert brain.cooldowns.get("account").tier == "quarantine"
    assert brain.store.section("account_policy") == {"invalid": "fixture"}
    assert brain.store.section("account_feedback")["receipt"]["policy_error"] == "invalid_policy_evidence"


def test_actual_task_router_consumes_revision_and_rollback_without_changing_owner_config(tmp_path, monkeypatch):
    from tests.platform_v1.test_model_router import fixture_host
    from reverse_agent.platform_v1.multi_account import dispatch
    from reverse_agent.platform_v1.goal_service import PlannedTask
    host = fixture_host(monkeypatch, tmp_path)
    for ref, account in (("free-api", "bad-account"), ("backup-api", "good-account")):
        host._store.upsert_connection(dict(connection_id=ref, name=ref, provider="openai-compatible",
            base_url="https://example.invalid/v1", auth_method="none", enabled=True, account_ref=account))
    host._store.upsert_binding(dict(binding_id="backup", name="backup", executor_id="opencode",
        connection_id="backup-api", model_id="flash-lite", enabled=True))
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "backup"})
    brain = MultiAccountOrchestrator(config(enable_feedback_routing=True), store_path=tmp_path / "feedback.json")
    for index in range(3):
        brain.record_account_outcome("bad-account", ok=False, failure_kind="task_failed", outcome_id=f"bad:{index}")
        brain.record_account_outcome("good-account", ok=True, outcome_id=f"good:{index}")
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: brain)
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    result = host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))
    evidence = result["score_breakdown"]["account_feedback"]
    revision = brain.account_policy_view()["revision"]
    assert result["binding_ref"] == "backup" and evidence["evolution_revision"] == revision
    assert evidence["policy"]["reliability_weight"] > 12 and brain.config.reliability_weight == 12
    brain.rollback_account_policy(0, expected_revision=revision)
    result = host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))
    evidence = result["score_breakdown"]["account_feedback"]
    assert evidence["evolution_revision"] == revision + 1
    assert evidence["policy"]["reliability_weight"] == 12


def test_concurrent_stale_rollbacks_cannot_overwrite_a_new_revision(tmp_path):
    path = tmp_path / "feedback.json"
    first = MultiAccountOrchestrator(config(), store_path=path)
    train(first)
    second = MultiAccountOrchestrator(config(), store_path=path)
    def rollback(brain):
        try:
            return brain.rollback_account_policy(0, expected_revision=1)["revision"]
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rollback, (first, second)))
    assert results.count(2) == 1 and results.count("policy_revision_changed") == 1


def test_failed_rollback_persistence_preserves_effective_policy_and_history(tmp_path, monkeypatch):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(config(), store_path=path)
    train(brain)
    saved = path.read_bytes()
    def fail(*args):
        raise OSError("fixture write failure")
    monkeypatch.setattr("reverse_agent.platform_v1.multi_account.evolution.os.replace", fail)
    with pytest.raises(OSError):
        brain.rollback_account_policy(0, expected_revision=1)
    assert path.read_bytes() == saved
    assert brain.account_policy_view()["revision"] == 1


def test_capacity_waits_do_not_change_quality_weights_and_timeouts_have_distinct_feedback(tmp_path):
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json")
    train(brain, kind="quota_exhausted")
    view = brain.account_policy_view()
    assert view["revision"] == 0 and view["last_assessment"]["reason"] == "capacity_only"
    assert view["last_assessment"]["quality_success_rate_excluding_capacity"] is None
    train(brain, start=3, kind="timeout")
    view = brain.account_policy_view()
    assert view["revision"] == 1 and view["effective"]["latency_weight"] == 5.5
    assert view["effective"]["reliability_weight"] == 12


def test_old_partial_window_cannot_complete_a_new_evolution_quorum(tmp_path):
    clock = [1000.0]
    brain = MultiAccountOrchestrator(config(), store_path=tmp_path / "feedback.json", clock=lambda: clock[0])
    train(brain, count=2)
    clock[0] += 86401
    train(brain, start=2, count=1)
    assert brain.account_policy_view()["revision"] == 0
    train(brain, start=3, count=2)
    view = brain.account_policy_view()
    assert view["revision"] == 1
    assert view["history"][-1]["evidence"]["source_ids"] == ["attempt:2", "attempt:3", "attempt:4"]


def test_unconsumed_state_sections_survive_feedback_and_policy_updates(tmp_path):
    path = tmp_path / "feedback.json"
    unknown = {"future_version": 3, "audit": [{"event": "retained"}]}
    path.write_text(json.dumps({"future_policy": unknown}), encoding="utf-8")
    brain = MultiAccountOrchestrator(config(), store_path=path)
    train(brain)
    brain.rollback_account_policy(0, expected_revision=1)
    assert json.loads(path.read_text())["future_policy"] == unknown
