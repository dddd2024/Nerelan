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


def test_failed_delete_is_reported(repo, root, tmp_path, monkeypatch):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))

    def locked(path):
        raise PermissionError("in use")

    monkeypatch.setattr(workspace_reclaim, "_remove_tree", locked)
    record = {"path": str(clone), "name": clone.name, "kind": "clone", "reclaim": True, "reason": ""}
    result = workspace_reclaim.remove(record)
    assert result["removed"] is False and "in use" in result["error"]


def test_git_refusal_is_final_and_never_falls_back_to_rmtree(repo, root, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    (wt / "late.txt").write_text("new work\n")
    monkeypatch.setattr(workspace_reclaim, "_remove_tree",
                        lambda path: pytest.fail("rmtree after git refused"))
    record = {"path": str(wt), "name": wt.name, "kind": "worktree", "reclaim": True, "reason": ""}
    result = workspace_reclaim.remove(record)
    assert result["removed"] is False and result["error"].startswith("git worktree remove")
    assert (wt / "late.txt").exists()


def _ignore(wt, *patterns):
    (wt / ".git").read_text()  # linked worktree: use the per-worktree exclude
    exclude = Path(git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "info" / "exclude"
    exclude.parent.mkdir(exist_ok=True)
    exclude.write_text("\n".join(patterns) + "\n")


@pytest.mark.parametrize("rel", [".env", "out/result.bin", ".platform_v1_runtime/run/evidence.json"])
def test_ignored_work_files_are_kept(repo, root, rel):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, ".env", "out/", ".platform_v1_runtime/")
    (wt / rel).parent.mkdir(parents=True, exist_ok=True)
    (wt / rel).write_text("secret or evidence\n")
    os.utime(wt / rel, (0, 0))
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"].startswith("ignored files present") and (wt / rel).exists()


def test_ignored_caches_do_not_block(repo, root):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "__pycache__/", "node_modules/", "*.pyc")
    (wt / "__pycache__").mkdir()
    (wt / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"x")
    (wt / "frontend" / "node_modules" / "pkg").mkdir(parents=True)
    (wt / "frontend" / "node_modules" / "pkg" / "i.js").write_text("x")
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry.get("removed") is True, entry["reason"]
    assert not wt.exists()


def test_native_execution_scratch_does_not_block(repo, root):
    wt = add_worktree(repo, root, "task-1")
    for name in (".nt", ".nt-0a1b2c3d4e5f", ".nt-9f8e7d6c5b4a"):
        (wt / name).mkdir()
        (wt / name / ".gitignore").write_text("*\n")
        (wt / name / "tmpfile").write_text("scratch\n")
    assert by_name(sweep([root], now=LATER, apply=True))["task-1"].get("removed") is True
    assert not wt.exists()


@pytest.mark.parametrize("name", [".nt-business-data", ".nt-0A1B2C3D4E5F", ".ntx"])
def test_other_scratch_like_names_are_kept(repo, root, name):
    wt = add_worktree(repo, root, "task-1")
    (wt / name).mkdir()
    (wt / name / ".gitignore").write_text("*\n")
    (wt / name / "data").write_text("x")
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"].startswith("ignored files present") and wt.exists()


def test_scratch_name_below_top_level_is_not_special(repo, root):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "out/")
    (wt / "out" / ".nt-0a1b2c3d4e5f").mkdir(parents=True)
    (wt / "out" / ".nt-0a1b2c3d4e5f" / "result.bin").write_text("x")
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"].startswith("ignored files present") and wt.exists()


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
@pytest.mark.parametrize("kind", ["worktree", "clone"])
def test_hidden_index_edits_are_kept(repo, root, tmp_path, flag, kind):
    if kind == "worktree":
        target = add_worktree(repo, root, "task-1")
    else:
        target = root / "task-1"
        git(root, "clone", "-q", str(tmp_path / "remote.git"), str(target))
    git(target, "update-index", flag, "a.txt")
    (target / "a.txt").write_text("local secret\n")
    os.utime(target / "a.txt", (0, 0))
    entry = by_name(sweep([root], now=LATER, apply=True, include_clones=True))["task-1"]
    assert entry["reason"] == "assume-unchanged or skip-worktree entries"
    assert (target / "a.txt").read_text() == "local secret\n"


@pytest.mark.parametrize("kind", ["worktree", "clone"])
def test_reflog_only_commits_are_kept(repo, root, tmp_path, kind):
    if kind == "worktree":
        target = add_worktree(repo, root, "task-1")
    else:
        target = root / "task-1"
        git(root, "clone", "-q", str(tmp_path / "remote.git"), str(target))
    git(target, "commit", "-q", "--allow-empty", "-m", "abandoned")
    git(target, "reset", "-q", "--hard", "origin/main")
    entry = by_name(sweep([root], now=LATER, apply=True, include_clones=True))["task-1"]
    assert entry["reason"] == "commits not on any remote branch" and target.exists()


def test_other_missing_worktrees_stay_registered(repo, root, tmp_path):
    add_worktree(repo, root, "task-1")
    away = tmp_path / "away"
    git(repo, "worktree", "add", "-q", "--detach", str(away), "origin/main")
    away.rename(tmp_path / "away-moved")  # missing but unlocked: prune would drop it
    assert by_name(sweep([root], now=LATER, apply=True))["task-1"]["removed"] is True
    assert str(away) in git(repo, "worktree", "list", "--porcelain")


def test_locked_worktree_is_kept(repo, root):
    wt = add_worktree(repo, root, "task-1")
    git(repo, "worktree", "lock", str(wt))
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"] == "worktree is locked" and wt.exists()


def test_recent_change_deep_in_tree_is_kept(repo, root):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "__pycache__/")
    (wt / "d" / "e" / "__pycache__").mkdir(parents=True)
    (wt / "d" / "e" / "__pycache__" / "x.pyc").write_bytes(b"x")
    for p in (wt, wt / "d", wt / "d" / "e", wt / "a.txt"):
        os.utime(p, (0, 0))
    now = os.stat(wt / "d" / "e" / "__pycache__" / "x.pyc").st_mtime + 86400
    entry = by_name(sweep([root], now=now, apply=True))["task-1"]
    assert "retention" in entry["reason"] and wt.exists()


def test_nested_repository_is_kept(repo, root):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "node_modules/")
    git(wt, "init", "-q", str(wt / "node_modules" / "vendored"))
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"] == "contains a nested repository or submodule" and wt.exists()


def test_unpushed_tag_in_clone_is_kept(repo, root, tmp_path):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    git(clone, "commit", "-q", "--allow-empty", "-m", "tagged only")
    git(clone, "tag", "v-local")
    git(clone, "reset", "-q", "--hard", "origin/main")
    entry = by_name(sweep([root], now=LATER, apply=True, include_clones=True))["review-clone"]
    assert entry["reason"] == "commits not on any remote branch" and clone.exists()


def test_gitfile_pointing_at_full_repository_is_kept(repo, root, tmp_path):
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(other))
    fake = root / "fake"
    fake.mkdir()
    (fake / ".git").write_text(f"gitdir: {other / '.git'}\n")
    (fake / "a.txt").write_text("a\n")
    entry = by_name(sweep([root], now=LATER, apply=True))["fake"]
    assert entry["reason"] == "gitdir is not a linked worktree entry" and fake.exists()


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
