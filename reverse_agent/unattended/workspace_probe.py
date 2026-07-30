"""Sanitized fresh/restart probe for the fixed workspace-volume contract."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .identifiers import executor_id, workspace_id
from .sandbox import AGENT_SERVER_IMAGE
from .workspace import WORKSPACE_ROOT

_PROJECT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,62}\Z")
_WORKER_IMAGE = "reverse-agent-unattended-worker:issue82"
_WORKFLOW_ID = "unattended:dddd2024/reverse-agent:issue:85:workspace-preflight"
_CONTROLLER_PROBE = """\
import json
from dataclasses import asdict
from reverse_agent.unattended.contracts import ExecutionHandle
from reverse_agent.unattended.identifiers import executor_id, workspace_id
from reverse_agent.unattended.workspace import WORKSPACE_ROOT, WorkspaceRootManager
w = "unattended:dddd2024/reverse-agent:issue:85:workspace-preflight"
h = ExecutionHandle(w, 1, workspace_id(w), executor_id(w, 1), "2026-07-30T06:00:00+00:00")
m = WorkspaceRootManager(WORKSPACE_ROOT, volume_name="VOLUME_NAME")
print(json.dumps(asdict(m.preflight(h)), sort_keys=True))
"""
_AGENT_PROBE = """\
import json
from pathlib import Path
def writable(path):
    try:
        probe = path / ".agent-write-probe"
        probe.write_text("probe")
        probe.unlink()
        return True
    except OSError:
        return False
print(json.dumps({
    "agent_exact_attempt_write": writable(Path("/workspace/attempt")),
    "agent_root_denied": not writable(Path("/workspace")),
    "agent_sibling_denied": not writable(Path("/workspace/sibling")),
    "agent_outside_denied": not writable(Path("/opt")),
}, sort_keys=True))
"""
_CLEANUP_PROBE = """\
import json
import shutil
from reverse_agent.unattended.contracts import ExecutionHandle
from reverse_agent.unattended.identifiers import executor_id, workspace_id
from reverse_agent.unattended.workspace import WORKSPACE_ROOT, WorkspaceRootManager
w = "unattended:dddd2024/reverse-agent:issue:85:workspace-preflight"
h = ExecutionHandle(w, 1, workspace_id(w), executor_id(w, 1), "2026-07-30T06:00:00+00:00")
m = WorkspaceRootManager(WORKSPACE_ROOT, volume_name="VOLUME_NAME")
p = m.attempt_path(h)
if p.exists():
    shutil.rmtree(p)
print(json.dumps({
    "attempt_absent": not p.exists(),
    "root_preserved": WORKSPACE_ROOT.is_dir(),
}, sort_keys=True))
"""


def run_workspace_preflight_probe(
    *,
    repository_root: Path,
    compose_project: str,
    stack_mode: str,
) -> dict[str, Any]:
    if _PROJECT_NAME.fullmatch(compose_project) is None:
        return _failure("compose_project_invalid")
    if stack_mode not in {"fresh", "restart"}:
        return _failure("stack_mode_invalid")
    volume_name = f"{compose_project}_attempt-workspaces"
    volume_exists = _run(
        ("docker", "volume", "inspect", volume_name),
        accept=(0, 1),
    ).returncode == 0
    if (stack_mode == "fresh" and volume_exists) or (
        stack_mode == "restart" and not volume_exists
    ):
        return _failure("workspace_volume_lifecycle_mismatch")

    created = False
    try:
        if stack_mode == "fresh":
            _require_success(
                (
                    "docker",
                    "volume",
                    "create",
                    "--label",
                    f"reverse-agent.workspace-project={compose_project}",
                    volume_name,
                ),
                "workspace_volume_create_failed",
            )
            created = True
        source_mount = (
            f"type=bind,src={repository_root / 'reverse_agent'},"
            "dst=/opt/reverse-agent/reverse_agent,readonly"
        )
        root_mount = (
            f"type=volume,src={volume_name},dst={WORKSPACE_ROOT.as_posix()}"
        )
        _require_success(
            (
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--cap-add",
                "CHOWN",
                "--cap-add",
                "FOWNER",
                "--cap-add",
                "DAC_OVERRIDE",
                "--security-opt",
                "no-new-privileges:true",
                "--user",
                "0:0",
                "--mount",
                root_mount,
                "--mount",
                source_mount,
                "--entrypoint",
                "python",
                _WORKER_IMAGE,
                "-m",
                "reverse_agent.unattended.workspace_bootstrap",
            ),
            "workspace_bootstrap_failed",
        )
        controller = _json_command(
            (
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--user",
                "10001:10001",
                "--mount",
                root_mount,
                "--mount",
                source_mount,
                "--entrypoint",
                "python",
                _WORKER_IMAGE,
                "-c",
                _CONTROLLER_PROBE.replace("VOLUME_NAME", volume_name),
            ),
            "controller_workspace_preflight_failed",
        )
        subpath = _attempt_subpath()
        agent = _json_command(
            (
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--user",
                "10001:10001",
                "--mount",
                (
                    f"type=volume,src={volume_name},"
                    "dst=/workspace/attempt,"
                    f"volume-subpath={subpath}"
                ),
                "--entrypoint",
                "python",
                AGENT_SERVER_IMAGE,
                "-c",
                _AGENT_PROBE,
            ),
            "agent_workspace_probe_failed",
        )
        cleanup = _json_command(
            (
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--user",
                "10001:10001",
                "--mount",
                root_mount,
                "--mount",
                source_mount,
                "--entrypoint",
                "python",
                _WORKER_IMAGE,
                "-c",
                _CLEANUP_PROBE.replace("VOLUME_NAME", volume_name),
            ),
            "workspace_cleanup_probe_failed",
        )
        checks = {
            "bootstrap": True,
            "preflight": all(
                bool(controller[name])
                for name in (
                    "owner_matches_policy",
                    "mode_matches_policy",
                    "controller_atomic_probe",
                    "attempt_directory_provisioned",
                    "host_controller_identity_match",
                )
            ),
            "agent_exact_attempt_write": bool(
                agent["agent_exact_attempt_write"]
            ),
            "agent_root_denied": bool(agent["agent_root_denied"]),
            "agent_sibling_denied": bool(agent["agent_sibling_denied"]),
            "agent_outside_denied": bool(agent["agent_outside_denied"]),
            "attempt_cleanup": bool(cleanup["attempt_absent"]),
            "root_preserved": bool(cleanup["root_preserved"]),
        }
        report = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "stack_mode": stack_mode,
            "source_kind": controller["source_kind"],
            "root_uid": controller["root_uid"],
            "root_gid": controller["root_gid"],
            "root_mode": controller["root_mode"],
            "controller_uid": controller["controller_uid"],
            "controller_gid": controller["controller_gid"],
            "agent_uid": controller["agent_uid"],
            "agent_gid": controller["agent_gid"],
            "checks": checks,
            "failure_category": None,
        }
        if stack_mode == "restart":
            _require_success(
                ("docker", "volume", "rm", volume_name),
                "workspace_volume_cleanup_failed",
            )
        return report
    except WorkspaceProbeFailure as error:
        if created and stack_mode == "fresh":
            _run(("docker", "volume", "rm", volume_name), accept=(0, 1))
        return _failure(error.category, stack_mode=stack_mode)


class WorkspaceProbeFailure(RuntimeError):
    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


def _run(
    argv: Sequence[str],
    *,
    accept: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(argv),
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    if completed.returncode not in accept:
        raise WorkspaceProbeFailure("docker_command_failed")
    return completed


def _require_success(argv: Sequence[str], category: str) -> None:
    completed = _run(argv, accept=(0, 1, 125))
    if completed.returncode != 0:
        raise WorkspaceProbeFailure(category)


def _json_command(argv: Sequence[str], category: str) -> dict[str, Any]:
    completed = _run(argv, accept=(0, 1, 125))
    if completed.returncode != 0:
        raise WorkspaceProbeFailure(category)
    try:
        value = json.loads(completed.stdout)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise WorkspaceProbeFailure(category) from None
    if not isinstance(value, dict):
        raise WorkspaceProbeFailure(category)
    return value


def _attempt_subpath() -> str:
    from .workspace import WorkspaceRootManager

    from .contracts import ExecutionHandle

    handle = ExecutionHandle(
        _WORKFLOW_ID,
        1,
        workspace_id(_WORKFLOW_ID),
        executor_id(_WORKFLOW_ID, 1),
        "2026-07-30T06:00:00+00:00",
    )
    return WorkspaceRootManager.attempt_subpath(handle)


def _failure(
    category: str,
    *,
    stack_mode: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "stack_mode": stack_mode,
        "source_kind": "volume",
        "checks": {},
        "failure_category": category,
    }
