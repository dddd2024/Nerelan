import json
from pathlib import Path

from reverse_agent.project_jobs import (
    JOB_STATUS_TRANSITIONS,
    JOB_STATUSES,
    validate_job_file,
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
