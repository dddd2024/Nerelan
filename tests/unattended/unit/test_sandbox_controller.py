from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

import pytest

from reverse_agent.unattended import (
    AGENT_SERVER_DIGEST,
    AGENT_SERVER_IMAGE,
    ATTEMPT_WORKSPACE_DESTINATION,
    FIXED_LAUNCH_SPEC,
    DockerCommandResult,
    ExecutionHandle,
    FixedLaunchSpec,
    SandboxController,
    SandboxControllerError,
    container_name_for,
    executor_id,
    workspace_id,
    workspace_path,
)

_NETWORK = "issue81_model-executor"
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
        },
        "State": {"Status": "running"},
        "Mounts": [
            {
                "Type": "bind",
                "Source": str(_workspace(root, handle)),
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
    ) -> None:
        self.root = root
        self.handle = handle
        self.exists = exists
        self.create_returncode = create_returncode
        self.race_on_failure = race_on_failure
        self.overrides = overrides
        self.calls: list[tuple[tuple[str, ...], Mapping[str, str] | None]] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str] | None = None,
    ) -> DockerCommandResult:
        call = tuple(argv)
        self.calls.append((call, environment))
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
        if call[:2] == ("docker", "run"):
            if self.create_returncode == 0 or self.race_on_failure:
                self.exists = True
            return DockerCommandResult(self.create_returncode, "created", "")
        if call[:4] == ("docker", "container", "rm", "--force"):
            self.exists = False
            return DockerCommandResult(0, "", "")
        raise AssertionError(call)


def _controller(
    tmp_path: Path,
    runner: StatefulRunner,
) -> SandboxController:
    return SandboxController(
        runner,
        host_workspace_root=(tmp_path / "attempts").absolute(),
        executor_network=_NETWORK,
    )


def test_container_name_is_deterministic_per_attempt() -> None:
    assert container_name_for(_handle()) == container_name_for(_handle())
    assert container_name_for(_handle()) != container_name_for(_handle(2))
    assert container_name_for(_handle()).startswith("reverse-agent-attempt-")


def test_launch_uses_only_fixed_argv_and_sanitized_metadata(tmp_path: Path) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle())

    metadata = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    launch, environment = next(call for call in runner.calls if call[0][1] == "run")
    assert launch[0:2] == ("docker", "run")
    assert AGENT_SERVER_IMAGE in launch
    assert ("--cap-drop", "ALL") == launch[
        launch.index("--cap-drop") : launch.index("--cap-drop") + 2
    ]
    assert "no-new-privileges:true" in launch
    assert "/var/run/docker.sock" not in " ".join(launch)
    assert "SESSION_API_KEY" not in launch
    assert launch[launch.index("--host") + 1] == "127.0.0.1"
    assert environment is None
    assert metadata.image_digest == AGENT_SERVER_DIGEST
    assert metadata.workspace_destination == ATTEMPT_WORKSPACE_DESTINATION
    assert metadata.network_name == _NETWORK
    assert metadata.privileged is False
    assert metadata.no_new_privileges is True
    assert metadata.read_only_rootfs is True
    assert "SESSION_API_KEY" not in repr(metadata)


def test_reconcile_existing_never_creates_duplicate(tmp_path: Path) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), exists=True)

    first = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )
    second = _controller(tmp_path, runner).launch_or_reconcile(
        _handle(), FIXED_LAUNCH_SPEC
    )

    assert first == second
    assert not any(call[0][1] == "run" for call in runner.calls)


def test_create_conflict_reconciles_exact_existing_container(tmp_path: Path) -> None:
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
    assert sum(call[0][1] == "run" for call in runner.calls) == 1


def test_failed_create_without_reconciled_container_is_sanitized(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(root, _handle(), create_returncode=125)

    with pytest.raises(
        SandboxControllerError, match="docker_container_create_failed"
    ):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )


def test_reconcile_rejects_nonrunning_container(tmp_path: Path) -> None:
    root = (tmp_path / "attempts").absolute()
    runner = StatefulRunner(
        root,
        _handle(),
        exists=True,
        overrides={"State.Status": "exited"},
    )

    with pytest.raises(SandboxControllerError, match="not_running"):
        _controller(tmp_path, runner).launch_or_reconcile(
            _handle(), FIXED_LAUNCH_SPEC
        )


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
