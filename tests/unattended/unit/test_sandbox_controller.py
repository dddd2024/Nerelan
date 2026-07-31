from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Sequence

import pytest
import reverse_agent.unattended.workspace as workspace_module

from reverse_agent.unattended import (
    AGENT_SERVER_DIGEST,
    AGENT_SERVER_IMAGE,
    ATTEMPT_WORKSPACE_DESTINATION,
    FIXED_LAUNCH_SPEC,
    DockerCommandResult,
    ExecutionHandle,
    FixedLaunchSpec,
    LaunchFailure,
    SandboxController,
    SandboxControllerError,
    container_name_for,
    executor_id,
    workspace_id,
    workspace_path,
)
from reverse_agent.unattended.workspace import (
    WORKSPACE_ROOT_IDENTITY_CONTENT,
    WORKSPACE_ROOT_IDENTITY_MARKER,
)
from reverse_agent.unattended.temporal_contracts import (
    is_launch_failure_code,
    is_launch_failure_retryable,
)

_NETWORK = "issue81_model-executor"
_VOLUME = "issue81_attempt-workspaces"


@pytest.fixture
def temporary_workspace_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name == "posix":
        monkeypatch.setattr(workspace_module, "WORKSPACE_ROOT_UID", os.geteuid())
        monkeypatch.setattr(workspace_module, "WORKSPACE_ROOT_GID", os.getegid())


def _handle(attempt: int = 1) -> ExecutionHandle:
    identifier = "unattended:dddd2024/reverse-agent:issue:81"
    return ExecutionHandle(
        identifier,
        attempt,
        workspace_id(identifier),
        executor_id(identifier, attempt),
        "2026-07-29T14:00:00+00:00",
    )


def _workspace(root: Path, handle: ExecutionHandle) -> Path:
    relative = Path(workspace_path(handle.workflow_id, handle.attempt)).relative_to(
        ".var/unattended"
    )
    return (root / relative).resolve()


def _inspect_payload(
    root: Path,
    handle: ExecutionHandle,
    *,
    overrides: Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    payload: dict[str, object] = {
        "Config": {
            "Image": AGENT_SERVER_IMAGE,
            "Labels": {"reverse-agent.execution-id": handle.executor_id},
            "Env": [
                "DO_NOT_TRACK=1",
                "OPENHANDS_AGENT_SERVER_CONFIG_PATH=/tmp/agent-server.json",
                "PATH=/usr/local/bin:/usr/bin",
            ],
        },
        "HostConfig": {
            "Privileged": False,
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"],
            "ReadonlyRootfs": True,
            "NetworkMode": _NETWORK,
            "PidMode": "",
            "IpcMode": "private",
            "Memory": 1073741824,
            "NanoCpus": 1000000000,
            "PidsLimit": 128,
            "Tmpfs": {
                "/tmp": "rw,exec,nosuid,nodev,size=512m",
                "/home/openhands": "rw,nosuid,size=128m",
            },
            "Mounts": [
                {
                    "Type": "volume",
                    "Source": _VOLUME,
                    "Target": ATTEMPT_WORKSPACE_DESTINATION,
                    "VolumeOptions": {
                        "Subpath": str(
                            Path(
                                workspace_path(
                                    handle.workflow_id,
                                    handle.attempt,
                                )
                            ).relative_to(".var/unattended")
                        ).replace("\\", "/")
                    },
                }
            ],
        },
        "State": {"Status": "running"},
        "Mounts": [
            {
                "Type": "volume",
                "Name": _VOLUME,
                "Destination": ATTEMPT_WORKSPACE_DESTINATION,
                "RW": True,
            }
        ],
        "NetworkSettings": {
            "Networks": {_NETWORK: {}},
        },
    }
    for dotted, value in (overrides or {}).items():
        current: dict[str, object] = payload
        parts = dotted.split(".")
        for part in parts[:-1]:
            selected = current[part]
            assert isinstance(selected, dict)
            current = selected
        current[parts[-1]] = value
    return [payload]


class StatefulRunner:
    def __init__(
        self,
        root: Path,
        handle: ExecutionHandle,
        *,
        exists: bool = False,
        create_returncode: int = 0,
        race_on_failure: bool = False,
        overrides: Mapping[str, object] | None = None,
        daemon_unavailable: bool = False,
        daemon_permission_denied: bool = False,
        network_missing: bool = False,
        volume_missing: bool = False,
        image_missing: bool = False,
        start_returncode: int = 0,
    ) -> None:
        self.root = root
        self.handle = handle
        self.exists = exists
        self.create_returncode = create_returncode
        self.race_on_failure = race_on_failure
        self.overrides = overrides
        self.daemon_unavailable = daemon_unavailable
        self.daemon_permission_denied = daemon_permission_denied
        self.network_missing = network_missing
        self.volume_missing = volume_missing
        self.image_missing = image_missing
        self.start_returncode = start_returncode
        self.calls: list[tuple[tuple[str, ...], Mapping[str, str] | None]] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
    ) -> DockerCommandResult:
        call = tuple(argv)
        self.calls.append((call, environment))

        if call[:2] == ("docker", "info"):
            if self.daemon_unavailable:
                return DockerCommandResult(
                    1, "", "Cannot connect to the Docker daemon"
                )
            if self.daemon_permission_denied:
                return DockerCommandResult(
                    1, "", "permission denied while trying to connect"
                )
            return DockerCommandResult(0, "29.5.2", "")

        if call[:3] == ("docker", "network", "inspect"):
            if self.network_missing:
                return DockerCommandResult(1, "", "network not found")
            return DockerCommandResult(0, "[]", "")

        if call[:3] == ("docker", "volume", "inspect"):
            if self.volume_missing:
                return DockerCommandResult(1, "", "volume not found")
            return DockerCommandResult(0, "[]", "")

        if call[:3] == ("docker", "image", "inspect"):
            if self.image_missing:
                return DockerCommandResult(1, "", "image not found")
            return DockerCommandResult(0, "[]", "")

        if call[:3] == ("docker", "container", "inspect"):
            if not self.exists:
                return DockerCommandResult(1, "", "not found")
            return DockerCommandResult(
                0,
                json.dumps(
                    _inspect_payload(
                        self.root,
                        self.handle,
                        overrides=self.overrides,
                    )
                ),
                "",
            )

        if call[:2] == ("docker", "create"):
            if self.create_returncode == 0 or self.race_on_failure:
                self.exists = True
            return DockerCommandResult(self.create_returncode, "created", "")

        if call[:3] == ("docker", "container", "start"):
            return DockerCommandResult(self.start_returncode, "", "")

        if call[:4] == ("docker", "container", "rm", "--force"):
            self.exists = False
            return DockerCommandResult(0, "", "")

        raise AssertionError(call)


def _controller(
    tmp_path: Path,
    runner: StatefulRunner,
) -> SandboxController:
    root = (tmp_path / "attempts").absolute()
    root.mkdir(mode=0o750, exist_ok=True)
    root.chmod(0o750)
    (root / WORKSPACE_ROOT_IDENTITY_MARKER).write_text(
        WORKSPACE_ROOT_IDENTITY_CONTENT,
        encoding="utf-8",
    )
    return SandboxController(
        runner,
        host_workspace_root=root,
        executor_network=_NETWORK,
        workspace_volume=_VOLUME,
    )


def test_container_name_is_deterministic_per_attempt() -> None:
    assert container_name_for(_handle()) == container_name_for(_handle())
    assert container_name_for(_handle()) != container_name_for(_handle(2))
    assert container_name_for(_handle()).startswith("reverse-agent-attempt-")


def test_launch_uses_only_fixed_argv_and_sanitized_metadata(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    metadata = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    create_call = next(
        (call for call in runner.calls if call[0][1] == "create"), None
    )
    assert create_call is not None
    launch = create_call[0]
    assert launch[0:2] == ("docker", "create")
    assert AGENT_SERVER_IMAGE in launch
    assert ("--cap-drop", "ALL") == launch[
        launch.index("--cap-drop") : launch.index("--cap-drop") + 2
    ]
    assert "no-new-privileges:true" in launch
    assert "/var/run/docker.sock" not in " ".join(launch)
    mount = launch[launch.index("--mount") + 1]
    assert mount.startswith(f"type=volume,src={_VOLUME},")
    assert "volume-subpath=" in mount
    assert "SESSION_API_KEY" not in launch
    assert launch[launch.index("--host") + 1] == "127.0.0.1"
    assert create_call[1] is None
    assert metadata.image_digest == AGENT_SERVER_DIGEST
    assert metadata.workspace_destination == ATTEMPT_WORKSPACE_DESTINATION
    assert metadata.network_name == _NETWORK
    assert metadata.privileged is False
    assert metadata.no_new_privileges is True
    assert metadata.read_only_rootfs is True
    assert "SESSION_API_KEY" not in repr(metadata)


def test_reconcile_existing_never_creates_duplicate(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), exists=True)

    first = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )
    second = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    assert first == second
    assert not any(call[0][1] == "create" for call in runner.calls)


def test_create_conflict_reconciles_exact_existing_container(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        race_on_failure=True,
    )

    metadata = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    assert metadata.container_name == container_name_for(_handle())
    assert sum(call[0][1] == "create" for call in runner.calls) == 1


def test_failed_create_without_reconciled_container_raises_launch_failure(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), create_returncode=125)

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_CREATE_FAILED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_reconcile_rejects_nonrunning_container(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={"State.Status": "exited"},
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_NOT_RUNNING_AFTER_START"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_stop_remove_is_exact_and_idempotent(tmp_path: Path) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), exists=True)
    controller = _controller(tmp_path, runner)

    controller.stop_and_remove(_handle())
    controller.stop_and_remove(_handle())

    removals = [
        call[0] for call in runner.calls if call[0][:3] == ("docker", "container", "rm")
    ]
    assert removals == [
        ("docker", "container", "rm", "--force", container_name_for(_handle()))
    ]


def test_cleanup_removes_exact_container_and_workspace_idempotently(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), exists=True)
    controller = _controller(tmp_path, runner)
    workspace = _workspace(root, _handle())
    workspace.mkdir(parents=True)
    (workspace / "provider-free-runtime-proof.txt").write_text(
        "PROVIDER_FREE_RUNTIME_PROOF",
        encoding="utf-8",
    )

    assert controller.cleanup_attempt(_handle()) == (True, True)
    assert controller.cleanup_attempt(_handle()) == (True, True)
    assert not workspace.exists()
    removals = [
        call[0] for call in runner.calls if call[0][:3] == ("docker", "container", "rm")
    ]
    assert removals == [
        ("docker", "container", "rm", "--force", container_name_for(_handle()))
    ]


def test_only_singleton_fixed_launch_spec_is_accepted(tmp_path: Path) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    with pytest.raises(ValueError, match="untrusted_launch_spec"):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FixedLaunchSpec()
        )
    with pytest.raises(AttributeError):
        FIXED_LAUNCH_SPEC.profile = "caller-controlled"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("override", "value"),
    [
        ("Config.Image", "caller/image:latest"),
        ("HostConfig.Privileged", True),
        ("HostConfig.CapDrop", []),
        ("HostConfig.SecurityOpt", []),
        ("HostConfig.ReadonlyRootfs", False),
        ("HostConfig.NetworkMode", "control"),
        ("HostConfig.PidMode", "host"),
        ("HostConfig.IpcMode", "host"),
        ("HostConfig.Memory", 0),
        ("HostConfig.NanoCpus", 0),
        ("HostConfig.PidsLimit", 0),
        ("HostConfig.Tmpfs", {}),
        ("Mounts", []),
        ("NetworkSettings.Networks", {"control": {}}),
        ("Config.Env", ["SESSION_API_KEY=synthetic", "GITHUB_TOKEN=forbidden"]),
    ],
)
def test_inspect_rejects_any_launch_contract_drift(
    tmp_path: Path, override: str, value: object
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={override: value},
    )

    with pytest.raises(SandboxControllerError, match="inspect_contract_mismatch"):
        _controller(tmp_path, runner).inspect(_handle())


@pytest.mark.parametrize(
    "unexpected",
    [
        {"image": "caller/image"},
        {"command": ["sh"]},
        {"mount": "/:/host"},
        {"environment": {"GITHUB_TOKEN": "caller"}},
        {"network": "host"},
        {"privileged": True},
    ],
)
def test_launch_rejects_task_controlled_container_fields(
    tmp_path: Path, unexpected: Mapping[str, object]
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    with pytest.raises(ValueError, match="untrusted_launch_spec"):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), unexpected  # type: ignore[arg-type]
        )


# --- Finite launch failure category tests ---


def test_launch_raises_docker_socket_unavailable(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), daemon_unavailable=True)

    with pytest.raises(
        LaunchFailure, match="DOCKER_SOCKET_UNAVAILABLE"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_docker_socket_permission_denied(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), daemon_permission_denied=True)

    with pytest.raises(
        LaunchFailure, match="DOCKER_SOCKET_PERMISSION_DENIED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_executor_network_missing(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), network_missing=True)

    with pytest.raises(
        LaunchFailure, match="EXECUTOR_NETWORK_MISSING"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_workspace_volume_missing(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), volume_missing=True)

    with pytest.raises(
        LaunchFailure, match="WORKSPACE_VOLUME_MISSING"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_agent_image_unavailable(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), image_missing=True)

    with pytest.raises(
        LaunchFailure, match="AGENT_IMAGE_UNAVAILABLE"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_docker_container_start_failed(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), start_returncode=1)

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_START_FAILED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_inspect_contract_mismatch(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={"HostConfig.Privileged": True},
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_INSPECT_CONTRACT_MISMATCH"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_failure_retryable_only_for_transient() -> None:
    """Only DOCKER_LAUNCH_TRANSIENT_UNAVAILABLE is retryable; all others are not."""
    transient = LaunchFailure("DOCKER_LAUNCH_TRANSIENT_UNAVAILABLE")
    assert transient.retryable is True
    assert is_launch_failure_retryable("DOCKER_LAUNCH_TRANSIENT_UNAVAILABLE") is True

    non_retryable_codes = (
        "DOCKER_SOCKET_UNAVAILABLE",
        "DOCKER_SOCKET_PERMISSION_DENIED",
        "EXECUTOR_NETWORK_MISSING",
        "WORKSPACE_VOLUME_MISSING",
        "WORKSPACE_SUBPATH_MISSING",
        "WORKSPACE_VOLUME_SUBPATH_UNSUPPORTED",
        "AGENT_IMAGE_UNAVAILABLE",
        "DOCKER_CREATE_CONTRACT_REJECTED",
        "DOCKER_CONTAINER_CREATE_FAILED",
        "DOCKER_CONTAINER_MISSING_AFTER_CREATE",
        "DOCKER_CONTAINER_START_FAILED",
        "DOCKER_CONTAINER_NOT_RUNNING_AFTER_START",
        "DOCKER_INSPECT_CONTRACT_MISMATCH",
    )
    for code in non_retryable_codes:
        assert is_launch_failure_code(code) is True
        assert is_launch_failure_retryable(code) is False
        assert LaunchFailure(code).retryable is False


def test_launch_failure_rejects_invalid_code() -> None:
    with pytest.raises(ValueError, match="invalid_launch_failure_code"):
        LaunchFailure("ATTEMPT_LAUNCH_FAILED")
    with pytest.raises(ValueError, match="invalid_launch_failure_code"):
        LaunchFailure("CALLER_CONTROLLED_CODE")
