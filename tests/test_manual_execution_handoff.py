from reverse_agent.manual_execution_handoff import build_manual_execution_handoff


def test_manual_execution_handoff_preserves_command_plan_authority() -> None:
    handoff = build_manual_execution_handoff(
        decision={"decision_id": "decision_x", "round_id": "round_x", "mainline": "engineering_branch"},
        command_plan={"commands": [{"index": 1, "kind": "pytest", "command": "python -m pytest", "expected_exit_codes": [0]}], "omitted_commands": [{"kind": "github", "command": "gh workflow run"}]},
        task_id="demo_task",
        job_id="job_demo_task",
    )

    assert handoff["command_plan_authority"] == "project_state/gates/command_plan.json"
    assert handoff["runner_dispatch_enabled"] is False
    assert handoff["omitted_commands"][0]["command"] == "gh workflow run"
