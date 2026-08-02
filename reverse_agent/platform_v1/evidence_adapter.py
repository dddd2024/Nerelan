"""Git/GitHub evidence adapter: derive truth from repository state.

F14: The production live collector (:func:`collect_live_evidence`) owns truth.
It does not accept caller-supplied test pass/fail booleans or CI success
lists. It reads local Git HEAD/diff, PR metadata, workflow runs/checks, and
authorized test-command evidence through injectable structured adapters.

F19: Commands are selected by ``command_id`` from the approved Command Plan
(via :class:`AuthorityBundle`), never from caller-supplied shell text.
Execution uses ``shell=False`` with an argv list.

F20/F26: Authority comes from the internally loaded
:class:`AuthorityBundle`, not from stdin Work Item or authority digest.

F27: ``assemble_evidence`` is deprecated and produces fixture evidence only.
Only :func:`_create_trusted_evidence` can create live evidence.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from typing import Any, Protocol, Sequence

from .authority_adapter import AuthorityBundle
from .contracts import ExecutionEvidence, _LIVE_FACTORY_TOKEN
from .github_adapter import (
    GitHubAdapter,
    GitHubAdapterError,
    LiveGitHubAdapter,
    WorkflowRun,
    checks_to_ci_tuples,
    composite_name,
    validate_workflow_observations,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class EvidenceCollectionError(Exception):
    """Raised when Git/GitHub evidence collection fails."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Git adapter protocol
# ---------------------------------------------------------------------------

class GitAdapter(Protocol):
    """Injectable Git adapter protocol."""

    def get_changed_paths(self, base_sha: str, head_sha: str) -> tuple[str, ...]:
        ...

    def check_git_diff(self, base_sha: str, head_sha: str) -> bool:
        ...

    def get_head_sha(self) -> str:
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

# F19: Shell metacharacters that must never appear in an approved command.
# Commands are split with shlex and executed with shell=False, but we also
# reject these characters in the source string to prevent encoding tricks.
_SHELL_METACHARS_RE = re.compile(r"[;|&<>`$\n\r]|\|\||&&|\$\(|`")


def _is_safe_command(command_str: str) -> bool:
    """Check that a command string contains no shell metacharacters."""

    return _SHELL_METACHARS_RE.search(command_str) is None


class CommandRunner(Protocol):
    """Injectable command runner for authorized test commands.

    F19: Commands are executed as argv lists with ``shell=False``.
    Caller-supplied shell text is never executed.
    """

    def run(self, argv: list[str], *, cwd: str = "") -> tuple[int, str, str]:
        """Run a command (argv list, shell=False) and return (exit_code, stdout, stderr)."""
        ...


class LiveCommandRunner:
    """Production command runner using subprocess with shell=False.

    F19: Never uses ``shell=True``. Accepts only an argv list, never a
    caller-supplied shell string.
    """

    def __init__(self, cwd: str = ".") -> None:
        self.default_cwd = cwd

    def run(self, argv: list[str], *, cwd: str = "") -> tuple[int, str, str]:
        if not isinstance(argv, list) or not argv:
            raise EvidenceCollectionError("invalid_argv", "argv must be a non-empty list")
        result = subprocess.run(
            argv,
            shell=False,  # F19: shell must remain False
            cwd=cwd or self.default_cwd,
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
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], *, cwd: str = "") -> tuple[int, str, str]:
        self.calls.append(list(argv))
        return (self._exit_code, self._stdout, self._stderr)


# ---------------------------------------------------------------------------
# Trusted live evidence factory (F27)
# ---------------------------------------------------------------------------

def _create_trusted_evidence(
    *,
    execution_id: str,
    repository: str,
    base_sha: str,
    head_sha: str,
    pr_number: int,
    required_workflows: tuple[str, ...],
    changed_paths: tuple[str, ...] = (),
    test_results: dict[str, Any] | None = None,
    git_diff_check_passed: bool = False,
    agent_completion_claim: str = "",
    ci_checks: tuple[dict[str, Any], ...] = (),
    collected_at: str = "",
) -> ExecutionEvidence:
    """Create live evidence — the sole trusted factory.

    F27: This function imports the module-private ``_LIVE_FACTORY_TOKEN``
    from :mod:`contracts` and passes it to the ``ExecutionEvidence``
    constructor. No other path can produce ``collection_mode=live``.
    """

    return ExecutionEvidence(
        execution_id=execution_id,
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        pr_number=pr_number,
        required_workflows=required_workflows,
        changed_paths=changed_paths,
        test_results=test_results or {},
        git_diff_check_passed=git_diff_check_passed,
        agent_completion_claim=agent_completion_claim,
        ci_checks=ci_checks,
        collected_at=collected_at,
        collection_mode="live",
        provenance="trusted_git_github_collector",
        _factory_token=_LIVE_FACTORY_TOKEN,
    )


# ---------------------------------------------------------------------------
# Legacy function-based Git evidence (kept for backward compatibility)
# ---------------------------------------------------------------------------

def get_changed_paths(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> tuple[str, ...]:
    return LiveGitAdapter(repo_dir).get_changed_paths(base_sha, head_sha)


def check_git_diff(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> bool:
    return LiveGitAdapter(repo_dir).check_git_diff(base_sha, head_sha)


def get_head_sha(repo_dir: str = ".") -> str:
    return LiveGitAdapter(repo_dir).get_head_sha()


# ---------------------------------------------------------------------------
# Trusted live evidence collection (F14/F19/F20/F26)
# ---------------------------------------------------------------------------

def _select_required_test_commands(bundle: AuthorityBundle) -> list[dict[str, Any]]:
    """Select required test commands from the Authority Bundle.

    F19: Commands are selected by ``command_id`` from the approved Command
    Plan. Only commands with ``phase=test`` and ``required=true`` are
    selected for live evidence collection.
    """

    commands: list[dict[str, Any]] = []
    for cmd in bundle.allowed_commands:
        if (
            cmd.get("phase") == "test"
            and cmd.get("required") is True
        ):
            commands.append(cmd)
    return commands


def _parse_command_to_argv(command_str: str) -> list[str]:
    """Parse a command string into an argv list.

    F19: Uses ``shlex.split`` to produce an argv list for ``shell=False``
    execution. Rejects shell metacharacters.
    """

    if not _is_safe_command(command_str):
        raise EvidenceCollectionError(
            "shell_metacharacters_rejected",
            command_str,
        )
    try:
        argv = shlex.split(command_str)
    except ValueError as exc:
        raise EvidenceCollectionError("shlex_parse_failed", str(exc))
    if not argv:
        raise EvidenceCollectionError("empty_command", command_str)
    return argv


def collect_live_evidence(
    *,
    bundle: AuthorityBundle,
    git_adapter: GitAdapter | None = None,
    github_adapter: GitHubAdapter | None = None,
    command_runner: CommandRunner | None = None,
    agent_completion_claim: str = "",
    collected_at: str = "",
) -> ExecutionEvidence:
    """Collect trusted live evidence through injectable adapters.

    F14: The collector owns truth. It does NOT accept caller-supplied test
    pass/fail booleans, CI success lists, or shell commands.

    F19: Test commands are selected by ``command_id`` from the Authority
    Bundle's Command Plan. Execution uses ``shell=False`` with argv lists.

    F20/F26: All authority comes from the ``bundle``, not from stdin.

    Raises ``EvidenceCollectionError`` or ``GitHubAdapterError`` on failure.
    """

    if git_adapter is None:
        git_adapter = LiveGitAdapter()
    if github_adapter is None:
        github_adapter = LiveGitHubAdapter()

    # The expected head is the PR head observed by the Authority Bundle.
    expected_head = bundle.pr_head_ref_oid
    if not expected_head:
        raise EvidenceCollectionError(
            "missing_pr_head_ref_oid",
            "Authority Bundle did not observe PR head SHA",
        )

    # 1. Collect Git facts
    local_head = git_adapter.get_head_sha()
    if local_head != expected_head:
        raise EvidenceCollectionError(
            "head_sha_mismatch",
            f"local={local_head} pr_head={expected_head}",
        )

    changed_paths = git_adapter.get_changed_paths(bundle.base_sha, expected_head)
    diff_ok = git_adapter.check_git_diff(bundle.base_sha, expected_head)

    # 2. Collect test results (only from approved command_id selections)
    test_results: dict[str, Any] = {}
    if command_runner is not None:
        test_commands = _select_required_test_commands(bundle)
        all_passed = True
        command_results: list[dict[str, Any]] = []
        for cmd in test_commands:
            command_id = str(cmd.get("command_id", ""))
            command_str = str(cmd.get("command", ""))
            try:
                argv = _parse_command_to_argv(command_str)
            except EvidenceCollectionError as exc:
                command_results.append({
                    "command_id": command_id,
                    "command": command_str,
                    "passed": False,
                    "error": exc.code,
                })
                all_passed = False
                continue
            exit_code, stdout, _stderr = command_runner.run(argv)
            passed = exit_code == 0
            command_results.append({
                "command_id": command_id,
                "command": command_str,
                "argv": argv,
                "passed": passed,
                "exit_code": exit_code,
            })
            if not passed:
                all_passed = False
        test_results = {
            "passed": all_passed,
            "commands": command_results,
        }

    # 3. Collect CI workflow runs via structured GitHub adapter
    workflow_runs = github_adapter.get_workflow_runs(
        bundle.repository, expected_head,
    )

    # 4. Validate workflow observations
    required_workflows = tuple(
        composite_name(wf, ev) for wf, ev in bundle.required_workflow_keys
    )
    blocking, _info = validate_workflow_observations(
        workflow_runs, required_workflows, expected_head,
    )
    if blocking:
        raise EvidenceCollectionError(
            "workflow_validation_failed",
            ";".join(blocking),
        )

    # 5. Build live evidence using the trusted factory
    ci_checks = checks_to_ci_tuples(workflow_runs)
    return _create_trusted_evidence(
        execution_id=f"exec-issue-{bundle.issue_number}-{bundle.decision_content_sha256[:12]}",
        repository=bundle.repository,
        base_sha=bundle.base_sha,
        head_sha=expected_head,
        pr_number=bundle.pr_number,
        required_workflows=required_workflows,
        changed_paths=changed_paths,
        test_results=test_results,
        git_diff_check_passed=diff_ok,
        agent_completion_claim=agent_completion_claim,
        ci_checks=ci_checks,
        collected_at=collected_at,
    )


# ---------------------------------------------------------------------------
# Legacy assemble_evidence (F27: deprecated — produces fixture evidence only)
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
    """DEPRECATED: produces fixture evidence only.

    F27: This function can no longer produce acceptance-grade live evidence.
    It returns ``collection_mode=fixture`` and ``provenance=caller_asserted``.
    Use :func:`collect_live_evidence` with an :class:`AuthorityBundle` for
    live evidence.
    """

    git_adapter = LiveGitAdapter(repo_dir)
    changed_paths = git_adapter.get_changed_paths(base_sha, head_sha)
    diff_ok = git_adapter.check_git_diff(base_sha, head_sha)

    # F27: use create_live (which now produces fixture) for backward compat
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
    remain empty — NO fallback to untrusted data.
    """

    return ExecutionEvidence(
        execution_id=trusted.execution_id,
        repository=trusted.repository,
        base_sha=trusted.base_sha,
        head_sha=trusted.head_sha,
        pr_number=trusted.pr_number,
        required_workflows=trusted.required_workflows,
        changed_paths=trusted.changed_paths,
        test_results=trusted.test_results,
        git_diff_check_passed=trusted.git_diff_check_passed,
        agent_completion_claim=untrusted.agent_completion_claim,
        ci_checks=trusted.ci_checks,
        collected_at=trusted.collected_at,
        collection_mode=trusted.collection_mode,
        provenance=trusted.provenance,
    )
