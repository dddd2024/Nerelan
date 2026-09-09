"""Fail-closed binding between one trusted SourceDir and Task/Goal repository identity.

The current Platform V1 product mode has exactly one configured source workspace,
provided by ``REVERSE_AGENT_REPO_DIR``.  This module deliberately does not search
for repositories, clone/fetch/pull, rewrite remotes, or create worktrees.  It only
proves that the configured local Git repository's ``origin`` identifies the same
``owner/repo`` requested by a Goal/Task before the existing executor/worktree stack
is allowed to continue.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping, Sequence
from urllib.parse import urlsplit


_REPOSITORY_TOKEN = re.compile(r"^[A-Za-z0-9_.-]+$")
_GIT_OUTPUT_LIMIT = 4096
_GIT_TIMEOUT_SECONDS = 5.0


class RepositoryWorkspaceError(RuntimeError):
    """Stable sanitized fail-closed repository/workspace classification."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RepositoryWorkspaceBinding:
    """One proven local workspace bound to one Task/Goal repository identity."""

    repository: str
    repo_dir: Path


def _repository_identity(owner: str, repo: str) -> str:
    if not owner or not repo:
        raise ValueError("repository identity is incomplete")
    if not _REPOSITORY_TOKEN.fullmatch(owner) or not _REPOSITORY_TOKEN.fullmatch(repo):
        raise ValueError("repository identity contains unsupported characters")
    return f"{owner}/{repo}"


def normalize_repository_identity(value: str) -> str:
    """Validate an already-normalized Task/Goal ``owner/repo`` identity."""

    if not isinstance(value, str):
        raise ValueError("repository identity must be a string")
    normalized = value.strip()
    parts = normalized.split("/")
    if len(parts) != 2:
        raise ValueError("repository identity must use owner/repo form")
    return _repository_identity(parts[0], parts[1])


def normalize_github_origin(origin: str) -> str:
    """Normalize supported GitHub transport syntax to ``owner/repo``.

    This is syntax normalization only.  It performs no network lookup, redirect
    resolution, fuzzy matching, or historical repository-alias rewriting.
    """

    if not isinstance(origin, str):
        raise ValueError("origin must be a string")
    value = origin.strip()
    if not value or len(value) > _GIT_OUTPUT_LIMIT:
        raise ValueError("origin is missing or oversized")
    if any(char in value for char in ("\r", "\n", "\x00")):
        raise ValueError("origin contains unsupported control characters")

    path: str
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:") :]
        if not path:
            raise ValueError("origin path is missing")
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "ssh"}:
            raise ValueError("unsupported origin scheme")
        if (parsed.hostname or "").lower() != "github.com":
            raise ValueError("unsupported origin host")
        if parsed.query or parsed.fragment:
            raise ValueError("origin query/fragment is not supported")
        if parsed.scheme == "https" and (parsed.username or parsed.password):
            raise ValueError("credential-bearing origin is not supported")
        if parsed.scheme == "ssh" and parsed.username not in {None, "git"}:
            raise ValueError("unsupported SSH origin user")
        path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2:
        raise ValueError("origin must identify exactly one owner/repo")
    return _repository_identity(parts[0], parts[1])


def _run_git(repo_dir: Path, args: Sequence[str]) -> str:
    """Run one bounded read-only Git command and return bounded stdout."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_dir), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RepositoryWorkspaceError("repository_workspace_invalid") from exc
    if completed.returncode != 0:
        raise RepositoryWorkspaceError("repository_workspace_invalid")
    stdout = completed.stdout.strip()
    if not stdout or len(stdout) > _GIT_OUTPUT_LIMIT:
        raise RepositoryWorkspaceError("repository_workspace_identity_unavailable")
    return stdout


def resolve_repository_workspace(
    expected_repository: str,
    *,
    source_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> RepositoryWorkspaceBinding:
    """Prove the configured SourceDir is the requested repository or fail closed.

    ``source_dir`` exists for deterministic trusted-host callers/tests.  When it
    is absent, the only accepted source is ``REVERSE_AGENT_REPO_DIR``.  Caller
    CWD is never used as a fallback.
    """

    if source_dir is None:
        environment = os.environ if environ is None else environ
        configured = str(environment.get("REVERSE_AGENT_REPO_DIR", "")).strip()
        if not configured:
            raise RepositoryWorkspaceError("repository_workspace_unconfigured")
        source_dir = configured

    raw_path = str(source_dir).strip()
    if not raw_path:
        raise RepositoryWorkspaceError("repository_workspace_unconfigured")
    try:
        candidate = Path(raw_path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RepositoryWorkspaceError("repository_workspace_invalid") from exc
    if not candidate.is_dir():
        raise RepositoryWorkspaceError("repository_workspace_invalid")

    try:
        expected = normalize_repository_identity(expected_repository)
    except ValueError as exc:
        raise RepositoryWorkspaceError("repository_workspace_mismatch") from exc

    try:
        top_level = _run_git(candidate, ("rev-parse", "--show-toplevel"))
        root = Path(top_level).resolve(strict=True)
    except RepositoryWorkspaceError:
        raise
    except (OSError, RuntimeError) as exc:
        raise RepositoryWorkspaceError("repository_workspace_invalid") from exc
    if not root.is_dir():
        raise RepositoryWorkspaceError("repository_workspace_invalid")

    try:
        origin = _run_git(root, ("config", "--get", "remote.origin.url"))
        discovered = normalize_github_origin(origin)
    except RepositoryWorkspaceError as exc:
        if exc.code == "repository_workspace_invalid":
            raise RepositoryWorkspaceError(
                "repository_workspace_identity_unavailable"
            ) from exc
        raise
    except ValueError as exc:
        raise RepositoryWorkspaceError(
            "repository_workspace_identity_unavailable"
        ) from exc

    if discovered != expected:
        raise RepositoryWorkspaceError("repository_workspace_mismatch")

    return RepositoryWorkspaceBinding(repository=discovered, repo_dir=root)
