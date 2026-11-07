"""Pool read model, alert rules and the operator CLI."""
from __future__ import annotations

import json
import socket
import threading
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.multi_account import (
    MultiAccountConfig,
    MultiAccountOrchestrator,
    cli,
)
from reverse_agent.platform_v1.multi_account.alerts import (
    Alert,
    AlertLedger,
    evaluate_alerts,
    jsonl_sink,
)
from reverse_agent.platform_v1.multi_account.cooldowns import Cooldown
from reverse_agent.platform_v1.multi_account.pool_monitor import PoolMonitor, account_row
from reverse_agent.platform_v1.multi_account.status import (
    AccountHealth,
    AccountStatus,
    MultiAccountStatusMonitor,
    pool_account_quotas,
)

NOW = 1_800_000_000.0


def config(**overrides):
    return MultiAccountConfig(**overrides)


def status(ref="a", health=AccountHealth.HEALTHY, headroom=50.0):
    return AccountStatus(account_ref=ref, provider="codex", health=health, headroom_pct=headroom)


def row(ref="a", *, dispatchable=True, health="HEALTHY", cooldown=None):
    return {"account_ref": ref, "dispatchable": dispatchable, "health": health, "cooldown": cooldown}


def codes(alerts):
    return [(alert.code, alert.subject) for alert in alerts]


def brain(*, cooling=None, scores=None):
    cooling = cooling or {}
    return SimpleNamespace(
        _clock=lambda: NOW,
        cooldowns=SimpleNamespace(
            active_map=lambda now=None: {ref: item.until for ref, item in cooling.items()},
            get=cooling.get,
        ),
        account_scores=lambda: scores or {},
        routing=lambda: {"owner": "local"},
        account_policy_view=lambda: {"revision": 3},
    )


def monitor(**overrides):
    defaults = dict(
        config=config(),
        fetch_snapshot=lambda: None,
        stored_statuses=lambda: [status()],
        runtime_status=lambda: {},
        brain=brain,
        clock=lambda: NOW,
    )
    return PoolMonitor(**{**defaults, **overrides})


class TestAlertRules:
    def test_a_healthy_pool_raises_nothing(self):
        pool = {"source": "magpie", "accounts": [row("a"), row("b")]}
        assert evaluate_alerts(pool, {}, config(), now=NOW) == []

    def test_no_usable_account_is_critical_and_outranks_low_capacity(self):
        pool = {"source": "magpie", "accounts": [row("a", dispatchable=False)]}
        alerts = evaluate_alerts(pool, {}, config(), now=NOW)
        assert codes(alerts) == [("pool_no_usable_account", "pool")]
        assert alerts[0].severity == "critical"

    def test_low_capacity_follows_the_configured_threshold(self):
        pool = {"source": "magpie", "accounts": [row("a"), row("b", dispatchable=False)]}
        assert codes(evaluate_alerts(pool, {}, config(), now=NOW)) == [("pool_capacity_low", "pool")]
        assert evaluate_alerts(pool, {}, config(alert_min_usable_accounts=1), now=NOW) == []

    def test_account_conditions_name_the_account(self):
        pool = {"source": "magpie", "cooldowns": {"q": {"tier": "quarantine", "kind": "account_abnormal"}},
                "accounts": [
            row("q", dispatchable=False),
            row("x", dispatchable=False, health="EXHAUSTED"),
            row("y", dispatchable=False, health="ABNORMAL"),
            row("ok"), row("ok2"),
        ]}
        assert set(codes(evaluate_alerts(pool, {}, config(), now=NOW))) == {
            ("account_quarantined", "q"), ("account_exhausted", "x"), ("account_abnormal", "y")}

    def test_transient_cooldown_is_not_reported_as_quarantine(self):
        pool = {"source": "magpie", "accounts": [row("a"), row("b")],
                "cooldowns": {"a": {"tier": "transient", "kind": "task_failed"}}}
        assert evaluate_alerts(pool, {}, config(), now=NOW) == []

    def test_unavailable_perception_warns_without_claiming_the_pool_is_empty(self):
        alerts = evaluate_alerts({"source": "unavailable", "accounts": []}, {}, config(), now=NOW)
        assert codes(alerts) == [("perception_unavailable", "pool")]

    def test_no_configured_source_is_silent(self):
        assert evaluate_alerts({"source": "none", "accounts": []}, {}, config(), now=NOW) == []

    @pytest.mark.parametrize("remaining,expected", [
        (500, []),
        (100, [("window_budget_low", "cost")]),
        (0, [("window_budget_exhausted", "cost")]),
    ])
    def test_budget_alerts_read_the_enforced_window_budget(self, remaining, expected):
        runtime = {"budget": {"max_cost_micro_units": 1000, "remaining_cost_micro_units": remaining}}
        assert codes(evaluate_alerts({"source": "none"}, runtime, config(), now=NOW)) == expected

    def test_an_uncapped_budget_never_alerts(self):
        runtime = {"budget": {"max_cost_micro_units": None, "remaining_cost_micro_units": None}}
        assert evaluate_alerts({"source": "none"}, runtime, config(), now=NOW) == []

    def test_stopped_coordinator_only_matters_with_an_active_window(self):
        stopped = {"coordinator": {"lifecycle": "STOPPED"}}
        assert evaluate_alerts({"source": "none"}, stopped, config(), now=NOW) == []
        alerts = evaluate_alerts({"source": "none"}, {**stopped, "window": {"id": "w"}}, config(), now=NOW)
        assert codes(alerts) == [("coordinator_stopped", "coordinator")]

    def test_admission_holds_stay_distinct_per_reason(self):
        runtime = {"coordinator": {"admission_holds": ["quota_wait", "window_cost_budget_exhausted"]}}
        assert set(codes(evaluate_alerts({"source": "none"}, runtime, config(), now=NOW))) == {
            ("admission_hold", "quota_wait"), ("admission_hold", "window_cost_budget_exhausted")}

    def test_window_expiry_notice_is_skipped_for_a_renewing_window(self):
        # The renewal fact comes from the store; test_standing_window.py proves
        # it on a real window, because window records carry no renewal field.
        soon = time_in(1800)
        expiring = {"window": {"id": "w", "expires_at": soon}, "window_renews": False}
        assert codes(evaluate_alerts({"source": "none"}, expiring, config(), now=NOW)) == [("window_expiring", "w")]
        renewing = {"window": {"id": "w", "expires_at": soon}, "window_renews": True}
        assert evaluate_alerts({"source": "none"}, renewing, config(), now=NOW) == []


def time_in(seconds):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(NOW + seconds, tz=timezone.utc).isoformat()


class TestAlertLedger:
    ALERT = Alert("pool_capacity_low", "warning", "pool", "detail")

    def test_a_persisting_condition_is_raised_once_and_keeps_its_start(self):
        ledger = AlertLedger()
        assert [e["event"] for e in ledger.observe([self.ALERT], now=1)] == ["raised"]
        assert ledger.observe([self.ALERT], now=2) == []
        assert ledger.active()[0]["since"] == 1

    def test_a_cleared_condition_resolves_once(self):
        ledger = AlertLedger()
        ledger.observe([self.ALERT], now=1)
        assert [e["event"] for e in ledger.observe([], now=2)] == ["resolved"]
        assert ledger.active() == []
        assert ledger.observe([], now=3) == []

    def test_escalation_is_a_new_event_without_resetting_the_start(self):
        ledger = AlertLedger()
        ledger.observe([self.ALERT], now=1)
        worse = Alert("pool_capacity_low", "critical", "pool", "detail")
        assert [e["severity"] for e in ledger.observe([worse], now=2)] == ["critical"]
        assert ledger.active()[0]["since"] == 1

    def test_a_failing_sink_cannot_break_evaluation(self):
        def broken(_event):
            raise OSError("disk full")
        ledger = AlertLedger(broken)
        assert ledger.observe([self.ALERT], now=1)
        assert len(ledger.active()) == 1

    def test_the_jsonl_sink_rotates_within_its_bound(self, tmp_path):
        path = tmp_path / "logs" / "alerts.jsonl"
        write = jsonl_sink(path, max_bytes=10_000, backups=1)
        for index in range(600):
            write({"event": "raised", "index": index, "padding": "x" * 40})
        assert sum(item.stat().st_size for item in path.parent.iterdir()) < 25_000
        assert len(list(path.parent.iterdir())) == 2
        last = path.read_text(encoding="utf-8").splitlines()[-1]
        assert json.loads(last)["index"] == 599


class TestAccountRow:
    def test_an_active_cooldown_blocks_dispatch(self):
        cooling = {"until": NOW + 60, "kind": "task_failed", "tier": "transient", "streak": 1}
        result = account_row(status(), cooldown=cooling, score=None, now=NOW)
        assert result["dispatchable"] is False and result["cooldown"] == cooling

    def test_an_expired_cooldown_is_gone(self):
        result = account_row(status(), cooldown={"until": NOW - 1}, score=None, now=NOW)
        assert result["dispatchable"] is True and result["cooldown"] is None

    @pytest.mark.parametrize("health", [AccountHealth.STALE, AccountHealth.UNKNOWN,
                                        AccountHealth.EXHAUSTED, AccountHealth.ABNORMAL])
    def test_only_usable_health_is_dispatchable(self, health):
        assert account_row(status(health=health), cooldown=None, score=None, now=NOW)["dispatchable"] is False

    def test_raw_upstream_evidence_stays_host_side(self):
        evidence = AccountStatus(account_ref="a", health=AccountHealth.HEALTHY, raw={"secret": "x"})
        assert "raw" not in account_row(evidence, cooldown=None, score=None, now=NOW)


def snapshot(*accounts):
    return {"status": "available", "accounts": list(accounts)}


def magpie_account(provider, *, state="FRESH", windows=(), reason=None, ref=None):
    return {"account_ref": ref or f"{provider}:1", "provider": provider, "state": state, "reason": reason,
            "windows": list(windows), "observed_at": "2027-01-15T08:00:00+00:00"}


class TestDiagnosticProjection:
    NOW = datetime(2027, 1, 15, 8, 1, tzinfo=timezone.utc).timestamp()

    def statuses(self, *accounts):
        monitor_ = MultiAccountStatusMonitor(config(), clock=lambda: self.NOW)
        return {s.account_ref: s for s in monitor_.diagnose(snapshot(*accounts))}

    def test_keeps_accounts_no_route_claims(self):
        view = self.statuses(magpie_account("codex"), magpie_account("workbuddy"), magpie_account("trae-cn"))
        assert set(view) == {"codex:1", "workbuddy:1", "trae-cn:1"}

    def test_the_admission_projection_still_excludes_them(self):
        pooled = pool_account_quotas(snapshot(
            magpie_account("codex", windows=[{"name": "5 hours", "used_percent": 1}]),
            magpie_account("workbuddy", windows=[{"name": "Credits", "used_percent": 1}])))
        assert set(pooled) == {"codex:1"}

    def test_judges_fresh_windows(self):
        view = self.statuses(
            magpie_account("codex", windows=[{"name": "5 hours", "used_percent": 100, "unlimited": False}]),
            magpie_account("claude", windows=[{"name": "7 days", "used_percent": 52, "unlimited": False}]))
        assert view["codex:1"].health is AccountHealth.EXHAUSTED
        assert view["claude:1"].health is AccountHealth.HEALTHY
        assert view["claude:1"].headroom_pct == 48

    def test_magpie_stale_and_unknown_verdicts_stand(self):
        view = self.statuses(magpie_account("a", state="STALE", reason="stale_reading"),
                             magpie_account("b", state="UNKNOWN", reason="quota_error"))
        assert view["a:1"].health is AccountHealth.STALE and "stale_reading" in view["a:1"].anomaly_flags
        assert view["b:1"].health is AccountHealth.UNKNOWN

    def test_parses_iso_reset_times_for_the_next_reset(self):
        view = self.statuses(magpie_account("a", windows=[
            {"name": "w", "used_percent": 5, "resets_at": "2027-01-15T09:00:00+00:00"}]))
        assert view["a:1"].public_view()["next_reset_at"] == self.NOW + 59 * 60

    def test_unidentified_accounts_stay_distinct(self):
        first, second = magpie_account("a", state="STALE"), magpie_account("a", state="STALE")
        first["account_ref"] = second["account_ref"] = None
        assert set(self.statuses(first, second)) == {"a:unidentified:1", "a:unidentified:2"}

    def test_a_window_past_its_reset_does_not_constrain_the_account(self):
        view = self.statuses(magpie_account("a", windows=[
            {"name": "w", "used_percent": 100, "resets_at": "2027-01-15T07:00:00+00:00"}]))
        assert view["a:1"].health is AccountHealth.HEALTHY

    def test_one_malformed_account_does_not_empty_the_pool(self):
        view = self.statuses(magpie_account("a", windows=[{"name": "w", "used_percent": "bad"}]),
                             magpie_account("b"))
        assert view["a:1"].health is AccountHealth.UNKNOWN and "perception_error" in view["a:1"].anomaly_flags
        assert "b:1" in view

    def test_marks_which_accounts_feed_admission(self):
        rows = monitor(fetch_snapshot=lambda: snapshot(magpie_account("codex"), magpie_account("workbuddy")),
                       clock=lambda: self.NOW).refresh()["accounts"]
        assert {r["provider"]: r["admission_evidence"] for r in rows} == {"codex": True, "workbuddy": False}


class TestPoolMonitor:
    def test_joins_perception_cooldowns_scores_and_policy(self):
        item = Cooldown("a", until=NOW + 60, kind="account_abnormal", streak=1, tier="quarantine")
        view = monitor(
            stored_statuses=lambda: [status("a"), status("b")],
            brain=lambda: brain(cooling={"a": item}, scores={"b": {"attempts": 4}}),
        ).refresh()
        rows = {r["account_ref"]: r for r in view["accounts"]}
        assert view["source"] == "observations"
        assert rows["a"]["cooldown"]["tier"] == "quarantine"
        assert rows["b"]["score"] == {"attempts": 4}
        assert view["summary"]["dispatchable_accounts"] == 1
        assert view["summary"]["cooling_accounts"] == 1
        assert view["policy"] == {"revision": 3}
        assert [a["code"] for a in view["alerts"]["active"]] == ["account_quarantined", "pool_capacity_low"]

    def test_lists_dispatchable_accounts_first(self):
        view = monitor(stored_statuses=lambda: [
            status("stale", AccountHealth.STALE), status("low", headroom=10), status("high", headroom=90),
        ]).refresh()
        assert [r["account_ref"] for r in view["accounts"]] == ["high", "low", "stale"]

    def test_a_failed_read_does_not_fake_a_resolution(self, tmp_path):
        path = tmp_path / "alerts.jsonl"
        item = Cooldown("a", until=NOW + 600, kind="account_abnormal", streak=1, tier="quarantine")
        reads = iter([snapshot(magpie_account("codex", ref="a")), {"status": "refused"},
                      snapshot(magpie_account("codex", ref="a"))])
        pool = monitor(config=config(alert_log_path=path), persist_alerts=True, fetch_snapshot=lambda: next(reads),
                       brain=lambda: brain(cooling={"a": item}), clock=lambda: NOW)
        pool.refresh()
        degraded = pool.refresh()
        assert degraded["source"] == "unavailable" and len(degraded["accounts"]) == 1
        pool.refresh()
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        quarantine = [e["event"] for e in events if e["code"] == "account_quarantined"]
        assert quarantine == ["raised"]

    def test_a_cooldown_with_no_observed_account_is_still_reported(self):
        item = Cooldown("connection-1", until=NOW + 60, kind="account_abnormal", streak=1, tier="quarantine")
        view = monitor(brain=lambda: brain(cooling={"connection-1": item})).refresh()
        assert view["summary"]["cooling_accounts"] == 1
        alert = next(a for a in view["alerts"]["active"] if a["code"] == "account_quarantined")
        assert alert["subject"] == "connection-1"

    @staticmethod
    def unreadable_ledger(cooling):
        """Registry readable, ledger not: the shape of a corrupted store file."""
        def broken():
            raise ValueError("corrupt ledger")
        fake = brain(cooling=cooling)
        fake.account_scores = broken
        fake.account_policy_view = broken
        return fake

    def test_an_unreadable_ledger_still_reports_a_new_quarantine_and_says_so(self):
        item = Cooldown("a", until=NOW + 60, kind="account_abnormal", streak=1, tier="quarantine")
        view = monitor(brain=lambda: self.unreadable_ledger({"a": item})).refresh()
        assert {"account_quarantined", "feedback_unavailable"} <= {a["code"] for a in view["alerts"]["active"]}

    def test_an_unreadable_ledger_does_not_freeze_an_expired_quarantine(self):
        clock = {"now": NOW}
        cooling = {"a": Cooldown("a", until=NOW + 60, kind="account_abnormal", streak=1, tier="quarantine")}
        pool = monitor(brain=lambda: self.unreadable_ledger(cooling), clock=lambda: clock["now"])
        pool.refresh()
        cooling.clear()
        clock["now"] += 61
        view = pool.refresh()
        assert "account_quarantined" not in [a["code"] for a in view["alerts"]["active"]]
        assert view["summary"]["cooling_accounts"] == 0

    def test_a_remembered_quarantine_expires_when_the_brain_is_gone(self):
        clock = {"now": NOW}
        item = Cooldown("a", until=NOW + 60, kind="account_abnormal", streak=1, tier="quarantine")
        healthy = iter([brain(cooling={"a": item})])

        def flaky():
            try:
                return next(healthy)
            except StopIteration:
                raise RuntimeError("store busy") from None

        pool = monitor(brain=flaky, clock=lambda: clock["now"])
        pool.refresh()
        codes_ = [a["code"] for a in pool.refresh()["alerts"]["active"]]
        assert "account_quarantined" in codes_ and "feedback_unavailable" in codes_
        clock["now"] += 61
        assert "account_quarantined" not in [a["code"] for a in pool.refresh()["alerts"]["active"]]

    def test_last_known_rows_stop_claiming_health_past_the_freshness_budget(self):
        clock = {"now": NOW}
        pool = monitor(clock=lambda: clock["now"])
        pool._perceive = lambda: ("magpie", [status("a")])
        pool.refresh()
        pool._perceive = lambda: ("unavailable", [])
        assert pool.refresh()["accounts"][0]["health"] == "HEALTHY"
        clock["now"] += pool._config.observation_freshness_seconds + 1
        row_ = pool.refresh()["accounts"][0]
        assert row_["health"] == "STALE" and row_["dispatchable"] is False

    def test_a_failed_runtime_read_keeps_its_alerts_and_says_so(self):
        runtime = iter([{"coordinator": {"last_error": "boom"}}])

        def flaky():
            try:
                return next(runtime)
            except StopIteration:
                raise RuntimeError("store closed") from None

        pool = monitor(runtime_status=flaky)
        pool.refresh()
        active = {a["code"] for a in pool.refresh()["alerts"]["active"]}
        assert {"coordinator_error", "runtime_status_unavailable"} <= active

    def test_time_asleep_does_not_count_as_a_stall(self):
        clock = {"now": NOW}
        runtime = {"coordinator": {"lifecycle": "RUNNING", "ticks": 5}}
        pool = monitor(config=config(alert_stall_seconds=60), runtime_status=lambda: runtime,
                       clock=lambda: clock["now"], stored_statuses=lambda: [])
        pool.refresh()
        clock["now"] += 3600
        assert pool.refresh()["alerts"]["active"] == []

    def test_a_failed_snapshot_reports_unavailable_rather_than_an_empty_pool(self):
        def boom():
            raise OSError("http://secret/url")
        view = monitor(fetch_snapshot=boom).refresh()
        assert view["source"] == "unavailable"
        assert "secret" not in json.dumps(view)

    def test_a_refused_snapshot_reports_unavailable(self):
        assert monitor(fetch_snapshot=lambda: {"status": "refused"}).refresh()["source"] == "unavailable"

    def test_an_unavailable_brain_does_not_hide_perception(self):
        def broken():
            raise RuntimeError("no brain")
        view = monitor(brain=broken).refresh()
        assert len(view["accounts"]) == 1 and view["policy"] == {}

    def test_a_failing_runtime_source_does_not_break_the_view(self):
        def broken():
            raise RuntimeError("store closed")
        assert monitor(runtime_status=broken).refresh()["budget"] is None

    def test_detects_a_coordinator_that_stopped_finishing_ticks(self):
        clock = {"now": NOW}
        runtime = {"coordinator": {"lifecycle": "RUNNING", "ticks": 5}}
        pool = monitor(config=config(alert_stall_seconds=60), runtime_status=lambda: runtime,
                       clock=lambda: clock["now"], stored_statuses=lambda: [])
        pool.refresh()
        clock["now"] += 30
        pool.refresh()
        clock["now"] += 31
        assert [a["code"] for a in pool.refresh()["alerts"]["active"]] == ["coordinator_stalled"]
        runtime["coordinator"]["ticks"] = 6
        assert pool.refresh()["alerts"]["active"] == []

    def test_view_uses_the_cache_inside_the_interval(self):
        calls = []
        pool = monitor(stored_statuses=lambda: calls.append(1) or [status()])
        pool.view()
        pool.view()
        assert len(calls) == 1

    def test_the_thread_keeps_observing_after_a_source_fails(self):
        seen = threading.Event()
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) >= 2:
                seen.set()
            raise OSError("down")

        pool = monitor(fetch_snapshot=flaky, clock=time.time)
        pool._config = SimpleNamespace(**{**pool._config.model_dump(), "alert_interval_seconds": 0.01})
        pool.start()
        try:
            assert seen.wait(5)
        finally:
            pool.stop()
        assert pool._thread is None

    def test_persists_transitions_only_when_asked(self, tmp_path):
        path = tmp_path / "alerts.jsonl"
        pool = monitor(config=config(alert_log_path=path), persist_alerts=True,
                       stored_statuses=lambda: [status(health=AccountHealth.STALE)])
        pool.refresh()
        pool.refresh()
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert [(e["event"], e["code"]) for e in events] == [("raised", "pool_no_usable_account")]


class TestCli:
    @pytest.fixture
    def env(self, tmp_path, monkeypatch):
        store = tmp_path / "store.json"
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_STORE", str(store))
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ALERT_LOG_PATH", str(tmp_path / "alerts.jsonl"))
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_POLICY_EVOLUTION", "1")
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_ACCOUNT_SCORING", "1")
        return tmp_path

    def test_policy_prints_the_effective_view(self, env, capsys):
        assert cli.main(["policy"]) == 0
        view = json.loads(capsys.readouterr().out)
        assert view["revision"] == 0 and "effective" in view

    def test_alerts_reads_the_log_tail_and_skips_corrupt_lines(self, env, capsys):
        (env / "alerts.jsonl").write_text('{"code":"a"}\nnot json\n{"code":"b"}\n', encoding="utf-8")
        assert cli.main(["alerts", "--limit", "2"]) == 0
        assert [e["code"] for e in json.loads(capsys.readouterr().out)] == ["b"]

    def test_alerts_with_no_log_is_empty(self, env, capsys):
        assert cli.main(["alerts"]) == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_host_check_treats_any_listener_as_running(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            assert cli._host_running(f"http://127.0.0.1:{port}") is True
        assert cli._host_running(f"http://127.0.0.1:{port}") is False

    def test_host_check_accepts_a_target_without_a_scheme(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(8)
            assert cli._host_running(f"127.0.0.1:{listener.getsockname()[1]}") is True

    def test_host_check_fails_closed_on_an_ambiguous_error(self, monkeypatch):
        def timeout(*_args, **_kwargs):
            raise TimeoutError
        monkeypatch.setattr(cli.socket, "create_connection", timeout)
        assert cli._host_running("http://127.0.0.1:8766") is True

    def test_the_default_target_follows_the_configured_port(self, monkeypatch):
        monkeypatch.delenv("REVERSE_AGENT_TASK_API", raising=False)
        monkeypatch.setenv("REVERSE_AGENT_TASK_SERVICE_PORT", "9001")
        assert cli._default_task_api() == "http://127.0.0.1:9001"

    def test_rollback_refuses_while_a_host_is_running(self, env, monkeypatch, capsys):
        monkeypatch.setattr(cli, "_host_running", lambda _url: True)
        assert cli.main(["rollback", "--target", "0", "--expected-revision", "0"]) == 2
        assert "host_running" in capsys.readouterr().err

    def test_rollback_refuses_a_stale_revision(self, env, monkeypatch, capsys):
        monkeypatch.setattr(cli, "_host_running", lambda _url: False)
        assert cli.main(["rollback", "--target", "0", "--expected-revision", "9"]) == 1
        assert "rollback_refused" in capsys.readouterr().err

    def test_rollback_restores_an_earlier_version_as_a_new_revision(self, env, monkeypatch, capsys):
        monkeypatch.setattr(cli, "_host_running", lambda _url: False)
        settings = MultiAccountConfig.from_env()
        brain_ = MultiAccountOrchestrator(settings, store_path=settings.break_even_store_path)
        for index in range(settings.policy_min_new_attempts + 1):
            brain_.record_account_outcome("acct", ok=False, failure_kind="account_abnormal",
                                          outcome_id=f"o{index}", wall_seconds=1.0, cost_units=1.0)
        revision = brain_.account_policy_view()["revision"]
        assert revision >= 1
        assert cli.main(["rollback", "--target", "0", "--expected-revision", str(revision)]) == 0
        capsys.readouterr()
        fresh = MultiAccountOrchestrator(settings, store_path=settings.break_even_store_path)
        view = fresh.account_policy_view()
        assert view["revision"] == revision + 1
        assert view["effective"]["reliability_weight"] == settings.reliability_weight


class TestHostLifecycle:
    @staticmethod
    def host(tmp_path, monkeypatch):
        import reverse_agent.model_access.credential_relay as relay_module
        import reverse_agent.platform_v1.trusted_host as host_module
        from reverse_agent.model_access.store import ModelProfileStore
        from reverse_agent.platform_v1.run_store import TaskStore

        class Server:
            def __init__(self, address=("127.0.0.1", 8765), handler=None):
                self.server_address = address
                self.RequestHandlerClass = handler

            def serve_forever(self):
                pass

            def shutdown(self):
                pass

            def server_close(self):
                pass

        monkeypatch.setattr(host_module, "ThreadingHTTPServer", Server)
        monkeypatch.setattr(relay_module, "run_credential_relay_server", lambda **kw: Server())
        task_store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
        host = host_module.CombinedTrustedHost(store=ModelProfileStore(), task_store=task_store,
                                               auth_list_probe=lambda: {})
        return host, task_store

    def test_the_monitor_thread_runs_only_when_the_brain_is_enabled(self, tmp_path, monkeypatch):
        monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", raising=False)
        monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
        host, task_store = self.host(tmp_path, monkeypatch)
        try:
            host.start(coordinator_paused=True)
            assert host._pool_monitor._thread is None
            assert host._pool_monitor.view()["monitoring"] is False
        finally:
            host.stop()
            task_store._conn.close()

    def test_the_monitor_stops_with_the_host_and_writes_no_admission_row(self, tmp_path, monkeypatch):
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_STORE", str(tmp_path / "store.json"))
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ALERT_LOG_PATH", str(tmp_path / "alerts.jsonl"))
        monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
        host, task_store = self.host(tmp_path, monkeypatch)
        try:
            host.start(coordinator_paused=True)
            monitor_ = host._pool_monitor
            thread = monitor_._thread
            assert thread is not None and thread.is_alive()
            monitor_.refresh()
            rows = task_store._conn.execute("SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0]
            assert rows == 0
        finally:
            host.stop()
            task_store._conn.close()
        assert not thread.is_alive()
        assert host._pool_monitor is None
