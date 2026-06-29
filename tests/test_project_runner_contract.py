import json
from pathlib import Path

from reverse_agent.project_jobs import build_planned_job_payload
from reverse_agent.project_runner_contract import (
    build_runner_contract_payload,
    validate_runner_contract_payload,
)


def _write_decision(state_dir: Path) -> dict:
    decision = {
        "schema_version": 1,
        "decision_id": "decision_runner_contract",
        "round_id": "round_runner_contract",
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(decision, indent=2)}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )
    return decision


def _command_plan() -> dict:
    return {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_runner_contract",
        "round_id": "round_runner_contract",
        "mainline": "engineering_branch",
        "commands": [
            {
                "index": 1,
                "kind": "job-orchestration",
                "phase": "gate",
                "command": "python -m reverse_agent.project_gate job-orchestration --state-dir project_state",
                "expected_exit_codes": [0],
                "required": True,
            },
            {
                "index": 2,
                "kind": "runner-contract",
                "phase": "gate",
                "command": "python -m reverse_agent.project_gate runner-contract --state-dir project_state",
                "expected_exit_codes": [0],
                "required": True,
            },
        ],
        "omitted_commands": [
            {
                "kind": "github-actions",
                "command": "gh workflow run state-gate.yml",
                "reason": "remote mutation forbidden",
            }
        ],
    }


def test_runner_contract_packages_command_plan_without_dispatch(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision = _write_decision(state_dir)
    job_payload = build_planned_job_payload(decision)

    payload = build_runner_contract_payload(
        state_dir=state_dir,
        job_payload=job_payload,
        command_plan_payload=_command_plan(),
        repo_root=tmp_path,
        job_artifact_path="project_state/jobs/job_runner_contract.json",
    )
    result = validate_runner_contract_payload(
        payload,
        command_plan_payload=_command_plan(),
        job_payload=job_payload,
    )

    assert result["validation_status"] == "PASSED"
    assert payload["dispatch_enabled"] is False
    assert payload["executable"] is False
    assert payload["external_invocations"]["github_actions"] is False
    assert payload["allowed_commands"][0]["kind"] == "job-orchestration"
    assert payload["forbidden_commands"][0]["command"] == "gh workflow run state-gate.yml"
    assert payload["policy"]["command_plan_is_authority"] is True


def test_runner_contract_rejects_commands_outside_command_plan(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision = _write_decision(state_dir)
    job_payload = build_planned_job_payload(decision)
    payload = build_runner_contract_payload(
        state_dir=state_dir,
        job_payload=job_payload,
        command_plan_payload=_command_plan(),
        repo_root=tmp_path,
    )
    payload["allowed_commands"].append(
        {
            "index": 99,
            "kind": "powershell",
            "phase": "status",
            "command": "Remove-Item project_state -Recurse",
            "expected_exit_codes": [0],
            "required": True,
        }
    )

    result = validate_runner_contract_payload(
        payload,
        command_plan_payload=_command_plan(),
        job_payload=job_payload,
    )

    assert result["validation_status"] == "FAILED"
    assert "allowed_commands include commands outside command-plan" in result["errors"]


def test_runner_contract_rejects_omitted_command_as_allowed(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision = _write_decision(state_dir)
    job_payload = build_planned_job_payload(decision)
    payload = build_runner_contract_payload(
        state_dir=state_dir,
        job_payload=job_payload,
        command_plan_payload=_command_plan(),
        repo_root=tmp_path,
    )
    payload["allowed_commands"].append(
        {
            "index": 3,
            "kind": "github-actions",
            "phase": "status",
            "command": "gh workflow run state-gate.yml",
            "expected_exit_codes": [0],
            "required": True,
        }
    )

    result = validate_runner_contract_payload(
        payload,
        command_plan_payload=_command_plan(),
        job_payload=job_payload,
    )

    assert result["validation_status"] == "FAILED"
    assert "allowed_commands include omitted command-plan commands" in result["errors"]


def test_runner_contract_rejects_executable_contract(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision = _write_decision(state_dir)
    job_payload = build_planned_job_payload(decision)
    payload = build_runner_contract_payload(
        state_dir=state_dir,
        job_payload=job_payload,
        command_plan_payload=_command_plan(),
        repo_root=tmp_path,
    )
    payload["executable"] = True
    payload["external_invocations"]["codex_cli"] = True

    result = validate_runner_contract_payload(
        payload,
        command_plan_payload=_command_plan(),
        job_payload=job_payload,
    )

    assert result["validation_status"] == "FAILED"
    assert "executable must be false" in result["errors"]
    assert any("external invocations must be false" in error for error in result["errors"])
