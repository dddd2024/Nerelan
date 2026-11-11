"""Explicit native/Magpie identity confirmation, without servers or external reads."""
from copy import deepcopy
from http import HTTPStatus

import pytest

from reverse_agent.model_access import service
from reverse_agent.model_access.resources import build_resource_view, native_account_link_suggestions
from reverse_agent.model_access.store import ModelProfileStore


REF = "abcdef123456"


def connection(provider="codex", **extra):
    return dict(connection_id="native", name="Native", provider=provider,
                executor_provider_id=provider, upstream_provider_id="openai" if provider == "codex" else "anthropic",
                protocol_family="codex-cli" if provider == "codex" else "claude-code-cli",
                base_url="https://example.test", auth_method="external_cli_session", enabled=True, **extra)


def snapshot(provider="codex", refs=(REF,)):
    return {"status": "available", "accounts": [
        {"provider": provider, "account_ref": ref, "plan": "plus"} for ref in refs]}


@pytest.mark.parametrize("provider,external", [("codex", "codex"), ("claude-code", "claude")])
def test_unique_account_is_only_a_suggestion(provider, external):
    c = connection(provider)
    original = deepcopy(c)
    assert native_account_link_suggestions([c], snapshot(external)) == {
        "native": {"account_ref": REF, "provider": external, "plan": "plus"}}
    assert c == original


@pytest.mark.parametrize("accounts", [(), (REF, "other")])
def test_zero_or_several_accounts_are_not_suggested(accounts):
    assert not native_account_link_suggestions([connection()], snapshot(refs=accounts))


@pytest.mark.parametrize("status", ["disabled", "unavailable", "refused"])
def test_magpie_must_be_available(status):
    assert not native_account_link_suggestions([connection()], dict(snapshot(), status=status))


def test_claimed_ref_including_disabled_connections_is_not_suggested():
    assert not native_account_link_suggestions([
        connection(), dict(connection(), connection_id="other", enabled=False, account_ref=REF)], snapshot())


@pytest.mark.parametrize("change", [{"enabled": False}, {"auth_method": "api_key"}, {"account_ref": REF}])
def test_only_enabled_unlinked_cli_sessions_are_suggested(change):
    assert not native_account_link_suggestions([dict(connection(), **change)], snapshot())


def handler(store, payload, action="link-magpie-account"):
    # Exercise the real POST dispatch and Origin gate without constructing a server.
    h = service._ModelControlHandler.__new__(service._ModelControlHandler)
    h.store = store
    h.headers = {}
    h.path = f"/api/connections/native/{action}"
    h._read_json = lambda: payload
    responses = []
    h._send_json = lambda status, body: responses.append((status, body))
    return h, responses


def test_post_rechecks_live_snapshot_and_saves_only_identity(monkeypatch, tmp_path):
    store = ModelProfileStore(tmp_path / "state.json")
    store.upsert_connection(connection())
    before = store.get_connection_public("native")
    monkeypatch.setenv("REVERSE_AGENT_MAGPIE", "1")
    live = snapshot()
    monkeypatch.setattr(service, "_magpie_external", lambda: live)
    offered = build_resource_view(store, dict, external=lambda: live)
    assert offered["resources"][0]["magpie_link_suggestion"]["account_ref"] == REF
    assert "account_ref" not in store.get_connection_public("native")

    live = snapshot(refs=(REF, "second"))
    h, responses = handler(store, {"account_ref": REF})
    h.do_POST()
    assert responses[-1][0] == HTTPStatus.BAD_REQUEST
    assert store.get_connection_public("native") == before

    live = snapshot()
    h.do_POST()
    assert responses[-1] == (HTTPStatus.OK, dict(before, account_ref=REF))
    reloaded = ModelProfileStore(tmp_path / "state.json").get_connection_public("native")
    assert reloaded["account_ref"] == REF
    # Session readiness is derived again at startup, independently of saved identity.
    assert {k: v for k, v in reloaded.items() if k != "external_session_status"} == {
        k: v for k, v in dict(before, account_ref=REF).items() if k != "external_session_status"}
    linked = build_resource_view(store, dict)["resources"][0]
    assert linked["magpie_account_ref"] == REF
    assert "magpie_link_suggestion" not in linked

    def unavailable():
        raise AssertionError("unlink must not fetch Magpie")
    monkeypatch.setattr(service, "_magpie_external", unavailable)
    h, responses = handler(store, {}, "unlink-magpie-account")
    h.do_POST()
    assert responses[-1] == (HTTPStatus.OK, before)
    assert "account_ref" not in ModelProfileStore(tmp_path / "state.json").get_connection_public("native")


@pytest.mark.parametrize("payload", [{}, {"account_ref": None}, {"account_ref": ""},
                                      {"account_ref": REF, "enabled": False}, {"account_ref": "wrong"}])
def test_post_rejects_invalid_or_unsuggested_link(monkeypatch, payload):
    store = ModelProfileStore()
    store.upsert_connection(connection())
    before = store.get_connection_public("native")
    h, responses = handler(store, payload)
    h._magpie_source = lambda: lambda: snapshot()
    h.do_POST()
    assert responses[-1][0] == HTTPStatus.BAD_REQUEST
    assert store.get_connection_public("native") == before


def test_resources_use_one_snapshot_in_every_view_mode():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    for mode in ("legacy", "hybrid", "magpie_primary"):
        calls = []
        def read():
            calls.append(True)
            return snapshot()
        view = build_resource_view(store, dict, external=read, mode=mode)
        assert len(calls) == 1
        assert view["resources"][0]["magpie_link_suggestion"]["account_ref"] == REF
    assert "magpie_link_suggestion" not in build_resource_view(store, dict)["resources"][0]


@pytest.mark.parametrize("case", ["off", "unreachable", "zero", "claimed"])
def test_accept_rechecks_disabled_unreachable_empty_or_claimed_accounts(monkeypatch, case):
    store = ModelProfileStore()
    store.upsert_connection(connection())
    before = store.get_connection_public("native")
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
    h, responses = handler(store, {"account_ref": REF})
    if case != "off":
        monkeypatch.setenv("REVERSE_AGENT_MAGPIE", "1")
    if case == "claimed":
        store.upsert_connection(dict(connection(account_ref=REF), connection_id="other"))
    def read():
        if case == "off":
            pytest.fail("disabled Magpie must not be fetched")
        if case == "unreachable":
            raise OSError("unreachable")
        return snapshot(refs=() if case == "zero" else (REF,))
    monkeypatch.setattr(service, "_magpie_external", read)
    h.do_POST()
    assert responses[-1][0] == HTTPStatus.BAD_REQUEST
    assert store.get_connection_public("native") == before


def test_link_action_keeps_the_existing_origin_gate():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    h, responses = handler(store, {"account_ref": REF})
    h.headers = {"Origin": "https://untrusted.example.test"}
    h._send_forbidden = lambda: responses.append((HTTPStatus.FORBIDDEN, {}))
    h._magpie_source = lambda: pytest.fail("origin must be checked before external reads")
    h.do_POST()
    assert responses == [(HTTPStatus.FORBIDDEN, {})]
    assert "account_ref" not in store.get_connection_public("native")
