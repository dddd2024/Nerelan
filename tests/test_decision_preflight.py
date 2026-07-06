import json
from pathlib import Path

from reverse_agent.decision_preflight import (
    build_decision_preflight_result,
    validate_decision_preflight_result,
)
from reverse_agent.project_jobs import build_planned_job_payload, planned_job_id_for_round


DECISION_ID = "decision_20260706_post_final_sync_job_preflight_big_step_v1"
ROUND_ID = "round_20260706_post_final_sync_job_preflight_big_step_v1"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_state(state_dir: Path, repo_root: Path, *, workflow_ready: bool = True) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "jobs").mkdir()
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "round_id": "{ROUND_ID}",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "forbidden_capabilities_this_round": [
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "model_api_invocation",
    "workflow_dispatch_trigger",
    "real_sample_analysis_execution",
    "sqlite_database_creation"
  ]
}}
```
""",
        encoding="utf-8",
    )
    _write_json(
        repo_root / ".codex-skills" / "registry.json",
        {"skills": {"reverse-agent-iteration": {"version": 2, "status": "active"}}},
    )
    _write_json(
        state_dir / "gates" / "command_plan.json",
        {"decision_id": DECISION_ID, "round_id": ROUND_ID, "plan_status": "PASSED"},
    )
    _write_json(
        state_dir / "gates" / "post_final_evidence_sync_result.json",
        {"decision_id": DECISION_ID, "round_id": ROUND_ID, "gate_status": "PASSED"},
    )
    decision = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "mainline": "engineering_branch",
    }
    job = build_planned_job_payload(decision, status="READY")
    _write_json(state_dir / "jobs" / f"{planned_job_id_for_round(ROUND_ID)}.json", job)

    workflows = repo_root / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    decision_preflight_command = (
        "python -m reverse_agent.project_gate decision-preflight --state-dir project_state"
    )
    decision_preflight_step = f"      - run: {decision_preflight_command}\n" if workflow_ready else ""
    (workflows / "decision-preflight.yml").write_text(
        f"""name: Decision Preflight
on:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  decision-preflight:
    runs-on: ubuntu-latest
    steps:
      - run: python -m reverse_agent.project_gate command-plan --state-dir project_state
{decision_preflight_step}""",
        encoding="utf-8",
    )
    (workflows / "state-gate.yml").write_text(
        f"""name: State Gate
on:
  pull_request:
permissions:
  contents: read
jobs:
  state-gate:
    runs-on: ubuntu-latest
    steps:
{decision_preflight_step}""",
        encoding="utf-8",
    )


def test_decision_preflight_accepts_current_static_ready_job(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir, tmp_path)

    result = build_decision_preflight_result(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["workflow_readiness_status"] == "READY"
    assert result["job_validation_status"] == "PASSED"
    assert result["expected_job_id"] == planned_job_id_for_round(ROUND_ID)
    assert result["runner_dispatch"] is False
    assert result["model_api_invocation"] is False
    assert (state_dir / "gates" / "decision_preflight_workflow_readiness.json").exists()
    assert validate_decision_preflight_result(result, decision_id=DECISION_ID, round_id=ROUND_ID) == []


def test_decision_preflight_rejects_missing_workflow_command(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir, tmp_path, workflow_ready=False)

    result = build_decision_preflight_result(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert result["workflow_readiness_status"] == "REWORK_REQUIRED"
    assert any("workflow readiness" in error for error in result["errors"])
