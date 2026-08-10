from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import urlsplit

import pytest

from reverse_agent.platform_v1.binding_resolver import (
    BindingResolutionError,
    BindingResolver,
    OpenCodeBindingResolution,
)


def _binding(**overrides: Any) -> dict[str, Any]:
    value = {
        "binding_id": "coding-fast",
        "name": "Fast coding",
        "executor_id": "opencode",
        "connection_id": "sense-api",
        "model_id": "sense-coding-fast",
        "enabled": True,
    }
    value.update(overrides)
    return value


def _connection(**overrides: Any) -> dict[str, Any]:
    value = {
        "connection_id": "sense-api",
        "name": "SenseNova API",
        "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1",
        "auth_method": "none",
        "enabled": True,
        "secret_status": "not_applicable",
        "external_session_status": "not_applicable",
    }
    value.update(overrides)
    return value


def _executor(**overrides: Any) -> dict[str, Any]:
    value = {
        "executor_id": "opencode",
        "name": "OpenCode",
        "operational": True,
        "capabilities": ["model_selection", "workspace_execution"],
    }
    value.update(overrides)
    return value


class _FakeTransport:
    def __init__(
        self,
        *,
        binding: Any | None = None,
        connection: Any | None = None,
        executor: Any | None = None,
        statuses: dict[str, int] | None = None,
    ) -> None:
        self.responses = {
            "/api/bindings/coding-fast": _binding() if binding is None else binding,
            "/api/connections/sense-api": _connection() if connection is None else connection,
            "/api/executors/opencode": _executor() if executor is None else executor,
        }
        self.statuses = statuses or {}
        self.calls: list[tuple[str, float, int]] = []

    def __call__(self, url: str, timeout: float, max_response_bytes: int):
        path = urlsplit(url).path
        self.calls.append((url, timeout, max_response_bytes))
        return self.statuses.get(path, 200), deepcopy(self.responses.get(path))


def test_resolver_rejects_non_loopback_model_control_before_transport() -> None:
    transport = _FakeTransport()

    with pytest.raises(BindingResolutionError, match="model_control_not_loopback"):
        BindingResolver("https://model-control.example.test:8765", transport=transport)

    assert transport.calls == []


def test_resolver_normalizes_secret_free_none_auth_resolution() -> None:
    transport = _FakeTransport()
    resolver = BindingResolver(transport=transport)

    resolution = resolver.resolve("coding-fast", task_executor="opencode")

    assert resolution == OpenCodeBindingResolution(
        binding_ref="coding-fast",
        connection_id="sense-api",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/sense-coding-fast",
        base_url="https://models.example.test/v1",
        auth_method="none",
        external_session_status="not_applicable",
    )
    assert [urlsplit(call[0]).path for call in transport.calls] == [
        "/api/bindings/coding-fast",
        "/api/connections/sense-api",
        "/api/executors/opencode",
    ]
    assert all(call[1] > 0 and call[2] > 0 for call in transport.calls)


def test_sanitized_public_status_fields_remain_accepted() -> None:
    resolution = BindingResolver(
        transport=_FakeTransport(
            connection=_connection(
                secret_status="not_applicable",
                external_session_status="not_applicable",
            )
        )
    ).resolve("coding-fast", task_executor="opencode")

    assert resolution.auth_method == "none"
    assert resolution.external_session_status == "not_applicable"


@pytest.mark.parametrize(
    ("transport", "reason"),
    [
        (
            _FakeTransport(statuses={"/api/bindings/coding-fast": 404}),
            "binding_not_found",
        ),
        (_FakeTransport(binding=_binding(enabled=False)), "binding_disabled"),
        (
            _FakeTransport(binding=_binding(binding_id="other-binding")),
            "binding_identity_mismatch",
        ),
        (
            _FakeTransport(binding=_binding(executor_id="other")),
            "binding_executor_mismatch",
        ),
        (
            _FakeTransport(statuses={"/api/connections/sense-api": 404}),
            "connection_not_found",
        ),
        (_FakeTransport(connection=_connection(enabled=False)), "connection_disabled"),
        (
            _FakeTransport(statuses={"/api/executors/opencode": 404}),
            "executor_not_found",
        ),
        (_FakeTransport(executor=_executor(operational=False)), "executor_not_operational"),
    ],
)
def test_resolver_fails_closed_for_missing_disabled_or_mismatched_records(
    transport: _FakeTransport,
    reason: str,
) -> None:
    with pytest.raises(BindingResolutionError, match=reason):
        BindingResolver(transport=transport).resolve(
            "coding-fast", task_executor="opencode"
        )


def test_api_key_auth_is_rejected_without_secret_transport() -> None:
    transport = _FakeTransport(
        connection=_connection(auth_method="api_key", secret_status="session")
    )

    with pytest.raises(BindingResolutionError, match="auth_method_api_key_forbidden"):
        BindingResolver(transport=transport).resolve(
            "coding-fast", task_executor="opencode"
        )


@pytest.mark.parametrize("auth_method", ["external_cli_session", "account_login"])
def test_external_auth_requires_available_session(auth_method: str) -> None:
    transport = _FakeTransport(
        connection=_connection(
            auth_method=auth_method,
            external_session_status="missing",
        )
    )

    with pytest.raises(BindingResolutionError, match="external_session_unavailable"):
        BindingResolver(transport=transport).resolve(
            "coding-fast", task_executor="opencode"
        )


@pytest.mark.parametrize("auth_method", ["external_cli_session", "account_login"])
def test_external_auth_accepts_available_session_without_credentials(
    auth_method: str,
) -> None:
    resolution = BindingResolver(
        transport=_FakeTransport(
            connection=_connection(
                auth_method=auth_method,
                external_session_status="available",
            )
        )
    ).resolve("coding-fast", task_executor="opencode")

    assert resolution.auth_method == auth_method
    assert resolution.external_session_status == "available"


def test_existing_matching_provider_prefix_is_preserved() -> None:
    resolution = BindingResolver(
        transport=_FakeTransport(
            binding=_binding(model_id="openai-compatible/sense-coding-fast")
        )
    ).resolve("coding-fast", task_executor="opencode")

    assert resolution.model_id == "openai-compatible/sense-coding-fast"


def test_provider_prefix_mismatch_fails_closed() -> None:
    with pytest.raises(BindingResolutionError, match="model_provider_mismatch"):
        BindingResolver(
            transport=_FakeTransport(binding=_binding(model_id="other/model"))
        ).resolve("coding-fast", task_executor="opencode")


def test_provider_base_url_query_is_rejected_before_transient_config() -> None:
    with pytest.raises(BindingResolutionError, match="connection_base_url_invalid"):
        BindingResolver(
            transport=_FakeTransport(
                connection=_connection(
                    base_url="https://models.example.test/v1?api_key=fake-not-real"
                )
            )
        ).resolve("coding-fast", task_executor="opencode")


@pytest.mark.parametrize(
    "secret_fragment",
    [
        {"api_key": "fake-openai-key-not-real"},
        {"nested": {"apiKey": "fake-anthropic-key-not-real"}},
        {"access_token": "fake-access-token-not-real"},
        {"nested": {"refresh_token": "fake-refresh-token-not-real"}},
        {"nested": [{"client_secret": "fake-client-secret-not-real"}]},
        {"nested": [{"token": "fake-token-not-real"}]},
        {"auth_token": "fake-auth-token-not-real"},
        {"bearer_token": "fake-bearer-token-not-real"},
        {"password": "fake-password-not-real"},
        {"secret": "fake-secret-not-real"},
        {"secret_key": "fake-secret-key-not-real"},
        {"credential": "fake-credential-not-real"},
        {"credentials": {"value": "fake-credentials-not-real"}},
        {"cookie": "fake-cookie-not-real"},
        {"authorization": "fake-authorization-not-real"},
        {"nested": {"private_key": "fake-private-key-not-real"}},
        {"nested": {"Access-Token": "fake-normalized-access-token-not-real"}},
    ],
)
def test_resolver_rejects_recursive_secret_material_without_echoing_value(
    secret_fragment: dict[str, Any],
) -> None:
    binding = _binding()
    binding.update(secret_fragment)

    with pytest.raises(BindingResolutionError) as excinfo:
        BindingResolver(transport=_FakeTransport(binding=binding)).resolve(
            "coding-fast", task_executor="opencode"
        )

    assert str(excinfo.value) == "secret_material_rejected"
    assert "fake-" not in str(excinfo.value)


def test_resolver_rejects_non_object_response_without_body_echo() -> None:
    body = ["fake-token-not-real"]

    with pytest.raises(BindingResolutionError) as excinfo:
        BindingResolver(transport=_FakeTransport(binding=body)).resolve(
            "coding-fast", task_executor="opencode"
        )

    assert str(excinfo.value) == "binding_response_not_object"
    assert "fake-token-not-real" not in str(excinfo.value)
