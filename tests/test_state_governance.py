import json
from pathlib import Path

from reverse_agent.state_governance import (
    RETENTION_CLASSES,
    build_cleanup_plan,
    build_retention_policy,
    build_state_governance_bundle,
    validate_cleanup_plan,
    validate_retention_policy,
    validate_state_governance_bundle,
)


DECISION_ID = "decision_20260705_state_governance_bundle_big_step_v1"
ROUND_ID = "round_20260705_state_governance_bundle_big_step_v1"
REPORT_ID = "codex_report_20260705_state_governance_bundle_big_step_v1"


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "context").mkdir()
    (state_dir / "roadmap").mkdir()
    (state_dir / "rounds" / "round_20260705_project_governance_context_registry_v1").mkdir(parents=True)
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "round_id": "{ROUND_ID}",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "follows_last_accepted_decision_id": "decision_20260705_project_governance_context_registry_v1",
  "follows_last_accepted_round_id": "round_20260705_project_governance_context_registry_v1",
  "accepted_requires_retention_policy": true,
  "accepted_requires_cleanup_plan": true,
  "accepted_requires_archive_index": true,
  "accepted_requires_lifecycle_registry": true,
  "accepted_requires_governance_gate": true,
  "forbidden_capabilities_this_round": ["cleanup_apply", "model_api_invocation"]
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{{
  "schema_version": 1,
  "report_id": "{REPORT_ID}",
  "round_id": "{ROUND_ID}",
  "based_on_decision_id": "{DECISION_ID}",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")
    for name, payload in {
        "command_plan.json": {"plan_status": "PASSED", "decision_id": DECISION_ID, "round_id": ROUND_ID},
        "execution_log.json": {"gate_status": "PASSED", "decision_id": DECISION_ID, "round_id": ROUND_ID},
        "final_gate_result.json": {"gate_status": "PASSED", "decision_id": DECISION_ID, "round_id": ROUND_ID},
        "report_summary_synthesis.json": {"synthesis_status": "PASSED", "decision_id": DECISION_ID, "round_id": ROUND_ID},
        "run_closeout_result.json": {"closeout_status": "PASSED", "decision_id": DECISION_ID, "round_id": ROUND_ID},
    }.items():
        (state_dir / "gates" / name).write_text(json.dumps(payload), encoding="utf-8")
    (state_dir / "gates" / "run_closeout_20260705_000000.out.log").write_text("ok", encoding="utf-8")
    (state_dir / "gates" / "run_closeout_20260705_000000.err.log").write_text("", encoding="utf-8")
    (state_dir / "gates" / "run_closeout_20260705_000000.pid").write_text("123", encoding="utf-8")
    (state_dir / "task_packet.json").write_text("{}", encoding="utf-8")
    (state_dir / "current_state.json").write_text("{}", encoding="utf-8")
    (state_dir / "negative_results.json").write_text("[]", encoding="utf-8")
    (state_dir / "artifact_index.json").write_text(
        json.dumps({"missing": ["summary"], "latest_artifacts_v2": {"summary": {"freshness": "missing"}}}),
        encoding="utf-8",
    )
    (state_dir / "rounds" / "round_20260705_project_governance_context_registry_v1" / "round_manifest.json").write_text(
        json.dumps({"round_id": "round_20260705_project_governance_context_registry_v1"}),
        encoding="utf-8",
    )


def test_retention_policy_covers_required_classes_without_deletion(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    policy = build_retention_policy(state_dir=state_dir)

    assert set(policy["retention_classes"]) == set(RETENTION_CLASSES)
    assert validate_retention_policy(policy) == []
    assert all(item["deletion_allowed_this_round"] is False for item in policy["retention_classes"].values())


def test_cleanup_plan_is_planning_only_and_classifies_transients(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    plan, summary = build_cleanup_plan(state_dir=state_dir)

    assert plan["cleanup_apply_allowed"] is False
    assert plan["deleted_files"] == []
    assert plan["moved_files"] == []
    assert plan["archived_files"] == []
    assert len(plan["future_candidates"]) == 3
    assert all(item["delete_allowed_now"] is False for item in plan["future_candidates"])
    assert plan["missing_historical_sample_references"][0]["blocking_for_current_round"] is False
    assert summary["future_candidate_count"] == 3
    assert validate_cleanup_plan(plan) == []


def test_state_governance_bundle_generates_all_design_artifacts(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    result = build_state_governance_bundle(state_dir=state_dir)

    assert result["gate_status"] == "PASSED"
    assert result["planning_index_schema_only"] is True
    assert result["cleanup_apply_allowed"] is False
    assert result["destructive_operation_performed"] is False
    assert validate_state_governance_bundle(result) == []
    for path in result["generated_artifacts"]:
        assert (tmp_path / path).exists()
