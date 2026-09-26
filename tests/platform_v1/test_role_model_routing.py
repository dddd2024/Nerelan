"""Per-role model routing: multi-model collaboration inside one Task.

One Task's planner, coder and reviewer roles may be served by different
models of the same Connection, so the roles divide the labour instead of a
single model performing all three passes.  These tests pin the three
properties that make that safe:

1. the owner-declared role-model map is parsed fail-closed;
2. the executor selects a model per role and views the Binding resolution
   for that role without weakening any pre-lease drift check;
3. the credential relay still compares the requested model against the
   lease, so a role lease is widened to exactly one declared model id.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.credential_relay import (
    CredentialRelayError,
    CredentialRelayManager,
    _normalize_model_id,
)
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_executor import (
    ExecutionLeaseHandle,
    OpenCodeExecutor,
    ROLE_MODEL_ENV,
    build_binding_config_content,
    resolve_role_models,
)
from reverse_agent.platform_v1.trusted_host import _resolve_role_model_override


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_snapshot(**overrides: Any) -> ExecutionSnapshot:
    base = dict(
        binding_id="coding-glm",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="glm-5.2",
        connection_id="gateway",
        connection_enabled=True,
        provider="litellm-proxy",
        base_url="https://gateway.example.test/v1",
        auth_method="api_key",
        resolved_api_key="provider-master-key-xyz",
        external_session_status="not_applicable",
    )
    base.update(overrides)
    return ExecutionSnapshot(**base)


def _make_resolution(**overrides: Any) -> OpenCodeBindingResolution:
    base = dict(
        binding_ref="coding-glm",
        connection_id="gateway",
        executor_id="opencode",
        provider_id="litellm-proxy",
        model_id="litellm-proxy/glm-5.2",
        base_url="https://gateway.example.test/v1",
        auth_method="api_key",
        external_session_status="not_applicable",
        relay_required=True,
    )
    base.update(overrides)
    return OpenCodeBindingResolution(**base)


@pytest.fixture()
def manager() -> CredentialRelayManager:
    return CredentialRelayManager(default_expiry_seconds=2.0)


def _stub_lease_provider(*, cli_model: str = "reverse-agent-relay/glm-5.2"):
    """Lease provider that never leaves the process.

    Only the construction-time validation matters in these unit tests; the
    real provider is exercised end to end through the trusted host.
    """
    def _provider(resolution: Any) -> ExecutionLeaseHandle:
        return ExecutionLeaseHandle(
            lease_id="sk-unit-test",
            relay_url="http://127.0.0.1:9/relay",
            model_id=cli_model,
        )

    return _provider


# ---------------------------------------------------------------------------
# 1. Owner-declared role-model map is parsed fail-closed
# ---------------------------------------------------------------------------

def test_missing_or_blank_configuration_yields_single_model_behaviour() -> None:
    assert resolve_role_models("") == {}
    assert resolve_role_models("   ") == {}
    assert resolve_role_models(None) == {}


def test_malformed_configuration_is_ignored_rather_than_trusted() -> None:
    assert resolve_role_models("{not json") == {}
    assert resolve_role_models("[1, 2, 3]") == {}
    assert resolve_role_models("\"planner\"") == {}


def test_valid_configuration_is_parsed_verbatim() -> None:
    raw = json.dumps(
        {
            "planner": "glm-5.2",
            "coder": "sensenova-6.8-flash-lite",
            "reviewer": "kimi-k3",
        }
    )
    assert resolve_role_models(raw) == {
        "planner": "glm-5.2",
        "coder": "sensenova-6.8-flash-lite",
        "reviewer": "kimi-k3",
    }


def test_unknown_roles_and_invalid_models_are_dropped_entry_by_entry() -> None:
    raw = json.dumps(
        {
            "planner": "glm-5.2",
            "coder": "  padded-model  ",
            "reviewer": "bad model with spaces",
            "verifier": "kimi-k3",
            "": "kimi-k3",
            "arbiter": "kimi-k3",
        }
    )
    resolved = resolve_role_models(raw)
    # A whitespace-padded id is trimmed and kept; truly invalid entries and
    # roles outside the sequential team are dropped rather than trusted.
    assert resolved == {"planner": "glm-5.2", "coder": "padded-model"}


def test_environment_variable_is_the_default_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        ROLE_MODEL_ENV,
        json.dumps({"planner": "glm-5.2", "coder": "kimi-k3"}),
    )
    assert resolve_role_models() == {"planner": "glm-5.2", "coder": "kimi-k3"}


# ---------------------------------------------------------------------------
# 2. The executor selects a model per role
# ---------------------------------------------------------------------------

def test_each_role_resolves_to_its_own_declared_model() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
        role_models={
            "planner": "glm-5.2",
            "coder": "sensenova-6.8-flash-lite",
            "reviewer": "kimi-k3",
        },
    )
    # Bare declarations are qualified with the Binding's provider id so the
    # trusted host always sees one normalised provider/model value.
    assert executor._model_for_role("planner") == "litellm-proxy/glm-5.2"
    assert executor._model_for_role("coder") == "litellm-proxy/sensenova-6.8-flash-lite"
    assert executor._model_for_role("reviewer") == "litellm-proxy/kimi-k3"
    # An undeclared role keeps the Binding's own model.
    assert executor._model_for_role("executor") == "litellm-proxy/glm-5.2"


def test_already_qualified_role_models_are_kept_verbatim() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
        role_models={"reviewer": "litellm-proxy/meta-llama/llama-3.3"},
    )
    assert executor._model_for_role("reviewer") == "litellm-proxy/meta-llama/llama-3.3"


def test_without_role_models_every_role_uses_the_binding_model() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
    )
    for role in ("planner", "coder", "reviewer", "executor"):
        assert executor._model_for_role(role) == "litellm-proxy/glm-5.2"
    # Single-model behaviour must not rewrite the resolution at all.
    assert executor._role_binding_resolution("litellm-proxy/glm-5.2") is executor._binding_resolution


def test_role_resolution_pins_every_field_except_the_model() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
        role_models={"reviewer": "kimi-k3"},
    )
    role_model = executor._model_for_role("reviewer")
    viewed = executor._role_binding_resolution(role_model)
    assert viewed is not None
    assert viewed.model_id == "litellm-proxy/kimi-k3"
    assert viewed.binding_ref == "coding-glm"
    assert viewed.connection_id == "gateway"
    assert viewed.executor_id == "opencode"
    assert viewed.provider_id == "litellm-proxy"
    assert viewed.base_url == "https://gateway.example.test/v1"
    assert viewed.auth_method == "api_key"
    assert viewed.relay_required is True


def test_role_resolution_is_none_without_a_binding() -> None:
    executor = OpenCodeExecutor(model_id="glm-5.2")
    assert executor._role_binding_resolution("glm-5.2") is None


def test_role_model_configuration_is_validated_at_construction() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
        role_models={
            "planner": "bad model",
            "coder": "  ",
            "reviewer": 123,  # not a string
            "arbiter": "kimi-k3",  # not a sequential role
        },
    )
    # Every unusable entry is dropped; no role override survives.
    assert executor._model_for_role("planner") == "litellm-proxy/glm-5.2"
    assert executor._model_for_role("coder") == "litellm-proxy/glm-5.2"
    assert executor._model_for_role("reviewer") == "litellm-proxy/glm-5.2"


def test_role_model_equal_to_the_binding_model_declares_no_override() -> None:
    executor = OpenCodeExecutor(
        binding_resolution=_make_resolution(),
        lease_provider=_stub_lease_provider(),
        role_models={"planner": "glm-5.2"},
    )
    assert executor._role_binding_resolution(
        executor._model_for_role("planner")
    ) is executor._binding_resolution


# ---------------------------------------------------------------------------
# 3. The relay still compares the requested model against the lease
# ---------------------------------------------------------------------------

def test_lease_carries_the_role_model_override(manager: CredentialRelayManager) -> None:
    snapshot = _make_snapshot()
    lease = manager.create_lease(
        snapshot,
        relay_url="http://127.0.0.1:9/relay",
        model_override="kimi-k3",
    )
    assert lease.model_id == "kimi-k3"
    # The override must not widen anything else about the lease.
    assert lease.relay_url == "http://127.0.0.1:9/relay"


def test_lease_defaults_to_the_binding_model_without_an_override(
    manager: CredentialRelayManager,
) -> None:
    lease = manager.create_lease(_make_snapshot(), relay_url="http://127.0.0.1:9/relay")
    assert lease.model_id == "glm-5.2"


@pytest.mark.parametrize(
    "invalid",
    ["", " ", "kimi k3", "kimi\nk3", "k" * 300, "kimi\\k3", "kimi;rm -rf"],
)
def test_invalid_model_overrides_are_rejected(
    manager: CredentialRelayManager, invalid: str
) -> None:
    with pytest.raises(CredentialRelayError):
        manager.create_lease(
            _make_snapshot(),
            relay_url="http://127.0.0.1:9/relay",
            model_override=invalid,
        )


def test_role_lease_still_rejects_a_different_requested_model(
    manager: CredentialRelayManager,
) -> None:
    snapshot = _make_snapshot()
    manager.create_lease(
        snapshot,
        relay_url="http://127.0.0.1:9/relay",
        model_override="kimi-k3",
    )
    # The lease is widened to exactly one declared model; any third model in
    # the request body is still refused by the relay's own comparison.
    active = next(iter(manager._leases.values()))
    assert active.model_id == "kimi-k3"
    assert active.model_id != snapshot.raw_model_id


def test_config_content_declares_the_role_model(
    manager: CredentialRelayManager,
) -> None:
    lease = manager.create_lease(
        _make_snapshot(),
        relay_url="http://127.0.0.1:9/relay",
        model_override="kimi-k3",
    )
    content = build_binding_config_content(_make_resolution(), lease=lease)
    payload = json.loads(content)
    provider = payload["provider"]["reverse-agent-relay"]
    assert list(provider["models"].keys()) == ["kimi-k3"]
    assert provider["options"]["apiKey"] == lease.lease_id


# ---------------------------------------------------------------------------
# 4. Host-side decision: declared role models only, everything else fails closed
# ---------------------------------------------------------------------------

def test_binding_own_model_needs_no_override() -> None:
    provider = "litellm-proxy"
    expected = _normalize_model_id(provider, "glm-5.2")
    assert _resolve_role_model_override(
        expected_model=expected,
        requested_model=expected,
        declared_role_models={_normalize_model_id(provider, "kimi-k3")},
    ) is None


def test_declared_role_model_is_allowed_and_stripped_of_its_provider_prefix() -> None:
    provider = "litellm-proxy"
    expected = _normalize_model_id(provider, "glm-5.2")
    declared = {_normalize_model_id(provider, "kimi-k3")}
    assert _resolve_role_model_override(
        expected_model=expected,
        requested_model=_normalize_model_id(provider, "kimi-k3"),
        declared_role_models=declared,
    ) == "kimi-k3"


def test_bare_requested_model_is_refused_because_the_host_only_sees_normalised_ids() -> None:
    # Defence in depth: the executor always normalises before asking, so a
    # bare id reaching this decision means something bypassed the executor
    # and must not be authorised.
    with pytest.raises(RuntimeError):
        _resolve_role_model_override(
            expected_model="litellm-proxy/glm-5.2",
            requested_model="kimi-k3",
            declared_role_models={"litellm-proxy/kimi-k3"},
        )


def test_undeclared_model_fails_closed_before_any_credential_is_minted() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        _resolve_role_model_override(
            expected_model="litellm-proxy/glm-5.2",
            requested_model="litellm-proxy/gpt-5",
            declared_role_models={"litellm-proxy/kimi-k3"},
        )
    assert "role_model_not_declared_before_lease" in str(excinfo.value)


def test_provider_facing_model_keeps_its_own_slash_segments() -> None:
    assert _resolve_role_model_override(
        expected_model="litellm-proxy/glm-5.2",
        requested_model="litellm-proxy/meta-llama/llama-3.3",
        declared_role_models={"litellm-proxy/meta-llama/llama-3.3"},
    ) == "meta-llama/llama-3.3"


def test_role_timeout_env_rejects_non_finite_values_instead_of_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`inf` 在旧实现里会穿透 `int(float(raw))` 抛未捕获 OverflowError。

    配置解析器必须 fail-closed 回落，而不是让一个畸形环境变量在角色启动
    路径上炸掉执行器。
    """
    from reverse_agent.platform_v1.opencode_executor import (
        resolve_role_timeout_seconds,
    )

    for raw in ("1e999", "inf", "-inf", "nan", "0", "-1", "abc", ""):
        monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", raw)
        assert resolve_role_timeout_seconds(default=2700) == 2700, raw

    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", "2700")
    assert resolve_role_timeout_seconds() == 2700
    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", "2700.9")
    assert resolve_role_timeout_seconds() == 2700


def test_role_timeout_env_rejects_non_finite_values_instead_of_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`inf` 在旧实现里会穿透 `int(float(raw))` 抛未捕获 OverflowError。

    配置解析器必须 fail-closed 回落，而不是让一个畸形环境变量在角色启动
    路径上炸掉执行器。
    """
    from reverse_agent.platform_v1.opencode_executor import (
        resolve_role_timeout_seconds,
    )

    for raw in ("1e999", "inf", "-inf", "nan", "0", "-1", "abc", ""):
        monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", raw)
        assert resolve_role_timeout_seconds(default=2700) == 2700, raw

    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", "2700")
    assert resolve_role_timeout_seconds() == 2700
    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_TIMEOUT_SECONDS", "2700.9")
    assert resolve_role_timeout_seconds() == 2700
