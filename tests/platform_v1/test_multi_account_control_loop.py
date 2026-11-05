"""End-to-end control loop through the orchestrator facade.

Each test drives the same object a host would: perceive, admit, schedule, report,
evolve, roll back. The point is that the five capabilities stay consistent with
each other across a restart, not that each helper works in isolation.
"""
import json
from datetime import datetime, timezone

from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus

NOW = 1_700_000_000.0


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def evidence(ref_provider="codex", *, used=10.0, at=NOW, resets_in=3600.0):
    return {"provider": ref_provider, "observed_at": iso(at),
            "windows": [{"name": "5h", "used_percent": used,
                         "resets_at": iso(at + resets_in)}]}


def brain(*, config=None, store_path=None, quotas=None):
    return MultiAccountOrchestrator(
        config or MultiAccountConfig(), clock=lambda: NOW,
        fetch_quotas=quotas, store_path=store_path)


def status(ref, health=AccountHealth.HEALTHY, headroom=60.0):
    return AccountStatus(account_ref=ref, provider="codex", health=health,
                         headroom_pct=headroom)


# --- perception --------------------------------------------------------------

def test_observe_returns_one_consistent_payload():
    payload = brain(quotas=lambda _snap: {"acct-a": evidence(used=20.0)}).observe(now=NOW)
    assert set(payload) == {"accounts", "summary", "budget", "alerts", "run", "routing",
                            "policy", "perception_error"}
    assert payload["summary"]["total_accounts"] == 1
    assert payload["summary"]["eligible_accounts"] == 1
    assert payload["accounts"][0]["health"] == "HEALTHY"
    assert payload["run"]["action"] == "continue"
    assert payload["policy"]["version"] == 0
    assert payload["alerts"] == []


def test_observe_alerts_on_an_exhausted_pool():
    payload = brain(quotas=lambda _snap: {"acct-a": evidence(used=100.0)}).observe(now=NOW)
    codes = [alert["code"] for alert in payload["alerts"]]
    assert "all_accounts_exhausted" in codes
    # The alert is queued for delivery exactly once.
    assert len(brain(quotas=lambda _snap: {}).drain_alerts()) == 0


def test_a_failing_observation_degrades_to_a_diagnosable_hold():
    def boom(_snap):
        raise RuntimeError("provider down")

    bot = brain(quotas=boom)
    payload = bot.observe(now=NOW)
    assert payload["accounts"] == []
    assert "provider down" in payload["perception_error"]
    # Empty pool is not silent: it alerts, and a broken source says *why*.
    codes = [alert["code"] for alert in payload["alerts"]]
    assert "perception_failed" in codes
    assert "no_accounts_observed" in codes


# --- cost ceiling through the facade -----------------------------------------

def test_admission_and_settlement_close_the_cost_loop():
    cfg = MultiAccountConfig(cost_budget_enabled=True, cost_budget_units=10.0,
                             cost_budget_window_seconds=100.0,
                             cost_budget_default_task_units=2.0)
    bot = brain(config=cfg)
    decision = bot.admit(2.0, account_ref="acct-a")
    assert decision["decision"] == "allow"
    bot.record_account_outcome("acct-a", ok=True, cost_units=1.5,
                               budget_token=decision["reservation"])
    assert bot.budget_status()["spent_units"] == 1.5
    assert bot.budget_status()["open_reservations"] == 0


def test_exhausted_budget_holds_dispatch_instead_of_dropping_it():
    cfg = MultiAccountConfig(cost_budget_enabled=True, cost_budget_units=5.0,
                             cost_budget_window_seconds=100.0)
    bot = brain(config=cfg)
    bot.record_account_outcome("acct-a", ok=True, cost_units=5.0)
    decision = bot.select([status("acct-a")], need={"cost_units": 1.0})
    assert decision["decision"] == "hold"
    assert decision["reason"] == "cost_budget_exhausted"
    assert decision["retry_at"] == NOW + 100.0


# --- fault tolerance through the facade --------------------------------------

def test_dead_letter_raises_a_task_alert():
    bot = brain()
    result = bot.on_failure([status("acct-a"), status("acct-b", headroom=40.0)],
                            failed_ref="acct-a", failure_kind="task_failed", attempt=3)
    assert result["decision"] == "dead_letter"
    codes = [alert.code for alert in bot.drain_alerts()]
    assert "task_dead_letter" in codes


# --- self-evolution cadence --------------------------------------------------

def test_policy_evaluates_once_per_sample_window_and_alerts():
    bot = brain()
    # Four successes and one account-level failure: below the target success
    # rate, so the loop has a reason to move.
    for index in range(bot.config.policy_min_samples - 1):
        bot.record_account_outcome("acct-a", ok=True, cost_units=1.0)
    bot.record_account_outcome("acct-b", ok=False, failure_kind="account_abnormal")
    assert bot.policy_view()["version"] == 1
    decision = bot.last_policy_decision()
    assert decision is not None and decision["changed"] is True
    assert "policy_changed" in [alert.code for alert in bot.drain_alerts()]


def test_rollback_restores_the_configured_baseline():
    bot = brain()
    for _ in range(bot.config.policy_min_samples):
        bot.record_account_outcome("acct-a", ok=False, failure_kind="account_abnormal")
    evolved = bot.policy_view()
    assert evolved["version"] >= 1
    assert evolved["effective"] != evolved["baseline"]

    rolled = bot.rollback_policy(0)
    assert rolled["changed"] is True
    assert bot.policy_view()["effective"] == bot.policy_view()["baseline"]
    assert "policy_rolled_back" in [alert.code for alert in bot.drain_alerts()]


# --- run duration ------------------------------------------------------------

def test_run_verdict_bounds_the_run():
    cfg = MultiAccountConfig(max_run_duration_seconds=100.0)
    bot = brain(config=cfg)
    bot.start_run(now=NOW)
    assert bot.run_verdict(now=NOW + 50)["action"] == "continue"
    assert bot.run_verdict(now=NOW + 100)["action"] == "conclude"
    assert bot.run_status(now=NOW + 100)["attempts"] == 0


def test_feedback_advances_the_run_watchdog():
    bot = brain()
    bot.start_run(now=NOW)
    bot.record_account_outcome("acct-a", ok=True)
    assert bot.run_status(now=NOW)["attempts"] == 1


# --- restart continuity ------------------------------------------------------

def test_restart_keeps_spend_cooldowns_policy_and_alerts(tmp_path):
    store = tmp_path / "brain.json"
    cfg = MultiAccountConfig(cost_budget_enabled=True, cost_budget_units=50.0,
                             cost_budget_window_seconds=3600.0,
                             max_run_duration_seconds=10_000.0)
    first = brain(config=cfg, store_path=store)
    first.start_run(now=NOW)
    first.record_account_outcome("acct-a", ok=True, cost_units=4.0)
    first.record_account_outcome("acct-b", ok=False, failure_kind="account_abnormal")
    first.on_failure([status("acct-b")], failed_ref="acct-b",
                     failure_kind="account_abnormal", attempt=1)
    first.observe(now=NOW)          # raises and persists an alert
    # Enough evidence for the policy chain to take one step.
    for _ in range(cfg.policy_min_samples):
        first.record_account_outcome("acct-b", ok=False, failure_kind="account_abnormal")

    document = json.loads(store.read_text(encoding="utf-8"))
    assert {"budget", "alerts", "policy", "watchdog", "cooldowns"} <= set(document)

    second = brain(config=cfg, store_path=store)
    assert second.budget_status()["spent_units"] == 4.0
    assert second.cooldowns.is_cooling("acct-b", now=NOW)
    assert second.alert_history()          # dedupe state survived
    assert second.policy_view()["version"] >= 1
    assert second.run_status(now=NOW)["attempts"] >= 1


def test_the_same_alert_is_not_re_paged_after_a_restart(tmp_path):
    store = tmp_path / "brain.json"
    cfg = MultiAccountConfig()

    def quotas(_snap):
        return {"acct-a": evidence(used=100.0)}

    first = brain(config=cfg, store_path=store, quotas=quotas)
    assert first.observe(now=NOW)["alerts"]
    second = brain(config=cfg, store_path=store, quotas=quotas)
    assert second.observe(now=NOW + 5)["alerts"] == []
