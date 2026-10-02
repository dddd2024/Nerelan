"""Synthetic public snapshots; no provider, credential or execution probes."""

from copy import deepcopy

import pytest

from reverse_agent.model_access.selection import recommend_model_selection


@pytest.fixture
def snapshot():
    return {
        "connections": [
            {"connection_id": "deepseek", "enabled": True, "provider": "deepseek",
             "upstream_provider_id": "deepseek", "protocol_family": "openai",
             "executor_provider_id": "deepseek", "auth_method": "api_key",
             "secret_status": "stored", "configuration_revision": "test-generation-d"},
            {"connection_id": "agnes", "enabled": True, "provider": "sensetime",
             "upstream_provider_id": "sensetime", "protocol_family": "openai",
             "executor_provider_id": "sensetime", "auth_method": "none",
             "configuration_revision": "test-generation-a"},
        ],
        "executors": [{"executor_id": "opencode", "operational": True,
                       "capabilities": ["workspace_execution", "model_selection"],
                       "readiness_status": "ready"}],
        "bindings": [
            {"binding_id": "deepseek-user", "connection_id": "deepseek",
             "executor_id": "opencode", "model_id": "deepseek/deepseek-chat", "enabled": True},
            {"binding_id": "agnes-user", "connection_id": "agnes",
             "executor_id": "opencode", "model_id": "sensetime/agnes-code", "enabled": True},
        ],
        "catalogs": {},
    }


def test_preference_is_deterministic_without_fabricated_history(snapshot):
    original = deepcopy(snapshot)
    result = recommend_model_selection(snapshot, {"preferred_binding_refs": ["agnes-user"]})
    assert result["recommended"]["binding_ref"] == "agnes-user"
    assert result["preview_only"] is True
    assert result["recommended"]["cost"] is None
    assert result["recommended"]["quality"] is None
    assert result["recommended"]["availability"] == "not_observed"
    assert result["recommended"]["underlying_identity"] is None
    assert result["recommended"]["underlying_identity_status"] == "not_observed"
    assert "证据不足" in result["recommended"]["explanation"]
    assert snapshot == original


def test_static_operational_is_not_observed_readiness(snapshot):
    snapshot["executors"][0].pop("readiness_status")
    result = recommend_model_selection(snapshot, {})
    assert result["recommended"] is None
    assert all("readiness_not_observed" in c["reason_codes"] for c in result["candidates"])


@pytest.mark.parametrize("patch,reason", [
    ({"enabled": False}, "connection_disabled"),
    ({"secret_status": "store_locked"}, "credential_missing"),
    ({"secret_status": "replacement_required"}, "credential_missing"),
    ({"protocol_family": "custom"}, "protocol_unsupported"),
    ({"auth_method": "external_cli_session", "external_session_status": "missing"}, "session_not_observed"),
])
def test_manual_override_preserved_but_cannot_hide_ineligibility(snapshot, patch, reason):
    snapshot["connections"][0].update(patch)
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["status"] == "manual_blocked"
    assert result["recommended"] is None
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["binding_ref"] == "deepseek-user"
    assert reason in result["candidates"][0]["reason_codes"]


def test_disabled_manual_tuple_is_not_substituted(snapshot):
    snapshot["bindings"][0]["enabled"] = False
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"] is None
    assert "binding_disabled" in result["candidates"][0]["reason_codes"]
    assert snapshot["bindings"][0]["enabled"] is False


@pytest.mark.parametrize("requested_model", ["gpt-6.1-sol", "deepseek-gpt4", "deepseek-v3gpt6.1", "o3", "codex-mini"])
def test_gpt_cannot_get_approval_from_explicit_ui_choice(snapshot, requested_model):
    snapshot["bindings"][0]["model_id"] = "deepseek/" + requested_model
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"] is None
    assert "requires_bounded_gpt_approval" in result["candidates"][0]["reason_codes"]


def test_relabeling_gpt_or_unknown_does_not_make_routine_candidate(snapshot):
    snapshot["bindings"][0]["model_id"] = "deepseek/private-alias"
    snapshot["bindings"][1]["model_id"] = "sensetime/hidden-gpt-6"
    result = recommend_model_selection(snapshot, {})
    assert result["recommended"] is None
    unknown = next(c for c in result["candidates"] if c["binding_ref"] == "deepseek-user")
    assert "model_family_unknown" in unknown["reason_codes"]
    assert any("requires_bounded_gpt_approval" in c["reason_codes"] for c in result["candidates"])


def test_catalog_success_only_advertised_unverified(snapshot):
    snapshot["catalogs"]["deepseek"] = {
        "ok": True, "configuration_revision": "test-generation-d",
        "catalog_revision": "safe-projection-1", "models": ["deepseek-chat"],
        "latency_ms": 0, "entitlement": "not_observed",
    }
    result = recommend_model_selection(snapshot, {})
    candidate = next(c for c in result["candidates"] if c["binding_ref"] == "deepseek-user")
    assert candidate["availability"] == "advertised_unverified"
    assert candidate["cost"] is None
    assert "task_success" in result["evidence_unknowns"]
    assert candidate["underlying_identity"] is None


@pytest.mark.parametrize("mutation,reason", [
    ({"configuration_revision": "obsolete-generation"}, "configuration_stale"),
    ({"catalog_revision": "obsolete-catalog"}, "catalog_stale"),
])
def test_generated_binding_requires_exact_catalog_generation(snapshot, mutation, reason):
    binding = snapshot["bindings"][0]
    binding.update(source="discovered", configuration_revision="test-generation-d", catalog_revision="catalog-1")
    snapshot["catalogs"]["deepseek"] = {"ok": True, "configuration_revision": "test-generation-d", "catalog_revision": "catalog-1", "models": ["deepseek-chat"]}
    binding.update(mutation)
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"] is None
    assert reason in result["candidates"][0]["reason_codes"]


def test_catalog_response_from_prior_configuration_cannot_prove_current_availability(snapshot):
    snapshot["catalogs"]["deepseek"] = {"ok": True, "configuration_revision": "old", "catalog_revision": "old", "models": ["deepseek-chat"]}
    result = recommend_model_selection(snapshot, {})
    candidate = next(c for c in result["candidates"] if c["binding_ref"] == "deepseek-user")
    assert candidate["availability"] == "not_observed"
    assert candidate["catalog_revision"] is None


def test_openrouter_hierarchical_id_is_not_reinterpreted_as_wrong_provider(snapshot):
    connection = snapshot["connections"][0]
    connection.update(provider="openrouter", upstream_provider_id="openrouter", executor_provider_id="openrouter")
    snapshot["bindings"][0]["model_id"] = "openrouter/deepseek/deepseek-chat"
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"]["binding_ref"] == "deepseek-user"
    assert result["recommended"]["model_id"] == "openrouter/deepseek/deepseek-chat"
    snapshot["bindings"][0]["model_id"] = "deepseek/deepseek-chat"
    blocked = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert "model_namespace_mismatch" in blocked["candidates"][0]["reason_codes"]


def test_native_login_is_not_catalog_entitlement_or_team_capability(snapshot):
    snapshot["connections"][0].update(provider="codex", upstream_provider_id="openai", protocol_family="codex-cli", executor_provider_id="codex", auth_method="external_cli_session", external_session_status="available")
    snapshot["bindings"][0].update(executor_id="codex", model_id="gpt-6.1-sol")
    snapshot["executors"].append({"executor_id": "codex", "operational": True, "readiness_status": "managed_login_ready", "capabilities": ["workspace_execution", "single_mode"]})
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user", "orchestration_mode": "sequential_team"})
    reasons = result["candidates"][0]["reason_codes"]
    assert "native_single_only" in reasons
    assert "requires_bounded_gpt_approval" in reasons
    assert result["recommended"] is None


def test_preferences_cannot_hide_capability_and_executor_mismatch(snapshot):
    result = recommend_model_selection(snapshot, {"required_capabilities": ["firmware_patch"], "executor_preference": "codex", "preferred_binding_refs": ["deepseek-user"]})
    assert result["recommended"] is None
    assert all("capability_missing" in c["reason_codes"] and "executor_preference_mismatch" in c["reason_codes"] for c in result["candidates"])


@pytest.mark.parametrize("payload", [
    {"allow_gpt": True}, {"approved_by": "browser"},
    {"selection_mode": "manual"}, {"selection_mode": "automatic", "manual_binding_ref": "deepseek-user"},
    {"selection_mode": "oops"}, {"purpose": "x" * 81},
    {"required_capabilities": ["x"] * 17}, {"preferred_binding_refs": ["x"] * 33},
    {"manual_binding_ref": "../outside", "selection_mode": "manual"},
])
def test_request_cannot_supply_authority_or_unbounded_preferences(snapshot, payload):
    with pytest.raises(ValueError):
        recommend_model_selection(snapshot, payload)


def test_secret_bearing_extra_snapshot_fields_never_enter_projection(snapshot):
    snapshot["connections"][0]["api_key"] = "synthetic-do-not-copy"
    snapshot["bindings"][0]["authorization"] = "synthetic-do-not-copy"
    result = recommend_model_selection(snapshot, {})
    assert "synthetic-do-not-copy" not in repr(result)


def test_duplicate_snapshot_identity_fails_closed(snapshot):
    snapshot["bindings"].append(deepcopy(snapshot["bindings"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        recommend_model_selection(snapshot, {})


@pytest.mark.parametrize("model_id", ["sk-synthetic-credential", "BearerSynthetic", 'token="synthetic"', "deepseek-chat?key=synthetic", "deepseek-chat\nsecret"])
def test_invalid_or_credential_shaped_ids_are_not_reflected(snapshot, model_id):
    snapshot["bindings"][0]["model_id"] = model_id
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"] is None
    assert result["candidates"][0]["model_id"] == ""
    assert model_id not in repr(result)


def test_catalog_safe_version_id_keeps_upstream_characters(snapshot):
    snapshot["bindings"][0]["model_id"] = "deepseek/deepseek-v3@2026+revision"
    result = recommend_model_selection(snapshot, {"selection_mode": "manual", "manual_binding_ref": "deepseek-user"})
    assert result["recommended"]["model_id"] == "deepseek/deepseek-v3@2026+revision"


def test_no_explicit_preference_does_not_invent_family_quality_order(snapshot):
    snapshot["bindings"][0]["binding_id"] = "a-configured-deepseek"
    snapshot["bindings"][1]["binding_id"] = "b-configured-agnes"
    first = recommend_model_selection(snapshot, {})
    assert first["recommended"]["binding_ref"] == "a-configured-deepseek"
    snapshot["bindings"][0]["binding_id"] = "z-configured-deepseek"
    second = recommend_model_selection(snapshot, {})
    assert second["recommended"]["binding_ref"] == "b-configured-agnes"
    assert "尚未指定绑定偏好" in second["message"]
