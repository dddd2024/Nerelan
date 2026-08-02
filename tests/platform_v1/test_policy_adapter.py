"""Tests for the Platform V1 policy adapter.

Covers:
- R0/R1 pass; R2/R3 blocked_approval (fail-closed)
- broad path scope rejection (fail-closed)
- empty path scope rejection (fail-closed)
- forbidden publication operation rejection
- changed-path scope validation
- task prompt generation (no credential injection)
- is_blocked_approval_violation helper
"""

from __future__ import annotations

import pytest

from reverse_agent.platform_v1.contracts import (
    FORBIDDEN_PUBLICATION_OPERATIONS,
    ExecutionBinding,
    PlatformWorkItem,
)
from reverse_agent.platform_v1.policy_adapter import (
    PolicyViolation,
    generate_task_prompt,
    is_blocked_approval_violation,
    validate_binding,
    validate_changed_paths,
    validate_publication_operation,
    validate_work_item,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_ISSUE_BODY_DIGEST = "a" * 64  # F25: SHA-256, 64 hex chars


def _make_work_item(**overrides) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ("reverse_agent/platform_v1/**", "tests/platform_v1/**"),
        "forbidden_operations": ("push_main", "merge"),
        "acceptance_criteria": ("pytest passes",),
        "goal": "test goal",
        "required_checks": ("pytest",),
        "approved_issue_body_digest": VALID_ISSUE_BODY_DIGEST,
        "risk_tier": "R0",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


# ---------------------------------------------------------------------------
# validate_work_item
# ---------------------------------------------------------------------------

class TestValidateWorkItem:
    def test_valid_R0_work_item_passes(self) -> None:
        # Should not raise
        validate_work_item(_make_work_item(risk_tier="R0"))

    def test_valid_R1_work_item_passes(self) -> None:
        validate_work_item(_make_work_item(risk_tier="R1"))

    def test_R2_raises_blocked_approval(self) -> None:
        # R2 is valid at construction but blocked by policy.
        with pytest.raises(PolicyViolation, match="blocked_approval"):
            validate_work_item(_make_work_item(risk_tier="R2"))

    def test_R3_raises_blocked_approval(self) -> None:
        # R3 is valid at construction but blocked by policy.
        with pytest.raises(PolicyViolation, match="blocked_approval"):
            validate_work_item(_make_work_item(risk_tier="R3"))

    @pytest.mark.parametrize("tier", ["R3", "R4", "R5"])
    def test_R3_or_higher_fail_closed(self, tier: str) -> None:
        # PlatformWorkItem.__post_init__ rejects R4+ at construction, so we
        # construct with a valid tier then mutate via object.__setattr__ to
        # test validate_work_item independently.
        wi = _make_work_item()
        object.__setattr__(wi, "risk_tier", tier)
        with pytest.raises(PolicyViolation, match="blocked_approval"):
            validate_work_item(wi)

    def test_blocked_approval_violation_carries_tier_as_detail(self) -> None:
        wi = _make_work_item(risk_tier="R2")
        with pytest.raises(PolicyViolation) as exc_info:
            validate_work_item(wi)
        assert exc_info.value.code == "blocked_approval"
        assert exc_info.value.detail == "R2"

    def test_empty_path_scope_fail_closed(self) -> None:
        wi = _make_work_item()
        object.__setattr__(wi, "allowed_paths", ())
        with pytest.raises(PolicyViolation, match="empty_path_scope"):
            validate_work_item(wi)

    @pytest.mark.parametrize("broad", ["**", "*", ".", "./", "/", "./**", "*.*"])
    def test_broad_path_fail_closed(self, broad: str) -> None:
        wi = _make_work_item()
        object.__setattr__(wi, "allowed_paths", (broad,))
        with pytest.raises(PolicyViolation, match="broad_path_rejected"):
            validate_work_item(wi)

    def test_forbidden_operations_listed_in_deny_list_passes(self) -> None:
        # forbidden_operations is a deny-list: listing push_main/merge there
        # is correct and expected. validate_work_item should NOT reject.
        # R0 so the tier check passes and we isolate the deny-list behavior.
        wi = PlatformWorkItem(
            source_issue_number=1,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("a.py",),
            forbidden_operations=("push_main", "merge", "mark_ready"),
            acceptance_criteria=(),
            goal="g",
            required_checks=("pytest",),
            approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
            risk_tier="R0",
        )
        validate_work_item(wi)


# ---------------------------------------------------------------------------
# is_blocked_approval_violation
# ---------------------------------------------------------------------------

class TestIsBlockedApprovalViolation:
    def test_returns_true_for_blocked_approval(self) -> None:
        exc = PolicyViolation("blocked_approval", "R2")
        assert is_blocked_approval_violation(exc) is True

    def test_returns_false_for_other_violations(self) -> None:
        exc = PolicyViolation("empty_path_scope")
        assert is_blocked_approval_violation(exc) is False

    def test_returns_false_for_broad_path_rejected(self) -> None:
        exc = PolicyViolation("broad_path_rejected", "**")
        assert is_blocked_approval_violation(exc) is False


# ---------------------------------------------------------------------------
# validate_binding
# ---------------------------------------------------------------------------

class TestValidateBinding:
    def test_valid_binding_passes(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
        validate_binding(binding)

    def test_R2_binding_raises_blocked_approval(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"), attempt=1)
        with pytest.raises(PolicyViolation, match="blocked_approval"):
            validate_binding(binding)

    def test_attempt_zero_rejected(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
        object.__setattr__(binding, "attempt", 0)
        with pytest.raises(PolicyViolation, match="invalid_attempt"):
            validate_binding(binding)


# ---------------------------------------------------------------------------
# validate_changed_paths
# ---------------------------------------------------------------------------

class TestValidateChangedPaths:
    def test_in_scope_paths_return_empty(self) -> None:
        allowed = ("reverse_agent/platform_v1/**", "tests/platform_v1/**")
        changed = (
            "reverse_agent/platform_v1/__init__.py",
            "reverse_agent/platform_v1/cli.py",
            "tests/platform_v1/test_contracts.py",
        )
        outside = validate_changed_paths(changed, allowed)
        assert outside == ()

    def test_out_of_scope_paths_returned(self) -> None:
        allowed = ("reverse_agent/platform_v1/**",)
        changed = (
            "reverse_agent/platform_v1/cli.py",
            "reverse_agent/other_module/foo.py",
            "pyproject.toml",
        )
        outside = validate_changed_paths(changed, allowed)
        assert "reverse_agent/other_module/foo.py" in outside
        assert "pyproject.toml" in outside
        assert "reverse_agent/platform_v1/cli.py" not in outside

    def test_empty_changed_paths_return_empty(self) -> None:
        outside = validate_changed_paths((), ("a.py",))
        assert outside == ()

    def test_exact_path_match(self) -> None:
        allowed = ("pyproject.toml",)
        changed = ("pyproject.toml",)
        assert validate_changed_paths(changed, allowed) == ()

    def test_path_normalization_in_match(self) -> None:
        allowed = ("reverse_agent/platform_v1/**",)
        changed = ("./reverse_agent/platform_v1/cli.py",)
        assert validate_changed_paths(changed, allowed) == ()


# ---------------------------------------------------------------------------
# validate_publication_operation
# ---------------------------------------------------------------------------

class TestValidatePublicationOperation:
    @pytest.mark.parametrize("op", sorted(FORBIDDEN_PUBLICATION_OPERATIONS))
    def test_forbidden_operations_rejected(self, op: str) -> None:
        with pytest.raises(PolicyViolation, match="forbidden_publication_operation"):
            validate_publication_operation(op)

    def test_safe_operation_passes(self) -> None:
        # Should not raise
        validate_publication_operation("push_named_branch")
        validate_publication_operation("create_or_update_draft_pr")
        validate_publication_operation("run_checks")


# ---------------------------------------------------------------------------
# generate_task_prompt
# ---------------------------------------------------------------------------

class TestGenerateTaskPrompt:
    def test_prompt_contains_execution_id(self) -> None:
        wi = _make_work_item()
        prompt = generate_task_prompt(wi)
        assert wi.execution_id in prompt

    def test_prompt_contains_branch_name(self) -> None:
        wi = _make_work_item()
        prompt = generate_task_prompt(wi)
        assert wi.branch_name in prompt

    def test_prompt_contains_allowed_paths(self) -> None:
        wi = _make_work_item(allowed_paths=("reverse_agent/platform_v1/**",))
        prompt = generate_task_prompt(wi)
        assert "reverse_agent/platform_v1/**" in prompt

    def test_prompt_contains_forbidden_operations(self) -> None:
        wi = _make_work_item(forbidden_operations=("push_main", "merge"))
        prompt = generate_task_prompt(wi)
        assert "push_main" in prompt
        assert "merge" in prompt

    def test_prompt_contains_goal(self) -> None:
        wi = _make_work_item(goal="Ship the platform v1 slice")
        prompt = generate_task_prompt(wi)
        assert "Ship the platform v1 slice" in prompt

    def test_prompt_contains_required_checks(self) -> None:
        wi = _make_work_item(required_checks=("pytest", "git diff --check"))
        prompt = generate_task_prompt(wi)
        assert "pytest" in prompt
        assert "git diff --check" in prompt

    def test_prompt_does_not_inject_credential_values(self) -> None:
        wi = _make_work_item()
        prompt = generate_task_prompt(wi)
        # The prompt may instruct the agent not to access secrets, but it
        # must never contain actual credential values or env-var names.
        forbidden_tokens = [
            "GITHUB_TOKEN=",
            "CODEX_API_KEY=",
            "OPENAI_API_KEY=",
            "ANTHROPIC_API_KEY=",
            "LLM_API_KEY=",
            "ghp_",
            "sk-",
            "Bearer ",
            "token=",
            "api_key=",
            "password=",
            "secret=",
        ]
        for token in forbidden_tokens:
            assert token not in prompt, f"prompt must not contain credential pattern {token!r}"

    def test_prompt_states_completion_claim_does_not_override(self) -> None:
        wi = _make_work_item()
        prompt = generate_task_prompt(wi)
        assert "completion claim does not override" in prompt.lower()
