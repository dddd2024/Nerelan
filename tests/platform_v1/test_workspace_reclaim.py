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
    try:
        os.symlink(repo, root / "link")
    except OSError:
        if os.name != "nt":
            raise
        # Unprivileged Windows accounts lack symlink privilege; directory junctions share the same link guard.
        subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "link"), str(repo)], check=True, capture_output=True)
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
    assert away.as_posix() in git(repo, "worktree", "list", "--porcelain").replace("\\", "/")


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


@pytest.mark.parametrize("setup", [
    lambda c: git(c, "branch", "--no-track", "no-upstream", "origin/main"),
    lambda c: git(c, "branch", "--track", "behind", "origin/main") and None,
])
def test_clone_branch_names_need_matching_upstream(repo, root, tmp_path, setup):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    setup(clone)
    if "behind" in git(clone, "branch"):
        # Same commit as upstream: allowed. Move upstream ahead so it differs.
        git(repo, "commit", "-q", "--allow-empty", "-m", "ahead")
        git(repo, "push", "-q", "origin", "HEAD:main")
        git(clone, "fetch", "-q")
    entry = by_name(sweep([root], now=LATER + 86400 * 365, apply=True, include_clones=True))["review-clone"]
    assert entry["reason"] == "local branch without matching upstream" and clone.exists()


def test_clone_branch_matching_upstream_is_reclaimed(repo, root, tmp_path):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    entry = by_name(sweep([root], now=LATER, apply=True, include_clones=True))["review-clone"]
    assert entry.get("removed") is True, entry["reason"]


def test_recent_fetch_in_clone_counts_as_activity(repo, root, tmp_path):
    clone = root / "review-clone"
    git(root, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    git(clone, "fetch", "-q")  # FETCH_HEAD exists, so the next fetch rewrites it in place
    follow = os.utime in os.supports_follow_symlinks
    for dirpath, dirs, files in os.walk(clone):
        for name in dirs + files:
            target = os.path.join(dirpath, name)
            if follow:
                os.utime(target, (0, 0), follow_symlinks=False)
            elif not os.path.islink(target):
                os.utime(target, (0, 0))
    os.utime(clone, (0, 0))
    git(clone, "fetch", "-q")
    now = os.stat(clone / ".git" / "FETCH_HEAD").st_mtime + 86400
    entry = by_name(sweep([root], now=now, apply=True, include_clones=True))["review-clone"]
    assert "retention" in entry["reason"] and clone.exists()


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


def _store_db(path, rows):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE tasks(id TEXT PRIMARY KEY, status TEXT, updated_at TEXT)")
        db.executemany("INSERT INTO tasks VALUES(?,?,?)", rows)
    return path


def _iso(ts):
    return workspace_reclaim.datetime.fromtimestamp(ts, workspace_reclaim.timezone.utc) \
        .replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _reclaimer(root, db, mode="apply", **kw):
    return workspace_reclaim.AutoReclaimer(root, db, mode=mode, clock=lambda: LATER, **kw)


def test_auto_config_is_on_by_default_and_rejects_bad_values():
    assert workspace_reclaim.auto_config({}) == {
        "mode": "apply", "retention_days": 3.0, "interval_hours": 24.0, "poll_minutes": 15.0,
        "preserve": False, "low_disk_gb": 10.0, "low_disk_retention_days": 1.0}
    config = workspace_reclaim.auto_config({
        "REVERSE_AGENT_WORKSPACE_RECLAIM": "delete-all",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS": "-1",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_INTERVAL_HOURS": "nan",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_POLL_MINUTES": "0.1",
    })
    assert (config["mode"], config["retention_days"], config["interval_hours"],
            config["poll_minutes"]) == ("off", 3.0, 24.0, 15.0)
    config = workspace_reclaim.auto_config({
        "REVERSE_AGENT_WORKSPACE_RECLAIM": " Apply ",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS": "7"})
    assert config["mode"] == "apply" and config["retention_days"] == 7.0


def test_configured_reclaimer_can_be_disabled_and_needs_a_file_store(root, tmp_path):
    db = str(tmp_path / "tasks.sqlite3")
    assert workspace_reclaim.configured_reclaimer(root, db, env={}).apply is True
    off = {"REVERSE_AGENT_WORKSPACE_RECLAIM": "off"}
    assert workspace_reclaim.configured_reclaimer(root, db, env=off) is None
    on = {"REVERSE_AGENT_WORKSPACE_RECLAIM": "report"}
    assert workspace_reclaim.configured_reclaimer(root, ":memory:", env=on) is None
    reclaimer = workspace_reclaim.configured_reclaimer(root, db, env=on)
    assert reclaimer.apply is False
    assert reclaimer.state_path == tmp_path / "workspace_reclaim_state.json"


def test_finished_task_is_reclaimed_after_retention_once(repo, root, tmp_path):
    old = add_worktree(repo, root, "task-old")
    fresh = add_worktree(repo, root, "task-fresh")
    running = add_worktree(repo, root, "task-run")
    db = _store_db(tmp_path / "tasks.sqlite3", [
        ("task-old", "READY_FOR_REVIEW", _iso(LATER - 4 * 86400)),
        ("task-fresh", "FAILED", _iso(LATER - 3600)),
        ("task-run", "RUNNING", _iso(LATER - 10 * 86400)),
        ("task-gone", "FAILED", _iso(LATER - 10 * 86400)),
    ])
    reclaimer = _reclaimer(root, db)
    records = reclaimer.reclaim_finished(LATER)
    assert [Path(r["path"]).name for r in records] == ["task-old"]
    assert records[0]["removed"] is True and not old.exists()
    assert fresh.exists() and running.exists()
    assert str(old) not in git(repo, "worktree", "list", "--porcelain")
    assert reclaimer.reclaim_finished(LATER) == []


def test_finished_task_with_unsafe_work_is_kept(repo, root, tmp_path):
    dirty = add_worktree(repo, root, "task-dirty")
    (dirty / "a.txt").write_text("changed\n")
    unpushed = add_worktree(repo, root, "task-unpushed")
    git(unpushed, "commit", "-q", "--allow-empty", "-m", "local")
    done = _iso(LATER - 5 * 86400)
    db = _store_db(tmp_path / "tasks.sqlite3",
                   [("task-dirty", "FAILED", done), ("task-unpushed", "READY_FOR_REVIEW", done)])
    records = {Path(r["path"]).name: r for r in _reclaimer(root, db).reclaim_finished(LATER)}
    assert records["task-dirty"]["reason"] == "uncommitted or untracked changes"
    assert records["task-unpushed"]["reason"] == "commits not on any remote branch"
    assert dirty.exists() and unpushed.exists()


def _deny_listing(monkeypatch, name):
    real = workspace_reclaim.os.scandir

    def scandir(path):
        if os.path.basename(str(path)) == name:
            raise PermissionError(5, "Access is denied", str(path))
        return real(path)

    monkeypatch.setattr(workspace_reclaim.os, "scandir", scandir)


def test_unlistable_cache_does_not_block_reclaim(repo, root, monkeypatch):
    with (repo / ".git" / "info" / "exclude").open("a") as handle:
        handle.write("__pycache__/\n")
    wt = add_worktree(repo, root, "task-1")
    (wt / "__pycache__").mkdir()
    _deny_listing(monkeypatch, "__pycache__")
    assert by_name(sweep([root], now=LATER))["task-1"]["reclaim"] is True


def test_unlistable_work_directory_keeps_the_tree(repo, root, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    (wt / "results").mkdir()
    _deny_listing(monkeypatch, "results")
    entry = by_name(sweep([root], now=LATER, apply=True))["task-1"]
    assert entry["reason"] == "tree unreadable" and wt.exists()


def test_report_mode_never_deletes(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    db = _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 5 * 86400))])
    result = _reclaimer(root, db, mode="report", state_path=tmp_path / "state.json").tick()
    assert result["finished"][0]["reclaim"] is True
    assert result["sweep"]["applied"] is False and wt.exists()


def test_full_sweep_runs_once_per_interval_across_restarts(repo, root, tmp_path):
    db = _store_db(tmp_path / "tasks.sqlite3", [])
    wt = add_worktree(repo, root, "untracked-task")
    state = tmp_path / "state.json"
    first = _reclaimer(root, db, state_path=state).tick()
    assert first["sweep"]["removed"] == 1 and not wt.exists()
    assert json.loads(state.read_text())["last_sweep_at"] == LATER
    assert _reclaimer(root, db, state_path=state).tick()["sweep"] is None
    later = workspace_reclaim.AutoReclaimer(root, db, mode="apply", state_path=state,
                                            clock=lambda: LATER + 25 * 3600)
    assert later.tick()["sweep"] is not None


def test_unreadable_store_skips_finished_pass(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    (tmp_path / "bad.sqlite3").write_text("not sqlite")
    result = _reclaimer(root, tmp_path / "bad.sqlite3").tick()
    assert result["finished"] == []
    assert by_name(result["sweep"])["task-1"]["reason"] == "task store unreadable"
    assert wt.exists()


def test_background_thread_starts_and_stops(root, tmp_path):
    reclaimer = _reclaimer(root, _store_db(tmp_path / "tasks.sqlite3", []))
    reclaimer.start()
    assert reclaimer._thread.is_alive()
    reclaimer.stop()
    assert reclaimer._thread is None


def test_auto_config_rejects_non_finite_durations():
    config = workspace_reclaim.auto_config({
        "REVERSE_AGENT_WORKSPACE_RECLAIM": "apply",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS": "inf",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_INTERVAL_HOURS": "1e309",
        "REVERSE_AGENT_WORKSPACE_RECLAIM_POLL_MINUTES": "Infinity"})
    assert (config["retention_days"], config["interval_hours"], config["poll_minutes"]) == (
        3.0, 24.0, 15.0)


def test_stop_during_a_slow_check_skips_removal_and_keeps_the_worker(
        repo, root, tmp_path, monkeypatch):
    import threading
    wt = add_worktree(repo, root, "task-1")
    db = _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 5 * 86400))])
    reclaimer = _reclaimer(root, db, state_path=tmp_path / "state.json")
    entered, release = threading.Event(), threading.Event()
    real_inspect = workspace_reclaim.inspect

    def slow_inspect(path, **kw):
        record = real_inspect(path, **kw)
        entered.set()
        release.wait(10)
        return record

    monkeypatch.setattr(workspace_reclaim, "inspect", slow_inspect)
    worker = threading.Thread(target=reclaimer.tick)
    reclaimer._thread = worker
    worker.start()
    assert entered.wait(10)
    assert reclaimer.stop(timeout=0.05) is False
    assert reclaimer._thread is worker
    reclaimer.start()
    assert reclaimer._thread is worker
    release.set()
    worker.join(10)
    assert wt.exists()
    assert reclaimer.stop() is True and reclaimer._thread is None


def test_finished_pass_ignores_task_ids_that_are_not_plain_children(repo, root, tmp_path):
    done = _iso(LATER - 5 * 86400)
    db = _store_db(tmp_path / "tasks.sqlite3",
                   [("..", "FAILED", done), (".", "FAILED", done), ("", "FAILED", done),
                    ("a/b", "FAILED", done)])
    assert _reclaimer(root, db).reclaim_finished(LATER) == []
    assert root.exists()


def _preserve_sweep(root, tmp_path, status="FAILED", name="task-1", **kw):
    db = tmp_path / "tasks.sqlite3"
    if not db.exists():
        _store_db(db, [(name, status, _iso(LATER - 5 * 86400))])
    return by_name(sweep([root], now=LATER, apply=True, task_db=db, preserve=True, **kw))[name]


def test_preserve_keeps_every_kind_of_work_before_removing(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    git(wt, "commit", "-q", "--allow-empty", "-m", "reflog only")
    orphan = git(wt, "rev-parse", "HEAD")
    git(wt, "reset", "-q", "--hard", "origin/main")
    git(wt, "commit", "-q", "--allow-empty", "-m", "unpushed")
    head = git(wt, "rev-parse", "HEAD")
    (wt / "a.txt").write_text("staged\n")
    git(wt, "add", "a.txt")
    (wt / "a.txt").write_text("unstaged\n")
    (wt / "new.txt").write_text("untracked\n")
    entry = _preserve_sweep(root, tmp_path)
    assert entry["removed"] is True and not wt.exists()
    ref = entry["preserved_ref"]
    assert ref.startswith("refs/nerelan/reclaimed/task-1/")
    assert git(repo, "show", f"{ref}:a.txt") == "unstaged"
    assert git(repo, "show", f"{ref}:new.txt") == "untracked"
    assert git(repo, "show", f"{ref}^2:a.txt") == "staged"
    reachable = git(repo, "rev-list", ref).split()
    assert head in reachable and orphan in reachable


def test_preserve_keeps_a_deleted_file_deleted(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    (wt / "a.txt").unlink()
    ref = _preserve_sweep(root, tmp_path)["preserved_ref"]
    assert git(repo, "ls-tree", "--name-only", ref) == ""


@pytest.mark.parametrize("status", ["RUNNING", "QUEUED", "INTERRUPTED"])
def test_preserve_never_touches_an_unfinished_task(repo, root, tmp_path, status):
    wt = add_worktree(repo, root, "task-1")
    (wt / "a.txt").write_text("x\n")
    assert _preserve_sweep(root, tmp_path, status)["reclaim"] is False and wt.exists()


def test_preserve_needs_a_known_task(repo, root, tmp_path):
    wt = add_worktree(repo, root, "unknown")
    (wt / "a.txt").write_text("x\n")
    db = _store_db(tmp_path / "tasks.sqlite3", [])
    for task_db in (None, db):
        entry = by_name(sweep([root], now=LATER, apply=True, task_db=task_db, preserve=True))["unknown"]
        assert entry["reason"] == "uncommitted or untracked changes" and wt.exists()


@pytest.mark.parametrize("block", ["ignored", "hidden", "locked", "conflict"])
def test_preserve_relaxes_no_other_check(repo, root, tmp_path, block):
    wt = add_worktree(repo, root, "task-1")
    (wt / "new.txt").write_text("x\n")
    if block == "ignored":
        _ignore(wt, "*.env")
        (wt / "secret.env").write_text("k\n")
    elif block == "hidden":
        git(wt, "update-index", "--assume-unchanged", "a.txt")
    elif block == "locked":
        git(repo, "worktree", "lock", str(wt))
    else:
        blob = git(wt, "hash-object", "-w", "a.txt")
        subprocess.run(["git", "update-index", "--index-info"], cwd=wt, check=True,
                       input=(f"0 {'0' * 40}\ta.txt\n100644 {blob} 1\ta.txt\n"
                              f"100644 {blob} 2\ta.txt\n").encode())
    entry = _preserve_sweep(root, tmp_path)
    assert not entry.get("removed") and wt.exists() and (wt / "new.txt").exists()


def test_work_written_during_preservation_keeps_the_checkout(repo, root, tmp_path, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    (wt / "new.txt").write_text("x\n")
    real, calls = workspace_reclaim._snapshot, []

    def racing(path, head):
        calls.append(1)
        if len(calls) == 2:
            (wt / "late.txt").write_text("late\n")
        return real(path, head)

    monkeypatch.setattr(workspace_reclaim, "_snapshot", racing)
    entry = _preserve_sweep(root, tmp_path)
    assert entry["removed"] is False and (wt / "late.txt").exists()


def _fixture_repo(path, content="x\n"):
    git(path.parent, "init", "-q", str(path))
    (path / "fixture.txt").write_text(content)
    return path


@pytest.mark.parametrize("nested", ["task-1794752891525-b7316c826cf2",
                                    "task_workspaces/task-1794752891525-b7316c826cf2"])
def test_test_fixture_repositories_do_not_block(repo, root, nested):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "task-[0-9]*-*/", "task_workspaces/")
    (wt / nested).parent.mkdir(exist_ok=True)
    _fixture_repo(wt / nested)
    assert by_name(sweep([root], now=LATER, apply=True))["task-1"]["removed"] is True
    assert not wt.exists()


@pytest.mark.parametrize("change", ["remote", "extra", "name", "untracked"])
def test_other_nested_repositories_still_block(repo, root, change):
    wt = add_worktree(repo, root, "task-1")
    if change != "untracked":
        _ignore(wt, "task-*/")
    nested = _fixture_repo(wt / ("task-notes" if change == "name" else "task-1794752891525-b7316c826cf2"))
    if change == "remote":
        git(nested, "remote", "add", "origin", "https://example.invalid/x.git")
    elif change == "extra":
        (nested / "work.py").write_text("x\n")
    assert not by_name(sweep([root], now=LATER, apply=True))["task-1"]["reclaim"]
    assert nested.exists()


def _disk(free_gb):
    return lambda path: type("U", (), {"free": int(free_gb * 2 ** 30), "total": 100 * 2 ** 30})()


def test_low_disk_sweeps_early_with_the_shorter_retention(repo, root, tmp_path):
    age = os.stat(add_worktree(repo, root, "task-1")).st_mtime
    db = _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(age))])
    state = tmp_path / "state.json"
    clock = [age + 2 * 86400]
    state.write_text(json.dumps({"last_sweep_at": clock[0]}))

    def reclaimer(free):
        return workspace_reclaim.AutoReclaimer(root, db, mode="apply", state_path=state,
                                               clock=lambda: clock[0], disk_usage=_disk(free))

    assert reclaimer(50).tick()["sweep"] is None and (root / "task-1").exists()
    low = reclaimer(5)
    result = low.tick()
    assert result["disk"]["low"] is True and result["sweep"]["removed"] == 1
    assert json.loads(state.read_text())["report"]["disk"]["free_gb"] == 5
    clock[0] += 900
    assert low.tick()["sweep"] is None  # at most hourly
    clock[0] += 3600
    assert low.tick()["sweep"] is not None


def test_low_disk_never_lengthens_retention_or_deletes_in_report_mode(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    db = _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 5 * 86400))])
    reclaimer = _reclaimer(root, db, mode="report", retention_days=0.5, disk_usage=_disk(1))
    assert reclaimer.low_disk_retention_days == 0.5
    assert reclaimer.tick()["sweep"]["applied"] is False and wt.exists()


def test_unreadable_disk_is_not_low(root, tmp_path):
    def broken(path):
        raise OSError("gone")
    assert _reclaimer(root, tmp_path / "x", disk_usage=broken).disk()["low"] is False


def _junction(link, target):
    target.mkdir()
    (target / "precious.txt").write_text("keep\n")
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)


windows_only = pytest.mark.skipif(os.name != "nt", reason="NTFS junctions")


@windows_only
@pytest.mark.parametrize("place", ["link", "sub/link", "a.txt"])
def test_a_junction_keeps_the_worktree_and_its_target(repo, root, tmp_path, place):
    wt = add_worktree(repo, root, "task-1")
    (wt / place).parent.mkdir(exist_ok=True)
    if place == "a.txt":
        (wt / place).unlink()
    _junction(wt / place, tmp_path / "outside")
    entry = _preserve_sweep(root, tmp_path)
    assert entry["reason"] == "contains a junction" and wt.exists()
    assert (tmp_path / "outside" / "precious.txt").exists()


@windows_only
@pytest.mark.parametrize("dirty", [False, True])
def test_a_node_modules_junction_is_unlinked_not_followed(repo, root, tmp_path, dirty):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "node_modules")
    _junction(wt / "node_modules", tmp_path / "shared")
    if dirty:
        (wt / "new.txt").write_text("x\n")
    assert _preserve_sweep(root, tmp_path)["removed"] is True and not wt.exists()
    assert (tmp_path / "shared" / "precious.txt").exists()


def _goal_db(path, task_status, goal_status, window="STOPPED", phase="", classification="", escalated=False):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE tasks(id TEXT, status TEXT, updated_at TEXT, failure_classification TEXT)")
        db.execute("INSERT INTO tasks VALUES('task-1', ?, ?, ?)",
                   (task_status, _iso(LATER - 5 * 86400), classification))
        db.execute("CREATE TABLE platform_goals(id TEXT, status TEXT, window_id TEXT)")
        db.execute("CREATE TABLE platform_goal_task_links(goal_id TEXT, task_id TEXT)")
        db.execute("CREATE TABLE platform_autonomous_windows(id TEXT, status TEXT)")
        db.execute("CREATE TABLE platform_landing_state(goal_id TEXT, phase TEXT)")
        db.execute("INSERT INTO platform_goals VALUES('g', ?, 'w')", (goal_status,))
        db.execute("CREATE TABLE platform_task_escalations(goal_id TEXT, from_task_id TEXT)")
        db.execute("INSERT INTO platform_task_escalations VALUES('g', 'task-1')" if escalated else
                   "INSERT INTO platform_goal_task_links VALUES('g', 'task-1')")
        db.execute("INSERT INTO platform_autonomous_windows VALUES('w', ?)", (window,))
        if phase:
            db.execute("INSERT INTO platform_landing_state VALUES('g', ?)", (phase,))


@pytest.mark.parametrize("kept,task_status,goal_status,kw", [
    (True, "READY_FOR_REVIEW", "RUNNING", {}),
    (True, "BLOCKED", "BLOCKED", {}),
    (True, "FAILED", "BLOCKED", {"window": "ACTIVE"}),
    (True, "FAILED", "BLOCKED", {"classification": "model_review_rejected"}),
    (True, "READY_FOR_REVIEW", "COMPLETED", {"window": "ACTIVE"}),  # complete, not published yet
    (True, "READY_FOR_REVIEW", "COMPLETED", {"phase": "WAITING"}),
    (True, "READY_FOR_REVIEW", "RUNNING", {"phase": "COMPLETE"}),
    (True, "READY_FOR_REVIEW", "RUNNING", {"window": "ACTIVE", "escalated": True}),  # a repair reads it
    (False, "FAILED", "BLOCKED", {}),
    (False, "READY_FOR_REVIEW", "COMPLETED", {}),
    (False, "READY_FOR_REVIEW", "COMPLETED", {"phase": "COMPLETE", "window": "ACTIVE"}),
    (False, "READY_FOR_REVIEW", "SUPERSEDED", {"window": "ACTIVE"}),
])
def test_what_an_open_goal_may_need_is_kept(repo, root, tmp_path, kept, task_status, goal_status, kw):
    wt = add_worktree(repo, root, "task-1")
    db = tmp_path / "tasks.sqlite3"
    _goal_db(db, task_status, goal_status, **kw)
    if kept:
        [record] = _reclaimer(root, db).reclaim_finished(LATER)
        assert record["reason"] == "an open goal may still need it"
    entry = _preserve_sweep(root, tmp_path)
    assert wt.exists() is kept and (entry["reason"] == "an open goal may still need it") is kept


def test_full_sweep_waits_for_the_task_not_only_the_tree(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 3600))])
    assert "task finished recently" in _preserve_sweep(root, tmp_path)["reason"] and wt.exists()


def test_a_fixture_repository_with_other_history_blocks(repo, root):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "task-[0-9]*-*/")
    nested = _fixture_repo(wt / "task-1794752891525-b7316c826cf2")
    git(nested, "add", "fixture.txt")
    git(nested, "commit", "-qm", "fixture")
    git(nested, "checkout", "-qb", "work")
    (nested / "work.py").write_text("x\n")
    git(nested, "add", "work.py")
    git(nested, "commit", "-qm", "work")
    git(nested, "checkout", "-q", "-")
    assert not (nested / "work.py").exists()
    assert not by_name(sweep([root], now=LATER, apply=True))["task-1"]["reclaim"] and nested.exists()


def test_a_fixture_repository_that_is_not_ignored_blocks_preserve(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    nested = _fixture_repo(wt / "task-1794752891525-b7316c826cf2")
    git(nested, "add", "fixture.txt")
    git(nested, "commit", "-qm", "fixture")
    assert not _preserve_sweep(root, tmp_path)["reclaim"] and nested.exists()


@pytest.mark.parametrize("renamed", [False, True])
def test_intent_to_add_keeps_the_worktree(repo, root, tmp_path, renamed):
    wt = add_worktree(repo, root, "task-1")
    _ignore(wt, "*.log")
    (wt / "x.log").write_text("x\n")
    git(wt, "add", "-N", "-f", "x.log")
    if renamed:  # git would report the pair as a rename
        (wt / "x.log").write_text((wt / "a.txt").read_text())
        (wt / "a.txt").unlink()
    assert _preserve_sweep(root, tmp_path)["reason"] == "intent-to-add entries" and wt.exists()


@pytest.mark.parametrize("state", ["rebase-merge/autostash", "MERGE_HEAD", "BISECT_LOG",
                                   "refs/worktree/mine"])
def test_operation_state_keeps_the_worktree(repo, root, tmp_path, state):
    wt = add_worktree(repo, root, "task-1")
    target = workspace_reclaim._gitdir(wt) / state
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(git(wt, "rev-parse", "HEAD") + "\n")
    old = time.time() - 60
    os.utime(target, (old, old))
    assert _preserve_sweep(root, tmp_path)["reason"] == "operation in progress or refs of its own"
    assert wt.exists()


def test_a_long_reflog_is_preserved_and_the_index_is_untouched(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    tree, main = git(wt, "rev-parse", "HEAD^{tree}"), git(wt, "rev-parse", "HEAD")
    commits = [git(wt, "commit-tree", tree, "-p", main, "-m", f"c{n}") for n in range(120)]
    log = workspace_reclaim._gitdir(wt) / "logs" / "HEAD"
    with open(log, "a", newline="\n") as out:
        for sha in commits:
            out.write(f"{main} {sha} t <t@t> 1700000000 +0000\tx\n")
    (wt / "new.txt").write_text("x\n")
    index = workspace_reclaim._gitdir(wt) / "index"
    before = index.read_bytes()
    db = _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 5 * 86400))])
    [record] = sweep([root], now=LATER, task_db=db, preserve=True)["entries"]
    ref = workspace_reclaim.preserve_work(record)
    assert index.read_bytes() == before
    assert set(commits) <= set(git(repo, "rev-list", ref).split())


def test_the_hold_lookup_reads_the_real_schema_and_fails_closed(repo, root, tmp_path):
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.run_store import TaskStore

    def holds(name):
        return workspace_reclaim._task_holds(tmp_path / name, now=LATER, retention_days=1)
    store = TaskStore(str(tmp_path / "real.sqlite3"))
    try:
        PlatformControlStore(store)
        assert holds("real.sqlite3") == {}
    finally:
        store._conn.close()
    _store_db(tmp_path / "tasks.sqlite3", [("task-1", "FAILED", _iso(LATER - 5 * 86400))])
    with sqlite3.connect(tmp_path / "tasks.sqlite3") as db:
        db.execute("CREATE TABLE platform_goals(id TEXT, status TEXT)")
    assert holds("tasks.sqlite3") is None and holds("missing.sqlite3") is None
    wt = add_worktree(repo, root, "task-1")
    assert _preserve_sweep(root, tmp_path)["reason"] == "task store unreadable" and wt.exists()


def test_a_failed_intent_to_add_check_keeps_the_worktree(repo, root, tmp_path, monkeypatch):
    wt = add_worktree(repo, root, "task-1")
    git(wt, "commit", "-q", "--allow-empty", "-m", "reflog only")
    git(wt, "reset", "-q", "--hard", "origin/main")
    real = workspace_reclaim._git
    monkeypatch.setattr(workspace_reclaim, "_git",
                        lambda args, *a, **k: None if args[0] == "diff" else real(args, *a, **k))
    assert _preserve_sweep(root, tmp_path)["reclaim"] is False and wt.exists()


def test_a_same_size_edit_with_the_indexed_timestamp_is_not_missed(repo, root, tmp_path):
    wt = add_worktree(repo, root, "task-1")
    path = wt / "a.txt"
    path.write_text("AAAA\n")
    git(wt, "add", "a.txt")
    when = os.stat(path).st_mtime_ns
    path.write_text("BBBB\n")
    os.utime(path, ns=(when, when))
    # As git sees a racy entry: the index is no newer than the file it describes.
    os.utime(workspace_reclaim._gitdir(wt) / "index", ns=(when, when))
    entry = _preserve_sweep(root, tmp_path)
    assert git(repo, "show", f"{entry['preserved_ref']}:a.txt") == "BBBB"


def test_reclaim_releases_superseded_failed_escalations_but_keeps_active_or_review_ancestors(repo, root, tmp_path):
    wt_old_fail = add_worktree(repo, root, "t-old-fail")
    wt_new_running = add_worktree(repo, root, "t-old-wait")
    wt_review_esc = add_worktree(repo, root, "t-rev-rej")
    wt_pub_esc = add_worktree(repo, root, "t-pub")
    db = tmp_path / "tasks.sqlite3"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, updated_at TEXT, worktree_path TEXT, failure_classification TEXT);
        CREATE TABLE platform_goals (id TEXT PRIMARY KEY, status TEXT, window_id TEXT);
        CREATE TABLE platform_autonomous_windows (id TEXT PRIMARY KEY, status TEXT);
        CREATE TABLE platform_landing_state (goal_id TEXT, phase TEXT);
        CREATE TABLE platform_goal_task_links (goal_id TEXT, task_id TEXT);
        CREATE TABLE platform_task_escalations (goal_id TEXT, from_task_id TEXT, to_task_id TEXT);
        CREATE TABLE platform_publications (task_id TEXT);
        """
    )
    old_ts = "2026-01-01T00:00:00Z"
    conn.executemany(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
        [
            ("t-old-fail", "FAILED", old_ts, str(wt_old_fail), "functional_check_failed"),
            ("t-repl-done", "FAILED", old_ts, "", "functional_check_failed"),
            ("t-old-wait", "FAILED", old_ts, str(wt_new_running), "functional_check_failed"),
            ("t-repl-run", "RUNNING", old_ts, str(wt_new_running), ""),
            ("t-rev-rej", "FAILED", old_ts, str(wt_review_esc), "model_review_rejected"),
            ("t-pub", "FAILED", old_ts, str(wt_pub_esc), "functional_check_failed"),
        ],
    )
    conn.execute("INSERT INTO platform_autonomous_windows VALUES ('w-1', 'ACTIVE')")
    conn.execute("INSERT INTO platform_goals VALUES ('g-1', 'EXECUTING', 'w-1')")
    conn.executemany(
        "INSERT INTO platform_task_escalations VALUES (?, ?, ?)",
        [
            ("g-1", "t-old-fail", "t-repl-done"),
            ("g-1", "t-old-wait", "t-repl-run"),
            ("g-1", "t-rev-rej", "t-repl-done"),
            ("g-1", "t-pub", "t-repl-done"),
        ],
    )
    conn.execute("INSERT INTO platform_publications VALUES ('t-pub')")
    conn.commit()
    conn.close()

    report = sweep([root], task_db=db, now=LATER, apply=False)
    entries = by_name(report)
    assert entries["t-old-fail"]["reclaim"] is True
    assert entries["t-old-wait"]["reclaim"] is False and entries["t-old-wait"]["reason"] == "an open goal may still need it"
    assert entries["t-rev-rej"]["reclaim"] is False and entries["t-rev-rej"]["reason"] == "an open goal may still need it"
    assert entries["t-pub"]["reclaim"] is False and entries["t-pub"]["reason"] == "an open goal may still need it"
