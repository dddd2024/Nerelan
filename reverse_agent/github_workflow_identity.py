"""Canonical identity checks for GitHub workflow-run paths."""

from __future__ import annotations

import re
from typing import Any


STATE_GATE_WORKFLOW_PATH = ".github/workflows/state-gate.yml"
_COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")

class WorkflowRunPathIdentityError(ValueError):
    """Raised when a workflow-run path cannot be bound to the expected file."""


def canonicalize_workflow_run_path(
    observed: Any,
    expected_repository_relative_path: str,
) -> str:
    """Return the bare repository-relative workflow path or fail closed.

    GitHub may report a workflow-run path as the bare workflow file or append
    the target ref.  Main, its fully qualified ref, and an exact lower-case
    commit SHA are accepted; all other adornment is rejected.
    """

    if not isinstance(observed, str):
        raise WorkflowRunPathIdentityError("workflow_path_not_string")
    if not isinstance(expected_repository_relative_path, str):
        raise WorkflowRunPathIdentityError("expected_workflow_path_not_string")
    expected = expected_repository_relative_path
    if expected != STATE_GATE_WORKFLOW_PATH:
        raise WorkflowRunPathIdentityError("expected_workflow_path_invalid")
    if not observed or observed != observed.strip():
        raise WorkflowRunPathIdentityError("workflow_path_invalid")
    if observed == expected:
        return expected
    if observed.count("@") != 1:
        raise WorkflowRunPathIdentityError("workflow_path_suffix_invalid")
    path, suffix = observed.split("@", 1)
    if path != expected:
        raise WorkflowRunPathIdentityError("workflow_path_mismatch")
    if suffix not in ("main", "refs/heads/main") and not _COMMIT_SHA_RE.fullmatch(suffix):
        raise WorkflowRunPathIdentityError("workflow_path_suffix_invalid")
    return expected
