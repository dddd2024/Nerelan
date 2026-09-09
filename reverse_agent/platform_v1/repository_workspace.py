"""Repository workspace identity validation for trusted-host single-source mode.

Resolves REVERSE_AGENT_REPO_DIR as a local Git repository, derives its
configured origin identity via bounded local Git commands, normalizes
ordinary GitHub HTTPS/SSH transport syntax to ``owner/repo``, and compares
that identity with the Goal/Task ``repository`` field.

Fail-closed: missing source, invalid Git repository, missing/unsupported
origin, or identity mismatch produces stable sanitized failures.
"""

from __future__ import annotations

import os
import re
import subprocess

_GITHUB_ORIGIN_RE = re.compile(
    r"(?:https://|ssh://git@|git@)github\.com[/:]"
    r"([^/:]+)/([^/\s]+?)(?:\.git)?$"
)


class RepositoryWorkspaceError(Exception):
    """Base for repository workspace identity failures."""

    code = "error"


class RepositoryWorkspaceUnconfigured(RepositoryWorkspaceError):
    """REVERSE_AGENT_REPO_DIR is missing or empty."""

    code = "unconfigured"


class RepositoryWorkspaceInvalid(RepositoryWorkspaceError):
    """The source path does not exist or is not a Git repository."""

    code = "invalid"


class RepositoryWorkspaceIdentityUnavailable(RepositoryWorkspaceError):
    """Cannot determine the origin identity of the Git repository."""

    code = "identity_unavailable"


class RepositoryWorkspaceMismatch(RepositoryWorkspaceError):
    """Origin identity does not match the expected repository."""

    code = "mismatch"


def normalize_github_origin(url: str) -> str:
    """Normalize a GitHub origin URL to ``owner/repo`` form.

    Handles:
        https://github.com/owner/repo.git
        https://github.com/owner/repo
        ssh://git@github.com/owner/repo.git
        ssh://git@github.com/owner/repo
        git@github.com:owner/repo.git
        git@github.com:owner/repo

    Returns ``""`` if the URL does not match ordinary GitHub syntax.
    """
    m = _GITHUB_ORIGIN_RE.fullmatch(url.strip())
    if not m:
        return ""
    return f"{m.group(1)}/{m.group(2)}"


def _git_repo_root(source_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=source_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _git_origin_url(repo_root: str) -> str:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def resolve_repository_identity(source_dir: str) -> str:
    """Resolve the normalized ``owner/repo`` identity of a Git repository.

    Raises :class:`RepositoryWorkspaceInvalid` if the source is not a Git
    repository and :class:`RepositoryWorkspaceIdentityUnavailable` if the
    origin cannot be determined or is not in supported GitHub syntax.
    """
    repo_root = _git_repo_root(source_dir)
    if not repo_root:
        raise RepositoryWorkspaceInvalid()
    origin_url = _git_origin_url(repo_root)
    if not origin_url:
        raise RepositoryWorkspaceIdentityUnavailable()
    identity = normalize_github_origin(origin_url)
    if not identity:
        raise RepositoryWorkspaceIdentityUnavailable()
    return identity


def validate_repository_workspace(repository: str) -> None:
    """Validate that ``REVERSE_AGENT_REPO_DIR`` origin matches *repository*.

    This is the primary entry point called by goal_service, task_execution,
    and durable_execution before any executor creation or worktree
    preparation.
    """
    source_dir = os.environ.get("REVERSE_AGENT_REPO_DIR", "").strip()
    if not source_dir:
        raise RepositoryWorkspaceUnconfigured()
    if not os.path.isdir(source_dir):
        raise RepositoryWorkspaceInvalid()
    actual = resolve_repository_identity(source_dir)
    if actual != repository:
        raise RepositoryWorkspaceMismatch()
