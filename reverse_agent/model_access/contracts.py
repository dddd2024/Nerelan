"""Model access contracts shared by the trusted-host control service."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

_PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_PROVIDER_VALUES = frozenset({"openai-compatible", "litellm-proxy"})
_EXECUTOR_VALUES = frozenset({"openhands", "codex-acp"})
_AUTH_METHOD_VALUES = frozenset(
    {"api_key", "account_login", "external_cli_session", "none"}
)
_SECRET_STATUS_VALUES = frozenset(
    {"missing", "session", "environment", "not_applicable"}
)
_EXTERNAL_SESSION_STATUS_VALUES = frozenset(
    {"missing", "available", "not_applicable"}
)


def _read(mapping: Mapping[str, Any], snake: str, camel: str | None = None) -> Any:
    if snake in mapping:
        return mapping[snake]
    if camel and camel in mapping:
        return mapping[camel]
    return None


def _required_text(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return normalized


def _boolean(value: Any, field: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _identifier(value: Any, field: str) -> str:
    normalized = _required_text(value, field, maximum=80)
    if not _PROFILE_ID.fullmatch(normalized):
        raise ValueError(
            f"{field} must use lowercase letters, digits, dots, underscores or hyphens"
        )
    return normalized


def _base_url(value: Any) -> str:
    normalized = _required_text(value, "base_url", maximum=2048).rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an absolute http or https URL")
    if parsed.username or parsed.password:
        raise ValueError("base_url must not contain credentials")
    if parsed.fragment:
        raise ValueError("base_url must not contain a fragment")
    return normalized


@dataclass(frozen=True, slots=True)
class Connection:
    """Sanitized provider/service access metadata.

    Raw API keys and environment references belong to the trusted process-local
    store and are deliberately absent from this contract.
    """

    connection_id: str
    name: str
    provider: str
    base_url: str
    auth_method: str
    enabled: bool = True

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Connection":
        auth_method = _required_text(
            _read(value, "auth_method", "authMethod"),
            "auth_method",
            maximum=40,
        )
        if auth_method not in _AUTH_METHOD_VALUES:
            raise ValueError(f"unsupported auth_method: {auth_method}")
        provider = _identifier(_read(value, "provider"), "provider")
        return cls(
            connection_id=_identifier(
                _read(value, "connection_id", "connectionId"),
                "connection_id",
            ),
            name=_required_text(_read(value, "name"), "name", maximum=120),
            provider=provider,
            base_url=_base_url(_read(value, "base_url", "baseUrl")),
            auth_method=auth_method,
            enabled=_boolean(_read(value, "enabled"), "enabled", True),
        )

    def to_public_dict(
        self,
        *,
        secret_status: str,
        external_session_status: str,
    ) -> dict[str, Any]:
        if secret_status not in _SECRET_STATUS_VALUES:
            raise ValueError(f"unsupported secret status: {secret_status}")
        if external_session_status not in _EXTERNAL_SESSION_STATUS_VALUES:
            raise ValueError(
                f"unsupported external session status: {external_session_status}"
            )
        return {
            "connection_id": self.connection_id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "auth_method": self.auth_method,
            "enabled": self.enabled,
            "secret_status": secret_status,
            "external_session_status": external_session_status,
        }


@dataclass(frozen=True, slots=True)
class ExecutorDescriptor:
    """Public capability metadata for a currently proven executor runtime."""

    executor_id: str
    name: str
    operational: bool
    capabilities: tuple[str, ...]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "name": self.name,
            "operational": self.operational,
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True, slots=True)
class Binding:
    """References one executor, one connection and one model identifier."""

    binding_id: str
    name: str
    executor_id: str
    connection_id: str
    model_id: str
    enabled: bool = True

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Binding":
        forbidden = {
            "api_key",
            "apiKey",
            "key",
            "password",
            "secret",
            "token",
            "credential",
        }
        if forbidden.intersection(value):
            raise ValueError("Binding must contain references, not credentials")
        return cls(
            binding_id=_identifier(
                _read(value, "binding_id", "bindingId"), "binding_id"
            ),
            name=_required_text(_read(value, "name"), "name", maximum=120),
            executor_id=_identifier(
                _read(value, "executor_id", "executorId"), "executor_id"
            ),
            connection_id=_identifier(
                _read(value, "connection_id", "connectionId"),
                "connection_id",
            ),
            model_id=_required_text(
                _read(value, "model_id", "modelId"), "model_id", maximum=200
            ),
            enabled=_boolean(_read(value, "enabled"), "enabled", True),
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "name": self.name,
            "executor_id": self.executor_id,
            "connection_id": self.connection_id,
            "model_id": self.model_id,
            "enabled": self.enabled,
        }


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Non-secret model profile metadata."""

    id: str
    name: str
    provider: str
    base_url: str
    model_id: str
    executor: str
    enabled: bool = True
    is_default: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ModelProfile":
        profile_id = _required_text(_read(value, "id"), "id", maximum=80)
        if not _PROFILE_ID.fullmatch(profile_id):
            raise ValueError(
                "id must use lowercase letters, digits, dots, underscores or hyphens"
            )

        provider = _required_text(
            _read(value, "provider"), "provider", maximum=40
        )
        if provider not in _PROVIDER_VALUES:
            raise ValueError(f"unsupported provider: {provider}")

        executor = _required_text(
            _read(value, "executor"), "executor", maximum=40
        )
        if executor not in _EXECUTOR_VALUES:
            raise ValueError(f"unsupported executor: {executor}")

        base_url = _required_text(
            _read(value, "base_url", "baseUrl"), "base_url", maximum=2048
        ).rstrip("/")
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute http or https URL")
        if parsed.username or parsed.password:
            raise ValueError("base_url must not contain credentials")
        if parsed.fragment:
            raise ValueError("base_url must not contain a fragment")

        return cls(
            id=profile_id,
            name=_required_text(_read(value, "name"), "name", maximum=120),
            provider=provider,
            base_url=base_url,
            model_id=_required_text(
                _read(value, "model_id", "modelId"),
                "model_id",
                maximum=200,
            ),
            executor=executor,
            enabled=_boolean(_read(value, "enabled"), "enabled", True),
            is_default=_boolean(
                _read(value, "is_default", "isDefault"),
                "is_default",
                False,
            ),
        )

    def with_default(self, is_default: bool) -> "ModelProfile":
        return ModelProfile(
            id=self.id,
            name=self.name,
            provider=self.provider,
            base_url=self.base_url,
            model_id=self.model_id,
            executor=self.executor,
            enabled=self.enabled,
            is_default=is_default,
        )

    def to_public_dict(self, secret_status: str = "missing") -> dict[str, Any]:
        if secret_status not in {"missing", "session", "environment"}:
            raise ValueError(f"unsupported secret status: {secret_status}")
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "model_id": self.model_id,
            "executor": self.executor,
            "enabled": self.enabled,
            "is_default": self.is_default,
            "secret_status": secret_status,
        }


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    """Private trusted-host snapshot read atomically under the store lock.

    This object must never be serialized through the public Model Control API.
    It carries the exact execution-scoped identity plus the resolved provider
    API key, all read under a single store-lock acquisition so that the
    Binding, Connection, and secret cannot drift between reads.
    """

    binding_id: str
    binding_enabled: bool
    executor_id: str
    raw_model_id: str
    connection_id: str
    connection_enabled: bool
    provider: str
    base_url: str
    auth_method: str
    resolved_api_key: str | None
    external_session_status: str


@dataclass(frozen=True, slots=True)
class ProbeResult:
    ok: bool
    status: str
    message: str
    latency_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "message": self.message,
            "latency_ms": self.latency_ms,
        }
