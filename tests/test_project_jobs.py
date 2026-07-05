import json
from pathlib import Path

from reverse_agent.project_jobs import (
    JOB_STATUS_TRANSITIONS,
    JOB_STATUSES,
    build_demo_manual_job_payload,
    build_planned_job_payload,
    planned_job_artifact_path,
    planned_job_id_for_round,
    validate_job_file,
    validate_jobs_dir,
    validate_job_payload,
    validate_job_transition,
)


def _valid_job() -> dict:
    return {
        "schema_version": 1,
        "job_id": "job_preflight_foundation",
        "round_id": "round_preflight_foundation",
        "decision_id": "decision_preflight_foundation",
        "mainline": "engineering_branch",
        "status": "READY",
        "runner": {
            "kind": "codex",
            "dispatch_enabled": False,
        },
        "required_inputs": [
            "project_state/decision_packet.md",
            ".github/workflows/decision-preflight.yml",
        ],
        "required_outputs": [
            "project_state/gates/preflight_result.json",
            "project_state/gates/command_plan.json",
        ],
        "permissions": {
            "allow_remote_mutation": False,
            "allow_llm_calls": False,
            "allow_agent_dispatch": False,
            "allow_reverse_solving": False,
        },
        "budgets": {
            "max_runtime_seconds": 1500,
            "max_commands": 8,
        },
    }


def test_validate_job_payload_accepts_non_dispatching_contract() -> None:
    result = validate_job_payload(_valid_job())

    assert result["validation_status"] == "PASSED"
    assert result["dispatch_enabled"] is False
    assert result["errors"] == []


def test_build_planned_job_payload_is_deterministic_non_dispatching() -> None:
    decision = {
        "decision_id": "decision_20260629_job_orchestration_foundation_v1",
        "round_id": "round_20260629_job_orchestration_foundation_v1",
        "mainline": "engineering_branch",
    }

    payload = build_planned_job_payload(decision)
    result = validate_job_payload(payload)

    assert payload["job_id"] == "job_20260629_job_orchestration_foundation_v1"
    assert planned_job_id_for_round(decision["round_id"]) == payload["job_id"]
    assert planned_job_artifact_path(payload["job_id"]) in payload["required_outputs"]
    assert payload["status"] == "DRAFT"
    assert payload["runner"]["dispatch_enabled"] is False
    assert payload["permissions"]["allow_remote_mutation"] is False
    assert payload["permissions"]["allow_llm_calls"] is False
    assert payload["permissions"]["allow_agent_dispatch"] is False
    assert payload["permissions"]["allow_reverse_solving"] is False
    assert payload["budgets"]["max_runtime_seconds"] == 0
    assert payload["budgets"]["max_commands"] == 0
    assert result["validation_status"] == "PASSED"


def test_validate_job_payload_rejects_missing_required_fields() -> None:
    payload = _valid_job()
    del payload["decision_id"]

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert any("missing required fields" in error for error in result["errors"])


def test_validate_job_payload_rejects_unknown_status() -> None:
    payload = _valid_job()
    payload["status"] = "LAUNCHED"

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert any("status must be one of" in error for error in result["errors"])
    assert "ACCEPTED_WITH_LIMITATIONS" in JOB_STATUSES
    assert "MANUAL_DISPATCHED" in JOB_STATUSES


def test_validate_job_payload_rejects_dispatch_or_mutation_permissions() -> None:
    payload = _valid_job()
    payload["runner"]["dispatch_enabled"] = True
    payload["permissions"]["allow_remote_mutation"] = True
    payload["permissions"]["allow_agent_dispatch"] = True

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert "runner.dispatch_enabled must be false" in result["errors"]
    assert any("allow_agent_dispatch" in error for error in result["errors"])
    assert any("allow_remote_mutation" in error for error in result["errors"])


def test_validate_job_file_reads_json_contract(tmp_path: Path) -> None:
    job_path = tmp_path / "project_state" / "jobs" / "example.json"
    job_path.parent.mkdir(parents=True)
    job_path.write_text(json.dumps(_valid_job()), encoding="utf-8")

    result = validate_job_file(job_path)

    assert result["validation_status"] == "PASSED"
    assert result["job_id"] == "job_preflight_foundation"


def test_validate_job_transition_accepts_happy_path_state_machine() -> None:
    transitions = [
        ("DRAFT", "READY"),
        ("READY", "MANUAL_DISPATCHED"),
        ("MANUAL_DISPATCHED", "MANUAL_RESULT_IMPORTED"),
        ("MANUAL_RESULT_IMPORTED", "FINAL_CHECKED"),
        ("READY", "RUNNING"),
        ("RUNNING", "DONE"),
        ("DONE", "FINAL_CHECKED"),
        ("FINAL_CHECKED", "AUDITED"),
        ("AUDITED", "ACCEPTED"),
        ("AUDITED", "ACCEPTED_WITH_LIMITATIONS"),
        ("AUDITED", "REWORK_REQUIRED"),
        ("AUDITED", "BLOCKED"),
    ]

    for from_status, to_status in transitions:
        result = validate_job_transition(from_status, to_status)
        assert result["validation_status"] == "PASSED", result


def test_validate_job_transition_rejects_unsafe_transitions() -> None:
    for from_status, to_status in [
        ("DRAFT", "RUNNING"),
        ("DONE", "RUNNING"),
        ("ACCEPTED", "RUNNING"),
        ("ACCEPTED", "REWORK_REQUIRED"),
        ("BLOCKED", "RUNNING"),
    ]:
        result = validate_job_transition(from_status, to_status)
        assert result["validation_status"] == "FAILED"
        assert any("not allowed" in error for error in result["errors"])


def test_validate_job_payload_accepts_running_contract_with_lock_and_lease() -> None:
    payload = _valid_job()
    payload["status"] = "RUNNING"
    payload["transition"] = {"from_status": "READY", "to_status": "RUNNING"}
    payload["lock"] = {
        "lock_id": "lock_job_preflight_foundation",
        "owner": "codex",
        "created_at": "2026-06-28T09:00:00Z",
    }
    payload["lease"] = {
        "lease_id": "lease_job_preflight_foundation",
        "owner": "codex",
        "acquired_at": "2026-06-28T09:00:00Z",
        "heartbeat_at": "2026-06-28T09:05:00Z",
        "expires_at": "2026-06-28T10:00:00Z",
    }

    result = validate_job_payload(payload)

    assert result["validation_status"] == "PASSED"
    assert result["transition"]["validation_status"] == "PASSED"
    assert result["lock"]["lock_id"] == "lock_job_preflight_foundation"
    assert result["lease"]["lease_id"] == "lease_job_preflight_foundation"


def test_validate_job_payload_rejects_invalid_transition_metadata() -> None:
    payload = _valid_job()
    payload["status"] = "RUNNING"
    payload["transition"] = {"from_status": "DRAFT", "to_status": "RUNNING"}

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert any("transition DRAFT->RUNNING is not allowed" in error for error in result["errors"])


def test_validate_job_payload_rejects_transition_target_drift() -> None:
    payload = _valid_job()
    payload["status"] = "DONE"
    payload["transition"] = {"from_status": "READY", "to_status": "RUNNING"}

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert "transition.to_status must match job status" in result["errors"]


def test_validate_job_payload_rejects_bad_lock_and_lease_metadata() -> None:
    payload = _valid_job()
    payload["status"] = "RUNNING"
    payload["transition"] = {"from_status": "READY", "to_status": "RUNNING"}
    payload["lock"] = {"lock_id": "", "owner": ""}
    payload["lease"] = {
        "lease_id": "lease_bad",
        "owner": "codex",
        "acquired_at": "2026-06-28T10:00:00Z",
        "expires_at": "2026-06-28T09:00:00Z",
    }

    result = validate_job_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert "lock.lock_id must be a non-empty string" in result["errors"]
    assert "lock.owner must be a non-empty string" in result["errors"]
    assert "lease.expires_at must be later than lease.acquired_at" in result["errors"]


def test_validate_job_payload_keeps_minimal_contract_backward_compatible() -> None:
    payload = _valid_job()

    result = validate_job_payload(payload)

    assert result["validation_status"] == "PASSED"
    assert result["transition"] is None
    assert result["lock"] is None
    assert result["lease"] is None
    assert "READY" in JOB_STATUS_TRANSITIONS["DRAFT"]


def test_validate_job_file_accepts_safe_current_example(tmp_path: Path) -> None:
    payload = _valid_job()
    payload.update({
        "job_id": "job_20260628_clean_baseline_and_job_state_machine_v1",
        "round_id": "round_20260628_clean_baseline_and_job_state_machine_v1",
        "decision_id": "decision_20260628_clean_baseline_and_job_state_machine_v1",
        "status": "READY",
        "required_outputs": [
            "project_state/gates/final_gate_result.json",
            "project_state/gates/run_closeout_result.json",
        ],
    })
    job_path = tmp_path / "project_state" / "jobs" / "job_20260628_clean_baseline_and_job_state_machine_v1.json"
    job_path.parent.mkdir(parents=True)
    job_path.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_job_file(job_path)

    assert result["validation_status"] == "PASSED"
    assert result["dispatch_enabled"] is False


def test_validate_jobs_dir_accepts_missing_directory(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()

    result = validate_jobs_dir(state_dir)

    assert result["validation_status"] == "PASSED"
    assert result["job_count"] == 0
    assert result["validated_paths"] == []
    assert result["dispatch_enabled"] is False
    assert result["status_counts"]["DRAFT"] == 0


def test_validate_jobs_dir_reports_invalid_json_without_dispatch(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "project_state" / "jobs"
    jobs_dir.mkdir(parents=True)
    (jobs_dir / "bad.json").write_text("{not json", encoding="utf-8")

    result = validate_jobs_dir(tmp_path / "project_state")

    assert result["validation_status"] == "FAILED"
    assert result["job_count"] == 0
    assert result["validated_paths"] == []
    assert result["dispatch_enabled"] is False
    assert any("bad.json" in error for error in result["errors"])


def test_validate_jobs_dir_reports_invalid_payload_without_dispatch(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "project_state" / "jobs"
    jobs_dir.mkdir(parents=True)
    invalid_payload = _valid_job()
    invalid_payload["runner"]["dispatch_enabled"] = True
    (jobs_dir / "unsafe.json").write_text(json.dumps(invalid_payload), encoding="utf-8")

    result = validate_jobs_dir(tmp_path / "project_state")

    assert result["validation_status"] == "FAILED"
    assert result["job_count"] == 1
    assert result["validated_paths"] == []
    assert result["dispatch_enabled"] is False
    assert any("runner.dispatch_enabled must be false" in error for error in result["errors"])


def test_validate_jobs_dir_rejects_duplicate_job_ids(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "project_state" / "jobs"
    jobs_dir.mkdir(parents=True)
    first = _valid_job()
    second = _valid_job()
    second["round_id"] = "round_second"
    second["decision_id"] = "decision_second"
    (jobs_dir / "first.json").write_text(json.dumps(first), encoding="utf-8")
    (jobs_dir / "second.json").write_text(json.dumps(second), encoding="utf-8")

    result = validate_jobs_dir(tmp_path / "project_state")

    assert result["validation_status"] == "FAILED"
    assert result["job_count"] == 2
    assert len(result["validated_paths"]) == 2
    assert any("duplicate job_id 'job_preflight_foundation'" in error for error in result["errors"])


def test_validate_jobs_dir_returns_status_counts_and_validated_paths(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "project_state" / "jobs"
    jobs_dir.mkdir(parents=True)
    draft = _valid_job()
    draft.update({"job_id": "job_draft", "status": "DRAFT"})
    ready = _valid_job()
    ready.update({"job_id": "job_ready", "status": "READY"})
    blocked = _valid_job()
    blocked.update({"job_id": "job_blocked", "status": "BLOCKED"})
    for payload in (draft, ready, blocked):
        (jobs_dir / f"{payload['job_id']}.json").write_text(json.dumps(payload), encoding="utf-8")

    result = validate_jobs_dir(tmp_path / "project_state")

    assert result["validation_status"] == "PASSED"
    assert result["job_count"] == 3
    assert len(result["validated_paths"]) == 3
    assert result["status_counts"]["DRAFT"] == 1
    assert result["status_counts"]["READY"] == 1
    assert result["status_counts"]["BLOCKED"] == 1


def test_validate_jobs_dir_accepts_current_draft_job_contract() -> None:
    result = validate_jobs_dir(Path("project_state"))

    assert result["validation_status"] == "PASSED"
    current_job = next(
        job
        for job in result["jobs"]
        if job["job_id"] == "job_20260628_clean_baseline_job_inventory_v1"
    )
    assert current_job["status"] == "DRAFT"
    assert current_job["round_id"] == "round_20260628_clean_baseline_job_inventory_v1"
    assert current_job["decision_id"] == "decision_20260628_clean_baseline_job_inventory_v1"


def test_build_demo_manual_job_payload_is_non_dispatching() -> None:
    payload = build_demo_manual_job_payload(
        {
            "decision_id": "decision_manual",
            "round_id": "round_manual",
            "mainline": "engineering_branch",
        },
        task_id="demo_manual_mode_task",
    )
    result = validate_job_payload(payload)

    assert payload["job_id"] == "job_demo_manual"
    assert payload["runner"]["kind"] == "manual"
    assert payload["runner"]["dispatch_enabled"] is False
    assert payload["manual_mode"]["handoff_export_only"] is True
    assert result["validation_status"] == "PASSED"
