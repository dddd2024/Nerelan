"""Idempotently install the single bounded synthetic-audit executor key."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

_BASE_URL = "http://litellm:4000"
_KEY_FILE = Path("/run/secrets/litellm_executor_key")
_POLICY = {
    "key_alias": "unattended-v0-synthetic-audit",
    "models": ["unattended-v0"],
    "max_budget": 1.0,
    "budget_duration": "1d",
    "rpm_limit": 10,
    "tpm_limit": 50000,
    "max_parallel_requests": 1,
    "allowed_routes": [
        "/v1/chat/completions",
        "/chat/completions",
        "/v1/models",
    ],
    "key_type": "llm_api",
    "metadata": {"purpose": "unattended-v0-synthetic-audit"},
}


def _request(
    method: str,
    path: str,
    *,
    bearer: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer}",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(
        f"{_BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=30) as response:
        decoded = json.loads(response.read())
        if not isinstance(decoded, dict):
            raise RuntimeError("unexpected_litellm_response")
        return decoded


def main() -> int:
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    if not master_key or not _KEY_FILE.is_file() or _KEY_FILE.is_symlink():
        return 1
    executor_key = _KEY_FILE.read_text(encoding="utf-8").strip()
    if (
        not executor_key.startswith("sk-")
        or len(executor_key) < 20
        or any(character.isspace() for character in executor_key)
    ):
        return 1

    create = dict(_POLICY)
    create["key"] = executor_key
    try:
        _request("POST", "/key/generate", bearer=master_key, payload=create)
    except HTTPError as error:
        if error.code not in {400, 409}:
            raise

    update = dict(_POLICY)
    update["key"] = executor_key
    result = _request(
        "POST",
        "/key/update",
        bearer=master_key,
        payload=update,
    )
    expected = {
        "models": ["unattended-v0"],
        "max_budget": 1.0,
        "rpm_limit": 10,
        "tpm_limit": 50000,
        "max_parallel_requests": 1,
        "allowed_routes": [
            "/v1/chat/completions",
            "/chat/completions",
            "/v1/models",
        ],
        "key_type": "llm_api",
    }
    if any(result.get(name) != value for name, value in expected.items()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
