"""Thin fixed-contract Docker controller for one OpenHands Attempt container."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from .contracts import ExecutionHandle
from .identifiers import executor_id
from .temporal_contracts import WorkspaceRootPreflightResult
from .workspace import WorkspaceRootManager

AGENT_SERVER_IMAGE = (
    "ghcr.io/openhands/agent-server:1.37.0-python@"
    "sha256:c188dac7624d486331b455042d54abe020af43b843c2c02694deccecfbed487a"
)
AGENT_SERVER_DIGEST = (
    "sha256:c188dac7624d486331b455042d54abe020af43b843c2c02694deccecfbed487a"
)
ATTEMPT_WORKSPACE_DESTINATION = "/workspace/attempt"
_NETWORK_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,126}\Z")
_FORBIDDEN_ENV_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "COHERE_API_KEY",
        "GEMINI_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GOOGLE_API_KEY",
        "LITELLM_MASTER_KEY",
        "LLM_API_KEY",
        "MISTRAL_API_KEY",
        "OH_SESSION_API_KEYS_0",
        "OPENAI_API_KEY",
        "SESSION_API_KEY",
    }
)
_EXPECTED_TMPFS = frozenset({"/tmp", "/home/openhands"})


class SandboxControllerError(RuntimeError):
    """A sanitized controller failure without Docker output."""


@dataclass(frozen=True, slots=True)
class FixedLaunchSpec:
    """Opaque marker for the sole audited launch profile."""

    schema_version: int = 1
    profile: str = "unattended-openhands-v1.37-attempt"


FIXED_LAUNCH_SPEC = FixedLaunchSpec()


@dataclass(frozen=True, slots=True)
class DockerCommandResult:
    returncode: int
    stdout: str
    stderr: str


class DockerCommandRunner(Protocol):
    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
        input_text: str | None = None,
    ) -> DockerCommandResult: ...


class SubprocessDockerRunner:
    """Run fixed Docker argv without a shell."""

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
        input_text: str | None = None,
    ) -> DockerCommandResult:
        if not argv or argv[0] != "docker":
            raise ValueError("docker_argv_required")
        process_env = os.environ.copy()
        if environment:
            process_env.update(environment)
        completed = subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            env=process_env,
            input=input_text,
        )
        return DockerCommandResult(
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )


@dataclass(frozen=True, slots=True)
class AttemptContainerMetadata:
    container_name: str
    state: str
    image_digest: str
    workspace_destination: str
    network_name: str
    privileged: bool
    no_new_privileges: bool
    read_only_rootfs: bool


class SandboxController:
    """Own exactly one deterministic, fixed-profile container per Attempt."""

    def __init__(
        self,
        runner: DockerCommandRunner,
        *,
        host_workspace_root: Path,
        executor_network: str,
        workspace_volume: str,
    ) -> None:
        if not host_workspace_root.is_absolute():
            raise ValueError("host_workspace_root_must_be_absolute")
        if _NETWORK_NAME.fullmatch(executor_network) is None:
            raise ValueError("executor_network_invalid")
        self._workspace = WorkspaceRootManager(
            host_workspace_root,
            volume_name=workspace_volume,
        )
        self._runner = runner
        self._host_workspace_root = host_workspace_root
        self._executor_network = executor_network
        self._workspace_volume = workspace_volume

    def preflight_workspace(
        self,
        handle: ExecutionHandle,
    ) -> WorkspaceRootPreflightResult:
        self._validate_handle(handle)
        return self._workspace.preflight(handle)

    def launch_or_reconcile(
        self,
        handle: ExecutionHandle,
        fixed_launch_spec: FixedLaunchSpec,
    ) -> AttemptContainerMetadata:
        self._require_fixed_spec(fixed_launch_spec)
        self._validate_handle(handle)
        self.preflight_workspace(handle)
        existing = self.inspect(handle)
        if existing is not None:
            return self._require_running(existing)

        result = self._runner.run(
            self._launch_argv(handle),
        )
        if result.returncode != 0:
            raced = self.inspect(handle)
            if raced is not None:
                return self._require_running(raced)
            raise SandboxControllerError("docker_container_create_failed")
        created = self.inspect(handle)
        if created is None:
            raise SandboxControllerError("docker_container_missing_after_create")
        return self._require_running(created)

    def inspect(self, handle: ExecutionHandle) -> AttemptContainerMetadata | None:
        self._validate_handle(handle)
        name = container_name_for(handle)
        result = self._runner.run(("docker", "container", "inspect", name))
        if result.returncode != 0:
            return None
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, list) or len(payload) != 1:
                raise ValueError("unexpected_inspect_shape")
            item = payload[0]
            return self._validate_inspect(handle, item)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise SandboxControllerError("docker_inspect_contract_mismatch") from error

    def stop_and_remove(self, handle: ExecutionHandle) -> None:
        self._validate_handle(handle)
        if self.inspect(handle) is None:
            return
        result = self._runner.run(
            ("docker", "container", "rm", "--force", container_name_for(handle))
        )
        if result.returncode != 0:
            raise SandboxControllerError("docker_container_remove_failed")
        if self.inspect(handle) is not None:
            raise SandboxControllerError("docker_container_present_after_remove")

    def cleanup_attempt(self, handle: ExecutionHandle) -> tuple[bool, bool]:
        """Remove the exact deterministic container and workspace idempotently."""

        self._validate_handle(handle)
        self.stop_and_remove(handle)
        workspace = self._workspace_candidate(handle)
        if workspace.exists():
            if workspace.is_symlink() or not workspace.is_dir():
                raise SandboxControllerError("attempt_workspace_contract_mismatch")
            shutil.rmtree(workspace)
        if workspace.exists():
            raise SandboxControllerError("attempt_workspace_present_after_remove")
        parent = workspace.parent
        while parent != self._host_workspace_root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
        return self.inspect(handle) is None, not workspace.exists()

    @staticmethod
    def _require_fixed_spec(spec: FixedLaunchSpec) -> None:
        if spec is not FIXED_LAUNCH_SPEC:
            raise ValueError("untrusted_launch_spec")

    @staticmethod
    def _require_running(
        metadata: AttemptContainerMetadata,
    ) -> AttemptContainerMetadata:
        if metadata.state != "running":
            raise SandboxControllerError("attempt_container_not_running")
        return metadata

    @staticmethod
    def _validate_handle(handle: ExecutionHandle) -> None:
        if handle.executor_id != executor_id(handle.workflow_id, handle.attempt):
            raise ValueError("executor_id_mismatch")

    def _workspace_for(self, handle: ExecutionHandle) -> Path:
        return self._workspace.attempt_path(handle)

    def _workspace_candidate(self, handle: ExecutionHandle) -> Path:
        return self._workspace.attempt_path(handle)

    def _launch_argv(self, handle: ExecutionHandle) -> tuple[str, ...]:
        return (
            "docker",
            "run",
            "--detach",
            "--name",
            container_name_for(handle),
            "--label",
            f"reverse-agent.execution-id={handle.executor_id}",
            "--network",
            self._executor_network,
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "128",
            "--cpus",
            "1.0",
            "--memory",
            "1g",
            "--tmpfs",
            "/tmp:rw,exec,nosuid,nodev,size=512m",
            "--tmpfs",
            "/home/openhands:rw,nosuid,size=128m",
            "--mount",
            (
                f"type=volume,src={self._workspace_volume},"
                f"dst={ATTEMPT_WORKSPACE_DESTINATION},"
                f"volume-subpath={self._workspace.attempt_subpath(handle)}"
            ),
            "--workdir",
            ATTEMPT_WORKSPACE_DESTINATION,
            "--env",
            "DO_NOT_TRACK=1",
            "--env",
            "OPENHANDS_AGENT_SERVER_CONFIG_PATH=/tmp/agent-server.json",
            AGENT_SERVER_IMAGE,
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        )

    def _validate_inspect(
        self, handle: ExecutionHandle, item: Mapping[str, object]
    ) -> AttemptContainerMetadata:
        config = _mapping(item, "Config")
        host = _mapping(item, "HostConfig")
        state = _mapping(item, "State")
        mounts = item.get("Mounts")
        network_settings = _mapping(item, "NetworkSettings")
        networks = _mapping(network_settings, "Networks")
        labels = config.get("Labels")
        env = config.get("Env")
        security_opt = host.get("SecurityOpt")
        cap_drop = host.get("CapDrop")
        tmpfs = host.get("Tmpfs")
        host_mounts = host.get("Mounts")

        if config.get("Image") != AGENT_SERVER_IMAGE:
            raise ValueError("image_mismatch")
        if not isinstance(labels, Mapping) or labels.get(
            "reverse-agent.execution-id"
        ) != handle.executor_id:
            raise ValueError("identity_label_mismatch")
        if host.get("Privileged") is not False:
            raise ValueError("privileged_container")
        if not isinstance(cap_drop, list) or {str(v).upper() for v in cap_drop} != {
            "ALL"
        }:
            raise ValueError("capabilities_not_dropped")
        if not isinstance(security_opt, list) or not any(
            str(value).lower().replace("=", ":")
            == "no-new-privileges:true"
            for value in security_opt
        ):
            raise ValueError("no_new_privileges_missing")
        if host.get("ReadonlyRootfs") is not True:
            raise ValueError("rootfs_not_read_only")
        if host.get("NetworkMode") != self._executor_network:
            raise ValueError("network_mode_mismatch")
        if host.get("PidMode") not in {"", None} or host.get("IpcMode") in {"host"}:
            raise ValueError("host_namespace_sharing")
        if host.get("Memory") != 1073741824 or host.get("NanoCpus") != 1000000000:
            raise ValueError("cpu_memory_limit_mismatch")
        if host.get("PidsLimit") != 128:
            raise ValueError("pid_limit_mismatch")
        if not isinstance(tmpfs, Mapping) or set(tmpfs) != _EXPECTED_TMPFS:
            raise ValueError("tmpfs_mismatch")
        if not isinstance(mounts, list) or len(mounts) != 1:
            raise ValueError("mount_count_mismatch")
        mount = mounts[0]
        if (
            not isinstance(mount, Mapping)
            or mount.get("Type") != "volume"
            or mount.get("Name") != self._workspace_volume
            or mount.get("Destination") != ATTEMPT_WORKSPACE_DESTINATION
            or mount.get("RW") is not True
        ):
            raise ValueError("workspace_mount_mismatch")
        if not isinstance(host_mounts, list) or len(host_mounts) != 1:
            raise ValueError("host_mount_count_mismatch")
        host_mount = host_mounts[0]
        if not isinstance(host_mount, Mapping):
            raise ValueError("host_mount_shape")
        volume_options = host_mount.get("VolumeOptions")
        if (
            host_mount.get("Type") != "volume"
            or host_mount.get("Source") != self._workspace_volume
            or host_mount.get("Target") != ATTEMPT_WORKSPACE_DESTINATION
            or not isinstance(volume_options, Mapping)
            or volume_options.get("Subpath")
            != self._workspace.attempt_subpath(handle)
        ):
            raise ValueError("workspace_volume_subpath_mismatch")
        if set(networks) != {self._executor_network}:
            raise ValueError("network_attachment_mismatch")
        if not isinstance(env, list):
            raise ValueError("environment_shape")
        env_names = {str(value).split("=", 1)[0] for value in env}
        if env_names & _FORBIDDEN_ENV_NAMES:
            raise ValueError("forbidden_container_environment")

        return AttemptContainerMetadata(
            container_name=container_name_for(handle),
            state=str(state.get("Status") or "unknown"),
            image_digest=AGENT_SERVER_DIGEST,
            workspace_destination=ATTEMPT_WORKSPACE_DESTINATION,
            network_name=self._executor_network,
            privileged=False,
            no_new_privileges=True,
            read_only_rootfs=True,
        )


def container_name_for(handle: ExecutionHandle) -> str:
    if handle.executor_id != executor_id(handle.workflow_id, handle.attempt):
        raise ValueError("executor_id_mismatch")
    return f"reverse-agent-attempt-{handle.executor_id}"


def _mapping(
    value: Mapping[str, object], key: str
) -> Mapping[str, object]:
    selected = value.get(key)
    if not isinstance(selected, Mapping):
        raise ValueError(f"missing_{key.lower()}")
    return selected
