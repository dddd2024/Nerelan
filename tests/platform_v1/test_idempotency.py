"""Idempotency tests for Platform V1.

Verifies the deterministic identity guarantees:
- Same Work Item (Issue + base SHA + goal + checks + digest) always produces
  the same execution_id, branch_name, and pr_marker.
- Duplicate events for the same Work Item never create a second execution,
  branch, or Draft PR (same identity).
- Different Issue numbers or different base SHAs produce different identities.
- Identity is derived from the canonical digest, not the base SHA prefix.
- Material field changes (goal, required_checks, approved_issue_body_digest)
  change the digest and identity.
"""

from __future__ import annotations

from reverse_agent.platform_v1.contracts import (
    ExecutionBinding,
    PlatformWorkItem,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
ALT_BASE_SHA = "16526801bda2a816fc707342f903c1ad037de9bd"
VALID_ISSUE_BODY_DIGEST = "a" * 64  # F25: SHA-256, 64 hex chars


def _make_work_item(
    issue: int = 96,
    base_sha: str = VALID_BASE_SHA,
    target_branch: str = "agent/platform-v1-openhands-codex-acp",
    **overrides,
) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": issue,
        "repository": "dddd2024/reverse-agent",
        "base_sha": base_sha,
        "allowed_paths": ("reverse_agent/platform_v1/**",),
        "forbidden_operations": ("push_main",),
        "acceptance_criteria": (),
        "goal": "test goal",
        "required_checks": ("pytest",),
        "approved_issue_body_digest": VALID_ISSUE_BODY_DIGEST,
        "risk_tier": "R0",
        "target_branch": target_branch,
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


# ---------------------------------------------------------------------------
# Deterministic identity
# ---------------------------------------------------------------------------

class TestDeterministicIdentity:
    def test_same_issue_and_base_produce_same_execution_id(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.execution_id == wi2.execution_id

    def test_same_issue_and_base_produce_same_branch_name(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.branch_name == wi2.branch_name

    def test_same_issue_and_base_produce_same_pr_marker(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.pr_marker == wi2.pr_marker

    def test_different_issue_produces_different_execution_id(self) -> None:
        wi1 = _make_work_item(issue=96)
        wi2 = _make_work_item(issue=97)
        assert wi1.execution_id != wi2.execution_id

    def test_different_base_produces_different_execution_id(self) -> None:
        wi1 = _make_work_item(base_sha=VALID_BASE_SHA)
        wi2 = _make_work_item(base_sha=ALT_BASE_SHA)
        assert wi1.execution_id != wi2.execution_id

    def test_different_issue_produces_different_pr_marker(self) -> None:
        wi1 = _make_work_item(issue=96)
        wi2 = _make_work_item(issue=97)
        assert wi1.pr_marker != wi2.pr_marker


# ---------------------------------------------------------------------------
# Duplicate events never create a second execution
# ---------------------------------------------------------------------------

class TestDuplicateEventIdempotency:
    """Two events for the same Work Item must produce the same identity.

    This means a duplicate event would never create a second execution,
    branch, or Draft PR — the second event would target the same identity
    and be deduplicated by the caller.
    """

    def test_two_events_same_work_item_same_identity(self) -> None:
        wi = _make_work_item()
        # First event creates binding attempt 1
        binding1 = ExecutionBinding(work_item=wi, attempt=1)
        # Second (duplicate) event also creates binding attempt 1
        binding2 = ExecutionBinding(work_item=wi, attempt=1)
        assert binding1.execution_id == binding2.execution_id
        assert binding1.branch_name == binding2.branch_name
        assert binding1.pr_marker == binding2.pr_marker
        assert binding1.attempt == binding2.attempt

    def test_retry_uses_same_identity_different_attempt(self) -> None:
        wi = _make_work_item()
        binding1 = ExecutionBinding(work_item=wi, attempt=1)
        binding2 = binding1.next_attempt()
        # Identity is the same; only the attempt differs
        assert binding1.execution_id == binding2.execution_id
        assert binding1.branch_name == binding2.branch_name
        assert binding1.pr_marker == binding2.pr_marker
        assert binding1.attempt != binding2.attempt

    def test_execution_id_uses_digest_prefix(self) -> None:
        wi = _make_work_item()
        # The execution_id is derived from the canonical digest, not the
        # base SHA. The first 12 chars of the digest must appear in the id.
        assert wi.digest[:12] in wi.execution_id
        assert wi.execution_id == f"exec-issue-96-{wi.digest[:12]}"

    def test_execution_id_does_not_use_base_sha_prefix(self) -> None:
        wi = _make_work_item()
        # The execution_id must NOT contain the base SHA prefix anymore.
        assert VALID_BASE_SHA[:12] not in wi.execution_id

    def test_pr_marker_uses_issue_and_digest(self) -> None:
        wi = _make_work_item(issue=96, base_sha=VALID_BASE_SHA)
        assert "issue-96" in wi.pr_marker
        assert wi.digest[:12] in wi.pr_marker
        assert wi.pr_marker == f"pr-marker-issue-96-{wi.digest[:12]}"

    def test_pr_marker_does_not_use_base_sha_prefix(self) -> None:
        wi = _make_work_item()
        assert VALID_BASE_SHA[:12] not in wi.pr_marker

    def test_digest_stable_across_constructors(self) -> None:
        wi1 = _make_work_item()
        wi2 = PlatformWorkItem.from_mapping({
            "source_issue_number": wi1.source_issue_number,
            "repository": wi1.repository,
            "base_sha": wi1.base_sha,
            "allowed_paths": list(wi1.allowed_paths),
            "forbidden_operations": list(wi1.forbidden_operations),
            "acceptance_criteria": list(wi1.acceptance_criteria),
            "goal": wi1.goal,
            "required_checks": list(wi1.required_checks),
            "approved_issue_body_digest": wi1.approved_issue_body_digest,
            "risk_tier": wi1.risk_tier,
            "target_branch": wi1.target_branch,
        })
        assert wi1.digest == wi2.digest
        assert wi1.execution_id == wi2.execution_id
        assert wi1.pr_marker == wi2.pr_marker


# ---------------------------------------------------------------------------
# Material field changes change digest/execution_id/pr_marker
# ---------------------------------------------------------------------------

class TestMaterialFieldChangeChangesIdentity:
    """Changing any materially meaningful field changes the digest and identity."""

    def test_changing_goal_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(goal="different goal")
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id
        assert changed.pr_marker != base.pr_marker

    def test_changing_required_checks_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(required_checks=("different-check",))
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id
        assert changed.pr_marker != base.pr_marker

    def test_changing_approved_issue_body_digest_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(approved_issue_body_digest="b" * 64)
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id
        assert changed.pr_marker != base.pr_marker

    def test_changing_acceptance_criteria_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(acceptance_criteria=("different criterion",))
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id

    def test_changing_risk_tier_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(risk_tier="R1")
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id

    def test_changing_target_branch_changes_identity(self) -> None:
        base = _make_work_item()
        changed = _make_work_item(target_branch="agent/other-branch")
        assert changed.digest != base.digest
        assert changed.execution_id != base.execution_id
