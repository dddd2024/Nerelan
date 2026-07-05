from reverse_agent.user_solve_task_lifecycle import (
    TASK_STATUSES,
    build_demo_task_payload,
    validate_task_payload,
    validate_task_transition,
)


def test_task_lifecycle_accepts_manual_path() -> None:
    transitions = [
        ("DRAFT", "READY"),
        ("READY", "MANUAL_DISPATCHED"),
        ("MANUAL_DISPATCHED", "MANUAL_RESULT_IMPORTED"),
        ("MANUAL_RESULT_IMPORTED", "FINAL_CHECKED"),
        ("FINAL_CHECKED", "AUDITED"),
        ("AUDITED", "ACCEPTED"),
    ]

    for source, target in transitions:
        assert validate_task_transition(source, target)["validation_status"] == "PASSED"
    assert "MANUAL_DISPATCHED" in TASK_STATUSES


def test_task_lifecycle_rejects_unsafe_jump() -> None:
    result = validate_task_transition("DRAFT", "ACCEPTED")

    assert result["validation_status"] == "FAILED"
    assert result["dispatch_enabled"] is False


def test_demo_task_payload_is_fixture_only() -> None:
    payload = build_demo_task_payload(
        task_id="demo_manual_mode_task",
        decision_id="decision_x",
        round_id="round_x",
        report_id="codex_report_x",
        status="READY",
    )
    result = validate_task_payload(payload)

    assert result["validation_status"] == "PASSED"
    assert payload["fixture_only"] is True
    assert payload["real_sample"] is False
    assert payload["manual_execution"]["dispatch_enabled"] is False
