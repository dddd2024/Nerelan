"""#1471: Magpie's time-limited model allowances and expiring credits reach routing. Provider-free."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.model_access.magpie import parse_quotas
from reverse_agent.platform_v1 import resource_allowances as ra
from reverse_agent.platform_v1.pool_verifier import PoolVerifier
from test_model_router import candidate, choose
from test_pool_verifier import _Host, _binding

NOW = datetime(2026, 11, 12, 5, 0, tzinfo=timezone.utc)
T = NOW.timestamp()
GATEWAY = {"connection_id": "magpie", "auth_method": "none", "base_url": "http://127.0.0.1:3425/v1"}
OTHER = {"connection_id": "direct", "auth_method": "api_key", "base_url": "https://api.example.invalid/v1"}


def iso(hours: float) -> str:
    return (NOW + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def raw_account(provider, windows, user=None):
    return {"provider": provider, "kind": "subscription", "plan": "Free plan", "user": user,
            "readAt": NOW.isoformat(), "windows": windows}


def snapshot(*accounts):
    parsed = parse_quotas({"object": "list", "data": list(accounts)}, NOW)
    return {"status": "available", "accounts": parsed}


WORKBUDDY = raw_account("workbuddy", [
    {"name": "Credits", "used": 0, "remaining": 100, "limit": 500, "resetsAt": iso(450)},
    {"name": "Extra credits", "used": 60, "remaining": 40, "limit": 3900, "runsOutAt": iso(370), "runsOut": 26.9},
    {"name": "deepseek-v4.1-flash tokens (est.)", "used": 0, "remaining": 100, "limit": 200_000_000,
     "resetsAt": iso(10)},
])
WORKBUDDY_AI = raw_account("workbuddy-ai", [
    {"name": "Free model tokens", "used": 0, "remaining": 100, "limit": 100_000_000, "resetsAt": iso(9)}])
RACCOON = raw_account("raccoon", [
    {"name": "Credits", "used": 0, "remaining": 100, "limit": 7800, "runsOutAt": iso(30), "runsOut": 300}])


def binding(model, connection="magpie", binding_id=None):
    return {"binding_id": binding_id or model.replace("/", "-"), "model_id": model, "connection_id": connection}


class TestParser:
    def test_limit_and_expiry_are_kept_only_when_stated(self):
        windows = {w["name"]: w for w in snapshot(WORKBUDDY)["accounts"][0]["windows"]}
        assert windows["Extra credits"]["runs_out"] == 26.9
        assert windows["Extra credits"]["runs_out_at"].startswith("2026-11-27")
        assert windows["deepseek-v4.1-flash tokens (est.)"]["limit"] == 200_000_000
        assert "runs_out_at" not in windows["Credits"]
        plain = parse_quotas({"object": "list", "data": [raw_account("codex", [
            {"name": "5 hours", "used": 10, "remaining": 90, "resetsAt": iso(2)}])]}, NOW)[0]["windows"][0]
        assert set(plain) == {"name", "used_percent", "remaining_percent", "resets_at", "unlimited"}

    def test_an_unreadable_expiry_is_dropped_not_guessed(self):
        account = raw_account("raccoon", [{"name": "Credits", "used": 0, "remaining": 100,
                                           "runsOutAt": "soon", "runsOut": 300}])
        window = snapshot(account)["accounts"][0]["windows"][0]
        assert "runs_out_at" not in window and "runs_out" not in window


class TestReading:
    def test_model_allowances_credits_and_unnamed_allowances(self):
        found = ra.read_allowances(snapshot(WORKBUDDY, WORKBUDDY_AI, RACCOON), now=T)
        assert set(found["models"]) == {"workbuddy/deepseek-v4.1-flash"}
        assert found["models"]["workbuddy/deepseek-v4.1-flash"]["resets_at"] == pytest.approx(T + 10 * 3600)
        assert [(u["provider"], u["window"]) for u in found["unattributed"]] == [("workbuddy-ai", "Free model tokens")]
        assert found["credits"]["raccoon"]["runs_out"] == 300
        assert found["credits"]["workbuddy"]["runs_out_at"] == pytest.approx(T + 370 * 3600)

    def test_two_fresh_accounts_for_one_provider_are_ambiguous(self):
        second = raw_account("workbuddy", WORKBUDDY["windows"], user="someone-else")
        found = ra.read_allowances(snapshot(WORKBUDDY, second), now=T)
        assert found["models"] == {} and found["credits"] == {} and found["ambiguous"] == ["workbuddy"]

    def test_a_second_stale_account_still_makes_the_provider_ambiguous(self):
        stale = dict(raw_account("workbuddy", WORKBUDDY["windows"], user="someone-else"),
                     readAt=(NOW - timedelta(hours=1)).isoformat())
        found = ra.read_allowances(snapshot(WORKBUDDY, stale), now=T)
        assert found["models"] == {} and found["ambiguous"] == ["workbuddy"]

    @pytest.mark.parametrize("title", ["Input tokens", "Weekly tokens", "Free model tokens", "Premium tokens (est.)"])
    def test_generic_titles_name_no_model(self, title):
        account = raw_account("workbuddy", [{"name": title, "used": 0, "remaining": 100, "resetsAt": iso(5)}])
        found = ra.read_allowances(snapshot(account), now=T)
        assert found["models"] == {} and [u["window"] for u in found["unattributed"]] == [title]

    def test_stale_or_missing_readings_give_nothing(self):
        stale = dict(WORKBUDDY, readAt=(NOW - timedelta(hours=1)).isoformat())
        assert ra.read_allowances(snapshot(stale), now=T)["models"] == {}
        assert ra.read_allowances({"status": "unavailable"}, now=T)["models"] == {}
        assert ra.read_allowances(None, now=T) == {"models": {}, "credits": {}, "unattributed": [], "ambiguous": []}


class TestEffectiveCost:
    allowances = ra.read_allowances(snapshot(WORKBUDDY, RACCOON), now=T)

    def test_an_active_allowance_makes_the_matching_gateway_binding_free(self):
        cost, resources = ra.effective_cost(binding("workbuddy/deepseek-v4.1-flash"), GATEWAY, {}, self.allowances, now=T)
        assert cost == "free"
        assert resources["allowance"]["default_cost_class"] == "subscription"
        # Another model of the same provider keeps its default.
        assert ra.effective_cost(binding("workbuddy/glm-5.3-flash"), GATEWAY, {}, self.allowances, now=T)[0] == "subscription"

    @pytest.mark.parametrize("remaining, hours, expected", [
        (100, 10, "free"), (4, 10, "subscription"), (100, -1, "subscription")])
    def test_reserve_and_reset(self, remaining, hours, expected):
        account = raw_account("workbuddy", [{"name": "deepseek-v4.1-flash tokens", "used": 100 - remaining,
                                             "remaining": remaining, "resetsAt": iso(hours)}])
        allowances = ra.read_allowances(snapshot(account), now=T)
        assert ra.effective_cost(binding("workbuddy/deepseek-v4.1-flash"), GATEWAY, {}, allowances, now=T)[0] == expected

    def test_owner_choice_and_other_connections_are_never_changed(self):
        owner = {"models": {"workbuddy/deepseek-v4.1-flash": {"cost_class": "subscription"}}}
        assert ra.effective_cost(binding("workbuddy/deepseek-v4.1-flash"), GATEWAY, owner, self.allowances, now=T)[0] == "subscription"
        assert ra.effective_cost(binding("workbuddy/deepseek-v4.1-flash", "direct"), OTHER, {}, self.allowances, now=T) == ("subscription", {})

    def test_a_weekly_paced_provider_keeps_its_subscription_guards(self):
        account = raw_account("codex", [{"name": "gpt-6 tokens", "used": 0, "remaining": 100, "resetsAt": iso(5)}])
        allowances = ra.read_allowances(snapshot(account), now=T)
        cost, resources = ra.effective_cost(binding("codex/gpt-6"), GATEWAY, {}, allowances, now=T)
        assert cost == "subscription" and "default_cost_class" not in resources["allowance"]

    def test_an_unclassified_paid_route_is_not_upgraded(self):
        account = raw_account("unknownco", [{"name": "big-model tokens", "used": 0, "remaining": 100, "resetsAt": iso(5)}])
        allowances = ra.read_allowances(snapshot(account), now=T)
        cost, resources = ra.effective_cost(binding("unknownco/big-model"), GATEWAY, {}, allowances, now=T)
        assert cost == "paid_api" and "default_cost_class" not in resources["allowance"]

    def test_expiring_credits_are_attached_to_free_and_subscription_routes(self):
        owner = {"models": {"raccoon/sn-kimi-k3": {"cost_class": "free"}}}
        cost, resources = ra.effective_cost(binding("raccoon/sn-kimi-k3"), GATEWAY, owner, self.allowances, now=T)
        assert cost == "free" and resources["credit_expiry"]["runs_out"] == 300


class TestUrgency:
    def test_bounded_and_growing_as_the_moment_nears(self):
        far = {"allowance": {"resets_at": T + 48 * 3600}}
        near = {"allowance": {"resets_at": T + 3600}}
        assert ra.urgency({}, now=T) == 0
        assert ra.urgency(far, now=T) == pytest.approx(ra.ALLOWANCE_BASE_BONUS)
        assert ra.ALLOWANCE_BASE_BONUS < ra.urgency(near, now=T) <= ra.ALLOWANCE_BASE_BONUS + ra.ALLOWANCE_URGENCY_BONUS
        assert ra.urgency({"credit_expiry": {"runs_out_at": T + 8 * 86400}}, now=T) == 0
        assert ra.urgency({"credit_expiry": {"runs_out_at": T + 3600}}, now=T) > .45
        # The largest preference never makes a subscription cheaper than a free route.
        most = ra.ALLOWANCE_BASE_BONUS + ra.ALLOWANCE_URGENCY_BONUS + ra.CREDIT_URGENCY_BONUS
        assert 1 - most > 0


class TestRouting:
    def test_an_allowance_about_to_reset_is_chosen_over_an_unlimited_free_model(self):
        expiring = {"allowance": {"window": "glm-5.3 tokens", "resets_at": T + 2 * 3600}}
        decision = choose([candidate("a-unlimited", "glm-5.3"), candidate("z-allowance", "glm-5.3", resources=expiring)],
                          difficulty=3, kind="code", now=T)
        assert decision["binding_ref"] == "z-allowance"
        chosen = next(row for row in decision["candidates"] if row["binding_id"] == "z-allowance")
        assert chosen["score_breakdown"]["resource_urgency"] > 0 and chosen["resources"] == expiring

    def test_expiring_credits_order_subscriptions_but_free_stays_first(self):
        credits = {"credit_expiry": {"runs_out_at": T + 3600, "runs_out": 300}}
        decision = choose([candidate("a-sub", "glm-5.3", "subscription"),
                           candidate("b-sub", "glm-5.3", "subscription", resources=credits)],
                          difficulty=3, kind="code", now=T)
        assert decision["binding_ref"] == "b-sub"
        decision = choose([candidate("b-sub", "glm-5.3", "subscription", resources=credits),
                           candidate("z-free", "glm-5.3")], difficulty=3, kind="code", now=T)
        assert decision["binding_ref"] == "z-free"


class TestVerification:
    def test_a_binding_free_only_until_its_reset_is_verified_first(self, tmp_path):
        bindings = [_binding("a-free", "free/a", connection="magpie"),
                    _binding("w-allowance", "workbuddy/deepseek-v4.1-flash", connection="magpie")]
        host = _Host(tmp_path, bindings, overrides={"models": {"free/a": {"cost_class": "free"}}})
        host._store.list_connections_public = lambda: [{**GATEWAY, "enabled": True}]
        allowances = ra.read_allowances(snapshot(WORKBUDDY), now=T)
        host._resource_allowances = lambda refresh=True: allowances
        assert PoolVerifier(host).verify_once(now=T) == "w-allowance"
