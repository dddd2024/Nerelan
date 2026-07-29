"""Thin fixed-contract Docker controller for one OpenHands Attempt container."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Protocol, Sequence

from .contracts import ExecutionHandle
from .identifiers import executor_id, workspace_path
from .openhands import prepare_bounded_workspace

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
    ) -> DockerCommandResult: ...


class SubprocessDockerRunner:
    """Run fixed Docker argv without a shell."""

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
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
        session_api_key: str,
    ) -> None:
        if not host_workspace_root.is_absolute():
            raise ValueError("host_workspace_root_must_be_absolute")
        host_workspace_root.mkdir(parents=True, exist_ok=True)
        if host_workspace_root.is_symlink():
            raise ValueError("host_workspace_root_symlink")
        if _NETWORK_NAME.fullmatch(executor_network) is None:
            raise ValueError("executor_network_invalid")
        if (
            not isinstance(session_api_key, str)
            or not session_api_key
            or "\x00" in session_api_key
        ):
            raise ValueError("session_api_key_invalid")
        self._runner = runner
        self._host_workspace_root = host_workspace_root.resolve(strict=True)
        self._executor_network = executor_network
        self._session_api_key = session_api_key

    def launch_or_reconcile(
        self,
        handle: ExecutionHandle,
        fixed_launch_spec: FixedLaunchSpec,
    ) -> AttemptContainerMetadata:
        self._require_fixed_spec(fixed_launch_spec)
        self._validate_handle(handle)
        existing = self.inspect(handle)
        if existing is not None:
            return existing

        workspace = self._workspace_for(handle)
        result = self._runner.run(
            self._launch_argv(handle, workspace),
            environment={"SESSION_API_KEY": self._session_api_key},
        )
        if result.returncode != 0:
            raced = self.inspect(handle)
            if raced is not None:
                return raced
            raise SandboxControllerError("docker_container_create_failed")
        created = self.inspect(handle)
        if created is None:
            raise SandboxControllerError("docker_container_missing_after_create")
        return created

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

    @staticmethod
    def _require_fixed_spec(spec: FixedLaunchSpec) -> None:
        if spec is not FIXED_LAUNCH_SPEC:
            raise ValueError("untrusted_launch_spec")

    @staticmethod
    def _validate_handle(handle: ExecutionHandle) -> None:
        if handle.executor_id != executor_id(handle.workflow_id, handle.attempt):
            raise ValueError("executor_id_mismatch")

    def _workspace_for(self, handle: ExecutionHandle) -> Path:
        relative = (
            PurePosixPath(workspace_path(handle.workflow_id, handle.attempt))
            .relative_to(".var/unattended")
            .as_posix()
        )
        return prepare_bounded_workspace(self._host_workspace_root, relative)

    def _launch_argv(self, handle: ExecutionHandle, workspace: Path) -> tuple[str, ...]:
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
            "/tmp:rw,noexec,nosuid,size=64m",
            "--tmpfs",
            "/home/openhands:rw,nosuid,size=128m",
            "--mount",
            (
                f"type=bind,src={workspace},"
                f"dst={ATTEMPT_WORKSPACE_DESTINATION},rw"
            ),
            "--workdir",
            ATTEMPT_WORKSPACE_DESTINATION,
            "--env",
            "SESSION_API_KEY",
            "--env",
            "DO_NOT_TRACK=1",
            "--env",
            "OPENHANDS_AGENT_SERVER_CONFIG_PATH=/tmp/agent-server.json",
            AGENT_SERVER_IMAGE,
            "--host",
            "0.0.0.0",
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
        networks = _mapping(_mapping(item, "NetworkSettings"), "Networks")
        labels = config.get("Labels")
        env = config.get("Env")
        security_opt = host.get("SecurityOpt")
        cap_drop = host.get("CapDrop")
        tmpfs = host.get("Tmpfs")

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
        expected_workspace = self._workspace_for(handle)
        if (
            not isinstance(mount, Mapping)
            or mount.get("Type") != "bind"
            or Path(str(mount.get("Source"))).resolve() != expected_workspace
            or mount.get("Destination") != ATTEMPT_WORKSPACE_DESTINATION
            or mount.get("RW") is not True
        ):
            raise ValueError("workspace_mount_mismatch")
        if set(networks) != {self._executor_network}:
            raise ValueError("network_attachment_mismatch")
        if not isinstance(env, list):
            raise ValueError("environment_shape")
        env_names = {str(value).split("=", 1)[0] for value in env}
        if env_names & _FORBIDDEN_ENV_NAMES:
            raise ValueError("forbidden_container_environment")
        if "SESSION_API_KEY" not in env_names:
            raise ValueError("session_credential_missing")

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
