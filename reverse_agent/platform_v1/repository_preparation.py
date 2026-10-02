"""Shared provider-free isolated Git worktree preparation, extracted from OpenCode."""

from pathlib import Path
import re
import subprocess
from .task_runtime import ExecutorRuntimeError, _sanitize_output
from .opencode_executor import _emit, redact_secrets

def _is_path_contained(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents

def _run_git(argv: list[str], *, cwd: Path, timeout: int):
    try:
        return subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExecutorRuntimeError("repository_preparation_failed") from exc

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

    list_proc = _run_git(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_dir,
        timeout=10,
    )
    if dest.as_posix() not in list_proc.stdout and str(dest) not in list_proc.stdout:
        raise ExecutorRuntimeError("worktree_not_registered")

    return dest, base_sha
