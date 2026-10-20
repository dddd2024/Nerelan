"""Reclaim finished task worktrees and stale developer clones.

Task execution creates one linked worktree per task under ``task_workspaces``
and nothing removes it afterwards. This sweep removes a direct child of a root
only when every check below proves no work can be lost:

* it is an unlocked linked worktree (or, with ``include_clones``, a standalone
  clone that hosts no other worktree), not a symlink/junction, and nests no
  other repository or submodule;
* ``git status`` shows no tracked change and no untracked file, and every
  ignored path is a regenerable cache (``__pycache__``, ``node_modules``,
  native execution scratch ``.nt``/``.nt-<12 hex>``...);
* no index entry is assume-unchanged or skip-worktree (status hides those);
* HEAD and its reflog, and for a clone every ref and reflog (branches, tags,
  stash), is reachable from a remote-tracking ref;
* nothing anywhere in the tree was modified within the retention window;
* when a TaskStore is given, the matching task is not in a non-terminal state;
* it is not a planner worktree, which recovers itself from owner records.

"Pushed" means reachable from a local remote-tracking ref; run ``git fetch
--prune`` first if those may be stale. Deleting a clone that other repositories
borrow objects from (``clone --shared``/``--reference``) breaks them; such
clones are rare and not detected. Per-worktree refs (``refs/worktree/*``,
``refs/bisect/*``) are not checked, and a clone's tags are assumed to have
been fetched: a tag created locally on an already-pushed commit is not
distinguished from a fetched one.

Anything else is kept and reported with the reason. The default is a dry run;
``apply=True`` re-checks each candidate immediately before deleting it. Deletion
tolerates Windows long paths and read-only files. A worktree is removed only
through ``git worktree remove`` without ``--force``; if git refuses, or a file
is locked, the failure is reported and the sweep continues.

``AutoReclaimer`` runs the same checks unattended inside the trusted host. It
is off unless ``REVERSE_AGENT_WORKSPACE_RECLAIM`` is ``report`` (log only) or
``apply``. Every poll it reclaims the workspace of each task that finished
(terminal status, last update) more than the retention period ago, and once per
sweep interval it sweeps the whole root. Standalone clones are never included.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import os
import threading
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
from urllib.parse import quote

from .run_store import TERMINAL_STATUSES

LOG = logging.getLogger(__name__)
DEFAULT_RETENTION_DAYS = 3.0
_GIT = ("git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false",
        "-c", "core.longpaths=true")
_GIT_ENV = {"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
# Ignored paths that only hold regenerable caches. Any other ignored file
# (.env, run evidence, build outputs) keeps the checkout.
_CACHE_NAMES = frozenset({
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis",
    "node_modules", ".vite", ".tox", ".nox",
})
_CACHE_SUFFIXES = (".pyc", ".pyo")
_SCRATCH_RE = re.compile(r"\.nt(?:-[0-9a-f]{12})?")


def _run(args, cwd, timeout=60, stdin_text=None):
    try:
        proc = subprocess.run(
            [*_GIT, *args], cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
            input=stdin_text, stdin=None if stdin_text is not None else subprocess.DEVNULL,
            env={**os.environ, **_GIT_ENV},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    return proc.returncode, proc.stdout.strip() if proc.returncode == 0 else proc.stderr.strip()


def _git(args, cwd, timeout=60):
    code, out = _run(args, cwd, timeout)
    return out if code == 0 else None


def _is_cache(rel: str) -> bool:
    parts = [p for p in rel.replace("\\", "/").split("/") if p]
    # Top-level .nt / .nt-<hex> is per-execution native TMP scratch, which
    # codex_executor already excludes from product evidence.
    if parts and _SCRATCH_RE.fullmatch(parts[0]):
        return True
    return any(p in _CACHE_NAMES for p in parts) or rel.endswith(_CACHE_SUFFIXES)


def _is_link(path: Path) -> bool:
    try:
        st = os.lstat(path)
    except OSError:
        return True
    if stat.S_ISLNK(st.st_mode):
        return True
    if getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        return True
    return bool(os.path.isjunction(path))


def _long(path: Path) -> str:
    # Windows MAX_PATH is 260; the extended prefix lifts it for os/shutil calls.
    text = str(path.absolute())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\") else "\\\\?\\" + text
    return text


def _walk(path: Path) -> tuple[float, bool]:
    """Return the newest mtime in the whole tree and whether it nests a repo."""
    newest = os.lstat(path).st_mtime
    nested = False
    top = _long(path)
    stack = [top]
    while stack:
        current = stack.pop()
        with os.scandir(current) as it:
            for entry in it:
                st = entry.stat(follow_symlinks=False)
                newest = max(newest, st.st_mtime)
                if current != top and entry.name == ".git":
                    nested = True
                if stat.S_ISDIR(st.st_mode) and entry.name != ".git" and not _is_link(Path(entry.path)):
                    stack.append(entry.path)
    # Commits and checkouts touch the (per-worktree) gitdir, not the tree root.
    gitdir = _gitdir(path)
    for name in ("index", "HEAD", "logs/HEAD", "FETCH_HEAD", "ORIG_HEAD", "packed-refs"):
        try:
            if gitdir is not None:
                newest = max(newest, os.stat(gitdir / name).st_mtime)
        except OSError:
            continue
    return newest, nested


def _gitdir(path: Path) -> Path | None:
    dot_git = path / ".git"
    if dot_git.is_dir():
        return dot_git
    try:
        text = dot_git.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("gitdir:"):
            target = Path(line[len("gitdir:"):].strip())
            return target if target.is_absolute() else (path / target)
    return None


def _read_tasks(db, columns: str) -> list[tuple] | None:
    conn = None
    try:
        path = Path(db).expanduser().resolve()
        conn = sqlite3.connect("file:" + quote(path.as_posix(), safe="/:") + "?mode=ro",
                               uri=True, timeout=3)
        conn.execute("PRAGMA query_only=ON")
        return [tuple(str(v) for v in row) for row in conn.execute(f"SELECT {columns} FROM tasks")]
    except (sqlite3.Error, OSError, ValueError):
        return None
    finally:
        if conn is not None:
            conn.close()


def _task_statuses(db) -> dict[str, str] | None:
    if db is None:
        return {}
    rows = _read_tasks(db, "id, status")
    return None if rows is None else dict(rows)


def _task_rows(db) -> dict[str, tuple[str, str]] | None:
    """Return ``{task_id: (status, updated_at)}``; ``None`` if unreadable."""
    rows = _read_tasks(db, "id, status, updated_at")
    return None if rows is None else {i: (s, u) for i, s, u in rows}


def inspect(path: Path, *, now: float, retention_days: float,
            include_clones: bool = False, task_statuses: dict | None = None) -> dict:
    """Return ``{"path", "kind", "reclaim", "reason"}`` for one root child."""
    record = {"path": str(path), "name": path.name, "kind": "unknown",
              "reclaim": False, "reason": ""}

    def keep(reason):
        record["reason"] = reason
        return record

    if _is_link(path):
        return keep("symlink or junction; not followed")
    if not path.is_dir():
        return keep("not a directory")
    if path.with_name(path.name + ".planner-owner.json").exists():
        return keep("planner worktree; recovered by its owner record")
    dot_git = path / ".git"
    if dot_git.is_file():
        record["kind"] = "worktree"
    elif dot_git.is_dir() and not _is_link(dot_git):
        record["kind"] = "clone"
    else:
        return keep("not a git checkout")
    gitdir = _gitdir(path)
    if gitdir is None or not gitdir.exists():
        return keep("gitdir missing")
    if task_statuses is None:
        return keep("task store unreadable")
    status = task_statuses.get(path.name)
    if status is not None and status not in TERMINAL_STATUSES:
        return keep(f"task still {status}")
    if record["kind"] == "clone":
        if not include_clones:
            return keep("standalone clone; pass --include-clones")
        if any((gitdir / "worktrees").glob("*")):
            return keep("clone hosts linked worktrees")
    else:
        # Only a registered linked worktree gets the lighter HEAD-only check;
        # its gitdir must be <common>/worktrees/<id> outside the tree itself.
        resolved = gitdir.resolve()
        if resolved.parent.name != "worktrees" or resolved.is_relative_to(path.resolve()):
            return keep("gitdir is not a linked worktree entry")
        if (resolved / "locked").exists():
            return keep("worktree is locked")
    try:
        newest, nested = _walk(path)
    except OSError:
        return keep("tree unreadable")
    if nested:
        return keep("contains a nested repository or submodule")
    age_days = (now - newest) / 86400
    if age_days < retention_days:
        return keep(f"modified {age_days:.1f} days ago; retention {retention_days:g}")
    # Inside the worktree, rev-parse must agree it is its own top level, so a
    # crafted .git file cannot redirect checks to another checkout.
    top = _git(["rev-parse", "--show-toplevel"], path)
    if top is None or Path(top).resolve() != path.resolve():
        return keep("git top level mismatch")
    porcelain = _git(["status", "--porcelain", "--untracked-files=all"], path)
    if porcelain is None:
        return keep("git status failed")
    if porcelain:
        return keep("uncommitted or untracked changes")
    # status hides edits to assume-unchanged (lowercase tag) and
    # skip-worktree (S) entries, so their presence alone keeps the checkout.
    flags = _git(["ls-files", "-v", "-z"], path, timeout=300)
    if flags is None:
        return keep("index flags unreadable")
    if any(e and (e[0].islower() or e[0] == "S") for e in flags.split("\0")):
        return keep("assume-unchanged or skip-worktree entries")
    # Per file, not --directory: git collapses a parent whose children are all
    # ignored, which would hide whether they are only caches.
    ignored = _git(["ls-files", "-z", "--others", "--ignored", "--exclude-standard"],
                   path, timeout=300)
    if ignored is None:
        return keep("ignored files unreadable")
    kept = [p for p in ignored.split("\0") if p and not _is_cache(p)]
    if kept:
        return keep(f"ignored files present: {kept[0]}")
    head = _git(["rev-parse", "--verify", "HEAD^{commit}"], path)
    if not head:
        return keep("head unknown")
    # Commits left behind by reset/checkout survive only in the reflog.
    reflog = _git(["log", "-g", "--format=%H", "HEAD", "--"], path, timeout=120)
    if reflog is None and _git(["reflog", "exists", "HEAD"], path) is not None:
        return keep("reflog unreadable")
    if record["kind"] == "clone":
        refs = ["--all", "--reflog", "HEAD"]
        if _git(["stash", "list"], path) != "":
            return keep("stash present or unreadable")
    else:
        refs = ["HEAD"]
    code, unpushed = _run(["rev-list", "-n1", "--stdin", *refs, "--not", "--remotes"], path,
                          stdin_text="\n".join(sorted(set((reflog or "").split()))) + "\n")
    if code != 0:
        unpushed = None
    if unpushed is None:
        return keep("remote reachability unknown")
    if unpushed:
        return keep("commits not on any remote branch")
    if record["kind"] == "clone":
        # Reachability alone would drop a local branch name; every branch
        # must track an upstream that points at the same commit.
        branches = _git(["for-each-ref", "--format=%(objectname) %(upstream)",
                         "refs/heads"], path)
        if branches is None:
            return keep("branches unreadable")
        for line in branches.splitlines():
            sha, _, upstream = line.partition(" ")
            if not upstream or _git(["rev-parse", "--verify", "-q", upstream], path) != sha:
                return keep("local branch without matching upstream")
    record["head"] = head
    record["reclaim"] = True
    record["reason"] = "clean, pushed, older than retention"
    return record


def _on_rm_error(func, target, _exc):
    # Git object files are read-only on Windows; clear the bit and retry once.
    try:
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        func(target)
    except OSError:
        pass


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(_long(path), onexc=_on_rm_error)


def remove(record: dict) -> dict:
    path = Path(record["path"])
    if record["kind"] == "worktree":
        common = _git(["rev-parse", "--path-format=absolute", "--git-common-dir"], path)
        if common is None:
            return {**record, "removed": False, "error": "git common dir unknown"}
        # Plain remove (no --force): git's own refusal (dirty, locked) is final.
        # It also drops the registration, so no repository-wide prune runs:
        # that would unregister unrelated missing worktrees outside the root.
        code, err = _run(["worktree", "remove", str(path)], Path(common))
        if code != 0:
            return {**record, "removed": False, "error": f"git worktree remove: {err}"}
    try:
        _remove_tree(path)
    except OSError as exc:
        return {**record, "removed": False, "error": f"{type(exc).__name__}: {exc}"}
    if path.exists():
        return {**record, "removed": False, "error": "files remain (locked or in use)"}
    return {**record, "removed": True}


def _reclaim_one(child: Path, opts: dict, apply: bool) -> dict:
    record = inspect(child, **opts)
    if apply and record["reclaim"]:
        # Re-check right before deletion: state may have changed.
        record = inspect(child, **opts)
        if record["reclaim"]:
            record = remove(record)
    return record


def sweep(roots, *, retention_days: float = DEFAULT_RETENTION_DAYS,
          patterns=None, include_clones: bool = False, task_db=None,
          apply: bool = False, now: float | None = None, stop=None) -> dict:
    now = time.time() if now is None else now
    compiled = [re.compile(p, re.IGNORECASE) for p in (patterns or [])]
    statuses = _task_statuses(task_db)
    entries = []
    for root in roots:
        root = Path(root).absolute()
        try:
            children = sorted(root.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            entries.append({"path": str(root), "name": root.name, "kind": "root",
                            "reclaim": False, "reason": f"root unreadable: {exc}"})
            continue
        for child in children:
            if stop is not None and stop():
                break
            if child.name.endswith(".planner-owner.json"):
                continue
            if compiled and not any(p.search(child.name) for p in compiled):
                continue
            opts = dict(now=now, retention_days=retention_days,
                        include_clones=include_clones, task_statuses=statuses)
            entries.append(_reclaim_one(child, opts, apply))
    return {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "applied": apply,
        "retention_days": retention_days,
        "entries": entries,
        "reclaimable": sum(e["reclaim"] for e in entries),
        "removed": sum(bool(e.get("removed")) for e in entries),
        "failed": sum(e.get("removed") is False for e in entries),
    }


AUTO_MODES = ("off", "report", "apply")
DEFAULT_SWEEP_INTERVAL_HOURS = 24.0
DEFAULT_POLL_MINUTES = 15.0


def _env_number(env, name, default, minimum):
    raw = env.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        value = None
    if value is None or value != value or value < minimum:
        # An unusable value falls back to the conservative default.
        LOG.warning("workspace reclaim: ignoring %s=%r; using %g", name, raw, default)
        return default
    return value


def auto_config(env=None) -> dict:
    """Read the automatic reclaim settings; anything invalid falls back safely."""
    env = os.environ if env is None else env
    mode = env.get("REVERSE_AGENT_WORKSPACE_RECLAIM", "").strip().lower() or "off"
    if mode not in AUTO_MODES:
        LOG.warning("workspace reclaim: unknown mode %r; staying off", mode)
        mode = "off"
    return {
        "mode": mode,
        "retention_days": _env_number(env, "REVERSE_AGENT_WORKSPACE_RECLAIM_RETENTION_DAYS",
                                      DEFAULT_RETENTION_DAYS, 0.0),
        "interval_hours": _env_number(env, "REVERSE_AGENT_WORKSPACE_RECLAIM_INTERVAL_HOURS",
                                      DEFAULT_SWEEP_INTERVAL_HOURS, 1.0),
        "poll_minutes": _env_number(env, "REVERSE_AGENT_WORKSPACE_RECLAIM_POLL_MINUTES",
                                    DEFAULT_POLL_MINUTES, 1.0),
    }


def _parse_utc(text: str) -> float | None:
    try:
        moment = datetime.fromisoformat(text.strip())
    except (AttributeError, ValueError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


class AutoReclaimer:
    """Reclaim finished task workspaces under one root in the background.

    A task's workspace is considered once the task has been terminal for the
    retention period; ``inspect`` still applies every safety check, including
    the tree-wide modification time. Each (task, last update) pair is handled
    once per process, so a kept or locked workspace is not retried every poll;
    the periodic full sweep retries it. The full sweep's time and report are
    kept in ``state_path`` so a host restart does not sweep again early.
    """

    def __init__(self, root, task_db, *, mode="report",
                 retention_days=DEFAULT_RETENTION_DAYS,
                 interval_hours=DEFAULT_SWEEP_INTERVAL_HOURS,
                 poll_minutes=DEFAULT_POLL_MINUTES, state_path=None, clock=time.time):
        if mode not in ("report", "apply"):
            raise ValueError(f"unsupported reclaim mode: {mode}")
        self.root = Path(root).absolute()
        self.task_db = task_db
        self.apply = mode == "apply"
        self.retention_days = float(retention_days)
        self.interval_seconds = float(interval_hours) * 3600
        self.poll_seconds = float(poll_minutes) * 60
        self.state_path = Path(state_path) if state_path else None
        self.clock = clock
        self._handled: set[tuple[str, str]] = set()
        self._memory_state: dict = {}
        self._stop = threading.Event()
        self._mutex = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread is None:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="workspace-reclaim",
                                            daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _run(self):
        # The first pass waits one poll, so host startup does no extra I/O.
        while not self._stop.wait(self.poll_seconds):
            try:
                self.tick()
            except Exception:
                LOG.exception("workspace reclaim tick failed")

    def tick(self) -> dict:
        with self._mutex:
            now = self.clock()
            finished = self.reclaim_finished(now)
            swept = self.full_sweep(now) if self._sweep_due(now) else None
            return {"finished": finished, "sweep": swept}

    def _opts(self, now, statuses):
        return dict(now=now, retention_days=self.retention_days, include_clones=False,
                    task_statuses=statuses)

    def reclaim_finished(self, now: float) -> list[dict]:
        rows = _task_rows(self.task_db)
        if rows is None:
            LOG.warning("workspace reclaim: task store unreadable; skipping")
            return []
        statuses = {k: v[0] for k, v in rows.items()}
        records = []
        for task_id, (status, updated_at) in sorted(rows.items()):
            if self._stop.is_set():
                break
            if status not in TERMINAL_STATUSES or (task_id, updated_at) in self._handled:
                continue
            finished_at = _parse_utc(updated_at)
            if finished_at is None or now - finished_at < self.retention_days * 86400:
                continue
            child = self.root / task_id
            if Path(task_id).name != task_id or not os.path.lexists(child):
                continue
            self._handled.add((task_id, updated_at))
            record = _reclaim_one(child, self._opts(now, statuses), self.apply)
            self._log(record)
            records.append(record)
        return records

    def _sweep_due(self, now: float) -> bool:
        last = self._state().get("last_sweep_at")
        return not isinstance(last, (int, float)) or now - last >= self.interval_seconds

    def _state(self) -> dict:
        if self.state_path is None:
            return self._memory_state
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def full_sweep(self, now: float) -> dict:
        report = sweep([self.root], retention_days=self.retention_days, task_db=self.task_db,
                       apply=self.apply, now=now, stop=self._stop.is_set)
        for record in report["entries"]:
            self._log(record)
        LOG.info("workspace reclaim sweep: %d checked, %d reclaimable, %d removed, %d failed%s",
                 len(report["entries"]), report["reclaimable"], report["removed"],
                 report["failed"], "" if self.apply else " (report only)")
        state = {"last_sweep_at": now, "report": report}
        if self.state_path is None:
            self._memory_state = state
        else:
            try:
                self.state_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.state_path.with_name(self.state_path.name + ".tmp")
                tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp, self.state_path)
            except OSError:
                LOG.warning("workspace reclaim: could not write %s", self.state_path)
        return report

    def _log(self, record: dict) -> None:
        if record.get("removed"):
            LOG.info("workspace reclaim: removed %s", record["path"])
        elif record.get("removed") is False:
            LOG.warning("workspace reclaim: kept %s: %s", record["path"], record.get("error"))
        elif record["reclaim"]:
            LOG.info("workspace reclaim: would remove %s", record["path"])


def configured_reclaimer(workspace_root, task_db, env=None) -> AutoReclaimer | None:
    """Build the host's reclaimer from the environment, or ``None`` when off."""
    config = auto_config(env)
    if config["mode"] == "off" or not task_db or task_db == ":memory:":
        return None
    state_path = Path(task_db).absolute().parent / "workspace_reclaim_state.json"
    return AutoReclaimer(workspace_root, task_db, mode=config["mode"],
                         retention_days=config["retention_days"],
                         interval_hours=config["interval_hours"],
                         poll_minutes=config["poll_minutes"], state_path=state_path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", action="append", required=True, type=Path,
                        help="directory whose direct children are swept; repeatable")
    parser.add_argument("--retention-days", type=float, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--pattern", action="append",
                        help="only consider children whose name matches this regex; repeatable")
    parser.add_argument("--include-clones", action="store_true",
                        help="also reclaim standalone clones that host no worktrees")
    parser.add_argument("--task-db", type=Path, help="TaskStore SQLite; keeps non-terminal tasks")
    parser.add_argument("--apply", action="store_true", help="delete; default is a dry run")
    parser.add_argument("--json", type=Path, help="write the full report here")
    args = parser.parse_args(argv)
    if args.retention_days < 0:
        parser.error("--retention-days must be >= 0")
    report = sweep(args.root, retention_days=args.retention_days, patterns=args.pattern,
                   include_clones=args.include_clones, task_db=args.task_db, apply=args.apply)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for e in report["entries"]:
        if e["reclaim"]:
            state = ("removed" if e.get("removed") else f"FAILED {e.get('error')}") \
                if args.apply else "would remove"
            print(f"{state}: {e['path']}")
    print(f"workspace_reclaim: {len(report['entries'])} checked, "
          f"{report['reclaimable']} reclaimable, {report['removed']} removed, "
          f"{report['failed']} failed{'' if args.apply else ' (dry run)'}")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
