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
HARD_PACE = {**DEFAULT_WEEKLY_PACE, "soft_pacing": False}


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

    @pytest.mark.parametrize("missing", ["weekly_headroom", "weekly_resets_at"])
    def test_require_fresh_holds_an_account_with_no_fresh_reading(self, missing):
        # Owner decision 2026-11-08: a stale Claude reading means Claude is not used.
        row = paced(.5, .1, executor="claude_code", model="sonnet")
        row[missing] = None
        strict = {**PACE, "require_fresh": True}
        assert weekly_pace_hold(row, now=NOW, pace=strict) == NOW + 900
        with pytest.raises(ModelSelectionError):
            choose([row], difficulty=4, now=NOW, weekly_pace=strict)

    def test_require_fresh_leaves_free_and_unpaced_bindings_alone(self):
        strict = {**PACE, "require_fresh": True}
        for row in (paced(.1, .9, executor="opencode"), paced(.1, .9, cost="free")):
            row["weekly_headroom"] = None
            assert weekly_pace_hold(row, now=NOW, pace=strict) is None

    def test_require_fresh_is_off_by_default(self):
        assert DEFAULT_WEEKLY_PACE["require_fresh"] is False

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
        decision = choose(pool, difficulty=4, now=NOW, weekly_pace=HARD_PACE)
        assert decision["binding_ref"] == "free"
        held = next(row for row in decision["excluded_candidates"] if row["binding_id"] == "sub")
        assert held["filter"] == "weekly_pace" and held["retry_at"] > NOW

    def test_a_fully_paced_pool_is_a_temporary_wait_with_a_retry_time(self):
        with pytest.raises(ModelSelectionError) as caught:
            choose([paced(.479, .74)], difficulty=4, now=NOW, weekly_pace=HARD_PACE)
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
            choose([paced(.479, .74)], difficulty=4, now=NOW, weekly_pace=HARD_PACE, reset_signal=signal)

    def test_claude_is_never_drained_by_a_codex_announcement(self):
        row = paced(.2, .6, executor="claude_code", model="sonnet")
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": NOW + 86400}
        with pytest.raises(ModelSelectionError):
            choose([row], difficulty=4, now=NOW, weekly_pace=HARD_PACE, reset_signal=signal)

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

    def test_require_fresh_can_be_switched_on(self, tmp_path):
        data = read_overrides(self.write(tmp_path, {"weekly_pace": {"require_fresh": True}}))
        assert weekly_pace_config(data)["require_fresh"] is True

    def test_overrides_merge_onto_defaults(self, tmp_path):
        data = read_overrides(self.write(tmp_path, {"weekly_pace": {"slack": .2}}))
        assert weekly_pace_config(data) == {**DEFAULT_WEEKLY_PACE, "slack": .2}

    @pytest.mark.parametrize("pace", [
        {"slack": .9}, {"reserve": -.1}, {"enabled": "yes"}, {"executors": "codex"},
        {"executors": [""]}, {"unknown": 1}, [], {"require_fresh": "yes"}, {"require_fresh": 1},
        {"soft_pacing": "yes"}, {"soft_pacing": 1},
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
        monkeypatch.setattr("reverse_agent.platform_v1.routing_inputs.read_overrides",
                            lambda path: {"weekly_pace": {"soft_pacing": False}})
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
        monkeypatch.setattr("reverse_agent.platform_v1.routing_inputs.read_overrides",
                            lambda path: {"weekly_pace": {"soft_pacing": False}})
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
            choose([fresh_week], difficulty=4, now=NOW, weekly_pace=HARD_PACE, reset_signal=self.signal(NOW - 3 * 3600))


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

    # #1400 review at 241f19e9: most mirror events confirm a reset that already landed.
    @pytest.mark.parametrize("landed_before_post", [0, 120, 1800, 9000, 23 * 3600])
    def test_a_confirmation_posted_after_the_reset_never_drains_the_new_week(self, landed_before_post):
        from datetime import datetime, timezone
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")
        announced = NOW - 600
        week_began = announced - landed_before_post
        renewed = candidate("sub", "gpt-6-sol", "subscription", "codex", weekly_headroom=.99,
                            task_weekly_fraction=.02, weekly_resets_at=week_began + WEEK_SECONDS)
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": iso(announced + 24 * 3600),
                  "announced_at": iso(announced)}
        decision = choose([renewed], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)
        observation = decision["reset_observations"][0]
        assert observation["drain"] is False and observation["drain_ended"] == "window_renewed"

    def test_a_week_older_than_the_margin_still_drains(self):
        from datetime import datetime, timezone
        from reverse_agent.platform_v1.model_router import RENEWAL_MARGIN_SECONDS
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")
        announced = NOW - 600
        older = candidate("sub", "gpt-6-sol", "subscription", "codex", weekly_headroom=.26, task_weekly_fraction=.02,
                          weekly_resets_at=announced - RENEWAL_MARGIN_SECONDS - 3600 + WEEK_SECONDS)
        signal = {"state": "PLAN_ONLY", "validated": True, "expected_reset_at": iso(announced + 3600),
                  "announced_at": iso(announced)}
        decision = choose([older], difficulty=4, now=NOW, weekly_pace=PACE, reset_signal=signal)
        assert decision["reset_observations"][0]["drain"] is True

    def test_the_display_matches_routing_for_a_confirmation(self):
        from reverse_agent.platform_v1.multi_account.pool_monitor import pace_state
        just_reset = TestPoolView().status("codex", 5, WEEK_SECONDS * (1 - 2 * 3600 / WEEK_SECONDS))
        assert pace_state(just_reset, PACE, NOW, drain_since=NOW - 600)["draining"] is False

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


class TestGatewayAccounts:
    """A Magpie model naming a paced upstream spends that account's week (2026-11-09)."""

    def test_a_gateway_model_of_a_paced_provider_is_held(self):
        row = paced(.479, .74, need=.03, executor="opencode", model="claude/claude-sonnet-5-5")
        assert weekly_pace_hold(row, now=NOW, pace=PACE) is None  # not marked: unpaced, as before
        row["paced_provider"] = "claude"
        assert weekly_pace_hold(row, now=NOW, pace=PACE) is not None

    def test_require_fresh_holds_a_gateway_model_with_no_account_reading(self):
        row = paced(.5, .1, executor="opencode", model="codex/gpt-6.1-sol")
        row.update(paced_provider="codex", weekly_headroom=None)
        assert weekly_pace_hold(row, now=NOW, pace={**PACE, "require_fresh": True}) is not None

    def test_other_providers_are_not_paced(self):
        row = paced(.479, .74, executor="opencode", model="trae-cn/doubao")
        row["paced_provider"] = "trae-cn"
        assert weekly_pace_hold(row, now=NOW, pace=PACE) is None

    def test_providers_are_an_owner_knob(self, tmp_path):
        state = tmp_path / "model_setup_state.json"
        (tmp_path / "model_routing_overrides.json").write_text(
            json.dumps({"weekly_pace": {"providers": ["claude"]}}), encoding="utf-8")
        assert weekly_pace_config(read_overrides(state))["providers"] == ["claude"]
        (tmp_path / "model_routing_overrides.json").write_text(
            json.dumps({"weekly_pace": {"providers": "claude"}}), encoding="utf-8")
        with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
            read_overrides(state)

    @staticmethod
    def gateway_host(monkeypatch, accounts, model="claude/claude-sonnet-5-5"):
        from types import SimpleNamespace
        from tests.platform_v1 import test_magpie_account_quota_wiring as wiring
        h = wiring._accounts_host(monkeypatch, wiring._snapshot(*accounts), {})
        gateway = {"connection_id": "magpie", "auth_method": "none", "base_url": "http://127.0.0.1:3425/v1"}
        binding = {"binding_id": "magpie-model", "connection_id": "magpie", "executor_id": "opencode",
                   "model_id": model, "enabled": True}
        h.host._store = SimpleNamespace(list_bindings_public=lambda: [binding],
                                        list_connections_public=lambda: [gateway],
                                        get_connection_public=lambda conn: gateway,
                                        list_executors_public=lambda: [],
                                        get_agent_roster_public=lambda: {"roles": {}})
        monkeypatch.setattr(h.host, "_runnable_bindings", lambda: {"magpie-model"})
        for name, value in (("_routing_refresh_quota_for_signal", lambda: {"state": "UNKNOWN"}),
                            ("_routing_bind_discovered", lambda: None), ("_usage_profiles", lambda: {}),
                            ("_routing_model_metadata", lambda: {}), ("_routing_paid_allowed", lambda *a: False),
                            ("_routing_availability_history", lambda: {}),
                            ("_routing_probe_window_allowed", lambda goal: False),
                            ("_routing_availability", lambda *a, **k: {"state": "AVAILABLE", "reason": "fixture"})):
            monkeypatch.setattr(h.host, name, value)
        return wiring, h

    def test_the_host_paces_a_magpie_claude_model_against_the_claude_account(self, monkeypatch):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        claude = w._account("claude-acct", 10.0, weekly=95.0, provider="claude")
        wiring, h = self.gateway_host(monkeypatch, [claude])
        with pytest.raises(wiring.TaskStoreError) as caught:
            wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=3))
        assert [row["filter"] for row in caught.value.decision["excluded_candidates"]] == ["weekly_pace"]

    def test_the_host_routes_a_magpie_claude_model_with_room(self, monkeypatch):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        claude = w._account("claude-acct", 10.0, weekly=5.0, provider="claude")
        wiring, h = self.gateway_host(monkeypatch, [claude])
        real, seen = wiring.model_router.select_model, []

        def spy(candidates, **kwargs):
            seen.append(candidates)
            return real(candidates, **kwargs)
        monkeypatch.setattr(wiring.model_router, "select_model", spy)
        decision = wiring.CombinedTrustedHost._resolve_task_model(
            h.host, wiring.PlannedTask("T1", "t", "i", difficulty=2))
        assert decision["binding_ref"] == "magpie-model"
        chosen = next(c for c in seen[-1] if c["binding_id"] == "magpie-model")
        assert chosen["paced_provider"] == "claude" and chosen["weekly_headroom"] == pytest.approx(.95)

    def test_two_accounts_of_one_provider_give_no_headroom_claim(self, monkeypatch):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        accounts = [w._account("claude-a", 10.0, weekly=5.0, provider="claude"),
                    w._account("claude-b", 10.0, weekly=5.0, provider="claude")]
        wiring, h = self.gateway_host(monkeypatch, accounts)
        assert h.host._gateway_account_quota("claude") == {"windows": [], "pace_input": "gateway_account_ambiguous"}

    # Live 2026-11-17: Magpie re-reads Claude Pro about every 13 minutes (up to ~56), so
    # the 600 s admission freshness held every claude/* and codex/* gateway binding.
    @staticmethod
    def held(wiring, h, difficulty=3):
        with pytest.raises(wiring.TaskStoreError) as caught:
            wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=difficulty))
        rows = caught.value.decision["excluded_candidates"]
        assert [row["filter"] for row in rows] == ["weekly_pace"]
        return rows[0]

    @staticmethod
    def week(account, *, used, reset_in):
        import time as _time
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        for window in account.get("windows") or account.get("cached_windows"):
            if window["name"] == "7 days":
                window.update(used_percent=used, remaining_percent=100 - used,
                              resets_at=w._iso(_time.time() + reset_in))
        return account

    @pytest.mark.parametrize("provider,model", [("claude", "claude/claude-sonnet-5-5"), ("codex", "codex/gpt-6.1-sol")])
    def test_a_fresh_gateway_reading_lets_a_paced_binding_route(self, monkeypatch, provider, model):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        account = w._account(f"{provider}-acct", 10.0, weekly=5.0, provider=provider)
        wiring, h = self.gateway_host(monkeypatch, [account], model=model)
        decision = wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=2))
        assert decision["binding_ref"] == "magpie-model"

    def test_a_reading_older_than_admission_freshness_still_paces_the_week(self, monkeypatch):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        account = w._account("claude-acct", 10.0, weekly=5.0, provider="claude", age=1800)
        # parse_quotas keeps a reading older than 15 minutes only as cached windows.
        account.update(state="STALE", reason="stale_reading", cached_windows=account["windows"], windows=[])
        wiring, h = self.gateway_host(monkeypatch, [account])
        view = h.host._gateway_account_quota("claude")
        assert view["pace_input"] == "gateway_reading_aged" and 1790 <= view["reading_age_seconds"] <= 1900
        assert {window["window"] for window in view["windows"]} == {"five_hour", "weekly"}
        decision = wiring.CombinedTrustedHost._resolve_task_model(h.host, wiring.PlannedTask("T1", "t", "i", difficulty=2))
        assert decision["binding_ref"] == "magpie-model"

    def test_no_reading_within_the_pace_bound_holds_with_no_fresh_gateway_quota(self, monkeypatch):
        import time as _time
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        from reverse_agent.platform_v1.trusted_host import GATEWAY_PACE_MAX_AGE_SECONDS
        account = w._account("claude-acct", 10.0, weekly=5.0, provider="claude", age=GATEWAY_PACE_MAX_AGE_SECONDS + 120)
        account.update(state="STALE", reason="stale_reading", cached_windows=account["windows"], windows=[])
        wiring, h = self.gateway_host(monkeypatch, [account])
        monkeypatch.setattr("reverse_agent.platform_v1.routing_inputs.read_overrides",
                            lambda path: {"weekly_pace": {"require_fresh": True}})
        row = self.held(wiring, h, difficulty=2)
        assert row["cause"] == "no_fresh_gateway_quota"
        assert _time.time() < row["retry_at"] <= _time.time() + 900

    def test_no_gateway_account_is_named(self, monkeypatch):
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        other = w._account("trae-acct", 10.0, weekly=5.0, provider="trae-cn")
        wiring, h = self.gateway_host(monkeypatch, [other])
        monkeypatch.setattr("reverse_agent.platform_v1.routing_inputs.read_overrides",
                            lambda path: {"weekly_pace": {"require_fresh": True}})
        assert self.held(wiring, h, difficulty=2)["cause"] == "no_gateway_account"

    def test_an_account_ahead_of_pace_holds_until_its_pace_catches_up(self, monkeypatch):
        import time as _time
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        # Day one of the week (reset in six days) with half of it already spent.
        account = self.week(w._account("claude-acct", 10.0, provider="claude"), used=50.0, reset_in=6 * 86400)
        wiring, h = self.gateway_host(monkeypatch, [account])
        monkeypatch.setattr("reverse_agent.platform_v1.routing_inputs.read_overrides",
                            lambda path: {"weekly_pace": {"soft_pacing": False}})
        row = self.held(wiring, h, difficulty=2)
        from reverse_agent.platform_v1.model_router import UNKNOWN_WEEKLY_NEED
        start = _time.time() + 6 * 86400 - WEEK_SECONDS
        assert row["cause"] == "ahead_of_pace"
        assert row["retry_at"] == pytest.approx(start + WEEK_SECONDS * (.5 + UNKNOWN_WEEKLY_NEED - .10), abs=120)

    def test_an_account_past_its_reserve_holds_until_the_reset(self, monkeypatch):
        import time as _time
        from tests.platform_v1 import test_magpie_account_quota_wiring as w
        account = self.week(w._account("codex-acct", 10.0, provider="codex"), used=98.0, reset_in=4 * 86400)
        wiring, h = self.gateway_host(monkeypatch, [account], model="codex/gpt-6.1-sol")
        row = self.held(wiring, h, difficulty=2)
        assert row["cause"] == "weekly_reserve"
        assert row["retry_at"] == pytest.approx(_time.time() + 4 * 86400, abs=120)


def test_the_pace_decision_names_its_cause():
    from reverse_agent.platform_v1.model_router import weekly_pace_decision
    strict = {**PACE, "require_fresh": True}
    native = paced(.5, .1)
    native.update(weekly_headroom=None)
    assert weekly_pace_decision(native, now=NOW, pace=strict) == (NOW + 900, "no_fresh_account_quota")
    gateway = paced(.5, .1, executor="opencode", model="claude/claude-sonnet-5-5")
    gateway.update(paced_provider="claude", weekly_headroom=None)
    assert weekly_pace_decision(gateway, now=NOW, pace=strict)[1] == "no_fresh_gateway_quota"
    gateway["weekly_pace_input"] = "gateway_account_ambiguous"
    assert weekly_pace_decision(gateway, now=NOW, pace=strict)[1] == "gateway_account_ambiguous"
    assert weekly_pace_decision(native, now=NOW, pace=PACE) == (None, "")  # not strict: no claim
    assert weekly_pace_decision(paced(.5, .45), now=NOW, pace=PACE) == (None, "")


def test_the_reserve_is_released_only_in_the_last_hours_before_the_reset():
    from reverse_agent.platform_v1.model_router import weekly_pace_decision
    pace = {**PACE, "reserve_release_hours": 6}
    resets = NOW + 48 * 3600
    row = {**paced(.5, .91), "weekly_resets_at": resets}
    assert weekly_pace_decision(row, now=resets - 6 * 3600 - 1, pace=pace) == (resets - 6 * 3600, "weekly_reserve")
    assert weekly_pace_decision(row, now=resets - 6 * 3600, pace=pace) == (None, "")
    # Off by default: the reserve stays to the end.
    assert weekly_pace_decision(row, now=resets - 60, pace=PACE) == (resets, "weekly_reserve")
    # A task larger than what is left waits for the reset, released or not.
    big = {**row, "weekly_headroom": .01}
    for now in (resets - 7 * 3600, resets - 3600):
        assert weekly_pace_decision(big, now=now, pace=pace)[0] == resets


@pytest.mark.parametrize("value,ok", [(6, True), (0, True), (2.5, True), (-1, False), (73, False), (True, False), ("6", False)])
def test_reserve_release_hours_are_validated(tmp_path, value, ok):
    import json
    from reverse_agent.platform_v1.routing_inputs import read_overrides, weekly_pace_config
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps({"weekly_pace": {"reserve_release_hours": value}}))
    state = tmp_path / "model_setup_state.json"
    if ok:
        assert weekly_pace_config(read_overrides(state))["reserve_release_hours"] == value
    else:
        with pytest.raises(ValueError):
            read_overrides(state)


def test_selection_uses_the_released_reserve():
    row = {**paced(.5, .91), "weekly_resets_at": NOW + 5 * 3600}
    with pytest.raises(ModelSelectionError):
        choose([row], difficulty=4, now=NOW, weekly_pace=PACE)
    pace = {**PACE, "reserve_release_hours": 6}
    assert choose([row], difficulty=4, now=NOW, weekly_pace=pace)["binding_ref"] == "sub"
    for held in ({**row, "weekly_resets_at": NOW + 7 * 3600}, {**row, "weekly_headroom": .01},
                 {**row, "short_headroom": .05, "task_short_fraction": .04}):
        with pytest.raises(ModelSelectionError):
            choose([held], difficulty=4, now=NOW, weekly_pace=pace)


def test_admission_and_in_flight_use_the_released_reserve_for_that_window_only():
    from reverse_agent.model_access.quota_forecast import iso
    from reverse_agent.platform_v1 import quota_reservation as quota
    from reverse_agent.platform_v1.quota_inflight import projection

    def evidence(weekly_used=91, resets=NOW + 5 * 3600, short_used=10):
        return {"account_ref": "a", "source": "cli", "observed_at": iso(NOW), "windows": [
            {"window": "five_hour", "used_percent": short_used, "resets_at": iso(NOW + 3600)},
            {"window": "weekly", "used_percent": weekly_used, "resets_at": iso(resets)}]}
    need = {"account_ref": "a", "windows": {"five_hour": {"p80": 5}, "weekly": {"p80": 6}}}

    def verdict(ev, marked):
        return quota.admission(ev, marked, now=NOW)["decision"]
    assert verdict(evidence(), need) == "quota_wait"
    marked = quota.release_weekly_reserve(need, evidence(), release_hours=6, now=NOW)
    assert verdict(evidence(), marked) == "ok" and "reserve_released_until" not in need["windows"]["weekly"]
    assert verdict(evidence(weekly_used=95), marked) == "quota_wait"  # never past the allowance
    assert verdict(evidence(short_used=90), marked) == "quota_wait"  # the 5-hour margin stays
    assert verdict(evidence(resets=NOW + WEEK_SECONDS), marked) == "quota_wait"  # a renewed week
    for hours, resets in ((4, NOW + 5 * 3600), (0, NOW + 5 * 3600), (6, NOW + 7 * 3600)):
        assert quota.release_weekly_reserve(need, evidence(resets=resets), release_hours=hours, now=NOW) == need
    kwargs = dict(reservation_id="r", spent={}, now=NOW)
    assert projection(evidence(), need, (), **kwargs)["decision"] == "quota_wait"
    assert projection(evidence(), marked, (), **kwargs)["decision"] == "ok"
    spent = {"five_hour": 5, "weekly": 9}
    assert projection(evidence(weekly_used=100), marked, (), **{**kwargs, "spent": spent})["decision"] == "quota_wait"


def test_soft_pacing_penalizes_ahead_of_pace_while_failing_free_yields_to_paid():
    sub = paced(.2, .45, executor="claude_code", model="sonnet")
    free_ok = candidate("free-ok", "kimi-k3")
    free_bad = candidate("free-bad", "kimi-k3")
    profiles = {
        "sub": {"task_buckets": {"code:4": {"attempts": 4, "success_rate": 1.0, "timeouts": 0}}},
        "free-ok": {"task_buckets": {"code:4": {"attempts": 5, "success_rate": 1.0, "timeouts": 0}}},
        "free-bad": {"task_buckets": {"code:4": {"attempts": 5, "success_rate": 0.2, "timeouts": 0}}},
    }
    # Ahead of pace stays selectable and receives pace_penalty without weekly_pace exclusion.
    solo = choose([sub], difficulty=4, now=NOW, weekly_pace=PACE, profiles=profiles)
    assert solo["binding_ref"] == "sub"
    bd = solo["score_breakdown"]
    assert bd["pace_penalty"] > 0 and bd["pace_cause"] == "ahead_of_pace" and bd["pace_retry_at"] > NOW
    # Healthy free model beats the soft-paced subscription.
    assert choose([sub, free_ok], difficulty=4, now=NOW, weekly_pace=PACE, profiles=profiles)["binding_ref"] == "free-ok"
    # Unreliable free model (20% success) gets reliability_penalty=2.0 and loses to ahead-of-pace paid subscription.
    unreliable = choose([sub, free_bad], difficulty=4, now=NOW, weekly_pace=PACE, profiles=profiles)
    assert unreliable["binding_ref"] == "sub"
    bad_row = next(item for item in unreliable["candidates"] if item["binding_id"] == "free-bad")
    assert bad_row["score_breakdown"]["reliability_penalty"] == pytest.approx(2.0)


def test_soft_pacing_still_enforces_weekly_reserve_until_12h_release():
    from reverse_agent.platform_v1.model_router import weekly_pace_decision
    pace = {**PACE, "reserve_release_hours": 12}
    resets = NOW + 48 * 3600
    row = {**paced(.5, .91), "weekly_resets_at": resets}
    assert weekly_pace_decision(row, now=resets - 12 * 3600 - 1, pace=pace) == (resets - 12 * 3600, "weekly_reserve")
    assert weekly_pace_decision(row, now=resets - 12 * 3600, pace=pace) == (None, "")
    # Even with soft_pacing=True (default in PACE), weekly_reserve still hard-blocks before the 12h release window.
    with pytest.raises(ModelSelectionError) as caught:
        choose([{**paced(.5, .95, need=None, ref="sub"), "weekly_resets_at": resets}],
               difficulty=4, now=resets - 12 * 3600 - 1, weekly_pace={**pace})
    assert caught.value.decision["excluded_candidates"][0]["filter"] == "weekly_pace"
    assert caught.value.decision["excluded_candidates"][0]["cause"] == "weekly_reserve"
    # A task requiring more than remaining weekly_headroom stays held until reset even within 12h.
    big = {**paced(.5, .99), "weekly_resets_at": resets}
    assert weekly_pace_decision(big, now=resets - 3600, pace=pace) == (resets, "weekly_reserve")


def test_an_unreadable_policy_releases_nothing_and_does_not_raise(monkeypatch):
    import inspect
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import quota_reservation, trusted_host

    owner = next(cls for _, cls in inspect.getmembers(trusted_host, inspect.isclass)
                 if "_prepare_task_quota" in vars(cls))
    prepared = []

    class Host:
        _prepare_task_quota = vars(owner)["_prepare_task_quota"]
        _store = SimpleNamespace(
            list_bindings_public=lambda: [{"binding_id": "b", "connection_id": "c"}],
            get_connection_public=lambda _id: {"connection_id": "c", "account_ref": "a",
                                               "auth_method": "external_cli_session",
                                               "executor_provider_id": provider})
        _task_store = SimpleNamespace(get_task=lambda _id: task)
        _control_store = SimpleNamespace(prepare_quota_admission=lambda **kw: prepared.append(kw["need"]),
                                         goal_id_for_task=lambda _id: None)

        def _account_quota_candidates(self, *_):
            return []

        def _subscription_quotas(self):
            return []

        def _aged_account_reading(self, *_, **__):
            return None

        def _account_task_need(self, *_):
            return need

        def _weekly_pace_policy(self):
            raise ValueError("invalid_model_routing_overrides")

    from reverse_agent.model_access.contracts import NATIVE_CLI_PROVIDERS
    provider = next(iter(NATIVE_CLI_PROVIDERS))
    need = {"windows": {"weekly": {"p80": 6}}}
    task = SimpleNamespace(id="t", binding_ref="b", executor_kind="codex", status="QUEUED")
    monkeypatch.setattr(quota_reservation, "observation", lambda *a, **k: {"fresh": True, "windows": []})
    monkeypatch.setattr("reverse_agent.platform_v1.usage_ledger.estimation_records", lambda store: [], raising=False)
    Host()._prepare_task_quota(task)
    assert prepared == [need]
