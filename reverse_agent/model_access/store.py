"""In-memory model profile and secret store for a trusted host."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import errno
import json
import os
import re
from threading import RLock
from typing import Any, Mapping
import tempfile

from .contracts import (
    AGENT_ROLES,
    NATIVE_CLI_PROVIDER_FOR_EXECUTOR,
    NATIVE_CLI_PROVIDERS,
    Binding,
    Connection,
    ExecutionSnapshot,
    ExecutorDescriptor,
    ModelProfile,
    anthropic_endpoint,
    is_anthropic_relay_connection,
)
from .os_vault import (
    VaultAdapter,
    VaultItemMissingError,
    connection_vault_ref,
)
from .provider_identity import identity_authority_changed


# Schema version for persisted sanitized product setup state.
_STATE_SCHEMA_VERSION = 2
_LEGACY_STATE_SCHEMA_VERSION = 1

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

# Sanitized connection fields that are safe to persist. ``credential_ref`` is
# a non-secret vault item reference; the referenced secret stays in the OS
# credential store and never enters persisted state. Schema v1 stored the
# overloaded ``provider`` token; schema v2 stores the three explicit identity
# axes and never treats ``provider`` as a second source of authority.
_CONNECTION_SAFE_FIELDS_V1 = frozenset({
    "connection_id",
    "name",
    "provider",
    "base_url",
    "auth_method",
    "enabled",
    "api_key_env",
    "credential_ref",
})
_CONNECTION_SAFE_FIELDS_V2 = frozenset({
    "connection_id",
    "anthropic_base_url",
    "name",
    "upstream_provider_id",
    "protocol_family",
    "executor_provider_id",
    "base_url",
    "auth_method",
    "enabled",
    "api_key_env",
    "credential_ref",
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


class _PostReplaceDurabilityUncertainError(StoreError):
    """Raised when replace succeeded but directory durability is uncertain."""


_KNOWN_UNSUPPORTED_DIR_FSYNC_ERRNOS = frozenset(
    err
    for err in (
        getattr(errno, "EINVAL", None),
        getattr(errno, "ENOTSUP", None),
        getattr(errno, "EOPNOTSUPP", None),
        getattr(errno, "ENOSYS", None),
    )
    if err is not None
)


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


def _sanitize_credential_ref(value: Any) -> str | None:
    """Validate a persisted non-secret vault reference.

    The reference must match the store-owned namespace format. It is metadata
    only; the referenced secret stays in the OS credential store.
    """

    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("credential_ref must be a string or absent")
    normalized = value.strip()
    if len(normalized) > 240:
        raise ValueError("credential_ref exceeds maximum length")
    parts = normalized.split(":")
    if (
        len(parts) != 5
        or parts[0] != "nerelan"
        or parts[1] != "conn"
        or parts[2] != "v1"
        or not parts[3]
        or len(parts[4]) != 16
        or not all(char in "0123456789abcdef" for char in parts[4])
    ):
        raise ValueError("credential_ref is not a valid vault reference")
    return normalized


def _sanitize_agent_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """The Owner's preference sentence, the interpreter's explanation and exclusions; text only."""
    text = policy.get("text", "")
    explanation = policy.get("explanation", "")
    excluded = policy.get("excluded", [])
    return {
        "text": text[:2000] if isinstance(text, str) else "",
        "explanation": explanation[:1000] if isinstance(explanation, str) else "",
        "excluded": [item for item in excluded if isinstance(item, str)][:50] if isinstance(excluded, list) else [],
    }


STANDIN_ROLES = ("simple", "coder", "complex")


def _sanitize_standins(raw: Mapping[str, Any]) -> dict[str, list[str]]:
    """Coding role -> up to 4 binding ids, in the Owner's order of preference."""
    return {role: list(dict.fromkeys(b for b in ids if isinstance(b, str) and b))[:4]
            for role, ids in raw.items() if role in STANDIN_ROLES and isinstance(ids, list)
            and any(isinstance(b, str) and b for b in ids)}


def _write_atomic(data: bytes, target: Path) -> None:
    parent = target.parent
    os.makedirs(parent, exist_ok=True)
    fd = None
    tmp_path = None
    replaced = False
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
        replaced = True
        _fsync_parent_directory(target.parent)
    except OSError as exc:
        if replaced:
            raise _PostReplaceDurabilityUncertainError(
                f"POST_REPLACE_DURABILITY_UNCERTAIN: {exc}"
            ) from exc
        raise
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


def _fsync_parent_directory(parent: Path) -> None:
    if _is_windows_platform():
        return
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    dir_fd = None
    try:
        dir_fd = os.open(str(parent), flags)
        os.fsync(dir_fd)
    except OSError as exc:
        if exc.errno in _KNOWN_UNSUPPORTED_DIR_FSYNC_ERRNOS:
            return
        raise
    finally:
        if dir_fd is not None:
            os.close(dir_fd)


def _is_windows_platform() -> bool:
    return os.name == "nt"


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
    credential_ref: str | None = None
    external_session_status: str = "not_applicable"

    @property
    def credential_configured(self) -> bool:
        return (
            self.connection.auth_method == "api_key"
            and bool(self.api_key or self.api_key_env or self.credential_ref)
        )

    @property
    def secret_status(self) -> str:
        if self.connection.auth_method != "api_key":
            return "not_applicable"
        if self.credential_ref:
            # A durable reference exists; its live availability is resolved
            # by the owning store (vault-backed status). Without a live vault
            # probe the state is degraded, never fabricated as missing.
            return "store_locked"
        if self.api_key:
            return "session"
        if self.api_key_env and os.environ.get(self.api_key_env) is not None:
            return "environment"
        return "missing"

    def public(self, secret_status: str | None = None) -> dict[str, Any]:
        return self.connection.to_public_dict(
            credential_configured=self.credential_configured,
            secret_status=secret_status if secret_status is not None else self.secret_status,
            external_session_status=self.external_session_status,
        )

    def sanitized_dict(self) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "connection_id": self.connection.connection_id,
            "name": self.connection.name,
            "upstream_provider_id": self.connection.upstream_provider_id,
            "protocol_family": self.connection.protocol_family,
            "executor_provider_id": self.connection.executor_provider_id,
            "base_url": self.connection.base_url,
            "auth_method": self.connection.auth_method,
            "enabled": self.connection.enabled,
        }
        if self.connection.anthropic_base_url:
            entry["anthropic_base_url"] = self.connection.anthropic_base_url
        if self.api_key_env:
            entry["api_key_env"] = self.api_key_env
        if self.credential_ref:
            entry["credential_ref"] = self.credential_ref
        return entry

    @classmethod
    def from_sanitized_dict(
        cls,
        data: Mapping[str, Any],
        *,
        schema_version: int,
    ) -> "_StoredConnection":
        if not isinstance(data, dict):
            raise ValueError("invalid connection record: not an object")
        if schema_version == _LEGACY_STATE_SCHEMA_VERSION:
            safe_fields = _CONNECTION_SAFE_FIELDS_V1
        elif schema_version == _STATE_SCHEMA_VERSION:
            safe_fields = _CONNECTION_SAFE_FIELDS_V2
        else:
            raise ValueError(f"unsupported schema_version: {schema_version}")
        extra = set(data.keys()) - safe_fields
        if extra:
            raise ValueError(
                f"forbidden field(s) in persisted connection: {sorted(extra)}"
            )
        api_key_env = _sanitize_env_name(data.get("api_key_env"))
        credential_ref = _sanitize_credential_ref(data.get("credential_ref"))
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
            credential_ref=credential_ref,
            external_session_status=initial_status,
        )


class ModelProfileStore:
    """Profile store with optional durable sanitized metadata persistence.

    When ``state_path`` is None (default) the store is purely process-local
    and backward compatible with all existing callers.  When a path is
    provided the store persists a schema-versioned JSON document containing
    only sanitized Connection/Binding metadata.  Raw secrets, credentials,
    and session tokens are never written.

    Schema-v1 sanitized state remains readable. Loading v1 is read-only; the
    next ordinary product-state persistence writes deterministic schema v2 with
    the explicit provider identity axes. Existing non-secret ``credential_ref``
    metadata is carried forward byte-for-byte and no vault item is touched just
    to migrate sanitized metadata.

    When ``vault`` is provided, API keys entered through the trusted setup
    boundary are durably stored in the OS-backed credential vault and the
    sanitized state persists only the non-secret ``credential_ref``. Without
    a vault the store keeps its exact legacy process-local behavior; there
    is never a plaintext fallback for durable storage.
    """

    def __init__(
        self,
        state_path: str | Path | None = None,
        *,
        vault: VaultAdapter | None = None,
    ) -> None:
        self._state_path: Path | None = None
        if state_path is not None:
            self._state_path = Path(state_path).resolve()
        self._vault: VaultAdapter | None = vault

        self._profiles: dict[str, _StoredProfile] = {}
        self._connections: dict[str, _StoredConnection] = {}
        self._executors = {
            "opencode": ExecutorDescriptor(
                executor_id="opencode",
                name="OpenCode",
                operational=True,
                capabilities=("model_selection", "workspace_execution"),
            ),
            "codex": ExecutorDescriptor(
                executor_id="codex", name="Codex", operational=False,
                capabilities=("model_selection", "workspace_execution", "single_mode"),
                readiness_status="not_probed",
            ),
            "claude_code": ExecutorDescriptor(
                executor_id="claude_code", name="Claude Code", operational=False,
                capabilities=("model_selection", "workspace_execution", "single_mode"),
                readiness_status="not_probed",
            ),
        }
        self._bindings: dict[str, Binding] = {}
        self._routing_catalogs: dict[str, Any] = {}
        self._agent_roster: dict[str, str] = {}
        self._agent_pins: set[str] = set()
        self._agent_policy: dict[str, Any] = {}
        # Owner-declared stand-ins per coding role, used only when the role's account is exhausted.
        self._agent_standins: dict[str, list[str]] = {}
        self._lock = RLock()
        self._connection_binding_poison: StoreError | None = None

        if self._state_path is not None:
            self._load_from_disk()
            try:
                self._load_agent_roster()
            except StoreError:
                # A damaged roster never blocks connections/bindings; roles start unfilled.
                self._agent_roster = {}
            try:
                catalogs = json.loads(self._state_path.with_name("model_catalog_observations.json").read_text(encoding="utf-8"))
                if isinstance(catalogs, dict):
                    for connection_id, catalog in catalogs.items():
                        if isinstance(catalog, dict) and connection_id in self._connections:
                            self.record_model_catalog(connection_id, catalog.get("models", []), catalog.get("metadata", {}), persist=False)
            except (OSError, ValueError, TypeError):
                self._routing_catalogs = {}

    def record_model_catalog(self, connection_id: str, models: list[str], metadata: Mapping[str, Any], *, persist: bool = True) -> None:
        """Save sanitized listing observations, never entitlement or credentials."""
        from .magpie import parse_models
        if not isinstance(models, list) or len(models) > 300 or any(not isinstance(m, str) or not m or len(m) > 200 for m in models):
            raise ValueError("invalid_routing_catalog")
        if not isinstance(metadata, Mapping):
            raise ValueError("invalid_routing_catalog")
        normalized = {}
        for model in models:
            raw = metadata.get(model, {})
            if isinstance(raw, Mapping):
                parsed = parse_models({"object": "list", "data": [{**raw, "id": model}]})
                if parsed:
                    normalized[model] = parsed[0]
        with self._lock:
            if connection_id not in self._connections:
                raise ValueError("routing_catalog_unknown_connection")
            self._routing_catalogs[connection_id] = {"status": "discovered", "models": list(dict.fromkeys(models)), "metadata": normalized}
            if persist and self._state_path:
                _write_atomic(json.dumps(self._routing_catalogs, allow_nan=False).encode("utf-8"),
                              self._state_path.with_name("model_catalog_observations.json"))

    def _connection_secret_status(self, stored: _StoredConnection) -> str:
        """Compute the live public secret status for one Connection.

        Vault-backed references probe the OS credential store so a locked or
        missing item is reported explicitly instead of being fabricated as
        ``missing``. Probing never returns the secret itself.
        """

        if stored.connection.auth_method != "api_key":
            return "not_applicable"
        if stored.credential_ref:
            if self._vault is None:
                return "store_locked"
            probe_state = self._vault.probe(stored.credential_ref)
            if probe_state == "available":
                return "stored"
            if probe_state == "locked":
                return "store_locked"
            return "replacement_required"
        if stored.api_key:
            return "session"
        if stored.api_key_env and os.environ.get(stored.api_key_env) is not None:
            return "environment"
        return "missing"

    def _ensure_connection_binding_ready(self) -> None:
        if self._connection_binding_poison is not None:
            raise StoreError(str(self._connection_binding_poison))

    def _fail_closed_on_reconciliation_error(self, exc: Exception) -> None:
        poisoned = StoreError(f"PERSISTENCE_RECONCILIATION_FAILED: {exc}")
        self._connection_binding_poison = poisoned
        raise poisoned from exc

    def _handle_post_replace_uncertainty(
        self,
        exc: _PostReplaceDurabilityUncertainError,
    ) -> None:
        try:
            self._load_from_disk()
        except Exception as reconcile_exc:
            self._fail_closed_on_reconciliation_error(reconcile_exc)
        raise StoreError(str(exc)) from exc

    def _vault_ref_for(self, connection: Connection) -> str:
        """Return the existing v1 vault-reference relation for a Connection.

        ``provider`` is the compatibility alias for ``executor_provider_id``.
        This slice intentionally does not introduce a new vault-reference
        format or move secret material during sanitized metadata migration.
        """

        return connection_vault_ref(
            connection.connection_id,
            connection.provider,
            connection.base_url,
            connection.auth_method,
        )

    def _vault_secret_snapshot(self, ref: str | None) -> str | None:
        """Read the prior vault value for compensating rollback.

        The value exists only inside the trusted host and is never serialized.
        A missing item is a valid snapshot (``None``); an unavailable vault
        fails closed before any state or vault mutation begins.
        """

        if self._vault is None or not ref:
            return None
        try:
            return self._vault.resolve(ref)
        except VaultItemMissingError:
            return None

    def _commit_connection_transaction(
        self,
        *,
        snap_conns: dict[str, _StoredConnection],
        snap_bindings: dict[str, Binding],
        old_ref: str | None,
        old_secret: str | None,
        write_ref: str | None,
        write_secret: str | None,
        delete_ref: str | None,
    ) -> None:
        """Commit one Connection/vault change with compensating rollback.

        The OS credential store and the sanitized JSON file do not share a
        native transaction.  This method therefore snapshots the prior vault
        value, writes the candidate item, persists sanitized state, and only
        then removes an obsolete item.  Any single failure restores memory,
        disk and vault to the prior committed relation and removes a newly
        created item, closing the post-vault/pre-state failure window.
        """

        new_item_written = False
        persist_attempted = False
        state_written = False
        try:
            if self._vault is not None and write_ref and write_secret is not None:
                self._vault.store(write_ref, write_secret)
                new_item_written = True
            if self._state_path is not None:
                persist_attempted = True
                _write_atomic(self._build_state_doc(), self._state_path)
                state_written = True
            if self._vault is not None and delete_ref:
                self._vault.delete(delete_ref)
        except Exception as exc:
            if isinstance(exc, _PostReplaceDurabilityUncertainError):
                self._handle_post_replace_uncertainty(exc)
            self._rollback_conn_binding(snap_conns, snap_bindings)
            rollback_errors: list[str] = []

            if state_written and self._state_path is not None:
                try:
                    _write_atomic(self._build_state_doc(), self._state_path)
                except Exception:
                    rollback_errors.append("sanitized_state")

            if self._vault is not None:
                try:
                    old_item_may_have_changed = bool(
                        new_item_written
                        or (delete_ref and state_written)
                    )
                    if old_ref and old_item_may_have_changed:
                        if old_secret is None:
                            self._vault.delete(old_ref)
                        else:
                            self._vault.store(old_ref, old_secret)
                    if new_item_written and write_ref and write_ref != old_ref:
                        self._vault.delete(write_ref)
                except Exception:
                    rollback_errors.append("credential_store")

            if rollback_errors:
                raise StoreError(
                    "connection transaction rollback failed: "
                    + ",".join(sorted(set(rollback_errors)))
                ) from exc
            if isinstance(exc, StoreError):
                raise
            if persist_attempted and not state_written:
                raise StoreError(f"persistence failed: {exc}") from exc
            raise

    def list_connections_public(self) -> list[dict[str, Any]]:
        with self._lock:
            self._ensure_connection_binding_ready()
            return [
                stored.public(self._connection_secret_status(stored))
                for stored in self._connections.values()
            ]

    def refresh_external_session_status(
        self,
        authenticated_provider_ids: Mapping[str, str],
    ) -> int:
        """Refresh in-memory external-session status from sanitized auth probe.

        ``authenticated_provider_ids`` is an executor-provider-id -> auth-type
        mapping derived from a fresh, sanitized OpenCode ``auth list`` probe.
        External-session status is intentionally NOT persisted; each fresh
        process must reprove availability from a live probe.

        Only exact executor-provider-ID matches are accepted (no fuzzy matching,
        no display-label guessing). ``api_key`` and ``none`` Connections always
        remain ``not_applicable``.
        """
        provider_set = set(authenticated_provider_ids.keys())
        refreshed = 0
        with self._lock:
            self._ensure_connection_binding_ready()
            for stored in self._connections.values():
                auth_method = stored.connection.auth_method
                if stored.connection.executor_provider_id in NATIVE_CLI_PROVIDERS:
                    # Native CLI readiness is never inferred from OpenCode auth.
                    continue
                if auth_method in {"account_login", "external_cli_session"}:
                    provider = stored.connection.executor_provider_id
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
        self._ensure_connection_binding_ready()
        for stored in self._connections.values():
            if stored.connection.executor_provider_id in NATIVE_CLI_PROVIDERS:
                continue
            if stored.connection.auth_method in {
                "account_login",
                "external_cli_session",
            }:
                return True
        return False

    def get_connection_public(self, connection_id: str) -> dict[str, Any]:
        with self._lock:
            self._ensure_connection_binding_ready()
            stored = self._connections.get(connection_id)
            if stored is None:
                raise KeyError(f"connection not found: {connection_id}")
            return stored.public(self._connection_secret_status(stored))

    def upsert_connection(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        _reject_derived_external_status(payload)
        connection = Connection.from_mapping(payload)
        native = NATIVE_CLI_PROVIDERS.get(connection.executor_provider_id)
        if native is not None and any(
            payload.get(key) for key in ("api_key", "apiKey", "api_key_env", "apiKeyEnv")
        ):
            raise ValueError(f"{native[2]}_credentials_owned_by_cli")
        with self._lock:
            self._ensure_connection_binding_ready()
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
            existing_credential_ref = existing.credential_ref if existing else None
            snap_conns = dict(self._connections)
            snap_bindings = dict(self._bindings)
            write_ref: str | None = None
            write_secret: str | None = None
            delete_ref: str | None = None
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
                new_credential_ref = self._vault_ref_for(connection)
                if clear_secret:
                    delete_ref = existing_credential_ref
                    api_key = None
                    api_key_env = None
                    credential_ref = None
                elif incoming_api_key:
                    if self._vault is not None:
                        write_ref = new_credential_ref
                        write_secret = incoming_api_key
                        if existing_credential_ref != new_credential_ref:
                            delete_ref = existing_credential_ref
                        api_key = None
                        credential_ref = new_credential_ref
                    else:
                        api_key = incoming_api_key
                        credential_ref = None
                    api_key_env = None
                elif incoming_api_key_env:
                    delete_ref = existing_credential_ref
                    api_key = None
                    api_key_env = incoming_api_key_env
                    credential_ref = None
                elif existing is None:
                    api_key = existing_api_key
                    api_key_env = existing_api_key_env
                    credential_ref = existing_credential_ref
                else:
                    api_key = existing_api_key
                    api_key_env = existing_api_key_env
                    credential_ref = existing_credential_ref
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
                if (
                    clear_secret
                    and self._vault is not None
                    and existing_credential_ref
                ):
                    delete_ref = existing_credential_ref
                api_key = None
                api_key_env = None
                credential_ref = None
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

            touches_existing_vault = bool(
                existing_credential_ref
                and (
                    delete_ref
                    or (write_ref and write_ref == existing_credential_ref)
                )
            )
            old_vault_secret = (
                self._vault_secret_snapshot(existing_credential_ref)
                if touches_existing_vault
                else None
            )
            stored = _StoredConnection(
                connection=connection,
                api_key=api_key,
                api_key_env=api_key_env,
                credential_ref=credential_ref,
                external_session_status=external_status,
            )
            native = NATIVE_CLI_PROVIDERS.get(connection.executor_provider_id)
            if native is not None:
                stored.external_session_status = "available" if self._executors[native[2]].operational else "missing"
            self._connections[connection.connection_id] = stored
            self._commit_connection_transaction(
                snap_conns=snap_conns,
                snap_bindings=snap_bindings,
                old_ref=existing_credential_ref,
                old_secret=old_vault_secret,
                write_ref=write_ref,
                write_secret=write_secret,
                delete_ref=delete_ref,
            )
            return stored.public(self._connection_secret_status(stored))

    def delete_connection(self, connection_id: str) -> None:
        with self._lock:
            self._ensure_connection_binding_ready()
            stored = self._connections.get(connection_id)
            if stored is None:
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
            old_vault_secret = self._vault_secret_snapshot(stored.credential_ref)
            del self._connections[connection_id]
            self._commit_connection_transaction(
                snap_conns=snap_conns,
                snap_bindings=snap_bindings,
                old_ref=stored.credential_ref,
                old_secret=old_vault_secret,
                write_ref=None,
                write_secret=None,
                delete_ref=stored.credential_ref,
            )

    def resolve_connection_secret(self, connection_id: str) -> str | None:
        with self._lock:
            self._ensure_connection_binding_ready()
            stored = self._connections.get(connection_id)
            if stored is None:
                raise KeyError(f"connection not found: {connection_id}")
            return self._resolve_stored_secret(stored)

    def _resolve_stored_secret(self, stored: _StoredConnection) -> str | None:
        """Resolve one Connection's secret at point of use (trusted only).

        Vault-backed references resolve through the OS credential store. A
        locked or unavailable vault raises ``VaultUnavailableError`` so the
        caller fails closed; an externally missing item resolves to ``None``
        so existing missing-credential fail-closed paths apply. Only the
        owning Connection's own reference is ever resolved.
        """

        if stored.credential_ref:
            if self._vault is None:
                return None
            try:
                return self._vault.resolve(stored.credential_ref)
            except VaultItemMissingError:
                return None
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
            self._ensure_connection_binding_ready()
            binding = self._bindings.get(binding_id)
            if binding is None:
                raise KeyError(f"binding not found: {binding_id}")
            if binding.connection_id not in self._connections:
                raise KeyError(f"binding references unknown connection")
            stored_conn = self._connections[binding.connection_id]
            conn = stored_conn.connection
            resolved_key: str | None = None
            if conn.auth_method == "api_key":
                # Resolves through the OS vault at point of use. A locked or
                # unavailable vault raises VaultUnavailableError so execution
                # fails closed; there is never a plaintext fallback.
                resolved_key = self._resolve_stored_secret(stored_conn)
            # The same key reaches Claude Code through the connection's Anthropic endpoint.
            relay_anthropic = binding.executor_id == "claude_code" and anthropic_endpoint(conn) is not None
            return ExecutionSnapshot(
                binding_id=binding.binding_id,
                binding_enabled=binding.enabled,
                executor_id=binding.executor_id,
                raw_model_id=binding.model_id,
                connection_id=conn.connection_id,
                connection_enabled=conn.enabled,
                provider=conn.provider,
                base_url=anthropic_endpoint(conn) if relay_anthropic else conn.base_url,
                auth_method=conn.auth_method,
                resolved_api_key=resolved_key,
                external_session_status=stored_conn.external_session_status,
                upstream_provider_id=conn.upstream_provider_id,
                protocol_family="anthropic" if relay_anthropic else conn.protocol_family,
                executor_provider_id=conn.executor_provider_id,
                native_endpoint=self.get_binding_public(binding_id).get("native_endpoint", "/chat/completions"),
            )

    def list_executors_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [executor.to_public_dict() for executor in self._executors.values()]

    def set_codex_readiness(self, status: str) -> None:
        self.set_native_readiness("codex", status)

    def set_native_readiness(self, executor_id: str, status: str) -> None:
        """Trusted process-local probe result; never persisted as account authority."""
        allowed = {"not_probed", "managed_login_ready", "managed_login_unavailable",
                   "cli_unavailable", "cli_incompatible", "probe_output_invalid"}
        provider = NATIVE_CLI_PROVIDER_FOR_EXECUTOR.get(executor_id)
        if provider is None:
            raise ValueError("native_executor_unknown")
        if status not in allowed:
            raise ValueError(f"{executor_id}_readiness_invalid")
        with self._lock:
            current = self._executors[executor_id]
            self._executors[executor_id] = ExecutorDescriptor(
                executor_id=executor_id, name=current.name, operational=status == "managed_login_ready",
                capabilities=current.capabilities, readiness_status=status,
            )
            for stored in self._connections.values():
                if stored.connection.executor_provider_id == provider:
                    stored.external_session_status = "available" if status == "managed_login_ready" else "missing"

    def get_executor_public(self, executor_id: str) -> dict[str, Any]:
        with self._lock:
            executor = self._executors.get(executor_id)
            if executor is None:
                raise KeyError(f"executor not found: {executor_id}")
            return executor.to_public_dict()

    def list_bindings_public(self) -> list[dict[str, Any]]:
        with self._lock:
            self._ensure_connection_binding_ready()
            return [self.get_binding_public(binding.binding_id) for binding in self._bindings.values()]

    def get_binding_public(self, binding_id: str) -> dict[str, Any]:
        with self._lock:
            self._ensure_connection_binding_ready()
            binding = self._bindings.get(binding_id)
            if binding is None:
                raise KeyError(f"binding not found: {binding_id}")
            result = binding.to_public_dict()
            metadata = getattr(self, "_routing_catalogs", {}).get(binding.connection_id, {}).get("metadata", {}).get(binding.model_id, {})
            result["native_endpoint"] = "/responses" if metadata.get("native_endpoints") and all(
                endpoint in {"/responses", "/v1/responses", "responses"} for endpoint in metadata["native_endpoints"]) else "/chat/completions"
            return result

    def upsert_binding(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        binding = Binding.from_mapping(payload)
        with self._lock:
            self._ensure_connection_binding_ready()
            if binding.connection_id not in self._connections:
                raise ValueError(f"unknown connection_id: {binding.connection_id}")
            if binding.executor_id not in self._executors:
                raise ValueError(f"unknown executor_id: {binding.executor_id}")
            connection_provider = self._connections[binding.connection_id].connection.executor_provider_id
            native_provider = NATIVE_CLI_PROVIDER_FOR_EXECUTOR.get(binding.executor_id)
            if native_provider is not None:
                from ..platform_v1.codex_executor import validate_codex_model
                from ..platform_v1.task_runtime import ExecutorRuntimeError
                prefix = binding.executor_id
                try:
                    connection = self._connections[binding.connection_id].connection
                    if binding.executor_id == "claude_code":
                        from ..platform_v1.claude_executor import validate_claude_model
                        validate_claude_model(binding.model_id, relay_mode=is_anthropic_relay_connection(connection))
                    else:
                        validate_codex_model(binding.model_id)
                except ExecutorRuntimeError as exc:
                    raise ValueError(f"{prefix}_model_id_invalid") from exc
                connection = self._connections[binding.connection_id].connection
                upstream = NATIVE_CLI_PROVIDERS[native_provider][0]
                relay_mode = binding.executor_id == "claude_code" and is_anthropic_relay_connection(connection)
                if not relay_mode and (connection.executor_provider_id != native_provider
                        or connection.upstream_provider_id != upstream
                        or connection.auth_method != "external_cli_session"):
                    raise ValueError("codex_requires_openai_managed_connection" if prefix == "codex"
                                     else f"{prefix}_requires_managed_connection")
            elif connection_provider in NATIVE_CLI_PROVIDERS:
                raise ValueError(f"{NATIVE_CLI_PROVIDERS[connection_provider][2]}_connection_requires_native_executor")
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

    def bind_connection_models(self, connection_id: str, model_ids: Any, executor_id: Any) -> dict[str, Any]:
        """Bind many models of one Connection to one executor in a single step.

        Existing (connection, model, executor) bindings are reused, never duplicated or
        overwritten; each new binding still passes every upsert_binding rule.
        """
        if (not isinstance(model_ids, list) or not 1 <= len(model_ids) <= 300
                or any(not isinstance(item, str) or not item.strip() for item in model_ids)):
            raise ValueError("bind_models_model_ids_invalid")
        if not isinstance(executor_id, str) or not executor_id:
            raise ValueError("bind_models_executor_required")
        if executor_id == "auto":
            # Every executor this connection's key can drive: free model x executor combination.
            return self._bind_models_all_executors(connection_id, model_ids)
        with self._lock:
            self._ensure_connection_binding_ready()
            if connection_id not in self._connections:
                raise ValueError(f"unknown connection_id: {connection_id}")
            name = self._connections[connection_id].connection.name
            existing = {(b.model_id, b.executor_id): b.binding_id for b in self._bindings.values()
                        if b.connection_id == connection_id}
            taken = set(self._bindings)
        created, reused = [], []
        for model_id in dict.fromkeys(item.strip() for item in model_ids):
            if (model_id, executor_id) in existing:
                reused.append(existing[(model_id, executor_id)])
                continue
            # Name the executor too when it is not the default, so pairings stay readable.
            label = f"{connection_id}-{model_id}" + ("" if executor_id == "opencode" else f"-{executor_id}")
            stem = re.sub(r"[^a-z0-9._-]+", "-", label.lower()).strip("-.")[:72] or "binding"
            binding_id, suffix = stem, 2
            while binding_id in taken:
                binding_id, suffix = f"{stem[:68]}-{suffix}", suffix + 1
            suffix = "" if executor_id == "opencode" else f" · {executor_id}"
            self.upsert_binding({"binding_id": binding_id, "name": f"{name} · {model_id}{suffix}"[:120],
                                 "connection_id": connection_id, "executor_id": executor_id,
                                 "model_id": model_id, "enabled": True})
            taken.add(binding_id)
            created.append(binding_id)
        return {"created": created, "reused": reused}

    def compatible_executors(self, connection_id: str) -> list[str]:
        with self._lock:
            self._ensure_connection_binding_ready()
            if connection_id not in self._connections:
                raise ValueError(f"unknown connection_id: {connection_id}")
            connection = self._connections[connection_id].connection
        native = NATIVE_CLI_PROVIDERS.get(connection.executor_provider_id)
        if native is not None:
            return [executor for executor, provider in NATIVE_CLI_PROVIDER_FOR_EXECUTOR.items()
                    if provider == connection.executor_provider_id]
        executors = [] if connection.protocol_family == "anthropic" else ["opencode"]
        if anthropic_endpoint(connection) is not None:
            executors.append("claude_code")
        return executors

    def _bind_models_all_executors(self, connection_id: str, model_ids: Any) -> dict[str, Any]:
        created: list[str] = []
        reused: list[str] = []
        executors = self.compatible_executors(connection_id)
        if not executors:
            raise ValueError("bind_models_no_compatible_executor")
        for executor in executors:
            result = self.bind_connection_models(connection_id, model_ids, executor)
            created += result["created"]
            reused += result["reused"]
        return {"created": created, "reused": reused, "executors": executors}

    # ---- multi-agent team roster -------------------------------------------------

    def _roster_path(self) -> Path | None:
        return None if self._state_path is None else self._state_path.with_name("agent_roster.json")

    def _load_agent_roster(self) -> None:
        path = self._roster_path()
        if path is None or not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StoreError(f"invalid agent roster file: {type(exc).__name__}") from exc
        if not isinstance(data, dict):
            raise StoreError("invalid agent roster file")
        roles = data.get("roles")
        if data.get("schema_version") != 1 or not isinstance(roles, dict):
            raise StoreError("invalid agent roster file")
        self._agent_roster = {role: binding for role, binding in roles.items()
                              if role in AGENT_ROLES and isinstance(binding, str) and binding}
        self._agent_pins = {role for role in data.get("pins", []) if role in self._agent_roster}
        policy = data.get("policy")
        self._agent_policy = _sanitize_agent_policy(policy) if isinstance(policy, dict) else {}
        standins = data.get("standins")
        self._agent_standins = _sanitize_standins(standins) if isinstance(standins, dict) else {}

    def get_agent_roster_public(self) -> dict[str, Any]:
        with self._lock:
            self._ensure_connection_binding_ready()
            roles = {}
            for role in AGENT_ROLES:
                binding_id = self._agent_roster.get(role, "")
                binding = self._bindings.get(binding_id)
                roles[role] = {
                    "binding_id": binding_id,
                    **({"pin": True} if role in self._agent_pins else {}),
                    # A deleted or disabled binding leaves the role unfilled, never silently remapped.
                    "available": bool(binding and binding.enabled),
                    "executor_id": binding.executor_id if binding else "",
                    "model_id": binding.model_id if binding else "",
                }
            # A stand-in that was deleted or disabled is simply not offered.
            standins = {role: [b for b in ids if b in self._bindings and self._bindings[b].enabled]
                        for role, ids in self._agent_standins.items()}
            return {"roles": roles, "role_order": list(AGENT_ROLES), "policy": dict(self._agent_policy),
                    "standins": {role: ids for role, ids in standins.items() if ids}}

    def put_agent_roster(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Legacy role hints, or explicit {binding_id, pin: True} task-route pins."""
        roles = payload.get("roles") if isinstance(payload, Mapping) else None
        if not isinstance(roles, Mapping):
            raise ValueError("agent_roster_roles_required")
        with self._lock:
            self._ensure_connection_binding_ready()
            roster: dict[str, str] = {}
            pins: set[str] = set()
            for role, binding_id in roles.items():
                if role not in AGENT_ROLES:
                    raise ValueError(f"unknown_agent_role:{role}")
                if isinstance(binding_id, Mapping):
                    if type(binding_id.get("pin", False)) is not bool:
                        raise ValueError(f"agent_role_pin_invalid:{role}")
                    if binding_id.get("pin"):
                        pins.add(role)
                    binding_id = binding_id.get("binding_id", "")
                elif role in self._agent_pins:
                    pins.add(role)
                if binding_id in (None, ""):
                    continue
                if not isinstance(binding_id, str) or binding_id not in self._bindings:
                    raise ValueError(f"agent_role_binding_unknown:{role}")
                if not self._bindings[binding_id].enabled:
                    raise ValueError(f"agent_role_binding_disabled:{role}")
                roster[role] = binding_id
            pins.intersection_update(roster)
            reviewer, coder = roster.get("reviewer"), roster.get("coder")
            if reviewer and coder and self._bindings[reviewer].model_id == self._bindings[coder].model_id:
                # Independent review needs a different underlying model, not just another label.
                raise ValueError("agent_reviewer_must_differ_from_coder")
            policy_raw = payload.get("policy") if isinstance(payload, Mapping) else None
            policy = _sanitize_agent_policy(policy_raw) if isinstance(policy_raw, Mapping) else {}
            standins = self._agent_standins
            if isinstance(payload, Mapping) and "standins" in payload:
                # Only an explicit edit changes the Owner's stand-ins; a role edit keeps them.
                raw = payload["standins"]
                if not isinstance(raw, Mapping):
                    raise ValueError("agent_standins_invalid")
                standins = _sanitize_standins(raw)
                for role, ids in raw.items():
                    if role not in STANDIN_ROLES:
                        raise ValueError(f"agent_standin_role_invalid:{role}")
                    if not isinstance(ids, list) or any(
                            not isinstance(b, str) or (b and b not in self._bindings) for b in ids):
                        raise ValueError(f"agent_standin_binding_unknown:{role}")
            path = self._roster_path()
            if path is not None:
                document: dict[str, Any] = {"schema_version": 1, "roles": roster}
                if pins:
                    document["pins"] = sorted(pins)
                if policy:
                    document["policy"] = policy
                if standins:
                    document["standins"] = standins
                _write_atomic(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                              .encode("utf-8"), path)
            self._agent_roster = roster
            self._agent_pins = pins
            self._agent_standins = standins
            # A manual role edit drops the stored natural-language policy it no longer reflects.
            self._agent_policy = policy
        return self.get_agent_roster_public()

    def delete_binding(self, binding_id: str) -> None:
        with self._lock:
            self._ensure_connection_binding_ready()
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
        schema_version = int(data["schema_version"])

        # Parse into temporary maps first. A malformed v1/v2 document therefore
        # never leaves a partially replaced in-memory relation behind.
        conn_by_id: dict[str, _StoredConnection] = {}
        for entry in data["connections"]:
            try:
                stored = _StoredConnection.from_sanitized_dict(
                    entry,
                    schema_version=schema_version,
                )
            except ValueError as exc:
                raise StoreError(f"invalid persisted connection: {exc}") from exc
            cid = stored.connection.connection_id
            if cid in conn_by_id:
                raise StoreError(f"duplicate connection_id in state: {cid}")
            conn_by_id[cid] = stored

        binding_by_id: dict[str, Binding] = {}
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
            if binding.binding_id in binding_by_id:
                raise StoreError(
                    f"duplicate binding_id in state: {binding.binding_id}"
                )
            if binding.connection_id not in conn_by_id:
                raise StoreError(
                    f"dangling binding references unknown connection: "
                    f"{binding.binding_id} -> {binding.connection_id}"
                )
            if binding.executor_id not in self._executors:
                raise StoreError(
                    f"binding references unknown executor: {binding.executor_id}"
                )
            binding_by_id[binding.binding_id] = binding

        self._connections.clear()
        self._connections.update(conn_by_id)
        self._bindings.clear()
        self._bindings.update(binding_by_id)

    def _parse_state_doc(self, raw: bytes) -> dict[str, Any]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StoreError(f"invalid JSON in state file: {exc}") from exc
        if not isinstance(data, dict):
            raise StoreError("state file root must be an object")
        schema_version = data.get("schema_version")
        if type(schema_version) is not int:
            raise StoreError(f"unsupported schema_version: {schema_version}")
        if schema_version not in {_LEGACY_STATE_SCHEMA_VERSION, _STATE_SCHEMA_VERSION}:
            raise StoreError(f"unsupported schema_version: {schema_version}")
        connections = data.get("connections", [])
        bindings = data.get("bindings", [])
        if not isinstance(connections, list):
            raise StoreError("connections must be an array")
        if not isinstance(bindings, list):
            raise StoreError("bindings must be an array")

        if schema_version == _LEGACY_STATE_SCHEMA_VERSION:
            safe_connection_fields = _CONNECTION_SAFE_FIELDS_V1
            required_connection_fields = (
                "connection_id",
                "name",
                "provider",
                "base_url",
                "auth_method",
            )
        else:
            safe_connection_fields = _CONNECTION_SAFE_FIELDS_V2
            required_connection_fields = (
                "connection_id",
                "name",
                "upstream_provider_id",
                "protocol_family",
                "executor_provider_id",
                "base_url",
                "auth_method",
            )

        for item in connections:
            if not isinstance(item, dict):
                raise StoreError("each connection entry must be an object")
            extra = set(item.keys()) - safe_connection_fields
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
            for fld in required_connection_fields:
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
                    f"forbidden field(s) in persisted binding: {sorted(forbidden_hits)}"
                )
            if extra - forbidden_hits:
                raise StoreError(
                    f"unknown field(s) in persisted binding: {sorted(extra - forbidden_hits)}"
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
            if isinstance(exc, _PostReplaceDurabilityUncertainError):
                self._handle_post_replace_uncertainty(exc)
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
        identity_authority_changed(
            old.provider_identity,
            new_connection.provider_identity,
        )
        or old.base_url != new_connection.base_url
        or old.auth_method != new_connection.auth_method
        # The Anthropic relay sends the stored key here; a new host needs a new key.
        or new_connection.anthropic_base_url not in (None, old.anthropic_base_url)
    )
