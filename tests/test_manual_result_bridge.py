from reverse_agent.manual_result_bridge import evidence_summary_from_import, preview_manual_result_import
from reverse_agent.user_solve_manual_import import build_demo_manual_result
from reverse_agent.user_solve_task_lifecycle import build_demo_task_payload


def test_manual_result_bridge_previews_without_writes() -> None:
    task = build_demo_task_payload(task_id="demo_task", decision_id="decision_x", round_id="round_x")
    result = build_demo_manual_result(decision_id="decision_x", round_id="round_x", task_id="demo_task", job_id="job_demo_task")

    preview = preview_manual_result_import(task_payload=task, result_payload=result, decision_id="decision_x", round_id="round_x")
    summary = evidence_summary_from_import(preview)

    assert preview["preview_status"] == "PASSED"
    assert preview["writes_performed"] is False
    assert summary["verified_evidence"] is False
