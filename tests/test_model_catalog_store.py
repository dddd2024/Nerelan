"""Provider-free catalog generations, persistence and user binding protection."""

from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from reverse_agent.model_access.os_vault import FakeVault
from reverse_agent.model_access.service import discover_saved_connection_models
from reverse_agent.model_access.store import ModelProfileStore, StoreError


def connection(**overrides):
    return {
        "connection_id": "deepseek-local", "name": "My DeepSeek",
        "provider": "deepseek", "base_url": "https://catalog.example.test/v1",
        "auth_method": "none", "enabled": True, **overrides,
    }


def discover(store, *, model="deepseek-chat", transport=None):
    return discover_saved_connection_models(
        store=store, connection_id="deepseek-local", payload={}, live_enabled=True,
        transport=transport or (lambda *_: (200, json.dumps({"data": [{"id": model}]}).encode())),
    )


def selection(result, **overrides):
    return {"configuration_revision": result.configuration_revision,
            "catalog_revision": result.catalog_revision,
            "executor_id": "opencode", "model_id": "deepseek-chat", **overrides}


def manual(**overrides):
    return {"binding_id": "my-deepseek", "name": "User-selected DeepSeek",
            "connection_id": "deepseek-local", "executor_id": "opencode",
            "model_id": "deepseek/deepseek-chat", "enabled": True, **overrides}


def test_catalog_selection_is_atomic_idempotent_and_preserves_raw_upstream_id():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    result = discover(store, model="deepseek/deepseek-chat")
    payload = selection(result, model_id="deepseek/deepseek-chat")
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: store.select_catalog_binding("deepseek-local", payload), range(24)))
    assert sum(item["created"] for item in responses) == 1
    assert len({item["binding"]["binding_id"] for item in responses}) == 1
    assert len(store.list_bindings_public()) == 1
    assert responses[0]["binding"]["model_id"] == "deepseek/deepseek/deepseek-chat"
    assert responses[0]["advertised_model_id"] == "deepseek/deepseek-chat"
    snapshot = store.selection_public_snapshot()
    assert snapshot["bindings"][0]["source"] == "discovered"
    assert snapshot["bindings"][0]["availability"] == "advertised_unverified"
    assert "configuration_revision" not in store.list_connections_public()[0]
    assert "source" not in store.list_bindings_public()[0]


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("model_id", ["deepseek-chat", "deepseek/deepseek-chat"])
def test_manual_binding_and_disabled_tuple_are_preserved_exactly(enabled, model_id):
    store = ModelProfileStore()
    store.upsert_connection(connection())
    original = store.upsert_binding(manual(enabled=enabled, model_id=model_id))
    result = discover(store)
    response = store.select_catalog_binding("deepseek-local", selection(result))
    assert response["binding"] == original
    assert response["created"] is False
    assert response["reused_manual"] is True
    assert response["source"] == "manual"
    assert store.list_bindings_public() == [original]


def test_unrelated_user_agnes_and_deepseek_preferences_remain_unchanged():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    store.upsert_connection(connection(connection_id="agnes-local", name="My Agnes", provider="sensetime"))
    a = store.upsert_binding(manual())
    b = store.upsert_binding(manual(binding_id="my-agnes", name="User Agnes", connection_id="agnes-local", model_id="sensetime/agnes-coder", enabled=False))
    discover(store)
    before = store.list_bindings_public()
    catalog = discover(store, model="deepseek-reasoner")
    store.select_catalog_binding("deepseek-local", selection(catalog, model_id="deepseek-reasoner"))
    assert store.get_binding_public(a["binding_id"]) == a
    assert store.get_binding_public(b["binding_id"]) == b
    assert store.list_bindings_public()[:2] == before


def test_name_only_change_keeps_generation_and_catalog_but_authority_change_invalidates():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    first = discover(store)
    store.upsert_connection(connection(name="Renamed by user"))
    assert store.catalog_snapshot("deepseek-local").configuration_revision == first.configuration_revision
    assert store.selection_public_snapshot()["catalogs"]["deepseek-local"]["catalog_revision"] == first.catalog_revision
    store.upsert_connection(connection(name="Renamed by user", base_url="https://other.example.test/v1"))
    assert store.catalog_snapshot("deepseek-local").configuration_revision != first.configuration_revision
    assert store.selection_public_snapshot()["catalogs"] == {}
    with pytest.raises(ValueError, match="configuration_changed"):
        store.select_catalog_binding("deepseek-local", selection(first))


@pytest.mark.parametrize("update", [{"enabled": False}, {"provider": "sensetime"}, {"auth_method": "api_key", "api_key": "synthetic-only-key"}])
def test_config_and_identity_axes_change_invalidate_catalog(update):
    store = ModelProfileStore()
    store.upsert_connection(connection())
    first = discover(store)
    store.upsert_connection(connection(**update))
    assert store.catalog_snapshot("deepseek-local").configuration_revision != first.configuration_revision
    assert store.selection_public_snapshot()["catalogs"] == {}


def test_secret_replacement_and_clear_use_opaque_generations():
    store = ModelProfileStore()
    store.upsert_connection(connection(auth_method="api_key", api_key="synthetic-original"))
    first = discover(store)
    store.upsert_connection(connection(auth_method="api_key", api_key="synthetic-replacement"))
    second = discover(store)
    assert first.configuration_revision != second.configuration_revision
    assert first.catalog_revision != second.catalog_revision
    store.upsert_connection(connection(auth_method="api_key", clear_secret=True))
    assert store.catalog_snapshot("deepseek-local").configuration_revision != second.configuration_revision
    public = json.dumps(store.selection_public_snapshot())
    assert "synthetic-original" not in public and "synthetic-replacement" not in public


def test_delete_recreate_and_restart_invalidate_discovery_without_state_schema_change(tmp_path):
    state = tmp_path / "setup.json"
    store = ModelProfileStore(state)
    store.upsert_connection(connection())
    old = discover(store)
    store.delete_connection("deepseek-local")
    store.upsert_connection(connection())
    fresh = discover(store)
    assert fresh.configuration_revision != old.configuration_revision
    made = store.select_catalog_binding("deepseek-local", selection(fresh))
    raw = json.loads(state.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 2
    assert set(raw["bindings"][0]) == {"binding_id", "name", "executor_id", "connection_id", "model_id", "enabled"}
    assert "catalog_revision" not in json.dumps(raw)
    reloaded = ModelProfileStore(state)
    assert reloaded.list_connections_public() == store.list_connections_public()
    assert reloaded.list_bindings_public() == store.list_bindings_public()
    assert reloaded.selection_public_snapshot()["catalogs"] == {}
    assert reloaded.selection_public_snapshot()["bindings"][0]["source"] == "manual"
    assert reloaded.catalog_snapshot("deepseek-local").configuration_revision != fresh.configuration_revision
    new_catalog = discover(reloaded)
    kept = reloaded.select_catalog_binding("deepseek-local", selection(new_catalog))
    assert kept["binding"] == made["binding"] and kept["reused_manual"] is True


def test_user_edit_of_generated_binding_removes_generation_ownership():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    result = discover(store)
    made = store.select_catalog_binding("deepseek-local", selection(result))
    changed = {**made["binding"], "name": "Mine now", "enabled": False}
    store.upsert_binding(changed)
    assert store.selection_public_snapshot()["bindings"][0]["source"] == "manual"
    assert store.select_catalog_binding("deepseek-local", selection(result))["binding"] == changed


def test_safe_catalog_projection_has_stable_digest_but_metadata_change_invalidates_selection():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    first = discover(store)
    same = discover(store)
    assert same.catalog_revision == first.catalog_revision
    changed = discover(store, transport=lambda *_: (200, b'{"data":[{"id":"deepseek-chat","owned_by":"deepseek"}]}'))
    assert changed.catalog_revision != first.catalog_revision
    with pytest.raises(ValueError, match="catalog_changed"):
        store.select_catalog_binding("deepseek-local", selection(first))


@pytest.mark.parametrize("change", ["during", "after_cas", "after_snapshot"])
def test_external_environment_credential_change_invalidates_old_catalog(monkeypatch, change):
    env_name = "NERELAN_CATALOG_SYNTHETIC_KEY"
    monkeypatch.setenv(env_name, "synthetic-old-env")
    store = ModelProfileStore()
    store.upsert_connection(connection(auth_method="api_key", api_key_env=env_name))
    old_revision = store.catalog_snapshot("deepseek-local").configuration_revision

    def transport(_url, headers, _timeout):
        assert headers["Authorization"] == "Bearer synthetic-old-env"
        if change == "during":
            monkeypatch.setenv(env_name, "synthetic-new-env")
        return 200, b'{"data":[{"id":"deepseek-chat"}]}'

    result = discover(store, transport=transport)
    if change == "during":
        assert result.status == "configuration_changed" and not result.ok
    else:
        assert result.ok
        monkeypatch.setenv(env_name, "synthetic-new-env")
        if change == "after_cas":
            with pytest.raises(ValueError, match="configuration_changed"):
                store.select_catalog_binding("deepseek-local", selection(result))
        else:
            assert store.selection_public_snapshot()["catalogs"] == {}
    assert store.catalog_snapshot("deepseek-local").configuration_revision != old_revision
    assert store.selection_public_snapshot()["catalogs"] == {}
    assert "synthetic-" not in json.dumps(store.selection_public_snapshot())


@pytest.mark.parametrize("change", ["during", "after_cas", "after_snapshot", "locked", "missing"])
def test_external_mock_vault_change_invalidates_old_catalog(change):
    vault = FakeVault()
    store = ModelProfileStore(vault=vault)
    store.upsert_connection(connection(auth_method="api_key", api_key="synthetic-old-vault"))
    ref = vault.item_refs()[0]
    old_revision = store.catalog_snapshot("deepseek-local").configuration_revision

    def transport(_url, headers, _timeout):
        assert headers["Authorization"] == "Bearer synthetic-old-vault"
        if change == "during":
            vault.store(ref, "synthetic-new-vault")
        return 200, b'{"data":[{"id":"deepseek-chat"}]}'

    result = discover(store, transport=transport)
    if change == "during":
        assert result.status == "configuration_changed" and not result.ok
    else:
        assert result.ok
        if change == "locked":
            vault.locked = True
        elif change == "missing":
            vault.delete(ref)
        else:
            vault.store(ref, "synthetic-new-vault")
        if change == "after_cas":
            with pytest.raises(ValueError, match="configuration_changed"):
                store.select_catalog_binding("deepseek-local", selection(result))
        else:
            assert store.selection_public_snapshot()["catalogs"] == {}
    assert store.catalog_snapshot("deepseek-local").configuration_revision != old_revision
    assert "synthetic-" not in json.dumps(store.selection_public_snapshot())


def test_failed_configuration_persistence_keeps_old_catalog_and_generation(tmp_path, monkeypatch):
    store = ModelProfileStore(tmp_path / "setup.json")
    store.upsert_connection(connection())
    result = discover(store)

    def fail_write(*_):
        raise OSError("synthetic persistence failure")

    monkeypatch.setattr("reverse_agent.model_access.store._write_atomic", fail_write)
    with pytest.raises(StoreError):
        store.upsert_connection(connection(enabled=False))
    assert store.get_connection_public("deepseek-local")["enabled"] is True
    assert store.catalog_snapshot("deepseek-local").configuration_revision == result.configuration_revision
    assert store.selection_public_snapshot()["catalogs"]["deepseek-local"]["catalog_revision"] == result.catalog_revision


def test_failed_binding_persistence_does_not_leave_binding_or_provenance(tmp_path, monkeypatch):
    store = ModelProfileStore(tmp_path / "setup.json")
    store.upsert_connection(connection())
    result = discover(store)

    def fail_write(*_):
        raise OSError("synthetic persistence failure")

    with monkeypatch.context() as context:
        context.setattr("reverse_agent.model_access.store._write_atomic", fail_write)
        with pytest.raises(StoreError):
            store.select_catalog_binding("deepseek-local", selection(result))
    assert store.list_bindings_public() == []
    assert store.selection_public_snapshot()["bindings"] == []
    assert store.select_catalog_binding("deepseek-local", selection(result))["created"] is True


@pytest.mark.parametrize("override", [{"executor_id": "codex"}, {"executor_id": "unknown"}, {"model_id": "not-advertised"}, {"allow_gpt": True}, {"configuration_revision": []}])
def test_catalog_selection_rejects_unsupported_pairing_and_browser_authority(override):
    store = ModelProfileStore()
    store.upsert_connection(connection())
    result = discover(store)
    with pytest.raises(ValueError):
        store.select_catalog_binding("deepseek-local", selection(result, **override))
    assert store.list_bindings_public() == []


def test_snapshot_is_detached_and_retains_unknown_executor_readiness():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    result = discover(store)
    store.select_catalog_binding("deepseek-local", selection(result))
    first = store.selection_public_snapshot()
    opencode = next(item for item in first["executors"] if item["executor_id"] == "opencode")
    assert "readiness_status" not in opencode
    first["catalogs"]["deepseek-local"]["models"].clear()
    first["catalogs"]["deepseek-local"]["model_records"][0]["model_id"] = "forged"
    first["connections"][0]["provider"] = "forged"
    second = store.selection_public_snapshot()
    assert second["catalogs"]["deepseek-local"]["models"] == ["deepseek-chat"]
    assert second["connections"][0]["provider"] == "deepseek"


def test_slash_advertisement_does_not_reuse_legacy_binding_for_different_upstream_model():
    store = ModelProfileStore()
    store.upsert_connection(connection(provider="openrouter"))
    old = store.upsert_binding(manual(model_id="openrouter/claude-x"))
    result = discover(store, model="openrouter/claude-x")
    selected = store.select_catalog_binding("deepseek-local", selection(result, model_id="openrouter/claude-x"))
    assert selected["created"] and not selected["reused_manual"]
    assert selected["binding"]["model_id"] == "openrouter/openrouter/claude-x"
    assert store.get_binding_public(old["binding_id"]) == old


def test_slash_advertisement_exact_canonical_manual_binding_is_reused():
    store = ModelProfileStore()
    store.upsert_connection(connection(provider="openrouter"))
    old = store.upsert_binding(manual(model_id="openrouter/openrouter/claude-x", enabled=False))
    result = discover(store, model="openrouter/claude-x")
    selected = store.select_catalog_binding("deepseek-local", selection(result, model_id="openrouter/claude-x"))
    assert selected["binding"] == old and selected["reused_manual"]
    assert len(store.list_bindings_public()) == 1


@pytest.mark.parametrize("old_result", ["success", "failure"])
def test_latest_started_refresh_wins_and_older_failure_cannot_delete_new_catalog(old_result):
    store = ModelProfileStore()
    store.upsert_connection(connection())

    def old_transport(*_):
        assert discover(store, model="deepseek-new").ok
        if old_result == "failure":
            from reverse_agent.model_access.catalog_transport import CatalogTransportError
            raise CatalogTransportError("timeout")
        return 200, b'{"data":[{"id":"deepseek-old"}]}'

    old = discover(store, transport=old_transport)
    assert not old.ok and old.status == "catalog_changed"
    assert store.selection_public_snapshot()["catalogs"]["deepseek-local"]["models"] == ["deepseek-new"]


def test_new_refresh_clears_old_catalog_before_io_and_blocks_old_selection():
    store = ModelProfileStore()
    store.upsert_connection(connection())
    old = discover(store)

    def transport(*_):
        with pytest.raises(ValueError, match="catalog_changed"):
            store.select_catalog_binding("deepseek-local", selection(old))
        return 200, b'{"data":[{"id":"deepseek-chat"}]}'

    assert discover(store, transport=transport).ok


def test_reconciliation_clears_process_discovery_and_generated_ownership(tmp_path, monkeypatch):
    from reverse_agent.model_access import store as store_module
    store = ModelProfileStore(tmp_path / "setup.json")
    store.upsert_connection(connection())
    old = discover(store)
    made = store.select_catalog_binding("deepseek-local", selection(old))
    original_write = store_module._write_atomic

    def uncertain_write(data, target):
        original_write(data, target)
        raise store_module._PostReplaceDurabilityUncertainError("synthetic post-replace uncertainty")

    monkeypatch.setattr(store_module, "_write_atomic", uncertain_write)
    with pytest.raises(StoreError):
        store.upsert_connection(connection(base_url="https://other.example.test/v1"))
    snapshot = store.selection_public_snapshot()
    assert snapshot["catalogs"] == {}
    assert snapshot["connections"][0]["configuration_revision"] != old.configuration_revision
    assert snapshot["bindings"][0]["binding_id"] == made["binding"]["binding_id"]
    assert snapshot["bindings"][0]["source"] == "manual"


def test_external_key_replacement_before_refresh_changes_generation_before_network(monkeypatch):
    monkeypatch.setenv("NERELAN_CATALOG_REFRESH_SYNTHETIC", "synthetic-old")
    store = ModelProfileStore()
    store.upsert_connection(connection(auth_method="api_key", api_key_env="NERELAN_CATALOG_REFRESH_SYNTHETIC"))
    old = discover(store)
    monkeypatch.setenv("NERELAN_CATALOG_REFRESH_SYNTHETIC", "synthetic-new")
    stale = discover(store, transport=lambda *_: pytest.fail("stale refresh must not make request"))
    assert stale.status == "configuration_changed"
    assert store.catalog_snapshot("deepseek-local").configuration_revision != old.configuration_revision
    assert discover(store).ok


@pytest.mark.parametrize("secret_source", ["environment", "mock_vault"])
def test_failed_refresh_with_credential_replacement_changes_third_catalog_generation(monkeypatch, secret_source):
    from reverse_agent.model_access.catalog_transport import CatalogTransportError
    from reverse_agent.model_access.selection import recommend_model_selection
    if secret_source == "environment":
        monkeypatch.setenv("NERELAN_CATALOG_FAILED_SYNTHETIC", "synthetic-first-key")
        store = ModelProfileStore()
        store.upsert_connection(connection(auth_method="api_key", api_key_env="NERELAN_CATALOG_FAILED_SYNTHETIC"))
        replace = lambda: monkeypatch.setenv("NERELAN_CATALOG_FAILED_SYNTHETIC", "synthetic-next-key")
    else:
        vault = FakeVault()
        store = ModelProfileStore(vault=vault)
        store.upsert_connection(connection(auth_method="api_key", api_key="synthetic-first-key"))
        ref = vault.item_refs()[0]
        replace = lambda: vault.store(ref, "synthetic-next-key")
    first = discover(store)
    old_binding = store.select_catalog_binding("deepseek-local", selection(first))["binding"]

    def failed_refresh(_url, headers, _timeout):
        assert headers["Authorization"] == "Bearer synthetic-first-key"
        replace()
        raise CatalogTransportError("timeout")

    failed = discover(store, transport=failed_refresh)
    assert not failed.ok and failed.status == "configuration_changed"
    third = discover(store)
    assert third.ok
    assert third.configuration_revision != first.configuration_revision
    assert third.catalog_revision != first.catalog_revision
    snapshot = store.selection_public_snapshot()
    old = next(binding for binding in snapshot["bindings"] if binding["binding_id"] == old_binding["binding_id"])
    assert old["configuration_revision"] == first.configuration_revision
    assert old["availability"] is None
    preview = recommend_model_selection(snapshot, {})
    candidate = next(candidate for candidate in preview["candidates"] if candidate["binding_ref"] == old_binding["binding_id"])
    assert not candidate["eligible"]
    assert "configuration_stale" in candidate["reason_codes"]
    assert "catalog_stale" in candidate["reason_codes"]
    assert store.get_binding_public(old_binding["binding_id"]) == old_binding
    assert store.select_catalog_binding("deepseek-local", selection(third))["binding"]["binding_id"] != old_binding["binding_id"]
    assert "synthetic-first-key" not in json.dumps(snapshot)
    assert "synthetic-next-key" not in json.dumps(snapshot)


def test_credential_replacement_after_failed_refresh_remains_observed(monkeypatch):
    from reverse_agent.model_access.catalog_transport import CatalogTransportError
    monkeypatch.setenv("NERELAN_CATALOG_BETWEEN_SYNTHETIC", "synthetic-first-key")
    store = ModelProfileStore()
    store.upsert_connection(connection(auth_method="api_key", api_key_env="NERELAN_CATALOG_BETWEEN_SYNTHETIC"))
    first = discover(store)

    def failed(*_):
        raise CatalogTransportError("timeout")

    assert discover(store, transport=failed).status == "timeout"
    monkeypatch.setenv("NERELAN_CATALOG_BETWEEN_SYNTHETIC", "synthetic-next-key")
    snapshot = store.selection_public_snapshot()
    assert snapshot["catalogs"] == {}
    assert snapshot["connections"][0]["configuration_revision"] != first.configuration_revision
    third = discover(store)
    assert third.ok and third.catalog_revision != first.catalog_revision


def test_initial_failed_observation_retains_comparison_without_prior_success(monkeypatch):
    from reverse_agent.model_access.catalog_transport import CatalogTransportError
    monkeypatch.setenv("NERELAN_CATALOG_INITIAL_SYNTHETIC", "synthetic-first-key")
    store = ModelProfileStore()
    store.upsert_connection(connection(auth_method="api_key", api_key_env="NERELAN_CATALOG_INITIAL_SYNTHETIC"))
    first_revision = store.catalog_snapshot("deepseek-local").configuration_revision

    def failed(*_):
        raise CatalogTransportError("timeout")

    assert discover(store, transport=failed).status == "timeout"
    monkeypatch.setenv("NERELAN_CATALOG_INITIAL_SYNTHETIC", "synthetic-next-key")
    snapshot = store.selection_public_snapshot()
    assert snapshot["connections"][0]["configuration_revision"] != first_revision
    assert discover(store).ok
