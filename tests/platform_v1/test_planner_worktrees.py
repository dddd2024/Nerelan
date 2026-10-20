"""Real Git coverage for disposable planner worktrees (no providers)."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reverse_agent.platform_v1 import repository_preparation as preparation
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init")
    git(source, "config", "user.email", "fixture@example.invalid")
    git(source, "config", "user.name", "Fixture")
    (source / "file.txt").write_text("first")
    git(source, "add", ".")
    git(source, "commit", "-m", "first")
    return source


@pytest.mark.parametrize("explicit", [False, True])
def test_base_detachment_and_source_preserved(repo, tmp_path, explicit):
    first = git(repo, "rev-parse", "HEAD")
    (repo / "file.txt").write_text("second")
    git(repo, "commit", "-am", "second")
    head = git(repo, "rev-parse", "HEAD")
    (repo / "file.txt").write_text("staged")
    git(repo, "add", ".")
    (repo / "file.txt").write_text("dirty")
    (repo / "untracked").write_text("keep")
    before = git(repo, "status", "--porcelain"), git(repo, "diff", "--cached")
    with preparation.planner_worktree(repo, tmp_path / "tasks", "goal", 2,
                                     first if explicit else None) as (path, sha):
        assert sha == (first if explicit else head)
        assert path.parent == tmp_path / "tasks" / "planner"
        assert path.name.startswith("goal-r2-")
        assert git(path, "rev-parse", "HEAD") == sha
        assert subprocess.run(["git", "-C", str(path), "symbolic-ref", "-q", "HEAD"],
                              capture_output=True).returncode != 0
        (path / "scratch").write_text("discard")
    assert not path.exists()
    assert git(repo, "rev-parse", "HEAD") == head
    assert before == (git(repo, "status", "--porcelain"), git(repo, "diff", "--cached"))
    assert (repo / "file.txt").read_text() == "dirty"
    assert str(path).replace("\\", "/") not in git(repo, "worktree", "list", "--porcelain")


def test_exception_and_overlapping_runs(repo, tmp_path):
    root = tmp_path / "tasks"
    with preparation.planner_worktree(repo, root, "goal", 1) as (outer, _):
        with pytest.raises(RuntimeError, match="body failed"):
            with preparation.planner_worktree(repo, root, "goal", 1) as (inner, _):
                assert inner != outer
                assert outer.exists()
                raise RuntimeError("body failed")
        assert not inner.exists()
        assert outer.exists()
    assert not outer.exists()


def child(repo, root, crash):
    code = '''
import os, sys
from reverse_agent.platform_v1 import repository_preparation as p
with p.planner_worktree(sys.argv[1], sys.argv[2], "child", 1) as (path, sha):
    print(path, flush=True)
    if sys.argv[3] == "crash":
        os._exit(0)
    sys.stdin.readline()
'''
    return subprocess.Popen([sys.executable, "-c", code, str(repo), str(root),
                             "crash" if crash else "wait"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)


def test_crash_recovery_and_other_process_liveness(repo, tmp_path):
    root = tmp_path / "tasks"
    active = child(repo, root, False)
    try:
        active_path = Path(active.stdout.readline().strip())
        assert active_path.is_dir()
        dead = child(repo, root, True)
        output, error = dead.communicate(timeout=30)
        assert dead.returncode == 0, error
        stale = Path(output.strip())
        assert stale.is_dir()
        unrelated = root / "planner" / "unrelated"
        unrelated.mkdir()
        with preparation.planner_worktree(repo, root, "parent", 1):
            assert active_path.is_dir()
            assert not stale.exists()
            assert unrelated.is_dir()
    finally:
        active.communicate("done\n", timeout=30)
    assert active.returncode == 0
    assert not active_path.exists()


def test_partial_add_failure_cleanup(repo, tmp_path, monkeypatch):
    original = preparation._planner_git
    def fail_after_add(source, *args):
        result = original(source, *args)
        if args[:2] == ("worktree", "add"):
            raise ExecutorRuntimeError("injected")
        return result
    monkeypatch.setattr(preparation, "_planner_git", fail_after_add)
    with pytest.raises(ExecutorRuntimeError, match="injected"):
        with preparation.planner_worktree(repo, tmp_path / "tasks", "goal", 1):
            pytest.fail("must not enter")
    assert not list((tmp_path / "tasks" / "planner").glob("*.planner-owner.json"))
    assert len(git(repo, "worktree", "list", "--porcelain").split("worktree ")) == 2


def test_containment_guards(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("safe")
    root = tmp_path / "tasks" / "planner"
    root.mkdir(parents=True)
    with pytest.raises(ExecutorRuntimeError, match="planner_path_invalid"):
        preparation._remove_planner_worktree(repo, root, outside)
    with pytest.raises(ExecutorRuntimeError, match="planner_path_invalid"):
        with preparation.planner_worktree(repo, root / "..", "goal", 1):
            pass
    with pytest.raises(ExecutorRuntimeError, match="planner_identity_invalid"):
        with preparation.planner_worktree(repo, root, "../outside", 1):
            pass
    assert (outside / "keep").read_text() == "safe"
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "link"), str(outside)],
                       check=True, capture_output=True)
    with pytest.raises(ExecutorRuntimeError, match="planner_path_invalid"):
        preparation._remove_planner_worktree(repo, root, root / "link")
    assert (outside / "keep").exists()


def test_partial_unregistered_directory(repo, tmp_path, monkeypatch):
    original = preparation._planner_git
    def fail_during_add(source, *args):
        if args[:2] == ("worktree", "add"):
            Path(args[3]).mkdir()
            (Path(args[3]) / "partial").write_text("partial checkout")
            raise ExecutorRuntimeError("planner_git_failed")
        return original(source, *args)
    monkeypatch.setattr(preparation, "_planner_git", fail_during_add)
    with pytest.raises(ExecutorRuntimeError, match="planner_git_failed"):
        with preparation.planner_worktree(repo, tmp_path / "tasks", "goal", 1):
            pytest.fail("must not enter")
    assert not [p for p in (tmp_path / "tasks" / "planner").iterdir() if p.is_dir()]


def test_default_head_resolved_once(repo, tmp_path, monkeypatch):
    original = preparation._planner_git
    resolutions = []
    def observe(source, *args):
        result = original(source, *args)
        if args == ("rev-parse", "--verify", "HEAD^{commit}"):
            resolutions.append(result)
            (repo / "file.txt").write_text("advance after pin")
            git(repo, "commit", "-am", "advance")
        return result
    monkeypatch.setattr(preparation, "_planner_git", observe)
    with preparation.planner_worktree(repo, tmp_path / "tasks", "goal", 1) as (path, sha):
        assert resolutions == [sha]
        assert git(path, "rev-parse", "HEAD") == sha
        assert git(repo, "rev-parse", "HEAD") != sha


def test_git_failure_has_finite_code(repo, tmp_path):
    with pytest.raises(ExecutorRuntimeError) as error:
        with preparation.planner_worktree(repo, tmp_path / "tasks", "goal", 1,
                                         "missing-sensitive-reference"):
            pass
    assert str(error.value) == "planner_git_failed"
