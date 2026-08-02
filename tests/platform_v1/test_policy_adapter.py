"""Tests for the Platform V1 policy adapter.

Covers:
- R3+ risk tier rejection (fail-closed)
- broad path scope rejection (fail-closed)
- empty path scope rejection (fail-closed)
- forbidden publication operation rejection
- changed-path scope validation
- task prompt generation (no credential injection)
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
    validate_binding,
    validate_changed_paths,
    validate_publication_operation,
    validate_work_item,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"


def _make_work_item(**overrides) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ("reverse_agent/platform_v1/**", "tests/platform_v1/**"),
        "forbidden_operations": ("push_main", "merge"),
        "acceptance_criteria": ("pytest passes",),
        "risk_tier": "R2",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


# ---------------------------------------------------------------------------
# validate_work_item
# ---------------------------------------------------------------------------

class TestValidateWorkItem:
    def test_valid_R2_work_item_passes(self) -> None:
        # Should not raise
        validate_work_item(_make_work_item(risk_tier="R2"))

    def test_valid_R0_work_item_passes(self) -> None:
        validate_work_item(_make_work_item(risk_tier="R0"))

    def test_valid_R1_work_item_passes(self) -> None:
        validate_work_item(_make_work_item(risk_tier="R1"))

    @pytest.mark.parametrize("tier", ["R3", "R4", "R5"])
    def test_R3_or_higher_fail_closed(self, tier: str) -> None:
        # PlatformWorkItem.__post_init__ rejects these too, but we construct
        # via __new__ to test validate_work_item independently.
        wi = _make_work_item()
        object.__setattr__(wi, "risk_tier", tier)
        with pytest.raises(PolicyViolation, match="risk_tier_exceeds_R2"):
            validate_work_item(wi)

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
        wi = PlatformWorkItem(
            source_issue_number=1,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("a.py",),
            forbidden_operations=("push_main", "merge", "mark_ready"),
            acceptance_criteria=(),
        )
        validate_work_item(wi)


# ---------------------------------------------------------------------------
# validate_binding
# ---------------------------------------------------------------------------

class TestValidateBinding:
    def test_valid_binding_passes(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
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
