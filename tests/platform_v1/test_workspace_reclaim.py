"""Workspace reclaim never deletes work that is dirty, unpushed, recent or still running."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

import pytest

from reverse_agent.platform_v1 import workspace_reclaim
from reverse_agent.platform_v1.workspace_reclaim import main, sweep

LATER = time.time() + 30 * 86400


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    main_repo = tmp_path / "main"
    git(tmp_path, "clone", "-q", str(remote), str(main_repo))
    (main_repo / "a.txt").write_text("a\n")
    git(main_repo, "add", "a.txt")
    git(main_repo, "commit", "-qm", "init")
    git(main_repo, "push", "-q", "origin", "HEAD:main")
    git(main_repo, "fetch", "-q")
    return main_repo


@pytest.fixture
def root(tmp_path):
    path = tmp_path / "task_workspaces"
    path.mkdir()
    return path


def add_worktree(repo, root, name):
    dest = root / name
    git(repo, "worktree", "add", "-q", "--detach", str(dest), "origin/main")
    return dest


def by_name(report):
    return {Path(e["path"]).name: e for e in report["entries"]}


def test_dry_run_reports_but_keeps_everything(repo, root):
    wt = add_worktree(repo, root, "task-1")
    report = sweep([root], now=LATER)
    assert by_name(report)["task-1"]["reclaim"] is True
    assert report["removed"] == 0 and wt.exists()


def test_apply_removes_clean_pushed_worktree_and_prunes(repo, root):
    wt = add_worktree(repo, root, "task-1")
    report = sweep([root], now=LATER, apply=True)
    assert by_name(report)["task-1"]["removed"] is True
    assert not wt.exists()
    assert str(wt) not in git(repo, "worktree", "list", "--porcelain")
    assert (repo / "a.txt").exists()


@pytest.mark.parametrize("mutate,reason", [
    (lambda wt: (wt / "a.txt").write_text("changed\n"), "uncommitted or untracked changes"),
    (lambda wt: (wt / "new.txt").write_text("x\n"), "uncommitted or untracked changes"),
    (lambda wt: [(wt / "d").mkdir(), (wt / "d" / "deep.txt").write_text("x\n")],
     "uncommitted or untracked changes"),
    (lambda wt: git(wt, "commit", "-q", "--allow-empty", "-m", "local"),
     "commits not on any remote branch"),
])
def test_unsafe_worktrees_are_kept(repo, root, mutate, reason):
    wt = add_worktree(repo, root, "task-1")
    mutate(wt)
    report = sweep([root], now=LATER, apply=True)
    entry = by_name(report)["task-1"]
    assert entry["reclaim"] is False and entry["reason"] == reason
    assert wt.exists()


def test_recent_worktree_is_kept(repo, root):
    wt = add_worktree(repo, root, "task-1")
    entry = by_name(sweep([root], apply=True))["task-1"]
    assert entry["reclaim"] is False and "retention" in entry["reason"]
    assert wt.exists()


def test_non_git_symlink_and_planner_entries_are_kept(repo, root, tmp_path):
    (root / "scratch").mkdir()
    (root / "scratch" / "notes.txt").write_text("keep\n")
    planner = add_worktree(repo, root, "goal-r1-" + "0" * 32)
    (root / (planner.name + ".planner-owner.json")).write_text("{}")
    os.symlink(repo, root / "link")
    report = sweep([root], now=LATER, apply=True)
    entries = by_name(report)
    assert entries["scratch"]["reason"] == "not a git checkout"
    assert entries[planner.name]["reason"].startswith("planner worktree")
    assert entries["link"]["reason"].startswith("symlink")
    assert planner.exists() and (root / "scratch").exists() and repo.exists()
    assert report["removed"] == 0


def test_clones_need_opt_in_and_are_kept_when_hosting_worktrees(repo, root, tmp_path):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    host = root / "host-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(host))
    git(host, "worktree", "add", "-q", "--detach", str(tmp_path / "elsewhere"), "origin/main")
    assert by_name(sweep([root], now=LATER, apply=True))["review-clone"]["reason"].startswith(
        "standalone clone")
    report = sweep([root], now=LATER, apply=True, include_clones=True)
    assert by_name(report)["review-clone"]["removed"] is True
    assert by_name(report)["host-clone"]["reason"] == "clone hosts linked worktrees"
    assert not clone.exists() and host.exists()


@pytest.mark.parametrize("setup,reason", [
    (lambda c: git(c, "checkout", "-qb", "local-only") or git(c, "commit", "-q", "--allow-empty", "-m", "x")
     or git(c, "checkout", "-q", "main"), "commits not on any remote branch"),
    (lambda c: [(c / "a.txt").write_text("stashed\n"), git(c, "stash", "-q")],
     "stash present or unreadable"),
])
def test_clone_with_unpushed_branch_or_stash_is_kept(repo, root, tmp_path, setup, reason):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    setup(clone)
    entry = by_name(sweep([root], now=LATER, apply=True, include_clones=True))["review-clone"]
    assert entry["reason"] == reason and clone.exists()


def _task_db(path, rows):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE tasks(id TEXT PRIMARY KEY, status TEXT)")
        db.executemany("INSERT INTO tasks VALUES(?,?)", rows)
    return path


def test_task_store_keeps_non_terminal_tasks(repo, root, tmp_path):
    add_worktree(repo, root, "task-run")
    add_worktree(repo, root, "task-done")
    db = _task_db(tmp_path / "tasks.sqlite3", [("task-run", "RUNNING"), ("task-done", "FAILED")])
    before = db.read_bytes()
    entries = by_name(sweep([root], now=LATER, apply=True, task_db=db))
    assert entries["task-run"]["reason"] == "task still RUNNING"
    assert entries["task-done"]["removed"] is True
    assert db.read_bytes() == before


def test_unreadable_task_store_keeps_everything(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    (tmp_path / "bad.sqlite3").write_text("not sqlite")
    entry = by_name(sweep([root], now=LATER, apply=True, task_db=tmp_path / "bad.sqlite3"))["task-1"]
    assert entry["reason"] == "task store unreadable" and wt.exists()


def test_recheck_before_delete_catches_late_change(repo, root, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    real = workspace_reclaim.inspect
    calls = []

    def racing(path, **kw):
        calls.append(path)
        if len(calls) == 2:
            (wt / "late.txt").write_text("new work\n")
        return real(path, **kw)

    monkeypatch.setattr(workspace_reclaim, "inspect", racing)
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reclaim"] is False and (wt / "late.txt").exists()


def test_read_only_files_are_removed(repo, root):
    wt = add_worktree(repo, root, "task-1")
    monkey_target = wt / "a.txt"
    os.chmod(monkey_target, 0o444)
    os.chmod(wt, 0o755)
    # Force the rmtree fallback path by making git worktree remove unavailable.
    record = workspace_reclaim.inspect(wt, now=LATER, retention_days=3, task_statuses={})
    record["kind"] = "clone"
    assert workspace_reclaim.remove(record)["removed"] is True
    assert not wt.exists()


def test_failed_delete_is_reported(repo, root, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    monkeypatch.setattr(workspace_reclaim, "_git", lambda *a, **k: None)

    def locked(path):
        raise PermissionError("in use")

    monkeypatch.setattr(workspace_reclaim, "_remove_tree", locked)
    record = {"path": str(wt), "name": wt.name, "kind": "worktree", "reclaim": True, "reason": ""}
    result = workspace_reclaim.remove(record)
    assert result["removed"] is False and "in use" in result["error"]


def test_windows_long_path_prefix(monkeypatch):
    monkeypatch.setattr(workspace_reclaim.os, "name", "nt")
    monkeypatch.setattr(Path, "absolute", lambda self: self)
    assert workspace_reclaim._long(Path("C:\\a\\b")) == "\\\\?\\C:\\a\\b"


def test_pattern_filter_and_cli(repo, root, tmp_path, capsys):
    add_worktree(repo, root, "nerelan-1")
    add_worktree(repo, root, "other")
    out = tmp_path / "r.json"
    os.utime(root / "nerelan-1", (0, 0))
    assert main(["--root", str(root), "--pattern", "^nerelan-", "--json", str(out),
                 "--retention-days", "0"]) == 0
    report = json.loads(out.read_text())
    assert [Path(e["path"]).name for e in report["entries"]] == ["nerelan-1"]
    assert report["applied"] is False
    assert "(dry run)" in capsys.readouterr().out
    assert (root / "nerelan-1").exists()
