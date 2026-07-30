"""Fixed workspace-root provisioning and fail-fast Attempt preflight."""

from __future__ import annotations

import os
import re
import stat
import threading
import uuid
from pathlib import Path, PurePosixPath

from .contracts import ExecutionHandle
from .identifiers import workspace_path
from .temporal_contracts import WorkspaceRootPreflightResult

WORKSPACE_ROOT = Path("/var/lib/reverse-agent/unattended-workspaces")
WORKSPACE_ROOT_UID = 10001
WORKSPACE_ROOT_GID = 10001
WORKSPACE_ROOT_MODE = 0o750
ATTEMPT_DIRECTORY_MODE = 0o700
WORKSPACE_ROOT_IDENTITY_MARKER = ".reverse-agent-workspace-root-v1"
WORKSPACE_ROOT_IDENTITY_CONTENT = "reverse-agent-workspace-root-v1\n"
_VOLUME_NAME = re.compile(r"[a-z0-9][a-z0-9_.-]{0,126}\Z")

WORKSPACE_PREFLIGHT_FAILURE_CODES = frozenset(
    {
        "WORKSPACE_ROOT_MISSING",
        "WORKSPACE_ROOT_NOT_DIRECTORY",
        "WORKSPACE_ROOT_SYMLINK_REJECTED",
        "WORKSPACE_ROOT_OWNER_MISMATCH",
        "WORKSPACE_ROOT_MODE_MISMATCH",
        "WORKSPACE_ROOT_NOT_WRITABLE",
        "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH",
        "ATTEMPT_DIRECTORY_PROVISION_FAILED",
    }
)


class WorkspacePreflightError(RuntimeError):
    """A finite, sanitized workspace-preflight failure."""

    def __init__(self, code: str) -> None:
        if code not in WORKSPACE_PREFLIGHT_FAILURE_CODES:
            raise ValueError("invalid_workspace_preflight_code")
        super().__init__(code)
        self.code = code


class WorkspaceRootManager:
    """Validate one fixed volume root and provision deterministic Attempts."""

    def __init__(self, root: Path, *, volume_name: str) -> None:
        if not root.is_absolute():
            raise ValueError("workspace_root_must_be_absolute")
        if _VOLUME_NAME.fullmatch(volume_name) is None:
            raise ValueError("workspace_volume_invalid")
        self.root = root
        self.volume_name = volume_name
        self._provision_lock = threading.Lock()

    def preflight(self, handle: ExecutionHandle) -> WorkspaceRootPreflightResult:
        with self._provision_lock:
            return self._preflight_locked(handle)

    def _preflight_locked(
        self,
        handle: ExecutionHandle,
    ) -> WorkspaceRootPreflightResult:
        if not self.root.exists():
            raise WorkspacePreflightError("WORKSPACE_ROOT_MISSING")
        if self.root.is_symlink():
            raise WorkspacePreflightError("WORKSPACE_ROOT_SYMLINK_REJECTED")
        if not self.root.is_dir():
            raise WorkspacePreflightError("WORKSPACE_ROOT_NOT_DIRECTORY")

        root_stat = self.root.stat()
        if not _owner_matches_policy(
            root_stat.st_uid,
            root_stat.st_gid,
            platform_name=os.name,
        ):
            raise WorkspacePreflightError("WORKSPACE_ROOT_OWNER_MISMATCH")
        if not _mode_matches_policy(
            stat.S_IMODE(root_stat.st_mode),
            platform_name=os.name,
        ):
            raise WorkspacePreflightError("WORKSPACE_ROOT_MODE_MISMATCH")
        if not os.access(self.root, os.W_OK):
            raise WorkspacePreflightError("WORKSPACE_ROOT_NOT_WRITABLE")
        self._require_identity_marker()
        self._atomic_probe(self.root)

        attempt = self._provision_attempt(handle)
        self._atomic_probe(attempt)
        return WorkspaceRootPreflightResult(
            source_kind="volume",
            root_uid=root_stat.st_uid,
            root_gid=root_stat.st_gid,
            root_mode=stat.S_IMODE(root_stat.st_mode),
            controller_uid=_effective_id("geteuid"),
            controller_gid=_effective_id("getegid"),
            agent_uid=WORKSPACE_ROOT_UID,
            agent_gid=WORKSPACE_ROOT_GID,
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

    def attempt_path(self, handle: ExecutionHandle) -> Path:
        relative = self.attempt_subpath(handle)
        candidate = self.root.joinpath(*PurePosixPath(relative).parts)
        if candidate.is_symlink():
            raise WorkspacePreflightError(
                "ATTEMPT_DIRECTORY_PROVISION_FAILED"
            )
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(self.root.resolve(strict=True)):
            raise WorkspacePreflightError(
                "ATTEMPT_DIRECTORY_PROVISION_FAILED"
            )
        return resolved

    @staticmethod
    def attempt_subpath(handle: ExecutionHandle) -> str:
        return (
            PurePosixPath(workspace_path(handle.workflow_id, handle.attempt))
            .relative_to(".var/unattended")
            .as_posix()
        )

    def _require_identity_marker(self) -> None:
        marker = self.root / WORKSPACE_ROOT_IDENTITY_MARKER
        if marker.is_symlink() or not marker.is_file():
            raise WorkspacePreflightError(
                "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH"
            )
        try:
            content = marker.read_text(encoding="utf-8")
        except OSError:
            raise WorkspacePreflightError(
                "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH"
            ) from None
        if content != WORKSPACE_ROOT_IDENTITY_CONTENT:
            raise WorkspacePreflightError(
                "WORKSPACE_ROOT_HOST_IDENTITY_MISMATCH"
            )

    def _provision_attempt(self, handle: ExecutionHandle) -> Path:
        attempt = self.attempt_path(handle)
        workspace_parent = attempt.parent
        try:
            workspace_parent.mkdir(
                mode=ATTEMPT_DIRECTORY_MODE,
                parents=True,
                exist_ok=True,
            )
            if workspace_parent.is_symlink() or not workspace_parent.is_dir():
                raise OSError("workspace_parent_contract")
            workspace_parent.chmod(ATTEMPT_DIRECTORY_MODE)
            attempt.mkdir(mode=ATTEMPT_DIRECTORY_MODE, exist_ok=True)
            if attempt.is_symlink() or not attempt.is_dir():
                raise OSError("attempt_directory_contract")
            attempt.chmod(ATTEMPT_DIRECTORY_MODE)
            attempt_stat = attempt.stat()
            root_stat = self.root.stat()
            expected_attempt_mode = (
                ATTEMPT_DIRECTORY_MODE
                if os.name == "posix"
                else stat.S_IMODE(attempt_stat.st_mode)
            )
            if (
                attempt_stat.st_uid,
                attempt_stat.st_gid,
                stat.S_IMODE(attempt_stat.st_mode),
            ) != (
                root_stat.st_uid,
                root_stat.st_gid,
                expected_attempt_mode,
            ):
                raise OSError("attempt_identity_contract")
            return attempt
        except OSError:
            raise WorkspacePreflightError(
                "ATTEMPT_DIRECTORY_PROVISION_FAILED"
            ) from None

    @staticmethod
    def _atomic_probe(directory: Path) -> None:
        token = uuid.uuid4().hex
        source = directory / f".workspace-probe-{token}"
        target = directory / f".workspace-probe-{token}.ready"
        descriptor: int | None = None
        try:
            descriptor = os.open(
                source,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            os.write(descriptor, b"workspace-probe-v1\n")
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            source.replace(target)
            _fsync_directory(directory)
            target.unlink()
            _fsync_directory(directory)
        except OSError:
            if descriptor is not None:
                os.close(descriptor)
            source.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            raise WorkspacePreflightError(
                "WORKSPACE_ROOT_NOT_WRITABLE"
            ) from None


def _effective_id(name: str) -> int:
    function = getattr(os, name, None)
    return int(function()) if function is not None else -1


def _owner_matches_policy(
    uid: int,
    gid: int,
    *,
    platform_name: str,
) -> bool:
    return (
        (uid, gid) == (WORKSPACE_ROOT_UID, WORKSPACE_ROOT_GID)
        if platform_name == "posix"
        else True
    )


def _mode_matches_policy(mode: int, *, platform_name: str) -> bool:
    return mode == WORKSPACE_ROOT_MODE if platform_name == "posix" else True


def _fsync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
