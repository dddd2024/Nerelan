"""Weekly quota pacing: a subscription allowance must last its week."""
from __future__ import annotations

import json

import pytest

from reverse_agent.platform_v1.model_router import (
    WEEK_SECONDS,
    ModelSelectionError,
    weekly_pace_hold,
)
from reverse_agent.platform_v1.routing_inputs import (
    DEFAULT_WEEKLY_PACE,
    read_overrides,
    weekly_pace_config,
)
from tests.platform_v1.test_model_router import candidate, choose

NOW = 1_800_000_000.0
PACE = dict(DEFAULT_WEEKLY_PACE)


def paced(elapsed, used, *, need=.02, executor="codex", cost="subscription", ref="sub", model="gpt-6-sol"):
    """A subscription candidate `elapsed` of the way through its week with `used` spent."""
    return candidate(ref, model, cost, executor, weekly_headroom=1 - used, task_weekly_fraction=need,
                     weekly_resets_at=NOW + WEEK_SECONDS * (1 - elapsed))


class TestHold:
    def test_on_pace_is_allowed(self):
        assert weekly_pace_hold(paced(.5, .45), now=NOW, pace=PACE) is None

    def test_ahead_of_the_calendar_waits_until_the_line_catches_up(self):
        # The live Codex reading on 2026-11-07: 74% spent, 47.9% of the week gone.
        row = paced(.479, .74, need=.03)
        start = row["weekly_resets_at"] - WEEK_SECONDS
        assert weekly_pace_hold(row, now=NOW, pace=PACE) == pytest.approx(start + WEEK_SECONDS * (.74 + .03 - .10))

    def test_the_live_claude_reading_still_has_room(self):
        assert weekly_pace_hold(paced(.775, .69, executor="claude_code", model="sonnet"), now=NOW, pace=PACE) is None

    def test_the_reserve_holds_until_the_reset_even_late_in_the_week(self):
        row = paced(.99, .88, need=.03)
        assert weekly_pace_hold(row, now=NOW, pace=PACE) == row["weekly_resets_at"]

    def test_unknown_need_uses_the_uncalibrated_median(self):
        assert weekly_pace_hold(paced(.5, .57, need=None), now=NOW, pace=PACE) is None
        assert weekly_pace_hold(paced(.5, .58, need=None), now=NOW, pace=PACE) is not None

    @pytest.mark.parametrize("missing", ["weekly_headroom", "weekly_resets_at"])
    def test_unknown_usage_or_reset_makes_no_claim(self, missing):
        row = paced(.1, .9)
        row[missing] = None
        assert weekly_pace_hold(row, now=NOW, pace=PACE) is None

    def test_only_paced_subscription_executors_are_held(self):
        assert weekly_pace_hold(paced(.1, .9, executor="opencode"), now=NOW, pace=PACE) is None
        assert weekly_pace_hold(paced(.1, .9, cost="free"), now=NOW, pace=PACE) is None
        assert weekly_pace_hold(paced(.1, .9), now=NOW, pace={**PACE, "enabled": False}) is None
        assert weekly_pace_hold(paced(.1, .9), now=NOW, pace=None) is None

    def test_slack_and_reserve_are_owner_knobs(self):
        row = paced(.5, .62)
        assert weekly_pace_hold(row, now=NOW, pace=PACE) is not None
        assert weekly_pace_hold(row, now=NOW, pace={**PACE, "slack": .2}) is None


class TestRouter:
    def test_routes_around_a_paced_account(self):
        pool = [paced(.479, .74), candidate("free", "kimi-k3")]
        decision = choose(pool, difficulty=4, now=NOW, weekly_pace=PACE)
        assert decision["binding_ref"] == "free"
        held = next(row for row in decision["excluded_candidates"] if row["binding_id"] == "sub")
        assert held["filter"] == "weekly_pace" and held["retry_at"] > NOW

    def test_a_fully_paced_pool_is_a_temporary_wait_with_a_retry_time(self):
        with pytest.raises(ModelSelectionError) as caught:
            choose([paced(.479, .74)], difficulty=4, now=NOW, weekly_pace=PACE)
        assert caught.value.decision["temporary_resource_blocked"] is True
        assert caught.value.decision["retry_at"] > NOW

    def test_a_validated_codex_reset_announcement_drains_instead(self):
        row = paced(.479, .74)
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": NOW + 86400}
        decision = choose([row], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)
        assert decision["binding_ref"] == "sub"

    def test_an_unvalidated_announcement_does_not_lift_pacing(self):
        signal = {"state": "PLAN_ONLY", "validated": False, "expected_reset_at": NOW + 86400}
        with pytest.raises(ModelSelectionError):
            choose([paced(.479, .74)], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)

    def test_claude_is_never_drained_by_a_codex_announcement(self):
        row = paced(.2, .6, executor="claude_code", model="sonnet")
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": NOW + 86400}
        with pytest.raises(ModelSelectionError):
            choose([row], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)

    def test_pacing_is_off_when_the_caller_passes_no_policy(self):
        assert choose([paced(.479, .74)], difficulty=4, now=NOW)["binding_ref"] == "sub"


class TestOwnerConfig:
    def write(self, tmp_path, payload):
        state = tmp_path / "model_setup_state.json"
        (tmp_path / "model_routing_overrides.json").write_text(json.dumps(payload), encoding="utf-8")
        return state

    def test_defaults_apply_without_an_override(self):
        assert weekly_pace_config({}) == DEFAULT_WEEKLY_PACE
        assert DEFAULT_WEEKLY_PACE["enabled"] is True
        assert set(DEFAULT_WEEKLY_PACE["executors"]) == {"codex", "claude_code"}

    def test_overrides_merge_onto_defaults(self, tmp_path):
        data = read_overrides(self.write(tmp_path, {"weekly_pace": {"slack": .2}}))
        assert weekly_pace_config(data) == {**DEFAULT_WEEKLY_PACE, "slack": .2}

    @pytest.mark.parametrize("pace", [
        {"slack": .9}, {"reserve": -.1}, {"enabled": "yes"}, {"executors": "codex"},
        {"executors": [""]}, {"unknown": 1}, [],
    ])
    def test_invalid_overrides_are_refused(self, tmp_path, pace):
        with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
            read_overrides(self.write(tmp_path, {"weekly_pace": pace}))


class TestHostWiring:
    """The host must feed the router the weekly reset time and the Owner policy.

    The Codex reset rule sat unwired in main because nothing passed its input;
    these tests fail if pacing ever ends up in the same state.
    """

    @staticmethod
    def host(monkeypatch, weekly_used, weekly_resets_in):
        from tests.platform_v1 import test_magpie_account_quota_wiring as wiring
        account = wiring._account("acct-a", 10.0, weekly=weekly_used)
        account["windows"][1]["resets_at"] = wiring._iso(wiring.time.time() + weekly_resets_in)
        h = wiring._accounts_host(monkeypatch, wiring._snapshot(account), {"conn-a": "acct-a"})
        for name, value in (("_routing_refresh_quota_for_signal", lambda: {"state": "UNKNOWN"}),
                            ("_routing_bind_discovered", lambda: None), ("_usage_profiles", lambda: {}),
                            ("_routing_model_metadata", lambda: {}), ("_routing_paid_allowed", lambda *a: False),
                            ("_routing_availability_history", lambda: {}),
                            ("_routing_probe_window_allowed", lambda goal: False),
                            ("_routing_availability", lambda *a, **k: {"state": "AVAILABLE", "reason": "fixture"})):
            monkeypatch.setattr(h.host, name, value)
        return wiring, h

    def test_candidates_carry_the_weekly_reset_and_calls_carry_the_policy(self, monkeypatch):
        wiring, h = self.host(monkeypatch, 30.0, 3 * 86400)
        seen = []

        def select(candidates, **kwargs):
            seen.append((candidates, kwargs))
            return {"binding_ref": candidates[0]["binding_id"]}

        monkeypatch.setattr(wiring.model_router, "select_model", select)
        wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=3))
        candidates, kwargs = seen[-1]
        assert candidates[0]["weekly_resets_at"] == pytest.approx(wiring.time.time() + 3 * 86400, abs=10)
        assert kwargs["weekly_pace"] == DEFAULT_WEEKLY_PACE

    def test_a_real_route_waits_for_an_account_spent_ahead_of_its_week(self, monkeypatch):
        wiring, h = self.host(monkeypatch, 80.0, 6 * 86400)
        with pytest.raises(wiring.TaskStoreError) as caught:
            wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=3))
        decision = caught.value.decision
        assert decision["temporary_resource_blocked"] is True
        assert [row["filter"] for row in decision["excluded_candidates"]] == ["weekly_pace"]


class TestPoolView:
    def status(self, provider, used, resets_in):
        from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus, WindowStatus
        return AccountStatus(account_ref=f"{provider}:1", provider=provider, health=AccountHealth.HEALTHY,
                             windows=[WindowStatus(window="7 days", used_percent=used, resets_at=NOW + resets_in)])

    def test_shows_the_same_hold_the_router_applies(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        state = pace_state(self.status("codex", 74, WEEK_SECONDS * .521), PACE, NOW)
        assert state["used"] == pytest.approx(.74) and state["line"] == pytest.approx(.579)
        row = paced(.479, .74, need=None)
        assert state["held_until"] == pytest.approx(weekly_pace_hold(row, now=NOW, pace=PACE))

    def test_on_pace_and_unpaced_accounts(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        assert pace_state(self.status("claude", 69, WEEK_SECONDS * .225), PACE, NOW)["held_until"] is None
        assert pace_state(self.status("workbuddy", 99, WEEK_SECONDS * .9), PACE, NOW) is None
        assert pace_state(self.status("codex", 74, WEEK_SECONDS * .5), None, NOW) is None


class TestMagpieReuse:
    def test_deviation_matches_the_magpie_panel(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        state = pace_state(TestPoolView().status("codex", 68, WEEK_SECONDS * .52), PACE, NOW)
        assert round(state["deviation"] * 100) == 20  # the panel showed "配速 +20%"

    def test_reset_cards_pass_through_without_their_ids(self):
        from datetime import datetime, timezone
        from reverse_agent.model_access.magpie import parse_quotas
        payload = {"object": "list", "data": [{
            "provider": "codex", "kind": "subscription", "plan": "plus", "user": "someone",
            "readAt": "2026-11-07T15:00:00Z",
            "windows": [{"name": "7 days", "used": 74, "remaining": 26, "resetsAt": "2026-11-11T06:41:43Z"}],
            "resets": {"count": 2, "until": "2026-11-30T20:04:36Z", "each": [
                {"until": "2026-12-01T20:43:49Z", "id": "RateLimitResetCredit_b"},
                {"until": "2026-11-30T20:04:36Z", "id": "RateLimitResetCredit_a"}]}}]}
        account = parse_quotas(payload, datetime(2026, 11, 7, 15, 1, tzinfo=timezone.utc))[0]
        assert account["reset_cards"] == {"count": 2, "next_expires_at": "2026-11-30T20:04:36+00:00"}
        assert "RateLimitResetCredit" not in repr(account)

    def test_reset_cards_reach_the_pool_row(self):
        from reverse_agent.platform_v1.multi_account import MultiAccountConfig
        from reverse_agent.platform_v1.multi_account.status import MultiAccountStatusMonitor
        snapshot = {"status": "available", "accounts": [{
            "account_ref": "c1", "provider": "codex", "state": "FRESH", "observed_at": "2026-11-07T15:00:00+00:00",
            "windows": [], "reset_cards": {"count": 1, "next_expires_at": "2026-11-30T20:04:36+00:00"}}]}
        status = MultiAccountStatusMonitor(MultiAccountConfig(), clock=lambda: NOW).diagnose(snapshot)[0]
        assert status.public_view()["reset_cards"]["count"] == 1


class TestResetAnnouncementThroughTheHost:
    """An announced Codex reset reaches routing through the real host path."""

    def route(self, monkeypatch, reader):
        wiring, h = TestHostWiring.host(monkeypatch, 80.0, 6 * 86400)
        h.host._reset_signal_reader = reader
        monkeypatch.setattr(h.host, "_routing_refresh_quota_for_signal", h.host._routing_reset_signal)
        return wiring, h

    def test_an_announcement_lets_paced_codex_drain(self, monkeypatch):
        from datetime import datetime, timedelta, timezone
        expected = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat().replace("+00:00", "Z")
        signal = {"state": "PLAN_ONLY", "validated": True, "scope": "global", "kind": "global_reset",
                  "expected_reset_at": expected}
        wiring, h = self.route(monkeypatch, lambda: signal)
        decision = wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=3))
        assert decision["binding_ref"] == "bind-conn-a"

    def test_without_an_announcement_paced_codex_waits(self, monkeypatch):
        wiring, h = self.route(monkeypatch, lambda: {"state": "UNKNOWN"})
        with pytest.raises(wiring.TaskStoreError) as caught:
            wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=3))
        assert [row["filter"] for row in caught.value.decision["excluded_candidates"]] == ["weekly_pace"]


class TestDrainStopsOnceTheResetHappened:
    """A drain must never spend the new week the reset just delivered."""

    def signal(self, announced):
        from datetime import datetime, timezone
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")
        return {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": iso(NOW + 3600),
                "announced_at": iso(announced)}

    def test_drains_while_the_window_predates_the_announcement(self):
        row = paced(.479, .74)  # window began ~3.4 days before NOW
        decision = choose([row], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=self.signal(NOW - 600))
        assert decision["binding_ref"] == "sub"

    def test_paces_again_once_a_new_window_began_after_the_announcement(self):
        fresh_week = paced(.01, .74)  # a window that began ~1.7 hours ago
        with pytest.raises(ModelSelectionError):
            choose([fresh_week], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=self.signal(NOW - 3 * 3600))


class TestReviewFollowUps:
    def test_a_malformed_reset_card_list_does_not_drop_the_snapshot(self):
        from datetime import datetime, timezone
        from reverse_agent.model_access.magpie import parse_quotas
        for each in (3, True, "x", None, {"until": "2026-11-30T20:04:36Z"}):
            payload = {"object": "list", "data": [{
                "provider": "codex", "kind": "subscription", "plan": "plus", "user": "u",
                "readAt": "2026-11-07T15:00:00Z",
                "windows": [{"name": "7 days", "used": 74, "remaining": 26, "resetsAt": "2026-11-11T06:41:43Z"}],
                "resets": {"count": 2, "each": each}}]}
            account = parse_quotas(payload, datetime(2026, 11, 7, 15, 1, tzinfo=timezone.utc))[0]
            assert account["state"] == "FRESH" and account["reset_cards"] == {"count": 2, "next_expires_at": None}

    def test_the_display_lifts_the_hold_while_codex_drains(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        status = TestPoolView().status("codex", 74, WEEK_SECONDS * .521)
        assert pace_state(status, PACE, NOW)["held_until"] is not None
        draining = pace_state(status, PACE, NOW, drain_since=NOW)
        assert draining["held_until"] is None and draining["draining"] is True
        claude = TestPoolView().status("claude", 95, WEEK_SECONDS * .9)
        assert pace_state(claude, PACE, NOW, drain_since=NOW)["draining"] is False


class TestRenewalEndsEveryDrainEffect:
    def test_a_renewed_window_loses_the_drain_cost_and_penalty_too(self):
        from datetime import datetime, timezone
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": iso(NOW + 3600),
                  "announced_at": iso(NOW - 3 * 3600)}
        renewed = paced(.01, .02)  # new week, nearly unused: pacing allows it anyway
        decision = choose([renewed], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)
        observation = decision["reset_observations"][0]
        assert observation["drain"] is False and observation["drain_ended"] == "window_renewed"
        assert observation["cost_adjustment"] == 0  # no drain discount on the new week

    def test_the_display_does_not_claim_a_drain_for_a_renewed_week(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        fresh = TestPoolView().status("codex", 5, WEEK_SECONDS * .99)  # week began ~1.7h before NOW
        state = pace_state(fresh, PACE, NOW, drain_since=NOW - 3 * 3600)
        assert state["draining"] is False


class TestHostEnvironment:
    @pytest.mark.parametrize("raw", ["24h", "nan", "0", "200", ""])
    def test_a_bad_reset_window_value_does_not_stop_the_host(self, raw, monkeypatch, tmp_path):
        from reverse_agent.platform_v1.run_store import TaskStore
        from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
        monkeypatch.setenv("REVERSE_AGENT_CODEX_RESET_WATCH", "1")
        monkeypatch.setenv("REVERSE_AGENT_CODEX_RESET_WITHIN_HOURS", raw)
        store = TaskStore(str(tmp_path / "t.sqlite"))
        host = CombinedTrustedHost(task_store=store, vault=None)
        assert host._reset_signal_reader._within.total_seconds() == 24 * 3600
        store._conn.close()
