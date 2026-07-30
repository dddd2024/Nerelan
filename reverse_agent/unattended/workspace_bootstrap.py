"""One-shot trusted provisioning for the fixed workspace volume root."""

from __future__ import annotations

import os
import stat

from .workspace import (
    WORKSPACE_ROOT,
    WORKSPACE_ROOT_GID,
    WORKSPACE_ROOT_IDENTITY_CONTENT,
    WORKSPACE_ROOT_IDENTITY_MARKER,
    WORKSPACE_ROOT_MODE,
    WORKSPACE_ROOT_UID,
)


def provision_fixed_workspace_root() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("workspace_bootstrap_requires_root")
    if WORKSPACE_ROOT.is_symlink():
        raise RuntimeError("workspace_root_symlink_rejected")
    if not WORKSPACE_ROOT.exists() or not WORKSPACE_ROOT.is_dir():
        raise RuntimeError("workspace_root_missing_or_not_directory")
    os.chown(WORKSPACE_ROOT, WORKSPACE_ROOT_UID, WORKSPACE_ROOT_GID)
    WORKSPACE_ROOT.chmod(WORKSPACE_ROOT_MODE)
    marker = WORKSPACE_ROOT / WORKSPACE_ROOT_IDENTITY_MARKER
    if marker.is_symlink():
        raise RuntimeError("workspace_marker_symlink_rejected")
    descriptor = os.open(
        marker,
        os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
        0o400,
    )
    try:
        os.write(descriptor, WORKSPACE_ROOT_IDENTITY_CONTENT.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chown(marker, WORKSPACE_ROOT_UID, WORKSPACE_ROOT_GID)
    marker.chmod(0o400)
    observed = WORKSPACE_ROOT.stat()
    if (
        observed.st_uid,
        observed.st_gid,
        stat.S_IMODE(observed.st_mode),
    ) != (WORKSPACE_ROOT_UID, WORKSPACE_ROOT_GID, WORKSPACE_ROOT_MODE):
        raise RuntimeError("workspace_root_identity_mismatch")


def main() -> int:
    provision_fixed_workspace_root()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
