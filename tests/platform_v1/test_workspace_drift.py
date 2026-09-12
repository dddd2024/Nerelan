from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

from reverse_agent.platform_v1.workspace_drift import (
    AGENT_EXPECTED_MUTATION,
    EXTERNAL_LOCAL_MUTATION,
    NO_DRIFT,
    UNKNOWN_DIRTY_STATE,
    WorkspaceObservationError,
    capture_workspace_generation,
    classify_workspace_generation,
)


def _run(repo: Path, *args: str, check: bool = True, input_text: str | None = None) -> str:
    result = subprocess.run(
        args,
        cwd=repo,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {args!r}\n{result.stderr}")
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
    return path.read_bytes() if path.exists() else b""


def _object_files(repo: Path) -> tuple[str, ...]:
    raw = _run(repo, "git", "rev-parse", "--git-path", "objects")
    root = Path(raw)
    if not root.is_absolute():
        root = repo / root
    return tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()))


def _stage_bytes_without_touching_worktree(repo: Path, payload: str) -> None:
    object_id = _run(repo, "git", "hash-object", "-w", "--stdin", input_text=payload)
    _run(repo, "git", "update-index", "--cacheinfo", "100644", object_id, "tracked.txt")


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


def test_same_captured_path_modified_again_is_external(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("agent\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "g3")
    (repo / "tracked.txt").write_text("external\n", encoding="utf-8")
    result = classify_workspace_generation(expected, repo)
    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert result.changed_paths == ("tracked.txt",)


def test_new_untracked_and_deletion_are_external_without_recovery(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g4")
    extra = repo / "extra.txt"
    extra.write_text("new\n", encoding="utf-8")
    result = classify_workspace_generation(expected, repo)
    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert "extra.txt" in result.changed_paths
    assert extra.exists()

    expected = capture_workspace_generation(repo, base, "g4b")
    (repo / "tracked.txt").unlink()
    result = classify_workspace_generation(expected, repo)
    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert "tracked.txt" in result.changed_paths
    assert not (repo / "tracked.txt").exists()


def test_stage_and_unstage_are_visible_with_same_raw_worktree_tree(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    unstaged = capture_workspace_generation(repo, base, "g5")
    _run(repo, "git", "add", "tracked.txt")
    staged_result = classify_workspace_generation(unstaged, repo)
    staged = capture_workspace_generation(repo, base, "g5")
    assert staged.observed_tree == unstaged.observed_tree
    assert staged_result.state == EXTERNAL_LOCAL_MUTATION
    assert staged_result.changed_paths == ("tracked.txt",)

    _run(repo, "git", "reset", "-q", "HEAD", "--", "tracked.txt")
    unstaged_result = classify_workspace_generation(staged, repo)
    assert unstaged_result.state == EXTERNAL_LOCAL_MUTATION
    assert unstaged_result.changed_paths == ("tracked.txt",)


def test_staged_blob_replacement_is_visible_with_same_worktree_bytes(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("worktree\n", encoding="utf-8")
    _stage_bytes_without_touching_worktree(repo, "stage-a\n")
    expected = capture_workspace_generation(repo, base, "g6")

    _stage_bytes_without_touching_worktree(repo, "stage-b\n")
    current = capture_workspace_generation(repo, base, "g6")
    result = classify_workspace_generation(expected, repo)

    assert current.observed_tree == expected.observed_tree
    assert current.index_entries != expected.index_entries
    assert result.state == EXTERNAL_LOCAL_MUTATION
    assert result.changed_paths == ("tracked.txt",)


def test_required_external_clean_filter_is_never_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / ".gitattributes").write_text("tracked.txt filter=guard\n", encoding="utf-8")
    _run(repo, "git", "add", ".gitattributes")
    _run(repo, "git", "commit", "-q", "-m", "attributes")
    base = _run(repo, "git", "rev-parse", "HEAD")
    _run(repo, "git", "config", "filter.guard.clean", "definitely-not-a-real-command-821")
    _run(repo, "git", "config", "filter.guard.required", "true")
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    generation = capture_workspace_generation(repo, base, "g7")
    result = classify_workspace_generation(generation, repo)

    assert result.state == AGENT_EXPECTED_MUTATION


@pytest.mark.skipif(os.name == "nt", reason="executable fsmonitor hook fixture is POSIX-only")
def test_external_fsmonitor_hook_is_never_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    marker = tmp_path / "fsmonitor-hit"
    hook = tmp_path / "fsmonitor-hook"
    hook.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('hit', encoding='utf-8')\n"
        "raise SystemExit(1)\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _run(repo, "git", "config", "core.fsmonitor", str(hook))
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    generation = capture_workspace_generation(repo, base, "g7-fsmonitor")
    result = classify_workspace_generation(generation, repo)

    assert result.state == AGENT_EXPECTED_MUTATION
    assert not marker.exists()


def test_touched_clean_file_does_not_rewrite_real_index(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    before = _index_bytes(repo)
    os.utime(repo / "tracked.txt", None)
    capture_workspace_generation(repo, base, "g8")
    after = _index_bytes(repo)
    assert before == after


def test_capture_and_classify_preserve_real_index_and_object_store(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    index_before = _index_bytes(repo)
    objects_before = _object_files(repo)

    expected = capture_workspace_generation(repo, base, "g9")
    result = classify_workspace_generation(expected, repo)

    assert result.state == AGENT_EXPECTED_MUTATION
    assert _index_bytes(repo) == index_before
    assert _object_files(repo) == objects_before


def test_second_worktree_does_not_contaminate_selected_worktree(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    other = tmp_path / "other"
    _run(repo, "git", "worktree", "add", "-q", "--detach", str(other), base)
    expected = capture_workspace_generation(repo, base, "g10")
    (other / "tracked.txt").write_text("other\n", encoding="utf-8")
    assert classify_workspace_generation(expected, repo).state == NO_DRIFT


def test_repeated_capture_is_deterministic(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    first = capture_workspace_generation(repo, base, "g11")
    second = capture_workspace_generation(repo, base, "g11")
    assert first == second
    assert first.digest == second.digest


def test_head_and_wrong_repository_fail_closed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g12")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    _run(repo, "git", "add", "new.txt")
    _run(repo, "git", "commit", "-q", "-m", "advance")
    result = classify_workspace_generation(expected, repo)
    assert result.state == UNKNOWN_DIRTY_STATE
    assert result.reason_code == "HEAD_IDENTITY_DRIFT"

    other = tmp_path / "not-repo"
    other.mkdir()
    result = classify_workspace_generation(expected, other)
    assert result.state == UNKNOWN_DIRTY_STATE


def test_unmerged_index_fails_closed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    _run(repo, "git", "checkout", "-q", "-b", "other")
    (repo / "tracked.txt").write_text("other\n", encoding="utf-8")
    _run(repo, "git", "commit", "-qam", "other")
    _run(repo, "git", "checkout", "-q", "master")
    (repo / "tracked.txt").write_text("master\n", encoding="utf-8")
    _run(repo, "git", "commit", "-qam", "master")
    current = _run(repo, "git", "rev-parse", "HEAD")
    expected = capture_workspace_generation(repo, current, "g13")
    _run(repo, "git", "merge", "other", check=False)

    result = classify_workspace_generation(expected, repo)
    assert result.state == UNKNOWN_DIRTY_STATE
    assert result.reason_code == "UNMERGED_INDEX"


def test_gitlink_index_fails_closed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    _run(repo, "git", "update-index", "--add", "--cacheinfo", "160000", base, "submodule")
    with pytest.raises(WorkspaceObservationError) as caught:
        capture_workspace_generation(repo, base, "g14")
    assert caught.value.code == "GITLINK_OR_INDEX_STATE_UNSUPPORTED"


def test_result_never_contains_file_content_or_raw_git_error(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    secret = "SECRET_SENTINEL_DRIFT_821"
    (repo / "tracked.txt").write_text(secret + "\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "g15")
    serialized = json.dumps(generation.to_dict(), sort_keys=True)
    assert secret not in serialized

    result = classify_workspace_generation(generation, tmp_path / "missing")
    assert secret not in json.dumps(result.to_dict(), sort_keys=True)
    assert result.reason_code == "REPOSITORY_UNOBSERVABLE"


def test_observation_uses_optional_lock_suppression_and_no_forbidden_git(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    import reverse_agent.platform_v1.workspace_drift as module

    real_execute = module._execute_git
    calls: list[tuple[tuple[str, ...], str | None, str | None]] = []

    def recording_execute(command, *, cwd, env, input_bytes):
        calls.append((tuple(command), env.get("GIT_OPTIONAL_LOCKS"), env.get("GIT_OBJECT_DIRECTORY")))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setattr(module, "_execute_git", recording_execute)
    capture_workspace_generation(repo, base, "g16")

    assert calls
    assert all(optional_locks == "0" for _, optional_locks, _ in calls)
    assert all(command[:3] == ("git", "-c", "core.fsmonitor=false") for command, _, _ in calls)
    forbidden = {"status", "add", "checkout", "reset", "clean", "restore", "commit", "merge", "rebase"}
    assert not any(any(arg in forbidden for arg in command[1:]) for command, _, _ in calls)
    write_like = {"hash-object", "update-index", "write-tree", "read-tree"}
    assert all(
        object_directory is not None
        for command, _, object_directory in calls
        if any(arg in write_like for arg in command[1:])
    )
