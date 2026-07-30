"""Sanitized real-container evidence for the fixed Attempt sandbox boundary."""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from .contracts import ExecutionHandle
from .identifiers import executor_id, workspace_id, workspace_path
from .sandbox import (
    FIXED_LAUNCH_SPEC,
    SandboxController,
    SubprocessDockerRunner,
    container_name_for,
)

_PROJECT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,62}\Z")
_WORKFLOW_ID = "unattended:dddd2024/reverse-agent:issue:82:runtime-proof"
_HTTP_CLIENT = r"""
import json
import os
import sys
import urllib.error
import urllib.request

method, path, payload = sys.argv[1:4]
headers = {"Content-Type": "application/json"}
session_key = os.environ.get("SESSION_API_KEY")
if session_key:
    headers["X-Session-API-Key"] = session_key
request = urllib.request.Request(
    "http://127.0.0.1:8000" + path,
    data=payload.encode("utf-8") if payload else None,
    headers=headers,
    method=method,
)
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.load(response)
    result = {"http_ok": True}
    if path.endswith("/execute_bash_command"):
        result["exit_code"] = body.get("exit_code")
    print(json.dumps(result, sort_keys=True))
except Exception:
    print(json.dumps({"http_ok": False}, sort_keys=True))
    raise SystemExit(2)
""".strip()
_LITELLM_CLIENT = r"""
import json
import os
import urllib.request

key = os.environ["UNATTENDED_EXECUTOR_API_KEY"]
request = urllib.request.Request(
    "http://litellm-executor:4000/v1/models",
    headers={"Authorization": "Bearer " + key},
)
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.load(response)
    models = body.get("data", [])
    ok = response.status == 200 and any(
        item.get("id") == "unattended-v0" for item in models
    )
except Exception:
    ok = False
raise SystemExit(0 if ok else 2)
""".strip()
_SETTINGS_ISOLATION_CLIENT = r"""
import json
import urllib.error
import urllib.request

request = urllib.request.Request("http://127.0.0.1:8000/api/settings")
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read(1048577)
        if len(raw) > 1048576:
            raise SystemExit(2)
except urllib.error.HTTPError as error:
    if error.code == 404:
        raise SystemExit(0)
    raw = error.read(1048577)
except Exception:
    raise SystemExit(2)
raise SystemExit(2 if b"SESSION_API_KEY" in raw else 0)
""".strip()

_WORKSPACE_COMMAND = (
    "set -eu; printf synthetic > probe-inside.txt; "
    'test "$(cat probe-inside.txt)" = synthetic'
)
_BOUNDARY_COMMAND = (
    "set -eu; test ! -e /workspace/sibling-attempt; "
    "! touch /workspace/sibling-attempt 2>/dev/null; "
    "! touch /issue81-outside 2>/dev/null"
)
_ENVIRONMENT_COMMAND = r"""
set -eu
test -z "${SESSION_API_KEY+x}"
test -z "${LITELLM_MASTER_KEY+x}"
test -z "${LLM_API_KEY+x}"
test -z "${OPENAI_API_KEY+x}"
test -z "${ANTHROPIC_API_KEY+x}"
test -z "${GITHUB_TOKEN+x}"
test -z "${GH_TOKEN+x}"
test -z "${UNATTENDED_EXECUTOR_API_KEY+x}"
python - <<'PY'
from pathlib import Path

name = b"SESSION_API_KEY"
try:
    pid_one = Path("/proc/1/environ").read_bytes()
except OSError:
    pid_one = b""
if name + b"=" in pid_one:
    raise SystemExit(2)
for root_name in ("/workspace/attempt", "/home/openhands", "/tmp"):
    root = Path(root_name)
    if not root.exists():
        continue
    for candidate in root.rglob("*"):
        try:
            if (
                candidate.is_file()
                and not candidate.is_symlink()
                and candidate.stat().st_size <= 1048576
                and name + b"=" in candidate.read_bytes()
            ):
                raise SystemExit(2)
        except (OSError, PermissionError):
            continue
PY
""".strip()
_DOCKER_COMMAND = (
    "set -eu; test ! -S /var/run/docker.sock; "
    "python - <<'PY'\n"
    "import socket\n"
    "sock = socket.socket(socket.AF_UNIX)\n"
    "try:\n"
    "    sock.connect('/var/run/docker.sock')\n"
    "except OSError:\n"
    "    raise SystemExit(0)\n"
    "raise SystemExit(2)\n"
    "PY"
)
_NETWORK_COMMAND = (
    "python - <<'PY'\n"
    "import socket\n"
    "import urllib.request\n"
    "try:\n"
    "    with urllib.request.urlopen("
    "'http://litellm-executor:4000/health/liveliness', timeout=5) as response:\n"
    "        if response.status != 200:\n"
    "            raise SystemExit(2)\n"
    "except Exception:\n"
    "    raise SystemExit(2)\n"
    "denied = [\n"
    "    ('temporal', 7233),\n"
    "    ('postgresql', 5432),\n"
    "    ('agent-canvas', 3000),\n"
    "    ('host.docker.internal', 80),\n"
    "    ('1.1.1.1', 443),\n"
    "]\n"
    "for host, port in denied:\n"
    "    try:\n"
    "        connection = socket.create_connection((host, port), timeout=1)\n"
    "    except OSError:\n"
    "        continue\n"
    "    connection.close()\n"
    "    raise SystemExit(2)\n"
    "PY"
)


def run_sandbox_boundary_probe(
    *,
    repository_root: Path,
    compose_project: str,
    executor_key_file: Path,
) -> dict[str, Any]:
    """Run a fixed real Attempt probe and return only allowlisted evidence."""

    checks: dict[str, bool] = {}
    exit_codes: dict[str, int] = {}
    error_type: str | None = None
    metadata = None
    cleanup_passed = False

    if _PROJECT_NAME.fullmatch(compose_project) is None:
        return _failure("compose_project_invalid")
    if not executor_key_file.is_absolute() or not executor_key_file.is_file():
        return _failure("executor_key_file_invalid")

    executor_key = executor_key_file.read_text(encoding="utf-8").strip()
    if not executor_key or "\x00" in executor_key:
        return _failure("executor_key_file_invalid")

    workspace_root = (repository_root / ".var" / "unattended").resolve()
    handle = ExecutionHandle(
        workflow_id=_WORKFLOW_ID,
        attempt=1,
        workspace_id=workspace_id(_WORKFLOW_ID),
        executor_id=executor_id(_WORKFLOW_ID, 1),
        started_at="2026-07-29T16:00:00+00:00",
    )
    runner = SubprocessDockerRunner()
    controller = SandboxController(
        runner,
        host_workspace_root=workspace_root,
        executor_network=f"{compose_project}_model-executor",
        workspace_volume=f"{compose_project}_attempt-workspaces",
    )
    try:
        metadata = controller.launch_or_reconcile(handle, FIXED_LAUNCH_SPEC)
        reconciled = controller.launch_or_reconcile(handle, FIXED_LAUNCH_SPEC)
        checks["duplicate_start_reconciled"] = (
            metadata.container_name == reconciled.container_name
        )
        checks["privileged_false"] = not metadata.privileged
        checks["no_new_privileges"] = metadata.no_new_privileges
        checks["read_only_rootfs"] = metadata.read_only_rootfs
        checks["single_attempt_workspace"] = (
            metadata.workspace_destination == "/workspace/attempt"
        )

        checks["alive"] = _wait_for_alive(runner, metadata.container_name)
        checks["health"] = _agent_http(
            runner, metadata.container_name, "GET", "/health", ""
        )[0]
        for name, command in (
            ("terminal_workspace", _WORKSPACE_COMMAND),
            ("outside_and_sibling_denied", _BOUNDARY_COMMAND),
            ("terminal_secret_absence", _ENVIRONMENT_COMMAND),
            ("docker_api_denied", _DOCKER_COMMAND),
            ("network_boundary", _NETWORK_COMMAND),
        ):
            passed, exit_code = _bash_command(
                runner, metadata.container_name, command
            )
            checks[name] = passed
            exit_codes[name] = exit_code

        settings = runner.run(
            (
                "docker",
                "exec",
                metadata.container_name,
                "python",
                "-c",
                _SETTINGS_ISOLATION_CLIENT,
            )
        )
        checks["settings_api_session_absence"] = settings.returncode == 0
        exit_codes["settings_api_session_absence"] = settings.returncode

        litellm = runner.run(
            (
                "docker",
                "exec",
                "--env",
                "UNATTENDED_EXECUTOR_API_KEY",
                metadata.container_name,
                "python",
                "-c",
                _LITELLM_CLIENT,
            ),
            environment={"UNATTENDED_EXECUTOR_API_KEY": executor_key},
        )
        checks["litellm_executor_endpoint"] = litellm.returncode == 0
        exit_codes["litellm_executor_endpoint"] = litellm.returncode
    except Exception as error:
        error_type = type(error).__name__
    finally:
        executor_key = ""
        try:
            controller.stop_and_remove(handle)
            cleanup_passed = controller.inspect(handle) is None
        except Exception as cleanup_error:
            cleanup_passed = False
            if error_type is None:
                error_type = type(cleanup_error).__name__
        _remove_probe_workspace(workspace_root, handle)

    checks["stop_cleanup"] = cleanup_passed
    status = "PASS" if checks and all(checks.values()) and error_type is None else "FAIL"
    report: dict[str, Any] = {
        "status": status,
        "checks": checks,
        "exit_codes": exit_codes,
        "error_type": error_type,
    }
    if metadata is not None:
        report["container_name"] = metadata.container_name
        report["image_digest"] = metadata.image_digest
        report["mount_destination"] = metadata.workspace_destination
        report["network_name"] = metadata.network_name
    return report


def _agent_http(
    runner: SubprocessDockerRunner,
    container_name: str,
    method: str,
    path: str,
    payload: str,
) -> tuple[bool, int]:
    result = runner.run(
        (
            "docker",
            "exec",
            container_name,
            "python",
            "-c",
            _HTTP_CLIENT,
            method,
            path,
            payload,
        )
    )
    if result.returncode != 0:
        return False, result.returncode
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, 2
    exit_code = response.get("exit_code", 0)
    return response.get("http_ok") is True and exit_code == 0, int(exit_code or 0)


def _bash_command(
    runner: SubprocessDockerRunner,
    container_name: str,
    command: str,
) -> tuple[bool, int]:
    payload = json.dumps(
        {"command": command, "cwd": "/workspace/attempt", "timeout": 30}
    )
    return _agent_http(
        runner,
        container_name,
        "POST",
        "/api/bash/execute_bash_command",
        payload,
    )


def _wait_for_alive(
    runner: SubprocessDockerRunner, container_name: str
) -> bool:
    for _ in range(60):
        passed, _ = _agent_http(runner, container_name, "GET", "/alive", "")
        if passed:
            return True
        time.sleep(1)
    return False


def _remove_probe_workspace(root: Path, handle: ExecutionHandle) -> None:
    relative = Path(workspace_path(handle.workflow_id, handle.attempt)).relative_to(
        ".var/unattended"
    )
    target = (root / relative).resolve()
    if target.is_relative_to(root) and target != root and target.exists():
        shutil.rmtree(target)
    parent = target.parent
    while parent != root and parent.is_relative_to(root):
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def _failure(error_type: str) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "checks": {},
        "exit_codes": {},
        "error_type": error_type,
    }
