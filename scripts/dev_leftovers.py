"""Read-only inventory of stale Nerelan development leftovers under a disk root.

Lists matching top-level entries, sizes them, inspects git state with read-only
git commands, and classifies each as safe_delete, review, or scratch. Nothing
is ever deleted, moved, or modified; only the optional --json/--markdown
output files are written.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

DEFAULT_PATTERNS = [
    r"^nrl",
    r"^Nerelan-",
    r"^n986v2-",
    r"^tmp721",
    r"^tmp_",
    r"^nerelan_",
    r"^reverse-agent-issue",
    r"^issue\d+",
    r"^_(fix_state|inspect_fg|refresh_report|run_gates)\.py$",
]

CLASSES = ("safe_delete", "review", "scratch")
_ISSUE_RE = re.compile(r"(?i)(?:issue|pr)[-_]?(\d+)")


def _is_link(path: str, entry: os.DirEntry | None = None, st: os.stat_result | None = None) -> bool:
    try:
        if entry is not None and entry.is_symlink():
            return True
        if st is None:
            st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode):
            return True
        if getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
        isjunction = getattr(os.path, "isjunction", None)
        return bool(isjunction and isjunction(path))
    except OSError:
        return False


def _dir_size(path: str) -> int:
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            it = os.scandir(current)
        except OSError:
            continue
        with it:
            while True:
                try:
                    entry = next(it)
                except StopIteration:
                    break
                except OSError:
                    break
                try:
                    st = entry.stat(follow_symlinks=False)
                    if _is_link(entry.path, entry, st):
                        continue
                    if stat.S_ISDIR(st.st_mode):
                        stack.append(entry.path)
                    elif stat.S_ISREG(st.st_mode):
                        total += st.st_size
                except OSError:
                    continue
    return total


def _git(args: list[str], path) -> str | None:
    try:
        # Read-only: optional locks off so `status` never refreshes the scanned repo's index,
        # and a scanned repository's config cannot launch an fsmonitor hook.
        proc = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _issue_numbers(name: str) -> list[int]:
    return sorted({int(m) for m in _ISSUE_RE.findall(name)})


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def _worktree_gitdir_missing(entry_path: str) -> bool:
    try:
        text = Path(entry_path, ".git").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    for line in text.splitlines():
        if line.startswith("gitdir:"):
            target = line[len("gitdir:"):].strip()
            if not os.path.isabs(target):
                target = os.path.join(entry_path, target)
            return not os.path.exists(target)
    return True


def _head_on_remote(head: str | None, repo) -> bool | None:
    if not head:
        return None
    if _git(["cat-file", "-e", f"{head}^{{commit}}"], repo) is None:
        return False
    out = _git(["branch", "-r", "--contains", head], repo)
    return bool(out and any(line.strip() for line in out.splitlines()))


def _classify(record: dict) -> tuple[str, str]:
    if record["kind"] == "link":
        return "review", "symlink or junction; not followed"
    if record["git_kind"] == "none":
        return "scratch", "non-git directory" if record["kind"] == "dir" else "loose file"
    if record["gitdir_missing"]:
        return "review", "worktree gitdir missing"
    if record["head"] is None:
        return "review", "head unknown"
    if record["dirty"] is None:
        return "review", "dirty state unknown"
    if record["dirty"]:
        return "review", "dirty working tree"
    if record["head_on_remote"] is not True:
        return "review", "head not on any remote branch"
    return "safe_delete", "clean, head on remote"


def scan(root, repo, patterns=None) -> dict:
    compiled = [re.compile(p, re.IGNORECASE) for p in (patterns or DEFAULT_PATTERNS)]
    root_s = os.path.abspath(str(root))
    entries = []
    with os.scandir(root_s) as it:
        children = sorted(it, key=lambda e: e.name)
    for child in children:
        if not any(p.search(child.name) for p in compiled):
            continue
        try:
            st = os.lstat(child.path)
        except OSError:
            continue
        path = os.path.abspath(child.path)
        link = _is_link(child.path, child, st)
        is_dir = stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode)
        kind = "dir" if stat.S_ISDIR(st.st_mode) else "file"
        record = {
            "name": child.name,
            "path": path,
            "kind": kind,
            "size_bytes": 0,
            "last_modified": _iso(st.st_mtime),
            "issue_numbers": _issue_numbers(child.name),
            "git_kind": "none",
            "gitdir_missing": False,
            "head": None,
            "branch": None,
            "dirty": None,
            "head_on_remote": None,
        }
        if link:
            record["kind"] = "link"
            record["size_bytes"] = 0
            record["git_kind"] = None
            record["gitdir_missing"] = False
        elif is_dir:
            record["size_bytes"] = _dir_size(path)
            dot_git = os.path.join(path, ".git")
            if os.path.isdir(dot_git) and not _is_link(dot_git):
                record["git_kind"] = "repo"
            elif os.path.isfile(dot_git):
                record["git_kind"] = "worktree"
                record["gitdir_missing"] = _worktree_gitdir_missing(path)
            else:
                record["git_kind"] = "none"
        else:
            try:
                record["size_bytes"] = st.st_size
            except OSError:
                pass
        if record["git_kind"] in ("repo", "worktree") and not record["gitdir_missing"]:
            record["head"] = _git(["rev-parse", "HEAD"], path) or None
            record["branch"] = _git(["rev-parse", "--abbrev-ref", "HEAD"], path) or None
            porcelain = _git(["status", "--porcelain"], path)
            record["dirty"] = None if porcelain is None else bool(porcelain)
            record["head_on_remote"] = _head_on_remote(record["head"], repo)
        record["classification"], record["reason"] = _classify(record)
        entries.append(record)

    totals = {c: {"count": 0, "size_bytes": 0} for c in CLASSES}
    for e in entries:
        totals[e["classification"]]["count"] += 1
        totals[e["classification"]]["size_bytes"] += e["size_bytes"]
    return {
        "root": root_s,
        "repo": os.path.abspath(str(repo)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
        "totals": totals,
        "total_bytes": sum(t["size_bytes"] for t in totals.values()),
        "total_count": len(entries),
    }


def _human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def summary_line(report: dict) -> str:
    parts = ", ".join(
        f"{c}={report['totals'][c]['count']} ({_human(report['totals'][c]['size_bytes'])})" for c in CLASSES
    )
    return f"dev_leftovers: {report['total_count']} entries, {_human(report['total_bytes'])} total; {parts}"


def _cell(value) -> str:
    if value is None:
        return "?"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict) -> str:
    order = {c: i for i, c in enumerate(CLASSES)}
    rows = sorted(
        report["entries"],
        key=lambda e: (order[e["classification"]], -e["size_bytes"], e["name"]),
    )
    lines = [
        "# Developer leftovers inventory",
        "",
        f"- Root: `{report['root']}`",
        f"- Repo: `{report['repo']}`",
        f"- Generated: {report['generated_at']}",
        "",
        "| Class | Name | Kind | Size | Git | Branch | Dirty | On remote | Issues | Last modified | Reason |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in rows:
        cells = [
            e["classification"],
            e["name"],
            e["kind"],
            _human(e["size_bytes"]),
            e["git_kind"],
            e["branch"],
            e["dirty"],
            e["head_on_remote"],
            ", ".join(str(n) for n in e["issue_numbers"]),
            e["last_modified"],
            e["reason"],
        ]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    lines += ["", "## Totals", "", "| Class | Count | Size |", "| --- | ---: | ---: |"]
    for c in CLASSES:
        t = report["totals"][c]
        lines.append(f"| {c} | {t['count']} | {_human(t['size_bytes'])} |")
    lines.append(f"| total | {report['total_count']} | {_human(report['total_bytes'])} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="directory to scan (direct children only)")
    parser.add_argument("--repo", type=Path, required=True, help="main Nerelan git checkout")
    parser.add_argument("--pattern", action="append", help="regex for entry names; replaces defaults; repeatable")
    parser.add_argument("--json", type=Path, help="write JSON report to this file")
    parser.add_argument("--markdown", type=Path, help="write Markdown report to this file")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"dev_leftovers: error: --root is not a directory: {args.root}", file=sys.stderr)
        return 2

    report = scan(args.root, args.repo, args.pattern)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(summary_line(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
