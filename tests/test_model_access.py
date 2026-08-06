from __future__ import annotations

import json
from typing import Any

import pytest

from reverse_agent.model_access.contracts import ModelProfile, ProbeResult
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.model_access.service import (
    probe_openai_compatible,
    validate_bind_host,
)


def profile_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": "coding-default",
        "name": "Default coding model",
        "provider": "litellm-proxy",
        "base_url": "http://localhost:4000/v1",
        "model_id": "coding-default",
        "executor": "openhands",
        "enabled": True,
        "is_default": True,
    }
    payload.update(overrides)
    return payload


def test_profile_validation_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        ModelProfile.from_mapping(
            profile_payload(base_url="https://user:pass@example.com/v1")
        )


def test_store_masks_api_keys_and_keeps_one_default() -> None:
    store = ModelProfileStore()
    first = store.upsert(profile_payload(api_key="secret-alpha"))
    second = store.upsert(
        profile_payload(
            id="review",
            name="Review model",
            model_id="review-strong",
            api_key="secret-beta",
            is_default=True,
        )
    )

    public = store.list_public()
    serialized = json.dumps(public)
    assert "secret-alpha" not in serialized
    assert "secret-beta" not in serialized
    assert first["secret_status"] == "session"
    assert second["secret_status"] == "session"
    assert [item["id"] for item in public if item["is_default"]] == ["review"]


def test_deleting_default_promotes_an_enabled_profile() -> None:
    store = ModelProfileStore()
    store.upsert(profile_payload())
    store.upsert(
        profile_payload(
            id="review",
            name="Review model",
            model_id="review-strong",
            is_default=False,
        )
    )

    store.delete("coding-default")

    assert store.list_public() == [
        {
            "id": "review",
            "name": "Review model",
            "provider": "litellm-proxy",
            "base_url": "http://localhost:4000/v1",
            "model_id": "review-strong",
            "executor": "openhands",
            "enabled": True,
            "is_default": True,
            "secret_status": "missing",
        }
    ]


def test_environment_secret_is_resolved_without_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_ACCESS_TEST_KEY", "environment-secret")
    store = ModelProfileStore()
    profile = store.upsert(
        profile_payload(api_key_env="MODEL_ACCESS_TEST_KEY", api_key=None)
    )

    assert profile["secret_status"] == "environment"
    assert store.resolve_secret("coding-default") == "environment-secret"
    assert "environment-secret" not in json.dumps(store.list_public())


def test_probe_is_blocked_without_explicit_live_opt_in() -> None:
    profile = ModelProfile.from_mapping(profile_payload())

    result = probe_openai_compatible(
        profile=profile,
        api_key="secret",
        live_enabled=False,
    )

    assert result == ProbeResult(
        ok=False,
        status="live_probe_disabled",
        message="Live model probes require REVERSE_AGENT_MODEL_CONTROL_LIVE=1",
        latency_ms=None,
    )


def test_probe_uses_injected_transport_and_never_returns_secret() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    def transport(
        url: str, headers: dict[str, str], timeout: float
    ) -> tuple[int, bytes]:
        calls.append((url, headers, timeout))
        return 200, b'{"data":[{"id":"coding-default"}]}'

    result = probe_openai_compatible(
        profile=ModelProfile.from_mapping(profile_payload()),
        api_key="probe-secret",
        live_enabled=True,
        transport=transport,
    )

    assert result.ok is True
    assert result.status == "connected"
    assert "probe-secret" not in result.message
    assert calls == [
        (
            "http://localhost:4000/v1/models",
            {
                "Accept": "application/json",
                "Authorization": "Bearer probe-secret",
            },
            10.0,
        )
    ]


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_control_service_accepts_only_loopback_hosts(host: str) -> None:
    assert validate_bind_host(host) == host


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.20", "model-host.local"])
def test_control_service_rejects_non_loopback_hosts(host: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        validate_bind_host(host)
