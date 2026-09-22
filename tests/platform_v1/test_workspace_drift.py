from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from reverse_agent.platform_v1.workspace_drift import (
    CAPTURED_DIRTY_MATCH,
    LOCAL_GENERATION_CHANGED,
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
    _run(repo, "git", "init", "-q", "--initial-branch=master")
    # Raw-byte observation intentionally does not apply checkout/clean filters.
    # Keep fixture bytes identical to their staged blobs on every host.
    _run(repo, "git", "config", "core.autocrlf", "false")
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


def _object_root(repo: Path) -> Path:
    raw = _run(repo, "git", "rev-parse", "--git-path", "objects")
    path = Path(raw)
    return path if path.is_absolute() else repo / path


def _object_files(repo: Path) -> tuple[str, ...]:
    root = _object_root(repo)
    return tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()))


def _loose_object(repo: Path, oid: str) -> Path:
    return _object_root(repo) / oid[:2] / oid[2:]


def _stage_bytes_without_touching_worktree(repo: Path, payload: str) -> None:
    object_id = _run(repo, "git", "hash-object", "-w", "--stdin", input_text=payload)
    _run(repo, "git", "update-index", "--cacheinfo", "100644", object_id, "tracked.txt")


def _configure_promisor(repo: Path, remote_url: str) -> None:
    _run(repo, "git", "remote", "add", "origin", remote_url)
    _run(repo, "git", "config", "extensions.partialClone", "origin")
    _run(repo, "git", "config", "remote.origin.promisor", "true")
    _run(repo, "git", "config", "remote.origin.partialclonefilter", "blob:none")


def test_clean_generation_remains_no_drift(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g1")
    result = classify_workspace_generation(expected, repo)
    assert expected.dirty is False
    assert result.state == NO_DRIFT
    assert result.current_generation_digest == expected.digest
    assert result.changed_paths == ()


def test_captured_dirty_generation_remains_matched_without_actor_claim(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("captured\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "g2")
    result = classify_workspace_generation(expected, repo)
    assert expected.dirty is True
    assert result.state == CAPTURED_DIRTY_MATCH
    assert "AGENT" not in result.state
    assert "EXTERNAL" not in result.state


def test_same_captured_path_modified_again_is_local_generation_changed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("captured\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "g3")
    (repo / "tracked.txt").write_text("later\n", encoding="utf-8")
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
    assert result.changed_paths == ("tracked.txt",)


def test_new_untracked_and_deletion_are_local_generation_changed_without_recovery(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "g4")
    extra = repo / "extra.txt"
    extra.write_text("new\n", encoding="utf-8")
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
    assert "extra.txt" in result.changed_paths
    assert extra.exists()

    expected = capture_workspace_generation(repo, base, "g4b")
    (repo / "tracked.txt").unlink()
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
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
    assert staged_result.state == LOCAL_GENERATION_CHANGED
    assert staged_result.changed_paths == ("tracked.txt",)

    _run(repo, "git", "reset", "-q", "HEAD", "--", "tracked.txt")
    unstaged_result = classify_workspace_generation(staged, repo)
    assert unstaged_result.state == LOCAL_GENERATION_CHANGED
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
    assert result.state == LOCAL_GENERATION_CHANGED
    assert result.changed_paths == ("tracked.txt",)


def test_required_external_clean_filter_is_never_executed(tmp_path) -> None:
    repo, _ = _repo(tmp_path)
    (repo / ".gitattributes").write_text("tracked.txt filter=guard\n", encoding="utf-8")
    _run(repo, "git", "add", ".gitattributes")
    _run(repo, "git", "commit", "-q", "-m", "attributes")
    base = _run(repo, "git", "rev-parse", "HEAD")
    _run(repo, "git", "config", "filter.guard.clean", "definitely-not-a-real-command-v7")
    _run(repo, "git", "config", "filter.guard.required", "true")
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "g7")
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH


@pytest.mark.skipif(os.name == "nt", reason="executable fsmonitor fixture is POSIX-only")
def test_external_fsmonitor_hook_is_never_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    marker = tmp_path / "fsmonitor-hit"
    hook = tmp_path / "fsmonitor-hook"
    hook.write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('hit', encoding='utf-8')\nraise SystemExit(1)\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _run(repo, "git", "config", "core.fsmonitor", str(hook))
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "g7-fsmonitor")
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH
    assert not marker.exists()


@pytest.mark.skipif(os.name == "nt", reason="executable Git hook fixture is POSIX-only")
def test_post_index_change_hook_is_never_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    marker = tmp_path / "post-index-change-hit"
    hooks = tmp_path / "configured-hooks"
    hooks.mkdir()
    hook = hooks / "post-index-change"
    hook.write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('hit', encoding='utf-8')\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _run(repo, "git", "config", "core.hooksPath", str(hooks))
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "g7-hooks")
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH
    assert not marker.exists()


def test_touched_clean_file_does_not_rewrite_real_index(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    before = _index_bytes(repo)
    os.utime(repo / "tracked.txt", None)
    capture_workspace_generation(repo, base, "g8")
    assert _index_bytes(repo) == before


def test_capture_and_classify_preserve_real_index_and_object_store(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    index_before = _index_bytes(repo)
    objects_before = _object_files(repo)
    expected = capture_workspace_generation(repo, base, "g9")
    result = classify_workspace_generation(expected, repo)
    assert result.state == CAPTURED_DIRTY_MATCH
    assert _index_bytes(repo) == index_before
    assert _object_files(repo) == objects_before


@pytest.mark.skipif(os.name == "nt", reason="literal backslash filename fixture is POSIX-only")
def test_posix_literal_backslash_path_identity_is_preserved(tmp_path) -> None:
    repo, _ = _repo(tmp_path)
    literal = r"a\b"
    (repo / "a").mkdir()
    (repo / literal).write_text("literal-backslash\n", encoding="utf-8")
    (repo / "a" / "b").write_text("slash-path\n", encoding="utf-8")
    _run(repo, "git", "add", "--all")
    _run(repo, "git", "commit", "-q", "-m", "path identities")
    base = _run(repo, "git", "rev-parse", "HEAD")
    generation = capture_workspace_generation(repo, base, "g9-backslash")
    paths = tuple(entry.path for entry in generation.index_entries)
    assert literal in paths
    assert "a/b" in paths
    assert literal != "a/b"
    assert classify_workspace_generation(generation, repo).state == NO_DRIFT


@pytest.mark.skipif(os.name == "nt", reason="colon path component fixture is POSIX-only")
def test_alternate_object_directory_handles_path_list_separator(tmp_path) -> None:
    parent = tmp_path / "with:colon"
    parent.mkdir()
    repo, base = _repo(parent)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    index_before = _index_bytes(repo)
    objects_before = _object_files(repo)
    generation = capture_workspace_generation(repo, base, "g9-colon")
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH
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
    assert classify_workspace_generation(expected, other).state == UNKNOWN_DIRTY_STATE


def test_unmerged_index_fails_closed(tmp_path) -> None:
    repo, _ = _repo(tmp_path)
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


def test_result_never_contains_file_content_raw_git_error_or_actor_claim(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    secret = "SECRET_SENTINEL_DRIFT_V7"
    (repo / "tracked.txt").write_text(secret + "\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "g15")
    serialized = json.dumps(generation.to_dict(), sort_keys=True)
    assert secret not in serialized
    result = classify_workspace_generation(generation, tmp_path / "missing")
    rendered = json.dumps(result.to_dict(), sort_keys=True)
    assert secret not in rendered
    assert result.reason_code == "REPOSITORY_UNOBSERVABLE"
    assert "AGENT" not in rendered
    assert "EXTERNAL" not in rendered


def test_observation_enforces_security_environment_and_no_forbidden_git(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    import reverse_agent.platform_v1.workspace_drift as module

    real_execute = module._execute_git
    calls: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def recording_execute(command, *, cwd, env, input_bytes):
        calls.append((tuple(command), dict(env)))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setattr(module, "_execute_git", recording_execute)
    capture_workspace_generation(repo, base, "g16")
    assert calls
    assert all(env.get("GIT_OPTIONAL_LOCKS") == "0" for _, env in calls)
    assert all(env.get("GIT_TERMINAL_PROMPT") == "0" for _, env in calls)
    assert all(env.get("GIT_NO_LAZY_FETCH") == "1" for _, env in calls)
    assert all(
        command[:5] == ("git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")
        for command, _ in calls
    )
    forbidden = {"status", "add", "checkout", "reset", "clean", "restore", "commit", "merge", "rebase", "fetch", "pull", "push"}
    assert not any(any(arg in forbidden for arg in command[1:]) for command, _ in calls)
    write_like = {"hash-object", "update-index", "write-tree", "read-tree"}
    assert all(
        env.get("GIT_OBJECT_DIRECTORY")
        for command, env in calls
        if any(arg in write_like for arg in command[1:])
    )


def test_security_environment_cannot_be_weakened_by_scratch_env(tmp_path, monkeypatch) -> None:
    repo, _ = _repo(tmp_path)
    import reverse_agent.platform_v1.workspace_drift as module

    observed: dict[str, str] = {}
    real_execute = module._execute_git

    def recording_execute(command, *, cwd, env, input_bytes):
        observed.update({key: env.get(key, "") for key in ("GIT_OPTIONAL_LOCKS", "GIT_TERMINAL_PROMPT", "GIT_NO_LAZY_FETCH")})
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setattr(module, "_execute_git", recording_execute)
    module._git_bytes(
        repo,
        "rev-parse",
        "HEAD",
        extra_env={"GIT_OPTIONAL_LOCKS": "1", "GIT_TERMINAL_PROMPT": "1", "GIT_NO_LAZY_FETCH": "0"},
    )
    assert observed == {"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1"}


@pytest.mark.skipif(os.name == "nt", reason="loose object fixture is POSIX CI coverage")
def test_missing_promisor_tree_fails_closed_without_restoring_real_objects(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(repo), str(remote)], check=True)
    _configure_promisor(repo, str(remote))
    tree_oid = _run(repo, "git", "rev-parse", f"{base}^{{tree}}")
    missing = _loose_object(repo, tree_oid)
    assert missing.exists()
    missing.unlink()
    objects_before = _object_files(repo)
    with pytest.raises(WorkspaceObservationError):
        capture_workspace_generation(repo, base, "g-promisor")
    assert not missing.exists()
    assert _object_files(repo) == objects_before


@pytest.mark.skipif(os.name == "nt", reason="ext remote helper fixture is POSIX-only")
def test_adversarial_promisor_remote_helper_is_not_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    marker = tmp_path / "remote-helper-hit"
    helper = tmp_path / "remote-helper.sh"
    helper.write_text(f"#!/bin/sh\necho hit > {marker}\nexit 1\n", encoding="utf-8")
    helper.chmod(0o755)
    _configure_promisor(repo, f"ext::{helper}")
    _run(repo, "git", "config", "protocol.ext.allow", "always")
    tree_oid = _run(repo, "git", "rev-parse", f"{base}^{{tree}}")
    missing = _loose_object(repo, tree_oid)
    assert missing.exists()
    missing.unlink()
    with pytest.raises(WorkspaceObservationError):
        capture_workspace_generation(repo, base, "g-ext")
    assert not marker.exists()
    assert not missing.exists()


def test_production_classification_vocabulary_is_actor_neutral() -> None:
    import reverse_agent.platform_v1.workspace_drift as module

    source = inspect.getsource(module)
    assert "AGENT_EXPECTED_MUTATION" not in source
    assert "EXTERNAL_LOCAL_MUTATION" not in source
    assert {NO_DRIFT, CAPTURED_DIRTY_MATCH, LOCAL_GENERATION_CHANGED, UNKNOWN_DIRTY_STATE} == module._VALID_STATES


@pytest.mark.parametrize("object_kind", ["missing", "tree", "commit"])
def test_staged_object_must_be_a_locally_available_blob(tmp_path, object_kind) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "staged-object")
    missing = None
    if object_kind == "missing":
        oid = _run(repo, "git", "hash-object", "-w", "--stdin", input_text="staged-only\n")
        missing = _loose_object(repo, oid)
        missing.chmod(0o600)
        missing.unlink()
    elif object_kind == "tree":
        oid = _run(repo, "git", "rev-parse", f"{base}^{{tree}}")
    else:
        oid = base
    _run(repo, "git", "update-index", "--cacheinfo", "100644", oid, "tracked.txt")
    index_before, objects_before = _index_bytes(repo), _object_files(repo)
    assert (repo / "tracked.txt").read_text(encoding="utf-8") == "base\n"
    with pytest.raises(WorkspaceObservationError, match="^INDEX_BLOB_UNOBSERVABLE$"):
        capture_workspace_generation(repo, base, "staged-object")
    result = classify_workspace_generation(expected, repo)
    assert result.state == UNKNOWN_DIRTY_STATE
    assert result.reason_code == "INDEX_BLOB_UNOBSERVABLE"
    assert _index_bytes(repo) == index_before
    assert _object_files(repo) == objects_before
    assert (repo / "tracked.txt").read_text(encoding="utf-8") == "base\n"
    if missing is not None:
        assert not missing.exists()


def test_replace_ref_cannot_disguise_staged_tree_as_blob(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    # Exercise an ordinary stored tree, not Git's special in-memory empty tree.
    tree = _run(repo, "git", "rev-parse", f"{base}^{{tree}}")
    blob = _run(repo, "git", "rev-parse", "HEAD:tracked.txt")
    _run(repo, "git", "update-ref", f"refs/replace/{tree}", blob)
    assert _run(repo, "git", "cat-file", "-t", tree) == "blob"
    _run(repo, "git", "update-index", "--cacheinfo", "100644", tree, "tracked.txt")
    before = _repository_file_bytes(repo)
    with pytest.raises(WorkspaceObservationError, match="^INDEX_BLOB_UNOBSERVABLE$"):
        capture_workspace_generation(repo, base, "raw-object")
    assert _repository_file_bytes(repo) == before


def test_missing_staged_promisor_blob_is_not_restored(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    _stage_bytes_without_touching_worktree(repo, "promised-stage\n")
    oid = _run(repo, "git", "rev-parse", ":tracked.txt")
    _run(repo, "git", "commit", "-q", "-m", "promised")
    remote = tmp_path / "remote.git"
    _run(tmp_path, "git", "clone", "-q", "--bare", str(repo), str(remote))
    assert _run(remote, "git", "cat-file", "-t", oid) == "blob"
    _run(repo, "git", "reset", "--soft", base)
    _configure_promisor(repo, str(remote))
    missing = _loose_object(repo, oid)
    missing.chmod(0o600)
    missing.unlink()
    local_before, remote_before = _repository_file_bytes(repo), _repository_file_bytes(remote)
    trace = tmp_path / "observation-trace.jsonl"
    globals_ = capture_workspace_generation.__globals__
    real_execute = globals_["_execute_git"]

    def traced_execute(command, *, cwd, env, input_bytes):
        traced_env = dict(env, GIT_TRACE2_EVENT=str(trace))
        return real_execute(command, cwd=cwd, env=traced_env, input_bytes=input_bytes)

    monkeypatch.setitem(globals_, "_execute_git", traced_execute)
    with pytest.raises(WorkspaceObservationError, match="^INDEX_BLOB_UNOBSERVABLE$"):
        capture_workspace_generation(repo, base, "promised-stage")
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert any(event.get("event") == "start" and "cat-file" in event.get("argv", []) for event in events)
    assert not any(event.get("event") == "child_start" for event in events)
    assert not missing.exists()
    assert _repository_file_bytes(repo) == local_before
    assert _repository_file_bytes(remote) == remote_before


def test_mixed_case_git_environment_cannot_redirect_observation(tmp_path, monkeypatch) -> None:
    source, alternate = tmp_path / "source", tmp_path / "alternate"
    source.mkdir()
    alternate.mkdir()
    repo, base = _repo(source)
    other, _ = _repo(alternate)
    expected = capture_workspace_generation(repo, base, "mixed-case")
    before = _repository_file_bytes(repo), _repository_file_bytes(other)
    actual_os = os

    class EnvironmentView:
        # Windows os.environ normalizes key case. Preserve mixed case here so
        # the production boundary is exercised with real child Git commands.
        environ = dict(os.environ, GiT_DiR=str(other / ".git"), git_no_lazy_fetch="0")

        def __getattr__(self, name):
            return getattr(actual_os, name)

    globals_ = capture_workspace_generation.__globals__
    real_execute = globals_["_execute_git"]
    environments = []

    def recording_execute(command, *, cwd, env, input_bytes):
        environments.append(dict(env))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setitem(globals_, "os", EnvironmentView())
    monkeypatch.setitem(globals_, "_execute_git", recording_execute)
    assert capture_workspace_generation(repo, base, "mixed-case") == expected
    assert classify_workspace_generation(expected, repo).state == NO_DRIFT
    assert environments
    assert all("GiT_DiR" not in env and "git_no_lazy_fetch" not in env for env in environments)
    assert all(env["GIT_NO_LAZY_FETCH"] == "1" for env in environments)
    assert (_repository_file_bytes(repo), _repository_file_bytes(other)) == before


def _repository_file_bytes(repo: Path) -> dict[str, bytes]:
    return {str(path.relative_to(repo)): path.read_bytes() for path in repo.rglob("*") if path.is_file()}


@pytest.mark.parametrize("override", [
    "GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
    "GIT_NO_LAZY_FETCH", "GIT_NO_REPLACE_OBJECTS",
])
def test_inherited_git_overrides_cannot_redirect_observation(tmp_path, monkeypatch, override) -> None:
    source_parent, other_parent = tmp_path / "source", tmp_path / "other"
    source_parent.mkdir()
    other_parent.mkdir()
    repo, base = _repo(source_parent)
    other, _ = _repo(other_parent)
    (other / "tracked.txt").write_text("different repository\n", encoding="utf-8")
    _run(other, "git", "add", "tracked.txt")
    _run(other, "git", "commit", "-q", "-m", "other")
    config = tmp_path / "inherited-config"
    config.write_text("[core]\n\tbare = true\n", encoding="utf-8")
    overrides = {
        "GIT_DIR": str(other / ".git"),
        "GIT_COMMON_DIR": str(other / ".git"),
        "GIT_WORK_TREE": str(other),
        "GIT_INDEX_FILE": str(other / ".git/index"),
        "GIT_OBJECT_DIRECTORY": str(other / ".git/objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(other / ".git/objects"),
        "GIT_CONFIG_SYSTEM": str(config),
        "GIT_CONFIG_GLOBAL": str(config),
        "GIT_CONFIG_PARAMETERS": "'core.bare=true'",
        "GIT_CONFIG_COUNT": "1",
        "GIT_NO_LAZY_FETCH": "0",
        "GIT_NO_REPLACE_OBJECTS": "0",
    }
    expected = capture_workspace_generation(repo, base, "ambient-env")
    before = _repository_file_bytes(repo), _repository_file_bytes(other)
    globals_ = capture_workspace_generation.__globals__
    real_execute = globals_["_execute_git"]
    environments = []

    def recording_execute(command, *, cwd, env, input_bytes):
        environments.append(dict(env))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    with monkeypatch.context() as context:
        context.setenv(override, overrides[override])
        if override == "GIT_CONFIG_COUNT":
            context.setenv("GIT_CONFIG_KEY_0", "core.bare")
            context.setenv("GIT_CONFIG_VALUE_0", "true")
        context.setitem(globals_, "_execute_git", recording_execute)
        observed = capture_workspace_generation(repo, base, "ambient-env")
        assert observed == expected
        assert classify_workspace_generation(expected, repo).state == NO_DRIFT
    assert environments
    assert all(env.get(override) != overrides[override] for env in environments)
    if override == "GIT_CONFIG_COUNT":
        assert all("GIT_CONFIG_KEY_0" not in env and "GIT_CONFIG_VALUE_0" not in env for env in environments)
    assert (_repository_file_bytes(repo), _repository_file_bytes(other)) == before


def test_external_diff_and_textconv_are_not_executed(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    marker = tmp_path / "diff-command-ran"
    # A shell command valid for Git's own shell on both supported platforms.
    command = f'echo ran > "{marker.as_posix()}"'
    _run(repo, "git", "config", "diff.external", command)
    _run(repo, "git", "config", "diff.probe.textconv", command)
    (repo / ".gitattributes").write_text("*.txt diff=probe\n", encoding="utf-8")
    _run(repo, "git", "add", ".gitattributes")
    _run(repo, "git", "commit", "-q", "-m", "attributes")
    base = _run(repo, "git", "rev-parse", "HEAD")
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    expected = capture_workspace_generation(repo, base, "diff-config")
    assert expected.dirty
    assert classify_workspace_generation(expected, repo).state == CAPTURED_DIRTY_MATCH
    assert not marker.exists()


# ---------------------------------------------------------------------------
# #829 v10 hardening: batching, semantic index identity, object formats,
# and hard runtime output bounds.
# ---------------------------------------------------------------------------


def test_stat_cache_refresh_does_not_change_semantic_generation(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "semantic-index")
    before_index = _index_bytes(repo)
    tracked = repo / "tracked.txt"
    now_ns = tracked.stat().st_mtime_ns + 2_000_000_000
    os.utime(tracked, ns=(now_ns, now_ns))
    _run(repo, "git", "update-index", "--refresh")
    refreshed_index = _index_bytes(repo)

    current = capture_workspace_generation(repo, base, "semantic-index")
    assert current.index_entries == expected.index_entries
    assert current.index_digest == expected.index_digest
    assert current.digest == expected.digest
    assert classify_workspace_generation(expected, repo).state == NO_DRIFT
    assert refreshed_index or before_index

    _run(repo, "git", "update-index", "--fsmonitor-valid", "tracked.txt")
    cache_only = capture_workspace_generation(repo, base, "semantic-index")
    assert cache_only.index_entries == expected.index_entries
    assert cache_only.index_digest == expected.index_digest
    assert cache_only.digest == expected.digest


def test_semantic_index_flags_are_bound_to_generation_identity(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    expected = capture_workspace_generation(repo, base, "semantic-flags")

    _run(repo, "git", "update-index", "--skip-worktree", "tracked.txt")
    skipped = capture_workspace_generation(repo, base, "semantic-flags")
    assert skipped.index_digest != expected.index_digest
    assert skipped.digest != expected.digest
    assert skipped.index_entries[0].skip_worktree is True
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
    assert result.changed_paths == ("tracked.txt",)

    _run(repo, "git", "update-index", "--no-skip-worktree", "tracked.txt")
    baseline = capture_workspace_generation(repo, base, "semantic-flags")
    assert baseline.digest == expected.digest
    _run(repo, "git", "update-index", "--assume-unchanged", "tracked.txt")
    assumed = capture_workspace_generation(repo, base, "semantic-flags")
    assert assumed.index_digest != expected.index_digest
    assert assumed.index_entries[0].assume_unchanged is True
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
    assert result.changed_paths == ("tracked.txt",)


def test_sha256_repository_is_supported_when_git_supports_it(tmp_path) -> None:
    repo = tmp_path / "sha256-repo"
    repo.mkdir()
    initialized = subprocess.run(
        ["git", "init", "-q", "--initial-branch=master", "--object-format=sha256"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if initialized.returncode != 0:
        pytest.skip("installed Git does not support SHA-256 repositories")
    _run(repo, "git", "config", "core.autocrlf", "false")
    _run(repo, "git", "config", "user.email", "drift@test.local")
    _run(repo, "git", "config", "user.name", "Drift Fixture")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _run(repo, "git", "add", "tracked.txt")
    _run(repo, "git", "commit", "-q", "-m", "base")
    base = _run(repo, "git", "rev-parse", "HEAD")
    assert len(base) == 64

    expected = capture_workspace_generation(repo, base, "sha256")
    assert len(expected.head_commit) == 64
    assert len(expected.observed_tree) == 64
    assert all(len(entry.object_id) == 64 for entry in expected.index_entries)
    assert classify_workspace_generation(expected, repo).state == NO_DRIFT
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    result = classify_workspace_generation(expected, repo)
    assert result.state == LOCAL_GENERATION_CHANGED
    assert result.changed_paths == ("tracked.txt",)


def test_three_thousand_paths_use_bounded_git_process_count(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    for index in range(3000):
        (repo / f"bulk-{index:04d}.txt").write_text("x", encoding="utf-8")

    import reverse_agent.platform_v1.workspace_drift as module

    real_execute = module._execute_git
    calls: list[tuple[str, ...]] = []

    def recording_execute(command, *, cwd, env, input_bytes):
        calls.append(tuple(command))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setattr(module, "_execute_git", recording_execute)
    generation = capture_workspace_generation(repo, base, "bulk-3000")
    assert generation.dirty
    assert len(generation.changed_paths) == 3000
    hash_batches = [
        command
        for command in calls
        if "hash-object" in command and "--stdin-paths" in command
    ]
    index_batches = [
        command
        for command in calls
        if "update-index" in command and "--index-info" in command
    ]
    assert len(hash_batches) == 2  # one per stability observation
    assert len(index_batches) == 2
    assert len(calls) < 40


@pytest.mark.skipif(os.name == "nt", reason="newline path is not a Windows filename")
def test_newline_paths_are_argv_batched_and_preserve_identity(tmp_path, monkeypatch) -> None:
    repo, base = _repo(tmp_path)
    paths = tuple(f"line\nbreak-{index:02d}.txt" for index in range(32))
    for path in paths:
        (repo / path).write_text("newline\n", encoding="utf-8")
    import reverse_agent.platform_v1.workspace_drift as module

    real_execute = module._execute_git
    calls: list[tuple[str, ...]] = []

    def recording_execute(command, *, cwd, env, input_bytes):
        calls.append(tuple(command))
        return real_execute(command, cwd=cwd, env=env, input_bytes=input_bytes)

    monkeypatch.setattr(module, "_execute_git", recording_execute)
    generation = capture_workspace_generation(repo, base, "newline-paths")
    assert set(paths).issubset(generation.changed_paths)
    argv_batches = [
        command
        for command in calls
        if "hash-object" in command and "--stdin-paths" not in command
    ]
    assert len(argv_batches) == 2  # one argv batch per stability observation
    expected_sources = {str(repo / path) for path in paths}
    assert all(
        set(command[command.index("--") + 1 :]) == expected_sources
        for command in argv_batches
    )
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH

@pytest.mark.parametrize("stream_name", ["stdout", "stderr"])
def test_execute_git_hard_bounds_each_output_stream(tmp_path, monkeypatch, stream_name) -> None:
    import reverse_agent.platform_v1.workspace_drift as module

    monkeypatch.setattr(module, "_MAX_GIT_OUTPUT_BYTES", 1024)
    monkeypatch.setattr(module, "_GIT_TIMEOUT_SECONDS", 5)
    target = "stdout" if stream_name == "stdout" else "stderr"
    code = (
        "import sys,time;"
        f"s=getattr(sys,'{target}').buffer;"
        "s.write(b'x'*10000000);s.flush();time.sleep(10)"
    )
    started = time.perf_counter()
    result = module._execute_git(
        (sys.executable, "-c", code),
        cwd=tmp_path,
        env=os.environ,
        input_bytes=None,
    )
    elapsed = time.perf_counter() - started
    assert result.returncode != 0
    assert len(result.stdout) <= 1024
    assert len(result.stderr) <= 1024
    assert elapsed < 5


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific helper suppression proof")
def test_windows_repository_helpers_remain_inert(tmp_path) -> None:
    repo, base = _repo(tmp_path)
    fsmonitor_marker = tmp_path / "fsmonitor-hit"
    fsmonitor = tmp_path / "fsmonitor.cmd"
    fsmonitor.write_text(
        f'@echo hit> "{fsmonitor_marker}"\r\n@exit /b 1\r\n',
        encoding="utf-8",
    )
    hooks_marker = tmp_path / "hook-hit"
    hooks = tmp_path / "configured-hooks"
    hooks.mkdir()
    hook = hooks / "post-index-change"
    hook.write_text(
        "#!/bin/sh\nprintf hit > "
        + repr(hooks_marker.as_posix())
        + "\n",
        encoding="utf-8",
    )
    _run(repo, "git", "config", "core.fsmonitor", str(fsmonitor))
    _run(repo, "git", "config", "core.hooksPath", str(hooks))
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    generation = capture_workspace_generation(repo, base, "windows-helper-inert")
    assert classify_workspace_generation(generation, repo).state == CAPTURED_DIRTY_MATCH
    assert not fsmonitor_marker.exists()
    assert not hooks_marker.exists()
