"""Single-request tool-less review over an execution-scoped host relay lease.

This module accepts only prompt text and connection identity, never a workspace.
"""
import json
from urllib.request import Request
from urllib.error import URLError

from ..model_access.http_safe import urlopen
from ..model_access.credential_relay import _normalize_model_id
from .run_store import TaskStoreError
from .task_runtime import ExecutorRuntimeError

TIMEOUT_SECONDS = 60
MAX_RESPONSE_BYTES = 512 * 1024


def validate_connection(resolution, lease_provider):
    if (resolution.executor_id != "opencode" or resolution.auth_method != "api_key"
            or not resolution.relay_required
            or getattr(resolution, "native_endpoint", "") != "/chat/completions"
            or not callable(lease_provider)):
        raise TaskStoreError("model_review_connection_unsupported")


def chat(lease, body):
    request = Request(lease.relay_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + lease.lease_id, "Content-Type": "application/json"})
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
