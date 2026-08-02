"""Fail-closed and forbidden-capability tests for Platform V1.

Verifies that the platform adapter fails closed for:
- R4+ risk tiers at construction (R3 is valid at construction, blocked by policy)
- R2/R3 blocked by policy validator (blocked_approval)
- broad path scope (**, *, etc.)
- empty path scope
- forbidden publication operations (push_main, merge, mark_ready, etc.)
- third retry attempt is rejected
- forbidden components are not present in the codebase

Also verifies that the adapter does NOT include:
- Temporal, LiteLLM, Langfuse, Spec Kit
- custom frontend, second executor, new database
- custom sandbox, custom agent loop
- auto-merge, production deployment
- reverse-engineering specific capabilities
"""

from __future__ import annotations

import importlib
import importlib.util
import sys

import pytest

from reverse_agent.platform_v1.contracts import (
    FORBIDDEN_PUBLICATION_OPERATIONS,
    MAX_ATTEMPTS,
    ExecutionBinding,
    PlatformWorkItem,
)
from reverse_agent.platform_v1.policy_adapter import (
    PolicyViolation,
    validate_publication_operation,
    validate_work_item,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_ISSUE_BODY_DIGEST = "a" * 40


def _make_work_item(**overrides) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ("reverse_agent/platform_v1/**",),
        "forbidden_operations": ("push_main", "merge"),
        "acceptance_criteria": (),
        "goal": "test goal",
        "required_checks": ("pytest",),
        "approved_issue_body_digest": VALID_ISSUE_BODY_DIGEST,
        "risk_tier": "R0",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


# ---------------------------------------------------------------------------
# Fail-closed: risk tier
# ---------------------------------------------------------------------------

class TestRiskTierFailClosed:
    @pytest.mark.parametrize("tier", ["R4", "R5", "R6", "RX", "R99"])
    def test_invalid_risk_tier_rejected_at_construction(self, tier: str) -> None:
        # R3 is now VALID at construction; only R4+ (not in VALID_RISK_TIERS)
        # are rejected at construction with invalid_risk_tier.
        with pytest.raises(ValueError, match="invalid_risk_tier"):
            _make_work_item(risk_tier=tier)

    def test_R3_is_valid_at_construction(self) -> None:
        # R3 is a recognized risk tier now; it is blocked later by policy.
        wi = _make_work_item(risk_tier="R3")
        assert wi.risk_tier == "R3"

    @pytest.mark.parametrize("tier", ["R2", "R3", "R4"])
    def test_R2_or_higher_rejected_by_validator(self, tier: str) -> None:
        # R3 is valid at construction; R4 is not, so we mutate via
        # object.__setattr__ to test validate_work_item independently.
        wi = _make_work_item()
        object.__setattr__(wi, "risk_tier", tier)
        with pytest.raises(PolicyViolation, match="blocked_approval"):
            validate_work_item(wi)


# ---------------------------------------------------------------------------
# Fail-closed: path scope
# ---------------------------------------------------------------------------

class TestPathScopeFailClosed:
    @pytest.mark.parametrize("broad", ["**", "*", ".", "./", "/", "", "./**", "*.*"])
    def test_broad_path_rejected_at_construction(self, broad: str) -> None:
        with pytest.raises(ValueError, match="broad_path_rejected"):
            PlatformWorkItem(
                source_issue_number=1,
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                allowed_paths=(broad,),
                forbidden_operations=(),
                acceptance_criteria=(),
                goal="g",
                required_checks=("pytest",),
                approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
            )

    def test_empty_path_rejected_at_construction(self) -> None:
        with pytest.raises(ValueError, match="empty_path_scope_rejected"):
            PlatformWorkItem(
                source_issue_number=1,
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                allowed_paths=(),
                forbidden_operations=(),
                acceptance_criteria=(),
                goal="g",
                required_checks=("pytest",),
                approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
            )

    def test_empty_path_rejected_by_validator(self) -> None:
        wi = _make_work_item()
        object.__setattr__(wi, "allowed_paths", ())
        with pytest.raises(PolicyViolation, match="empty_path_scope"):
            validate_work_item(wi)


# ---------------------------------------------------------------------------
# Fail-closed: forbidden publication operations
# ---------------------------------------------------------------------------

class TestForbiddenPublicationOperations:
    @pytest.mark.parametrize(
        "op",
        sorted(FORBIDDEN_PUBLICATION_OPERATIONS),
    )
    def test_forbidden_op_rejected(self, op: str) -> None:
        with pytest.raises(PolicyViolation, match="forbidden_publication_operation"):
            validate_publication_operation(op)

    def test_all_required_forbidden_ops_are_listed(self) -> None:
        """The forbidden set must include all operations the Work Item forbids."""
        required = {
            "push_main",
            "mark_ready",
            "merge",
            "auto_merge",
            "release",
            "deployment",
            "secret_access",
            "force_push",
            "rebase",
            "squash",
            "tag_or_release",
        }
        assert required.issubset(FORBIDDEN_PUBLICATION_OPERATIONS)


# ---------------------------------------------------------------------------
# Fail-closed: retry limit
# ---------------------------------------------------------------------------

class TestRetryLimitFailClosed:
    def test_max_attempts_is_two(self) -> None:
        # At most one bounded retry; the third attempt is rejected.
        assert MAX_ATTEMPTS == 2

    def test_third_attempt_rejected_at_construction(self) -> None:
        with pytest.raises(ValueError, match="max_attempts_exceeded"):
            ExecutionBinding(work_item=_make_work_item(), attempt=3)

    def test_next_attempt_exhausted_raises(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=MAX_ATTEMPTS)
        with pytest.raises(ValueError, match="retry_limit_exceeded"):
            binding.next_attempt()


# ---------------------------------------------------------------------------
# Forbidden components are not importable from the adapter
# ---------------------------------------------------------------------------

class TestForbiddenComponentsAbsent:
    """Verify the adapter does not pull in forbidden components."""

    def test_no_temporal_import(self) -> None:
        assert importlib.util.find_spec("temporal") is None or "temporal" not in {
            m for m in sys.modules if "temporal" in m.lower()
        }

    def test_no_litellm_import(self) -> None:
        # LiteLLM may not be installed; verify we don't import it
        assert "litellm" not in sys.modules
        spec = importlib.util.find_spec("litellm")
        if spec is not None:
            # If installed, verify the adapter doesn't import it
            import reverse_agent.platform_v1  # noqa: F401
            assert "litellm" not in sys.modules

    def test_no_langfuse_import(self) -> None:
        assert "langfuse" not in sys.modules
        spec = importlib.util.find_spec("langfuse")
        if spec is not None:
            import reverse_agent.platform_v1  # noqa: F401
            assert "langfuse" not in sys.modules

    def test_adapter_does_not_import_forbidden_modules(self) -> None:
        # Fresh import of the adapter package
        if "reverse_agent.platform_v1" in sys.modules:
            del sys.modules["reverse_agent.platform_v1"]
        importlib.import_module("reverse_agent.platform_v1")
        forbidden = ["temporal", "litellm", "langfuse", "spec_kit"]
        for mod in forbidden:
            assert mod not in sys.modules, f"adapter must not import {mod}"


# ---------------------------------------------------------------------------
# Adapter surface is thin (no executor, loop, sandbox, database, frontend)
# ---------------------------------------------------------------------------

class TestAdapterSurfaceIsThin:
    """The adapter must not implement executor, loop, sandbox, database, frontend."""

    def test_no_executor_module(self) -> None:
        # reverse_agent.platform_v1 should not have an executor submodule
        spec = importlib.util.find_spec("reverse_agent.platform_v1.executor")
        assert spec is None

    def test_no_agent_loop_module(self) -> None:
        spec = importlib.util.find_spec("reverse_agent.platform_v1.agent_loop")
        assert spec is None

    def test_no_sandbox_module(self) -> None:
        spec = importlib.util.find_spec("reverse_agent.platform_v1.sandbox")
        assert spec is None

    def test_no_database_module(self) -> None:
        spec = importlib.util.find_spec("reverse_agent.platform_v1.database")
        assert spec is None

    def test_no_frontend_module(self) -> None:
        spec = importlib.util.find_spec("reverse_agent.platform_v1.frontend")
        assert spec is None

    def test_no_orchestrator_module(self) -> None:
        spec = importlib.util.find_spec("reverse_agent.platform_v1.orchestrator")
        assert spec is None

    def test_public_api_is_limited(self) -> None:
        import reverse_agent.platform_v1 as pkg
        public = {name for name in dir(pkg) if not name.startswith("_")}
        # Must export the core contracts
        assert "PlatformWorkItem" in public
        assert "ExecutionBinding" in public
        assert "ExecutionEvidence" in public
        assert "PlatformAcceptanceResult" in public
        # Must NOT export executor/loop/sandbox/db/frontend
        forbidden_exports = {"Executor", "AgentLoop", "Sandbox", "Database", "Frontend"}
        assert not (forbidden_exports & public)
