"""Git/GitHub evidence adapter: derive truth from repository state.

F14: The production live collector (:func:`collect_live_evidence`) owns truth.
It does not accept caller-supplied test pass/fail booleans or CI success
lists. It reads local Git HEAD/diff, PR metadata, workflow runs/checks, and
authorized test-command evidence through injectable structured adapters.
Provider-free tests use :class:`FakeGitAdapter`, :class:`FakeGitHubAdapter`,
and :class:`FakeCommandRunner`.

F15: :func:`merge_evidence` never substitutes untrusted changed_paths,
test_results, ci_checks, head, PR, or provenance when trusted evidence is
empty. Empty trusted state remains empty and fails closed where evidence
is required.
"""

from __future__ import annotations

import subprocess
from typing import Any, Protocol, Sequence

from .contracts import ExecutionEvidence
from .github_adapter import (
    GitHubAdapter,
    GitHubAdapterError,
    LiveGitHubAdapter,
    WorkflowCheck,
    checks_to_ci_tuples,
    validate_workflow_observations,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class EvidenceCollectionError(Exception):
    """Raised when Git/GitHub evidence collection fails.

    The message is a stable, machine-readable error code so callers can map
    it to a documented nonzero exit code.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Git adapter protocol
# ---------------------------------------------------------------------------

class GitAdapter(Protocol):
    """Injectable Git adapter protocol.

    Production code uses :class:`LiveGitAdapter` which calls git directly.
    Tests inject :class:`FakeGitAdapter` to avoid filesystem access.
    """

    def get_changed_paths(self, base_sha: str, head_sha: str) -> tuple[str, ...]:
        """Return changed file paths between base and head."""
        ...

    def check_git_diff(self, base_sha: str, head_sha: str) -> bool:
        """Return True if git diff --check passes (no whitespace errors)."""
        ...

    def get_head_sha(self) -> str:
        """Return the current HEAD SHA."""
        ...


class LiveGitAdapter:
    """Production Git adapter using subprocess calls."""

    def __init__(self, repo_dir: str = ".") -> None:
        self.repo_dir = repo_dir

    def get_changed_paths(self, base_sha: str, head_sha: str = "HEAD") -> tuple[str, ...]:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_sha, head_sha],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise EvidenceCollectionError(
                "git_diff_name_only_failed",
                f"exit={result.returncode}",
            )
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tuple(dict.fromkeys(paths))

    def check_git_diff(self, base_sha: str, head_sha: str = "HEAD") -> bool:
        result = subprocess.run(
            ["git", "diff", "--check", f"{base_sha}..{head_sha}"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode not in (0, 2):
            raise EvidenceCollectionError(
                "git_diff_check_failed",
                f"exit={result.returncode}",
            )
        return result.returncode == 0

    def get_head_sha(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise EvidenceCollectionError("git_rev_parse_failed", f"exit={result.returncode}")
        return result.stdout.strip()


class FakeGitAdapter:
    """Fake Git adapter for provider-free tests."""

    def __init__(
        self,
        *,
        changed_paths: tuple[str, ...] = (),
        diff_check_passed: bool = True,
        head_sha: str = "",
        fail_with: EvidenceCollectionError | None = None,
    ) -> None:
        self._changed_paths = changed_paths
        self._diff_check_passed = diff_check_passed
        self._head_sha = head_sha
        self._fail_with = fail_with
        self.call_count = 0

    def get_changed_paths(self, base_sha: str, head_sha: str) -> tuple[str, ...]:
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        return self._changed_paths

    def check_git_diff(self, base_sha: str, head_sha: str) -> bool:
        if self._fail_with is not None:
            raise self._fail_with
        return self._diff_check_passed

    def get_head_sha(self) -> str:
        if self._fail_with is not None:
            raise self._fail_with
        return self._head_sha


# ---------------------------------------------------------------------------
# Command runner protocol (for authorized test commands)
# ---------------------------------------------------------------------------

class CommandRunner(Protocol):
    """Injectable command runner for authorized test commands.

    Production code uses :class:`LiveCommandRunner` which calls subprocess.
    Tests inject :class:`FakeCommandRunner`.
    """

    def run(self, command: str) -> tuple[int, str, str]:
        """Run a command and return (exit_code, stdout, stderr)."""
        ...


class LiveCommandRunner:
    """Production command runner using subprocess."""

    def __init__(self, cwd: str = ".") -> None:
        self.cwd = cwd

    def run(self, command: str) -> tuple[int, str, str]:
        result = subprocess.run(
            command,
            shell=True,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        return (result.returncode, result.stdout, result.stderr)


class FakeCommandRunner:
    """Fake command runner for provider-free tests."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self._exit_code = exit_code
        self._stdout = stdout
        self._stderr = stderr
        self.calls: list[str] = []

    def run(self, command: str) -> tuple[int, str, str]:
        self.calls.append(command)
        return (self._exit_code, self._stdout, self._stderr)


# ---------------------------------------------------------------------------
# Legacy function-based Git evidence (kept for backward compatibility)
# ---------------------------------------------------------------------------

def get_changed_paths(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> tuple[str, ...]:
    """Return the list of changed file paths between base and head.

    Raises ``EvidenceCollectionError`` on Git failure — never returns an
    empty list to mask a read failure.
    """

    return LiveGitAdapter(repo_dir).get_changed_paths(base_sha, head_sha)


def check_git_diff(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> bool:
    """Return True if ``git diff --check`` passes (no whitespace errors).

    Raises ``EvidenceCollectionError`` on Git failure.
    """

    return LiveGitAdapter(repo_dir).check_git_diff(base_sha, head_sha)


def get_head_sha(repo_dir: str = ".") -> str:
    """Return the current HEAD SHA.

    Raises ``EvidenceCollectionError`` on Git failure.
    """

    return LiveGitAdapter(repo_dir).get_head_sha()


# ---------------------------------------------------------------------------
# Legacy tabular parsing (DEPRECATED — kept for backward compat, not for live)
# ---------------------------------------------------------------------------

def parse_pr_checks(checks_output: str) -> tuple[dict[str, Any], ...]:
    """Parse ``gh pr checks`` tabular output into a tuple of check dicts.

    DEPRECATED: F13 replaces this with structured GitHub adapter. Kept only
    for backward compatibility with existing tests that verify the parser.
    New code must use :class:`LiveGitHubAdapter` or :class:`FakeGitHubAdapter`.
    """

    checks: list[dict[str, Any]] = []
    for line in checks_output.splitlines():
        line = line.strip()
        if not line or line.startswith("name"):
            continue
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        status = "UNKNOWN"
        for token in parts[1:]:
            token_upper = token.upper()
            if token_upper in ("SUCCESS", "FAILURE", "PENDING", "SKIPPED", "CANCELLED"):
                status = token_upper
                break
        checks.append({"name": name, "status": status, "conclusion": status})
    return tuple(checks)


def collect_pr_checks(
    pr_number: int,
    repository: str,
) -> tuple[dict[str, Any], ...]:
    """Collect PR checks from GitHub via ``gh pr checks``.

    DEPRECATED: F13 replaces this with structured GitHub adapter.
    """

    result = subprocess.run(
        ["gh", "pr", "checks", str(pr_number), "--repo", repository],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise EvidenceCollectionError(
            "gh_pr_checks_failed",
            f"exit={result.returncode}",
        )
    return parse_pr_checks(result.stdout)


# ---------------------------------------------------------------------------
# Trusted live evidence collection (F14)
# ---------------------------------------------------------------------------

def collect_live_evidence(
    *,
    execution_id: str,
    repository: str,
    base_sha: str,
    expected_head_sha: str,
    pr_number: int,
    required_workflows: tuple[str, ...],
    expected_branch: str,
    authority_digest: str,
    work_item: Any,
    git_adapter: GitAdapter | None = None,
    github_adapter: GitHubAdapter | None = None,
    test_command_runner: CommandRunner | None = None,
    test_command: str = "",
    agent_completion_claim: str = "",
    collected_at: str = "",
) -> ExecutionEvidence:
    """Collect trusted live evidence through injectable adapters.

    F14: The collector owns truth. It does NOT accept caller-supplied test
    pass/fail booleans or CI success lists. It reads:
    - local HEAD via git_adapter
    - git changed paths via git_adapter
    - git diff --check via git_adapter
    - PR workflow runs via github_adapter
    - authorized test command results via test_command_runner

    All adapters are injectable for provider-free testing.

    Raises ``EvidenceCollectionError`` or ``GitHubAdapterError`` on failure.
    """

    if git_adapter is None:
        git_adapter = LiveGitAdapter()
    if github_adapter is None:
        github_adapter = LiveGitHubAdapter()

    # 1. Collect Git facts
    local_head = git_adapter.get_head_sha()
    if local_head != expected_head_sha:
        raise EvidenceCollectionError(
            "head_sha_mismatch",
            f"local={local_head} expected={expected_head_sha}",
        )

    changed_paths = git_adapter.get_changed_paths(base_sha, expected_head_sha)
    diff_ok = git_adapter.check_git_diff(base_sha, expected_head_sha)

    # 2. Collect test results (only from authorized command runner)
    test_results: dict[str, Any] = {}
    if test_command_runner is not None and test_command:
        exit_code, stdout, _stderr = test_command_runner.run(test_command)
        test_results = {
            "passed": exit_code == 0,
            "command": test_command,
            "exit_code": exit_code,
        }

    # 3. Collect CI checks via structured GitHub adapter
    workflow_checks = github_adapter.get_pr_checks(
        pr_number, repository, expected_head_sha,
    )

    # 4. Validate workflow observations
    blocking, _info = validate_workflow_observations(
        workflow_checks, required_workflows, expected_head_sha,
    )
    if blocking:
        raise EvidenceCollectionError(
            "workflow_validation_failed",
            ";".join(blocking),
        )

    # 5. Build live evidence using the trusted factory
    ci_checks = checks_to_ci_tuples(workflow_checks)
    return ExecutionEvidence.create_live(
        execution_id=execution_id,
        repository=repository,
        base_sha=base_sha,
        head_sha=expected_head_sha,
        pr_number=pr_number,
        required_workflows=required_workflows,
        changed_paths=changed_paths,
        test_results=test_results,
        git_diff_check_passed=diff_ok,
        agent_completion_claim=agent_completion_claim,
        ci_checks=ci_checks,
        collected_at=collected_at,
    )


# ---------------------------------------------------------------------------
# Legacy assemble_evidence (F14: deprecated — use collect_live_evidence)
# ---------------------------------------------------------------------------

def assemble_evidence(
    execution_id: str,
    repository: str,
    base_sha: str,
    head_sha: str,
    pr_number: int,
    required_workflows: Sequence[str],
    repo_dir: str = ".",
    test_results: dict[str, Any] | None = None,
    agent_completion_claim: str = "",
    ci_checks: Sequence[dict[str, Any]] = (),
    collected_at: str = "",
) -> ExecutionEvidence:
    """Assemble trusted ExecutionEvidence from Git state.

    F14 DEPRECATED: This function accepts caller-supplied test_results and
    ci_checks, which is unsafe. New code must use :func:`collect_live_evidence`
    which collects all facts through injectable adapters.

    This function is kept for backward compatibility with existing tests but
    is no longer used by the CLI live path.
    """

    git_adapter = LiveGitAdapter(repo_dir)
    changed_paths = git_adapter.get_changed_paths(base_sha, head_sha)
    diff_ok = git_adapter.check_git_diff(base_sha, head_sha)

    return ExecutionEvidence.create_live(
        execution_id=execution_id,
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        pr_number=pr_number,
        required_workflows=tuple(required_workflows),
        changed_paths=changed_paths,
        test_results=test_results or {},
        git_diff_check_passed=diff_ok,
        agent_completion_claim=agent_completion_claim,
        ci_checks=tuple(ci_checks),
        collected_at=collected_at,
    )


# ---------------------------------------------------------------------------
# merge_evidence (F15: no untrusted fallback)
# ---------------------------------------------------------------------------

def merge_evidence(
    untrusted: ExecutionEvidence,
    trusted: ExecutionEvidence,
) -> ExecutionEvidence:
    """Merge untrusted (agent) evidence with trusted (Git/CI) evidence.

    F15: Trusted evidence always wins. When trusted fields are empty, they
    remain empty — NO fallback to untrusted data. The agent's completion
    claim is preserved for audit but never overrides trusted evidence.

    Removed behaviors (F15):
    - ``trusted.changed_paths or untrusted.changed_paths`` — now just ``trusted.changed_paths``
    - ``trusted.test_results or untrusted.test_results`` — now just ``trusted.test_results``
    """

    return ExecutionEvidence(
        execution_id=trusted.execution_id,
        repository=trusted.repository,
        base_sha=trusted.base_sha,
        head_sha=trusted.head_sha,
        pr_number=trusted.pr_number,
        required_workflows=trusted.required_workflows,
        # F15: no fallback to untrusted — empty trusted stays empty
        changed_paths=trusted.changed_paths,
        test_results=trusted.test_results,
        git_diff_check_passed=trusted.git_diff_check_passed,
        # agent_completion_claim is audit-only, preserved from untrusted
        agent_completion_claim=untrusted.agent_completion_claim,
        ci_checks=trusted.ci_checks,
        collected_at=trusted.collected_at,
        collection_mode=trusted.collection_mode,
        provenance=trusted.provenance,
    )
