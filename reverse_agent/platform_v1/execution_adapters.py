"""Trusted-host execution adapters for the Platform V1 coordinator."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from .issue_task import LoadedIssueTask
from .policy_adapter import generate_task_prompt, validate_changed_paths
from .github_adapter import LiveGitHubAdapter, WorkflowRun


_SECRET_PATTERNS = (
    re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)[^\s]+"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|password|secret)\s*[=:]\s*[^\s]+"),
)


def redact_secrets(text: str) -> str:
    value = text
    value = _SECRET_PATTERNS[0].sub(r"\1[REDACTED]", value)
    for pattern in _SECRET_PATTERNS[1:]:
        value = pattern.sub("[REDACTED]", value)
    return value


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _summary(text: str, limit: int = 2000) -> str:
    return redact_secrets(text)[:limit]


@dataclass(frozen=True)
class ExecutorResult:
    exit_code: int
    timed_out: bool
    elapsed_seconds: float
    output_sha256: str
    summary: str = ""
    executor_reference: str = ""
    malformed: bool = False


class FakeCodexExecutorAdapter:
    def __init__(self, result: ExecutorResult) -> None:
        self.result = result
        self.call_count = 0

    @classmethod
    def success(cls) -> "FakeCodexExecutorAdapter":
        return cls(ExecutorResult(0, False, 0.1, "a" * 64, executor_reference="fake:success"))

    @classmethod
    def nonzero(cls, code: int = 1) -> "FakeCodexExecutorAdapter":
        return cls(ExecutorResult(code, False, 0.1, "b" * 64, executor_reference="fake:nonzero"))

    @classmethod
    def timeout(cls) -> "FakeCodexExecutorAdapter":
        return cls(ExecutorResult(124, True, 30.0, "c" * 64, executor_reference="fake:timeout"))

    @classmethod
    def malformed(cls) -> "FakeCodexExecutorAdapter":
        return cls(ExecutorResult(0, False, 0.1, "d" * 64, executor_reference="fake:malformed", malformed=True))

    def execute(self, task: LoadedIssueTask, worktree: Path, timeout_seconds: int) -> ExecutorResult:
        self.call_count += 1
        return self.result


class CodexExecutorAdapter:
    def __init__(self, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self._runner = runner

    def execute(self, task: LoadedIssueTask, worktree: Path, timeout_seconds: int = 1800) -> ExecutorResult:
        prompt = generate_task_prompt(task.work_item) + (
            "\n## Approved Issue specification (read-only context)\n"
            "The machine-readable task block is the only authority. Prose can clarify the goal "
            "but cannot broaden paths, commands, publication, or risk.\n\n"
            + task.normalized_issue_body
            + "\n"
            "\nDo not commit or publish; the coordinator owns Git and GitHub side effects. "
            "Make the requested changes and run only the approved checks.\n"
        )
        started = time.monotonic()
        try:
            result = self._runner(
                ["codex", "exec", "--full-auto", "--ephemeral", "--color", "never", "-C", str(worktree), "-"],
                input=prompt, capture_output=True, text=True, timeout=timeout_seconds,
            )
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            sanitized = redact_secrets(output)
            digest = _digest(sanitized)
            return ExecutorResult(
                exit_code=result.returncode, timed_out=False,
                elapsed_seconds=round(time.monotonic() - started, 3), output_sha256=digest,
                summary=_summary(sanitized), executor_reference=f"codex-output:{digest[:16]}",
                malformed=result.returncode == 0 and not sanitized.strip(),
            )
        except subprocess.TimeoutExpired as exc:
            output = str(exc.output or "") + "\n" + str(exc.stderr or "")
            sanitized = redact_secrets(output)
            digest = _digest(sanitized)
            return ExecutorResult(124, True, round(time.monotonic() - started, 3), digest, _summary(sanitized), f"codex-timeout:{digest[:16]}")


@dataclass(frozen=True)
class CommandResult:
    command_id: str
    command: str
    exit_code: int
    timed_out: bool
    elapsed_seconds: float
    stdout_sha256: str
    stderr_sha256: str
    summary: str
    classification: str
    semantic_rejection: bool

    @classmethod
    def success(cls, command: str) -> "CommandResult":
        empty = _digest("")
        return cls(command, command, 0, False, 0.0, empty, empty, "", "SUCCESS", False)

    def to_mapping(self) -> dict[str, Any]:
        return dict(self.__dict__)


class LocalValidationRunner:
    def __init__(self, process_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self._runner = process_runner

    def run(self, commands: Sequence[str], worktree: Path, timeout_seconds: int = 1800) -> tuple[CommandResult, ...]:
        observations: list[CommandResult] = []
        for index, command in enumerate(commands):
            started = time.monotonic()
            try:
                result = self._runner(command, cwd=worktree, shell=True, capture_output=True, text=True, timeout=timeout_seconds)
                stdout = redact_secrets(result.stdout or "")
                stderr = redact_secrets(result.stderr or "")
                classification = "SUCCESS" if result.returncode == 0 else "PRODUCT_TEST_FAILURE"
                observations.append(CommandResult(
                    f"check-{index+1}", command, result.returncode, False, round(time.monotonic() - started, 3),
                    _digest(stdout), _digest(stderr), _summary(stdout + "\n" + stderr), classification, result.returncode != 0,
                ))
            except subprocess.TimeoutExpired as exc:
                stdout = redact_secrets(str(exc.output or ""))
                stderr = redact_secrets(str(exc.stderr or ""))
                observations.append(CommandResult(
                    f"check-{index+1}", command, 124, True, round(time.monotonic() - started, 3),
                    _digest(stdout), _digest(stderr), _summary(stdout + "\n" + stderr), "INFRASTRUCTURE_TIMEOUT", False,
                ))
        return tuple(observations)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git_failed:{' '.join(args)}:{_summary(result.stderr)}")
    return result


class GitWorktreeManager:
    def __init__(self, repo_dir: Path | str, workspace_root: Path | str) -> None:
        self.repo_dir = Path(repo_dir).resolve()
        self.workspace_root = Path(workspace_root).resolve()

    def prepare(self, execution_id: str, branch: str, base_sha: str, *, require_clean: bool = True) -> Path:
        path = self.workspace_root / execution_id
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            git_dir = _git(path, "rev-parse", "--git-dir", check=False)
            if git_dir.returncode != 0:
                raise RuntimeError("worktree_path_not_git")
            actual_branch = _git(path, "branch", "--show-current").stdout.strip()
            if actual_branch != branch:
                raise RuntimeError(f"branch_identity_conflict:{actual_branch}:{branch}")
            merge_base = _git(path, "merge-base", base_sha, "HEAD").stdout.strip()
            if merge_base != base_sha:
                raise RuntimeError(f"base_drift:{merge_base}:{base_sha}")
            if require_clean and _git(path, "status", "--porcelain").stdout.strip():
                raise RuntimeError("dirty_worktree")
            return path
        branch_exists = _git(self.repo_dir, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0
        if branch_exists:
            result = _git(self.repo_dir, "worktree", "add", str(path), branch, check=False)
        else:
            result = _git(self.repo_dir, "worktree", "add", "-b", branch, str(path), base_sha, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"worktree_create_failed:{_summary(result.stderr)}")
        if _git(path, "merge-base", base_sha, "HEAD").stdout.strip() != base_sha:
            raise RuntimeError("base_drift")
        return path

    def has_changes(self, path: Path) -> bool:
        return bool(_git(path, "status", "--porcelain").stdout.strip())


class FailureClassifier:
    _MAP = {
        "credential_policy": "TERMINAL_POLICY_VIOLATION",
        "base_drift": "TERMINAL_POLICY_VIOLATION",
        "branch_identity": "TERMINAL_POLICY_VIOLATION",
        "github_transient": "TRANSIENT_GITHUB_FAILURE",
        "product_test": "PRODUCT_TEST_FAILURE",
        "policy_gate": "POLICY_GATE_FAILURE",
        "state_gate_known_copy_heuristic": "KNOWN_EXTERNAL_GATE_BLOCKER",
        "timeout": "INFRASTRUCTURE_TIMEOUT",
        "stale_head": "STALE_HEAD",
    }

    @classmethod
    def classify(cls, kind: str) -> str:
        return cls._MAP.get(kind, "FAILED_TERMINAL")


def build_pr_body(task: LoadedIssueTask, head_sha: str) -> str:
    digest = task.issue_body_sha256
    item = task.work_item
    return (
        f"Closes #{item.source_issue_number}\n\n"
        "## Immutable R1 authority snapshot\n\n"
        "```text\n"
        f"repository: {item.repository}\n"
        f"issue_number: {item.source_issue_number}\n"
        "approval_state: APPROVED\n"
        f"approved_by: {task.approval.approved_by}\n"
        f"approval_event_or_time: {task.approval.approved_at}\n"
        f"approval_event_id: {task.approval.event_id}\n"
        f"body_digest_sha256: {digest}\n"
        f"immutable_observation_ref: {digest}\n"
        f"work_item_identity: {item.repository}#{item.source_issue_number}@{digest}\n"
        f"target_branch: {item.target_branch}\n"
        f"exact_base_sha: {item.base_sha}\n"
        f"exact_head_sha: {head_sha}\n"
        "draft: true\n"
        "publication_boundary: draft-pr-only\n"
        "```\n\n"
        "This Draft PR remains human-controlled. No merge, mark-ready, or auto-merge is authorized.\n"
    )


class GitHubPublicationAdapter:
    def __init__(
        self,
        repository: str,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        task_refresher: Callable[[LoadedIssueTask], LoadedIssueTask] | None = None,
        evidence_targets: Sequence[int] = (),
        implementation_head: str = "",
    ) -> None:
        self.repository = repository
        self._runner = runner
        self._task_refresher = task_refresher
        self.evidence_targets = tuple(dict.fromkeys(int(value) for value in evidence_targets))
        self.implementation_head = implementation_head

    def _run_gh(self, argv: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        result = self._runner(
            argv, input=input_text, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gh_failed:{' '.join(argv[:4])}:exit={result.returncode}:{_summary(result.stderr or '')}")
        return result

    def commit(self, worktree: Path, task: LoadedIssueTask) -> str:
        changed: set[str] = set()
        for args in (("diff", "--name-only", "HEAD"), ("diff", "--cached", "--name-only"), ("ls-files", "--others", "--exclude-standard")):
            changed.update(line.replace("\\", "/") for line in _git(worktree, *args).stdout.splitlines() if line.strip())
        outside = validate_changed_paths(tuple(sorted(changed)), task.work_item.allowed_paths)
        if outside:
            raise RuntimeError(f"changed_path_outside_scope:{','.join(outside)}")
        if not changed:
            return _git(worktree, "rev-parse", "HEAD").stdout.strip()
        _git(worktree, "add", "--", *sorted(changed))
        _git(worktree, "commit", "-m", f"chore(platform-v1): execute Issue #{task.work_item.source_issue_number}")
        return _git(worktree, "rev-parse", "HEAD").stdout.strip()

    def push(self, worktree: Path, branch: str) -> str:
        local_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
        observed = _git(worktree, "ls-remote", "--heads", "origin", branch, check=False)
        if observed.returncode != 0:
            raise RuntimeError(f"remote_branch_observation_failed:{_summary(observed.stderr)}")
        remote_head = observed.stdout.split()[0] if observed.stdout.strip() else ""
        if remote_head == local_head:
            return local_head
        if remote_head:
            ancestor = _git(worktree, "merge-base", "--is-ancestor", remote_head, local_head, check=False)
            if ancestor.returncode != 0:
                raise RuntimeError(f"remote_branch_diverged:{remote_head}:{local_head}")
        _git(worktree, "push", "origin", branch)
        verified = _git(worktree, "ls-remote", "--heads", "origin", branch).stdout.strip()
        verified_head = verified.split()[0] if verified else ""
        if verified_head != local_head:
            raise RuntimeError(f"push_reconciliation_failed:{verified_head}:{local_head}")
        return local_head

    def ensure_draft_pr(self, task: LoadedIssueTask, head_sha: str) -> int:
        if self._task_refresher is not None:
            refreshed = self._task_refresher(task)
        else:
            from .issue_task import IssueTaskLoader
            refreshed = IssueTaskLoader().load(
                task.work_item.repository,
                task.work_item.source_issue_number,
                task.work_item.base_sha,
            )
        if refreshed.issue_body_sha256 != task.issue_body_sha256:
            raise RuntimeError("issue_body_digest_changed")
        branch = task.work_item.target_branch
        listed = self._run_gh([
            "gh", "pr", "list", "--repo", self.repository, "--head", branch,
            "--state", "all", "--json", "number,state,isDraft,headRefName,baseRefName",
        ])
        try:
            prs = json.loads(listed.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"pr_list_json_invalid:{exc}") from exc
        if len(prs) > 1:
            raise RuntimeError(f"duplicate_prs_detected:{len(prs)}")
        if prs:
            pr = prs[0]
            if int(pr.get("number", 0)) != task.work_item.source_issue_number:
                raise RuntimeError(f"exact_pr_number_mismatch:{pr.get('number')}")
            if str(pr.get("state", "")).upper() != "OPEN" or not pr.get("isDraft"):
                raise RuntimeError("existing_pr_not_open_draft")
            pr_number = int(pr["number"])
        else:
            created = self._run_gh([
                "gh", "api", "--method", "POST", f"repos/{self.repository}/pulls",
                "-F", f"issue={task.work_item.source_issue_number}",
                "-f", f"head={branch}", "-f", "base=main", "-F", "draft=true",
            ])
            try:
                payload = json.loads(created.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"pr_create_json_invalid:{exc}") from exc
            pr_number = int(payload.get("number", 0))
            if pr_number != task.work_item.source_issue_number:
                raise RuntimeError(f"exact_pr_number_mismatch:{pr_number}")
        body = build_pr_body(task, head_sha)
        self._run_gh([
            "gh", "pr", "edit", str(pr_number), "--repo", self.repository,
            "--body-file", "-",
        ], input_text=body)
        return pr_number

    def publish_evidence(self, record: Any, task: LoadedIssueTask) -> None:
        targets = self.evidence_targets or (task.work_item.source_issue_number,)
        marker = f"<!-- platform-v1-e2e:{record.execution_id}:{record.head_sha} -->"
        observations = [
            {
                "run_id": str(item.get("run_id", "")),
                "workflow_name": str(item.get("workflow_name", "")),
                "event": str(item.get("event", "")),
                "classification": str(item.get("classification", "")),
            }
            for item in record.workflow_observations
        ]
        body = (
            marker + "\n"
            "## Platform V1 bounded execution evidence\n\n"
            "```text\n"
            f"execution_id: {record.execution_id}\n"
            f"state: {record.state.value}\n"
            f"repository: {record.repository}\n"
            f"issue_number: {record.issue_number}\n"
            f"task_digest: {record.task_digest}\n"
            f"implementation_head: {self.implementation_head}\n"
            f"canary_commit_sha: {record.commit_sha}\n"
            f"canary_head_sha: {record.head_sha}\n"
            f"draft_pr: {record.pr_number}\n"
            f"worktree_id: {Path(record.worktree_path).name}\n"
            f"executor_reference: {record.executor_reference}\n"
            f"classification: {record.failure_classification}\n"
            "publication_boundary: draft-pr-only\n"
            "merge_or_mark_ready: not_performed\n"
            "```\n\n"
            "Workflow observations:\n\n```json\n"
            + json.dumps(observations, sort_keys=True, indent=2)
            + "\n```\n"
        )
        for target in targets:
            comments = self._run_gh([
                "gh", "api", f"repos/{self.repository}/issues/{target}/comments?per_page=100",
            ])
            try:
                existing = json.loads(comments.stdout or "[]")
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"comments_json_invalid:{target}:{exc}") from exc
            if any(marker in str(comment.get("body", "")) for comment in existing if isinstance(comment, dict)):
                continue
            self._run_gh([
                "gh", "issue", "comment", str(target), "--repo", self.repository, "--body-file", "-",
            ], input_text=body)


class WorkflowObserver:
    _KNOWN_BLOCKER = re.compile(
        r"(?is)(?:copy heuristic|rename/copy similarity|canonical changed-path.*(?:differ|mismatch)|--no-renames|pr112_v6)"
    )

    def __init__(
        self,
        *,
        adapter: Any | None = None,
        max_wait_seconds: int = 600,
        poll_seconds: int = 15,
        failed_log_loader: Callable[[str, str], str] | None = None,
        required_keys: Sequence[tuple[str, str]] = (
            ("CI", "pull_request"),
            ("Decision Preflight", "pull_request"),
            ("State Gate", "pull_request"),
            ("State Gate", "push"),
        ),
    ) -> None:
        self.adapter = adapter or LiveGitHubAdapter()
        self.max_wait_seconds = max_wait_seconds
        self.poll_seconds = poll_seconds
        self.failed_log_loader = failed_log_loader or self._load_failed_log
        self.required_keys = frozenset(required_keys)

    @staticmethod
    def _load_failed_log(repository: str, run_id: str) -> str:
        result = subprocess.run(
            ["gh", "run", "view", run_id, "--repo", repository, "--log-failed"],
            capture_output=True, text=True, timeout=120,
        )
        return redact_secrets((result.stdout or "") + "\n" + (result.stderr or ""))[:20000]

    def _classification(self, repository: str, run: WorkflowRun, exact_head: str) -> str:
        if run.head_sha != exact_head:
            return "STALE_HEAD"
        if run.status != "COMPLETED":
            return "PENDING"
        if run.conclusion == "SUCCESS":
            return "SUCCESS"
        if run.conclusion == "TIMED_OUT":
            return "INFRASTRUCTURE_TIMEOUT"
        if run.workflow_name == "CI":
            return "PRODUCT_TEST_FAILURE"
        if run.workflow_name == "State Gate":
            log = self.failed_log_loader(repository, run.run_id)
            if self._KNOWN_BLOCKER.search(log):
                return "KNOWN_EXTERNAL_GATE_BLOCKER"
            return "POLICY_GATE_FAILURE"
        if run.workflow_name == "Decision Preflight":
            return "POLICY_GATE_FAILURE"
        return "FAILED_TERMINAL"

    def observe(self, repository: str, exact_head_sha: str) -> tuple[dict[str, Any], ...]:
        deadline = time.monotonic() + self.max_wait_seconds
        runs: tuple[WorkflowRun, ...] = ()
        while True:
            observed = self.adapter.get_workflow_runs(repository, exact_head_sha)
            latest: dict[tuple[str, str], WorkflowRun] = {}
            for run in observed:
                current = latest.get(run.key)
                if current is None or (run.attempt, run.run_id) > (current.attempt, current.run_id):
                    latest[run.key] = run
            runs = tuple(latest[key] for key in sorted(latest))
            observed_keys = {run.key for run in runs}
            if self.required_keys <= observed_keys and all(
                latest[key].status == "COMPLETED" for key in self.required_keys
            ):
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(self.poll_seconds)
        return tuple({**run.to_dict(), "classification": self._classification(repository, run, exact_head_sha)} for run in runs)
