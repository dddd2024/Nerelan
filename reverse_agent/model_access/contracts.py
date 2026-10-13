"""Model access contracts shared by the trusted-host control service."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from .provider_identity import ProviderIdentity

_PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_PROVIDER_VALUES = frozenset({"openai-compatible", "litellm-proxy"})
_EXECUTOR_VALUES = frozenset({"openhands", "codex-acp"})
_AUTH_METHOD_VALUES = frozenset(
    {"api_key", "account_login", "external_cli_session", "none"}
)
_SECRET_STATUS_VALUES = frozenset(
    {
        "missing",
        "session",
        "environment",
        "not_applicable",
        "stored",
        "store_locked",
        "replacement_required",
    }
)
_EXTERNAL_SESSION_STATUS_VALUES = frozenset(
    {"missing", "available", "executor_managed", "not_applicable"}
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


def _provider_alias(value: Any) -> str:
    """Normalize the temporary legacy provider alias as an executor namespace."""

    return ProviderIdentity.from_legacy_provider(value).executor_provider_id


# Native CLI executors own their account login (ChatGPT for Codex, a Claude
# account for Claude Code); Nerelan never reads or relays their credentials.
# executor provider id -> (upstream provider, protocol family, executor id)
NATIVE_CLI_PROVIDERS: dict[str, tuple[str, str, str]] = {
    "codex": ("openai", "codex-cli", "codex"),
    "claude-code": ("anthropic", "claude-code-cli", "claude_code"),
}
NATIVE_CLI_EXECUTORS = frozenset(spec[2] for spec in NATIVE_CLI_PROVIDERS.values())

# Multi-agent team roles. Each role is filled by one saved Binding, so different
# kinds of work go to agents of matching capability and cost.
AGENT_ROLES: tuple[str, ...] = ("planner", "complex", "coder", "simple", "reviewer")
NATIVE_CLI_PROVIDER_FOR_EXECUTOR = {spec[2]: provider for provider, spec in NATIVE_CLI_PROVIDERS.items()}


def _connection_provider_identity(value: Any) -> ProviderIdentity:
    identity = ProviderIdentity.from_legacy_provider(value)
    spec = NATIVE_CLI_PROVIDERS.get(identity.executor_provider_id)
    if spec is not None:
        return ProviderIdentity(spec[0], spec[1], identity.executor_provider_id)
    return identity


# An API-key connection that speaks Anthropic's Messages API (for example GLM, DeepSeek or
# Kimi through their Anthropic-compatible endpoints) can drive Claude Code through the relay.
ANTHROPIC_PROTOCOL = "anthropic"


# Providers whose one API key also serves an Anthropic Messages endpoint. A connection to
# one of these hosts carries that endpoint automatically, so the same key drives OpenCode
# (OpenAI protocol) and Claude Code (Anthropic protocol) with no second connection.
KNOWN_ANTHROPIC_ENDPOINTS = {
    "token.sensenova.cn": "https://token.sensenova.cn",
    "open.bigmodel.cn": "https://open.bigmodel.cn/api/anthropic",
    "api.deepseek.com": "https://api.deepseek.com/anthropic",
    "api.moonshot.cn": "https://api.moonshot.cn/anthropic",
}


def _read_field(connection: Mapping[str, Any] | "Connection", key: str) -> Any:
    return connection.get(key) if isinstance(connection, Mapping) else getattr(connection, key, None)


def anthropic_endpoint(connection: Mapping[str, Any] | "Connection") -> str | None:
    """The Anthropic Messages base URL this API-key connection's key can use, if any."""
    if _read_field(connection, "auth_method") != "api_key":
        return None
    if _read_field(connection, "executor_provider_id") in NATIVE_CLI_PROVIDERS:
        return None
    if _read_field(connection, "protocol_family") == ANTHROPIC_PROTOCOL:
        return _read_field(connection, "base_url")
    return _read_field(connection, "anthropic_base_url") or None


def is_anthropic_relay_connection(connection: Mapping[str, Any] | "Connection") -> bool:
    if _read_field(connection, "auth_method") != "api_key":
        return False
    if _read_field(connection, "executor_provider_id") in NATIVE_CLI_PROVIDERS:
        return False
    return (_read_field(connection, "protocol_family") == ANTHROPIC_PROTOCOL
            or bool(_read_field(connection, "anthropic_base_url")))


@dataclass(frozen=True, slots=True)
class Connection:
    """Sanitized provider/service access metadata.

    ``provider`` is retained only as a compatibility alias for
    ``executor_provider_id``. Provider/account semantics belong exclusively to
    ``upstream_provider_id`` and wire compatibility belongs to
    ``protocol_family``.

    Raw API keys and environment references belong to the trusted process-local
    store and are deliberately absent from this contract.
    """

    connection_id: str
    name: str
    provider: str
    base_url: str
    auth_method: str
    enabled: bool = True
    upstream_provider_id: str | None = None
    protocol_family: str | None = None
    executor_provider_id: str | None = None
    anthropic_base_url: str | None = None

    def __post_init__(self) -> None:
        provider_alias = _provider_alias(self.provider)
        partial_explicit_identity = (
            self.upstream_provider_id is not None
            or self.protocol_family is not None
        )
        if self.executor_provider_id is None:
            if partial_explicit_identity:
                raise ValueError(
                    "executor_provider_id is required when explicit provider identity is supplied"
                )
            identity = _connection_provider_identity(provider_alias)
        else:
            identity = ProviderIdentity(
                upstream_provider_id=self.upstream_provider_id,
                protocol_family=self.protocol_family,
                executor_provider_id=self.executor_provider_id,
            )
            if provider_alias != identity.executor_provider_id:
                raise ValueError(
                    "provider must match executor_provider_id when both are supplied"
                )
        object.__setattr__(self, "provider", identity.executor_provider_id)
        object.__setattr__(self, "upstream_provider_id", identity.upstream_provider_id)
        object.__setattr__(self, "protocol_family", identity.protocol_family)
        object.__setattr__(self, "executor_provider_id", identity.executor_provider_id)
        native = NATIVE_CLI_PROVIDERS.get(identity.executor_provider_id)
        if native is not None and (
            identity.upstream_provider_id != native[0] or identity.protocol_family != native[1]
            or self.auth_method != "external_cli_session"
        ):
            prefix = native[2]
            raise ValueError(f"{prefix}_requires_managed_session_connection")

    @property
    def provider_identity(self) -> ProviderIdentity:
        return ProviderIdentity(
            upstream_provider_id=self.upstream_provider_id,
            protocol_family=self.protocol_family,
            executor_provider_id=self.provider,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Connection":
        auth_method = _required_text(
            _read(value, "auth_method", "authMethod"),
            "auth_method",
            maximum=40,
        )
        if auth_method not in _AUTH_METHOD_VALUES:
            raise ValueError(f"unsupported auth_method: {auth_method}")

        explicit_identity_keys = {
            "upstream_provider_id",
            "upstreamProviderId",
            "protocol_family",
            "protocolFamily",
            "executor_provider_id",
            "executorProviderId",
        }
        has_explicit_identity = bool(explicit_identity_keys.intersection(value))
        provider_raw = _read(value, "provider")

        if has_explicit_identity:
            executor_raw = _read(
                value, "executor_provider_id", "executorProviderId"
            )
            if executor_raw is None:
                raise ValueError(
                    "executor_provider_id is required when explicit provider identity is supplied"
                )
            identity = ProviderIdentity(
                upstream_provider_id=_read(
                    value, "upstream_provider_id", "upstreamProviderId"
                ),
                protocol_family=_read(value, "protocol_family", "protocolFamily"),
                executor_provider_id=executor_raw,
            )
            if provider_raw is None:
                provider = identity.executor_provider_id
            else:
                provider = _provider_alias(provider_raw)
                if provider != identity.executor_provider_id:
                    raise ValueError(
                        "provider must match executor_provider_id when both are supplied"
                    )
        else:
            if provider_raw is None:
                raise ValueError("provider is required")
            identity = _connection_provider_identity(provider_raw)
            provider = identity.executor_provider_id

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
            upstream_provider_id=identity.upstream_provider_id,
            protocol_family=identity.protocol_family,
            executor_provider_id=identity.executor_provider_id,
            anthropic_base_url=_anthropic_base_url(value, auth_method, identity.protocol_family,
                                                   _read(value, "base_url", "baseUrl")),
        )

    def to_public_dict(
        self,
        *,
        credential_configured: bool,
        secret_status: str,
        external_session_status: str,
    ) -> dict[str, Any]:
        if not isinstance(credential_configured, bool):
            raise ValueError("credential_configured must be a boolean")
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
            "upstream_provider_id": self.upstream_provider_id,
            "protocol_family": self.protocol_family,
            "executor_provider_id": self.executor_provider_id,
            "base_url": self.base_url,
            "anthropic_base_url": self.anthropic_base_url,
            "auth_method": self.auth_method,
            "enabled": self.enabled,
            "credential_configured": credential_configured,
            "secret_status": secret_status,
            "external_session_status": external_session_status,
        }


def _anthropic_base_url(value: Mapping[str, Any], auth_method: str, protocol_family: str | None,
                        base_url: Any) -> str | None:
    """Explicit Anthropic endpoint, else the known one for this host; only for OpenAI-protocol API keys."""
    if auth_method != "api_key" or protocol_family == ANTHROPIC_PROTOCOL:
        return None
    explicit = _read(value, "anthropic_base_url", "anthropicBaseUrl")
    if explicit not in (None, ""):
        return _base_url(explicit)
    from urllib.parse import urlsplit
    try:
        host = (urlsplit(str(base_url or "")).hostname or "").casefold()
    except ValueError:
        return None
    return KNOWN_ANTHROPIC_ENDPOINTS.get(host)


@dataclass(frozen=True, slots=True)
class ExecutorDescriptor:
    """Public capability metadata for a currently proven executor runtime."""

    executor_id: str
    name: str
    operational: bool
    capabilities: tuple[str, ...]
    readiness_status: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        result = {
            "executor_id": self.executor_id,
            "name": self.name,
            "operational": self.operational,
            "capabilities": list(self.capabilities),
        }
        if self.readiness_status:
            result["readiness_status"] = self.readiness_status
        return result


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
    upstream_provider_id: str | None = None
    protocol_family: str | None = None
    executor_provider_id: str | None = None


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
