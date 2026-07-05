import json

from reverse_agent.orchestrator_context import build_orchestrator_context_snapshot


def test_orchestrator_context_snapshot_is_bounded(tmp_path) -> None:
    state_dir = tmp_path / "project_state"
    (state_dir / "gates").mkdir(parents=True)
    decision = {"decision_id": "decision_x", "round_id": "round_x", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2"]}
    (state_dir / "decision_packet.md").write_text(f"```json decision_meta\n{json.dumps(decision)}\n```\n```json decision_contract\n{{}}\n```", encoding="utf-8")
    (state_dir / "gates" / "command_plan.json").write_text("{}", encoding="utf-8")

    snapshot = build_orchestrator_context_snapshot(state_dir=state_dir, profile="planner")

    assert snapshot["decision_id"] == "decision_x"
    assert snapshot["model_api_invocation"] is False
    assert snapshot["full_solve_reports_read"] is False
