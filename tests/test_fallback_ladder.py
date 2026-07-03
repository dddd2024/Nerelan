from reverse_agent.fallback_ladder import (
    FallbackCapability,
    FallbackLadder,
    FallbackPolicy,
    FallbackStepName,
    PermissionRequirement,
)
from reverse_agent.user_solve_contract import contains_internal_reference


def test_default_ladder_covers_required_order_and_metadata() -> None:
    ladder = FallbackLadder.default()
    names = [step.name.value for step in ladder.steps]

    assert names == [
        "fast_strings",
        "ida_summary",
        "targeted_decompile",
        "constant_material_extract",
        "solver_attempt",
        "runtime_validation",
    ]
    assert all(step.timeout_seconds > 0 for step in ladder.steps)
    assert all(step.required_capability.value for step in ladder.steps)
    assert not ladder.to_dict()["executes_steps"]


def test_select_next_static_only_step_without_executing() -> None:
    decision = FallbackLadder.default().select_next(
        completed_steps=[FallbackStepName.FAST_STRINGS],
        missing_evidence=["targeted_decompile_missing", "project_state/artifact_index.json"],
    )

    user_payload = decision.to_user_dict()

    assert decision.selected_step is not None
    assert decision.selected_step.name == FallbackStepName.IDA_SUMMARY
    assert decision.executed is False
    assert user_payload["executed"] is False
    assert not contains_internal_reference(user_payload)


def test_local_dynamic_steps_remain_blocked_without_permission() -> None:
    decision = FallbackLadder.default().select_next(
        completed_steps=[
            "fast_strings",
            "ida_summary",
            "targeted_decompile",
        ],
        missing_evidence=["runtime_validation_missing"],
    )

    assert decision.selected_step is None
    blocked_names = {item["name"] for item in decision.blocked_steps}
    assert {"constant_material_extract", "solver_attempt", "runtime_validation"} <= blocked_names
    assert any("requires_local_execution" in item["reasons"] for item in decision.blocked_steps)


def test_explicit_permission_still_does_not_execute() -> None:
    decision = FallbackLadder.default().select_next(
        completed_steps=["fast_strings", "ida_summary", "targeted_decompile"],
        policy=FallbackPolicy(
            allowed_capabilities={FallbackCapability.MATERIAL_EXTRACTION},
            explicit_permissions={PermissionRequirement.EXPLICIT_PERMISSION},
            fast_mode=False,
        ),
    )

    assert decision.selected_step is None
    assert decision.executed is False
    assert any(item["name"] == "constant_material_extract" for item in decision.blocked_steps)
