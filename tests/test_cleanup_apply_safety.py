import json
from pathlib import Path

from reverse_agent.cleanup_apply_safety import (
    build_cleanup_apply_dry_run,
    build_cleanup_apply_review_bundle,
    build_cleanup_apply_safety_bundle,
    build_cleanup_apply_safety_plan,
    build_deletion_manifest_validation,
    build_doctor_backlog_split,
    build_governance_fix,
    build_status_policy_reconcile,
    build_tombstone_validation,
    validate_cleanup_apply_safety_bundle,
    validate_cleanup_apply_review_result,
)


DECISION_ID = "decision_20260705_governance_fix_cleanup_apply_safety_v1"
ROUND_ID = "round_20260705_governance_fix_cleanup_apply_safety_v1"
REPORT_ID = "codex_report_20260705_governance_fix_cleanup_apply_safety_v1"


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "context").mkdir()
    (state_dir / "roadmap").mkdir()
    previous_round = "round_20260705_state_governance_bundle_big_step_v1"
    (state_dir / "rounds" / previous_round).mkdir(parents=True)
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
  "follows_last_accepted_decision_id": "decision_20260705_state_governance_bundle_big_step_v1",
  "follows_last_accepted_round_id": "{previous_round}",
  "accepted_requires_fix_lane": true,
  "accepted_requires_status_policy_reconcile": true,
  "accepted_requires_doctor_backlog_split": true,
  "accepted_requires_engineering_lane": true,
  "accepted_requires_cleanup_apply_safety_gate": true,
  "accepted_requires_cleanup_apply_dry_run": true,
  "accepted_requires_manifest_and_tombstone_validation": true,
  "accepted_requires_no_real_cleanup_apply": true
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
    (state_dir / "task_packet.json").write_text("{}", encoding="utf-8")
    (state_dir / "current_state.json").write_text("{}", encoding="utf-8")
    (state_dir / "negative_results.json").write_text("[]", encoding="utf-8")
    (state_dir / "artifact_index.json").write_text(
        json.dumps(
            {
                "missing": ["summary"],
                "latest_artifacts_v2": {
                    "summary": {"freshness": "missing"},
                    "old_probe": {"freshness": "stale"},
                },
            }
        ),
        encoding="utf-8",
    )
    (state_dir / "rounds" / previous_round / "round_manifest.json").write_text(
        json.dumps({"round_id": previous_round, "report_status": "SUCCESS"}),
        encoding="utf-8",
    )


def test_status_policy_reconcile_and_doctor_split_make_historical_backlog_nonblocking(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    status = build_status_policy_reconcile(state_dir=state_dir)
    doctor = build_doctor_backlog_split(state_dir=state_dir)
    fix = build_governance_fix(state_dir=state_dir)

    assert status["gate_status"] == "PASSED"
    assert status["historical_backlog_blocking_current_round"] is False
    assert status["issue_classifications"][0]["classification"] == "historical_backlog_notice"
    assert doctor["historical_backlog_notices"][0]["current_blocker"] is False
    assert fix["previous_limitation_resolved_for_current_non_sample_governance"] is True


def test_cleanup_apply_dry_run_never_allows_real_actions(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    (state_dir / "gates" / "run_closeout_20260705_000000.out.log").write_text("ok", encoding="utf-8")

    plan = build_cleanup_apply_safety_plan(state_dir=state_dir)
    dry_run = build_cleanup_apply_dry_run(state_dir=state_dir, safety_plan=plan)

    assert plan["real_cleanup_apply"] is False
    assert all(item["real_action_allowed"] is False for item in plan["dry_run_candidates"])
    assert dry_run["real_cleanup_apply"] is False
    assert dry_run["deleted_files"] == []
    assert dry_run["moved_files"] == []
    assert dry_run["archived_files"] == []
    assert dry_run["written_tombstones"] == []
    assert dry_run["real_deletion_manifests"] == []


def test_manifest_and_tombstone_validation_are_schema_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    manifest = build_deletion_manifest_validation(state_dir=state_dir)
    tombstone = build_tombstone_validation(state_dir=state_dir)

    assert manifest["validation_status"] == "PASSED"
    assert manifest["real_deletion_payload"] is False
    assert tombstone["validation_status"] == "PASSED"
    assert tombstone["real_tombstone_payload"] is False


def test_cleanup_apply_safety_bundle_refreshes_context_and_workstream(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    result = build_cleanup_apply_safety_bundle(state_dir=state_dir)
    workstreams = json.loads((state_dir / "roadmap" / "workstreams.json").read_text(encoding="utf-8"))
    active = [item for item in workstreams["workstreams"] if item["status"] == "ACTIVE_ROUND"]

    assert result["gate_status"] == "PASSED"
    assert validate_cleanup_apply_safety_bundle(result) == []
    assert result["real_cleanup_apply"] is False
    assert result["dry_run_only"] is True
    assert active[0]["workstream_id"] == "governance_fix_cleanup_apply_safety"
    assert (state_dir / "state_manifest.json").exists()
    assert (state_dir / "context" / "current_context_packet.json").exists()


def test_cleanup_apply_review_bundle_is_human_review_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    (state_dir / "gates" / "run_closeout_20260705_000000.out.log").write_text("ok", encoding="utf-8")

    result = build_cleanup_apply_review_bundle(state_dir=state_dir)
    risk_matrix = json.loads((state_dir / "gates" / "cleanup_candidate_risk_matrix.json").read_text(encoding="utf-8"))
    checklist = json.loads((state_dir / "gates" / "cleanup_apply_approval_checklist.json").read_text(encoding="utf-8"))
    deletion_dry_run = json.loads((state_dir / "gates" / "deletion_manifest_dry_run.json").read_text(encoding="utf-8"))
    tombstone_dry_run = json.loads((state_dir / "gates" / "tombstone_plan_dry_run.json").read_text(encoding="utf-8"))

    assert result["gate_status"] == "PASSED"
    assert validate_cleanup_apply_review_result(result) == []
    assert risk_matrix["delete_allowed_now"] is False
    assert all(row["delete_allowed_now"] is False for row in risk_matrix["rows"])
    assert all(row["archive_allowed_now"] is False for row in risk_matrix["rows"])
    assert checklist["cleanup_apply_allowed_now"] is False
    assert all(item["satisfied_this_round"] is False for item in checklist["items"])
    assert deletion_dry_run["real_deletion_manifest"] is False
    assert deletion_dry_run["delete_allowed_now"] is False
    assert tombstone_dry_run["real_tombstone_write"] is False
