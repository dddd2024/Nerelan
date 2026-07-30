from __future__ import annotations

import inspect
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import reverse_agent.unattended.workspace as workspace_module

from reverse_agent.unattended import (
    ExecutionHandle,
    FIXED_LAUNCH_SPEC,
    SandboxController,
    WorkspacePreflightError,
    WorkspaceRootManager,
    executor_id,
    workspace_id,
)
from reverse_agent.unattended.activities.gate2 import (
    launch_or_reconcile_attempt,
    workspace_root_preflight,
)
from reverse_agent.unattended.workspace import (
    ATTEMPT_DIRECTORY_MODE,
    WORKSPACE_ROOT_IDENTITY_CONTENT,
    WORKSPACE_ROOT_IDENTITY_MARKER,
    WORKSPACE_ROOT_MODE,
    _mode_matches_policy,
    _owner_matches_policy,
)

_VOLUME = "issue85_attempt-workspaces"
_NETWORK = "issue85_model-executor"


@pytest.fixture
def temporary_workspace_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name == "posix":
        monkeypatch.setattr(workspace_module, "WORKSPACE_ROOT_UID", os.geteuid())
        monkeypatch.setattr(workspace_module, "WORKSPACE_ROOT_GID", os.getegid())


def _handle() -> ExecutionHandle:
    identifier = "unattended:dddd2024/reverse-agent:issue:85-unit"
    return ExecutionHandle(
        identifier,
        1,
        workspace_id(identifier),
        executor_id(identifier, 1),
        "2026-07-30T06:00:00+00:00",
    )


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    root.chmod(WORKSPACE_ROOT_MODE)
    (root / WORKSPACE_ROOT_IDENTITY_MARKER).write_text(
        WORKSPACE_ROOT_IDENTITY_CONTENT,
        encoding="utf-8",
    )
    return root


def test_fresh_and_restart_preflight_are_idempotent(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    manager = WorkspaceRootManager(_root(tmp_path), volume_name=_VOLUME)

    first = manager.preflight(_handle())
    second = manager.preflight(_handle())

    assert first == second
    assert first.source_kind == "volume"
    assert first.controller_atomic_probe
    assert first.attempt_directory_provisioned
    assert first.agent_exact_attempt_write
    assert first.agent_root_denied
    assert first.agent_sibling_denied
    assert first.agent_outside_denied
    assert first.host_controller_identity_match
    assert manager.attempt_path(_handle()).is_dir()


def test_concurrent_same_handle_provisions_one_directory(
    tmp_path: Path,
    temporary_workspace_identity: None,
) -> None:
    manager = WorkspaceRootManager(_root(tmp_path), volume_name=_VOLUME)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(lambda _: manager.preflight(_handle()), range(2)))

    assert all(item.attempt_directory_provisioned for item in results)
    assert manager.attempt_path(_handle()).is_dir()


@pytest.mark.parametrize(
    ("setup", "category"),
    [
        ("missing", "WORKSPACE_ROOT_MISSING"),
        ("file", "WORKSPACE_ROOT_NOT_DIRECTORY"),
    ],
)
def test_preflight_returns_finite_root_failures(
    tmp_path: Path,
    setup: str,
    category: str,
) -> None:
    root = tmp_path / "root"
    if setup == "file":
        root.write_text("not-a-directory", encoding="utf-8")
    elif setup != "missing":
        root.mkdir()
        root.chmod(WORKSPACE_ROOT_MODE)
        if setup == "marker_wrong":
            (root / WORKSPACE_ROOT_IDENTITY_MARKER).write_text(
                "wrong\n",
                encoding="utf-8",
            )
    manager = WorkspaceRootManager(root, volume_name=_VOLUME)

    with pytest.raises(WorkspacePreflightError, match=category):
        manager.preflight(_handle())


@pytest.mark.parametrize("setup", ["marker_missing", "marker_wrong"])
def test_preflight_returns_finite_marker_failures(
    tmp_path: Path,
    temporary_workspace_identity: None,
    setup: str,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    root.chmod(WORKSPACE_ROOT_MODE)
    if setup == "marker_wrong":
        (root / WORKSPACE_ROOT_IDENTITY_MARKER).write_text(
            "wrong\n",
            encoding="utf-8",
        )
    manager = WorkspaceRootManager(root, volume_name=_VOLUME)

    with pytest.raises(
        WorkspacePreflightError,
        match="WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH",
    ):
        manager.preflight(_handle())


def test_symlink_root_is_terminal_when_supported(tmp_path: Path) -> None:
    target = _root(tmp_path)
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink unavailable")
    manager = WorkspaceRootManager(link, volume_name=_VOLUME)

    with pytest.raises(
        WorkspacePreflightError,
        match="WORKSPACE_ROOT_SYMLINK_REJECTED",
    ):
        manager.preflight(_handle())


def test_posix_owner_and_mode_policy_is_exact_and_non_world_writable() -> None:
    assert _owner_matches_policy(10001, 10001, platform_name="posix")
    assert not _owner_matches_policy(0, 0, platform_name="posix")
    assert _mode_matches_policy(0o750, platform_name="posix")
    assert not _mode_matches_policy(0o777, platform_name="posix")
    assert WORKSPACE_ROOT_MODE & 0o002 == 0
    assert ATTEMPT_DIRECTORY_MODE == 0o700


class NoDockerRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv, **kwargs):
        self.calls.append(tuple(argv))
        raise AssertionError("docker_must_not_run_after_failed_preflight")


def test_failed_preflight_stops_before_docker_launch(tmp_path: Path) -> None:
    runner = NoDockerRunner()
    controller = SandboxController(
        runner,
        host_workspace_root=tmp_path / "missing",
        executor_network=_NETWORK,
        workspace_volume=_VOLUME,
    )

    with pytest.raises(
        WorkspacePreflightError,
        match="WORKSPACE_ROOT_MISSING",
    ):
        controller.launch_or_reconcile(_handle(), FIXED_LAUNCH_SPEC)
    assert runner.calls == []


def test_activities_preserve_finite_workspace_categories() -> None:
    preflight_source = inspect.getsource(workspace_root_preflight)
    launch_source = inspect.getsource(launch_or_reconcile_attempt)

    assert "WorkspacePreflightError" in preflight_source
    assert '"workspace_preflight"' in preflight_source
    assert "WorkspacePreflightError" in launch_source
    for category in (
        "WORKSPACE_ROOT_MISSING",
        "WORKSPACE_ROOT_NOT_DIRECTORY",
        "WORKSPACE_ROOT_SYMLINK_REJECTED",
        "WORKSPACE_ROOT_OWNER_MISMATCH",
        "WORKSPACE_ROOT_MODE_MISMATCH",
        "WORKSPACE_ROOT_NOT_WRITABLE",
        "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH",
        "ATTEMPT_DIRECTORY_PROVISION_FAILED",
    ):
        from reverse_agent.unattended.workspace import (
            WORKSPACE_PREFLIGHT_FAILURE_CODES,
        )

        assert category in WORKSPACE_PREFLIGHT_FAILURE_CODES
