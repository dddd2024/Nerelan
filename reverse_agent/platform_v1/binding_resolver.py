"""Secret-free Binding to OpenCode launch metadata resolver.

The resolver consumes only the public Task 3A GET contracts over a trusted
loopback connection.  It never asks Model Control for credential material and
rejects any secret-bearing field that appears unexpectedly.
"""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPConnection, HTTPSConnection
from ipaddress import ip_address
import json
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlsplit

from .task_runtime import ExecutorRuntimeError


DEFAULT_MODEL_CONTROL_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT_SECONDS = 3.0
DEFAULT_MAX_RESPONSE_BYTES = 64 * 1024

_SAFE_PUBLIC_STATUS_KEYS = {
    "secretstatus",
    "externalsessionstatus",
}

_SECRET_KEYS = {
    "apikey",
    "password",
    "secretkey",
    "credential",
    "credentials",
    "cookie",
    "authorization",
    "privatekey",
}

_SECRET_KEY_SUFFIXES = ("token", "secret")

Transport = Callable[[str, float, int], tuple[int, Any]]


class BindingResolutionError(ExecutorRuntimeError):
    """Finite, sanitized failure raised before OpenCode process launch."""


@dataclass(frozen=True, slots=True)
class OpenCodeBindingResolution:
    binding_ref: str
    connection_id: str
    executor_id: str
    provider_id: str
    model_id: str
    base_url: str
    auth_method: str
    external_session_status: str


class BindingResolver:
    def __init__(
        self,
        base_url: str = DEFAULT_MODEL_CONTROL_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = _validate_loopback_base_url(base_url)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 30:
            raise BindingResolutionError("model_control_timeout_invalid")
        if (
            not isinstance(max_response_bytes, int)
            or max_response_bytes <= 0
            or max_response_bytes > 1024 * 1024
        ):
            raise BindingResolutionError("model_control_response_limit_invalid")
        self._timeout = float(timeout)
        self._max_response_bytes = max_response_bytes
        self._transport = transport or _http_get_json

    def resolve(
        self,
        binding_ref: str,
        *,
        task_executor: str,
    ) -> OpenCodeBindingResolution:
        binding_id = _required_text(binding_ref, "binding_ref", maximum=200)
        if task_executor != "opencode":
            raise BindingResolutionError("binding_requires_opencode_executor")

        binding = self._get_object("binding", "/api/bindings", binding_id)
        if binding.get("enabled") is not True:
            raise BindingResolutionError("binding_disabled")
        if binding.get("binding_id") != binding_id:
            raise BindingResolutionError("binding_identity_mismatch")
        executor_id = _required_text(
            binding.get("executor_id"), "binding_executor_id", maximum=80
        )
        if executor_id != task_executor:
            raise BindingResolutionError("binding_executor_mismatch")
        connection_id = _required_text(
            binding.get("connection_id"), "binding_connection_id", maximum=80
        )

        connection = self._get_object(
            "connection", "/api/connections", connection_id
        )
        if connection.get("enabled") is not True:
            raise BindingResolutionError("connection_disabled")
        if connection.get("connection_id") != connection_id:
            raise BindingResolutionError("connection_identity_mismatch")

        executor = self._get_object("executor", "/api/executors", executor_id)
        if executor.get("executor_id") != executor_id:
            raise BindingResolutionError("executor_identity_mismatch")
        if executor.get("operational") is not True:
            raise BindingResolutionError("executor_not_operational")

        provider_id = _required_text(
            connection.get("provider"), "connection_provider", maximum=80
        )
        raw_model_id = _required_text(
            binding.get("model_id"), "binding_model_id", maximum=200
        )
        model_id = _normalize_model_id(provider_id, raw_model_id)
        base_url = _validate_provider_base_url(connection.get("base_url"))

        auth_method = _required_text(
            connection.get("auth_method"), "connection_auth_method", maximum=40
        )
        external_session_status = _required_text(
            connection.get("external_session_status"),
            "external_session_status",
            maximum=40,
        )
        if auth_method == "api_key":
            raise BindingResolutionError("auth_method_api_key_forbidden")
        if auth_method in {"external_cli_session", "account_login"}:
            if external_session_status != "available":
                raise BindingResolutionError("external_session_unavailable")
        elif auth_method != "none":
            raise BindingResolutionError("auth_method_unsupported")

        return OpenCodeBindingResolution(
            binding_ref=binding_id,
            connection_id=connection_id,
            executor_id=executor_id,
            provider_id=provider_id,
            model_id=model_id,
            base_url=base_url,
            auth_method=auth_method,
            external_session_status=external_session_status,
        )

    def _get_object(self, kind: str, route: str, identifier: str) -> Mapping[str, Any]:
        url = f"{self._base_url}{route}/{quote(identifier, safe='')}"
        try:
            status, payload = self._transport(
                url, self._timeout, self._max_response_bytes
            )
        except BindingResolutionError:
            raise
        except Exception as exc:
            raise BindingResolutionError("model_control_unavailable") from exc
        if status == 404:
            raise BindingResolutionError(f"{kind}_not_found")
        if status != 200:
            raise BindingResolutionError(f"{kind}_fetch_failed")
        if not isinstance(payload, Mapping):
            raise BindingResolutionError(f"{kind}_response_not_object")
        _reject_secret_material(payload)
        return payload


def _validate_loopback_base_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BindingResolutionError("model_control_url_invalid")
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BindingResolutionError("model_control_url_invalid")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise BindingResolutionError("model_control_url_invalid")
    if parsed.path not in {"", "/"}:
        raise BindingResolutionError("model_control_url_invalid")
    host = parsed.hostname.casefold()
    if host != "localhost":
        try:
            address = ip_address(host)
        except ValueError as exc:
            raise BindingResolutionError("model_control_not_loopback") from exc
        if address not in {ip_address("127.0.0.1"), ip_address("::1")}:
            raise BindingResolutionError("model_control_not_loopback")
    return normalized


def _http_get_json(url: str, timeout: float, max_response_bytes: int) -> tuple[int, Any]:
    parsed = urlsplit(url)
    if parsed.scheme == "https":
        connection: HTTPConnection = HTTPSConnection(
            parsed.hostname, parsed.port, timeout=timeout
        )
    else:
        connection = HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
    path = parsed.path or "/"
    try:
        connection.request("GET", path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        status = int(response.status)
        raw = response.read(max_response_bytes + 1)
    except BindingResolutionError:
        raise
    except Exception as exc:
        raise BindingResolutionError("model_control_unavailable") from exc
    finally:
        connection.close()
    if len(raw) > max_response_bytes:
        raise BindingResolutionError("model_control_response_too_large")
    if status != 200:
        return status, None
    try:
        return status, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BindingResolutionError("model_control_invalid_json") from exc


def _reject_secret_material(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).replace("_", "").replace("-", "").casefold()
            if normalized not in _SAFE_PUBLIC_STATUS_KEYS and (
                normalized in _SECRET_KEYS
                or normalized.endswith(_SECRET_KEY_SUFFIXES)
            ):
                raise BindingResolutionError("secret_material_rejected")
            _reject_secret_material(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_secret_material(nested)


def _required_text(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BindingResolutionError(f"{field}_invalid")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise BindingResolutionError(f"{field}_invalid")
    return normalized


def _normalize_model_id(provider_id: str, model_id: str) -> str:
    if "/" not in model_id:
        return f"{provider_id}/{model_id}"
    prefix, suffix = model_id.split("/", 1)
    if prefix != provider_id:
        raise BindingResolutionError("model_provider_mismatch")
    if not suffix:
        raise BindingResolutionError("binding_model_id_invalid")
    return model_id


def _validate_provider_base_url(value: Any) -> str:
    normalized = _required_text(value, "connection_base_url", maximum=2048).rstrip(
        "/"
    )
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise BindingResolutionError("connection_base_url_invalid")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise BindingResolutionError("connection_base_url_invalid")
    return normalized
