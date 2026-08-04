"""Structured GitHub adapter for Platform V1 live-evidence collection.

F22: Replaces unsupported ``gh pr checks --json ... detail`` with
``gh run list --commit <exact-head> --json ...`` which provides structured
exact-head workflow run data including ``workflowName``, ``event``,
``headSha``, ``status``, and ``conclusion``.

F23: Required runs are modeled as canonical ``(workflowName, event)`` keys.
The job ``name`` (e.g. ``baseline``) is never confused with the workflow
name (e.g. ``CI``). Push and pull_request State Gate runs remain distinct.

F24: Strict success — ``status=completed`` AND ``conclusion=success``.
Empty conclusion never passes. Pending, queued, in_progress, skipped,
cancelled, neutral, stale, timed_out, action_required, unknown, and
failure all block.

The adapter is injectable so provider-free tests can use
:class:`FakeGitHubAdapter` without network access.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Protocol, Sequence

from reverse_agent.github_workflow_identity import (
    WorkflowRunPathIdentityError,
    canonicalize_workflow_run_path,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class GitHubAdapterError(Exception):
    """Raised when GitHub API/CLI collection fails."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Canonical workflow/event key mapping
# ---------------------------------------------------------------------------

# Maps (workflowName, event) to the composite name used in required_workflows.
# F23: Do not manufacture composite names inside observed GitHub facts;
# this mapping is only used to bridge observed runs to the required_workflows
# list format used by ExecutionEvidence.
_KEY_TO_COMPOSITE_NAME: dict[tuple[str, str], str] = {
    ("CI", "pull_request"): "CI",
    ("Decision Preflight", "pull_request"): "Decision Preflight",
    ("State Gate", "pull_request_target"): "State Gate (pull_request_target)",
    ("State Gate", "push"): "State Gate (push)",
}

# Reverse mapping: composite name → (workflowName, event)
_COMPOSITE_NAME_TO_KEY: dict[str, tuple[str, str]] = {
    v: k for k, v in _KEY_TO_COMPOSITE_NAME.items()
}

# Non-success conclusions that fail closed. F24.
_REJECTED_CONCLUSIONS = frozenset({
    "PENDING",
    "QUEUED",
    "IN_PROGRESS",
    "SKIPPED",
    "CANCELLED",
    "UNKNOWN",
    "FAILURE",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "STALE",
    "NEUTRAL",
    "",  # empty conclusion never passes
})

# Non-completed statuses that fail closed.
_REJECTED_STATUSES = frozenset({
    "PENDING",
    "QUEUED",
    "IN_PROGRESS",
    "SKIPPED",
    "CANCELLED",
    "UNKNOWN",
    "STALE",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "NEUTRAL",
})


def composite_name(workflow_name: str, event: str) -> str:
    """Map (workflowName, event) to composite name for required_workflows."""

    return _KEY_TO_COMPOSITE_NAME.get(
        (workflow_name, event),
        f"{workflow_name} ({event})",
    )


# ---------------------------------------------------------------------------
# WorkflowRun — observed GitHub Actions run
# ---------------------------------------------------------------------------

class WorkflowRun:
    """A single GitHub Actions workflow run observation.

    F22/F23: Preserves the real ``workflow_name`` (e.g. ``CI``,
    ``Decision Preflight``, ``State Gate``) and ``event`` (e.g.
    ``pull_request``, ``push``) from ``gh run list``. The job ``name``
    (e.g. ``baseline``) is NOT used as the workflow identifier.
    """

    __slots__ = (
        "workflow_name",
        "event",
        "run_id",
        "head_sha",
        "head_branch",
        "status",
        "conclusion",
        "workflow_id",
        "attempt",
        "source_pr",
        "created_at",
        "workflow_path",
        "repository",
    )

    def __init__(
        self,
        *,
        workflow_name: str,
        event: str,
        run_id: str,
        head_sha: str,
        head_branch: str = "",
        status: str = "",
        conclusion: str = "",
        workflow_id: str = "",
        attempt: int = 0,
        source_pr: int = 0,
        created_at: str = "",
        workflow_path: str = "",
        repository: str = "",
    ) -> None:
        self.workflow_name = workflow_name
        self.event = event
        self.run_id = str(run_id)
        self.head_sha = head_sha
        self.head_branch = head_branch
        self.status = status.upper()
        self.conclusion = conclusion.upper()
        self.workflow_id = str(workflow_id)
        self.attempt = int(attempt)
        self.source_pr = int(source_pr)
        self.created_at = created_at
        self.workflow_path = workflow_path
        self.repository = repository

    @property
    def composite_name(self) -> str:
        """Composite name for comparison with required_workflows."""

        return composite_name(self.workflow_name, self.event)

    @property
    def key(self) -> tuple[str, str]:
        """Canonical (workflowName, event) key."""

        return (self.workflow_name, self.event)

    @property
    def is_success(self) -> bool:
        """F24: True only when status=completed AND conclusion=success."""

        return self.status == "COMPLETED" and self.conclusion == "SUCCESS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.composite_name,
            "workflow_name": self.workflow_name,
            "event": self.event,
            "run_id": self.run_id,
            "head_sha": self.head_sha,
            "head_branch": self.head_branch,
            "status": self.status,
            "conclusion": self.conclusion,
            "workflow_id": self.workflow_id,
            "attempt": self.attempt,
            "source_pr": self.source_pr,
            "created_at": self.created_at,
            "workflow_path": self.workflow_path,
            "repository": self.repository,
        }

    def __repr__(self) -> str:
        return (
            f"WorkflowRun(workflow_name={self.workflow_name!r}, "
            f"event={self.event!r}, run_id={self.run_id!r}, "
            f"head_sha={self.head_sha!r}, status={self.status!r}, "
            f"conclusion={self.conclusion!r})"
        )


# Backward-compatible alias
WorkflowCheck = WorkflowRun


# ---------------------------------------------------------------------------
# Adapter protocol
# ---------------------------------------------------------------------------

class GitHubAdapter(Protocol):
    """Injectable GitHub adapter protocol."""

    def get_workflow_runs(
        self,
        repository: str,
        exact_head_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        """Return workflow runs for the exact head SHA.

        Raises :class:`GitHubAdapterError` on any failure.
        """
        ...

    def get_state_gate_target_runs(
        self,
        repository: str,
        source_pr: int,
        trusted_base_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        """Return every canonical current-PR State Gate target run."""
        ...


# ---------------------------------------------------------------------------
# Live adapter — uses ``gh run list --commit``
# ---------------------------------------------------------------------------

class LiveGitHubAdapter:
    """Production GitHub adapter using ``gh run list --commit``.

    F22: Uses structured JSON output from ``gh run list`` which provides
    ``workflowName``, ``event``, ``headSha``, ``status``, ``conclusion``,
    ``databaseId``, and ``workflowDatabaseId`` — all structured fields.

    F23: Does NOT use ``gh pr checks`` (which has unsupported fields and
    confuses job name with workflow name).
    """

    # Fields requested from gh run list — all supported structured fields.
    _JSON_FIELDS = (
        "attempt,conclusion,databaseId,event,headBranch,headSha,"
        "name,status,workflowDatabaseId,workflowName"
    )

    _STATE_GATE_WORKFLOW_PATH = ".github/workflows/state-gate.yml"

    def get_workflow_runs(
        self,
        repository: str,
        exact_head_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        result = subprocess.run(
            [
                "gh", "run", "list",
                "--repo", repository,
                "--commit", exact_head_sha,
                "--json", self._JSON_FIELDS,
                "--limit", "50",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise GitHubAdapterError(
                "gh_run_list_failed",
                f"exit={result.returncode}",
            )
        try:
            raw_runs = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError as exc:
            raise GitHubAdapterError("gh_run_list_json_parse_failed", str(exc))

        runs: list[WorkflowRun] = []
        for raw in raw_runs:
            if not isinstance(raw, dict):
                continue
            workflow_name = str(raw.get("workflowName", ""))
            if not workflow_name:
                continue
            event = str(raw.get("event", ""))
            if not event:
                continue
            runs.append(WorkflowRun(
                workflow_name=workflow_name,
                event=event,
                run_id=str(raw.get("databaseId", "")),
                head_sha=str(raw.get("headSha", "")),
                head_branch=str(raw.get("headBranch", "")),
                status=str(raw.get("status", "")),
                conclusion=str(raw.get("conclusion", "")),
                workflow_id=str(raw.get("workflowDatabaseId", "")),
                attempt=int(raw.get("attempt", 0)),
            ))
        return tuple(runs)

    def get_state_gate_target_runs(
        self,
        repository: str,
        source_pr: int,
        trusted_base_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        """Observe every canonical State Gate target run for ``source_pr``.

        The REST workflow endpoint is queried with ``--paginate --slurp`` so
        pagination is owned by ``gh`` and every returned page can be checked
        against ``total_count``.  Each run is independently bound to the
        canonical workflow path, repository, target event, trusted base and
        GitHub's remote pull-request association before it is returned.
        """

        endpoint = (
            f"repos/{repository}/actions/workflows/state-gate.yml/runs"
        )
        result = subprocess.run(
            [
                "gh", "api", "--method", "GET", "--paginate", "--slurp",
                endpoint,
                "-f", "event=pull_request_target",
                "-f", f"head_sha={trusted_base_sha}",
                "-f", "per_page=100",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise GitHubAdapterError(
                "state_gate_target_api_failed", f"exit={result.returncode}",
            )
        try:
            pages = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise GitHubAdapterError(
                "state_gate_target_json_parse_failed", str(exc),
            )
        if not isinstance(pages, list) or not pages:
            raise GitHubAdapterError("state_gate_target_pagination_incomplete", "no_pages")

        raw_runs: list[dict[str, Any]] = []
        observed_total: int | None = None
        for page in pages:
            if not isinstance(page, dict):
                raise GitHubAdapterError(
                    "state_gate_target_pagination_incomplete", "page_not_object",
                )
            total_count = page.get("total_count")
            page_runs = page.get("workflow_runs")
            if not isinstance(total_count, int) or not isinstance(page_runs, list):
                raise GitHubAdapterError(
                    "state_gate_target_pagination_incomplete", "missing_page_fields",
                )
            if observed_total is None:
                observed_total = total_count
            elif observed_total != total_count:
                raise GitHubAdapterError(
                    "state_gate_target_pagination_incomplete", "total_count_changed",
                )
            if any(not isinstance(run, dict) for run in page_runs):
                raise GitHubAdapterError(
                    "state_gate_target_run_malformed", "run_not_object",
                )
            raw_runs.extend(page_runs)
        if observed_total is None or len(raw_runs) != observed_total:
            raise GitHubAdapterError(
                "state_gate_target_pagination_incomplete",
                f"observed={len(raw_runs)} total={observed_total}",
            )

        runs: list[WorkflowRun] = []
        for raw in raw_runs:
            try:
                workflow_path = canonicalize_workflow_run_path(
                    raw.get("path"), self._STATE_GATE_WORKFLOW_PATH,
                )
            except WorkflowRunPathIdentityError as exc:
                raise GitHubAdapterError(
                    "state_gate_target_run_identity_mismatch",
                    f"run_id={raw.get('id', '')}:workflow_path={exc}",
                ) from exc
            observed_repository = str(
                ((raw.get("repository") or {}).get("full_name")) or ""
            )
            pull_requests = raw.get("pull_requests")
            if (
                observed_repository != repository
                or raw.get("event") != "pull_request_target"
                or raw.get("head_sha") != trusted_base_sha
                or not isinstance(pull_requests, list)
            ):
                raise GitHubAdapterError(
                    "state_gate_target_run_identity_mismatch",
                    f"run_id={raw.get('id', '')}",
                )
            associated_prs = {
                int(pr.get("number") or 0)
                for pr in pull_requests
                if isinstance(pr, dict)
            }
            if int(source_pr) not in associated_prs:
                continue
            run_id = int(raw.get("id") or 0)
            attempt = int(raw.get("run_attempt") or 0)
            created_at = str(raw.get("created_at") or "")
            if run_id <= 0 or attempt <= 0 or not created_at:
                raise GitHubAdapterError(
                    "state_gate_target_run_malformed", f"run_id={run_id}",
                )
            runs.append(WorkflowRun(
                workflow_name="State Gate",
                event="pull_request_target",
                run_id=str(run_id),
                head_sha=str(raw.get("head_sha", "")),
                head_branch=str(raw.get("head_branch", "")),
                status=str(raw.get("status", "")),
                conclusion=str(raw.get("conclusion", "")),
                workflow_id=str(raw.get("workflow_id", "")),
                attempt=attempt,
                source_pr=int(source_pr),
                created_at=created_at,
                workflow_path=workflow_path,
                repository=observed_repository,
            ))
        return tuple(runs)

    # Backward-compatible alias for existing callers
    def get_pr_checks(
        self,
        pr_number: int,
        repository: str,
        expected_head_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        """DEPRECATED alias for :meth:`get_workflow_runs`.

        F22: The ``pr_number`` parameter is ignored. Workflow runs are
        queried by exact head SHA, not by PR number.
        """

        return self.get_workflow_runs(repository, expected_head_sha)


# ---------------------------------------------------------------------------
# Fake adapter for tests
# ---------------------------------------------------------------------------

class FakeGitHubAdapter:
    """Fake GitHub adapter for provider-free tests."""

    def __init__(
        self,
        runs: Sequence[WorkflowRun] | None = None,
        *,
        fail_with: GitHubAdapterError | None = None,
    ) -> None:
        self._runs = tuple(runs) if runs else ()
        self._fail_with = fail_with
        self.call_count = 0

    def get_workflow_runs(
        self,
        repository: str,
        exact_head_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        # Filter to exact head SHA — preserve observed head_sha, don't overwrite
        return tuple(r for r in self._runs if r.head_sha == exact_head_sha)

    # Backward-compatible alias
    def get_pr_checks(
        self,
        pr_number: int,
        repository: str,
        expected_head_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        return self.get_workflow_runs(repository, expected_head_sha)

    def get_state_gate_target_runs(
        self,
        repository: str,
        source_pr: int,
        trusted_base_sha: str,
    ) -> tuple[WorkflowRun, ...]:
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        return tuple(
            run for run in self._runs
            if run.workflow_name == "State Gate"
            and run.event == "pull_request_target"
            and run.head_sha == trusted_base_sha
            and run.source_pr in (0, int(source_pr))
        )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_workflow_observations(
    observed: tuple[WorkflowRun, ...],
    required_workflows: tuple[str, ...],
    expected_head_sha: str,
) -> tuple[list[str], list[str]]:
    """Validate observed workflow runs against required set.

    F22/F23/F24: Returns (blocking_reasons, info_messages).

    Required workflows are composite names (e.g. ``State Gate (push)``).
    Observed runs are matched by their composite_name property, which maps
    (workflowName, event) to the composite name.

    Blocking reasons include:
    - wrong head SHA (runs not matching expected_head_sha)
    - missing required workflows
    - duplicate runs for the same required key
    - extra unexpected workflows
    - any non-success status/conclusion (F24: strict success required)
    - empty conclusion (F24: never passes)
    """

    blocking: list[str] = []
    info: list[str] = []

    if not observed:
        blocking.append("no_workflow_observations")
        return blocking, info

    # F22: Check for wrong head SHA — observed head_sha is read from GitHub,
    # not assigned from expected_head_sha.
    for run in observed:
        if run.head_sha != expected_head_sha:
            blocking.append(
                f"wrong_head_workflow:{run.workflow_name}/{run.event}:"
                f"head={run.head_sha}:expected={expected_head_sha}"
            )

    # Map composite names to runs
    runs_by_composite: dict[str, list[WorkflowRun]] = {}
    for run in observed:
        comp = run.composite_name
        runs_by_composite.setdefault(comp, []).append(run)

    # Check for duplicate runs per required key
    for comp, runs in runs_by_composite.items():
        if len(runs) > 1:
            blocking.append(f"duplicate_workflow:{comp}:count={len(runs)}")

    # Check observed set matches required set exactly (F12)
    observed_set = set(runs_by_composite.keys())
    required_set = set(required_workflows)
    missing = required_set - observed_set
    extra = observed_set - required_set
    if missing:
        blocking.append(f"missing_workflows:{','.join(sorted(missing))}")
    if extra:
        blocking.append(f"extra_workflows:{','.join(sorted(extra))}")

    # F24: Check each required workflow has strict success
    for required in required_workflows:
        runs = runs_by_composite.get(required, [])
        if not runs:
            continue  # already reported as missing
        for run in runs:
            if not run.is_success:
                blocking.append(
                    f"workflow_not_success:{required}:"
                    f"status={run.status}:conclusion={run.conclusion}"
                )

    return blocking, info


def checks_to_ci_tuples(runs: tuple[WorkflowRun, ...]) -> tuple[dict[str, Any], ...]:
    """Convert WorkflowRun objects to the ci_checks dict format.

    Each dict includes ``name`` (composite), ``workflow_name``, ``event``,
    ``status``, ``conclusion``, ``head_sha``, and ``run_id``.
    """

    return tuple(r.to_dict() for r in runs)
