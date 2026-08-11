"""In-memory model profile and secret store for a trusted host."""

from __future__ import annotations

from dataclasses import dataclass
import os
from threading import RLock
from typing import Any, Mapping

from .contracts import Binding, Connection, ExecutionSnapshot, ExecutorDescriptor, ModelProfile


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


@dataclass(slots=True)
class _StoredConnection:
    connection: Connection
    api_key: str | None = None
    api_key_env: str | None = None
    external_session_status: str = "not_applicable"

    @property
    def secret_status(self) -> str:
        if self.connection.auth_method != "api_key":
            return "not_applicable"
        if self.api_key:
            return "session"
        if self.api_key_env:
            return "environment"
        return "missing"

    def public(self) -> dict[str, Any]:
        return self.connection.to_public_dict(
            secret_status=self.secret_status,
            external_session_status=self.external_session_status,
        )


class ModelProfileStore:
    """Process-local profile store that never serializes secret values."""

    def __init__(self) -> None:
        self._profiles: dict[str, _StoredProfile] = {}
        self._connections: dict[str, _StoredConnection] = {}
        self._executors = {
            "opencode": ExecutorDescriptor(
                executor_id="opencode",
                name="OpenCode",
                operational=True,
                capabilities=("model_selection", "workspace_execution"),
            )
        }
        self._bindings: dict[str, Binding] = {}
        self._lock = RLock()

    def list_connections_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [stored.public() for stored in self._connections.values()]

    def get_connection_public(self, connection_id: str) -> dict[str, Any]:
        with self._lock:
            stored = self._connections.get(connection_id)
            if stored is None:
                raise KeyError(f"connection not found: {connection_id}")
            return stored.public()

    def upsert_connection(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        connection = Connection.from_mapping(payload)
        with self._lock:
            existing = self._connections.get(connection.connection_id)

            authority_changed = _authority_fields_changed(existing, connection)

            incoming_api_key = _optional_secret(payload, "api_key", "apiKey")
            incoming_api_key_env = _optional_env(payload, "api_key_env", "apiKeyEnv")
            if incoming_api_key and incoming_api_key_env:
                raise ValueError("api_key and api_key_env are mutually exclusive")
            clear_secret = payload.get("clear_secret") is True or payload.get(
                "clearSecret"
            ) is True

            existing_api_key = existing.api_key if existing else None
            existing_api_key_env = existing.api_key_env if existing else None
            external_status = (
                existing.external_session_status if existing else "not_applicable"
            )

            if connection.auth_method == "api_key":
                if authority_changed:
                    if not clear_secret and not incoming_api_key and not incoming_api_key_env:
                        raise ValueError(
                            "authority-bearing connection field changed; "
                            "replacement api_key/api_key_env or clear_secret=true is required"
                        )
                if clear_secret:
                    api_key = None
                    api_key_env = None
                elif incoming_api_key:
                    api_key = incoming_api_key
                    api_key_env = None
                elif incoming_api_key_env:
                    api_key = None
                    api_key_env = incoming_api_key_env
                elif existing is None:
                    api_key = existing_api_key
                    api_key_env = existing_api_key_env
                else:
                    api_key = existing_api_key
                    api_key_env = existing_api_key_env
                external_status = "not_applicable"
            else:
                if incoming_api_key or incoming_api_key_env:
                    raise ValueError(
                        "raw session credentials are not accepted for this auth_method"
                    )
                _reject_raw_session_credentials(payload)
                api_key = None
                api_key_env = None
                if connection.auth_method in {"account_login", "external_cli_session"}:
                    incoming_status = payload.get(
                        "external_session_status",
                        payload.get("externalSessionStatus"),
                    )
                    if incoming_status is not None:
                        if incoming_status not in {"missing", "available"}:
                            raise ValueError(
                                "external_session_status must be missing or available"
                            )
                        external_status = str(incoming_status)
                    elif (
                        not existing
                        or existing.connection.auth_method != connection.auth_method
                    ):
                        external_status = "missing"
                else:
                    external_status = "not_applicable"

            stored = _StoredConnection(
                connection=connection,
                api_key=api_key,
                api_key_env=api_key_env,
                external_session_status=external_status,
            )
            self._connections[connection.connection_id] = stored
            return stored.public()

    def delete_connection(self, connection_id: str) -> None:
        with self._lock:
            if connection_id not in self._connections:
                raise KeyError(f"connection not found: {connection_id}")
            referenced_by = sorted(
                binding.binding_id
                for binding in self._bindings.values()
                if binding.connection_id == connection_id
            )
            if referenced_by:
                raise ValueError(
                    f"connection is referenced by binding: {referenced_by[0]}"
                )
            del self._connections[connection_id]

    def resolve_connection_secret(self, connection_id: str) -> str | None:
        with self._lock:
            stored = self._connections.get(connection_id)
            if stored is None:
                raise KeyError(f"connection not found: {connection_id}")
            if stored.api_key:
                return stored.api_key
            if stored.api_key_env:
                return os.environ.get(stored.api_key_env)
            return None

    def resolve_execution_snapshot(self, binding_id: str) -> ExecutionSnapshot:
        """Atomic private snapshot of one Binding + its Connection + secret.

        All fields are read under a single lock acquisition; the returned
        snapshot is immutable. This method is never exposed through the
        public Model Control API.
        """
        with self._lock:
            binding = self._bindings.get(binding_id)
            if binding is None:
                raise KeyError(f"binding not found: {binding_id}")
            if binding.connection_id not in self._connections:
                raise KeyError(f"binding references unknown connection")
            stored_conn = self._connections[binding.connection_id]
            conn = stored_conn.connection
            resolved_key: str | None = None
            if conn.auth_method == "api_key":
                if stored_conn.api_key:
                    resolved_key = stored_conn.api_key
                elif stored_conn.api_key_env:
                    resolved_key = os.environ.get(stored_conn.api_key_env)
            return ExecutionSnapshot(
                binding_id=binding.binding_id,
                binding_enabled=binding.enabled,
                executor_id=binding.executor_id,
                raw_model_id=binding.model_id,
                connection_id=conn.connection_id,
                connection_enabled=conn.enabled,
                provider=conn.provider,
                base_url=conn.base_url,
                auth_method=conn.auth_method,
                resolved_api_key=resolved_key,
                external_session_status=stored_conn.external_session_status,
            )

    def list_executors_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [executor.to_public_dict() for executor in self._executors.values()]

    def get_executor_public(self, executor_id: str) -> dict[str, Any]:
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None:
                raise KeyError(f"executor not found: {executor_id}")
            return executor.to_public_dict()

    def list_bindings_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [binding.to_public_dict() for binding in self._bindings.values()]

    def get_binding_public(self, binding_id: str) -> dict[str, Any]:
        with self._lock:
            binding = self._bindings.get(binding_id)
            if binding is None:
                raise KeyError(f"binding not found: {binding_id}")
            return binding.to_public_dict()

    def upsert_binding(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        binding = Binding.from_mapping(payload)
        with self._lock:
            if binding.connection_id not in self._connections:
                raise ValueError(f"unknown connection_id: {binding.connection_id}")
            if binding.executor_id not in self._executors:
                raise ValueError(f"unknown executor_id: {binding.executor_id}")
            self._bindings[binding.binding_id] = binding
            return binding.to_public_dict()

    def delete_binding(self, binding_id: str) -> None:
        with self._lock:
            if binding_id not in self._bindings:
                raise KeyError(f"binding not found: {binding_id}")
            del self._bindings[binding_id]

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


def _reject_raw_session_credentials(payload: Mapping[str, Any]) -> None:
    forbidden = {
        "token",
        "access_token",
        "accessToken",
        "password",
        "session_credential",
        "sessionCredential",
    }
    if forbidden.intersection(payload):
        raise ValueError("raw session credentials are not accepted")


def _authority_fields_changed(
    existing: "_StoredConnection | None",
    new_connection: Connection,
) -> bool:
    """Return True if any authority-bearing connection field would change."""
    if existing is None:
        return False
    old = existing.connection
    return (
        old.provider != new_connection.provider
        or old.base_url != new_connection.base_url
        or old.auth_method != new_connection.auth_method
    )
