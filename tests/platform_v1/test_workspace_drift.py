from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from reverse_agent.platform_v1.workspace_drift import (
    AGENT_EXPECTED_MUTATION,
    EXTERNAL_LOCAL_MUTATION,
    NO_DRIFT,
    UNKNOWN_DIRTY_STATE,
    capture_workspace_generation,
    classify_workspace_generation,
)


def _run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        args,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.email", "drift@test.local")
    _run(repo, "git", "config", "user.name", "Drift Fixture")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _run(repo, "git", "add", "tracked.txt")
    _run(repo, "git", "commit", "-q", "-m", "base")
    return repo, _run(repo, "git", "rev-parse", "HEAD")


def _index_bytes(repo: Path) -> bytes:
    raw = _run(repo, "git", "rev-parse", "--git-path", "index")
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    return path.read_bytes()


def test_clean_generation_remains_no_drift(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g1")

    result = classify_workspace_generation(expected, repo)

    assert expected.dirty is False
    assert result.state == NO_DRIFT
    assert result.current_generation_digest == expected.digest
    assert result.changed_paths == ()


def test_agent_dirty_generation_remains_expected(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("agent\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "g2")

    result = classify_workspace_generation(expected, repo)

    assert expected.dirty is True
    assert result.state == AGENT_EXPECTED_MUTATION
    assert result.changed_paths == ()


def test_same_agent_owned_path_modified_after_capture_is_external(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("agent\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "g3")
    (repo / "tracked.txt").write_text("external\n", encoding="utf-8")

    result = classify_workspace_generation(expected, repo)

    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert result.changed_paths == ("tracked.txt",)


def test_new_untracked_file_after_capture_is_external_and_preserved(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g4")
    marker = repo / "external.txt"
    marker.write_text("external\n", encoding="utf-8")

    result = classify_workspace_generation(expected, repo)

    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert "external.txt" in result.changed_paths
    assert marker.read_text(encoding="utf-8") == "external\n"


def test_deletion_after_capture_is_external_and_not_recovered(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g5")
    (repo / "tracked.txt").unlink()

    result = classify_workspace_generation(expected, repo)

    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert "tracked.txt" in result.changed_paths
    assert not (repo / "tracked.txt").exists()


def test_stage_only_and_unstage_only_drift_visible_with_same_materialized_tree(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    unstaged = capture_workspace_generation(repo, base, "g6")
    _run(repo, "git", "add", "tracked.txt")

    staged_result = classify_workspace_generation(unstaged, repo)
    staged = capture_workspace_generation(repo, base, "g6")
    assert staged.observed_tree == unstaged.observed_tree
    assert staged_result.state == EXTERNAL_LOCAL_MUTATION
    assert staged_result.changed_paths == ("tracked.txt",)

    _run(repo, "git", "reset", "-q", "HEAD", "--", "tracked.txt")
    unstaged_result = classify_workspace_generation(staged, repo)
    assert unstaged_result.state == EXTERNAL_LOCAL_MUTATION
    assert unstaged_result.changed_paths == ("tracked.txt",)


def test_other_worktree_change_does_not_contaminate_selected_worktree(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    other = tmp_path / "other"
    _run(repo, "git", "worktree", "add", "-q", "--detach", str(other), base)
    expected = capture_workspace_generation(repo, base, "g7")
    (other / "tracked.txt").write_text("other-worktree\n", encoding="utf-8")

    result = classify_workspace_generation(expected, repo)

    assert result.state == NO_DRIFT


def test_capture_and_classify_leave_real_index_byte_identical(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    before = _index_bytes(repo)

    expected = capture_workspace_generation(repo, base, "g8")
    middle = _index_bytes(repo)
    result = classify_workspace_generation(expected, repo)
    after = _index_bytes(repo)

    assert before == middle == after
    assert result.state == AGENT_EXPECTED_MUTATION


def test_repeated_capture_is_deterministic(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    first = capture_workspace_generation(repo, base, "g9")
    second = capture_workspace_generation(repo, base, "g9")

    assert first == second
    assert first.digest == second.digest


def test_head_identity_drift_is_unknown_not_external_attribution(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g10")
    (repo / "committed.txt").write_text("new\n", encoding="utf-8")
    _run(repo, "git", "add", "committed.txt")
    _run(repo, "git", "commit", "-q", "-m", "advance")

    result = classify_workspace_generation(expected, repo)

    assert result.state == UNKNOWN_DIRTY_STATE
    assert result.reason_code == "HEAD_IDENTITY_DRIFT"


def test_missing_or_wrong_repository_fails_closed_without_mutation(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g11")
    not_repo = tmp_path / "not-repo"
    not_repo.mkdir()

    result = classify_workspace_generation(expected, not_repo)

    assert result.state == UNKNOWN_DIRTY_STATE
    assert result.current_generation_digest is None


def test_result_contains_no_file_contents_or_secret_sentinel(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    secret = "SECRET_SENTINEL_DRIFT_805"
    (repo / "tracked.txt").write_text(secret + "\n", encoding="utf-8")

    generation = capture_workspace_generation(repo, base, "g12")
    serialized = json.dumps(generation.to_dict(), sort_keys=True)

    assert secret not in serialized


def test_capture_does_not_invoke_mutating_git_commands(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    import reverse_agent.platform_v1.workspace_drift as module

    real_git = module._git
    calls: list[tuple[str, ...]] = []

    def recording_git(repository, *args, **kwargs):
        calls.append(tuple(args))
        return real_git(repository, *args, **kwargs)

    monkeypatch.setattr(module, "_git", recording_git)
    capture_workspace_generation(repo, base, "g13")

    forbidden = {"add", "reset", "checkout", "clean", "restore", "commit", "merge", "rebase"}
    # The reused _snapshot_workspace owns a temporary-index `git add -A`; it is
    # intentionally outside this module's _git binding and proven not to touch
    # the real index. DRIFT-1 itself issues only read-only Git commands.
    assert not any(any(arg in forbidden for arg in call) for call in calls)
