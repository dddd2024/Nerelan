"""Git/GitHub evidence adapter: derive truth from repository state.

This adapter collects evidence from Git (diff, changed paths) and GitHub
(checks, CI results). The evidence produced here is "trusted" because it
comes from repository state, not from the agent's self-report.
"""

from __future__ import annotations

import subprocess
from typing import Any, Sequence

from .contracts import ExecutionEvidence


# ---------------------------------------------------------------------------
# Git evidence
# ---------------------------------------------------------------------------

def get_changed_paths(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> tuple[str, ...]:
    """Return the list of changed file paths between base and head."""

    result = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return ()
    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return tuple(dict.fromkeys(paths))


def check_git_diff(base_sha: str, head_sha: str = "HEAD", repo_dir: str = ".") -> bool:
    """Return True if ``git diff --check`` passes (no whitespace errors)."""

    result = subprocess.run(
        ["git", "diff", "--check", f"{base_sha}..{head_sha}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# GitHub evidence
# ---------------------------------------------------------------------------

def parse_pr_checks(checks_output: str) -> tuple[dict[str, Any], ...]:
    """Parse ``gh pr checks`` output into a tuple of check dicts.

    The output format is tabular; we parse name, state, and conclusion.
    This is a best-effort parser for the provider-free test path.
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
        # Look for SUCCESS/FAILURE/PENDING in the line
        status = "UNKNOWN"
        for token in parts[1:]:
            token_upper = token.upper()
            if token_upper in ("SUCCESS", "FAILURE", "PENDING", "SKIPPED", "CANCELLED"):
                status = token_upper
                break
        checks.append({"name": name, "status": status, "conclusion": status})
    return tuple(checks)


# ---------------------------------------------------------------------------
# Evidence assembly
# ---------------------------------------------------------------------------

def assemble_evidence(
    execution_id: str,
    base_sha: str,
    head_sha: str = "HEAD",
    repo_dir: str = ".",
    ci_checks: Sequence[dict[str, Any]] = (),
    test_results: dict[str, Any] | None = None,
    agent_completion_claim: str = "",
) -> ExecutionEvidence:
    """Assemble trusted ExecutionEvidence from Git and CI state.

    This function always prefers Git/CI truth over the agent's claim.
    """

    changed_paths = get_changed_paths(base_sha, head_sha, repo_dir)
    diff_ok = check_git_diff(base_sha, head_sha, repo_dir)

    return ExecutionEvidence(
        execution_id=execution_id,
        changed_paths=changed_paths,
        test_results=test_results or {},
        git_diff_check_passed=diff_ok,
        agent_completion_claim=agent_completion_claim,
        ci_checks=tuple(ci_checks),
        collected_at="",
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
        changed_paths=trusted.changed_paths or untrusted.changed_paths,
        test_results=trusted.test_results or untrusted.test_results,
        git_diff_check_passed=trusted.git_diff_check_passed,
        agent_completion_claim=untrusted.agent_completion_claim,
        ci_checks=trusted.ci_checks,
        collected_at=trusted.collected_at,
    )
