"""In-memory model profile and secret store for a trusted host."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from threading import RLock
from typing import Any, Mapping
import tempfile

from .contracts import Binding, Connection, ExecutionSnapshot, ExecutorDescriptor, ModelProfile


# Schema version for persisted sanitized product setup state.
_STATE_SCHEMA_VERSION = 1

# Field names that are strictly forbidden in persisted state files.
_FORBIDDEN_PERSISTED_FIELDS = frozenset({
    "api_key",
    "apiKey",
    "key",
    "secret",
    "password",
    "token",
    "access_token",
    "accessToken",
    "refresh_token",
    "refreshToken",
    "client_secret",
    "clientSecret",
    "session_credential",
    "sessionCredential",
    "authorization",
    "bearer",
    "cookie",
    "private_key",
    "account_token",
    "external_session_status",
    "externalSessionStatus",
    "executor_managed",
})

# Sanitized connection fields that are safe to persist.
_CONNECTION_SAFE_FIELDS = frozenset({
    "connection_id",
    "name",
    "provider",
    "base_url",
    "auth_method",
    "enabled",
    "api_key_env",
})

# Binding fields that are safe to persist.
_BINDING_SAFE_FIELDS = frozenset({
    "binding_id",
    "name",
    "executor_id",
    "connection_id",
    "model_id",
    "enabled",
})


class StoreError(RuntimeError):
    """Bounded error raised when persistence or load validation fails."""


def _sanitize_env_name(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("api_key_env must be a string or absent")
    normalized = value.strip()
    if not normalized or not normalized.replace("_", "A").isalnum() or not (
        normalized[0].isalpha() or normalized[0] == "_"
    ):
        raise ValueError("api_key_env is not a valid environment variable name")
    if normalized.upper() != normalized:
        raise ValueError("api_key_env must use uppercase characters")
    return normalized


def _write_atomic(data: bytes, target: Path) -> None:
    parent = target.parent
    os.makedirs(parent, exist_ok=True)
    fd = None
    tmp_path = None
    try:
        fd = tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(parent),
            delete=False,
            prefix=".model_setup_",
            suffix=".tmp",
        )
        tmp_path = Path(fd.name)
        fd.write(data)
        fd.flush()
        os.fsync(fd.fileno())
        fd.close()
        fd = None
        os.replace(str(tmp_path), str(target))
    finally:
        if fd is not None:
            try:
                fd.close()
            except Exception:
                pass
        if tmp_path is not None:
            try:
                os.unlink(str(tmp_path))
            except Exception:
                pass


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
    def credential_configured(self) -> bool:
        return (
            self.connection.auth_method == "api_key"
            and bool(self.api_key or self.api_key_env)
        )

    @property
    def secret_status(self) -> str:
        if self.connection.auth_method != "api_key":
            return "not_applicable"
        if self.api_key:
            return "session"
        if self.api_key_env and os.environ.get(self.api_key_env) is not None:
            return "environment"
        return "missing"

    def public(self) -> dict[str, Any]:
        return self.connection.to_public_dict(
            credential_configured=self.credential_configured,
            secret_status=self.secret_status,
            external_session_status=self.external_session_status,
        )

    def sanitized_dict(self) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "connection_id": self.connection.connection_id,
            "name": self.connection.name,
            "provider": self.connection.provider,
            "base_url": self.connection.base_url,
            "auth_method": self.connection.auth_method,
            "enabled": self.connection.enabled,
        }
        if self.api_key_env:
            entry["api_key_env"] = self.api_key_env
        return entry

    @classmethod
    def from_sanitized_dict(cls, data: Mapping[str, Any]) -> "_StoredConnection":
        if not isinstance(data, dict):
            raise ValueError("invalid connection record: not an object")
        extra = set(data.keys()) - _CONNECTION_SAFE_FIELDS
        if extra:
            raise ValueError(
                f"forbidden field(s) in persisted connection: {sorted(extra)}"
            )
        api_key_env = _sanitize_env_name(data.get("api_key_env"))
        conn = Connection.from_mapping(dict(data))
        auth_method = conn.auth_method
        if auth_method in {"account_login", "external_cli_session"}:
            initial_status = "executor_managed"
        else:
            initial_status = "not_applicable"
        return cls(
            connection=conn,
            api_key=None,
            api_key_env=api_key_env,
            external_session_status=initial_status,
        )


class ModelProfileStore:
    """Profile store with optional durable sanitized metadata persistence.

    When ``state_path`` is None (default) the store is purely process-local
    and backward compatible with all existing callers.  When a path is
    provided the store persists a schema-versioned JSON document containing
    only sanitized Connection/Binding metadata.  Raw secrets, credentials,
    and session tokens are never written.
    """

    def __init__(self, state_path: str | Path | None = None) -> None:
        self._state_path: Path | None = None
        if state_path is not None:
            self._state_path = Path(state_path).resolve()

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

        if self._state_path is not None:
            self._load_from_disk()

    def list_connections_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [stored.public() for stored in self._connections.values()]

    def refresh_external_session_status(
        self,
        authenticated_provider_ids: Mapping[str, str],
    ) -> int:
        """Refresh in-memory external-session status from sanitized auth probe.

        ``authenticated_provider_ids`` is a provider-id -> auth-type mapping
        derived from a fresh, sanitized OpenCode ``auth list`` probe.
        External-session status is intentionally NOT persisted; each fresh
        process must reprove availability from a live probe.

        Only exact provider-ID matches are accepted (no fuzzy matching, no
        display-label guessing).  ``api_key`` and ``none`` Connections
        always remain ``not_applicable``.
        """
        provider_set = set(authenticated_provider_ids.keys())
        refreshed = 0
        with self._lock:
            for stored in self._connections.values():
                auth_method = stored.connection.auth_method
                if auth_method in {"account_login", "external_cli_session"}:
                    provider = stored.connection.provider
                    if not provider:
                        status = "missing"
                    elif provider in provider_set:
                        status = "available"
                    else:
                        status = "missing"
                    if stored.external_session_status != status:
                        refreshed += 1
                    stored.external_session_status = status
                else:
                    if stored.external_session_status != "not_applicable":
                        refreshed += 1
                    stored.external_session_status = "not_applicable"
        return refreshed

    def has_external_session_connections(self) -> bool:
        """Return True if any Connection uses an external-session auth method."""
        for stored in self._connections.values():
            if stored.connection.auth_method in {
                "account_login",
                "external_cli_session",
            }:
                return True
        return False

    def get_connection_public(self, connection_id: str) -> dict[str, Any]:
        with self._lock:
            stored = self._connections.get(connection_id)
            if stored is None:
                raise KeyError(f"connection not found: {connection_id}")
            return stored.public()

    def upsert_connection(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        _reject_derived_external_status(payload)
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
                if (
                    existing is not None
                    and existing.connection.auth_method == "api_key"
                    and existing.credential_configured
                    and not clear_secret
                ):
                    raise ValueError(
                        "configured API-key credential would be discarded; "
                        "clear_secret=true is required"
                    )
                api_key = None
                api_key_env = None
                if connection.auth_method in {"account_login", "external_cli_session"}:
                    if (
                        not existing
                        or existing.connection.auth_method
                        != connection.auth_method
                        or authority_changed
                    ):
                        external_status = "executor_managed"
                    else:
                        external_status = existing.external_session_status
                else:
                    external_status = "not_applicable"

            old_stored = self._connections.get(connection.connection_id)
            snap_conns = dict(self._connections)
            snap_bindings = dict(self._bindings)
            stored = _StoredConnection(
                connection=connection,
                api_key=api_key,
                api_key_env=api_key_env,
                external_session_status=external_status,
            )
            self._connections[connection.connection_id] = stored
            result = stored.public()
            if self._state_path is not None:
                self._persist_with_rollback(
                    snap_conns, snap_bindings,
                    lambda: self._rollback_conn_binding(snap_conns, snap_bindings),
                )
            return result

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
            snap_conns = dict(self._connections)
            snap_bindings = dict(self._bindings)
            del self._connections[connection_id]
            if self._state_path is not None:
                self._persist_with_rollback(
                    snap_conns, snap_bindings,
                    lambda: self._rollback_conn_binding(snap_conns, snap_bindings),
                )

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
            snap_conns = dict(self._connections)
            snap_bindings = dict(self._bindings)
            self._bindings[binding.binding_id] = binding
            result = binding.to_public_dict()
            if self._state_path is not None:
                self._persist_with_rollback(
                    snap_conns, snap_bindings,
                    lambda: self._rollback_conn_binding(snap_conns, snap_bindings),
                )
            return result

    def delete_binding(self, binding_id: str) -> None:
        with self._lock:
            if binding_id not in self._bindings:
                raise KeyError(f"binding not found: {binding_id}")
            snap_conns = dict(self._connections)
            snap_bindings = dict(self._bindings)
            del self._bindings[binding_id]
            if self._state_path is not None:
                self._persist_with_rollback(
                    snap_conns, snap_bindings,
                    lambda: self._rollback_conn_binding(snap_conns, snap_bindings),
                )

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

    # ------------------------------------------------------------------
    # Persistence internals.  Called only under self._lock when
    # self._state_path is not None.
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        if self._state_path is None:
            return
        if not self._state_path.exists():
            return
        try:
            raw = self._state_path.read_bytes()
        except OSError as exc:
            raise StoreError(f"cannot read state file: {exc}") from exc

        data = self._parse_state_doc(raw)

        conn_by_id: dict[str, _StoredConnection] = {}
        for entry in data["connections"]:
            stored = _StoredConnection.from_sanitized_dict(entry)
            cid = stored.connection.connection_id
            if cid in conn_by_id:
                raise StoreError(f"duplicate connection_id in state: {cid}")
            conn_by_id[cid] = stored
            self._connections[cid] = stored

        seen_bindings: set[str] = set()
        for entry in data["bindings"]:
            if not isinstance(entry, dict):
                raise StoreError("invalid binding record: not an object")
            extra = set(entry.keys()) - _BINDING_SAFE_FIELDS
            if extra:
                forbidden_hits = extra & _FORBIDDEN_PERSISTED_FIELDS
                if forbidden_hits:
                    raise StoreError(
                        f"forbidden field(s) in persisted binding: "
                        f"{sorted(forbidden_hits)}"
                    )
                raise StoreError(
                    f"unknown field(s) in persisted binding: {sorted(extra)}"
                )
            binding = Binding.from_mapping(dict(entry))
            if binding.binding_id in seen_bindings:
                raise StoreError(
                    f"duplicate binding_id in state: {binding.binding_id}"
                )
            seen_bindings.add(binding.binding_id)
            if binding.connection_id not in conn_by_id:
                raise StoreError(
                    f"dangling binding references unknown connection: "
                    f"{binding.binding_id} -> {binding.connection_id}"
                )
            if binding.executor_id not in self._executors:
                raise StoreError(
                    f"binding references unknown executor: {binding.executor_id}"
                )
            self._bindings[binding.binding_id] = binding

    def _parse_state_doc(self, raw: bytes) -> dict[str, Any]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StoreError(f"invalid JSON in state file: {exc}") from exc
        if not isinstance(data, dict):
            raise StoreError("state file root must be an object")
        if data.get("schema_version") != _STATE_SCHEMA_VERSION:
            raise StoreError(
                f"unsupported schema_version: {data.get('schema_version')}"
            )
        connections = data.get("connections", [])
        bindings = data.get("bindings", [])
        if not isinstance(connections, list):
            raise StoreError("connections must be an array")
        if not isinstance(bindings, list):
            raise StoreError("bindings must be an array")
        for item in connections:
            if not isinstance(item, dict):
                raise StoreError("each connection entry must be an object")
            extra = set(item.keys()) - _CONNECTION_SAFE_FIELDS
            forbidden_hits = extra & _FORBIDDEN_PERSISTED_FIELDS
            if forbidden_hits:
                raise StoreError(
                    f"forbidden field(s) in persisted connection: "
                    f"{sorted(forbidden_hits)}"
                )
            if extra - forbidden_hits:
                raise StoreError(
                    f"unknown field(s) in persisted connection: "
                    f"{sorted(extra - forbidden_hits)}"
                )
            for fld in ("connection_id", "name", "provider",
                        "base_url", "auth_method"):
                if fld not in item:
                    raise StoreError(f"missing required connection field: {fld}")
            enabled = item.get("enabled", True)
            if not isinstance(enabled, bool):
                raise StoreError("connection.enabled must be a boolean")
        for item in bindings:
            if not isinstance(item, dict):
                raise StoreError("each binding entry must be an object")
            extra = set(item.keys()) - _BINDING_SAFE_FIELDS
            forbidden_hits = extra & _FORBIDDEN_PERSISTED_FIELDS
            if forbidden_hits:
                raise StoreError(
                    f"forbidden field(s) in persisted binding: "
                    f"{sorted(forbidden_hits)}"
                )
            if extra - forbidden_hits:
                raise StoreError(
                    f"unknown field(s) in persisted binding: "
                    f"{sorted(extra - forbidden_hits)}"
                )
            for fld in ("binding_id", "name", "executor_id",
                        "connection_id", "model_id"):
                if fld not in item:
                    raise StoreError(f"missing required binding field: {fld}")
            enabled = item.get("enabled", True)
            if not isinstance(enabled, bool):
                raise StoreError("binding.enabled must be a boolean")
        return data

    def _build_state_doc(self) -> bytes:
        connections = [
            stored.sanitized_dict() for stored in self._connections.values()
        ]
        bindings = [b.to_public_dict() for b in self._bindings.values()]
        doc = {
            "schema_version": _STATE_SCHEMA_VERSION,
            "connections": connections,
            "bindings": bindings,
        }
        return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    def _persist_with_rollback(
        self,
        snap_conns: dict[str, _StoredConnection],
        snap_bindings: dict[str, Binding],
        rollback_fn,
    ) -> None:
        try:
            data = self._build_state_doc()
            _write_atomic(data, self._state_path)
        except Exception as exc:
            rollback_fn()
            if isinstance(exc, StoreError):
                raise
            raise StoreError(f"persistence failed: {exc}") from exc

    def _rollback_conn_binding(
        self,
        snap_conns: dict[str, _StoredConnection],
        snap_bindings: dict[str, Binding],
    ) -> None:
        self._connections.clear()
        self._connections.update(snap_conns)
        self._bindings.clear()
        self._bindings.update(snap_bindings)

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


def _reject_derived_external_status(payload: Mapping[str, Any]) -> None:
    if "external_session_status" in payload:
        raise ValueError("external_session_status is a runtime value and is not accepted")
    if "externalSessionStatus" in payload:
        raise ValueError("externalSessionStatus is a runtime value and is not accepted")


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
