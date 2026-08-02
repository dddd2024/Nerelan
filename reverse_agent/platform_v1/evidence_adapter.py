"""Git/GitHub evidence adapter: derive truth from repository state.

This adapter collects evidence from Git (diff, changed paths) and GitHub
(checks, CI results). The evidence produced here is "trusted" because it
comes from repository state, not from the agent's self-report.

Fail-closed: Git/GitHub read failures raise ``EvidenceCollectionError``
rather than returning empty/success-shaped evidence. The caller must
propagate this as a terminal error with a nonzero exit code.
"""

from __future__ import annotations

import subprocess
from typing import Any, Sequence

from .contracts import ExecutionEvidence


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
# Git evidence
# ---------------------------------------------------------------------------

def get_changed_paths(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> tuple[str, ...]:
    """Return the list of changed file paths between base and head.

    Raises ``EvidenceCollectionError`` on Git failure — never returns an
    empty list to mask a read failure.
    """

    result = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        cwd=repo_dir,
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


def check_git_diff(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> bool:
    """Return True if ``git diff --check`` passes (no whitespace errors).

    Raises ``EvidenceCollectionError`` on Git failure.
    """

    result = subprocess.run(
        ["git", "diff", "--check", f"{base_sha}..{head_sha}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode not in (0, 2):
        # exit code 2 means whitespace errors found (expected)
        # other non-zero codes mean git failure
        raise EvidenceCollectionError(
            "git_diff_check_failed",
            f"exit={result.returncode}",
        )
    return result.returncode == 0


def get_head_sha(repo_dir: str = ".") -> str:
    """Return the current HEAD SHA.

    Raises ``EvidenceCollectionError`` on Git failure.
    """

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise EvidenceCollectionError("git_rev_parse_failed", f"exit={result.returncode}")
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# GitHub evidence
# ---------------------------------------------------------------------------

def parse_pr_checks(checks_output: str) -> tuple[dict[str, Any], ...]:
    """Parse ``gh pr checks`` output into a tuple of check dicts.

    The output format is tabular; we parse name, state, and conclusion.
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

    Raises ``EvidenceCollectionError`` on GitHub CLI failure.
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
# Evidence assembly
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
    """Assemble trusted ExecutionEvidence from Git and CI state.

    This function always prefers Git/CI truth over the agent's claim.
    Uses ``collection_mode="live"`` and ``provenance="trusted_git_github_collector"``.

    Raises ``EvidenceCollectionError`` on Git/GitHub read failure.
    """

    changed_paths = get_changed_paths(base_sha, head_sha, repo_dir)
    diff_ok = check_git_diff(base_sha, head_sha, repo_dir)

    return ExecutionEvidence(
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
        collection_mode="live",
        provenance="trusted_git_github_collector",
    )


def merge_evidence(
    untrusted: ExecutionEvidence,
    trusted: ExecutionEvidence,
) -> ExecutionEvidence:
    """Merge untrusted (agent) evidence with trusted (Git/CI) evidence.

    Trusted evidence always wins: Git changed_paths, diff check, test results,
    and CI checks come from the trusted source. The agent's completion claim
    is preserved for audit but never overrides trusted evidence.
    """

    return ExecutionEvidence(
        execution_id=trusted.execution_id,
        repository=trusted.repository,
        base_sha=trusted.base_sha,
        head_sha=trusted.head_sha,
        pr_number=trusted.pr_number,
        required_workflows=trusted.required_workflows,
        changed_paths=trusted.changed_paths or untrusted.changed_paths,
        test_results=trusted.test_results or untrusted.test_results,
        git_diff_check_passed=trusted.git_diff_check_passed,
        agent_completion_claim=untrusted.agent_completion_claim,
        ci_checks=trusted.ci_checks,
        collected_at=trusted.collected_at,
        collection_mode=trusted.collection_mode,
        provenance=trusted.provenance,
    )
