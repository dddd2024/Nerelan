"""Fixture-only checks for the one-time legacy API → Magpie migration report (#1170)."""

from io import BytesIO
import json

from reverse_agent.model_access import magpie_migration
from reverse_agent.model_access.magpie_migration import build_report, magpie_model_id, main


def state():
    return {
        "schema_version": 1,
        "magpie": {"enabled": True, "executable": "C:/m/magpie.exe", "base_url": "http://127.0.0.1:3425"},
        "connections": [
            {"connection_id": "openrouter", "auth_method": "api_key", "base_url": "https://openrouter.ai/api/v1", "enabled": True},
            {"connection_id": "groq", "auth_method": "api_key", "base_url": "https://api.groq.com/openai/v1", "enabled": True},
            {"connection_id": "relay", "auth_method": "api_key", "base_url": "https://relay.example.test/v1", "enabled": True},
            {"connection_id": "claude-account", "auth_method": "external_cli_session", "base_url": "https://claude.ai", "enabled": True},
            {"connection_id": "magpie", "auth_method": "api_key", "base_url": "http://127.0.0.1:3425/v1", "enabled": True},
        ],
        "bindings": [
            {"binding_id": "or-glm", "connection_id": "openrouter", "executor_id": "opencode",
             "model_id": "litellm-proxy/z-ai/glm-5.2", "enabled": False},
            {"binding_id": "or-kimi", "connection_id": "openrouter", "executor_id": "opencode",
             "model_id": "moonshot/kimi-k3", "enabled": True},
            {"binding_id": "mp-or-glm", "connection_id": "magpie", "executor_id": "opencode",
             "model_id": "openrouter/z-ai/glm-5.2", "enabled": True},
            {"binding_id": "claude-opus", "connection_id": "claude-account", "executor_id": "claude_code",
             "model_id": "opus", "enabled": True},
        ],
    }


def snapshot(*model_ids, status="available"):
    return {"status": status, "version": "0.1.1275", "reason": None if status == "available" else "request_failed",
            "models": [{"model_id": m} for m in model_ids]}


def rows(report):
    return {row["connection_id"]: row for row in report["connections"]}


def test_model_id_drops_litellm_prefix_and_keeps_namespaces():
    assert magpie_model_id("openrouter", "litellm-proxy/z-ai/glm-5.2") == "openrouter/z-ai/glm-5.2"
    assert magpie_model_id("mistral", "codestral-latest") == "mistral/codestral-latest"


def test_classifies_native_gateway_and_candidates():
    report = build_report(state(), snapshot("openrouter/z-ai/glm-5.2", "copilot/auto"))
    by_id = rows(report)
    assert by_id["claude-account"]["action"] == "KEEP_NATIVE"
    assert by_id["magpie"]["action"] == "MAGPIE_GATEWAY"
    assert by_id["openrouter"]["status"] == "IMPORTED"
    assert by_id["groq"]["status"] == "NOT_IMPORTED"
    # A host with no default mapping is not guessed.
    assert by_id["relay"]["status"] == "UNKNOWN" and by_id["relay"]["reason"] == "no_magpie_provider_mapping"
    assert report["summary"] == {"candidates": 3, "imported": 1, "tested": 0, "complete": False}


def test_binding_proposals_report_listing_and_existing_magpie_binding():
    bindings = {b["binding_id"]: b for b in rows(build_report(state(), snapshot("openrouter/z-ai/glm-5.2")))["openrouter"]["bindings"]}
    assert bindings["or-glm"] == {
        "binding_id": "or-glm", "enabled": False, "executor_id": "opencode",
        "legacy_model_id": "litellm-proxy/z-ai/glm-5.2", "magpie_model_id": "openrouter/z-ai/glm-5.2",
        "model_listed": True, "magpie_binding_id": "mp-or-glm",
    }
    assert bindings["or-kimi"]["model_listed"] is False and bindings["or-kimi"]["magpie_binding_id"] is None


def test_sensenova_host_maps_to_magpie_provider_id():
    data = state()
    data["connections"].append({"connection_id": "deepseek-flash", "auth_method": "api_key",
                                "base_url": "https://token.sensenova.cn/v1", "enabled": True})
    data["bindings"].append({"binding_id": "coding-glm", "connection_id": "deepseek-flash",
                             "executor_id": "opencode", "model_id": "glm-5.2", "enabled": True})
    row = rows(build_report(data, snapshot("token-sensenova/glm-5.2")))["deepseek-flash"]
    assert row["magpie_provider"] == "token-sensenova" and row["status"] == "IMPORTED"
    assert row["bindings"][0]["magpie_model_id"] == "token-sensenova/glm-5.2"
    assert row["bindings"][0]["model_listed"] is True


def test_override_maps_custom_vendor():
    report = build_report(state(), snapshot("my-relay/x"), provider_overrides={"relay": "my-relay"})
    assert rows(report)["relay"]["status"] == "IMPORTED"


def test_unavailable_magpie_never_reports_not_imported():
    report = build_report(state(), snapshot(status="unavailable"))
    by_id = rows(report)
    assert by_id["openrouter"]["status"] == "UNKNOWN" and by_id["openrouter"]["reason"] == "magpie_unavailable"
    assert all(b["model_listed"] is False for b in by_id["openrouter"]["bindings"])
    assert report["summary"]["imported"] == 0


class _Response:
    def __init__(self, body):
        self._body = BytesIO(json.dumps(body).encode())

    def getcode(self):
        return 200

    def read(self):
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_cli_reads_state_and_only_issues_get_requests(tmp_path, monkeypatch, capsys):
    path = tmp_path / "model_setup_state.json"
    path.write_text(json.dumps(state()), encoding="utf-8")
    before = path.read_bytes()
    requests = []
    bodies = {"/api/hello": {"name": "magpie", "version": "0.1.1275"},
              "/v1/models": {"object": "list", "data": [{"id": "groq/llama-4"}]},
              "/v1/magpie/quotas?kept=1": {"object": "list", "data": []}}

    def opener(request, timeout):
        requests.append((request.get_method(), request.full_url))
        return _Response(bodies[request.full_url.removeprefix("http://127.0.0.1:3425")])

    real_fetch = magpie_migration.fetch_magpie_snapshot
    monkeypatch.setattr(magpie_migration, "fetch_magpie_snapshot", lambda url: real_fetch(url, opener=opener))
    assert main(["--state", str(path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert rows(report)["groq"]["status"] == "IMPORTED"
    assert {method for method, _ in requests} == {"GET"}
    assert path.read_bytes() == before
