import json
from pathlib import Path

from reverse_agent.project_agent_runner import (
    ARTIFACT_PATH,
    build_agent_runner_dry_run,
)
from reverse_agent.project_jobs import build_planned_job_payload, planned_job_artifact_path
from reverse_agent.project_runner_contract import build_runner_contract_payload


def _write_decision(state_dir: Path) -> dict:
    decision = {
        "schema_version": 1,
        "decision_id": "decision_agent_runner",
        "round_id": "round_agent_runner",
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
        "decision_id": "decision_agent_runner",
        "round_id": "round_agent_runner",
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
                "kind": "agent-runner-dry-run",
                "phase": "gate",
                "command": "python -m reverse_agent.project_gate agent-runner-dry-run --state-dir project_state",
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


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_state(tmp_path: Path) -> Path:
    state_dir = tmp_path / "project_state"
    decision = _write_decision(state_dir)
    job_payload = build_planned_job_payload(decision)
    job_path = tmp_path / planned_job_artifact_path(job_payload["job_id"])
    _write_json(job_path, job_payload)
    _write_json(state_dir / "gates" / "command_plan.json", _command_plan())
    contract = build_runner_contract_payload(
        state_dir=state_dir,
        repo_root=tmp_path,
        job_payload=job_payload,
        command_plan_payload=_command_plan(),
        job_artifact_path=planned_job_artifact_path(job_payload["job_id"]),
    )
    contract.update({
        "gate_name": "runner-contract",
        "gate_status": "PASSED",
        "contract_validation_status": "PASSED",
    })
    _write_json(state_dir / "gates" / "runner_contract_result.json", contract)
    return state_dir


def test_agent_runner_dry_run_consumes_artifacts_without_execution(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)

    result = build_agent_runner_dry_run(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["dry_run_status"] == "PASSED"
    assert result["non_execution_proof"]["commands_executed"] is False
    assert result["non_execution_proof"]["subprocess_spawned"] is False
    assert result["non_execution_proof"]["external_runner_invoked"] is False
    assert result["dispatch_policy"]["local_dry_run_readiness"] is True
    assert result["dispatch_policy"]["real_dispatch_readiness"] is False
    assert result["execution_preview"]["planned_command_count"] == 2
    assert result["execution_preview"]["omitted_command_count"] == 1
    assert result["lifecycle_preview"]["local_dry_run_state"] == "DRY_RUN_PLANNED"
    assert (state_dir / "gates" / "agent_runner_dry_run_result.json").exists()
    assert ARTIFACT_PATH in result["generated_artifacts"]


def test_agent_runner_dry_run_fails_closed_on_stale_contract(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)
    contract_path = state_dir / "gates" / "runner_contract_result.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["decision_id"] = "decision_old"
    _write_json(contract_path, contract)

    result = build_agent_runner_dry_run(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert any("runner_contract decision_id mismatch" in error for error in result["errors"])


def test_agent_runner_dry_run_fails_closed_on_executable_contract(tmp_path: Path) -> None:
    state_dir = _make_state(tmp_path)
    contract_path = state_dir / "gates" / "runner_contract_result.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["executable"] = True
    contract["external_invocations"]["codex_cli"] = True
    _write_json(contract_path, contract)

    result = build_agent_runner_dry_run(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert any("executable" in error for error in result["errors"])
    assert any("external invocations" in error for error in result["errors"])
