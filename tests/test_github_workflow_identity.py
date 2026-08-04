"""Behavior tests for canonical GitHub workflow-run path identity."""

from __future__ import annotations

import pytest

from reverse_agent.github_workflow_identity import (
    WorkflowRunPathIdentityError,
    canonicalize_workflow_run_path,
)


EXPECTED = ".github/workflows/state-gate.yml"


@pytest.mark.parametrize(
    "observed",
    [
        EXPECTED,
        f"{EXPECTED}@main",
        f"{EXPECTED}@refs/heads/main",
        f"{EXPECTED}@{'a' * 40}",
    ],
)
def test_supported_run_paths_canonicalize_to_bare_path(observed: str) -> None:
    assert canonicalize_workflow_run_path(observed, EXPECTED) == EXPECTED


@pytest.mark.parametrize(
    "observed",
    [
        ".github/workflows/other.yml",
        "/.github/workflows/state-gate.yml",
        "../.github/workflows/state-gate.yml",
        f"{EXPECTED}@",
        f"{EXPECTED}@main@refs/heads/main",
        f"{EXPECTED}@refs/heads/feature",
        f"{EXPECTED}@main/extra",
        "",
        None,
        123,
    ],
)
def test_invalid_run_paths_fail_closed(observed: object) -> None:
    with pytest.raises(WorkflowRunPathIdentityError):
        canonicalize_workflow_run_path(observed, EXPECTED)
