import json
from pathlib import Path
from typing import Any

from reverse_agent.project_control_plane import ARTIFACT_PATH, build_control_plane_snapshot
from reverse_agent.project_state import write_pytest_result


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_decision(state_dir: Path, *, decision_id: str, round_id: str) -> None:
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )


def _write_report(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
) -> str:
    report_id = "codex_report_control_plane"
    payload = {
        "schema_version": 1,
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "status": status,
        "acceptance_recommendation": acceptance,
        "files_changed": [],
        "tests_ran": [],
        "generated_artifacts": [ARTIFACT_PATH],
    }
    (state_dir / "execution_report.md").write_text(
        f"""```json execution_report_summary
{json.dumps(payload, indent=2)}
```

# EXECUTION_REPORT
""",
        encoding="utf-8",
    )
    return report_id


def _make_state(tmp_path: Path, *, decision_id: str = "decision_control", round_id: str = "round_control") -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    report_id = _write_report(state_dir, decision_id=decision_id, round_id=round_id)
    write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": decision_id,
            "report_id": report_id,
            "round_id": round_id,
            "generated_at": "2026-06-29T00:00:00Z",
            "status": "PASSED",
            "tests_ran": [],
        },
        body="1 passed\n",
    )
    gates_dir = state_dir / "gates"
    for name, payload in {
        "command_plan.json": {
            "schema_version": 1,
            "plan_name": "command-plan",
            "plan_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "mainline": "engineering_branch",
            "recommended_next_action": "no_action_required",
            "commands": [],
            "warnings": [],
            "blocking_reasons": [],
        },
        "final_gate_result.json": {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "report_id": report_id,
        },
        "audit_inventory_result.json": {
            "schema_version": 1,
            "gate_name": "audit-inventory",
            "gate_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "inventory_validation_status": "PASSED",
            "audit_count": 1,
            "validated_paths": ["project_state/audits/audit.md"],
        },
        "jobs_inventory_result.json": {
            "schema_version": 1,
            "gate_name": "jobs-inventory",
            "gate_status": "PASSED",
            "decision_id": "decision_previous",
            "round_id": "round_previous",
            "inventory_validation_status": "PASSED",
            "job_count": 1,
            "validated_paths": ["project_state/jobs/job.json"],
            "dispatch_enabled": False,
            "dispatch_safety_status": "PASSED",
            "jobs": [{"status": "DRAFT"}],
        },
    }.items():
        _write_json(gates_dir / name, payload)
    return state_dir


def test_control_plane_snapshot_writes_current_read_only_status(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)

    result = build_control_plane_snapshot(state_dir=state_dir)

    artifact = json.loads((state_dir / "gates" / "control_plane_snapshot.json").read_text(encoding="utf-8"))
    assert result["gate_status"] == "PASSED"
    assert artifact["decision_id"] == "decision_control"
    assert artifact["round_id"] == "round_control"
    assert artifact["active_decision"]["consumed_by_matching_report"] is True
    assert artifact["runner_readiness"]["can_dispatch_next_decision"] is False
    assert artifact["authority_separation"]["snapshot_role"] == "read_only_status_output"
    assert artifact["ui_summary"]["headline"]


def test_control_plane_snapshot_treats_stale_jobs_inventory_as_historical(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False)

    jobs = result["inventory_status"]["jobs_inventory"]
    assert jobs["status"] == "historical_nonblocking"
    assert jobs["nonblocking"] is True
    assert "jobs inventory is historical_nonblocking" in result["ui_summary"]["warnings"]


def test_control_plane_snapshot_summarizes_job_and_runner_readiness(tmp_path: Path) -> None:
    state_dir = _make_state(
        tmp_path,
        decision_id="decision_job_runner",
        round_id="round_job_runner",
    )
    _write_json(
        state_dir / "gates" / "jobs_inventory_result.json",
        {
            "schema_version": 1,
            "gate_name": "jobs-inventory",
            "gate_status": "PASSED",
            "decision_id": "decision_job_runner",
            "round_id": "round_job_runner",
            "inventory_validation_status": "PASSED",
            "job_count": 1,
            "status_counts": {"DRAFT": 1, "READY": 0, "RUNNING": 0},
            "validated_paths": ["project_state/jobs/job_job_runner.json"],
            "dispatch_enabled": False,
            "dispatch_safety_status": "PASSED",
            "jobs": [{"job_id": "job_job_runner", "status": "DRAFT"}],
        },
    )
    _write_json(
        state_dir / "gates" / "job_orchestration_result.json",
        {
            "schema_version": 1,
            "gate_name": "job-orchestration",
            "gate_status": "PASSED",
            "decision_id": "decision_job_runner",
            "round_id": "round_job_runner",
            "job_id": "job_job_runner",
            "job_status": "DRAFT",
            "job_artifact_path": "project_state/jobs/job_job_runner.json",
            "dispatch_enabled": False,
            "dispatch_safety_status": "PASSED",
        },
    )
    _write_json(
        state_dir / "gates" / "runner_contract_result.json",
        {
            "schema_version": 1,
            "gate_name": "runner-contract",
            "gate_status": "PASSED",
            "decision_id": "decision_job_runner",
            "round_id": "round_job_runner",
            "contract_id": "runner_contract_job_runner",
            "contract_validation_status": "PASSED",
            "dispatch_enabled": False,
            "executable": False,
            "allowed_command_count": 2,
            "forbidden_command_count": 1,
        },
    )

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False)

    assert result["inventory_status"]["job_orchestration"]["status"] == "PASSED"
    assert result["inventory_status"]["runner_contract"]["contract_validation_status"] == "PASSED"
    assert result["job_queue_status"]["current_job_id"] == "job_job_runner"
    assert result["job_queue_status"]["current_job_status"] == "DRAFT"
    assert result["runner_readiness"]["job_orchestration_ready"] is True
    assert result["runner_readiness"]["runner_contract_ready"] is True
    assert result["runner_readiness"]["can_dispatch_next_decision"] is False


def test_control_plane_snapshot_records_hard_identity_mismatch(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "PASSED",
            "decision_id": "decision_previous",
            "round_id": "round_previous",
            "report_id": "codex_report_previous",
        },
    )

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False)

    assert "final_gate decision_id mismatch" in result["ui_summary"]["blocking_reasons"]
    assert "final_gate round_id mismatch" in result["ui_summary"]["blocking_reasons"]


def test_control_plane_snapshot_missing_command_plan_fails_build(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)
    (state_dir / "gates" / "command_plan.json").unlink()

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False)

    assert result["gate_status"] == "FAILED"
    assert "command_plan artifact missing" in result["ui_summary"]["blocking_reasons"]


def test_control_plane_snapshot_final_state_requires_closeout_completion(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False, final_state=True)

    assert result["gate_status"] == "FAILED"
    assert result["snapshot_mode"] == "final_state"
    assert result["execution_status"]["final_state_complete"] is False
    assert "final-state closeout status is not PASSED" in result["ui_summary"]["blocking_reasons"]


def test_control_plane_snapshot_final_state_passes_when_closeout_is_closed(tmp_path: Path) -> None:
    state_dir = _make_state(
        tmp_path,
        decision_id="decision_control_plane",
        round_id="round_control_plane",
    )
    _write_json(
        state_dir / "gates" / "run_closeout_result.json",
        {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_control_plane",
            "round_id": "round_control_plane",
            "close_round_result": {"close_status": "CLOSED"},
        },
    )

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False, final_state=True)

    assert result["gate_status"] == "PASSED"
    assert result["snapshot_mode"] == "final_state"
    assert result["execution_status"]["final_state_complete"] is True


def test_control_plane_snapshot_final_state_uses_closeout_when_tail_only_pending(
    tmp_path: Path,
) -> None:
    state_dir = _make_state(
        tmp_path,
        decision_id="decision_control_plane",
        round_id="round_control_plane",
    )
    _write_report(
        state_dir,
        decision_id="decision_control_plane",
        round_id="round_control_plane",
        status="FAILED",
        acceptance="REWORK_REQUIRED",
    )
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "FAILED",
            "decision_id": "decision_control_plane",
            "round_id": "round_control_plane",
            "report_id": "codex_report_control_plane",
            "checks": [
                {"name": "control_plane_snapshot_artifact", "status": "FAIL"},
                {"name": "execute_decision_contract", "status": "FAIL"},
                {"name": "execution_log_required_commands_recorded", "status": "FAIL"},
            ],
            "blocking_reasons": [
                "control_plane_snapshot_artifact: final-state snapshot pending",
                "execute_decision_contract: execute-decision result pending",
                "execution_log_required_commands_recorded: final-state command pending",
            ],
        },
    )
    _write_json(
        state_dir / "gates" / "run_closeout_result.json",
        {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_control_plane",
            "round_id": "round_control_plane",
            "close_round_result": {
                "close_status": "CLOSED",
                "status_summary": {
                    "report_status": "SUCCESS",
                    "report_acceptance_recommendation": "ACCEPTED",
                },
            },
        },
    )

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False, final_state=True)

    assert result["gate_status"] == "PASSED"
    assert result["execution_status"]["final_state_complete"] is True
    assert result["execution_status"]["report_status"] == "SUCCESS"
    assert result["execution_status"]["acceptance_recommendation"] == "ACCEPTED"
    assert result["execution_status"]["final_gate_status"] == "PASSED"
    assert result["ui_summary"]["blocking_reasons"] == []


def test_control_plane_snapshot_final_state_rejects_non_tail_final_gate_failure(
    tmp_path: Path,
) -> None:
    state_dir = _make_state(tmp_path)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "FAILED",
            "decision_id": "decision_control",
            "round_id": "round_control",
            "report_id": "codex_report_control_plane",
            "checks": [{"name": "pytest_result_match", "status": "FAIL"}],
        },
    )
    _write_json(
        state_dir / "gates" / "run_closeout_result.json",
        {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_control",
            "round_id": "round_control",
            "close_round_result": {
                "close_status": "CLOSED",
                "status_summary": {
                    "report_status": "SUCCESS",
                    "report_acceptance_recommendation": "ACCEPTED",
                },
            },
        },
    )

    result = build_control_plane_snapshot(state_dir=state_dir, write_result=False, final_state=True)

    assert result["gate_status"] == "FAILED"
    assert result["execution_status"]["final_state_complete"] is False
    assert "final-state final_gate status is not PASSED" in result["ui_summary"]["blocking_reasons"]
