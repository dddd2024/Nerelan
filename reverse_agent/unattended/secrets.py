"""Secret-safe provider file validation for the disposable audit stack."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any


def provider_secret_preflight(
    secret_file: str | os.PathLike[str] | None,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Validate the external provider file without reading or identifying it."""

    return _external_secret_file_preflight(
        secret_file,
        repository_root=repository_root,
        presence_field="provider_secret",
    )


def executor_key_secret_preflight(
    secret_file: str | os.PathLike[str] | None,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Validate the external bounded executor-key file without reading it."""

    return _external_secret_file_preflight(
        secret_file,
        repository_root=repository_root,
        presence_field="executor_key",
    )


def _external_secret_file_preflight(
    secret_file: str | os.PathLike[str] | None,
    *,
    repository_root: Path,
    presence_field: str,
) -> dict[str, Any]:
    checks = {
        "regular_file": "FAIL",
        "outside_repository": "FAIL",
        "permissions_0600": "FAIL",
    }
    if not secret_file:
        return {
            "status": "FAIL",
            presence_field: "MISSING",
            "checks": checks,
        }

    candidate = Path(secret_file).expanduser()
    if not candidate.is_absolute() or not candidate.exists():
        return {
            "status": "FAIL",
            presence_field: "MISSING",
            "checks": checks,
        }

    try:
        repository = repository_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        outside_repository = not resolved.is_relative_to(repository)
        regular_file = candidate.is_file() and not candidate.is_symlink()
        mode_is_0600 = _strict_posix_permissions(
            os.name,
            stat.S_IMODE(candidate.stat().st_mode),
        )
    except OSError:
        return {
            "status": "FAIL",
            presence_field: "MISSING",
            "checks": checks,
        }

    checks = {
        "regular_file": "PASS" if regular_file else "FAIL",
        "outside_repository": "PASS" if outside_repository else "FAIL",
        "permissions_0600": "PASS" if mode_is_0600 else "FAIL",
    }
    return {
        "status": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
        presence_field: "PRESENT",
        "checks": checks,
    }


def _strict_posix_permissions(platform_name: str, observed_mode: int) -> bool:
    return platform_name == "posix" and observed_mode == 0o600
