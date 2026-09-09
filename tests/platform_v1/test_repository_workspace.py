from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from reverse_agent.platform_v1.repository_workspace import (
    RepositoryWorkspaceError,
    normalize_github_origin,
    normalize_repository_identity,
    resolve_repository_workspace,
)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    return completed.stdout.strip()


def _repo(tmp_path: Path, *, origin: str | None = "https://github.com/owner/A.git") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    if origin is not None:
        _git(repo, "remote", "add", "origin", origin)
    return repo


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com/owner/repo.git",
        "https://github.com/owner/repo",
        "ssh://git@github.com/owner/repo.git",
        "ssh://git@github.com/owner/repo",
        "git@github.com:owner/repo.git",
        "git@github.com:owner/repo",
    ],
)
def test_common_github_origin_forms_normalize_without_network(origin: str) -> None:
    assert normalize_github_origin(origin) == "owner/repo"


@pytest.mark.parametrize(
    "origin",
    [
        "https://gitlab.com/owner/repo.git",
        "https://user:secret@github.com/owner/repo.git",
        "ssh://other@github.com/owner/repo.git",
        "https://github.com/owner/repo/extra.git",
        "https://github.com/owner/repo.git?token=secret",
        "file:///tmp/repo",
        "owner/repo",
        "",
    ],
)
def test_unsupported_or_credential_bearing_origins_fail_closed(origin: str) -> None:
    with pytest.raises(ValueError):
        normalize_github_origin(origin)


def test_task_goal_repository_identity_requires_exact_owner_repo_form() -> None:
    assert normalize_repository_identity("owner/repo") == "owner/repo"
    with pytest.raises(ValueError):
        normalize_repository_identity("https://github.com/owner/repo")
    with pytest.raises(ValueError):
        normalize_repository_identity("repo")


def test_matching_configured_repository_returns_proven_git_root(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    nested = repo / "nested"
    nested.mkdir()

    binding = resolve_repository_workspace("owner/A", source_dir=nested)

    assert binding.repository == "owner/A"
    assert binding.repo_dir == repo.resolve()


def test_repository_mismatch_is_stable_sanitized_and_precedes_fallback(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="git@github.com:owner/A.git")

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/B", source_dir=repo)

    assert caught.value.code == "repository_workspace_mismatch"
    assert str(caught.value) == "repository_workspace_mismatch"
    assert "github.com" not in str(caught.value)
    assert str(repo) not in str(caught.value)


def test_missing_configuration_never_falls_back_to_process_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", environ={})

    assert caught.value.code == "repository_workspace_unconfigured"


@pytest.mark.parametrize("kind", ["missing", "file", "directory"])
def test_invalid_source_directory_fails_closed(tmp_path: Path, kind: str) -> None:
    if kind == "missing":
        source = tmp_path / "does-not-exist"
    elif kind == "file":
        source = tmp_path / "plain-file"
        source.write_text("not a repository", encoding="utf-8")
    else:
        source = tmp_path / "plain-directory"
        source.mkdir()

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=source)

    assert caught.value.code == "repository_workspace_invalid"


def test_missing_origin_is_identity_unavailable(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin=None)

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=repo)

    assert caught.value.code == "repository_workspace_identity_unavailable"


def test_unsupported_origin_is_identity_unavailable_without_leaking_remote(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="https://example.invalid/secret-owner/secret-repo.git")

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=repo)

    assert caught.value.code == "repository_workspace_identity_unavailable"
    assert str(caught.value) == "repository_workspace_identity_unavailable"
    assert "secret-owner" not in str(caught.value)


def test_environment_binding_uses_only_reverse_agent_repo_dir(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="ssh://git@github.com/owner/A.git")
    environment = {
        "REVERSE_AGENT_REPO_DIR": str(repo),
        "UNRELATED_REPOSITORY": str(tmp_path / "other"),
    }

    binding = resolve_repository_workspace("owner/A", environ=environment)

    assert binding.repository == "owner/A"
    assert binding.repo_dir == repo.resolve()


def test_current_slug_is_not_rewritten_to_historical_alias(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="https://github.com/dddd2024/Nerelan.git")

    binding = resolve_repository_workspace("dddd2024/Nerelan", source_dir=repo)
    assert binding.repository == "dddd2024/Nerelan"

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("dddd2024/reverse-agent", source_dir=repo)
    assert caught.value.code == "repository_workspace_mismatch"
