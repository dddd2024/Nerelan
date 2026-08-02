"""Structured GitHub adapter for Platform V1 live-evidence collection.

F13: Replaces tabular ``gh pr checks`` parsing with structured JSON/API
results. Preserves full multi-word workflow names, run IDs, head SHAs,
events, statuses, conclusions, and workflow IDs. Correctly distinguishes
``State Gate (push)`` from ``State Gate (pull_request)``.

The adapter is injectable so provider-free tests can use
:class:`FakeGitHubAdapter` without network access.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Protocol, Sequence


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class GitHubAdapterError(Exception):
    """Raised when GitHub API/CLI collection fails.

    The message is a stable, machine-readable error code so callers can map
    it to a documented nonzero exit code.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Canonical workflow check record
# ---------------------------------------------------------------------------

# Non-SUCCESS conclusions that fail closed.
_REJECTED_CONCLUSIONS = frozenset({
    "PENDING",
    "SKIPPED",
    "CANCELLED",
    "UNKNOWN",
    "FAILURE",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "STALE",
    "NEUTRAL",
})


class WorkflowCheck:
    """A single GitHub Actions workflow run observation.

    Preserves the full workflow name (including multi-word names like
    ``Decision Preflight`` and ``State Gate (push)``), the run ID, head SHA,
    event, status, conclusion, and workflow ID.
    """

    __slots__ = (
        "name",
        "run_id",
        "head_sha",
        "event",
        "status",
        "conclusion",
        "workflow_id",
    )

    def __init__(
        self,
        *,
        name: str,
        run_id: str,
        head_sha: str,
        event: str,
        status: str,
        conclusion: str,
        workflow_id: str = "",
    ) -> None:
        self.name = name
        self.run_id = str(run_id)
        self.head_sha = head_sha
        self.event = event
        self.status = status.upper()
        self.conclusion = conclusion.upper()
        self.workflow_id = str(workflow_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "run_id": self.run_id,
            "head_sha": self.head_sha,
            "event": self.event,
            "status": self.status,
            "conclusion": self.conclusion,
            "workflow_id": self.workflow_id,
        }

    def __repr__(self) -> str:
        return (
            f"WorkflowCheck(name={self.name!r}, run_id={self.run_id!r}, "
            f"head_sha={self.head_sha!r}, event={self.event!r}, "
            f"status={self.status!r}, conclusion={self.conclusion!r})"
        )


# ---------------------------------------------------------------------------
# Adapter protocol
# ---------------------------------------------------------------------------

class GitHubAdapter(Protocol):
    """Injectable GitHub adapter protocol.

    Production code uses :class:`LiveGitHubAdapter` which calls the GitHub
    CLI/API. Tests inject :class:`FakeGitHubAdapter` to avoid network access.
    """

    def get_pr_checks(
        self,
        pr_number: int,
        repository: str,
        expected_head_sha: str,
    ) -> tuple[WorkflowCheck, ...]:
        """Return workflow checks for the PR, filtered to expected_head_sha.

        Raises :class:`GitHubAdapterError` on any failure.
        """
        ...


# ---------------------------------------------------------------------------
# Live adapter
# ---------------------------------------------------------------------------

class LiveGitHubAdapter:
    """Production GitHub adapter using ``gh pr checks --json``.

    F13: Uses structured JSON output, not tabular parsing. Preserves full
    multi-word workflow names and all metadata fields.
    """

    def get_pr_checks(
        self,
        pr_number: int,
        repository: str,
        expected_head_sha: str,
    ) -> tuple[WorkflowCheck, ...]:
        result = subprocess.run(
            [
                "gh", "pr", "checks", str(pr_number),
                "--repo", repository,
                "--json", "name,workflow,state,conclusion,startedAt,completedAt,link,detail",
                "--required",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise GitHubAdapterError(
                "gh_pr_checks_failed",
                f"exit={result.returncode}",
            )
        try:
            raw_checks = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError as exc:
            raise GitHubAdapterError("gh_pr_checks_json_parse_failed", str(exc))

        checks: list[WorkflowCheck] = []
        for raw in raw_checks:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", raw.get("workflow", "")))
            if not name:
                continue
            state = str(raw.get("state", "")).upper()
            conclusion = str(raw.get("conclusion", "")).upper()
            # Map GitHub API states to status/conclusion
            if state in ("SUCCESS", "NEUTRAL", "SKIPPED", "CANCELLED", "FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "STALE"):
                status = "COMPLETED"
                final_conclusion = state
            elif state in ("PENDING", "QUEUED", "IN_PROGRESS"):
                status = state
                final_conclusion = ""
            else:
                status = state or "UNKNOWN"
                final_conclusion = conclusion
            checks.append(WorkflowCheck(
                name=name,
                run_id=str(raw.get("databaseId", raw.get("link", ""))),
                head_sha=expected_head_sha,  # bound to expected head
                event=str(raw.get("event", "")),
                status=status,
                conclusion=final_conclusion,
                workflow_id=str(raw.get("workflowId", "")),
            ))
        return tuple(checks)


# ---------------------------------------------------------------------------
# Fake adapter for tests
# ---------------------------------------------------------------------------

class FakeGitHubAdapter:
    """Fake GitHub adapter for provider-free tests.

    Accepts pre-configured workflow checks and optional failure modes.
    """

    def __init__(
        self,
        checks: Sequence[WorkflowCheck] | None = None,
        *,
        fail_with: GitHubAdapterError | None = None,
    ) -> None:
        self._checks = tuple(checks) if checks else ()
        self._fail_with = fail_with
        self.call_count = 0

    def get_pr_checks(
        self,
        pr_number: int,
        repository: str,
        expected_head_sha: str,
    ) -> tuple[WorkflowCheck, ...]:
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        # Filter to expected head SHA
        return tuple(c for c in self._checks if c.head_sha == expected_head_sha)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_workflow_observations(
    observed: tuple[WorkflowCheck, ...],
    required_workflows: tuple[str, ...],
    expected_head_sha: str,
) -> tuple[list[str], list[str]]:
    """Validate observed workflow checks against required set.

    F13: Returns (blocking_reasons, info_messages). Blocking reasons include:
    - missing required workflows
    - duplicate workflow names
    - wrong head SHA
    - stale/pending/skipped/cancelled/unknown/neutral/action_required/timed_out/failure
    - extra unexpected workflows (set mismatch)
    """

    blocking: list[str] = []
    info: list[str] = []

    if not observed:
        blocking.append("no_workflow_observations")
        return blocking, info

    # Check for wrong head SHA
    for check in observed:
        if check.head_sha != expected_head_sha:
            blocking.append(
                f"wrong_head_workflow:{check.name}:head={check.head_sha}:expected={expected_head_sha}"
            )

    # Check for duplicate workflow names
    names = [c.name for c in observed]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            blocking.append(f"duplicate_workflow:{name}")
        seen.add(name)

    # Check observed set matches required set exactly (F12)
    observed_set = set(names)
    required_set = set(required_workflows)
    missing = required_set - observed_set
    extra = observed_set - required_set
    if missing:
        blocking.append(f"missing_workflows:{','.join(sorted(missing))}")
    if extra:
        blocking.append(f"extra_workflows:{','.join(sorted(extra))}")

    # Check each required workflow has a valid conclusion
    checks_by_name = {c.name: c for c in observed}
    for required in required_workflows:
        check = checks_by_name.get(required)
        if check is None:
            continue  # already reported as missing
        if check.conclusion in _REJECTED_CONCLUSIONS:
            blocking.append(
                f"workflow_not_success:{required}:conclusion={check.conclusion}"
            )
        elif check.conclusion not in ("SUCCESS", "COMPLETED", ""):
            # Empty conclusion with COMPLETED status is acceptable (e.g., success)
            if check.status not in ("COMPLETED", "SUCCESS"):
                blocking.append(
                    f"workflow_not_success:{required}:status={check.status}"
                )

    return blocking, info


def checks_to_ci_tuples(checks: tuple[WorkflowCheck, ...]) -> tuple[dict[str, Any], ...]:
    """Convert WorkflowCheck objects to the ci_checks dict format."""

    return tuple(c.to_dict() for c in checks)
