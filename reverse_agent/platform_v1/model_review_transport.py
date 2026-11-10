"""Single-request tool-less review.

Two transports, one request shape and one set of answer checks:

- an API-key connection goes through an execution-scoped host relay lease, so the
  key never leaves the host;
- a keyless gateway on this machine (a loopback ``http`` base URL with
  ``auth_method: none``, such as Magpie) is called directly: there is no credential
  to lease, and its accounts stay inside the gateway.

This module accepts only prompt text and connection identity, never a workspace.
"""
import json
from urllib.parse import urlsplit
from urllib.request import Request
from urllib.error import URLError

from ..model_access.http_safe import urlopen
from ..model_access.credential_relay import _normalize_model_id
from .run_store import TaskStoreError
from .task_runtime import ExecutorRuntimeError

TIMEOUT_SECONDS = 60
MAX_RESPONSE_BYTES = 512 * 1024


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def keyless_gateway(resolution):
    """True for a keyless OpenCode connection whose base URL is plain http on this machine."""
    if (resolution.executor_id != "opencode" or resolution.auth_method != "none"
            or getattr(resolution, "relay_required", False)
            or getattr(resolution, "native_endpoint", "") != "/chat/completions"):
        return False
    base_url = getattr(resolution, "base_url", "")
    if not isinstance(base_url, str) or not base_url:
        return False
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        return False
    return (parsed.scheme == "http" and parsed.hostname in _LOOPBACK_HOSTS and port is not None
            and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment)


def validate_connection(resolution, lease_provider):
    if keyless_gateway(resolution):
        return
    if (resolution.executor_id != "opencode" or resolution.auth_method != "api_key"
            or not resolution.relay_required
            or getattr(resolution, "native_endpoint", "") != "/chat/completions"
            or not callable(lease_provider)):
        raise TaskStoreError("model_review_connection_unsupported")


def chat(lease, body):
    return _post(lease.relay_url, body, {"Authorization": "Bearer " + lease.lease_id})


def gateway_chat(base_url, body):
    """One request to a keyless loopback gateway; no credential is sent."""
    return _post(base_url, body, {})


def _post(base_url, body, headers):
    request = Request(base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise TaskStoreError("model_review_invalid_output")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def review(prompt, resolution, lease_provider):
    validate_connection(resolution, lease_provider)
    lease = None
    try:
        if keyless_gateway(resolution):
            # The binding's model id is the gateway's own id under the connection's provider prefix.
            prefix = resolution.provider_id + "/"
            model = (resolution.model_id[len(prefix):] if resolution.model_id.startswith(prefix)
                     else resolution.model_id)
            if not model or _normalize_model_id(resolution.provider_id, model) != resolution.model_id:
                raise TaskStoreError("review_not_independent")
            payload = gateway_chat(resolution.base_url, {"model": model, "stream": False, "max_tokens": 8192,
                "messages": [{"role": "user", "content": prompt}]})
        else:
            lease = lease_provider(resolution)
            lease.bind_execution_deadline(TIMEOUT_SECONDS)
            prefix = "reverse-agent-relay/"
            if not lease.model_id.startswith(prefix):
                raise TaskStoreError("review_not_independent")
            model = lease.model_id[len(prefix):]
            if _normalize_model_id(resolution.provider_id, model) != resolution.model_id:
                raise TaskStoreError("review_not_independent")
            payload = chat(lease, {"model": model, "messages": [{"role": "user", "content": prompt}],
                "stream": False, "max_tokens": 8192})
        if not isinstance(payload, dict):
            raise TaskStoreError("model_review_invalid_output")
        actual = payload.get("model")
        if (not isinstance(actual, str) or not actual.strip()
                or _normalize_model_id(resolution.provider_id, actual) != resolution.model_id):
            raise TaskStoreError("review_not_independent")
        choices = payload.get("choices")
        if not isinstance(choices, list) or len(choices) != 1:
            raise TaskStoreError("model_review_invalid_output")
        choice = choices[0]
        message = choice["message"]
        if (choice.get("finish_reason") != "stop" or message.get("role") != "assistant"
                or message.get("tool_calls") or message.get("function_call")
                or payload.get("tool_calls") or payload.get("function_call")):
            raise TaskStoreError("model_review_invalid_output")
        from .model_review import parse_response
        text = message.get("content")
        parse_response(text)
        request_id = payload.get("id")
        if not isinstance(request_id, str) or not request_id.strip():
            raise TaskStoreError("model_review_invalid_output")
        return {"response": text, "actual_models": [resolution.model_id], "request_id": request_id,
                "quota_observations": []}
    except (TaskStoreError, ExecutorRuntimeError):
        raise
    except TimeoutError as exc:
        raise TaskStoreError("timeout") from exc
    except URLError as exc:
        reason = "timeout" if isinstance(exc.reason, TimeoutError) else "transport_error"
        raise TaskStoreError(reason) from exc
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        raise TaskStoreError("model_review_invalid_output") from exc
    except Exception as exc:
        raise TaskStoreError("transport_error") from exc
    finally:
        if lease is not None:
            lease.release()
