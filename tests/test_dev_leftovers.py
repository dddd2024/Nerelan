from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

if shutil.which("git") is None:
    pytest.skip("git is required", allow_module_level=True)

MODULE = runpy.run_path(str(REPO_ROOT / "scripts/dev_leftovers.py"))
scan = MODULE["scan"]
render_markdown = MODULE["render_markdown"]
summary_line = MODULE["summary_line"]
main = MODULE["main"]

GIT_PREFIX = [
    "git",
    "-c", "user.name=t",
    "-c", "user.email=t@example.com",
    "-c", "commit.gpgsign=false",
    "-c", "init.defaultBranch=main",
]


def git(cwd: Path, *args: str) -> str:
    # Optional locks off: a fixture `git status` must not refresh .git/index between snapshots.
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(
        [*GIT_PREFIX, *args], cwd=str(cwd), check=True, capture_output=True, text=True, env=env
    )
    return proc.stdout.strip()


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("leftovers")
    remote = base / "remote.git"
    remote.mkdir()
    git(remote, "init", "--bare")

    main_repo = base / "main"
    main_repo.mkdir()
    git(main_repo, "init")
    (main_repo / "a.txt").write_text("hello\n")
    git(main_repo, "add", "a.txt")
    git(main_repo, "commit", "-m", "init")
    git(main_repo, "remote", "add", "origin", str(remote))
    git(main_repo, "push", "origin", "main")

    root = base / "root"
    root.mkdir()

    git(base, "clone", str(remote), str(root / "Nerelan-pr949"))

    local = root / "nrl-issue757"
    local.mkdir()
    git(local, "init")
    (local / "x.txt").write_text("local only\n")
    git(local, "add", "x.txt")
    git(local, "commit", "-m", "local")

    git(base, "clone", str(remote), str(root / "tmp_dirty"))
    (root / "tmp_dirty" / "untracked.txt").write_text("dirty\n")

    scratch = root / "nerelan_scratch"
    scratch.mkdir()
    (scratch / "one.txt").write_text("12345")
    (scratch / "sub").mkdir()
    (scratch / "sub" / "two.txt").write_text("abcdefghij")

    (root / "_run_gates.py").write_bytes(b"print('x')\n")  # bytes: no CRLF translation on Windows

    unrelated = root / "unrelated_project"
    unrelated.mkdir()
    (unrelated / "f.txt").write_text("nope")

    wt = root / "issue1001"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {base / 'does-not-exist'}\n")

    return {"base": base, "root": root, "repo": main_repo}


@pytest.fixture(scope="module")
def report(world):
    return scan(world["root"], world["repo"])


def by_name(report):
    return {e["name"]: e for e in report["entries"]}


def snapshot(root: Path):
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            st = os.lstat(p)
            snap[p] = (st.st_mtime_ns, st.st_size)
    return snap


def test_safe_delete_clone(report):
    e = by_name(report)["Nerelan-pr949"]
    assert e["classification"] == "safe_delete"
    assert e["git_kind"] == "repo"
    assert e["kind"] == "dir"
    assert e["dirty"] is False
    assert e["head_on_remote"] is True
    assert e["issue_numbers"] == [949]


def test_local_only_commit_is_review(report):
    e = by_name(report)["nrl-issue757"]
    assert e["classification"] == "review"
    assert e["head_on_remote"] is False
    assert e["issue_numbers"] == [757]


def test_dirty_clone_is_review(report):
    e = by_name(report)["tmp_dirty"]
    assert e["classification"] == "review"
    assert e["dirty"] is True
    assert e["issue_numbers"] == []


def test_scratch_directory(report):
    e = by_name(report)["nerelan_scratch"]
    assert e["classification"] == "scratch"
    assert e["git_kind"] == "none"
    assert e["size_bytes"] == 15


def test_loose_file(report):
    e = by_name(report)["_run_gates.py"]
    assert e["classification"] == "scratch"
    assert e["kind"] == "file"
    assert e["size_bytes"] == len("print('x')\n")


def test_worktree_with_missing_gitdir(report):
    e = by_name(report)["issue1001"]
    assert e["classification"] == "review"
    assert e["git_kind"] == "worktree"
    assert e["gitdir_missing"] is True
    assert e["issue_numbers"] == [1001]


def test_non_matching_ignored(report):
    names = by_name(report)
    assert "unrelated_project" not in names
    assert set(names) == {
        "Nerelan-pr949", "nrl-issue757", "tmp_dirty", "nerelan_scratch", "_run_gates.py", "issue1001",
    }


def test_totals(report):
    totals = report["totals"]
    assert {c: totals[c]["count"] for c in totals} == {"safe_delete": 1, "review": 3, "scratch": 2}
    for cls, t in totals.items():
        assert t["size_bytes"] == sum(
            e["size_bytes"] for e in report["entries"] if e["classification"] == cls
        )
    assert report["total_bytes"] == sum(e["size_bytes"] for e in report["entries"])


def test_case_insensitive_matching(tmp_path):
    (tmp_path / "NRL_upper").mkdir()
    (tmp_path / "other").mkdir()
    result = scan(tmp_path, tmp_path)
    assert [e["name"] for e in result["entries"]] == ["NRL_upper"]


def test_top_level_symlink_is_reported_as_link(tmp_path):
    root = tmp_path / "root"
    target = tmp_path / "target"
    root.mkdir()
    target.mkdir()
    (target / "payload.bin").write_bytes(b"x" * 4096)
    link = root / "nrl_link"
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    result = scan(root, tmp_path)
    assert len(result["entries"]) == 1
    e = result["entries"][0]
    assert e["name"] == "nrl_link"
    assert e["kind"] == "link"
    assert e["classification"] == "review"
    assert e["size_bytes"] == 0
    assert e["git_kind"] is None
    assert result["total_bytes"] == 0
    assert result["totals"]["review"] == {"count": 1, "size_bytes": 0}
    assert result["totals"]["scratch"]["count"] == 0
    assert (target / "payload.bin").stat().st_size == 4096


def test_custom_pattern_overrides_defaults(world):
    result = scan(world["root"], world["repo"], patterns=[r"^unrelated"])
    assert [e["name"] for e in result["entries"]] == ["unrelated_project"]
    assert result["entries"][0]["classification"] == "scratch"


def test_main_writes_reports(world, tmp_path, capsys):
    out_json = tmp_path / "r.json"
    out_md = tmp_path / "r.md"
    rc = main([
        "--root", str(world["root"]), "--repo", str(world["repo"]),
        "--json", str(out_json), "--markdown", str(out_md),
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    assert len(captured.strip().splitlines()) == 1
    assert captured.startswith("dev_leftovers:")

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["total_count"] == 6
    assert {e["name"] for e in data["entries"]} >= {"Nerelan-pr949", "tmp_dirty"}

    md = out_md.read_text(encoding="utf-8")
    assert "| Class | Name |" in md
    pos = {c: md.index(f"| {c} | ") for c in ("safe_delete", "review", "scratch")}
    assert pos["safe_delete"] < pos["review"] < pos["scratch"]
    assert "| Nerelan-pr949 |" in md


def test_main_rejects_missing_root(tmp_path, capsys):
    rc = main(["--root", str(tmp_path / "nope"), "--repo", str(tmp_path)])
    assert rc == 2


def test_render_and_summary(report):
    assert summary_line(report).startswith("dev_leftovers: 6 entries")
    md = render_markdown(report)
    assert "| scratch | nerelan_scratch |" in md
    assert "| total | 6 |" in md


def test_scan_is_read_only(world):
    root = world["root"]
    before = snapshot(root)
    status_before = git(root / "tmp_dirty", "status", "--porcelain")
    scan(root, world["repo"])
    assert snapshot(root) == before
    assert git(root / "tmp_dirty", "status", "--porcelain") == status_before
    assert status_before == "?? untracked.txt"
