import json
from pathlib import Path

from reverse_agent.decision_preflight import (
    build_decision_preflight_result,
    validate_decision_preflight_result,
)
from reverse_agent.project_jobs import build_planned_job_payload, planned_job_id_for_round


DECISION_ID = "decision_20260706_post_final_sync_job_preflight_big_step_v1"
ROUND_ID = "round_20260706_post_final_sync_job_preflight_big_step_v1"
REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_decision_preflight_uses_event_aware_mode_and_explicit_path_a_delegation() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "decision-preflight.yml").read_text(encoding="utf-8")

    assert 'control-plane-mode --state-dir project_state --event-path "$GITHUB_EVENT_PATH"' in workflow
    assert "Path-A R1 authority delegated to State Gate" in workflow
    assert "steps.control_plane.outputs.mode == 'path_a_r1'" in workflow
    path_a_step = workflow.split("Path-A R1 authority delegated to State Gate", 1)[1].split("- name:", 1)[0]
    assert "transition-lint" not in path_a_step
    assert "transition-command-plan" not in path_a_step
    assert "transition-preflight" not in path_a_step
    assert "path-a-r1-gate" not in path_a_step
    assert "github.event.pull_request.number" not in workflow


def _write_routing_decision(
    state_dir: Path,
    *,
    branch: str = "owner/decision-bound-r2",
    decision_id: str = "decision_routing",
    round_id: str = "round_routing",
) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "decision_packet.md"
    path.write_text(
        "```json decision_meta\n"
        + json.dumps(
            {
                "decision_id": decision_id,
                "round_id": round_id,
                "status": "APPROVED",
                "mainline": "engineering_branch",
                "skill_profiles": ["reverse-agent-iteration@v2"],
            }
        )
        + "\n```\n\n```json decision_contract\n"
        + json.dumps(
            {
                "transition_kernel_required": True,
                "required_branch": branch,
                "activation_base_sha": "a" * 40,
                "bootstrap_exception_files": [],
                "bootstrap_exception_commands": [],
            }
        )
        + "\n```\n",
        encoding="utf-8",
    )
    return path


def _pr_event(branch: str, *, pr_number: int | None = None) -> dict:
    event = {"pull_request": {"head": {"ref": branch}}}
    if pr_number is not None:
        event["pull_request"]["number"] = pr_number
    return event


def test_shared_pr_routing_ordinary_r1_pr_chooses_path_a(tmp_path: Path) -> None:
    """Section 6: an ordinary R1 PR plus an unrelated active Decision must route
    State Gate AND Decision Preflight to Path A (path_a_r1)."""

    from reverse_agent.control_plane.legacy_adapter import detect_control_plane_mode

    decision = _write_routing_decision(tmp_path / "project_state", branch="owner/decision-bound-r2")
    event = _pr_event("codex/ordinary-r1")
    assert detect_control_plane_mode(decision, event=event) == "path_a_r1"


def test_shared_pr_routing_decision_bound_branch_chooses_transition(tmp_path: Path) -> None:
    """Section 6: a Decision-bound R2/R3 branch must route State Gate AND
    Decision Preflight to transition."""

    from reverse_agent.control_plane.legacy_adapter import detect_control_plane_mode

    decision = _write_routing_decision(tmp_path / "project_state", branch="owner/decision-bound-r2")
    event = _pr_event("owner/decision-bound-r2")
    assert detect_control_plane_mode(decision, event=event) == "transition"


def test_shared_pr_routing_has_no_pr_number_specific_exceptions(tmp_path: Path) -> None:
    """Section 6: mode selection must never depend on the PR number."""

    from reverse_agent.control_plane.legacy_adapter import detect_control_plane_mode

    decision = _write_routing_decision(tmp_path / "project_state", branch="owner/decision-bound-r2")
    for pr_number in (1, 49, 151, 555, 9999):
        assert detect_control_plane_mode(
            decision,
            event=_pr_event("codex/ordinary-r1", pr_number=pr_number),
        ) == "path_a_r1"
        assert detect_control_plane_mode(
            decision,
            event=_pr_event("owner/decision-bound-r2", pr_number=pr_number),
        ) == "transition"


def test_shared_pr_routing_both_workflows_use_same_event_aware_contract() -> None:
    """Section 6: State Gate and Decision Preflight must use the same
    event-aware control-plane-mode selection contract (PR event context, not
    repository-state-only inspection). The Detect control-plane mode block must
    never branch on a PR number."""

    for name in ("state-gate.yml", "decision-preflight.yml"):
        workflow = (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert 'control-plane-mode --state-dir project_state --event-path "$GITHUB_EVENT_PATH"' in workflow
        detect_block = workflow.split("Detect control-plane mode", 1)[1].split("      - name:", 1)[0]
        assert "github.event.pull_request.number" not in detect_block
