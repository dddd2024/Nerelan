from __future__ import annotations

from dataclasses import asdict

import pytest

from reverse_agent.unattended.temporal_contracts import (
    WorkspaceRootPreflightResult,
)
from reverse_agent.unattended.workspace import (
    ATTEMPT_DIRECTORY_MODE,
    WORKSPACE_PREFLIGHT_FAILURE_CODES,
    WORKSPACE_ROOT_MODE,
    WorkspacePreflightError,
    _mode_matches_policy,
    _owner_matches_policy,
)


def _result() -> WorkspaceRootPreflightResult:
    return WorkspaceRootPreflightResult(
        source_kind="volume",
        root_uid=10001,
        root_gid=10001,
        root_mode=0o750,
        controller_uid=10001,
        controller_gid=10001,
        agent_uid=10001,
        agent_gid=10001,
        root_exists=True,
        root_is_directory=True,
        root_is_symlink=False,
        owner_matches_policy=True,
        mode_matches_policy=True,
        controller_atomic_probe=True,
        attempt_directory_provisioned=True,
        agent_exact_attempt_write=True,
        agent_root_denied=True,
        agent_sibling_denied=True,
        agent_outside_denied=True,
        host_controller_identity_match=True,
    )


def test_workspace_preflight_result_is_concrete_and_passing_only() -> None:
    result = _result()

    assert result.source_kind == "volume"
    assert result.root_mode == 0o750
    for name, value in asdict(result).items():
        assert isinstance(value, (str, int, bool)), name
    with pytest.raises(ValueError, match="must_pass"):
        WorkspaceRootPreflightResult(
            **{**asdict(result), "controller_atomic_probe": False}
        )


def test_workspace_failure_categories_are_finite() -> None:
    expected = {
        "WORKSPACE_ROOT_MISSING",
        "WORKSPACE_ROOT_NOT_DIRECTORY",
        "WORKSPACE_ROOT_SYMLINK_REJECTED",
        "WORKSPACE_ROOT_OWNER_MISMATCH",
        "WORKSPACE_ROOT_MODE_MISMATCH",
        "WORKSPACE_ROOT_NOT_WRITABLE",
        "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH",
        "ATTEMPT_DIRECTORY_PROVISION_FAILED",
    }

    assert WORKSPACE_PREFLIGHT_FAILURE_CODES == expected
    for category in expected:
        assert WorkspacePreflightError(category).code == category
    with pytest.raises(ValueError, match="invalid_workspace_preflight_code"):
        WorkspacePreflightError("ATTEMPT_LAUNCH_FAILED")


def test_posix_workspace_identity_policy_is_fixed_and_non_world_writable() -> None:
    assert _owner_matches_policy(10001, 10001, platform_name="posix")
    assert not _owner_matches_policy(0, 0, platform_name="posix")
    assert _mode_matches_policy(0o750, platform_name="posix")
    assert not _mode_matches_policy(0o777, platform_name="posix")
    assert WORKSPACE_ROOT_MODE == 0o750
    assert WORKSPACE_ROOT_MODE & 0o002 == 0
    assert ATTEMPT_DIRECTORY_MODE == 0o700
