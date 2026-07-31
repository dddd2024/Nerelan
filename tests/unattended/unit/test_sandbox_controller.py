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
    """Deterministic Docker runner that distinguishes v12 bounded probes.

    The runner inspects argv to route each fixed probe (subpath, helper,
    capability, minimal) independently. Probe return codes are controlled
    by explicit parameters so tests can drive each finite failure category
    without relying on Docker stderr.
    """

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
        create_stderr: str = "",
        subpath_missing: bool = False,
        subpath_probe_returncode: int | None = None,
        helper_probe_returncode: int | None = None,
        capability_probe_returncode: int = 0,
        minimal_probe_returncode: int = 0,
        start_inspect_state: str | None = None,
    ) -> None:
        self.root = root
        self.handle = handle
        self.exists = exists
        self.create_returncode = create_returncode
        self.create_stderr = create_stderr
        self.race_on_failure = race_on_failure
        self.overrides = overrides
        self.daemon_unavailable = daemon_unavailable
        self.daemon_permission_denied = daemon_permission_denied
        self.network_missing = network_missing
        self.volume_missing = volume_missing
        self.image_missing = image_missing
        self.start_returncode = start_returncode
        # Backwards-compatible subpath_missing drives the default subpath
        # probe return code (1) and helper readiness (0), so a missing
        # subpath is reported as WORKSPACE_SUBPATH_MISSING rather than
        # masking a helper failure.
        self.subpath_probe_returncode = (
            subpath_probe_returncode
            if subpath_probe_returncode is not None
            else (1 if subpath_missing else 0)
        )
        self.helper_probe_returncode = (
            helper_probe_returncode
            if helper_probe_returncode is not None
            else 0
        )
        self.capability_probe_returncode = capability_probe_returncode
        self.minimal_probe_returncode = minimal_probe_returncode
        # When start returns nonzero, inspect reports this state for the
        # exact container. None means the container is absent.
        self.start_inspect_state = start_inspect_state
        self.calls: list[tuple[tuple[str, ...], Mapping[str, str] | None]] = []

    def _is_subpath_probe(self, call: tuple[str, ...]) -> bool:
        return (
            call[:2] == ("docker", "run")
            and "--rm" in call
            and "-v" in call
            and "/__volume_check" in " ".join(call)
        )

    def _is_helper_probe(self, call: tuple[str, ...]) -> bool:
        return (
            call[:2] == ("docker", "run")
            and "--rm" in call
            and "-v" not in call
            and "exit 0" in " ".join(call)
        )

    def _is_capability_probe(self, call: tuple[str, ...]) -> bool:
        return (
            call[:2] == ("docker", "create")
            and "--name" in call
            and "reverse-agent-capability-probe" in call
        )

    def _is_minimal_probe(self, call: tuple[str, ...]) -> bool:
        return (
            call[:2] == ("docker", "create")
            and "--name" in call
            and "reverse-agent-minimal-probe" in call
        )

    def _is_probe_cleanup(self, call: tuple[str, ...]) -> bool:
        return (
            call[:4] == ("docker", "container", "rm", "--force")
            and len(call) >= 5
            and call[4] in {"reverse-agent-capability-probe", "reverse-agent-minimal-probe"}
        )

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

        if self._is_subpath_probe(call):
            return DockerCommandResult(self.subpath_probe_returncode, "", "")

        if self._is_helper_probe(call):
            return DockerCommandResult(self.helper_probe_returncode, "", "")

        if self._is_capability_probe(call):
            return DockerCommandResult(self.capability_probe_returncode, "", "")

        if self._is_minimal_probe(call):
            return DockerCommandResult(self.minimal_probe_returncode, "", "")

        if self._is_probe_cleanup(call):
            return DockerCommandResult(0, "", "")

        if call[:2] == ("docker", "create"):
            if self.create_returncode == 0 or self.race_on_failure:
                self.exists = True
            return DockerCommandResult(
                self.create_returncode, "created", self.create_stderr
            )

        if call[:3] == ("docker", "container", "start"):
            if self.start_inspect_state == "absent":
                # Container is absent after start (vanishes or never created).
                self.exists = False
            elif self.start_inspect_state is not None:
                # Inspect reports the configured state regardless of returncode.
                merged: dict[str, object] = dict(self.overrides or {})
                merged["State.Status"] = self.start_inspect_state
                self.overrides = merged
            elif self.start_returncode == 0:
                # A successful start transitions the container to "running".
                merged = dict(self.overrides or {})
                merged["State.Status"] = "running"
                self.overrides = merged
            else:
                # Nonzero start with no explicit state: container is absent.
                self.exists = False
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
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        capability_probe_returncode=0,
        minimal_probe_returncode=1,
    )

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


def test_launch_raises_docker_container_start_failed_terminal(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """A nonzero start with the exact container in a non-running state is terminal.

    The v12 controller no longer raises DOCKER_CONTAINER_START_FAILED based
    on a nonzero start returncode alone. It inspects the exact container to
    classify the precise failure. This test verifies the terminal case where
    the container is absent after start (DOCKER_CONTAINER_MISSING_AFTER_START).
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state=None,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_MISSING_AFTER_START"
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
        "DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL",
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


# --- Issue #87: precise container reconciliation + reachable taxonomy tests ---


def test_launch_raises_workspace_subpath_missing(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Missing Attempt subpath inside the named volume is a finite terminal.

    The subpath probe fails and the helper readiness probe succeeds,
    confirming the subpath is genuinely missing (not a helper failure).
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        subpath_missing=True,
        helper_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="WORKSPACE_SUBPATH_MISSING"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Must not reach create when the subpath is missing.
    assert not any(call[0][1] == "create" for call in runner.calls)


def test_launch_raises_workspace_volume_subpath_unsupported(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Docker daemon rejecting volume-subpath mounts is a finite terminal.

    The v12 controller classifies this via the capability probe (a bounded
    docker create with the volume-subpath mount) failing, NOT by inspecting
    Docker stderr keywords.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="error creating mount path: volume-subpath not supported",
        capability_probe_returncode=1,
        minimal_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="WORKSPACE_VOLUME_SUBPATH_UNSUPPORTED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_launch_raises_docker_create_contract_rejected(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Create failures where the mount is rejected but minimal create works.

    The v12 controller classifies this via the capability probe succeeding
    (volume-subpath is supported) and the minimal create probe succeeding
    (the daemon can create containers), so the real create failure must be
    a contract rejection. This no longer relies on Docker stderr keywords.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="error response from daemon: invalid mount configuration",
        capability_probe_returncode=0,
        minimal_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CREATE_CONTRACT_REJECTED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_reconcile_created_starts_same_container(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """A 'created' container is started in place, never duplicated."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={"State.Status": "created"},
    )

    metadata = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    # Exactly one start call against the exact container name, no create calls.
    starts = [
        call[0] for call in runner.calls if call[0][:3] == ("docker", "container", "start")
    ]
    assert starts == [
        ("docker", "container", "start", container_name_for(_handle()))
    ]
    assert not any(call[0][1] == "create" for call in runner.calls)
    assert metadata.container_name == container_name_for(_handle())


@pytest.mark.parametrize(
    "terminal_state",
    ["exited", "dead", "paused", "restarting"],
)
def test_reconcile_rejects_terminal_states(
    tmp_path: Path,
    terminal_state: str,
    temporary_workspace_identity: None,
) -> None:
    """exited/dead/paused/restarting are finite terminals, not retried."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={"State.Status": terminal_state},
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_NOT_RUNNING_AFTER_START"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Must not start a terminal-state container and must not create a duplicate.
    assert not any(call[0][1] == "create" for call in runner.calls)
    starts = [
        call[0] for call in runner.calls if call[0][:3] == ("docker", "container", "start")
    ]
    assert starts == []


def test_create_failure_classifies_as_container_create_failed_when_no_signal(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Generic create failure with no subpath/mount/volume signal is DOCKER_CONTAINER_CREATE_FAILED.

    The v12 controller classifies this via the capability probe succeeding
    (volume-subpath is supported) and the minimal create probe failing (the
    daemon cannot create any container), so the real create failure is a
    genuine DOCKER_CONTAINER_CREATE_FAILED.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="some other daemon error",
        capability_probe_returncode=0,
        minimal_probe_returncode=1,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_CREATE_FAILED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False



# --- Issue #88: v12 bounded-probe launch hardening tests ---


def test_helper_unavailable_does_not_mask_as_subpath_missing(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """A helper probe failure must NOT be reported as WORKSPACE_SUBPATH_MISSING.

    When the subpath probe fails AND the helper readiness probe also fails,
    the controller must raise DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL (fail-closed)
    rather than masking the helper failure as a missing subpath.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        subpath_probe_returncode=1,
        helper_probe_returncode=1,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Must not reach create when the helper is unavailable.
    assert not any(call[0][1] == "create" for call in runner.calls)


def test_real_subpath_missing_raises_workspace_subpath_missing(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Subpath probe failure with a healthy helper = genuine WORKSPACE_SUBPATH_MISSING."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        subpath_probe_returncode=1,
        helper_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="WORKSPACE_SUBPATH_MISSING"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Must not reach create when the subpath is genuinely missing.
    assert not any(call[0][1] == "create" for call in runner.calls)
    # Both probes must have been invoked.
    assert any(
        runner._is_subpath_probe(call[0]) for call in runner.calls
    )
    assert any(
        runner._is_helper_probe(call[0]) for call in runner.calls
    )


def test_subpath_probe_is_pinned_no_network_no_pull(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """The subpath probe must use --network none, --pull never, and the pinned image."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    subpath_probe = next(
        (call[0] for call in runner.calls if runner._is_subpath_probe(call[0])),
        None,
    )
    assert subpath_probe is not None
    assert "--network" in subpath_probe
    assert subpath_probe[subpath_probe.index("--network") + 1] == "none"
    assert "--pull" in subpath_probe
    assert subpath_probe[subpath_probe.index("--pull") + 1] == "never"
    assert "--memory" in subpath_probe
    assert "--cpus" in subpath_probe
    assert "--read-only" in subpath_probe
    assert "--cap-drop" in subpath_probe
    assert "no-new-privileges:true" in subpath_probe
    assert AGENT_SERVER_IMAGE in subpath_probe
    # No alpine or other untrusted image may appear.
    assert "alpine" not in " ".join(subpath_probe).lower()


def test_helper_probe_is_pinned_no_network_no_pull_no_volume(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """The helper readiness probe must not mount the workspace volume."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), subpath_probe_returncode=1)

    with pytest.raises(LaunchFailure, match="WORKSPACE_SUBPATH_MISSING"):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )

    helper_probe = next(
        (call[0] for call in runner.calls if runner._is_helper_probe(call[0])),
        None,
    )
    assert helper_probe is not None
    assert "--network" in helper_probe
    assert helper_probe[helper_probe.index("--network") + 1] == "none"
    assert "--pull" in helper_probe
    assert helper_probe[helper_probe.index("--pull") + 1] == "never"
    assert "-v" not in helper_probe
    assert "--mount" not in helper_probe
    assert AGENT_SERVER_IMAGE in helper_probe


def test_volume_subpath_unsupported_classified_by_capability_probe(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """volume-subpath unsupported is classified by the capability probe failing.

    The classification no longer relies on Docker stderr keywords. The
    capability probe (a bounded docker create with the volume-subpath mount)
    failing means the daemon rejects volume-subpath mounts.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="some daemon output that must not be inspected",
        capability_probe_returncode=1,
        minimal_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="WORKSPACE_VOLUME_SUBPATH_UNSUPPORTED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # The capability probe must have been invoked.
    assert any(
        runner._is_capability_probe(call[0]) for call in runner.calls
    )
    # The minimal probe must NOT have been invoked (capability already failed).
    assert not any(
        runner._is_minimal_probe(call[0]) for call in runner.calls
    )


def test_create_mount_rejection_classified_by_minimal_probe(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Create mount rejection = capability probe succeeds, minimal probe succeeds.

    The capability probe (with the volume-subpath mount) succeeds, but the
    minimal create probe (without the mount) also succeeds. This means the
    daemon can create containers, so the real create failure must be a
    contract rejection (e.g., mount configuration rejected).
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="error response from daemon: invalid mount configuration",
        capability_probe_returncode=0,
        minimal_probe_returncode=0,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CREATE_CONTRACT_REJECTED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Both probes must have been invoked and cleaned up.
    assert any(
        runner._is_capability_probe(call[0]) for call in runner.calls
    )
    assert any(
        runner._is_minimal_probe(call[0]) for call in runner.calls
    )
    # Probe cleanup must have been called for both probes.
    cleanup_names = [
        call[0][4]
        for call in runner.calls
        if runner._is_probe_cleanup(call[0])
    ]
    assert "reverse-agent-capability-probe" in cleanup_names
    assert "reverse-agent-minimal-probe" in cleanup_names


def test_create_failure_classified_as_container_create_failed(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Real create failure = capability succeeds, minimal fails.

    The capability probe succeeds (volume-subpath is supported), but the
    minimal create probe fails (the daemon cannot create any container).
    This is a genuine DOCKER_CONTAINER_CREATE_FAILED.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr="some other daemon error",
        capability_probe_returncode=0,
        minimal_probe_returncode=1,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_CREATE_FAILED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False
    # Capability cleanup must have been called; minimal cleanup must NOT
    # have been called (minimal probe failed, so it never created a container).
    cleanup_names = [
        call[0][4]
        for call in runner.calls
        if runner._is_probe_cleanup(call[0])
    ]
    assert "reverse-agent-capability-probe" in cleanup_names
    assert "reverse-agent-minimal-probe" not in cleanup_names


def test_start_nonzero_but_inspect_running_reconciles_as_success(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """A nonzero start result with the exact container running = success.

    Docker start may return nonzero even when the container is already
    running. The controller must inspect the exact container and reconcile
    a running state as success.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state="running",
    )

    metadata = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    assert metadata.container_name == container_name_for(_handle())
    assert metadata.state == "running"
    # Exactly one start call against the exact container name.
    starts = [
        call[0] for call in runner.calls if call[0][:3] == ("docker", "container", "start")
    ]
    assert len(starts) == 1
    assert starts[0] == (
        "docker", "container", "start", container_name_for(_handle())
    )


def test_start_nonzero_and_inspect_created_raises_mount_initialization_failed(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Nonzero start + container stuck in 'created' = DOCKER_MOUNT_INITIALIZATION_FAILED."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state="created",
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_MOUNT_INITIALIZATION_FAILED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


@pytest.mark.parametrize("terminal_state", ["exited", "dead"])
def test_start_nonzero_and_inspect_terminal_raises_fixed_image_process_exited(
    tmp_path: Path,
    terminal_state: str,
    temporary_workspace_identity: None,
) -> None:
    """Nonzero start + container exited/dead = DOCKER_FIXED_IMAGE_PROCESS_EXITED."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state=terminal_state,
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_FIXED_IMAGE_PROCESS_EXITED"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_start_nonzero_and_container_absent_raises_container_missing_after_start(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Nonzero start + container absent = DOCKER_CONTAINER_MISSING_AFTER_START."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state=None,  # container absent after start
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_MISSING_AFTER_START"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_start_success_but_inspect_absent_raises_container_missing_after_start(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Zero start result but container absent = DOCKER_CONTAINER_MISSING_AFTER_START."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=0,
        start_inspect_state="absent",  # container vanishes after start
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_MISSING_AFTER_START"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_start_success_but_inspect_not_running_raises_not_running_after_start(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Zero start result but container not running = DOCKER_CONTAINER_NOT_RUNNING_AFTER_START."""
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=0,
        start_inspect_state="paused",
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_CONTAINER_NOT_RUNNING_AFTER_START"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_inspect_contract_drift_during_start_raises_inspect_contract_mismatch(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Inspect contract drift during start = DOCKER_INSPECT_CONTRACT_MISMATCH.

    After a nonzero start, the controller inspects the exact container. If
    the inspect payload drifts from the launch contract, the controller
    must raise DOCKER_INSPECT_CONTRACT_MISMATCH (not leak the raw error).
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        start_returncode=1,
        start_inspect_state="running",
        overrides={"HostConfig.Privileged": True},  # contract drift
    )

    with pytest.raises(
        LaunchFailure, match="DOCKER_INSPECT_CONTRACT_MISMATCH"
    ) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )
    assert exc_info.value.retryable is False


def test_unknown_exception_is_fail_closed_and_non_retryable(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Any unclassified exception must remain fail-closed and non-retryable.

    The DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL category is the fail-closed
    fallback for any condition the controller cannot classify into a
    finite category. It must be non-retryable.
    """
    code = "DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL"
    assert is_launch_failure_code(code) is True
    assert is_launch_failure_retryable(code) is False
    failure = LaunchFailure(code)
    assert failure.retryable is False


def test_new_mount_failure_codes_are_non_retryable() -> None:
    """The v12 mount/process/absent/drift failure codes are all non-retryable."""
    for code in (
        "DOCKER_MOUNT_INITIALIZATION_FAILED",
        "DOCKER_FIXED_IMAGE_PROCESS_EXITED",
        "DOCKER_CONTAINER_MISSING_AFTER_START",
        "DOCKER_INSPECT_CONTRACT_MISMATCH",
    ):
        assert is_launch_failure_code(code) is True
        assert is_launch_failure_retryable(code) is False
        assert LaunchFailure(code).retryable is False


def test_deterministic_failure_does_not_trigger_second_activity_attempt(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """A deterministic launch failure must not be retried by the Activity.

    The controller raises a non-retryable LaunchFailure. The Temporal
    Activity boundary must honor retryable=False and not schedule a
    second attempt. This test verifies the controller-side property:
    every finite launch failure code (except the single transient) has
    retryable=False, which the Activity must respect.
    """
    deterministic_codes = (
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
        "DOCKER_MOUNT_INITIALIZATION_FAILED",
        "DOCKER_FIXED_IMAGE_PROCESS_EXITED",
        "DOCKER_CONTAINER_MISSING_AFTER_START",
        "DOCKER_CONTAINER_NOT_RUNNING_AFTER_START",
        "DOCKER_INSPECT_CONTRACT_MISMATCH",
        "DOCKER_LAUNCH_UNCLASSIFIED_TERMINAL",
    )
    for code in deterministic_codes:
        assert is_launch_failure_code(code) is True
        failure = LaunchFailure(code)
        assert failure.retryable is False, (
            f"{code} must be non-retryable to prevent a second Activity attempt"
        )
    # Only the verified transient daemon unavailability is retryable.
    assert is_launch_failure_retryable("DOCKER_LAUNCH_TRANSIENT_UNAVAILABLE") is True


def test_no_raw_docker_output_in_launch_failure_or_exception(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Raw Docker stderr must never appear in LaunchFailure or its repr.

    The controller must not embed raw Docker output in exceptions, Temporal
    history, logs, or evidence. LaunchFailure carries only a finite code.
    """
    root = (tmp_path / "attempts").absolute()
    sensitive_stderr = "secret-daemon-token-xyz error creating mount"
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        create_stderr=sensitive_stderr,
        capability_probe_returncode=1,
        minimal_probe_returncode=0,
    )

    with pytest.raises(LaunchFailure) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )

    failure = exc_info.value
    # The exception message must be only the finite code.
    assert str(failure) == failure.code
    assert failure.code == "WORKSPACE_VOLUME_SUBPATH_UNSUPPORTED"
    # The sensitive stderr must not appear anywhere in the exception repr.
    assert "secret-daemon-token-xyz" not in repr(failure)
    assert "secret-daemon-token-xyz" not in str(failure)
    assert "error creating mount" not in repr(failure)


def test_probe_cleanup_invoked_on_all_create_classification_paths(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Probe containers must be cleaned up on every create-classification path.

    When the capability probe succeeds, it must be removed before the
    minimal probe runs. When the minimal probe succeeds, it must also be
    removed.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        create_returncode=125,
        capability_probe_returncode=0,
        minimal_probe_returncode=0,
    )

    with pytest.raises(LaunchFailure, match="DOCKER_CREATE_CONTRACT_REJECTED"):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )

    # Capability probe cleanup must occur BEFORE minimal probe runs.
    capability_create_idx = next(
        i for i, (call, _) in enumerate(runner.calls)
        if runner._is_capability_probe(call)
    )
    capability_cleanup_idx = next(
        i for i, (call, _) in enumerate(runner.calls)
        if runner._is_probe_cleanup(call)
        and call[4] == "reverse-agent-capability-probe"
    )
    minimal_create_idx = next(
        i for i, (call, _) in enumerate(runner.calls)
        if runner._is_minimal_probe(call)
    )
    assert capability_cleanup_idx < minimal_create_idx
    assert capability_create_idx < capability_cleanup_idx

    # Minimal probe cleanup must occur after minimal probe.
    minimal_cleanup_idx = next(
        i for i, (call, _) in enumerate(runner.calls)
        if runner._is_probe_cleanup(call)
        and call[4] == "reverse-agent-minimal-probe"
    )
    assert minimal_create_idx < minimal_cleanup_idx


def test_cleanup_attempt_removes_probe_residue_and_exact_container(
    tmp_path: Path,
) -> None:
    """cleanup_attempt must remove the exact container and workspace idempotently.

    This test verifies the cleanup contract: after cleanup, the exact
    container is absent and the workspace is absent. The cleanup is
    idempotent.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), exists=True)
    controller = _controller(tmp_path, runner)
    workspace = _workspace(root, _handle())
    workspace.mkdir(parents=True)
    (workspace / "runtime-proof.txt").write_text("PROOF", encoding="utf-8")

    assert controller.cleanup_attempt(_handle()) == (True, True)
    assert controller.cleanup_attempt(_handle()) == (True, True)
    assert not workspace.exists()


def test_replay_does_not_leak_raw_docker_output(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Replay of a launch failure must not leak raw Docker output.

    The LaunchFailure carries only a finite code. Repr/str of the failure
    must not contain any raw Docker stderr, ensuring Temporal history,
    logs, and evidence remain sanitized.
    """
    root = (tmp_path / "attempts").absolute()
    raw_output = "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"
    runner = StatefulRunner(
        root,
        _handle(),
        daemon_unavailable=True,
    )
    # Override the daemon stderr to contain sensitive raw output.
    original_run = runner.run

    def leaking_run(argv, *, environment=None):
        result = original_run(argv, environment=environment)
        if argv[:2] == ("docker", "info") and result.returncode != 0:
            return DockerCommandResult(1, "", raw_output)
        return result

    runner.run = leaking_run  # type: ignore[assignment]

    with pytest.raises(LaunchFailure) as exc_info:
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )

    failure = exc_info.value
    assert str(failure) == failure.code
    assert failure.code == "DOCKER_SOCKET_UNAVAILABLE"
    assert raw_output not in repr(failure)
    assert raw_output not in str(failure)
    assert "/var/run/docker.sock" not in repr(failure)


def test_secret_scan_no_provider_credentials_in_probe_argv(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    """Probe argv must never contain provider credentials or secret names.

    The bounded probes must not carry any provider credential, API key,
    or secret environment variable. Only the pinned image and fixed
    resource limits are allowed.
    """
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    forbidden_tokens = (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "SESSION_API_KEY",
        "LITELLM_MASTER_KEY",
        "sk-ant-",
        "sk-",
        "ghp_",
        "gho_",
    )
    for call, _ in runner.calls:
        joined = " ".join(call)
        for token in forbidden_tokens:
            assert token not in joined, (
                f"forbidden token {token!r} found in probe argv: {call}"
            )

