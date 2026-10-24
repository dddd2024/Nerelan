"""Account-level Magpie telemetry is shown for what it is, never promoted to a route.

Regression for #1328: a fresh ``Credit`` window for a product with no executor
behind it (``workbuddy``, ``trae-cn``) used to vanish from the resource view, so
the UI showed ``UNKNOWN`` beside a number Magpie was publishing.  The view now
lists every reported account with its windows and names what a route can claim:
provider-level ``route_bound``, an explicit ``no_route_identity``, an explicit
ambiguity, or ``unobserved`` with the original reason.  Admission quotas are
untouched.
"""

from __future__ import annotations

from reverse_agent.model_access.resources import build_resource_view
from reverse_agent.model_access.store import ModelProfileStore

# Shape of the live Magpie snapshot of 2026-10-24, percent-only and sanitized.
SNAPSHOT = {
    "status": "available",
    "reason": None,
    "version": "0.1.1313",
    "accounts": [
        {"provider": "claude", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:02.868343+00:00",
         "windows": [{"name": "5 hours", "used_percent": 0, "remaining_percent": 100,
                      "resets_at": None, "unlimited": False},
                     {"name": "7 days", "used_percent": 99, "remaining_percent": 1,
                      "resets_at": "2026-10-26T04:59:00+00:00", "unlimited": False}]},
        {"provider": "codex", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:03.372965+00:00",
         "windows": [{"name": "5 hours", "used_percent": 23, "remaining_percent": 77,
                      "resets_at": "2026-10-24T08:09:20+00:00", "unlimited": False}]},
        {"provider": "workbuddy", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:03.809254+00:00",
         "windows": [{"name": "Credits", "used_percent": 98.27586206896552,
                      "remaining_percent": 1.7241379310344769, "resets_at": None, "unlimited": False}]},
        {"provider": "trae-cn", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:03.699361+00:00",
         "windows": [{"name": "Credits", "used_percent": 90.93527272727273,
                      "remaining_percent": 9.064727272727268,
                      "resets_at": "2026-10-26T13:27:40+00:00", "unlimited": False}]},
        {"provider": "copilot", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:02.148393+00:00",
         "windows": [{"name": "Premium requests", "used_percent": 0.04999999999999716,
                      "remaining_percent": 99.95, "resets_at": "2026-11-01T00:00:00+00:00",
                      "unlimited": False},
                     {"name": "Chat requests", "used_percent": 0, "remaining_percent": 100,
                      "resets_at": None, "unlimited": True}]},
        {"provider": "opencode-zen-free", "kind": "subscription", "state": "UNKNOWN", "reason": None,
         "observed_at": None, "windows": []},
    ],
}


def _store() -> ModelProfileStore:
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_binding({"binding_id": "claude-sonnet", "name": "Sonnet", "connection_id": "claude-account",
                          "executor_id": "claude_code", "model_id": "sonnet", "enabled": True})
    store.upsert_connection({"connection_id": "chatgpt-account", "name": "ChatGPT", "provider": "codex",
                             "base_url": "https://chatgpt.com", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_binding({"binding_id": "codex-gpt", "name": "GPT", "connection_id": "chatgpt-account",
                          "executor_id": "codex", "model_id": "gpt-5", "enabled": True})
    store.upsert_connection({"connection_id": "magpie", "name": "Magpie gateway", "provider": "litellm-proxy",
                             "base_url": "http://127.0.0.1:3425/v1", "auth_method": "api_key",
                             "enabled": True, "api_key": "gateway-secret-value"})
    store.upsert_binding({"binding_id": "coding-default", "name": "Default", "connection_id": "magpie",
                          "executor_id": "opencode", "model_id": "sensenova-6.8-flash-lite", "enabled": True})
    return store


def _view(snapshot=None, *, mode="hybrid", quotas=None):
    snapshot = SNAPSHOT if snapshot is None else snapshot
    return build_resource_view(_store(), lambda: {}, quotas=(lambda: quotas or {}),
                               external=(lambda: snapshot), mode=mode)


def _accounts(view):
    return {account["provider"]: account for account in view["account_attribution"]["accounts"]}


def test_every_reported_account_appears_with_what_a_route_can_claim():
    view = _view()
    section = view["account_attribution"]

    assert section["status"] == "available" and section["reason"] is None
    accounts = _accounts(view)
    assert set(accounts) == {"claude", "codex", "workbuddy", "trae-cn", "copilot", "opencode-zen-free"}

    assert accounts["claude"]["attribution"] == {"status": "route_bound", "reason": None,
                                                "route_provider": "claude-code",
                                                "connection_ids": ["claude-account"]}
    assert accounts["codex"]["attribution"]["status"] == "route_bound"
    assert accounts["codex"]["attribution"]["connection_ids"] == ["chatgpt-account"]
    for provider in ("workbuddy", "trae-cn", "copilot"):
        assert accounts[provider]["attribution"]["status"] == "no_route_identity"
        assert accounts[provider]["attribution"]["reason"] == "provider_not_mapped_to_any_executor"
        assert accounts[provider]["attribution"]["connection_ids"] == []
    assert accounts["opencode-zen-free"]["attribution"]["status"] == "unobserved"
    assert accounts["opencode-zen-free"]["windows"] == []
    assert section["summary"] == {"accounts": 6, "route_bound": 2, "no_route_identity": 3,
                                  "ambiguous": 0, "unobserved": 1}


def test_unrouted_credit_numbers_are_published_verbatim_and_scoped_to_the_account():
    accounts = _accounts(_view())
    workbuddy = accounts["workbuddy"]

    assert workbuddy["usage_scope"] == "account"
    assert workbuddy["observed_at"] == "2026-10-24T03:30:03.809254+00:00"
    assert workbuddy["windows"] == [{"window": "Credits", "used_percent": 98.27586206896552,
                                     "remaining_percent": 1.7241379310344769, "resets_at": None,
                                     "unlimited": False}]
    copilot = accounts["copilot"]["windows"]
    assert [window["unlimited"] for window in copilot] == [False, True]


def test_accounts_sharing_one_provider_stay_ambiguous_and_are_never_averaged():
    duplicate = {"status": "available", "reason": None, "accounts": [
        {"provider": "codex", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:03Z", "windows": [
             {"name": "5 hours", "used_percent": 10, "remaining_percent": 90, "resets_at": None,
              "unlimited": False}]},
        {"provider": "codex", "kind": "subscription", "state": "FRESH", "reason": None,
         "observed_at": "2026-10-24T03:30:04Z", "windows": [
             {"name": "5 hours", "used_percent": 90, "remaining_percent": 10, "resets_at": None,
              "unlimited": False}]},
    ]}
    view = _view(duplicate)
    accounts = view["account_attribution"]["accounts"]

    assert len(accounts) == 2
    assert {account["attribution"]["status"] for account in accounts} == {"ambiguous_multiple_accounts"}
    assert {account["attribution"]["reason"] for account in accounts} == {"accounts_share_one_provider"}
    assert view["account_attribution"]["summary"]["ambiguous"] == 2
    assert view["account_attribution"]["summary"]["route_bound"] == 0
    assert [account["windows"][0]["used_percent"] for account in accounts] == [10, 90]  # both, not a mean


def test_two_connections_on_one_provider_are_named_not_guessed():
    store = ModelProfileStore()
    for connection_id in ("claude-account", "claude-relay"):
        store.upsert_connection({"connection_id": connection_id, "name": connection_id,
                                 "provider": "claude-code", "base_url": "https://claude.ai",
                                 "auth_method": "external_cli_session", "enabled": True})
    view = build_resource_view(store, lambda: {}, external=(lambda: SNAPSHOT), mode="hybrid")
    claude = _accounts(view)["claude"]

    assert claude["attribution"]["status"] == "ambiguous_multiple_routes"
    assert claude["attribution"]["reason"] == "connections_share_one_provider"
    assert claude["attribution"]["connection_ids"] == ["claude-account", "claude-relay"]


def test_stale_account_keeps_its_reason_and_has_no_current_percentage():
    stale = {"status": "available", "reason": None, "accounts": [
        {"provider": "codex", "kind": "subscription", "state": "STALE", "reason": "stale_reading",
         "observed_at": "2026-10-20T00:00:00Z", "windows": [],
         "cached_windows": [{"name": "5 hours", "used_percent": 44, "remaining_percent": 56,
                             "resets_at": None, "unlimited": False}]}]}
    account = _accounts(_view(stale))["codex"]

    assert account["state"] == "STALE" and account["reason"] == "stale_reading"
    assert account["attribution"]["status"] == "unobserved"
    assert account["windows"] == []  # the stale reading is not presented as current use


def test_disabled_or_unavailable_magpie_is_explicit_and_invents_nothing():
    for status in ("disabled", "unavailable"):
        view = _view({"status": status, "reason": "magpie_not_enabled"}, mode="magpie_primary")
        section = view["account_attribution"]
        assert section["status"] == status
        assert section["reason"] == "magpie_not_enabled"
        assert section["accounts"] == []
        assert section["summary"] == {"accounts": 0, "route_bound": 0, "no_route_identity": 0,
                                     "ambiguous": 0, "unobserved": 0}
    # The legacy view keeps its pre-existing shape: the section is additive only.
    assert "account_attribution" not in _view(mode="legacy")


def test_attribution_never_changes_admission_or_quota_known():
    def window(used, resets_at):
        return {"window": "5 hours", "basis": "official_percent", "used_percent": used,
                "resets_at": resets_at, "reset_passed": False, "status": None, "source": "magpie"}

    quotas = {"codex": {"state": "OBSERVED", "provenance": "EXTERNAL_MAGPIE", "source": "magpie",
                        "observed_at": "2026-10-24T03:30:03Z",
                        "windows": [window(23, "2026-10-24T08:09:20+00:00")]},
              "claude-code": {"state": "OBSERVED", "provenance": "EXTERNAL_MAGPIE", "source": "magpie",
                              "observed_at": "2026-10-24T03:30:02Z",
                              "windows": [window(99, "2026-10-26T04:59:00+00:00")]}}
    view = _view(quotas=quotas)
    by_id = {item["connection_id"]: item for item in view["resources"]}

    # The gateway keeps its honest UNKNOWN: account telemetry is not a route window.
    assert by_id["magpie"]["quota"]["state"] == "UNKNOWN"
    assert by_id["magpie"]["quota"]["reason"] == "api_key_has_no_subscription_window"
    assert by_id["claude-account"]["quota"]["state"] == "OBSERVED"
    assert by_id["claude-account"]["quota"]["windows"][0]["used_percent"] == 99
    assert view["summary"]["quota_known"] == 2  # only provider-keyed route quotas count
    assert "workbuddy" not in quotas and "trae-cn" not in quotas


def test_public_account_rows_carry_no_secret_or_free_text():
    allowed = {"provider", "account_ref", "state", "reason", "observed_at", "usage_scope",
               "windows", "attribution"}
    for account in _view()["account_attribution"]["accounts"]:
        assert set(account) == allowed
        assert all(set(window) == {"window", "used_percent", "remaining_percent", "resets_at",
                                   "unlimited"} for window in account["windows"])
    serialized = str(_view())
    assert "gateway-secret-value" not in serialized
