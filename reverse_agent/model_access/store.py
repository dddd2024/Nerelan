"""In-memory model profile and secret store for a trusted host."""

from __future__ import annotations

from dataclasses import dataclass
import os
from threading import RLock
from typing import Any, Mapping

from .contracts import ModelProfile


@dataclass(slots=True)
class _StoredProfile:
    profile: ModelProfile
    api_key: str | None = None
    api_key_env: str | None = None

    @property
    def secret_status(self) -> str:
        if self.api_key:
            return "session"
        if self.api_key_env:
            return "environment"
        return "missing"

    def public(self) -> dict[str, Any]:
        return self.profile.to_public_dict(self.secret_status)


class ModelProfileStore:
    """Process-local profile store that never serializes secret values."""

    def __init__(self) -> None:
        self._profiles: dict[str, _StoredProfile] = {}
        self._lock = RLock()

    def list_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [stored.public() for stored in self._profiles.values()]

    def upsert(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        profile = ModelProfile.from_mapping(payload)
        with self._lock:
            existing = self._profiles.get(profile.id)
            api_key = existing.api_key if existing else None
            api_key_env = existing.api_key_env if existing else None

            incoming_api_key = _optional_secret(payload, "api_key", "apiKey")
            incoming_api_key_env = _optional_env(payload, "api_key_env", "apiKeyEnv")
            clear_secret = payload.get("clear_secret") is True or payload.get(
                "clearSecret"
            ) is True

            if clear_secret:
                api_key = None
                api_key_env = None
            elif incoming_api_key:
                api_key = incoming_api_key
                api_key_env = None
            elif incoming_api_key_env:
                api_key = None
                api_key_env = incoming_api_key_env

            if profile.is_default:
                self._unset_default_locked(except_id=profile.id)
            elif not self._profiles or not self._has_default_locked():
                profile = profile.with_default(True)

            stored = _StoredProfile(
                profile=profile,
                api_key=api_key,
                api_key_env=api_key_env,
            )
            self._profiles[profile.id] = stored
            self._ensure_default_locked()
            return stored.public()

    def delete(self, profile_id: str) -> None:
        with self._lock:
            if profile_id not in self._profiles:
                raise KeyError(f"model profile not found: {profile_id}")
            was_default = self._profiles[profile_id].profile.is_default
            del self._profiles[profile_id]
            if was_default:
                self._ensure_default_locked(force=True)

    def set_default(self, profile_id: str) -> list[dict[str, Any]]:
        with self._lock:
            if profile_id not in self._profiles:
                raise KeyError(f"model profile not found: {profile_id}")
            self._unset_default_locked(except_id=profile_id)
            stored = self._profiles[profile_id]
            stored.profile = stored.profile.with_default(True)
            return [item.public() for item in self._profiles.values()]

    def get_profile(self, profile_id: str) -> ModelProfile:
        with self._lock:
            stored = self._profiles.get(profile_id)
            if stored is None:
                raise KeyError(f"model profile not found: {profile_id}")
            return stored.profile

    def resolve_secret(self, profile_id: str) -> str | None:
        with self._lock:
            stored = self._profiles.get(profile_id)
            if stored is None:
                raise KeyError(f"model profile not found: {profile_id}")
            if stored.api_key:
                return stored.api_key
            if stored.api_key_env:
                return os.environ.get(stored.api_key_env)
            return None

    def _has_default_locked(self) -> bool:
        return any(stored.profile.is_default for stored in self._profiles.values())

    def _unset_default_locked(self, except_id: str) -> None:
        for profile_id, stored in self._profiles.items():
            if profile_id != except_id and stored.profile.is_default:
                stored.profile = stored.profile.with_default(False)

    def _ensure_default_locked(self, force: bool = False) -> None:
        if not force and self._has_default_locked():
            return
        candidate = next(
            (
                stored
                for stored in self._profiles.values()
                if stored.profile.enabled
            ),
            None,
        )
        if candidate is not None:
            self._unset_default_locked(except_id=candidate.profile.id)
            candidate.profile = candidate.profile.with_default(True)


def _optional_secret(
    payload: Mapping[str, Any], snake: str, camel: str
) -> str | None:
    value = payload.get(snake, payload.get(camel))
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{snake} must be a string")
    if len(value) > 4096:
        raise ValueError(f"{snake} exceeds 4096 characters")
    return value


def _optional_env(
    payload: Mapping[str, Any], snake: str, camel: str
) -> str | None:
    value = payload.get(snake, payload.get(camel))
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{snake} must be a string")
    normalized = value.strip()
    if not normalized or not normalized.replace("_", "A").isalnum() or not (
        normalized[0].isalpha() or normalized[0] == "_"
    ):
        raise ValueError(f"{snake} is not a valid environment variable name")
    if normalized.upper() != normalized:
        raise ValueError(f"{snake} must use uppercase characters")
    return normalized
