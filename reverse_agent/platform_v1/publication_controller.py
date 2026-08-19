"""Idempotent trusted Draft-PR publication for validated task worktrees.

Publication is intentionally narrow: exact allowlisted files, a generated
non-main branch, one normal push and Draft PR reconciliation.  It never marks
ready, merges, force-pushes, rebases, tags or releases.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Callable, Mapping, Sequence

from .autonomy import AutonomyService
from .control_store import PlatformControlStore, PublicationRecord, sha256_json
from .run_store import TaskStore, TaskStoreError


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[Sequence[str], str], CommandResult]


class PublicationController:
    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore,
        autonomy: AutonomyService,
        runner: CommandRunner | None = None,
    ) -> None:
        self.store = store
        self.control_store = control_store
        self.autonomy = autonomy
        self.runner = runner or self._run

    def publish(
        self,
        task_id: str,
        *,
        window_id: str,
        base_branch: str,
        allowed_paths: Sequence[str],
        title: str = "",
        body: str = "",
    ) -> PublicationRecord:
        task = self.store.get_task(task_id)
        if task.status not in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
            raise TaskStoreError(f"publication_requires_validated_task:{task.status}")
        if base_branch in {"", "HEAD"} or not re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", base_branch):
            raise TaskStoreError("invalid_publication_base_branch")
        if not isinstance(allowed_paths, (list, tuple)):
            raise TaskStoreError("publication_allowed_paths_array_required")
        normalized_paths = tuple(sorted({self._safe_path(path) for path in allowed_paths}))
        if not normalized_paths:
            raise TaskStoreError("publication_allowed_paths_required")
        request = {
            "task_id": task_id,
            "repository": task.repository,
            "base_branch": base_branch,
            "allowed_paths": normalized_paths,
            "title": title.strip(),
            "body": body.strip(),
        }
        digest = sha256_json(request)
        branch = f"agent/task-{self._safe_slug(task_id)}"
        existing = self.control_store.get_publication(task_id)
        if existing is not None:
            if existing.request_digest != digest:
                raise TaskStoreError("publication_request_digest_mismatch")
            if existing.status == "COMPLETE":
                return existing

        if not self.autonomy.authorize(
            window_id=window_id,
            operation="open_draft_pr",
            repository=task.repository,
            subject_id=task_id,
            input_payload={"task_id": task_id, "base_branch": base_branch, "allowed_paths": normalized_paths},
        ):
            raise TaskStoreError("publication_denied_by_window")

        workspace_meta = self.control_store.durable_workspace(task_id)
        workspace = Path(str(workspace_meta.get("worktree_path", ""))).resolve()
        if not workspace.is_dir() or workspace == Path(workspace.anchor):
            raise TaskStoreError("publication_workspace_invalid")
        if existing is not None and existing.commit_sha:
            head = self._git(workspace, "rev-parse", "HEAD").stdout.strip()
            if head != existing.commit_sha:
                raise TaskStoreError("publication_committed_head_drift")
            self._git(workspace, "push", "origin", existing.branch)
            pr = self._find_or_create_draft_pr(
                workspace=workspace,
                repository=task.repository,
                branch=existing.branch,
                base_branch=base_branch,
                title=title.strip() or f"{task.title.splitlines()[0]}",
                body=body.strip() or self._default_body(task_id, digest, normalized_paths),
            )
            if not bool(pr.get("isDraft", False)):
                raise TaskStoreError("publication_pr_not_draft")
            return self.control_store.upsert_publication(
                task_id=task_id, repository=task.repository, base_branch=base_branch,
                branch=existing.branch, status="COMPLETE", request_digest=digest,
                commit_sha=existing.commit_sha, pr_number=int(pr.get("number", 0)),
                pr_url=str(pr.get("url", "")),
            )
        self._assert_git_workspace(workspace, workspace_meta)
        actual_paths = self._changed_paths(workspace)
        if not actual_paths:
            raise TaskStoreError("publication_has_no_changes")
        outside = [path for path in actual_paths if not self._path_allowed(path, normalized_paths)]
        if outside:
            raise TaskStoreError(f"publication_path_outside_allowlist:{','.join(outside)}")
        evidence_paths = {
            self._safe_path(str(item.get("path", "")))
            for item in task.changed_files
            if str(item.get("path", "")).strip()
        }
        if evidence_paths and evidence_paths != set(actual_paths):
            raise TaskStoreError("publication_task_evidence_scope_mismatch")

        record = self.control_store.upsert_publication(
            task_id=task_id,
            repository=task.repository,
            base_branch=base_branch,
            branch=branch,
            status="PENDING",
            request_digest=digest,
        )
        try:
            current_branch = self._git(workspace, "branch", "--show-current").stdout.strip()
            if current_branch != branch:
                if current_branch and current_branch not in {base_branch, "main", "planning"}:
                    raise TaskStoreError(f"publication_unexpected_branch:{current_branch}")
                self._git(workspace, "switch", "-c", branch)
            self._git(workspace, "add", "--", *actual_paths)
            staged = tuple(
                line.strip().replace("\\", "/")
                for line in self._git(workspace, "diff", "--cached", "--name-only").stdout.splitlines()
                if line.strip()
            )
            if set(staged) != set(actual_paths):
                raise TaskStoreError("publication_staged_scope_mismatch")
            commit_message = f"feat: complete {task_id}"
            commit = self._git(workspace, "commit", "-m", commit_message)
            commit_sha = self._git(workspace, "rev-parse", "HEAD").stdout.strip()
            record = self.control_store.upsert_publication(
                task_id=task_id, repository=task.repository, base_branch=base_branch, branch=branch,
                status="COMMIT_CREATED", request_digest=digest, commit_sha=commit_sha,
            )
            self._git(workspace, "push", "origin", branch)
            record = self.control_store.upsert_publication(
                task_id=task_id, repository=task.repository, base_branch=base_branch, branch=branch,
                status="PUSHED", request_digest=digest, commit_sha=commit_sha,
            )
            pr = self._find_or_create_draft_pr(
                workspace=workspace,
                repository=task.repository,
                branch=branch,
                base_branch=base_branch,
                title=title.strip() or f"{task.title.splitlines()[0]}",
                body=body.strip() or self._default_body(task_id, digest, actual_paths),
            )
            if not bool(pr.get("isDraft", False)):
                raise TaskStoreError("publication_pr_not_draft")
            head_oid = str(pr.get("headRefOid", ""))
            if head_oid and head_oid != commit_sha:
                raise TaskStoreError("publication_pr_head_mismatch")
            return self.control_store.upsert_publication(
                task_id=task_id, repository=task.repository, base_branch=base_branch, branch=branch,
                status="COMPLETE", request_digest=digest, commit_sha=commit_sha,
                pr_number=int(pr.get("number", 0)), pr_url=str(pr.get("url", "")),
            )
        except Exception as exc:
            self.control_store.upsert_publication(
                task_id=task_id, repository=task.repository, base_branch=base_branch, branch=branch,
                status="FAILED", request_digest=digest, commit_sha=record.commit_sha,
                pr_number=record.pr_number, pr_url=record.pr_url,
                failure_classification=type(exc).__name__,
            )
            raise

    def _find_or_create_draft_pr(
        self,
        *,
        workspace: Path,
        repository: str,
        branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> Mapping[str, Any]:
        view_args = (
            "pr", "list", "--repo", repository, "--head", branch, "--state", "open",
            "--json", "number,url,isDraft,headRefOid,baseRefName", "--limit", "1",
        )
        existing = self._json(self._gh(workspace, *view_args).stdout)
        if isinstance(existing, list) and existing:
            pr = existing[0]
        else:
            self._gh(
                workspace, "pr", "create", "--repo", repository, "--draft", "--head", branch,
                "--base", base_branch, "--title", title[:240], "--body", body,
            )
            created = self._json(self._gh(workspace, *view_args).stdout)
            if not isinstance(created, list) or not created:
                raise TaskStoreError("publication_pr_readback_missing")
            pr = created[0]
        if str(pr.get("baseRefName", "")) != base_branch:
            raise TaskStoreError("publication_pr_base_mismatch")
        return pr

    def _assert_git_workspace(self, workspace: Path, meta: Mapping[str, Any]) -> None:
        root = Path(self._git(workspace, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
        if root != workspace:
            raise TaskStoreError("publication_workspace_root_mismatch")
        head = self._git(workspace, "rev-parse", "HEAD").stdout.strip()
        expected = str(meta.get("worktree_head_sha", ""))
        if expected and head != expected:
            raise TaskStoreError("publication_workspace_head_drift")

    def _changed_paths(self, workspace: Path) -> tuple[str, ...]:
        output = self._git(workspace, "status", "--porcelain=v1", "--untracked-files=all").stdout
        paths: list[str] = []
        for line in output.splitlines():
            if len(line) < 4:
                continue
            raw = line[3:]
            if " -> " in raw:
                raw = raw.split(" -> ", 1)[1]
            raw = raw.strip().strip('"').replace("\\", "/")
            paths.append(self._safe_path(raw))
        return tuple(sorted(set(paths)))

    @staticmethod
    def _path_allowed(path: str, allowed: Sequence[str]) -> bool:
        return any(path == root or path.startswith(root.rstrip("/") + "/") for root in allowed)

    @staticmethod
    def _safe_path(value: str) -> str:
        normalized = value.strip().replace("\\", "/")
        path = PurePosixPath(normalized)
        if not normalized or path.is_absolute() or ".." in path.parts or normalized.startswith(".git/"):
            raise TaskStoreError(f"unsafe_publication_path:{value}")
        return path.as_posix()

    @staticmethod
    def _safe_slug(value: str) -> str:
        return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")[:80]

    def _git(self, workspace: Path, *args: str) -> CommandResult:
        result = self.runner(("git", *args), str(workspace))
        if result.returncode != 0:
            raise TaskStoreError(f"git_command_failed:{args[0]}:{result.stderr.strip()[:200]}")
        return result

    def _gh(self, workspace: Path, *args: str) -> CommandResult:
        result = self.runner(("gh", *args), str(workspace))
        if result.returncode != 0:
            raise TaskStoreError(f"github_command_failed:{args[0]}:{result.stderr.strip()[:200]}")
        return result

    @staticmethod
    def _run(argv: Sequence[str], cwd: str) -> CommandResult:
        completed = subprocess.run(
            list(argv), cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120, check=False, shell=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    @staticmethod
    def _json(value: str) -> Any:
        try:
            return json.loads(value or "null")
        except json.JSONDecodeError as exc:
            raise TaskStoreError("publication_json_readback_invalid") from exc

    @staticmethod
    def _default_body(task_id: str, digest: str, paths: Sequence[str]) -> str:
        path_lines = "\n".join(f"- `{path}`" for path in paths)
        return (
            f"Automated Draft PR for validated task `{task_id}`.\n\n"
            f"Request digest: `{digest}`\n\nChanged paths:\n{path_lines}\n\n"
            "This automation cannot mark ready or merge."
        )
