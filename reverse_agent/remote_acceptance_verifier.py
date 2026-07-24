"""Remote acceptance verifier interface for v3 exact-head merge approval.

The :class:`RemoteAcceptanceVerifier` protocol defines the narrow interface
that the production gate calls to prove every GitHub workflow run and PR
approval fact.  The production implementation (used in CI) queries the
GitHub API with read-only permissions.  Hermetic tests use
:class:`tests._v3_helpers.FakeRemoteAcceptanceVerifier`.

API failure, missing permission, unknown run, or mismatched identity must
fail closed (return ``{'verified': False, ...}``).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RemoteAcceptanceVerifier(Protocol):
    """Narrow interface for verifying remote GitHub evidence."""

    def verify_workflow_run(
        self,
        *,
        run_id: int,
        expected_head_sha: str,
        expected_workflow_file: str,
        expected_event: str,
        expected_conclusion: str = "success",
    ) -> dict[str, Any]:
        """Verify a GitHub Actions workflow run exists and matches expectations.

        Returns ``{'verified': True, 'run': {...}}`` on success or
        ``{'verified': False, 'reason': '...'}`` on failure.
        """
        ...

    def verify_pr(
        self,
        *,
        pr_number: int,
        expected_head_sha: str,
        expected_base_sha: str,
        expected_repository: str = "dddd2024/reverse-agent",
    ) -> dict[str, Any]:
        """Verify a pull request exists and matches the expected head/base.

        Returns ``{'verified': True, 'pr': {...}}`` on success or
        ``{'verified': False, 'reason': '...'}`` on failure.
        """
        ...

    def verify_pr_approval(
        self,
        *,
        pr_number: int,
        approval_reference: str,
        expected_head_sha: str,
        expected_base_sha: str,
        expected_merge_method: str,
        allowed_approvers: list[str],
    ) -> dict[str, Any]:
        """Verify a PR approval exists and was produced by an allowed approver.

        Returns ``{'verified': True, 'approval': {...}}`` on success or
        ``{'verified': False, 'reason': '...'}`` on failure.
        """
        ...
