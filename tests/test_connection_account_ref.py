from __future__ import annotations

from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import threading
from typing import Any

import pytest

from reverse_agent.model_access import store as store_module
from reverse_agent.model_access.contracts import Connection
from reverse_agent.model_access.service import _handler_factory
from reverse_agent.model_access.store import ModelProfileStore, StoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


BASE_PUBLIC_KEYS = {
    "connection_id",
    "name",
    "provider",
    "upstream_provider_id",
    "protocol_family",
    "executor_provider_id",
    "base_url",
    "anthropic_base_url",
    "auth_method",
    "enabled",
    "credential_configured",
    "secret_status",
    "external_session_status",
}

INVALID_ACCOUNT_REFS: list[Any] = [
    True,
    False,
    0,
    12,
    ["acct-a"],
    {"id": "acct-a"},
    object(),
    "",
    " ",
    "   ",
    " acct-a",
    "acct-a ",
    "\tacct-a",
    "acct-a\n",
    "acct\x00a",
    "acct\x7fa",
    "acct a",
    "Acct-A",
    "user@example.com",
    "https://example.com/acct",
    "acct:a",
    "acct/a",
    "a" * 81,
]


class FakeVault:
    """In-memory stand-in for the OS credential store; records every method call."""

    def __init__(self) -> None:
        self.items: dict[str, str] = {}
        self.calls: list[tuple[str, str]] = []

    def store(self, ref: str, secret: str) -> None:
        self.calls.append(("store", ref))
        self.items[ref] = secret

    def resolve(self, ref: str) -> str:
        self.calls.append(("resolve", ref))
        return self.items[ref]

    def delete(self, ref: str) -> None:
        self.calls.append(("delete", ref))
        self.items.pop(ref, None)

    def probe(self, ref: str) -> str:
        self.calls.append(("probe", ref))
        return "available" if ref in self.items else "missing"


def connection_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "connection_id": "sense-api",
        "name": "SenseNova API",
        "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _public(connection: Connection) -> dict[str, Any]:
    return connection.to_public_dict(
        credential_configured=False,
        secret_status="missing",
        external_session_status="not_applicable",
    )


def test_both_aliases_parse_to_the_same_public_field() -> None:
    snake = Connection.from_mapping(connection_payload(account_ref="acct-a"))
    camel = Connection.from_mapping(connection_payload(accountRef="acct-a"))

    assert snake.account_ref == camel.account_ref == "acct-a"
    assert _public(snake)["account_ref"] == "acct-a"
    assert "accountRef" not in _public(camel)


def test_equal_aliases_are_accepted_and_differing_aliases_are_rejected() -> None:
    both = Connection.from_mapping(connection_payload(account_ref="acct-a", accountRef="acct-a"))
    assert both.account_ref == "acct-a"

    with pytest.raises(ValueError, match="must match"):
        Connection.from_mapping(connection_payload(account_ref="acct-a", accountRef="acct-b"))
    # An explicit null beside a value is ambiguous too, so it is not silently resolved.
    with pytest.raises(ValueError, match="must match"):
        Connection.from_mapping(connection_payload(account_ref=None, accountRef="acct-b"))


@pytest.mark.parametrize("value", ["a" * 80, "0123456789ab", "account-a", "acct_01.a-b"])
def test_legitimate_opaque_refs_are_accepted_verbatim(value: str) -> None:
    assert Connection.from_mapping(connection_payload(account_ref=value)).account_ref == value
    assert Connection.from_mapping(connection_payload(accountRef=value)).account_ref == value


@pytest.mark.parametrize("value", INVALID_ACCOUNT_REFS, ids=repr)
def test_invalid_account_ref_is_rejected_without_echoing_it(value: Any) -> None:
    with pytest.raises(ValueError) as mapping_error:
        Connection.from_mapping(connection_payload(account_ref=value))
    with pytest.raises(ValueError) as constructor_error:
        Connection(
            connection_id="sense-api",
            name="SenseNova API",
            provider="openai-compatible",
            base_url="https://models.example.test/v1",
            auth_method="api_key",
            account_ref=value,
        )
    with pytest.raises(ValueError):
        Connection.from_mapping(connection_payload(accountRef=value))

    if isinstance(value, str) and len(value) >= 3:
        for error in (mapping_error, constructor_error):
            assert value not in str(error.value)


def test_absent_account_ref_keeps_public_shape_and_stays_unbound() -> None:
    connection = Connection.from_mapping(connection_payload())
    assert connection.account_ref is None
    assert set(_public(connection)) == BASE_PUBLIC_KEYS
    assert Connection.from_mapping(connection_payload(account_ref=None)).account_ref is None


def test_same_provider_connections_keep_distinct_and_shared_refs(tmp_path) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(connection_id="acct-one", account_ref="acct-a"))
    store.upsert_connection(connection_payload(connection_id="acct-two", account_ref="acct-b"))
    store.upsert_connection(connection_payload(connection_id="acct-shared", account_ref="acct-a"))

    listed = store.list_connections_public()
    assert {item["provider"] for item in listed} == {"openai-compatible"}
    assert {item["connection_id"]: item.get("account_ref") for item in listed} == {
        "acct-one": "acct-a",
        "acct-two": "acct-b",
        "acct-shared": "acct-a",
    }


def test_account_ref_survives_public_save_and_reload(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    created = store.upsert_connection(connection_payload(account_ref="acct-a"))
    assert created["account_ref"] == "acct-a"

    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 2
    assert document["connections"][0]["account_ref"] == "acct-a"

    reloaded = ModelProfileStore(state_path=path)
    assert reloaded.get_connection_public("sense-api") == created


def test_documents_without_account_ref_load_unchanged(tmp_path) -> None:
    v2_path = tmp_path / "v2.json"
    ModelProfileStore(state_path=v2_path).upsert_connection(connection_payload())
    assert "account_ref" not in json.loads(v2_path.read_text(encoding="utf-8"))["connections"][0]
    assert "account_ref" not in ModelProfileStore(state_path=v2_path).get_connection_public("sense-api")

    v1_path = tmp_path / "v1.json"
    v1_path.write_text(json.dumps({
        "schema_version": 1,
        "connections": [{
            "connection_id": "legacy-api",
            "name": "Legacy API",
            "provider": "openai-compatible",
            "base_url": "https://models.example.test/v1",
            "auth_method": "api_key",
        }],
        "bindings": [],
    }), encoding="utf-8")
    before = v1_path.read_bytes()
    legacy = ModelProfileStore(state_path=v1_path)
    assert "account_ref" not in legacy.get_connection_public("legacy-api")
    assert v1_path.read_bytes() == before


def test_schema_v1_stays_strict_and_rejects_account_ref(tmp_path) -> None:
    path = tmp_path / "v1.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "connections": [{
            "connection_id": "legacy-api",
            "name": "Legacy API",
            "provider": "openai-compatible",
            "base_url": "https://models.example.test/v1",
            "auth_method": "api_key",
            "account_ref": "acct-a",
        }],
        "bindings": [],
    }), encoding="utf-8")
    with pytest.raises(StoreError):
        ModelProfileStore(state_path=path)


@pytest.mark.parametrize(
    "value",
    ["user@example.com", "https://example.com/acct", "Acct-A", True, ["acct-a"], ""],
    ids=repr,
)
def test_malformed_persisted_account_ref_fails_closed_without_rewriting_file(tmp_path, value) -> None:
    path = tmp_path / "state.json"
    ModelProfileStore(state_path=path).upsert_connection(connection_payload())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["connections"][0]["account_ref"] = value
    path.write_text(json.dumps(document), encoding="utf-8")
    before = path.read_bytes()

    with pytest.raises(StoreError):
        ModelProfileStore(state_path=path)
    assert path.read_bytes() == before


def test_explicit_null_clears_mapping_while_omitted_field_preserves_it(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a"))

    preserved = store.upsert_connection(connection_payload(name="Renamed"))
    assert preserved["name"] == "Renamed"
    assert preserved["account_ref"] == "acct-a"

    cleared = store.upsert_connection(connection_payload(account_ref=None))
    assert "account_ref" not in cleared
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")

    store.upsert_connection(connection_payload(account_ref="acct-b"))
    cleared_camel = store.upsert_connection(connection_payload(accountRef=None))
    assert "account_ref" not in cleared_camel


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"base_url": "https://other.example.test/v1"}, "authority-bearing connection field changed"),
        ({"provider": "deepseek"}, "authority-bearing connection field changed"),
        ({"anthropic_base_url": "https://relay.example.test/anthropic"}, "authority-bearing connection field changed"),
        ({"auth_method": "account_login"}, "configured API-key credential would be discarded"),
    ],
    ids=["base_url", "provider", "anthropic_base_url", "auth_method"],
)
def test_authority_change_still_rejects_and_keeps_existing_mapping(tmp_path, overrides, match) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))
    before = store.get_connection_public("sense-api")

    # Rejected changes leave the saved mapping, endpoint and credential metadata exactly as they were.
    with pytest.raises(ValueError, match=match):
        store.upsert_connection(connection_payload(account_ref="acct-b", **overrides))
    assert store.get_connection_public("sense-api") == before
    assert before["account_ref"] == "acct-a"
    assert before["base_url"] == "https://models.example.test/v1"
    assert store.resolve_connection_secret("sense-api") == "fake-key-one"


def test_rejected_authority_change_leaves_vault_credential_untouched(tmp_path) -> None:
    vault = FakeVault()
    store = ModelProfileStore(state_path=tmp_path / "state.json", vault=vault)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-vault-key"))
    vault.calls.clear()

    with pytest.raises(ValueError, match="authority-bearing connection field changed"):
        store.upsert_connection(connection_payload(base_url="https://other.example.test/v1"))

    # The rejection happens before any vault read, write or delete.
    assert [call for call in vault.calls if call[0] != "probe"] == []
    current = store.get_connection_public("sense-api")
    assert current["base_url"] == "https://models.example.test/v1"
    assert current["account_ref"] == "acct-a"
    assert current["credential_configured"] is True
    assert store.resolve_connection_secret("sense-api") == "fake-vault-key"


def test_authority_change_with_replacement_and_omitted_mapping_clears_to_unbound(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    # A replacement credential proves no identity, so the old account binding is not inherited.
    replaced = store.upsert_connection(connection_payload(
        base_url="https://other.example.test/v1",
        api_key="fake-key-two",
    ))
    assert replaced["base_url"] == "https://other.example.test/v1"
    assert "account_ref" not in replaced
    assert "account_ref" not in json.loads(path.read_text(encoding="utf-8"))["connections"][0]
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")
    assert store.resolve_connection_secret("sense-api") == "fake-key-two"

    # Later ordinary edits on the new authority keep it unbound rather than resurrecting acct-a.
    renamed = store.upsert_connection(connection_payload(base_url="https://other.example.test/v1", name="Renamed"))
    assert "account_ref" not in renamed


@pytest.mark.parametrize("alias", ["account_ref", "accountRef"])
def test_authority_change_honors_explicit_mapping_on_new_authority(tmp_path, alias) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    replaced = store.upsert_connection(connection_payload(
        base_url="https://other.example.test/v1",
        api_key="fake-key-two",
        **{alias: "acct-new"},
    ))
    assert replaced["account_ref"] == "acct-new"
    assert ModelProfileStore(state_path=path).get_connection_public("sense-api")["account_ref"] == "acct-new"

    # The explicitly confirmed mapping is then an ordinary saved value for name-only edits.
    renamed = store.upsert_connection(connection_payload(base_url="https://other.example.test/v1", name="Renamed"))
    assert renamed["account_ref"] == "acct-new"


def test_authority_change_with_explicit_null_clears_mapping(tmp_path) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    cleared = store.upsert_connection(connection_payload(
        base_url="https://other.example.test/v1",
        api_key="fake-key-two",
        account_ref=None,
    ))
    assert "account_ref" not in cleared
    assert cleared["credential_configured"] is True


def test_authority_change_with_clear_secret_clears_mapping(tmp_path) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    cleared = store.upsert_connection(connection_payload(
        base_url="https://other.example.test/v1",
        clear_secret=True,
    ))
    assert "account_ref" not in cleared
    assert cleared["credential_configured"] is False


def test_auth_method_change_with_clear_secret_clears_mapping(tmp_path) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    changed = store.upsert_connection(connection_payload(auth_method="account_login", clear_secret=True))
    assert "account_ref" not in changed
    assert changed["auth_method"] == "account_login"


def test_vault_backed_authority_change_clears_mapping_and_rotates_credential(tmp_path) -> None:
    vault = FakeVault()
    store = ModelProfileStore(state_path=tmp_path / "state.json", vault=vault)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-vault-key"))

    replaced = store.upsert_connection(connection_payload(
        base_url="https://other.example.test/v1",
        api_key="fake-vault-key-two",
    ))
    assert "account_ref" not in replaced
    assert replaced["credential_configured"] is True
    assert store.resolve_connection_secret("sense-api") == "fake-vault-key-two"


@pytest.mark.parametrize(
    "overrides",
    [
        {"base_url": "https://models.example.test/v1/"},
        {"name": "Renamed"},
    ],
    ids=["normalized-base-url", "name-only"],
)
def test_omitted_mapping_is_preserved_when_authority_is_unchanged(tmp_path, overrides) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    # A trailing slash normalizes away, so no authority delta exists and no credential is required.
    updated = store.upsert_connection(connection_payload(**overrides))
    assert updated["account_ref"] == "acct-a"
    assert updated["credential_configured"] is True
    assert store.resolve_connection_secret("sense-api") == "fake-key-one"


def test_mapping_only_edit_leaves_vault_credentials_untouched(tmp_path) -> None:
    vault = FakeVault()
    store = ModelProfileStore(state_path=tmp_path / "state.json", vault=vault)
    store.upsert_connection(connection_payload(api_key="fake-vault-key"))
    vault.calls.clear()

    updated = store.upsert_connection(connection_payload(account_ref="acct-a"))

    assert updated["account_ref"] == "acct-a"
    assert updated["credential_configured"] is True
    # The response path probes availability for status only; no value is read, written or deleted.
    assert [call for call in vault.calls if call[0] != "probe"] == []
    assert store.resolve_connection_secret("sense-api") == "fake-vault-key"


@pytest.fixture()
def http_service(tmp_path):
    state_path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=state_path)
    handler = _handler_factory(
        store,
        live_enabled=False,
        allowed_origin="http://localhost:5173",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1]), state_path
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def api_request(
    port: int,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"Content-Length": str(len(body))}
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    connection.close()
    return response.status, response_body


def test_http_boundary_roundtrips_account_ref_and_reloads(http_service) -> None:
    port, state_path = http_service

    status, created = api_request(
        port, "PUT", "/api/connections/sense-api", connection_payload(accountRef="acct-a"),
    )
    assert status == 200
    assert created["account_ref"] == "acct-a"
    status, fetched = api_request(port, "GET", "/api/connections/sense-api")
    assert status == 200 and fetched == created

    status, renamed = api_request(
        port, "PUT", "/api/connections/sense-api", connection_payload(name="Renamed"),
    )
    assert status == 200 and renamed["account_ref"] == "acct-a"

    status, rejected = api_request(
        port, "PUT", "/api/connections/sense-api", connection_payload(account_ref="user@example.com"),
    )
    assert 400 <= status < 500
    assert "user@example.com" not in json.dumps(rejected)

    status, updated = api_request(
        port, "PUT", "/api/connections/sense-api", connection_payload(account_ref="acct-b"),
    )
    assert status == 200 and updated["account_ref"] == "acct-b"
    assert ModelProfileStore(state_path=state_path).get_connection_public("sense-api")["account_ref"] == "acct-b"

    status, cleared = api_request(
        port, "PUT", "/api/connections/sense-api", connection_payload(account_ref=None),
    )
    assert status == 200 and "account_ref" not in cleared
    assert "account_ref" not in ModelProfileStore(state_path=state_path).get_connection_public("sense-api")


# ---- identity lifetime: a credential source change never inherits the saved account ----

def _fail_state_write(*_args: Any, **_kwargs: Any) -> None:
    raise OSError("synthetic state write failure")


def _selected_candidates(connection: dict[str, Any], quotas: dict[str, Any]) -> list[Any]:
    # The real host selector reads no instance state, so it is called without a host.
    return CombinedTrustedHost._account_quota_candidates(None, connection, quotas)


@pytest.mark.parametrize("vault_backed", [False, True], ids=["process-local", "fake-vault"])
@pytest.mark.parametrize("key_alias", ["api_key", "apiKey"])
def test_same_endpoint_key_replacement_clears_mapping_and_survives_reopen(
    tmp_path, vault_backed, key_alias,
) -> None:
    path = tmp_path / "state.json"
    vault = FakeVault() if vault_backed else None
    store = ModelProfileStore(state_path=path, vault=vault)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    replaced = store.upsert_connection(connection_payload(**{key_alias: "fake-key-two"}))
    assert "account_ref" not in replaced
    assert replaced["credential_configured"] is True
    assert store.resolve_connection_secret("sense-api") == "fake-key-two"

    reopened = ModelProfileStore(state_path=path, vault=vault)
    assert "account_ref" not in reopened.get_connection_public("sense-api")
    assert "account_ref" not in json.loads(path.read_text(encoding="utf-8"))["connections"][0]
    if vault_backed:
        assert reopened.resolve_connection_secret("sense-api") == "fake-key-two"


@pytest.mark.parametrize("env_alias", ["api_key_env", "apiKeyEnv"])
def test_env_pointer_switch_and_reassertion_clear_mapping(tmp_path, env_alias) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key_env="FAKE_ACCOUNT_A_ENV"))

    switched = store.upsert_connection(connection_payload(**{env_alias: "FAKE_ACCOUNT_B_ENV"}))
    assert "account_ref" not in switched
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")

    # Reasserting the same pointer is a credential reassertion, so it also needs an explicit mapping.
    store.upsert_connection(connection_payload(account_ref="acct-b", api_key_env="FAKE_ACCOUNT_B_ENV"))
    reasserted = store.upsert_connection(connection_payload(**{env_alias: "FAKE_ACCOUNT_B_ENV"}))
    assert "account_ref" not in reasserted
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")


@pytest.mark.parametrize("clear_alias", ["clear_secret", "clearSecret"])
def test_clear_secret_unbinds_and_a_later_key_is_not_bound(tmp_path, clear_alias) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    cleared = store.upsert_connection(connection_payload(**{clear_alias: True}))
    assert "account_ref" not in cleared
    assert cleared["credential_configured"] is False
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")

    later = store.upsert_connection(connection_payload(api_key="fake-key-two"))
    assert "account_ref" not in later
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")


@pytest.mark.parametrize(
    "empty_input",
    [{"api_key": ""}, {"apiKey": None}, {"api_key_env": ""}, {"apiKeyEnv": None},
     {"clear_secret": False}, {"clearSecret": False}],
    ids=repr,
)
def test_empty_or_false_credential_inputs_keep_mapping_and_credential(tmp_path, empty_input) -> None:
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    updated = store.upsert_connection(connection_payload(name="Renamed", **empty_input))
    assert updated["name"] == "Renamed"
    assert updated["account_ref"] == "acct-a"
    assert updated["credential_configured"] is True
    assert store.resolve_connection_secret("sense-api") == "fake-key-one"


def test_name_only_edit_keeps_mapping_and_vault_credential_untouched(tmp_path) -> None:
    vault = FakeVault()
    store = ModelProfileStore(state_path=tmp_path / "state.json", vault=vault)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-vault-key"))
    vault.calls.clear()

    renamed = store.upsert_connection(connection_payload(name="Renamed"))

    assert renamed["account_ref"] == "acct-a"
    assert [call for call in vault.calls if call[0] != "probe"] == []
    assert store.resolve_connection_secret("sense-api") == "fake-vault-key"


@pytest.mark.parametrize("alias", ["account_ref", "accountRef"])
def test_credential_replacement_honors_explicit_mapping_and_null(tmp_path, alias) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))

    confirmed = store.upsert_connection(connection_payload(api_key="fake-key-two", **{alias: "acct-b"}))
    assert confirmed["account_ref"] == "acct-b"
    assert ModelProfileStore(state_path=path).get_connection_public("sense-api")["account_ref"] == "acct-b"

    cleared = store.upsert_connection(connection_payload(api_key="fake-key-three", **{alias: None}))
    assert "account_ref" not in cleared
    assert "account_ref" not in ModelProfileStore(state_path=path).get_connection_public("sense-api")


@pytest.mark.parametrize("vault_backed", [False, True], ids=["process-local", "fake-vault"])
def test_failed_credential_replacement_keeps_original_mapping_and_credential(
    tmp_path, monkeypatch, vault_backed,
) -> None:
    path = tmp_path / "state.json"
    vault = FakeVault() if vault_backed else None
    store = ModelProfileStore(state_path=path, vault=vault)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))
    before = store.get_connection_public("sense-api")
    monkeypatch.setattr(store_module, "_write_atomic", _fail_state_write)

    with pytest.raises(StoreError):
        store.upsert_connection(connection_payload(api_key="fake-key-two"))

    monkeypatch.undo()
    assert store.get_connection_public("sense-api") == before
    assert store.resolve_connection_secret("sense-api") == "fake-key-one"
    reopened = ModelProfileStore(state_path=path, vault=vault)
    assert reopened.get_connection_public("sense-api")["account_ref"] == "acct-a"
    if vault_backed:
        assert reopened.resolve_connection_secret("sense-api") == "fake-key-one"


def test_rotated_connection_no_longer_selects_previous_accounts_observation(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = ModelProfileStore(state_path=path)
    store.upsert_connection(connection_payload(account_ref="acct-a", api_key="fake-key-one"))
    observation = {"account_ref": "acct-a", "source": "magpie", "state": "OBSERVED",
                   "windows": [{"window": "weekly", "used_percent": 20}]}
    quotas = {"magpie-account:acct-a": observation}

    # Positive control: an ordinary rename keeps the confirmed account and selects its own evidence.
    renamed = store.upsert_connection(connection_payload(name="Renamed"))
    assert _selected_candidates(renamed, quotas) == [observation]

    rotated = store.upsert_connection(connection_payload(api_key="fake-key-two"))
    assert _selected_candidates(rotated, quotas) == []
    reopened = ModelProfileStore(state_path=path).get_connection_public("sense-api")
    assert _selected_candidates(reopened, quotas) == []
