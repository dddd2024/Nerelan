from dataclasses import FrozenInstanceError

import pytest

from reverse_agent.model_access.provider_identity import (
    ProviderIdentity,
    identity_authority_changed,
    identity_authority_equivalent,
    resolve_provider_usage_dispatch,
)


@pytest.mark.parametrize(
    ("legacy", "upstream", "protocol", "executor"),
    [
        ("openai", "openai", "openai", "openai"),
        ("sensetime", "sensetime", "openai", "sensetime"),
        ("deepseek", "deepseek", "openai", "deepseek"),
        ("openrouter", "openrouter", "openai", "openrouter"),
        ("openai-compatible", None, "openai", "openai-compatible"),
        ("litellm-proxy", None, "openai", "litellm-proxy"),
        ("custom-gateway", None, None, "custom-gateway"),
    ],
)
def test_legacy_provider_mapping(legacy, upstream, protocol, executor):
    identity = ProviderIdentity.from_legacy_provider(legacy)
    assert identity == ProviderIdentity(upstream, protocol, executor)


def test_legacy_normalization_is_syntax_only():
    identity = ProviderIdentity.from_legacy_provider("  SenseTime  ")
    assert identity == ProviderIdentity("sensetime", "openai", "sensetime")


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "bad value", "/provider", "provider/", "a" * 81, 7],
)
def test_legacy_provider_rejects_invalid_identifier(value):
    with pytest.raises(ValueError):
        ProviderIdentity.from_legacy_provider(value)


@pytest.mark.parametrize("field", ["upstream", "protocol", "executor"])
def test_explicit_identity_rejects_invalid_supplied_axis(field):
    kwargs = {
        "upstream_provider_id": "sensetime",
        "protocol_family": "openai",
        "executor_provider_id": "sensetime",
    }
    key = {
        "upstream": "upstream_provider_id",
        "protocol": "protocol_family",
        "executor": "executor_provider_id",
    }[field]
    kwargs[key] = "bad value"
    with pytest.raises(ValueError):
        ProviderIdentity(**kwargs)


def test_explicit_identity_keeps_axes_independent():
    identity = ProviderIdentity(
        upstream_provider_id=None,
        protocol_family=" OpenAI ",
        executor_provider_id=" Gateway ",
    )
    assert identity.upstream_provider_id is None
    assert identity.protocol_family == "openai"
    assert identity.executor_provider_id == "gateway"


def test_explicit_executor_does_not_infer_upstream():
    identity = ProviderIdentity(None, "openai", "openai")
    assert identity.upstream_provider_id is None
    assert resolve_provider_usage_dispatch(identity) is None


@pytest.mark.parametrize(
    ("provider", "expected_parser"),
    [
        ("sensetime", "sensenova_usage"),
        ("deepseek", "deepseek_balance"),
    ],
)
def test_concrete_identity_composes_with_existing_provider_usage_registry(
    provider, expected_parser
):
    identity = ProviderIdentity(provider, "openai", provider)
    dispatch = resolve_provider_usage_dispatch(identity)
    assert dispatch is not None
    assert dispatch.supported is True
    assert dispatch.provider_id == provider
    assert expected_parser in dispatch.parser_ids


@pytest.mark.parametrize("legacy", ["openai-compatible", "litellm-proxy"])
def test_protocol_compatibility_never_unlocks_openai_account_dispatch(legacy):
    identity = ProviderIdentity.from_legacy_provider(legacy)
    assert identity.upstream_provider_id is None
    assert identity.protocol_family == "openai"
    assert resolve_provider_usage_dispatch(identity) is None


def test_missing_protocol_blocks_provider_specific_dispatch():
    identity = ProviderIdentity("openai", None, "custom-executor")
    assert resolve_provider_usage_dispatch(identity) is None


def test_explicit_unknown_registry_entry_stays_unsupported():
    identity = ProviderIdentity("custom", "openai", "custom")
    dispatch = resolve_provider_usage_dispatch(identity)
    assert dispatch is not None
    assert dispatch.supported is False
    assert dispatch.provider_id == "custom"


def test_authority_equivalence_requires_all_axes_to_match():
    baseline = ProviderIdentity("sensetime", "openai", "sensetime")
    assert identity_authority_equivalent(baseline, baseline)
    assert not identity_authority_changed(baseline, baseline)

    variants = [
        ProviderIdentity("deepseek", "openai", "sensetime"),
        ProviderIdentity("sensetime", "anthropic", "sensetime"),
        ProviderIdentity("sensetime", "openai", "other-executor"),
    ]
    for variant in variants:
        assert not identity_authority_equivalent(baseline, variant)
        assert identity_authority_changed(baseline, variant)


def test_identity_is_immutable():
    identity = ProviderIdentity("sensetime", "openai", "sensetime")
    with pytest.raises(FrozenInstanceError):
        identity.executor_provider_id = "deepseek"


def test_authority_helpers_require_identity_objects():
    identity = ProviderIdentity("sensetime", "openai", "sensetime")
    with pytest.raises(TypeError):
        identity_authority_equivalent(identity, object())
    with pytest.raises(TypeError):
        identity_authority_changed(object(), identity)
