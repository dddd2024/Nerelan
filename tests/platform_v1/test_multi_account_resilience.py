"""Resilience of the multi-account brain on real evidence and long runs.

Covers three things the original suite did not:

* perception must survive the *actual* upstream window shape (``basis``,
  ``availability``, unexpected future keys) and one malformed account — the
  earlier strict model raised on real Magpie evidence, which silently disabled
  the whole perception layer in production;
* cooldowns must escalate, survive a restart and keep account quarantines
  separate from per-task quiet time;
* account-level feedback must re-order equal accounts without ever promoting an
  unhealthy one, and every hold must say when capacity returns.
"""
import json

import pytest

from reverse_agent.platform_v1.multi_account import MultiAccountOrchestrator
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.cooldowns import (
    QUARANTINE, TRANSIENT, CooldownRegistry,
)
from reverse_agent.platform_v1.multi_account.scoring import AccountScoreboard
from reverse_agent.platform_v1.multi_account.scheduler import (
    AccountAwareScheduler, next_after_failure, select_account,
)
from reverse_agent.platform_v1.multi_account.status import (
    AccountHealth, AccountStatus, MultiAccountStatusMonitor, pool_account_quotas,
)

CFG = MultiAccountConfig()
NOW = 1_700_000_000.0


def iso(epoch):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def magpie_snapshot(*accounts):
    return {"status": "available", "accounts": list(accounts)}


def magpie_account(ref, provider, used, resets_at, *, observed_at=None):
    return {"account_ref": ref, "provider": provider, "state": "FRESH",
            "observed_at": iso(observed_at if observed_at is not None else NOW),
            "windows": [{"name": "5h", "used_percent": used, "resets_at": iso(resets_at)}]}


def mk(ref, health, *, headroom=None, flags=(), provider="codex", fresh=0.0,
       windows=()):
    return AccountStatus(account_ref=ref, provider=provider, health=health,
                         headroom_pct=headroom, anomaly_flags=list(flags),
                         freshness_age=fresh, windows=list(windows))


# --- perception on real evidence ------------------------------------------------

def test_perceive_accepts_real_magpie_windows_with_basis_and_availability():
    """Regression: ``basis``/``availability`` used to raise extra_forbidden."""
    snapshot = magpie_snapshot(magpie_account("acct-1", "codex", 100.0, NOW + 600))
    pooled = pool_account_quotas(snapshot, now=NOW)
    assert pooled["acct-1"]["windows"][0]["basis"] == "official_percent"
    statuses = MultiAccountStatusMonitor(CFG, fetch_quotas=lambda s: pooled).perceive(now=NOW)
    assert [s.health for s in statuses] == [AccountHealth.EXHAUSTED]
    assert statuses[0].headroom_pct == 0.0


def test_pool_account_quotas_tolerates_empty_or_odd_snapshot():
    """Regression: an empty ``accounts`` list used to raise UnboundLocalError."""
    assert pool_account_quotas({"accounts": []}) == {}
    assert pool_account_quotas({"status": "unavailable", "accounts": None}) == {}
    assert pool_account_quotas({"accounts": "not-a-list"}) == {}
    assert pool_account_quotas({}) == {}


def test_unknown_window_keys_are_preserved_not_fatal():
    status = MultiAccountStatusMonitor._normalize_window(
        {"name": "weekly", "used_percent": 12.0, "future_field": {"x": 1}, "window": "weekly"})
    assert status.window == "weekly"
    assert status.extra == {"future_field": {"x": 1}}


def test_one_malformed_account_does_not_empty_the_pool():
    monitor = MultiAccountStatusMonitor(
        CFG, fetch_quotas=lambda s: {"bad": {"windows": [{"used_percent": "n/a"}]},
                                     "good": {"observed_at": iso(NOW), "windows": []}})
    statuses = {s.account_ref: s for s in monitor.perceive(now=NOW)}
    assert statuses["good"].health is AccountHealth.HEALTHY
    assert statuses["bad"].health is AccountHealth.UNKNOWN
    assert "perception_error" in statuses["bad"].anomaly_flags


def test_health_summary_of_a_generator_counts_every_account():
    """Regression: ``total_accounts`` was 0 because the generator was consumed."""
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=10.0),
                mk("b", AccountHealth.EXHAUSTED)]
    summary = MultiAccountStatusMonitor.health_summary(iter(statuses))
    assert summary["total_accounts"] == 2
    assert summary["eligible_accounts"] == 1


def test_public_view_is_json_safe_and_hides_raw_evidence():
    status = mk("a", AccountHealth.HEALTHY, headroom=40.0)
    status.raw = {"secret_free": "evidence"}
    view = status.public_view()
    assert "raw" not in view
    assert json.loads(json.dumps(view))["account_ref"] == "a"


# --- cooldowns ------------------------------------------------------------------

def test_cooldown_escalates_and_is_capped():
    registry = CooldownRegistry(CFG, clock=lambda: NOW)
    delays = []
    for _ in range(6):
        entry = registry.record_failure("a", "task_failed", now=NOW)
        delays.append(entry.until - NOW)
    assert delays[0] == CFG.failure_backoff_base_seconds
    assert delays[1] == 2 * delays[0]
    assert delays == sorted(delays)
    assert max(delays) == CFG.failure_backoff_max_seconds


def test_abnormal_failure_quarantines_and_quota_failure_only_quiets():
    registry = CooldownRegistry(CFG, clock=lambda: NOW)
    assert registry.record_failure("a", "account_abnormal", now=NOW).tier == QUARANTINE
    assert registry.record_failure("b", "quota_exhausted", now=NOW).tier == TRANSIENT
    assert registry.record_failure("a", "account_abnormal", now=NOW).until - NOW >= \
        CFG.abnormal_account_cooldown_seconds


def test_success_clears_quiet_time_but_not_quarantine():
    registry = CooldownRegistry(CFG, clock=lambda: NOW)
    registry.record_failure("quiet", "task_failed", now=NOW)
    registry.record_failure("sick", "account_abnormal", now=NOW)
    registry.record_success("quiet", now=NOW)
    registry.record_success("sick", now=NOW)
    assert not registry.is_cooling("quiet", now=NOW)
    assert registry.is_cooling("sick", now=NOW)


def test_new_task_clears_transient_cooldown_but_keeps_quarantine():
    sched = AccountAwareScheduler(CFG, clock=lambda: NOW)
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]
    sched.on_failure(statuses, failed_ref="a", failure_kind="quota_exhausted", attempt=1)
    assert sched.select(statuses)["account_ref"] == "b"
    sched.reset_for_task()
    assert sched.select(statuses)["account_ref"] == "a"

    sched.on_failure(statuses, failed_ref="a", failure_kind="account_abnormal", attempt=1)
    sched.reset_for_task()
    assert sched.select(statuses)["account_ref"] == "b"


def test_prune_drops_entries_past_the_memory_window():
    clock = [NOW]
    registry = CooldownRegistry(CFG, clock=lambda: clock[0])
    registry.record_failure("a", "task_failed")
    clock[0] = NOW + CFG.cooldown_memory_seconds + CFG.failure_backoff_max_seconds + 1
    assert registry.prune() == 1
    assert registry.snapshot() == {}


# --- restart safety -------------------------------------------------------------

def test_quarantine_and_scores_survive_a_restart(tmp_path):
    store = tmp_path / "multi_account.json"
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]

    first = MultiAccountOrchestrator(CFG, clock=lambda: NOW, store_path=store)
    first.on_failure(statuses, failed_ref="a", failure_kind="account_abnormal", attempt=1)
    first.record_account_outcome("b", ok=True, cost_units=2.0, wall_seconds=30.0)

    second = MultiAccountOrchestrator(CFG, clock=lambda: NOW, store_path=store)
    assert second.cooldowns.is_cooling("a", now=NOW)
    assert second.select(statuses)["account_ref"] == "b"
    assert second.account_scores()["b"]["attempts"] == 1


def test_state_document_is_one_atomic_json_with_every_section(tmp_path):
    store = tmp_path / "multi_account.json"
    brain = MultiAccountOrchestrator(CFG, clock=lambda: NOW, store_path=store)
    brain.record_outcome({"mode": "single", "accepted": True, "cost_units": 5.0,
                          "task_count": 2, "tokens": {}, "wall_seconds": 10.0})
    brain.record_account_outcome("a", ok=False, failure_kind="task_failed")
    brain.on_failure([mk("a", AccountHealth.HEALTHY, headroom=50.0)],
                     failed_ref="a", failure_kind="account_abnormal", attempt=1)

    document = json.loads(store.read_text(encoding="utf-8"))
    assert set(document) == {"runs", "break_even", "accounts", "cooldowns", "updated_at"}
    assert document["runs"] and document["accounts"]["a"]["attempts"] == 1


def test_persisting_disabled_keeps_state_in_memory(tmp_path):
    config = MultiAccountConfig(persist_account_state=False)
    store = tmp_path / "multi_account.json"
    brain = MultiAccountOrchestrator(config, clock=lambda: NOW, store_path=store)
    brain.on_failure([mk("a", AccountHealth.HEALTHY)], failed_ref="a",
                     failure_kind="account_abnormal", attempt=1)
    assert brain.cooldowns.is_cooling("a", now=NOW)
    assert not store.exists()


# --- scheduling: retry_at and cost/stability balance ----------------------------

def test_hold_reports_when_capacity_returns():
    window = {"window": "5h", "used_percent": 100.0, "resets_at": NOW + 600}
    statuses = [mk("a", AccountHealth.EXHAUSTED, windows=[window])]
    decision = select_account(statuses, config=CFG, now=NOW)
    assert decision["decision"] == "hold"
    assert decision["retry_at"] == NOW + 600


def test_hold_reports_earliest_cooldown_expiry():
    registry = CooldownRegistry(CFG, clock=lambda: NOW)
    registry.record_failure("a", "account_abnormal", now=NOW)
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=50.0)]
    decision = select_account(statuses, config=CFG, now=NOW, cooldowns=registry)
    assert decision["decision"] == "hold"
    assert decision["reason"] == "accounts_cooling_down"
    assert decision["retry_at"] == registry.until("a")


def _trained_scoreboard(*outcomes):
    board = AccountScoreboard(CFG, clock=lambda: NOW)
    for ref, ok, cost in outcomes:
        board.observe(ref, ok=ok, cost_units=cost, wall_seconds=60.0, now=NOW)
    return board


def test_measured_feedback_reorders_equally_healthy_accounts():
    # Same health, similar headroom: the reliable, cheaper account should win.
    statuses = [mk("flaky", AccountHealth.HEALTHY, headroom=60.0),
                mk("solid", AccountHealth.HEALTHY, headroom=50.0)]
    board = _trained_scoreboard(*([("flaky", False, 8.0)] * 4 + [("solid", True, 2.0)] * 4))
    decision = select_account(statuses, config=CFG, now=NOW, scores=board)
    assert decision["account_ref"] == "solid"
    assert decision["reason"] == "best_composite"


def test_feedback_never_promotes_a_degraded_account_over_a_healthy_one():
    statuses = [mk("healthy", AccountHealth.HEALTHY, headroom=5.0),
                mk("degraded", AccountHealth.DEGRADED, headroom=95.0)]
    board = _trained_scoreboard(*([("healthy", False, 9.0)] * 5 + [("degraded", True, 1.0)] * 5))
    decision = select_account(statuses, config=CFG, now=NOW, scores=board)
    assert decision["account_ref"] == "healthy"


def test_untrained_scoreboard_leaves_headroom_ordering_untouched():
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=30.0),
                mk("b", AccountHealth.HEALTHY, headroom=70.0)]
    decision = select_account(statuses, config=CFG, now=NOW, scores=AccountScoreboard(CFG))
    assert decision["account_ref"] == "b"
    assert decision["reason"] == "best_headroom"


def test_repeated_failures_grow_the_cooldown_across_attempts():
    sched = AccountAwareScheduler(CFG, clock=lambda: NOW)
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]
    sched.on_failure(statuses, failed_ref="a", failure_kind="task_failed", attempt=1)
    first = sched.cooldowns.until("a") - NOW
    sched.on_failure(statuses, failed_ref="a", failure_kind="task_failed", attempt=2)
    second = sched.cooldowns.until("a") - NOW
    assert second > first


def test_generator_input_is_consumed_once():
    """A caller passing a generator must not lose the pool on the hold path."""
    statuses = (mk(ref, AccountHealth.EXHAUSTED) for ref in ("a", "b"))
    decision = select_account(statuses, config=CFG, now=NOW)
    assert decision["decision"] == "hold"
    assert decision["evidence"]["observed"] == 2


def test_dead_letter_carries_evidence_and_retry_hint():
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0)]
    result = next_after_failure(statuses, config=CFG, failed_ref="a",
                                failure_kind="quota_exhausted",
                                attempt=CFG.reroute_max_attempts, now=NOW)
    assert result["decision"] == "dead_letter"
    assert result["evidence"]["failure_kind"] == "quota_exhausted"
    assert result["retry_at"] is not None


# --- bounded self-evolution -----------------------------------------------------

def test_run_ledger_is_bounded(monkeypatch):
    config = MultiAccountConfig(max_recorded_runs=3)
    from reverse_agent.platform_v1.multi_account.evolution import SelfEvolutionStore
    store = SelfEvolutionStore(config, path=None)
    for index in range(10):
        store.record_run({"mode": "single", "accepted": True, "cost_units": index,
                          "task_count": 1, "tokens": {}, "wall_seconds": 1.0})
    runs = store.get_runs()
    assert len(runs) == 3
    assert [r["cost_units"] for r in runs] == [7, 8, 9]


def test_account_outcome_is_ignored_when_scoring_is_disabled():
    config = MultiAccountConfig(enable_account_scoring=False)
    brain = MultiAccountOrchestrator(config, clock=lambda: NOW)
    assert brain.record_account_outcome("a", ok=True) is None
    assert brain.account_scores() == {}


def test_config_rejects_incoherent_backoff():
    with pytest.raises(ValueError):
        MultiAccountConfig(failure_backoff_base_seconds=100.0,
                           failure_backoff_max_seconds=10.0)
    with pytest.raises(ValueError):
        MultiAccountConfig(failure_backoff_multiplier=0.5)
    with pytest.raises(ValueError):
        MultiAccountConfig(score_ewma_alpha=0.0)


# --- coordinator feedback seam --------------------------------------------------

def test_coordinator_reports_feedback_and_swallows_failures():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

    calls = []
    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._last_error = ""
    coordinator.account_feedback = lambda task, ok: calls.append((task, ok))
    task = SimpleNamespace(binding_ref="binding-1")

    coordinator._report_account_feedback(task, success=True)
    assert calls == [(task, True)]

    def explode(_task, _ok):
        raise RuntimeError("feedback down")

    coordinator.account_feedback = explode
    coordinator._report_account_feedback(task, success=False)
    assert coordinator._last_error.startswith("account_feedback_failed")


def test_coordinator_without_feedback_callback_is_inert():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._last_error = ""
    coordinator.account_feedback = None
    coordinator._report_account_feedback(SimpleNamespace(binding_ref="b"), success=True)
    assert coordinator._last_error == ""


def test_dispatch_layer_round_trips_account_feedback(tmp_path):
    from reverse_agent.platform_v1.multi_account import dispatch

    store = tmp_path / "state.json"
    assert dispatch.record_account_outcome(None, ok=True) is None  # no account, no write
    payload = dispatch.record_account_outcome(
        "acct-9", ok=False, failure_kind="account_abnormal", store_path=store)
    assert payload and payload["attempts"] == 1
    assert dispatch.account_scores(store)["acct-9"]["attempts"] == 1
    dispatch.report_account_success("acct-9", store_path=store)
    dispatch.reset_orchestrator()


# --- coordinator feedback seam --------------------------------------------------

def test_coordinator_reports_feedback_and_swallows_failures():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

    calls = []
    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._last_error = ""
    coordinator.account_feedback = lambda task, ok: calls.append((task, ok))
    task = SimpleNamespace(binding_ref="binding-1")

    coordinator._report_account_feedback(task, success=True)
    assert calls == [(task, True)]

    def explode(_task, _ok):
        raise RuntimeError("feedback down")

    coordinator.account_feedback = explode
    coordinator._report_account_feedback(task, success=False)
    assert coordinator._last_error.startswith("account_feedback_failed")


def test_coordinator_without_feedback_callback_is_inert():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._last_error = ""
    coordinator.account_feedback = None
    coordinator._report_account_feedback(SimpleNamespace(binding_ref="b"), success=True)
    assert coordinator._last_error == ""


def test_dispatch_layer_round_trips_account_feedback(tmp_path):
    from reverse_agent.platform_v1.multi_account import dispatch

    store = tmp_path / "state.json"
    assert dispatch.record_account_outcome(None, ok=True) is None  # no account, no write
    payload = dispatch.record_account_outcome(
        "acct-9", ok=False, failure_kind="account_abnormal", store_path=store)
    assert payload and payload["attempts"] == 1
    assert dispatch.account_scores(store)["acct-9"]["attempts"] == 1
    dispatch.report_account_success("acct-9", store_path=store)
    dispatch.reset_orchestrator()


# --- cost/latency telemetry (spec §11.5 item 1) ---------------------------------

def _seed_task(store, *, model_id="claude-sonnet-5-5", observation=None,
               created="2026-11-04T10:00:00Z", updated="2026-11-04T10:02:30Z"):
    task = store.create_task(title="t", executor_kind="claude_code",
                             binding_ref="binding-1", repository="o/r")
    store._conn.execute("UPDATE tasks SET created_at = ?, updated_at = ? WHERE id = ?",
                        (created, updated, task.id))
    if observation is not None:
        store._conn.execute(
            "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, role, "
            "model_id, provider_id, source_kind, source_id, status, input_units, output_units, reasoning_units, "
            "cache_read_units, cache_write_units, payload_digest, created_at) VALUES "
            "(?, ?, '', 0, 'e', 'executor', ?, 'p', 's', ?, 'OBSERVED', ?, ?, ?, ?, ?, '', '')",
            (f"u-{task.id}", task.id, model_id, f"src-{task.id}", *observation))
    store._conn.commit()
    return task


def test_task_feedback_metrics_prices_tokens_and_wall_time():
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics

    store = TaskStore(":memory:")
    task = _seed_task(store, observation=(1000, 500, 100, 2000, 0))
    metrics = task_feedback_metrics(store, task.id)
    assert metrics["cost_units"] and metrics["cost_units"] > 0
    assert metrics["wall_seconds"] == 150.0


def test_task_feedback_metrics_never_invents_a_cost():
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics

    store = TaskStore(":memory:")
    unpriced = _seed_task(store, model_id="not-a-real-model", observation=(10, 10, 0, 0, 0))
    assert task_feedback_metrics(store, unpriced.id)["cost_units"] is None
    empty = _seed_task(store, observation=None)
    metrics = task_feedback_metrics(store, empty.id)
    assert metrics["cost_units"] is None and metrics["wall_seconds"] == 150.0
    empty_metrics = task_feedback_metrics(store, "")
    assert empty_metrics["cost_units"] is None and empty_metrics["wall_seconds"] is None
    assert empty_metrics["basis"] == "list_price"  # an estimate, never "cash"


def test_measured_cost_reaches_the_scoreboard():
    """End-to-end: a finished task's list price becomes the account's mean cost."""
    from reverse_agent.platform_v1.multi_account import dispatch, MultiAccountOrchestrator

    brain = MultiAccountOrchestrator(CFG, clock=lambda: NOW)
    brain.record_account_outcome("acct-1", ok=True, cost_units=0.42, wall_seconds=150.0)
    score = brain.account_scores()["acct-1"]
    assert score["mean_cost_units"] == 0.42
    assert score["mean_wall_seconds"] == 150.0
    dispatch.reset_orchestrator()


# --- cost/latency telemetry (spec §11.5 item 1) ---------------------------------

def _seed_task(store, *, model_id="claude-sonnet-5-5", observation=None,
               created="2026-11-04T10:00:00Z", updated="2026-11-04T10:02:30Z"):
    task = store.create_task(title="t", executor_kind="claude_code",
                             binding_ref="binding-1", repository="o/r")
    store._conn.execute("UPDATE tasks SET created_at = ?, updated_at = ? WHERE id = ?",
                        (created, updated, task.id))
    if observation is not None:
        store._conn.execute(
            "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, role, "
            "model_id, provider_id, source_kind, source_id, status, input_units, output_units, reasoning_units, "
            "cache_read_units, cache_write_units, payload_digest, created_at) VALUES "
            "(?, ?, '', 0, 'e', 'executor', ?, 'p', 's', ?, 'OBSERVED', ?, ?, ?, ?, ?, '', '')",
            (f"u-{task.id}", task.id, model_id, f"src-{task.id}", *observation))
    store._conn.commit()
    return task


def test_task_feedback_metrics_prices_tokens_and_wall_time():
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics

    store = TaskStore(":memory:")
    task = _seed_task(store, observation=(1000, 500, 100, 2000, 0))
    metrics = task_feedback_metrics(store, task.id)
    assert metrics["cost_units"] and metrics["cost_units"] > 0
    assert metrics["wall_seconds"] == 150.0


def test_task_feedback_metrics_never_invents_a_cost():
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics

    store = TaskStore(":memory:")
    unpriced = _seed_task(store, model_id="not-a-real-model", observation=(10, 10, 0, 0, 0))
    assert task_feedback_metrics(store, unpriced.id)["cost_units"] is None
    empty = _seed_task(store, observation=None)
    metrics = task_feedback_metrics(store, empty.id)
    assert metrics["cost_units"] is None and metrics["wall_seconds"] == 150.0
    empty_metrics = task_feedback_metrics(store, "")
    assert empty_metrics["cost_units"] is None and empty_metrics["wall_seconds"] is None
    assert empty_metrics["basis"] == "list_price"  # an estimate, never "cash"


def test_measured_cost_reaches_the_scoreboard():
    """End-to-end: a finished task's list price becomes the account's mean cost."""
    from reverse_agent.platform_v1.multi_account import dispatch, MultiAccountOrchestrator

    brain = MultiAccountOrchestrator(CFG, clock=lambda: NOW)
    brain.record_account_outcome("acct-1", ok=True, cost_units=0.42, wall_seconds=150.0)
    score = brain.account_scores()["acct-1"]
    assert score["mean_cost_units"] == 0.42
    assert score["mean_wall_seconds"] == 150.0
    dispatch.reset_orchestrator()


# --- idle wait hint (spec §11.5 item 3) -----------------------------------------

def test_orchestrator_exposes_seconds_until_the_earliest_cooldown():
    brain = MultiAccountOrchestrator(CFG, clock=lambda: NOW)
    assert brain.next_retry_in() is None
    brain.on_failure([mk("a", AccountHealth.HEALTHY)], failed_ref="a",
                     failure_kind="task_failed", attempt=1)
    assert brain.next_retry_in() == CFG.failure_backoff_base_seconds


def test_coordinator_sleeps_until_the_hint_but_never_past_the_cap():
    from reverse_agent.platform_v1.unattended_coordinator import (
        IDLE_WAIT_CAP_SECONDS, UnattendedCoordinator,
    )

    coordinator = object.__new__(UnattendedCoordinator)
    coordinator.poll_interval = 1.0
    coordinator._active_task_ids = set()
    coordinator._dispatch_active = False
    coordinator._lifecycle_lock = __import__("threading").RLock()

    coordinator.idle_wait_hint = None
    assert coordinator.idle_wait(0) == 1.0  # no hint: unchanged behaviour

    coordinator.idle_wait_hint = lambda: 30.0
    assert coordinator.idle_wait(0) == 30.0
    assert coordinator.idle_wait(dispatched=2) == 1.0  # work happened: poll again soon
    coordinator._active_task_ids = {"t"}
    assert coordinator.idle_wait(0) == 1.0  # work in flight: never stretch

    coordinator._active_task_ids = set()
    coordinator.idle_wait_hint = lambda: 5 * 3600.0
    assert coordinator.idle_wait(0) == IDLE_WAIT_CAP_SECONDS

    coordinator.idle_wait_hint = lambda: 0.0
    assert coordinator.idle_wait(0) == 1.0

    def broken():
        raise RuntimeError("no signal")

    coordinator.idle_wait_hint = broken
    assert coordinator.idle_wait(0) == 1.0
