"""Read-only discovery from live resource view shapes, never a daily reward claim."""

from reverse_agent.model_access.reward_opportunities import discover_reward_opportunities


def test_only_provider_identity_is_used_and_credentials_not_echoed():
    snapshot = {"resources": [{
        "upstream_provider_id": "trae-work",
        "connection_id": "private_id_not_for_frontend",
        "api_key": "secret_do_not_read",
        "name": "private-account-name",
    }]}
    data = discover_reward_opportunities(snapshot)
    assert data["status"] == "CANDIDATES_FOUND"
    item = data["candidates"][0]
    assert item["kind"] == "DAILY_CHECK_IN"
    assert item["source"] == "model_connection"
    assert item["action"] == "VERIFY_FIRST_PARTY_UI"
    assert item["can_auto_claim"] is False and item["claim_performed"] is False
    assert "private_id" not in repr(data) and "secret_do_not" not in repr(data)
    assert "private-account" not in repr(data)


def test_magpie_disabled_does_not_invent_usable_accounts():
    data = discover_reward_opportunities({
        "resources": [], "external_sources": {"magpie": {"status": "disabled"}}
    })
    assert data["status"] == "NOT_CONFIGURED_OR_UNVERIFIED"
    assert data["magpie_status"] == "disabled"
    assert data["candidates"] == []


def test_magpie_account_is_only_an_unverified_candidate():
    data = discover_reward_opportunities({
        "external_sources": {"magpie": {"status": "available", "accounts": [
            {"provider": "traework", "account_ref": "opaque12345678"},
            {"provider": "workbuddy", "account_ref": "opaque24681357"},
        ]}}
    })
    assert {r["kind"] for r in data["candidates"]} == {
        "DAILY_CHECK_IN", "ACTIVITY_REWARD_AUTO"}
    assert all(r["account_verified"] is False for r in data["candidates"])
    assert all(r["can_auto_claim"] is False for r in data["candidates"])


def test_running_workbuddy_is_not_evidence_of_login():
    data = discover_reward_opportunities({}, process_names=["WorkBuddy", "WorkBuddy"])
    assert len(data["candidates"]) == 1
    assert data["candidates"][0]["kind"] == "ACTIVITY_REWARD_AUTO"
    assert data["candidates"][0]["action"] == "NO_CHECK_IN"
    assert data["candidates"][0]["account_verified"] is False


def test_historic_trae_solo_process_name_does_not_claim_reward():
    data = discover_reward_opportunities({}, process_names=["TRAE SOLO CN"])
    assert data["candidates"][0]["service"] == "TRAE Work"
    assert data["candidates"][0]["can_auto_claim"] is False


def test_unknown_or_malformed_providers_are_ignored_without_false_claims():
    data = discover_reward_opportunities({
        "resources": [None, {"upstream_provider_id": ["bad"], "connection_id": "x"},
                      {"upstream_provider_id": "trae-work-lookalike", "connection_id": "x"}],
        "external_sources": {"magpie": {"status": "available", "accounts": [
            {}, {"provider": "traework", "account_ref": ["bad"]}]}},
    }, process_names=[None, "magpie", "trae-work-lookalike"])
    assert data["candidates"] == [] and data["actual_claims"] == 0


def test_passive_subscription_quota_is_not_signin():
    data = discover_reward_opportunities({"resources": [
        {"upstream_provider_id": "codex", "connection_id": "connection-1"},
        {"upstream_provider_id": "claude", "connection_id": "connection-2"}]})
    assert len(data["candidates"]) == 2
    assert all(x["kind"] == "PASSIVE_QUOTA_RESET" for x in data["candidates"])
    assert all(x["action"] == "NO_CHECK_IN" for x in data["candidates"])


def test_model_control_serves_read_only_opportunities_from_same_resource_model(
    tmp_path, monkeypatch,
):
    import json
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.request import Request, urlopen

    from reverse_agent.model_access import reward_opportunities as adapter
    from reverse_agent.model_access import service

    class FakeStore:
        def get_magpie(self):
            return {"enabled": False}

    def model_view(*args, **kwargs):
        assert kwargs["mode"] == "hybrid"
        return {"resources": [{
            "upstream_provider_id": "trae-work", "connection_id": "private-connection"
        }], "external_sources": {"magpie": {"status": "disabled"}}}

    monkeypatch.setattr(service, "build_resource_view", model_view)
    monkeypatch.setattr(adapter, "running_reward_app_names", lambda: [])
    monkeypatch.setenv("REVERSE_AGENT_MAGPIE_ENABLED", "0")
    handler = service._handler_factory(
        FakeStore(), live_enabled=False, allowed_origin="http://localhost:5173"
    )
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{srv.server_port}/api/reward-opportunities",
            headers={"Origin": "http://localhost:5173"},
        )
        with urlopen(request, timeout=3) as response:
            result = json.load(response)
        assert result["candidates"][0]["service"] == "TRAE Work"
        assert result["candidates"][0]["can_auto_claim"] is False
        assert result["actual_claims"] == 0
        assert "private-connection" not in json.dumps(result)
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)
