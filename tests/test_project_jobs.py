import json
from pathlib import Path

from reverse_agent.project_jobs import JOB_STATUSES, validate_job_file, validate_job_payload


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
