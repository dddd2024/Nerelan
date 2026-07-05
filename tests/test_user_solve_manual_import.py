from reverse_agent.user_solve_manual_import import (
    build_demo_manual_result,
    validate_manual_result_payload,
)


def test_manual_import_validates_bounded_demo_result() -> None:
    payload = build_demo_manual_result(
        decision_id="decision_x",
        round_id="round_x",
        task_id="demo_task",
        job_id="job_demo_task",
    )

    result = validate_manual_result_payload(
        payload,
        decision_id="decision_x",
        round_id="round_x",
        allowed_commands=[],
    )

    assert result["validation_status"] == "PASSED"
    assert result["verified_evidence"] is False
    assert result["manual_claim_only"] is True


def test_manual_import_rejects_real_execution_claims() -> None:
    payload = build_demo_manual_result(
        decision_id="decision_x",
        round_id="round_x",
        task_id="demo_task",
        job_id="job_demo_task",
    )
    payload["claims"]["real_execution"] = True

    result = validate_manual_result_payload(
        payload,
        decision_id="decision_x",
        round_id="round_x",
        allowed_commands=[],
    )

    assert result["validation_status"] == "FAILED"
    assert any("real_execution" in error for error in result["errors"])
