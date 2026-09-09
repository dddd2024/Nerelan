"""Provider identity normalization for account, protocol, and executor axes.

This module is intentionally provider-free: it performs no I/O, credential
resolution, provider calls, or state migration.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .provider_usage import ProviderDispatch


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")

_LEGACY_PROVIDER_MAP: dict[str, tuple[str | None, str | None]] = {
    "openai": ("openai", "openai"),
    "sensetime": ("sensetime", "openai"),
    "deepseek": ("deepseek", "openai"),
    "openrouter": ("openrouter", "openai"),
    "openai-compatible": (None, "openai"),
    "litellm-proxy": (None, "openai"),
}


def _normalize_identifier(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{field} is required")
    if not _IDENTIFIER.fullmatch(normalized):
        raise ValueError(
            f"{field} must use lowercase letters, digits, dots, underscores or hyphens "
            "and be at most 80 characters"
        )
    return normalized


def _normalize_optional_identifier(value: object | None, field: str) -> str | None:
    if value is None:
        return None
    return _normalize_identifier(value, field)


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    """Three independent provider-identity axes.

    ``upstream_provider_id`` identifies the provider/account semantics used by
    usage and quota collectors. ``protocol_family`` identifies wire
    compatibility. ``executor_provider_id`` is the executor/OpenCode namespace.
    """

    upstream_provider_id: str | None
    protocol_family: str | None
    executor_provider_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "upstream_provider_id",
            _normalize_optional_identifier(
                self.upstream_provider_id, "upstream_provider_id"
            ),
        )
        object.__setattr__(
            self,
            "protocol_family",
            _normalize_optional_identifier(self.protocol_family, "protocol_family"),
        )
        object.__setattr__(
            self,
            "executor_provider_id",
            _normalize_identifier(self.executor_provider_id, "executor_provider_id"),
        )

    @classmethod
    def from_legacy_provider(cls, provider: object) -> "ProviderIdentity":
        """Classify one schema-v1 provider token without fuzzy inference."""

        executor_provider_id = _normalize_identifier(provider, "provider")
        upstream_provider_id, protocol_family = _LEGACY_PROVIDER_MAP.get(
            executor_provider_id, (None, None)
        )
        return cls(
            upstream_provider_id=upstream_provider_id,
            protocol_family=protocol_family,
            executor_provider_id=executor_provider_id,
        )


def resolve_provider_usage_dispatch(
    identity: ProviderIdentity,
) -> "ProviderDispatch | None":
    """Resolve existing ProviderUsage dispatch only for concrete upstream truth."""

    if not isinstance(identity, ProviderIdentity):
        raise TypeError("identity must be ProviderIdentity")
    if identity.upstream_provider_id is None or identity.protocol_family is None:
        return None

    from .provider_usage import resolve_provider_dispatch

    return resolve_provider_dispatch(
        identity.upstream_provider_id,
        identity.protocol_family,
    )


def identity_authority_equivalent(
    left: ProviderIdentity,
    right: ProviderIdentity,
) -> bool:
    """Return True only when all three explicit authority axes are equal."""

    if not isinstance(left, ProviderIdentity) or not isinstance(right, ProviderIdentity):
        raise TypeError("left and right must be ProviderIdentity")
    return left == right


def identity_authority_changed(
    left: ProviderIdentity,
    right: ProviderIdentity,
) -> bool:
    """Return True when any explicit authority axis changes."""

    return not identity_authority_equivalent(left, right)
