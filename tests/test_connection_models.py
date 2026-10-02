"""Synthetic and owned-loopback HTTP acceptance of saved catalog APIs."""

from contextlib import contextmanager
from http.client import HTTPConnection, HTTPResponse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading

import pytest

from reverse_agent.model_access.catalog_transport import CatalogTransportError
from reverse_agent.model_access.os_vault import FakeVault
from reverse_agent.model_access.service import _handler_factory, discover_saved_connection_models
from reverse_agent.model_access.store import ModelProfileStore


def configured_store(**overrides):
    store = ModelProfileStore()
    store.upsert_connection({
        "connection_id": "fixture", "name": "Fixture", "provider": "deepseek",
        "base_url": "https://catalog.example.test/v1", "auth_method": "none",
        "enabled": True, **overrides,
    })
    return store


def discover(store, *, transport=None, live_enabled=True, payload=None):
    return discover_saved_connection_models(
        store=store, connection_id="fixture", payload={} if payload is None else payload,
        live_enabled=live_enabled,
        transport=transport or (lambda *_: (200, b'{"data":[{"id":"deepseek-chat"}]}')),
    )


@contextmanager
def running(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(port, path, payload, origin="http://localhost:5173"):
    client = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        client.request("POST", path, json.dumps(payload), {"Content-Type": "application/json", "Origin": origin})
        response = client.getresponse()
        return response.status, json.loads(response.read())
    finally:
        client.close()


def test_real_control_http_catalog_cas_and_recommend_preview_share_saved_store():
    calls = []
    store = configured_store(api_key="synthetic-only-fixture-key", auth_method="api_key")

    def transport(url, headers, timeout):
        calls.append((url, headers, timeout))
        return 200, b'{"data":[{"id":"deepseek-chat","owned_by":"deepseek"}]}'

    with running(_handler_factory(store, live_enabled=True, allowed_origin="http://localhost:5173", catalog_transport=transport)) as port:
        status, catalog = request(port, "/api/connections/fixture/models", {})
        assert status == 200 and catalog["ok"] and catalog["status"] == "advertised"
        assert catalog["models"] == ["deepseek-chat"]
        assert catalog["source"] == "provider_advertised" and catalog["entitlement"] == "not_observed"
        status, binding = request(port, "/api/connections/fixture/models/bindings", {
            "configuration_revision": catalog["configuration_revision"],
            "catalog_revision": catalog["catalog_revision"],
            "executor_id": "opencode", "model_id": "deepseek-chat",
        })
        assert status == 200 and binding["created"]
        assert binding["binding"]["model_id"] == "deepseek/deepseek-chat"
        status, preview = request(port, "/api/model-selections/recommend", {"selection_mode": "automatic"})
        assert status == 200 and preview["preview_only"] is True
        assert preview["recommended"] is None
        assert "readiness_not_observed" in preview["candidates"][0]["reason_codes"]
        assert "synthetic-only-fixture-key" not in json.dumps([catalog, binding, preview])
        assert request(port, "/api/model-selections/recommend", {"allow_gpt": True})[0] == 400
        assert request(port, "/api/connections/fixture/models", {"api_key": "browser-override"})[0] == 400
        assert request(port, "/api/connections/fixture/models", {}, origin="https://foreign.example.test")[0] == 403
    assert len(calls) == 1
    assert calls[0] == ("https://catalog.example.test/v1/models", {"Accept": "application/json", "Authorization": "Bearer synthetic-only-fixture-key"}, 10.0)


def test_production_transport_reads_owned_loopback_catalog_with_saved_synthetic_secret():
    requests = []

    class Upstream(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization")))
            body = b'{"data":[{"id":"deepseek-chat"},{"id":"deepseek-chat"},{"id":"deepseek-reasoner","owned_by":"deepseek"}]}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    with running(Upstream) as port:
        store = configured_store(base_url=f"http://127.0.0.1:{port}/v1", auth_method="api_key", api_key="synthetic-only-loopback")
        result = discover_saved_connection_models(store=store, connection_id="fixture", payload={}, live_enabled=True)
    assert result.ok and result.to_public_dict()["models"] == ["deepseek-chat", "deepseek-reasoner"]
    assert requests == [("/v1/models", "Bearer synthetic-only-loopback")]
    assert "synthetic-only-loopback" not in json.dumps(result.to_public_dict())


def test_default_live_zero_never_resolves_synthetic_vault_or_starts_transport():
    vault = FakeVault()
    store = ModelProfileStore(vault=vault)
    store.upsert_connection({"connection_id": "fixture", "name": "Fixture", "provider": "deepseek", "base_url": "https://catalog.example.test/v1", "auth_method": "api_key", "api_key": "synthetic-vault-only"})
    vault.probe_calls.clear()
    vault.resolve_calls.clear()

    def forbidden(*_):
        raise AssertionError("LIVE0 must not call transport")

    result = discover(store, live_enabled=False, transport=forbidden)
    assert result.status == "live_probe_disabled"
    assert vault.probe_calls == [] and vault.resolve_calls == []
    assert result.to_public_dict()["catalog_revision"] is None


def test_live_zero_with_prior_observation_still_does_not_resolve_credentials():
    vault = FakeVault()
    store = ModelProfileStore(vault=vault)
    store.upsert_connection({"connection_id": "fixture", "name": "Fixture", "provider": "deepseek", "base_url": "https://catalog.example.test/v1", "auth_method": "api_key", "api_key": "synthetic-vault-only"})
    assert discover(store).ok
    vault.probe_calls.clear()
    vault.resolve_calls.clear()
    result = discover(store, live_enabled=False, transport=lambda *_: pytest.fail("LIVE0 no transport"))
    assert result.status == "live_probe_disabled"
    assert vault.probe_calls == [] and vault.resolve_calls == []


@pytest.mark.parametrize("auth_method", ["account_login", "external_cli_session"])
def test_external_auth_is_explicitly_unsupported_without_account_or_cli_access(auth_method, monkeypatch):
    store = configured_store(auth_method=auth_method)
    monkeypatch.setattr(store, "_resolve_stored_secret", lambda *_: pytest.fail("no secret access"))
    result = discover(store, transport=lambda *_: pytest.fail("no transport"))
    assert result.status == "unsupported_auth_method" and not result.ok


@pytest.mark.parametrize("options,status", [({"enabled": False}, "disabled"), ({"auth_method": "api_key"}, "credential_missing"), ({"provider": "unknown"}, "unsupported_protocol")])
def test_closed_prerequisite_states_do_not_call_transport(options, status):
    result = discover(configured_store(**options), transport=lambda *_: pytest.fail("no transport"))
    assert result.status == status and not result.ok
    public = result.to_public_dict()
    assert public["models"] == [] and public["source"] is None
    assert public["observed_at"] is None and public["catalog_revision"] is None


def test_locked_synthetic_vault_is_not_reported_as_missing():
    vault = FakeVault()
    store = ModelProfileStore(vault=vault)
    store.upsert_connection({"connection_id": "fixture", "name": "Fixture", "provider": "deepseek", "base_url": "https://catalog.example.test/v1", "auth_method": "api_key", "api_key": "synthetic-vault-only"})
    vault.locked = True
    assert discover(store, transport=lambda *_: pytest.fail("no transport")).status == "credential_store_locked"


def test_empty_catalog_is_successful_observation_and_never_entitlement():
    result = discover(configured_store(), transport=lambda *_: (200, b'{"data":[]}'))
    assert result.ok and result.status == "empty"
    assert result.catalog_revision and result.observed_at
    assert result.to_public_dict()["entitlement"] == "not_observed"


@pytest.mark.parametrize("body,status", [
    (b'not-json', "invalid_upstream_response"),
    (b'{}', "invalid_upstream_response"),
    (b'[]', "invalid_upstream_response"),
    (b'{"data":{}}', "invalid_upstream_response"),
    (b'{"data":["deepseek-chat"]}', "invalid_upstream_response"),
    (b'{"data":[{"id":""}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":"model\\nsecret"}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":"https://user:pass@host"}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":"sk-synthetic-secret"}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":"model?token=synthetic"}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":false}]}', "invalid_upstream_response"),
    (b'{"data":[{"id":"' + b'a' * 201 + b'"}]}', "invalid_upstream_response"),
    (b'x' * (1_048_576 + 1), "catalog_too_large"),
    (json.dumps({"data": [{"id": "duplicate"}] * 1001}).encode(), "catalog_too_large"),
], ids=lambda value: f"body-{len(value)}" if isinstance(value, bytes) else value)
def test_bad_shape_ids_and_response_bounds_are_closed(body, status):
    store = configured_store()
    result = discover(store, transport=lambda *_: (200, body))
    assert not result.ok and result.status == status
    assert result.to_public_dict()["models"] == []
    assert store.selection_public_snapshot()["catalogs"] == {}


def test_metadata_projection_omits_secrets_urls_controls_and_unknown_objects():
    store = configured_store(auth_method="api_key", api_key="synthetic-key-only")
    raw = {"data": [{"id": "deepseek-chat", "name": "synthetic-key-only", "owned_by": "https://user:pass@host", "secret": "synthetic-key-only", "nested": {"Authorization": "Bearer synthetic-key-only"}}, {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "owned_by": "deepseek"}]}
    result = discover(store, transport=lambda *_: (200, json.dumps(raw).encode()))
    public = result.to_public_dict()
    assert public["model_records"][0] == {"model_id": "deepseek-chat", "display_name": None, "owned_by": None}
    assert public["model_records"][1]["display_name"] == "DeepSeek Reasoner"
    assert "synthetic-key-only" not in json.dumps(public)
    assert "user:pass" not in json.dumps(public)
    result = discover(store, transport=lambda *_: (200, b'{"data":[{"id":"synthetic-key-only"}]}'))
    assert result.status == "invalid_upstream_response"


@pytest.mark.parametrize("code,status", [(302, "redirect_rejected"), (307, "redirect_rejected"), (401, "upstream_http_error"), (503, "upstream_http_error")])
def test_actual_status_is_preserved_as_finite_state_without_error_body_echo(code, status):
    result = discover(configured_store(), transport=lambda *_: (code, b'{"error":"Bearer synthetic-key"}'))
    assert result.status == status and not result.ok
    assert "synthetic-key" not in json.dumps(result.to_public_dict())


@pytest.mark.parametrize("code,status", [("invalid_request", "invalid_connection_url"), ("response_too_large", "catalog_too_large"), ("timeout", "timeout"), ("connection_error", "connection_error"), ("worker_error", "worker_error")])
def test_transport_errors_are_finite_and_no_raw_exception_escapes(code, status):
    def transport(*_):
        raise CatalogTransportError(code)

    result = discover(configured_store(), transport=transport)
    assert result.status == status and not result.ok


def test_arbitrary_exception_is_opaque_and_failed_refresh_removes_old_catalog():
    store = configured_store()
    assert discover(store).ok

    def transport(*_):
        raise RuntimeError("Bearer synthetic-leak https://user:pass@provider")

    result = discover(store, transport=transport)
    assert result.status == "connection_error"
    assert "synthetic-leak" not in json.dumps(result.to_public_dict())
    assert store.selection_public_snapshot()["catalogs"] == {}


def test_configuration_change_and_delete_during_io_discard_stale_success():
    for operation in ("update", "delete"):
        store = configured_store()

        def transport(*_):
            if operation == "update":
                store.upsert_connection({"connection_id": "fixture", "name": "Fixture", "provider": "deepseek", "base_url": "https://catalog.example.test/v1", "auth_method": "none", "enabled": False})
            else:
                store.delete_connection("fixture")
            return 200, b'{"data":[{"id":"deepseek-chat"}]}'

        result = discover(store, transport=transport)
        assert not result.ok and result.status == "configuration_changed"
        assert store.selection_public_snapshot()["catalogs"] == {}


def test_live_zero_http_path_and_payload_overrides_are_checked_before_transport():
    store = configured_store()
    with running(_handler_factory(store, live_enabled=False, allowed_origin="http://localhost:5173", catalog_transport=lambda *_: pytest.fail("LIVE0 transport"))) as port:
        status, result = request(port, "/api/connections/fixture/models", {})
        assert status == 200 and result["status"] == "live_probe_disabled"
        for override in ({"base_url": "http://other"}, {"timeout": 60}, {"allow_gpt": True}):
            assert request(port, "/api/connections/fixture/models", override)[0] == 400
        assert request(port, "/api/connections/missing/models", {})[1]["status"] == "not_found"


@pytest.mark.parametrize("label", ["Model password: x", "model token: s", "secret:s", "Useful Bearer x", "Label api_key: q", "Label Authorization: x", "Label sk-synthetic-other-secret", "Model\u202esecret"])
def test_optional_embedded_credential_labels_and_format_controls_are_omitted(label):
    result = discover(configured_store(), transport=lambda *_: (200, json.dumps({"data": [{"id": "deepseek-chat", "display_name": label, "owned_by": label}]}).encode()))
    assert result.ok
    assert result.to_public_dict()["model_records"] == [{"model_id": "deepseek-chat", "display_name": None, "owned_by": None}]


def test_catalog_network_io_does_not_hold_store_lock():
    from concurrent.futures import ThreadPoolExecutor
    store = configured_store()

    def transport(*_):
        with ThreadPoolExecutor(max_workers=1) as pool:
            update = pool.submit(store.upsert_connection, {"connection_id": "fixture", "name": "Fixture", "provider": "deepseek", "base_url": "https://catalog.example.test/v1", "auth_method": "none", "enabled": False})
            update.result(timeout=2)
        return 200, b'{"data":[{"id":"deepseek-chat"}]}'

    result = discover(store, transport=transport)
    assert not result.ok and result.status == "configuration_changed"


def _assert_fixed_forbidden(response):
    assert response.status == 403
    headers = {key.lower(): value for key, value in response.getheaders()}
    assert headers["connection"].lower() == "close"
    assert "access-control-allow-origin" not in headers
    assert "access-control-allow-methods" not in headers
    assert response.read() == b'{"error":"forbidden"}'


def test_foreign_origin_catalog_body_gets_fixed_403_without_parsing_or_store_change():
    store = configured_store()
    before = store.selection_public_snapshot()
    parsed = threading.Event()
    transport_called = threading.Event()

    def forbidden_transport(*_):
        transport_called.set()
        raise AssertionError("rejected Origin must not invoke catalog transport")

    configured = _handler_factory(
        store, live_enabled=True, allowed_origin="http://localhost:5173",
        catalog_transport=forbidden_transport,
    )

    class RejectionHandler(configured):
        def _read_json(self, *, optional=False):
            parsed.set()
            raise AssertionError("rejected Origin must not parse request JSON")

    payload = json.dumps({"api_key": "synthetic-rejected-body-key", "model_id": "forbidden-override"}).encode()
    with running(RejectionHandler) as port:
        client = HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            client.request("POST", "/api/connections/fixture/models", payload, {
                "Origin": "https://foreign.example.test",
                "Content-Type": "application/json",
            })
            _assert_fixed_forbidden(client.getresponse())
        finally:
            client.close()
    assert not parsed.is_set()
    assert not transport_called.is_set()
    assert store.selection_public_snapshot() == before


@pytest.mark.parametrize("body_delivery", ["missing", "trickle"])
def test_foreign_origin_body_discard_has_absolute_deadline_with_open_peer(body_delivery):
    store = configured_store()
    before = store.selection_public_snapshot()
    finished = threading.Event()
    parsed = threading.Event()
    transport_called = threading.Event()

    def forbidden_transport(*_):
        transport_called.set()
        raise AssertionError("rejected Origin must not invoke catalog transport")

    configured = _handler_factory(
        store, live_enabled=True, allowed_origin="http://localhost:5173",
        catalog_transport=forbidden_transport,
    )

    class ObservedHandler(configured):
        def _read_json(self, *, optional=False):
            parsed.set()
            raise AssertionError("rejected Origin must not parse request JSON")

        def finish(self):
            try:
                super().finish()
            finally:
                finished.set()

    sender_stop = threading.Event()
    sender = None
    with running(ObservedHandler) as port:
        peer = socket.create_connection(("127.0.0.1", port), timeout=2)
        try:
            peer.sendall(
                b"POST /api/connections/fixture/models HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\nOrigin: https://foreign.example.test\r\n"
                b"Content-Type: application/json\r\nContent-Length: 4096\r\n\r\n"
            )
            if body_delivery == "trickle":
                def send_trickle():
                    # Each byte arrives sooner than the server's per-read timeout.
                    # A resettable timeout alone therefore cannot finish this peer.
                    while not sender_stop.wait(0.02):
                        try:
                            peer.sendall(b"x")
                        except OSError:
                            return

                sender = threading.Thread(target=send_trickle, daemon=True)
                sender.start()
            response = HTTPResponse(peer)
            try:
                response.begin()
                _assert_fixed_forbidden(response)
                # Keep the owning socket open: EOF must not be the reason that
                # draining ends. This permits ample Windows scheduling slack.
                assert finished.wait(1), "rejected body drain exceeded its absolute deadline"
            finally:
                response.close()
        finally:
            sender_stop.set()
            if sender is not None:
                sender.join(timeout=1)
            peer.close()
    assert not parsed.is_set()
    assert not transport_called.is_set()
    assert store.selection_public_snapshot() == before
