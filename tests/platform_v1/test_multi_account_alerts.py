"""Alert rules, de-duplication and bounded history.

An unattended run cannot page a human for every observation, so the engine must
emit once per condition, count repeats, and keep a bounded trail.
"""
import json

from reverse_agent.platform_v1.multi_account.alerts import AlertEngine, AlertSeverity
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus

NOW = 1_700_000_000.0


def engine(**overrides):
    config = MultiAccountConfig(**overrides)
    clock = lambda: NOW  # noqa: E731
    return AlertEngine(config, clock=clock)


def status(ref, health, *, headroom=None, flags=()):
    return AccountStatus(account_ref=ref, provider="codex", health=health,
                         headroom_pct=headroom, anomaly_flags=list(flags))


HEALTHY = status("ok", AccountHealth.HEALTHY, headroom=80.0)


def codes(alerts):
    return [alert.code for alert in alerts]


# --- account / pool rules ----------------------------------------------------

def test_exhausted_and_abnormal_accounts_raise_distinct_alerts():
    alerts = engine().evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0),
                                status("b", AccountHealth.ABNORMAL)], now=NOW)
    assert codes(alerts) == ["account_exhausted", "account_abnormal"]
    severities = {alert.code: alert.severity for alert in alerts}
    assert severities["account_abnormal"] is AlertSeverity.ERROR
    assert severities["account_exhausted"] is AlertSeverity.WARNING


def test_all_accounts_exhausted_is_critical():
    alerts = engine().evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0),
                                status("b", AccountHealth.EXHAUSTED, headroom=0.0)], now=NOW)
    assert "all_accounts_exhausted" in codes(alerts)
    pool = next(a for a in alerts if a.code == "all_accounts_exhausted")
    assert pool.severity is AlertSeverity.CRITICAL


def test_healthy_pool_raises_nothing():
    assert engine().evaluate([status("a", AccountHealth.HEALTHY, headroom=80.0)],
                             now=NOW) == []


def test_empty_observation_is_an_error_not_silence():
    alerts = engine().evaluate([], now=NOW)
    assert codes(alerts) == ["no_accounts_observed"]


def test_fully_stale_pool_warns_about_perception():
    alerts = engine().evaluate([status("a", AccountHealth.STALE),
                                status("b", AccountHealth.STALE)], now=NOW)
    assert "perception_stale" in codes(alerts)


# --- de-duplication ----------------------------------------------------------

def test_repeat_is_suppressed_then_counted():
    eng = engine(alert_quiet_seconds=300.0)
    first = eng.evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0)], now=NOW)
    assert len(first) == 1
    assert eng.evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0)],
                        now=NOW + 10) == []
    assert eng.evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0)],
                        now=NOW + 20) == []

    later = eng.evaluate([status("a", AccountHealth.EXHAUSTED, headroom=0.0)], now=NOW + 400)
    assert len(later) == 1
    assert later[0].repeats == 3   # one emission + two suppressed repeats


def test_drain_returns_pending_once():
    eng = engine()
    eng.evaluate([status("a", AccountHealth.ABNORMAL)], now=NOW)
    assert len(eng.drain()) == 1
    assert eng.drain() == []


def test_history_is_bounded():
    eng = engine(alert_max_history=3, alert_quiet_seconds=0.0)
    for index in range(6):
        eng.evaluate([status(f"a{index}", AccountHealth.ABNORMAL)], now=NOW + index)
    assert len(eng.history()) == 3


# --- budget / cooldown / reliability rules -----------------------------------

def test_budget_rules_report_soft_cap_and_exhaustion():
    eng = engine()
    soft = eng.evaluate([HEALTHY], budget={"enforced": True, "utilization": 0.85,
                                   "spent_units": 8.5, "cap_units": 10.0,
                                   "remaining_units": 1.5}, now=NOW)
    assert codes(soft) == ["cost_budget_soft_cap"]
    hard = eng.evaluate([HEALTHY], budget={"enforced": True, "utilization": 1.0,
                                    "spent_units": 10.0, "cap_units": 10.0,
                                    "remaining_units": 0.0}, now=NOW)
    assert codes(hard) == ["cost_budget_exhausted"]


def test_ungoverned_budget_raises_nothing():
    assert engine().evaluate([HEALTHY], budget={"enforced": False, "utilization": 5.0}, now=NOW) == []


def test_flapping_account_warns_after_the_streak_threshold():
    alerts = engine(alert_failure_streak_threshold=2).evaluate(
        [HEALTHY], cooldowns={"a": (2, "quota_exhausted")}, now=NOW)
    assert codes(alerts) == ["account_flapping"]
    assert alerts[0].evidence["streak"] == 2


def test_unreliable_account_requires_enough_samples():
    eng = engine(alert_min_samples=3, alert_min_success_rate=0.6)
    early = eng.evaluate([HEALTHY], account_scores={"a": {"reliability": 0.1, "attempts": 1}}, now=NOW)
    assert codes(early) == []
    late = eng.evaluate([HEALTHY], account_scores={"a": {"reliability": 0.1, "attempts": 5}}, now=NOW)
    assert codes(late) == ["account_unreliable"]


# --- host events / run state -------------------------------------------------

def test_host_event_keeps_its_own_severity():
    alerts = engine().evaluate([HEALTHY], events=[{
        "code": "task_dead_letter", "severity": "error", "subject": "a",
        "message": "reroutes exhausted", "evidence": {"attempt": 3}}], now=NOW)
    assert alerts[0].code == "task_dead_letter"
    assert alerts[0].severity is AlertSeverity.ERROR
    assert alerts[0].evidence["attempt"] == 3


def test_run_verdict_becomes_an_alert_only_when_it_stops():
    eng = engine()
    assert eng.evaluate([HEALTHY], run_state={"action": "continue"}, now=NOW) == []
    conclude = eng.evaluate([HEALTHY], run_state={"action": "conclude", "reason": "run_deadline_reached"},
                            now=NOW)
    assert conclude[0].code == "run_conclude"
    assert conclude[0].severity is AlertSeverity.WARNING


def test_disabled_engine_is_silent():
    assert engine(alerts_enabled=False).evaluate(
        [status("a", AccountHealth.ABNORMAL)], now=NOW) == []


# --- persistence -------------------------------------------------------------

def test_sink_receives_every_emitted_alert():
    seen = []
    config = MultiAccountConfig()
    eng = AlertEngine(config, clock=lambda: NOW, sink=seen.append)
    eng.evaluate([status("a", AccountHealth.ABNORMAL), HEALTHY], now=NOW)
    assert [alert.code for alert in seen] == ["account_abnormal"]


def test_a_failing_sink_does_not_break_evaluation():
    def boom(_alert):
        raise RuntimeError("sink down")

    config = MultiAccountConfig()
    eng = AlertEngine(config, clock=lambda: NOW, sink=boom)
    assert len(eng.evaluate([status("a", AccountHealth.ABNORMAL)], now=NOW)) == 1


def test_history_and_suppression_survive_a_restart(tmp_path):
    path = tmp_path / "alerts.json"
    config = MultiAccountConfig()
    first = AlertEngine(config, clock=lambda: NOW,
                        persist=lambda snap: path.write_text(json.dumps(snap), encoding="utf-8"))
    first.evaluate([status("a", AccountHealth.ABNORMAL)], now=NOW)

    restored = AlertEngine(config, clock=lambda: NOW,
                           state=json.loads(path.read_text(encoding="utf-8")))
    assert [row["code"] for row in restored.history()] == ["all_accounts_abnormal"]
    # Still inside the quiet window: must not re-page on restart.
    assert restored.evaluate([status("a", AccountHealth.ABNORMAL)], now=NOW + 10) == []


def test_a_host_event_does_not_fabricate_an_empty_pool_alert():
    # `None` means "not reporting on the pool"; only an explicit empty list
    # means "observed nothing". Mixing them made every policy change page an
    # operator about a pool that had never been observed in that call.
    eng = engine()
    alerts = eng.evaluate(events=[{"code": "policy_changed", "severity": "info"}], now=NOW)
    assert codes(alerts) == ["policy_changed"]
    assert codes(eng.evaluate([], now=NOW + 1)) == ["no_accounts_observed"]


# --- partial observability ---------------------------------------------------

def test_a_materially_unobservable_pool_warns_once():
    """Real machine: 4 of 11 accounts unobservable while the rest were healthy.

    The pool-level "everything is stale" rule cannot see that, so capacity that
    never appears stayed silent. A quarter of the pool missing is worth one line.
    """
    statuses = [status("a", AccountHealth.HEALTHY, headroom=90.0),
                status("b", AccountHealth.HEALTHY, headroom=80.0),
                status("c", AccountHealth.STALE),
                status("d", AccountHealth.UNKNOWN)]
    alerts = engine().evaluate(statuses, now=NOW)
    assert codes(alerts) == ["perception_partial"]
    assert alerts[0].severity is AlertSeverity.WARNING
    assert alerts[0].evidence["usable"] == 2
    assert alerts[0].evidence["total"] == 4


def test_one_stale_account_in_a_large_pool_does_not_page():
    """Noise floor: a single stale account among many is normal and stays quiet."""
    statuses = [status(f"ok{index}", AccountHealth.HEALTHY, headroom=80.0)
                for index in range(9)] + [status("stale", AccountHealth.STALE)]
    assert codes(engine().evaluate(statuses, now=NOW)) == []


def test_the_partial_alert_is_deduplicated_like_every_other():
    statuses = [status("a", AccountHealth.HEALTHY, headroom=90.0),
                status("b", AccountHealth.STALE),
                status("c", AccountHealth.UNKNOWN)]
    bot = engine()
    assert codes(bot.evaluate(statuses, now=NOW)) == ["perception_partial"]
    assert codes(bot.evaluate(statuses, now=NOW + 5)) == []
