"""Shared provider-free isolated Git worktree preparation, extracted from OpenCode."""

from pathlib import Path
from contextlib import contextmanager
import json
import os
import re
import shutil
import stat
import subprocess
import uuid
from .task_runtime import ExecutorRuntimeError, _sanitize_output
from .opencode_executor import _emit, redact_secrets

def _is_path_contained(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents

def _run_git(argv: list[str], *, cwd: Path, timeout: int):
    try:
        return subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExecutorRuntimeError("repository_preparation_failed") from exc

def assert_pristine_workspace(root):
    """Reject pre-execution dirt, including checkout-hook output, without deleting it."""
    status = _run_git(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=root, timeout=60)
    if status.returncode or status.stdout:
        raise ExecutorRuntimeError("workspace_preexisting_changes")


def prepare_linked_worktree(task_id, root_path, event_callback, *, repo_dir_value, base_ref):
    if not isinstance(task_id,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}",task_id):
        raise ExecutorRuntimeError("task_id_invalid")
    """Create a real linked Git worktree from the configured source repo."""
    if not repo_dir_value:
        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "repo_dir required",
            "description": "Model executor requires a non-empty repo_dir",
            "metadata": {"failure_classification": "policy_worktree_violation"},
        })
        raise ExecutorRuntimeError("repo_dir_required")

    repo_dir = Path(repo_dir_value).resolve()
    if not repo_dir.exists() or not repo_dir.is_dir():
        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "repo_dir not a directory",
            "description": "repo_dir does not exist or is not a directory",
            "metadata": {"failure_classification": "policy_worktree_violation"},
        })
        raise ExecutorRuntimeError(
            "repo_dir_invalid:%s" % repo_dir_value
        )

    is_inside = _run_git(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_dir,
        timeout=10,
    )
    if is_inside.returncode != 0:
        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "repo_dir not a git repository",
            "description": "repo_dir is not inside a git work tree",
            "metadata": {"failure_classification": "policy_worktree_violation"},
        })
        raise ExecutorRuntimeError("repo_dir_not_a_git_repository")

    base_ref = base_ref.strip()
    if base_ref:
        resolved = _run_git(
            ["git", "rev-parse", "--verify", "%s^{commit}" % base_ref],
            cwd=repo_dir,
            timeout=10,
        )
        if resolved.returncode != 0:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "base_ref invalid",
                "description": "Could not resolve base_ref %s" % base_ref,
                "metadata": {"failure_classification": "policy_worktree_violation"},
            })
            raise ExecutorRuntimeError(
                "base_ref_unresolved:%s" % base_ref
            )
        base_sha = resolved.stdout.strip()
    else:
        head = _run_git(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            timeout=10,
        )
        if head.returncode != 0:
            raise ExecutorRuntimeError("repo_dir_has_no_HEAD")
        base_sha = head.stdout.strip()

    dest = (root_path / task_id).resolve()
    repo_dir_resolved = repo_dir.resolve()
    if dest == repo_dir_resolved:
        raise ExecutorRuntimeError("worktree_must_be_outside_repo_dir")
    if _is_path_contained(dest, repo_dir_resolved):
        raise ExecutorRuntimeError("worktree_must_be_outside_repo_dir")

    if dest.exists():
        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "workspace destination exists",
            "description": "Destination path already exists; refusing to overwrite",
            "metadata": {"failure_classification": "policy_worktree_violation"},
        })
        raise ExecutorRuntimeError("workspace_destination_exists")

    parents = dest.parent
    parents.mkdir(parents=True, exist_ok=True)

    add_proc = _run_git(
        ["git", "worktree", "add", "--detach", str(dest), base_sha],
        cwd=repo_dir,
        timeout=60,
    )
    if add_proc.returncode != 0:
        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "worktree creation failed",
            "description": "git worktree add failed",
            "metadata": {
                "failure_classification": "policy_worktree_violation",
                "stderr_summary": redact_secrets(
                    _sanitize_output(add_proc.stderr, 512)
                )[:512],
            },
        })
        raise ExecutorRuntimeError(
            "worktree_add_failed:%s" % add_proc.stderr[:200]
        )

    head_check = _run_git(
        ["git", "rev-parse", "HEAD"],
        cwd=dest,
        timeout=10,
    )
    if head_check.returncode != 0 or head_check.stdout.strip() != base_sha:
        raise ExecutorRuntimeError("worktree_head_mismatch")

    assert_pristine_workspace(dest)

    list_proc = _run_git(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_dir,
        timeout=10,
    )
    if dest.as_posix() not in list_proc.stdout and str(dest) not in list_proc.stdout:
        raise ExecutorRuntimeError("worktree_not_registered")

    return dest, base_sha


def _planner_path(path):
    """Reject indirection before resolving, including Windows junctions."""
    path = Path(path)
    if ".." in path.parts:
        raise ExecutorRuntimeError("planner_path_invalid")
    path = Path(os.path.abspath(path))
    # On Windows a concurrently created parent can change non-strict resolve's
    # missing-tail result. Retry once, repeating every indirection check; an
    # actual link or a persistent canonical-path mismatch still fails closed.
    for _ in range(2):
        for part in (path, *path.parents):
            if part.is_symlink() or (part.exists() and
                    getattr(part.lstat(), "st_file_attributes", 0) &
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
                raise ExecutorRuntimeError("planner_path_invalid")
        if path.resolve() == path:
            return path
    raise ExecutorRuntimeError("planner_path_invalid")


@contextmanager
def _planner_lock(path):
    # Lock files deliberately remain: unlinking one permits two processes to
    # lock different inodes for the same ownership record.
    path = _planner_path(path)
    with path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    acquired = True
                except OSError:
                    pass
            else:
                import fcntl
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError:
                    pass
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


# Planner git runs on the host, so repository-controlled hooks (post-checkout on
# worktree add, including a tracked core.hooksPath) must never execute.
_PLANNER_GIT = ("git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false")


def _planner_git(repo, *args):
    result = _run_git([*_PLANNER_GIT, *args], cwd=repo, timeout=60)
    if result.returncode:
        raise ExecutorRuntimeError("planner_git_failed")
    return result.stdout.strip()


def _remove_planner_worktree(repo, root, dest):
    root = _planner_path(root)
    dest = _planner_path(dest)
    if dest.parent != root or dest == repo or repo.is_relative_to(dest):
        raise ExecutorRuntimeError("planner_path_invalid")
    try:
        # add can fail after creating a directory but before registering it.
        result = _run_git([*_PLANNER_GIT, "worktree", "remove", "--force", str(dest)],
                          cwd=repo, timeout=60)
        if result.returncode and dest.exists():
            _planner_path(dest)
            shutil.rmtree(dest)
    finally:
        _planner_git(repo, "worktree", "prune")


def _recover_planner_worktrees(repo, root):
    # Only host ownership records authorize deletion; unrelated directories and
    # worktrees, even ones with similar names, are never swept.
    for record in root.glob("*.planner-owner.json"):
        _planner_path(record)
        name = record.name.removesuffix(".planner-owner.json")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*-r[0-9]+-[0-9a-f]{32}", name):
            continue
        with _planner_lock(root / (name + ".lock")) as acquired:
            if not acquired or not record.exists():
                continue
            try:
                owner = json.loads(record.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue  # incomplete creation cannot yet have added a worktree
            if owner != {"version": 1, "repository": str(repo), "name": name}:
                continue
            _remove_planner_worktree(repo, root, root / name)
            record.unlink()


@contextmanager
def planner_worktree(source_repository, workspace_root, goal_id, revision,
                     base_commit=None):
    """Yield (detached workspace, pinned commit), then dispose of the workspace.

    The workspace root is host-owned. Persistent records plus lifetime kernel
    locks allow the next start to reclaim crashed runs across host processes.
    Planner output must be collected before leaving this context.
    """
    if (not isinstance(goal_id, str) or
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", goal_id) or
            type(revision) is not int or revision < 0):
        raise ExecutorRuntimeError("planner_identity_invalid")
    body_error = None
    try:
        repo = _planner_path(source_repository)
        root = _planner_path(Path(workspace_root) / "planner")
        if root.is_relative_to(repo) or repo.is_relative_to(root):
            raise ExecutorRuntimeError("planner_path_invalid")
        root.mkdir(parents=True, exist_ok=True)
        _planner_path(root)
        base = "HEAD" if base_commit is None else base_commit
        if not isinstance(base, str) or not base or base.startswith("-"):
            raise ExecutorRuntimeError("planner_base_invalid")
        sha = _planner_git(repo, "rev-parse", "--verify", base + "^{commit}")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            raise ExecutorRuntimeError("planner_base_invalid")
        _recover_planner_worktrees(repo, root)
        name = f"{goal_id}-r{revision}-{uuid.uuid4().hex}"
        dest = root / name
        record = root / (name + ".planner-owner.json")
        with _planner_lock(root / (name + ".lock")) as acquired:
            if not acquired:
                raise ExecutorRuntimeError("planner_busy")
            _planner_path(dest)
            if dest.exists():
                raise ExecutorRuntimeError("planner_destination_exists")
            with record.open("x", encoding="utf-8") as handle:
                json.dump({"version": 1, "repository": str(repo), "name": name}, handle)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                _planner_git(repo, "worktree", "add", "--detach", str(dest), sha)
                if _planner_git(dest, "rev-parse", "HEAD") != sha:
                    raise ExecutorRuntimeError("planner_head_mismatch")
                try:
                    yield dest, sha
                except BaseException as exc:
                    body_error = exc
                    raise
            finally:
                _remove_planner_worktree(repo, root, dest)
                record.unlink()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        if exc is body_error:
            raise
        raise ExecutorRuntimeError("planner_preparation_failed") from None
