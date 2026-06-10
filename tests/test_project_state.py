import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from reverse_agent.project_state import (
    archive_round,
    build_project_state,
    doctor,
    ensure_state_layout,
    extract_markdown_json_block,
    lint_decision,
    lint_handoff,
    lint_report,
    main,
    pack_context,
    parse_pytest_result_header,
    read_codex_report_summary,
    read_decision_meta,
    status_summary,
    validate_pytest_result_for_report,
    write_pytest_result,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_decision_packet(
    state_dir: Path,
    *,
    decision_id: str = "decision_test",
    round_id: str = "round_test",
    based_on_state_build_id: str = "state_test",
    based_on_state_digest: str = "digest_test",
    status: str = "APPROVED",
    mainline: str = "",
    skill_profiles: object = None,
) -> None:
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": based_on_state_build_id,
        "based_on_state_digest": based_on_state_digest,
        "status": status,
    }
    if mainline:
        payload["mainline"] = mainline
    if skill_profiles is not None:
        payload["skill_profiles"] = skill_profiles
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )


def _write_skill_registry(tmp_path: Path, skills: dict[str, object] | None = None) -> None:
    registry_skills = skills or {
        "reverse-agent-iteration": {
            "path": ".codex-skills/reverse-agent-iteration/SKILL.md",
            "status": "active",
            "scope": "generic_workflow",
            "version": 2,
        },
        "samplereverse-frontier": {
            "path": ".codex-skills/samplereverse-frontier/SKILL.md",
            "status": "active",
            "scope": "sample_profile",
            "version": 2,
        },
    }
    _write_json(tmp_path / ".codex-skills" / "registry.json", {"schema_version": 1, "skills": registry_skills})


def _write_codex_report(
    state_dir: Path,
    *,
    report_id: str = "report_test",
    based_on_decision_id: str = "decision_test",
    round_id: str = "round_test",
    status: str = "SUCCESS",
    acceptance_recommendation: str = "ACCEPTED",
    files_changed: object = None,
    tests_ran: object = None,
    generated_artifacts: object = None,
) -> None:
    payload = {
        "schema_version": 1,
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": based_on_decision_id,
        "status": status,
        "acceptance_recommendation": acceptance_recommendation,
        "files_changed": [] if files_changed is None else files_changed,
        "tests_ran": ["python -m pytest -q"] if tests_ran is None else tests_ran,
        "generated_artifacts": [] if generated_artifacts is None else generated_artifacts,
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )


def _write_pytest_result(
    state_dir: Path,
    *,
    summary: dict[str, object] | None = None,
    body: str = "pytest passed\n",
) -> None:
    summary = summary or {
        "schema_version": 1,
        "decision_id": "decision_test",
        "report_id": "report_test",
        "round_id": "round_test",
        "generated_at": "2026-05-23T00:00:00Z",
        "status": "PASSED",
        "tests_ran": ["python -m pytest -q"],
    }
    write_pytest_result(state_dir=state_dir, summary=summary, body=body)


def _make_minimal_harness_run(reports_dir: Path, run_name: str = "samplereverse_stalled") -> Path:
    run_dir = reports_dir / "harness_runs" / run_name
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        run_dir / "summary.json",
        {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "error_cases": 0,
            "case_result_paths": [str(run_dir / "case_results" / "samplereverse.json")],
        },
    )
    _write_json(
        run_dir / "run_manifest.json",
        {
            "run_name": run_name,
            "status": "completed",
            "case_ids": ["samplereverse"],
        },
    )
    _write_json(
        run_dir / "case_results" / "samplereverse.json",
        {
            "case_id": "samplereverse",
            "status": "completed_no_expected",
            "profile_name": "samplereverse",
            "matched_profiles": ["samplereverse"],
            "applied_strategies": ["CompareAwareSearchStrategy"],
            "error": "",
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_frontier_summary.json",
        {
            "frontier_active_lane": "frontier_exact1",
            "frontier_stall_stage": "pair_pool",
            "frontier_exact1_stall_reason": "distance_not_improved",
            "frontier_converged_reason": "distance_not_improved",
            "frontier_anchor_candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "compare_semantics_agree": True,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "runtime_ci_exact_wchars": 1,
                    "runtime_ci_distance5": 258,
                    "compare_semantics_agree": True,
                    "frontier_role": "exact1_frontier",
                },
            ],
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_strata_summary.json",
        {
            "frontier_stall_stage": "pair_pool",
            "frontier_exact1_stall_reason": "distance_not_improved",
            "best_exact2_runtime": {
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "runtime_ci_exact_wchars": 2,
                "runtime_ci_distance5": 246,
                "compare_semantics_agree": True,
            },
            "best_frontier_runtime": {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "runtime_ci_exact_wchars": 1,
                "runtime_ci_distance5": 258,
                "compare_semantics_agree": True,
                "frontier_role": "exact1_frontier",
            },
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_guided_pool_result.json",
        {"large_payload": "SOLVE_REPORTS_FULL_SENTINEL"},
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_guided_pool_validation.json",
        {"validations": [{"candidate_hex": "5a3e7f46ddd474d041414141414141"}]},
    )
    return run_dir


def test_build_missing_solve_reports_does_not_crash_and_writes_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"

    build_project_state(
        reports_dir=tmp_path / "missing_reports",
        state_dir=state_dir,
        sample="samplereverse",
    )

    expected = {
        "artifact_index.json",
        "current_state.json",
        "negative_results.json",
        "model_gate.json",
        "task_packet.json",
    }
    assert expected.issubset({item.name for item in state_dir.iterdir()})
    assert (state_dir / "decision_packet.md").exists()
    assert (state_dir / "codex_execution_report.md").exists()
    assert (state_dir / "README.md").exists()
    assert (state_dir / "rounds" / ".gitkeep").exists()
    artifact_index = _read_json(state_dir / "artifact_index.json")
    assert artifact_index["missing"] == ["reports_dir"]
    assert artifact_index["latest_artifacts_v2"]["summary"]["freshness"] == "missing"
    assert artifact_index["latest_artifacts_v2"]["summary"]["path"] is None
    assert _read_json(state_dir / "model_gate.json")["should_call_model"] is False


def test_model_gate_diagnoses_summary_error_with_missing_case_results_no_fallback(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_missing_case_results")
    _write_json(
        run_dir / "summary.json",
        {
            "run_name": "samplereverse_missing_case_results",
            "total_cases": 1,
            "executed_cases": 0,
            "resumed_cases": 1,
            "error_cases": 1,
            "case_result_paths": [str(run_dir / "case_results" / "samplereverse.json")],
        },
    )
    (run_dir / "case_results" / "samplereverse.json").unlink()
    (run_dir / "case_results").rmdir()

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    assert model_gate["reason"] == "latest harness case has errors"
    assert model_gate["harness_diagnostics"]["diagnosis"] == "case_results_directory_absent"
    assert model_gate["harness_diagnostics"]["case_results_missing"] is True
    assert model_gate["harness_diagnostics"]["summary_error_cases"] == 1
    assert model_gate["harness_diagnostics"]["latest_harness_run_status"] == "invalid_or_incomplete"
    # When no complete fallback exists, the next action should be rebuild, not generic repair.
    assert model_gate["harness_diagnostics"]["fallback_available"] is False
    assert model_gate["next_local_action"] == "rebuild_harness_artifact"
    summary = status_summary(state_dir=state_dir)
    assert summary["harness_diagnostics"]["diagnosis"] == "case_results_directory_absent"
    # task_packet should frame the condition as precise rebuild action, not generic reverse-solving.
    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["task"] == "rebuild_harness_artifact"
    assert task_packet["next_local_action"] == "rebuild_harness_artifact"


def test_model_gate_selects_fallback_when_latest_is_invalid(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create a complete fallback run with case_results/
    fallback_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_fallback")
    _write_json(
        fallback_dir / "summary.json",
        {
            "run_name": "samplereverse_fallback",
            "total_cases": 1,
            "executed_cases": 1,
            "error_cases": 0,
            "case_result_paths": [str(fallback_dir / "case_results" / "samplereverse.json")],
        },
    )
    _write_json(
        fallback_dir / "case_results" / "samplereverse.json",
        {"status": "ok", "result": "success"},
    )
    _write_json(fallback_dir / "run_manifest.json", {"run_name": "samplereverse_fallback"})

    # Create an invalid latest run without case_results/
    latest_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_latest_invalid")
    _write_json(
        latest_dir / "summary.json",
        {
            "run_name": "samplereverse_latest_invalid",
            "total_cases": 1,
            "executed_cases": 0,
            "resumed_cases": 1,
            "error_cases": 1,
            "case_result_paths": [str(latest_dir / "case_results" / "samplereverse.json")],
        },
    )
    (latest_dir / "case_results" / "samplereverse.json").unlink()
    (latest_dir / "case_results").rmdir()

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    assert model_gate["reason"] == "latest harness case has errors"
    assert model_gate["harness_diagnostics"]["diagnosis"] == "case_results_directory_absent"
    assert model_gate["harness_diagnostics"]["case_results_missing"] is True
    assert model_gate["harness_diagnostics"]["latest_harness_run_status"] == "invalid_or_incomplete"
    # When a complete fallback exists, the next action should be select_fallback.
    assert model_gate["harness_diagnostics"]["fallback_available"] is True
    assert model_gate["harness_diagnostics"]["fallback_harness_run"]["run_name"] == "samplereverse_fallback"
    assert model_gate["harness_diagnostics"]["fallback_harness_run"]["provenance"] == "fallback_from_invalid_latest_run"
    # model_gate should contain the materialized selected_harness_evidence_source with readiness audit.
    evidence = model_gate["selected_harness_evidence_source"]
    assert evidence is not None
    assert evidence["selection_role"] == "fallback"
    assert evidence["run_name"] == "samplereverse_fallback"
    assert evidence["provenance"] == "fallback_from_invalid_latest_run"
    assert evidence["latest_invalid_run_status"] == "invalid_or_incomplete"
    assert evidence["latest_invalid_run_reason"] == "case_results_directory_absent"
    assert evidence["case_results_count"] == 1
    # Readiness audit should be present and classify based on case result metadata.
    readiness = evidence["readiness_audit"]
    assert readiness is not None
    assert readiness["run_name"] == "samplereverse_fallback"
    assert readiness["summary_present"] is True
    assert readiness["manifest_present"] is True
    assert readiness["case_results_dir_present"] is True
    assert readiness["case_result_count"] == 1
    # The test case result has no structured_evidence or candidates, so it should be incomplete.
    assert readiness["classification"] == "fallback_evidence_incomplete"
    # Repair diagnostics should be present with blockers.
    repair_diag = readiness["repair_diagnostics"]
    assert repair_diag is not None
    assert len(repair_diag["blockers"]) > 0
    assert repair_diag["required_rebuild"] is True
    assert repair_diag["repairable_from_existing_metadata"] is False
    assert repair_diag["primary_blocker_owner"] is not None
    # The model_gate next_local_action should follow the readiness audit recommendation.
    assert model_gate["next_local_action"] == readiness["next_local_action"]
    # task_packet should frame the condition as the precise repair action.
    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["task"] == readiness["next_local_action"]
    assert task_packet["next_local_action"] == readiness["next_local_action"]


def test_model_gate_classifies_ready_fallback_when_evidence_is_sufficient(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create a complete fallback run with rich case_results metadata that passes ALL strictness checks.
    # Must have: status != not_found, no instrumentation_incomplete, validation_count > 0,
    # structured_evidence > 0 or tool_artifacts > 0, candidates > 0.
    fallback_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_ready_fallback")
    _write_json(
        fallback_dir / "summary.json",
        {
            "run_name": "samplereverse_ready_fallback",
            "total_cases": 1,
            "executed_cases": 1,
            "error_cases": 0,
            "not_found_cases": 0,
            "case_result_paths": [str(fallback_dir / "case_results" / "samplereverse.json")],
        },
    )
    _write_json(
        fallback_dir / "case_results" / "samplereverse.json",
        {
            "status": "ok",
            "case_id": "samplereverse",
            "structured_evidence_count": 2,
            "tool_artifact_count": 3,
            "candidate_count": 5,
            "validation_count": 2,
            "error": "",
            "artifact_manifest": [
                {"artifact_id": "test_artifact", "classification": "confirmed"}
            ],
        },
    )
    _write_json(fallback_dir / "run_manifest.json", {"run_name": "samplereverse_ready_fallback"})

    # Create an invalid latest run without case_results/
    latest_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_latest_invalid")
    _write_json(
        latest_dir / "summary.json",
        {
            "run_name": "samplereverse_latest_invalid",
            "total_cases": 1,
            "executed_cases": 0,
            "resumed_cases": 1,
            "error_cases": 1,
            "case_result_paths": [str(latest_dir / "case_results" / "samplereverse.json")],
        },
    )
    (latest_dir / "case_results" / "samplereverse.json").unlink()
    (latest_dir / "case_results").rmdir()

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    evidence = model_gate["selected_harness_evidence_source"]
    assert evidence is not None
    readiness = evidence["readiness_audit"]
    assert readiness is not None
    # All strictness checks passed: evidence is genuinely ready.
    assert readiness["classification"] == "fallback_evidence_ready_for_reverse_decision"
    assert readiness["structured_evidence_count"] == 2
    assert readiness["tool_artifact_count"] == 3
    assert readiness["candidate_count"] == 5
    assert readiness["validation_count"] == 2
    assert readiness["next_local_action"] == "prepare_reverse_solving_from_selected_fallback_evidence"
    # Ready path should have empty blockers and no rebuild required.
    repair_diag = readiness["repair_diagnostics"]
    assert repair_diag is not None
    assert repair_diag["blockers"] == []
    assert repair_diag["required_rebuild"] is False
    assert repair_diag["repairable_from_existing_metadata"] is True
    assert repair_diag["primary_blocker_owner"] is None
    assert model_gate["next_local_action"] == "prepare_reverse_solving_from_selected_fallback_evidence"
    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["task"] == "prepare_reverse_solving_from_selected_fallback_evidence"
    assert task_packet["next_local_action"] == "prepare_reverse_solving_from_selected_fallback_evidence"


def test_model_gate_strictness_blocks_not_found_with_instrumentation_incomplete(tmp_path: Path) -> None:
    """Regression test: status:not_found + instrumentation_incomplete must NOT be classified ready."""
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    fallback_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_strict_fallback")
    _write_json(
        fallback_dir / "summary.json",
        {
            "run_name": "samplereverse_strict_fallback",
            "total_cases": 1,
            "executed_cases": 1,
            "error_cases": 0,
            "not_found_cases": 1,
            "case_result_paths": [str(fallback_dir / "case_results" / "samplereverse.json")],
        },
    )
    _write_json(
        fallback_dir / "case_results" / "samplereverse.json",
        {
            "status": "not_found",
            "case_id": "samplereverse",
            "structured_evidence_count": 2,
            "tool_artifact_count": 3,
            "candidate_count": 5,
            "validation_count": 0,
            "error": "",
            "artifact_manifest": [
                {"artifact_id": "incomplete_probe", "classification": "instrumentation_incomplete"}
            ],
        },
    )
    _write_json(fallback_dir / "run_manifest.json", {"run_name": "samplereverse_strict_fallback"})

    latest_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_latest_invalid")
    _write_json(
        latest_dir / "summary.json",
        {
            "run_name": "samplereverse_latest_invalid",
            "total_cases": 1,
            "executed_cases": 0,
            "resumed_cases": 1,
            "error_cases": 1,
            "case_result_paths": [str(latest_dir / "case_results" / "samplereverse.json")],
        },
    )
    (latest_dir / "case_results" / "samplereverse.json").unlink()
    (latest_dir / "case_results").rmdir()

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    evidence = model_gate["selected_harness_evidence_source"]
    assert evidence is not None
    readiness = evidence["readiness_audit"]
    assert readiness is not None
    # Must be classified as incomplete, NOT ready.
    assert readiness["classification"] == "fallback_evidence_incomplete"
    # The first failing strictness check is status == not_found.
    assert readiness["reason"] == "case_result_status_is_not_found"
    # Repair diagnostics should identify the primary blocker owner.
    repair_diag = readiness["repair_diagnostics"]
    assert repair_diag is not None
    assert repair_diag["primary_blocker_owner"] == "case_result_writer"
    assert repair_diag["required_rebuild"] is True
    assert repair_diag["repairable_from_existing_metadata"] is False
    # next_local_action should be precise based on primary blocker owner.
    assert readiness["next_local_action"] == "repair_harness_case_result_materialization"
    assert model_gate["next_local_action"] == "repair_harness_case_result_materialization"
    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["task"] == "repair_harness_case_result_materialization"
    assert task_packet["next_local_action"] == "repair_harness_case_result_materialization"


def test_doctor_passes_on_healthy_state(tmp_path: Path) -> None:
    """Doctor should report PASS or WARN on a fully consumed and archived state.

    WARN is expected because build_project_state creates artifact_index.json with
    missing artifacts for a minimal harness run.
    """
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create skill registry in the temp directory (repo root = state_dir.parent = tmp_path)
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {"status": "active", "version": 2, "scope": "generic_workflow"},
                "samplereverse-frontier": {"status": "active", "version": 2},
            },
        },
    )

    # Build a minimal healthy state
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_healthy")
    _write_json(
        run_dir / "summary.json",
        {"run_name": "samplereverse_healthy", "total_cases": 1, "executed_cases": 1, "error_cases": 0},
    )
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "ok"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    # Write a matching decision, report, and pytest_result
    decision_id = "decision_test_healthy"
    round_id = "round_test_healthy"
    report_id = "report_test_healthy"
    (state_dir / "decision_packet.md").write_text(
        f'```json decision_meta\n{{"schema_version": 1, "decision_id": "{decision_id}", "round_id": "{round_id}", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        f'```json codex_report_summary\n{{"schema_version": 1, "report_id": "{report_id}", "round_id": "{round_id}", "based_on_decision_id": "{decision_id}", "status": "SUCCESS", "tests_ran": ["test"], "files_changed": [], "generated_artifacts": []}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "pytest_result.txt").write_text(
        f'```json pytest_result_summary\n{{"schema_version": 1, "decision_id": "{decision_id}", "report_id": "{report_id}", "round_id": "{round_id}", "status": "PASSED", "tests_ran": ["test"]}}\n```\n',
        encoding="utf-8",
    )

    # Archive the round
    archive_round(state_dir=state_dir, round_id=round_id)

    result = doctor(state_dir=state_dir)

    # Minimal harness runs produce missing artifacts in artifact_index.json,
    # so doctor reports WARN rather than PASS.  This is acceptable.
    assert result["status"] in {"PASS", "WARN"}
    assert result["next_action"] is None
    check_names = {c["name"] for c in result["checks"]}
    assert "decision_approval" in check_names
    assert "mainline" in check_names
    assert "skill_profiles" in check_names
    assert "report_parse" in check_names
    assert "report_decision_match" in check_names
    assert "pytest_result" in check_names
    assert "archive" in check_names
    assert "artifacts" in check_names


def test_doctor_fails_on_report_decision_mismatch(tmp_path: Path) -> None:
    """Doctor should FAIL when report decision_id does not match current decision."""
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create skill registry in the temp directory (repo root = state_dir.parent = tmp_path)
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {"status": "active", "version": 2, "scope": "generic_workflow"},
                "samplereverse-frontier": {"status": "active", "version": 2},
            },
        },
    )

    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_mismatch")
    _write_json(
        run_dir / "summary.json",
        {"run_name": "samplereverse_mismatch", "total_cases": 1, "executed_cases": 1, "error_cases": 0},
    )
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "ok"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    decision_id = "decision_test_mismatch"
    round_id = "round_test_mismatch"
    report_id = "report_test_mismatch"
    (state_dir / "decision_packet.md").write_text(
        f'```json decision_meta\n{{"schema_version": 1, "decision_id": "{decision_id}", "round_id": "{round_id}", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]}}\n```\n',
        encoding="utf-8",
    )
    # Report based_on_decision_id does NOT match decision_id
    (state_dir / "codex_execution_report.md").write_text(
        f'```json codex_report_summary\n{{"schema_version": 1, "report_id": "{report_id}", "round_id": "{round_id}", "based_on_decision_id": "wrong_decision_id", "status": "SUCCESS", "tests_ran": ["test"], "files_changed": [], "generated_artifacts": []}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "pytest_result.txt").write_text(
        f'```json pytest_result_summary\n{{"schema_version": 1, "decision_id": "wrong_decision_id", "report_id": "{report_id}", "round_id": "{round_id}", "status": "PASSED", "tests_ran": ["test"]}}\n```\n',
        encoding="utf-8",
    )

    result = doctor(state_dir=state_dir)

    assert result["status"] == "FAIL"
    assert result["next_action"] == "fix_project_state_issues"
    report_match_check = next(c for c in result["checks"] if c["name"] == "report_decision_match")
    assert report_match_check["status"] == "FAIL"


def test_doctor_fails_on_missing_pytest_result(tmp_path: Path) -> None:
    """Doctor should FAIL when pytest_result.txt is missing."""
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create skill registry in the temp directory (repo root = state_dir.parent = tmp_path)
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {"status": "active", "version": 2, "scope": "generic_workflow"},
                "samplereverse-frontier": {"status": "active", "version": 2},
            },
        },
    )

    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_no_pytest")
    _write_json(
        run_dir / "summary.json",
        {"run_name": "samplereverse_no_pytest", "total_cases": 1, "executed_cases": 1, "error_cases": 0},
    )
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "ok"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    decision_id = "decision_test_no_pytest"
    round_id = "round_test_no_pytest"
    report_id = "report_test_no_pytest"
    (state_dir / "decision_packet.md").write_text(
        f'```json decision_meta\n{{"schema_version": 1, "decision_id": "{decision_id}", "round_id": "{round_id}", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        f'```json codex_report_summary\n{{"schema_version": 1, "report_id": "{report_id}", "round_id": "{round_id}", "based_on_decision_id": "{decision_id}", "status": "SUCCESS", "tests_ran": ["test"], "files_changed": [], "generated_artifacts": []}}\n```\n',
        encoding="utf-8",
    )
    # Do NOT write pytest_result.txt
    if (state_dir / "pytest_result.txt").exists():
        (state_dir / "pytest_result.txt").unlink()

    result = doctor(state_dir=state_dir)

    assert result["status"] == "FAIL"
    assert result["next_action"] == "fix_project_state_issues"
    pytest_check = next(c for c in result["checks"] if c["name"] == "pytest_result")
    assert pytest_check["status"] == "FAIL"
    assert "missing" in pytest_check["detail"].lower() or "empty" in pytest_check["detail"].lower()


def test_doctor_json_output(tmp_path: Path) -> None:
    """Doctor --json should output valid JSON.

    WARN is expected because build_project_state creates artifact_index.json with
    missing artifacts for a minimal harness run.
    """
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"

    # Create skill registry in the temp directory (repo root = state_dir.parent = tmp_path)
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {"status": "active", "version": 2, "scope": "generic_workflow"},
                "samplereverse-frontier": {"status": "active", "version": 2},
            },
        },
    )

    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_json")
    _write_json(
        run_dir / "summary.json",
        {"run_name": "samplereverse_json", "total_cases": 1, "executed_cases": 1, "error_cases": 0},
    )
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "ok"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    decision_id = "decision_test_json"
    round_id = "round_test_json"
    report_id = "report_test_json"
    (state_dir / "decision_packet.md").write_text(
        f'```json decision_meta\n{{"schema_version": 1, "decision_id": "{decision_id}", "round_id": "{round_id}", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        f'```json codex_report_summary\n{{"schema_version": 1, "report_id": "{report_id}", "round_id": "{round_id}", "based_on_decision_id": "{decision_id}", "status": "SUCCESS", "tests_ran": ["test"], "files_changed": [], "generated_artifacts": []}}\n```\n',
        encoding="utf-8",
    )
    (state_dir / "pytest_result.txt").write_text(
        f'```json pytest_result_summary\n{{"schema_version": 1, "decision_id": "{decision_id}", "report_id": "{report_id}", "round_id": "{round_id}", "status": "PASSED", "tests_ran": ["test"]}}\n```\n',
        encoding="utf-8",
    )
    archive_round(state_dir=state_dir, round_id=round_id)

    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = doctor(state_dir=state_dir, json_output=True)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    parsed = json.loads(output)
    # Minimal harness runs produce missing artifacts, so WARN is acceptable.
    assert parsed["status"] in {"PASS", "WARN"}
    assert "checks" in parsed
    assert isinstance(parsed["checks"], list)


def test_project_state_indexes_pre_rc4_material_probe_and_negative_result(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_pre_rc4")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "pre_rc4_material_probe" / "pre_rc4_material_probe.json",
        {
            "artifact_kind": "pre_rc4_material_probe",
            "classification": "material_capture_unreliable",
            "runtime_backed_count": 0,
            "candidate_count": 3,
            "probe_points": {
                "base64_material": "unavailable",
                "rc4_ksa_key": "unavailable",
                "compare_buffer": "unavailable",
            },
            "rc4_key_status": "unknown",
            "rc4_input_status": "unknown",
            "first_divergence_stage": "unknown",
            "offline_runtime_agreement_table": [],
            "producer_material_relation_table": [],
            "next_bounded_action": "switch to manual breakpoints",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["pre_rc4_material_probe"].endswith("pre_rc4_material_probe.json")
    assert current_state["current_bottleneck"]["stage"] == "pre_rc4_material_probe"
    assert current_state["latest_pre_rc4_material_probe"]["classification"] == "material_capture_unreliable"
    assert current_state["latest_pre_rc4_material_probe"]["first_divergence_stage"] == "unknown"
    assert any("memory-scan lower-level pre-RC4" in item["direction"] for item in negative_results)


def test_project_state_indexes_base64_rc4_breakpoint_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_breakpoint")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_breakpoint_probe" / "base64_rc4_breakpoint_probe.json",
        {
            "artifact_kind": "base64_rc4_breakpoint_probe",
            "classification": "breakpoint_probe_partial",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_event_count": 3,
            "static_point_summary": {"base64": {"count": 1, "hookable_count": 1}},
            "hook_results": {
                "base64_input": "unavailable",
                "base64_output": "unavailable",
                "rc4_key": "unavailable",
                "rc4_input": "unavailable",
                "rc4_output": "unavailable",
                "compare_buffer": "available",
            },
            "first_captured_material_kind": "compare_buffer",
            "next_bottleneck": "compare-only capture",
            "next_bounded_action": "manual breakpoints",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["base64_rc4_breakpoint_probe"].endswith(
        "base64_rc4_breakpoint_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "base64_rc4_breakpoint_probe"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["classification"] == "breakpoint_probe_partial"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["hook_event_count"] == 3
    assert current_state["latest_base64_rc4_breakpoint_probe"]["first_captured_material_kind"] == "compare_buffer"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["next_bottleneck"] == "compare-only capture"
    assert "static_points" not in current_state["latest_base64_rc4_breakpoint_probe"]
    assert any("scripted Base64/RC4 breakpoint probe" in item["direction"] for item in negative_results)


def test_project_state_indexes_base64_rc4_static_point_discovery(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_static")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_static_point_discovery.json",
        {
            "artifact_kind": "base64_rc4_static_point_discovery",
            "classification": "manual_disassembly_required",
            "hookable_count": 2,
            "instruction_confirmed_count": 0,
            "by_kind": {
                "base64": {"count": 1, "hookable_count": 1, "instruction_confirmed_count": 0},
                "encrypted_const": {"count": 1, "hookable_count": 1, "instruction_confirmed_count": 0},
            },
            "best_points": [
                {
                    "kind": "base64",
                    "module_offset": "0x3000",
                    "rva": "0x3000",
                    "instruction": "",
                    "hookable": True,
                    "confidence": "high",
                    "evidence": ["standard alphabet"],
                    "classification": "hookable_but_unconfirmed",
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "confirm the ambiguous Base64/RC4 offsets in IDA/x64dbg before rerunning breakpoint probe",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["base64_rc4_static_point_discovery"].endswith(
        "base64_rc4_static_point_discovery.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "base64_rc4_static_point_discovery"
    latest = current_state["latest_static_point_discovery"]
    assert latest["classification"] == "manual_disassembly_required"
    assert latest["hookable_count"] == 2
    assert latest["by_kind"]["base64"]["hookable_count"] == 1
    assert latest["best_points"][0]["module_offset"] == "0x3000"
    assert any("static point discovery" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_stack_pivot_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_stack_pivot")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_stack_pivot_probe" / "compare_stack_pivot_probe.json",
        {
            "artifact_kind": "compare_stack_pivot_probe",
            "classification": "compare_stack_pivot_complete",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "utf16le_payload_available_count": 3,
            "hook_results": {
                "utf16le_payload": "available_from_compare_stack",
                "compare_buffer": "available",
            },
            "static_audit": {
                "classification": "static_anchor_confirmed",
                "compare_site": {
                    "expected_call_rva": "0x258c",
                    "actual_call_rva": "0x258c",
                    "helper_rva": "0x1028ac",
                },
            },
            "next_hook_points": [{"name": "post_handoff_lhs_reload", "module_offset": 0x2559}],
            "next_bounded_action": "hook module+0x1b50",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_stack_pivot_probe"].endswith(
        "compare_stack_pivot_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_stack_pivot_probe"
    latest = current_state["latest_compare_stack_pivot_probe"]
    assert latest["classification"] == "compare_stack_pivot_complete"
    assert latest["utf16le_payload_available_count"] == 3
    assert any("compare stack pivot hook points" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_probe" / "compare_handoff_probe.json",
        {
            "artifact_kind": "compare_handoff_probe",
            "classification": "handoff_capture_partial",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "unavailable",
                "post_handoff_lhs_reload": "available",
                "compare_lhs_buffer": "available",
                "lhs_slot": "available",
            },
            "compare_stack_pivot_audit": {
                "compare_call_rva": "0x258c",
                "handoff_helper_rva": "0x1b50",
                "post_handoff_reload_rva": "0x2559",
                "lhs_slot": "[ebp-0x1170]",
                "static_anchor_valid": True,
                "reason": [],
            },
            "next_bounded_action": "perform a narrower backward slice from 0x401b50 helper arguments",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_probe"].endswith("compare_handoff_probe.json")
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_probe"
    latest = current_state["latest_compare_handoff_probe"]
    assert latest["classification"] == "handoff_capture_partial"
    assert latest["hook_results"]["post_handoff_lhs_reload"] == "available"
    assert any("compare handoff probe" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_slice_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_handoff_slice")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_slice_probe" / "compare_handoff_slice_probe.json",
        {
            "artifact_kind": "compare_handoff_slice_probe",
            "classification": "wrong_reload_anchor",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "available",
                "post_handoff_lhs_reload": "unavailable",
                "post_handoff_after_reload": "available",
                "compare_lhs_buffer": "available",
                "lhs_slot": "available",
            },
            "static_audit": {
                "classification": "static_anchor_confirmed",
                "prior_reload_anchor": "module+0x2559",
                "corrected_post_helper_probe": "helper onLeave plus module+0x255c fallback",
            },
            "cross_candidate_summary": {
                "relation_counts": {"helper_return_eax_preview_matches_compare_lhs": 3},
            },
            "next_bounded_action": "replace module+0x2559 with an instruction-confirmed post-helper hook point",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_slice_probe"].endswith(
        "compare_handoff_slice_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_slice_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_reload_anchor"
    latest = current_state["latest_compare_handoff_slice_probe"]
    assert latest["classification"] == "wrong_reload_anchor"
    assert latest["hook_results"]["post_handoff_after_reload"] == "available"
    assert any("helper slice" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_return_site_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_return_site")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_return_site_probe" / "compare_handoff_return_site_probe.json",
        {
            "artifact_kind": "compare_handoff_return_site_probe",
            "classification": "wrong_helper_assumption",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "available",
                "helper_return_site": "available",
                "wide_flag_prefix_compare": "available",
                "compare_call_args": "available",
            },
            "static_audit": {
                "classification": "static_return_site_audit_complete",
                "hook_point_audit": [
                    {
                        "name": "post_handoff_after_reload",
                        "module_offset": "0x255c",
                        "boundary_status": "inside_instruction",
                    }
                ],
            },
            "cross_candidate_summary": {
                "relation_counts": {"helper_enter_return_is_0x233d": 3},
                "target_flag_side_counts": {"arg0": 3},
            },
            "next_bounded_action": "move to the next bounded pre-compare handoff target",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_return_site_probe"].endswith(
        "compare_handoff_return_site_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_return_site_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_helper_assumption"
    latest = current_state["latest_compare_handoff_return_site_probe"]
    assert latest["classification"] == "wrong_helper_assumption"
    assert latest["hook_results"]["compare_call_args"] == "available"
    assert any("return-site audit" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_producer_trace_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_producer_trace")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_static_point_discovery.json",
        {
            "artifact_kind": "base64_rc4_static_point_discovery",
            "classification": "hookable_points_found",
            "breakpoint_probe_allowed": False,
        },
    )
    _write_json(
        artifacts_dir / "base64_rc4_breakpoint_probe" / "base64_rc4_breakpoint_probe.json",
        {
            "artifact_kind": "base64_rc4_breakpoint_probe",
            "classification": "base64_rc4_static_points_unavailable",
            "hook_results": {"compare_buffer": "available"},
        },
    )
    _write_json(
        artifacts_dir / "compare_producer_trace_probe" / "compare_producer_trace_probe.json",
        {
            "artifact_kind": "compare_producer_trace_probe",
            "classification": "compare_producer_trace_captured",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "candidate_material_count": 3,
            "candidate_materials": [
                {
                    "kind": "compare_buffer",
                    "address": "0x36dce20",
                    "preview_hex": "46006c004464830d311c",
                    "evidence": ["matches compare arg"],
                }
            ],
            "write_source_trace_count": 1,
            "write_source_trace": [
                {
                    "source_module_offset": "0x253a",
                    "instruction": "mov dword ptr [ebp - 0x1170], eax",
                    "classification": "compare_buffer_write_source",
                }
            ],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "hook_results": {
                "producer_return_site": "available",
                "compare_helper_entry": "available",
                "compare_entry_args": "available",
            },
            "hook_miss_classification": {
                "missed_hooks": "post_handoff_lhs_reload, pre_compare_push_esi",
                "classification": "wrapper/alternate compare path",
            },
            "static_audit": {
                "classification": "static_producer_trace_audit_complete",
                "producer_window": {"start_rva": "0x2310", "end_rva": "0x2365"},
            },
            "cross_candidate_summary": {
                "relation_counts": {"producer_eax_matches_compare_arg_ptr": 3},
                "target_flag_side_counts": {"entry_arg1": 3},
            },
            "next_bounded_action": "derive candidate-side byte constraints from the actual compare helper entry args",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_producer_trace_probe"].endswith(
        "compare_producer_trace_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_producer_trace_probe"
    assert current_state["current_bottleneck"]["reason"] == "compare_producer_trace_captured"
    latest = current_state["latest_compare_producer_trace_probe"]
    assert latest["classification"] == "compare_producer_trace_captured"
    assert latest["candidate_material_count"] == 3
    assert latest["best_material_candidates"][0]["kind"] == "compare_buffer"
    assert latest["write_source_trace_count"] == 1
    assert latest["material_hook_candidate_count"] == 0
    assert latest["breakpoint_probe_allowed"] is False
    assert latest["hook_results"]["compare_helper_entry"] == "available"
    assert latest["hook_miss_classification"]["classification"] == "wrapper/alternate compare path"
    assert any("producer trace" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_producer_material_confirmation_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_material_confirmation")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_producer_trace_probe" / "compare_producer_trace_probe.json",
        {
            "artifact_kind": "compare_producer_trace_probe",
            "classification": "upstream_material_candidate_found",
            "candidate_material_count": 3,
            "breakpoint_probe_allowed": False,
        },
    )
    _write_json(
        artifacts_dir / "compare_producer_material_confirmation.json",
        {
            "artifact_kind": "compare_producer_material_confirmation",
            "classification": "material_confirmation_inconclusive",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "instruction_confirmation_table": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                    "observed_count": 3,
                    "candidate_dependent_eax": True,
                    "instruction_confirmed": True,
                    "hookable": True,
                }
            ],
            "material_source_trace": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "expected_candidate_material_seen",
                }
            ],
            "confirmed_material_hook_candidate_count": 0,
            "confirmed_material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "manually inspect producer offsets 0x2320, 0x2338, 0x234e, and 0x2355",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_producer_material_confirmation"].endswith(
        "compare_producer_material_confirmation.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_producer_material_confirmation"
    assert current_state["current_bottleneck"]["reason"] == "material_confirmation_inconclusive"
    latest = current_state["latest_compare_producer_material_confirmation"]
    assert latest["classification"] == "material_confirmation_inconclusive"
    assert latest["runtime_backed_count"] == 3
    assert latest["instruction_confirmation_table"][0]["hook_name"] == "producer_return_site"
    assert latest["material_source_trace"][0]["module_offset"] == "0x233d"
    assert latest["breakpoint_probe_allowed"] is False
    assert any("producer material confirmation" in item["direction"] for item in negative_results)


def test_project_state_indexes_pre_compare_handoff_target_probe_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_pre_compare_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_pre_compare_handoff_target_probe.json",
        {
            "artifact_kind": "compare_pre_compare_handoff_target_probe",
            "classification": "wrong_window",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hit_summary": {
                "hit_producer_return_site_count": 3,
                "hit_producer_pre_candidate_push_count": 3,
                "hit_producer_pre_output_call_count": 0,
                "hit_producer_pre_second_call_count": 0,
                "hit_compare_helper_entry_count": 3,
            },
            "hook_miss_classification": "branch_exits_before_output_calls",
            "candidate_dependent_fields": {"producer_return_site.eax_preview_hex": True},
            "relation_counts": {"producer_return_site.eax_to_arg0.ptr_matches": 3},
            "relation_table": [{"candidate_hex": "78d540b49c59077041414141414141"}],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "inspect branch/call outcome after 0x233d",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_pre_compare_handoff_target_probe"].endswith(
        "compare_pre_compare_handoff_target_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_pre_compare_handoff_target_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_window"
    latest = current_state["latest_compare_pre_compare_handoff_target_probe"]
    assert latest["classification"] == "wrong_window"
    assert latest["hook_miss_classification"] == "branch_exits_before_output_calls"
    assert latest["relation_counts"]["producer_return_site.eax_to_arg0.ptr_matches"] == 3
    assert any("0x401b50 -> 0x2559" in item["direction"] for item in negative_results)


def test_project_state_indexes_function_semantic_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_function_semantics")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "function_semantic_audit" / "function_semantic_audit.json",
        {
            "artifact_kind": "function_semantic_audit",
            "classification": "runtime_instrumentation_required",
            "sample": "samplereverse",
            "profile": "samplereverse",
            "target_functions": ["0x4019e0", "0x401b50", "0x4018cd", "0x401be3"],
            "function_count": 4,
            "functions": [
                {
                    "function": "0x401b50",
                    "semantic_guess": "unknown_but_bounded",
                    "confidence": "medium",
                    "candidate_dependent": False,
                    "instruction_confirmed": True,
                    "hookable": True,
                    "material_hook_candidate_status": "blocked_missing_candidate_dependent_output",
                }
            ],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "top_semantic_guesses": [
                {
                    "function": "0x401b50",
                    "semantic_guess": "unknown_but_bounded",
                    "confidence": "medium",
                }
            ],
            "next_bounded_action": "confirm the 0x401b50 return path",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["function_semantic_audit"].endswith("function_semantic_audit.json")
    assert current_state["current_bottleneck"]["stage"] == "function_semantic_audit"
    assert current_state["current_bottleneck"]["reason"] == "runtime_instrumentation_required"
    latest = current_state["latest_function_semantic_audit"]
    assert latest["function_count"] == 4
    assert latest["material_hook_candidate_count"] == 0
    assert latest["breakpoint_probe_allowed"] is False
    assert current_state["function_semantics"]["0x401b50"]["material_hook_candidate_status"] == (
        "blocked_missing_candidate_dependent_output"
    )
    assert any(item.get("scope") == "function_semantics" for item in negative_results)


def test_project_state_indexes_material_hook_runtime_validation_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_mhrv")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "material_hook_runtime_validation").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "material_hook_runtime_validation" / "material_hook_runtime_validation.json",
        {
            "artifact_kind": "material_hook_runtime_validation",
            "classification": "BLOCKED",
            "runtime_backed_count": 4,
            "candidate_count": 4,
            "validated_hooks": [],
            "blocked_hooks": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "candidate_dependent_but_not_transform_material",
                    "hit_count": 4,
                    "candidate_dependent": True,
                    "connects_to_transform_chain": False,
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "keep Base64/RC4 breakpoint probe blocked",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["material_hook_runtime_validation"].endswith(
        "material_hook_runtime_validation.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "material_hook_runtime_validation"
    assert current_state["current_bottleneck"]["reason"] == "BLOCKED"
    latest = current_state["latest_material_hook_runtime_validation"]
    assert latest["classification"] == "BLOCKED"
    assert latest["candidate_count"] == 4
    assert latest["validated_hook_count"] == 0
    assert latest["blocked_hook_count"] == 1
    assert latest["breakpoint_probe_allowed"] is False
    assert any(item.get("scope") == "material_hook_runtime_validation" for item in negative_results)


def test_project_state_tracks_esi_source_material_hook_task(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_esi_mhrv")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "material_hook_runtime_validation").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "material_hook_runtime_validation" / "material_hook_runtime_validation.json",
        {
            "artifact_kind": "material_hook_runtime_validation",
            "classification": "ACCEPT",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "source_compare_esi_source_window_classification": "esi_source_identified",
            "material_kind": "rc4_output",
            "validated_hooks": [
                {
                    "hook_name": "initial_lhs_reload",
                    "module_offset": "0x2559",
                    "classification": "confirmed_rc4_output_material",
                }
            ],
            "blocked_hooks": [],
            "breakpoint_probe_allowed": True,
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_material_hook_runtime_validation"]
    assert latest["source_compare_esi_source_window_classification"] == "esi_source_identified"
    assert latest["material_kind"] == "rc4_output"
    assert task_packet["task"] == "Run bounded Base64/RC4 breakpoint probe with validated 0x2559 hook"


def test_project_state_tracks_blocked_esi_source_material_hook_task(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_esi_mhrv_blocked")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "material_hook_runtime_validation").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "material_hook_runtime_validation" / "material_hook_runtime_validation.json",
        {
            "artifact_kind": "material_hook_runtime_validation",
            "classification": "BLOCKED",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "source_compare_esi_source_window_classification": "esi_source_identified",
            "material_kind": "rc4_output",
            "validated_hooks": [],
            "blocked_hooks": [
                {
                    "hook_name": "initial_lhs_reload",
                    "module_offset": "0x2559",
                    "classification": "candidate_dependent_but_not_transform_material",
                    "hit_count": 3,
                }
            ],
            "breakpoint_probe_allowed": False,
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    task_packet = _read_json(state_dir / "task_packet.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert task_packet["task"] == "Trace writer/source before 0x2559 / [ebp-0x1170]"
    assert any("0x2559" in item.get("reason", "") for item in negative_results)


def test_project_state_indexes_lhs_slot_writer_source_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_slot_writer")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_lhs_slot_writer_source_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_lhs_slot_writer_source_audit" / "compare_lhs_slot_writer_source_audit.json",
        {
            "artifact_kind": "compare_lhs_slot_writer_source_audit",
            "classification": "slot_writer_confirmed",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "relations": {"slot_writer_to_compare_arg0": "confirmed"},
            "slot_writer": {
                "hook_name": "slot_writer",
                "module_offset": "0x253a",
                "compare_lhs_match_count": 3,
            },
            "writer_rows": [
                {
                    "hook_name": "slot_writer",
                    "module_offset": "0x253a",
                    "candidate_dependent": True,
                }
            ],
            "identified_writers": [{"hook_name": "slot_writer", "module_offset": "0x253a"}],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "validate bounded material hook from confirmed slot writer/source",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_lhs_slot_writer_source_audit"].endswith(
        "compare_lhs_slot_writer_source_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_lhs_slot_writer_source_audit"
    assert current_state["current_bottleneck"]["reason"] == "slot_writer_confirmed"
    latest = current_state["latest_compare_lhs_slot_writer_source_audit"]
    assert latest["classification"] == "slot_writer_confirmed"
    assert latest["slot_writer"]["module_offset"] == "0x253a"
    assert task_packet["task"] == "Validate bounded material hook from confirmed slot writer/source"
    assert any(item.get("scope") == "compare_lhs_slot_writer_source_audit" for item in negative_results)


def test_project_state_indexes_lhs_slot_writer_predecessor_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_pred")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    artifact_path = (
        artifacts_dir
        / "pred"
        / "compare_lhs_slot_writer_predecessor_audit.json"
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        artifact_path,
        {
            "artifact_kind": "compare_lhs_slot_writer_predecessor_audit",
            "classification": "handoff_call_does_not_return_to_linear_path",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "relations": {"handoff_return_to_linear_path": "rejected"},
            "path_observed_counts": {
                "predecessor_handoff_call": 3,
                "predecessor_handoff_return": 0,
            },
            "predecessor_rows": [
                {
                    "hook_name": "predecessor_handoff_call",
                    "module_offset": "0x2338",
                    "observed_count": 3,
                }
            ],
            "identified_sources": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "trace 0x401b50 return, branch, or exception outcome before any Base64/RC4 probe",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_lhs_slot_writer_predecessor_audit"].endswith(
        "compare_lhs_slot_writer_predecessor_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_lhs_slot_writer_predecessor_audit"
    assert current_state["current_bottleneck"]["reason"] == "handoff_call_does_not_return_to_linear_path"
    latest = current_state["latest_compare_lhs_slot_writer_predecessor_audit"]
    assert latest["path_observed_counts"]["predecessor_handoff_call"] == 3
    assert task_packet["task"] == "Trace 0x401b50 return, branch, or exception outcome"
    assert any(item.get("scope") == "compare_lhs_slot_writer_predecessor_audit" for item in negative_results)


def test_project_state_indexes_post_handoff_branch_outcome_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_post_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "post_handoff_branch_outcome_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "post_handoff_branch_outcome_audit" / "post_handoff_branch_outcome_audit.json",
        {
            "artifact_kind": "post_handoff_branch_outcome_audit",
            "classification": "post_handoff_window_rejected",
            "source_pre_compare_handoff_classification": "next_handoff_target_identified",
            "source_pre_compare_handoff_hook_miss_classification": "branch_exits_before_output_calls",
            "source_material_hook_runtime_classification": "REJECTED",
            "failed_material_hook_hypotheses": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "not_reached",
                }
            ],
            "window": {
                "downstream_transform_calls_reached": False,
                "rows": [
                    {"hook_name": "producer_return_site", "module_offset": "0x233d", "observed_count": 3},
                    {"hook_name": "producer_pre_output_call", "module_offset": "0x234e", "observed_count": 0},
                ],
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "audit the 0x233d -> 0x2346 follow-up branch/call outcome",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["post_handoff_branch_outcome_audit"].endswith(
        "post_handoff_branch_outcome_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "post_handoff_branch_outcome_audit"
    assert current_state["current_bottleneck"]["reason"] == "post_handoff_window_rejected"
    latest = current_state["latest_post_handoff_branch_outcome_audit"]
    assert latest["classification"] == "post_handoff_window_rejected"
    assert latest["source_material_hook_runtime_classification"] == "REJECTED"
    assert latest["failed_material_hook_hypotheses"][0]["module_offset"] == "0x233d"
    assert latest["downstream_transform_calls_reached"] is False
    assert any(item.get("scope") == "post_handoff_branch_outcome_audit" for item in negative_results)


def test_project_state_indexes_post_handoff_runtime_outcome(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_401b50_outcome")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "post_handoff_branch_outcome_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "post_handoff_branch_outcome_audit" / "post_handoff_branch_outcome_audit.json",
        {
            "artifact_kind": "post_handoff_branch_outcome_audit",
            "classification": "handoff_returns_to_alternate_site",
            "source_predecessor_classification": "handoff_call_does_not_return_to_linear_path",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "path_observed_counts": {"handoff_helper_entry": 3, "static_compare_callsite": 3},
            "exit_summary": {
                "return_address_module_offsets": {
                    "78d540b49c59077041414141414141": "0x2400",
                }
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "validate bounded material/source hook from confirmed 0x401b50 alternate return site",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_post_handoff_branch_outcome_audit"]
    assert current_state["current_bottleneck"]["stage"] == "post_handoff_branch_outcome_audit"
    assert current_state["current_bottleneck"]["reason"] == "handoff_returns_to_alternate_site"
    assert latest["source_predecessor_classification"] == "handoff_call_does_not_return_to_linear_path"
    assert latest["runtime_backed_count"] == 3
    assert latest["exit_summary"]["return_address_module_offsets"]["78d540b49c59077041414141414141"] == "0x2400"
    assert task_packet["task"] == "Validate bounded material/source hook from confirmed 0x401b50 alternate return site"


def test_project_state_indexes_post_handoff_exception_unwind_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_exc_unwind")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "post_handoff_exception_unwind_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "post_handoff_exception_unwind_audit" / "post_handoff_exception_unwind_audit.json",
        {
            "artifact_kind": "post_handoff_exception_unwind_audit",
            "classification": "exception_dispatch_to_compare_path",
            "source_post_handoff_branch_outcome_classification": "handoff_exception_or_unwind",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "evidence_gate": {
                "upstream_hits": True,
                "compare_entry_observed": True,
                "compare_args_captured": True,
                "exception_evidence": True,
                "handler_unwind_evidence": False,
                "actual_compare_lhs_runtime_backed": True,
                "connected_producer_runtime_backed": False,
                "candidate_dependent_transform_material_runtime_backed": False,
            },
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "exception_path": {
                "observed_exception_offsets": {
                    "78d540b49c59077041414141414141": ["0x1913"],
                },
                "last_observed_offset_before_compare": {
                    "78d540b49c59077041414141414141": "0x1913",
                },
            },
            "tentative_hook_candidates": [
                {
                    "module_offset": "0x1913",
                    "status": "runtime_observed",
                    "evidence_ref": {
                        "artifact": "candidate_1/post_handoff_exception_unwind_audit.json",
                        "field": "hook_observations[2]",
                    },
                }
            ],
            "post_classification_route": "handler_to_lhs_dataflow",
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "trace exception handler to compare lhs dataflow",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["post_handoff_exception_unwind_audit"].endswith(
        "post_handoff_exception_unwind_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "post_handoff_exception_unwind_audit"
    assert current_state["current_bottleneck"]["reason"] == "exception_dispatch_to_compare_path"
    latest = current_state["latest_post_handoff_exception_unwind_audit"]
    assert latest["post_classification_route"] == "handler_to_lhs_dataflow"
    assert latest["tentative_hook_candidates"][0]["evidence_ref"]["field"] == "hook_observations[2]"
    assert task_packet["task"] == "Trace handler-to-lhs dataflow"
    assert any(item.get("scope") == "post_handoff_exception_unwind_audit" for item in negative_results)


def test_project_state_indexes_compare_hook_path_reachability_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_path")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_hook_path_reachability_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_hook_path_reachability_audit" / "compare_hook_path_reachability_audit.json",
        {
            "artifact_kind": "compare_hook_path_reachability_audit",
            "classification": "handoff_helper_entered_but_return_path_skips_compare_window",
            "new_blocker": "handoff_helper_entered_but_return_path_skips_compare_window",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "hook_points": [
                {"name": "handoff_helper_entry", "module_offset": "0x1b50"},
                {"name": "static_compare_callsite", "module_offset": "0x258c"},
            ],
            "hook_address_validation": {"resolved_count": 6, "unresolved_count": 0},
            "path_observed_counts": {"handoff_helper_entry": 3, "static_compare_callsite": 0},
            "actual_compare": {},
            "candidate_execution_health": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "hook_install_status": "installed",
                    "ui_trigger_status": "button_triggered",
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "trace 0x401b50 return or tail path before any Base64/RC4 probe",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_hook_path_reachability_audit"].endswith(
        "compare_hook_path_reachability_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_hook_path_reachability_audit"
    assert (
        current_state["current_bottleneck"]["blocker"]
        == "handoff_helper_entered_but_return_path_skips_compare_window"
    )
    latest = current_state["latest_compare_hook_path_reachability_audit"]
    assert latest["classification"] == "handoff_helper_entered_but_return_path_skips_compare_window"
    assert latest["path_observed_counts"]["handoff_helper_entry"] == 3
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Diagnose bounded compare hook path reachability"


def test_project_state_indexes_compare_handoff_exit_classifier_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_exit_classifier")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_handoff_exit_classifier_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_handoff_exit_classifier_audit" / "compare_handoff_exit_classifier_audit.json",
        {
            "artifact_kind": "compare_handoff_exit_classifier_audit",
            "classification": "exception_unwind_before_compare",
            "overall_classification": "exception_unwind_before_compare",
            "new_blocker": "exception_unwind_before_compare",
            "source_run": "sr_path",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "classification": "exception_unwind_before_compare",
                    "events": [
                        {"order": 1, "name": "predecessor_handoff_call"},
                        {"order": 2, "name": "handoff_helper_entry"},
                        {"order": 3, "name": "process_exception"},
                    ],
                    "process_exception_observed": True,
                    "first_compare_successor_observed": False,
                    "actual_compare_observed": False,
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "trace the exception unwind edge before any search expansion",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_exit_classifier_audit"].endswith(
        "compare_handoff_exit_classifier_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_exit_classifier_audit"
    assert current_state["current_bottleneck"]["blocker"] == "exception_unwind_before_compare"
    latest = current_state["latest_compare_handoff_exit_classifier_audit"]
    assert latest["classification"] == "exception_unwind_before_compare"
    assert latest["candidate_count"] == 3
    assert latest["candidates"][0]["process_exception_observed"] is True
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Trace exception unwind edge before compare"


def test_project_state_indexes_compare_handoff_path_divergence_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_path_divergence")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_handoff_path_divergence_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_handoff_path_divergence_audit" / "compare_handoff_path_divergence_audit.json",
        {
            "artifact_kind": "compare_handoff_path_divergence_audit",
            "classification": "candidate_dependent_non_reaching_path",
            "overall_classification": "candidate_dependent_non_reaching_path",
            "source_run": "sr_path",
            "source_artifact": "compare_handoff_exit_classifier_audit",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "cross_candidate": {
                "common_prefix_events": ["predecessor_handoff_call", "handoff_helper_entry"],
                "first_divergence_after": "handoff_helper_entry",
                "exception_subset_classification": "exception_edge_shared_for_subset",
                "branch_subset_classification": "branch_guard_or_silent_non_reaching_path",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "prior_classification": "exception_unwind_before_compare",
                    "event_sequence": [
                        "predecessor_handoff_call",
                        "handoff_helper_entry",
                        "process_exception",
                    ],
                    "exception_summary": {"address": "0xf41913", "memory": "0x5305154b"},
                },
                {
                    "candidate_hex": "78d540b49c59076f41414141414141",
                    "prior_classification": "branch_guard_before_compare",
                    "event_sequence": ["predecessor_handoff_call", "handoff_helper_entry"],
                    "first_divergence_role": "branch_guard_or_silent_non_reaching_path",
                },
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "branch_operand_provenance_or_exception_edge_audit",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_path_divergence_audit"].endswith(
        "compare_handoff_path_divergence_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_path_divergence_audit"
    assert current_state["current_bottleneck"]["reason"] == "candidate_dependent_non_reaching_path"
    latest = current_state["latest_compare_handoff_path_divergence_audit"]
    assert latest["classification"] == "candidate_dependent_non_reaching_path"
    assert latest["candidate_count"] == 3
    assert latest["cross_candidate"]["first_divergence_after"] == "handoff_helper_entry"
    assert latest["breakpoint_probe_allowed"] is False
    assert latest["next_bounded_action"] == "branch_operand_provenance_or_exception_edge_audit"


def test_project_state_indexes_compare_handoff_edge_operand_provenance_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_edge")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_edge_operand_provenance_audit.json",
        {
            "artifact_kind": "compare_handoff_edge_operand_provenance_audit",
            "classification": "candidate_dependent_handoff_exit_edge_unresolved",
            "overall_classification": "candidate_dependent_handoff_exit_edge_unresolved",
            "source_run": "sr_edge",
            "source_artifacts": [
                "compare_handoff_path_divergence_audit",
                "compare_handoff_exit_classifier_audit",
            ],
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "cross_candidate": {
                "common_prefix_events": ["predecessor_handoff_call", "handoff_helper_entry"],
                "first_divergence_after": "handoff_helper_entry",
                "return_context_candidate_dependent": True,
                "root_cause_classification": "candidate_dependent_handoff_exit_edge_unresolved",
                "schema_gap_fields": ["branch_operand_summary"],
                "next_bounded_action": "bounded_branch_operand_runtime_sidecar_or_instruction_boundary_audit",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "exception_edge_summary": {
                        "observed": True,
                        "memory": "0x5305154b",
                        "previous_event": {"name": "handoff_helper_entry"},
                    },
                    "branch_operand_summary": {"classification": "not_observed"},
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "exception_edge_summary": {
                        "observed": True,
                        "memory": "0x820004",
                        "previous_event": {"name": "handoff_helper_entry"},
                    },
                    "branch_operand_summary": {"classification": "not_observed"},
                },
                {
                    "candidate_hex": "78d540b49c59076f41414141414141",
                    "exception_edge_summary": {"observed": False},
                    "branch_operand_summary": {"classification": "schema_gap"},
                },
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "bounded_branch_operand_runtime_sidecar_or_instruction_boundary_audit",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_edge",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_edge_operand_provenance_audit"].endswith(
        "compare_handoff_edge_operand_provenance_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_edge_operand_provenance_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == (
        "candidate_dependent_handoff_exit_edge_unresolved"
    )
    latest = current_state["latest_compare_handoff_edge_operand_provenance_audit"]
    assert latest["classification"] == "candidate_dependent_handoff_exit_edge_unresolved"
    assert latest["candidate_count"] == 3
    assert latest["cross_candidate"]["return_context_candidate_dependent"] is True
    assert latest["candidates"][2]["branch_operand_summary"]["classification"] == "schema_gap"
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Trace bounded branch operand runtime sidecar or instruction boundary"


def test_project_state_indexes_compare_handoff_branch_operand_runtime_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_branch_operand")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_branch_operand_runtime_audit.json",
        {
            "artifact_kind": "compare_handoff_branch_operand_runtime_audit",
            "classification": "instruction_boundary_gap",
            "overall_classification": "instruction_boundary_gap",
            "source_run": "sr_branch_operand",
            "source_artifacts": [
                "compare_handoff_edge_operand_provenance_audit",
                "compare_handoff_path_divergence_audit",
                "compare_handoff_exit_classifier_audit",
            ],
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "cross_candidate": {
                "root_cause_classification": "instruction_boundary_gap",
                "branch_guard_explained": False,
                "return_context_candidate_dependent": True,
                "return_target_trust": "suspicious",
                "next_bounded_action": "hook_surface_repair",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "branch_operand_evidence": {"classification": "not_observed"},
                    "exception_edge_evidence": {"observed": True},
                    "post_entry_outcome": "exception_edge",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "branch_operand_evidence": {"classification": "not_observed"},
                    "exception_edge_evidence": {"observed": True},
                    "post_entry_outcome": "exception_edge",
                },
                {
                    "candidate_hex": "78d540b49c59076f41414141414141",
                    "branch_operand_evidence": {"classification": "instruction_boundary_gap"},
                    "exception_edge_evidence": {"observed": False},
                    "post_entry_outcome": "instruction_boundary_gap",
                },
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "hook_surface_repair",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_branch_operand",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_branch_operand_runtime_audit"].endswith(
        "compare_handoff_branch_operand_runtime_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_branch_operand_runtime_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == "instruction_boundary_gap"
    latest = current_state["latest_compare_handoff_branch_operand_runtime_audit"]
    assert latest["classification"] == "instruction_boundary_gap"
    assert latest["candidate_count"] == 3
    assert latest["cross_candidate"]["return_target_trust"] == "suspicious"
    assert latest["candidates"][2]["branch_operand_evidence"]["classification"] == (
        "instruction_boundary_gap"
    )
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Repair bounded handoff branch hook surface"


def test_project_state_indexes_compare_handoff_hook_surface_repair_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_hook_surface")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_hook_surface_repair_audit.json",
        {
            "artifact_kind": "compare_handoff_hook_surface_repair_audit",
            "classification": "hook_surface_requires_post_entry_step",
            "overall_classification": "hook_surface_requires_post_entry_step",
            "source_run": "sr_hook_surface",
            "source_artifacts": [
                "compare_handoff_branch_operand_runtime_audit",
                "compare_handoff_edge_operand_provenance_audit",
                "compare_handoff_path_divergence_audit",
                "compare_handoff_exit_classifier_audit",
            ],
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "hook_surface_repair": {
                "surface_classification": "static_boundary_explained",
                "missing_observation": "branch_instruction",
                "repair_type": "no_code_change_gap_classification",
            },
            "hook_surface_coverage": {
                "predecessor_handoff_call": True,
                "handoff_helper_entry": True,
                "process_exception": True,
                "post_entry_single_step": False,
            },
            "cross_candidate": {
                "root_cause_classification": "hook_surface_requires_post_entry_step",
                "return_target_trust": "suspicious",
                "next_bounded_action": "post_entry_step_runtime_audit",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "branch_observation": {"classification": "not_observed"},
                    "post_entry_outcome": "exception_edge",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "branch_observation": {"classification": "not_observed"},
                    "post_entry_outcome": "exception_edge",
                },
                {
                    "candidate_hex": "78d540b49c59076f41414141414141",
                    "branch_observation": {"classification": "instruction_boundary_gap"},
                    "post_entry_outcome": "instruction_boundary_gap",
                },
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "post_entry_step_runtime_audit",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_hook_surface",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_hook_surface_repair_audit"].endswith(
        "compare_handoff_hook_surface_repair_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_hook_surface_repair_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == "hook_surface_requires_post_entry_step"
    latest = current_state["latest_compare_handoff_hook_surface_repair_audit"]
    assert latest["classification"] == "hook_surface_requires_post_entry_step"
    assert latest["candidate_count"] == 3
    assert latest["hook_surface_repair"]["missing_observation"] == "branch_instruction"
    assert latest["hook_surface_coverage"]["post_entry_single_step"] is False
    assert latest["cross_candidate"]["return_target_trust"] == "suspicious"
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Run bounded post-entry step runtime audit"


def test_project_state_indexes_compare_handoff_post_entry_step_runtime_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_post_entry")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_post_entry_step_runtime_audit.json",
        {
            "artifact_kind": "compare_handoff_post_entry_step_runtime_audit",
            "classification": "step_api_unavailable",
            "overall_classification": "step_api_unavailable",
            "source_run": "sr_post_entry",
            "source_artifacts": [
                "compare_handoff_hook_surface_repair_audit",
                "compare_handoff_branch_operand_runtime_audit",
                "compare_handoff_edge_operand_provenance_audit",
            ],
            "candidate_count": 3,
            "runtime_sidecar_executed": False,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "runtime_scope": {
                "sidecar": "compare_handoff_post_entry_step_audit.py",
                "max_steps_per_candidate": 32,
                "material_capture_allowed": False,
                "crypto_hook_allowed": False,
                "breakpoint_probe_allowed": False,
            },
            "diagnostic_summary": {
                "blocker_counts": {"step_api_unavailable": 3},
                "debugger_backend_counts": {"frida": 3},
                "breakpoint_install_attempted_count": 0,
                "breakpoint_install_ok_count": 0,
                "breakpoint_hit_count": 0,
                "step_api_available_count": 0,
                "artifact_parse_error_count": 0,
            },
            "environment_diagnostics": {
                "debugger_backend": "frida",
                "backend_import_ok": True,
                "target_executable_exists": True,
            },
            "breakpoint_installation_diagnostics": {
                "predecessor_handoff_call": {
                    "address": "0x2338",
                    "install_attempted": False,
                    "install_ok": False,
                    "hit": False,
                    "error": "",
                },
                "handoff_helper_entry": {
                    "address": "0x1b50",
                    "install_attempted": False,
                    "install_ok": False,
                    "hit": False,
                    "error": "",
                },
            },
            "single_step_diagnostics": {
                "step_attempted": False,
                "step_api_available": False,
                "step_count": 0,
                "first_step_eip": "",
                "last_step_eip": "",
                "error": "no local stepping implementation",
            },
            "artifact_parse_diagnostics": {
                "raw_log_path": "",
                "raw_log_exists": False,
                "parse_attempted": False,
                "parse_ok": False,
                "parse_error": "",
            },
            "cross_candidate": {
                "first_divergence_point": "",
                "branch_guard_explained": False,
                "return_target_trust": "suspicious",
                "root_cause_classification": "step_api_unavailable",
                "next_bounded_action": "narrower_post_entry_breakpoint",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "post_entry_events": [],
                    "branch_observation": {"classification": "step_api_unavailable"},
                    "return_target_observation": {"trust": "instrumentation_gap"},
                    "post_entry_outcome": "step_api_unavailable",
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "narrower_post_entry_breakpoint",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_post_entry",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_post_entry_step_runtime_audit"].endswith(
        "compare_handoff_post_entry_step_runtime_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_post_entry_step_runtime_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == "step_api_unavailable"
    latest = current_state["latest_compare_handoff_post_entry_step_runtime_audit"]
    assert latest["classification"] == "step_api_unavailable"
    assert latest["candidate_count"] == 3
    assert latest["runtime_scope"]["max_steps_per_candidate"] == 32
    assert latest["diagnostic_summary"]["blocker_counts"] == {"step_api_unavailable": 3}
    assert latest["environment_diagnostics"]["debugger_backend"] == "frida"
    assert latest["breakpoint_installation_diagnostics"]["handoff_helper_entry"]["address"] == (
        "0x1b50"
    )
    assert latest["single_step_diagnostics"]["step_api_available"] is False
    assert latest["cross_candidate"]["next_bounded_action"] == "narrower_post_entry_breakpoint"
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Repair bounded post-entry step instrumentation"


def test_project_state_indexes_compare_handoff_narrower_post_entry_breakpoint_audit(
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_narrower_post_entry")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_post_entry_step_runtime_audit.json",
        {
            "artifact_kind": "compare_handoff_post_entry_step_runtime_audit",
            "classification": "step_api_unavailable",
            "overall_classification": "step_api_unavailable",
            "source_run": "sr_narrower_post_entry",
            "candidate_count": 3,
            "breakpoint_probe_allowed": False,
        },
    )
    _write_json(
        artifacts_dir / "compare_handoff_narrower_post_entry_breakpoint_audit.json",
        {
            "artifact_kind": "compare_handoff_narrower_post_entry_breakpoint_audit",
            "lifecycle_schema_version": 1,
            "ui_trigger_schema_version": 1,
            "window_discovery_schema_version": 1,
            "classification": "window_discovery_timeout",
            "overall_classification": "window_discovery_timeout",
            "source_run": "sr_narrower_post_entry",
            "source_artifacts": [
                "compare_handoff_post_entry_step_runtime_audit",
                "compare_handoff_hook_surface_repair_audit",
                "compare_handoff_branch_operand_runtime_audit",
            ],
            "candidate_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "runtime_scope": {
                "mode": "narrower_post_entry_breakpoint",
                "debugger_backend": "frida",
                "single_step_required": False,
                "breakpoint_probe_allowed": False,
                "material_capture_allowed": False,
                "crypto_hook_allowed": False,
            },
            "breakpoint_plan": [
                {"name": "predecessor_handoff_call", "module_offset": "0x2338"},
                {"name": "handoff_helper_entry", "module_offset": "0x1b50"},
                {"name": "process_exception", "module_offset": "0x1913"},
                {"name": "actual_compare", "module_offset": "0x258c"},
            ],
            "diagnostic_summary": {
                "blocker_counts": {"entry_breakpoint_not_hit": 3},
                "target_launch_attempted_count": 3,
                "target_launch_ok_count": 3,
                "breakpoint_install_attempted_count": 12,
                "breakpoint_install_ok_count": 12,
                "breakpoint_hit_counts": {},
            },
            "lifecycle_diagnostics": {
                "classification": "entry_breakpoint_not_hit",
                "stage_counts": {
                    "sidecar_started": 3,
                    "breakpoint_install_ok": 3,
                    "observation_wait_finished_or_timeout": 3,
                },
                "last_confirmed_stages": {
                    "78d540b49c59077041414141414141": "observation_wait_finished_or_timeout"
                },
                "timeout_stages": {
                    "78d540b49c59077041414141414141": ""
                },
                "candidate_invocation_health": {
                    "78d540b49c59077041414141414141": {
                        "subprocess_returncode": 0,
                        "subprocess_timed_out": False,
                    }
                },
            },
            "ui_trigger_diagnostics": {
                "classification": "entry_breakpoint_not_hit_after_ui_trigger",
                "classification_counts": {"entry_breakpoint_not_hit_after_ui_trigger": 1},
                "last_ui_stages": {
                    "78d540b49c59077041414141414141": "entry_breakpoint_not_hit_after_ui_trigger"
                },
                "timeout_stages": {
                    "78d540b49c59077041414141414141": ""
                },
                "method_counts": {"invoke": 1, "invoke_returned": 1},
                "control_lookup_counts": {"input_lookup_ok": 1, "button_lookup_ok": 1},
                "post_trigger_observation": {
                    "entry_breakpoint_hit_count": 0,
                    "successor_breakpoint_hit_count": 0,
                },
            },
            "window_discovery_diagnostics": {
                "classification": "top_window_call_timeout",
                "classification_counts": {"top_window_call_timeout": 3},
                "last_window_stages": {
                    "78d540b49c59077041414141414141": "top_window_timeout"
                },
                "timeout_stages": {
                    "78d540b49c59077041414141414141": "top_window"
                },
                "pid_alive": {"78d540b49c59077041414141414141": True},
                "top_window_attempted_count": 3,
                "top_window_returned_count": 0,
                "window_inventory_attempted_count": 0,
                "window_inventory_returned_count": 0,
                "window_inventory_counts": {
                    "78d540b49c59077041414141414141": {
                        "window_count": 0,
                        "visible_window_count": 0,
                    }
                },
                "selected_window_available_count": 0,
                "candidate_windows": {"78d540b49c59077041414141414141": []},
            },
            "cross_candidate": {
                "classification": "window_discovery_timeout",
                "first_divergence_after": "",
                "breakpoint_hit_counts": {},
                "lifecycle_stage_counts": {
                    "sidecar_started": 3,
                    "breakpoint_install_ok": 3,
                    "observation_wait_finished_or_timeout": 3,
                },
                "next_bounded_action": "review_narrower_post_entry_breakpoint_result",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "target_launch": {"attempted": True, "ok": True, "pid": 1234, "error": ""},
                    "breakpoints": [
                        {
                            "name": "handoff_helper_entry",
                            "module_offset": "0x1b50",
                            "install_attempted": True,
                            "install_ok": True,
                            "hit": False,
                            "hit_order": None,
                            "eip": "",
                            "error": "",
                        }
                    ],
                    "event_sequence": [],
                    "handoff_helper_entry_observed": False,
                    "successor_surface_observed": False,
                    "classification": "entry_breakpoint_not_hit",
                    "lifecycle_schema_version": 1,
                    "ui_trigger_schema_version": 1,
                    "window_discovery_schema_version": 1,
                    "lifecycle": {
                        "last_confirmed_stage": "observation_wait_finished_or_timeout",
                        "last_error_stage": "",
                        "timeout_stage": "",
                        "stages": [
                            {"stage": "sidecar_started", "status": "confirmed"},
                            {"stage": "breakpoint_install_ok", "status": "confirmed"},
                            {
                                "stage": "observation_wait_finished_or_timeout",
                                "status": "confirmed",
                            },
                        ],
                    },
                    "ui_trigger": {
                        "classification": "entry_breakpoint_not_hit_after_ui_trigger",
                        "last_ui_stage": "entry_breakpoint_not_hit_after_ui_trigger",
                        "timeout_stage": "",
                        "input_control": {"lookup_ok": True, "set_text_ok": True},
                        "button_control": {"lookup_ok": True, "enabled": True, "visible": True},
                        "trigger_methods": [
                            {"method": "invoke", "attempted": True, "returned": True}
                        ],
                        "post_trigger_observation": {
                            "entry_breakpoint_hit": False,
                            "successor_breakpoint_hit": False,
                        },
                    },
                    "window_discovery": {
                        "classification": "top_window_call_timeout",
                        "last_window_stage": "top_window_timeout",
                        "timeout_stage": "top_window",
                        "process_liveness": {"pid": 1234, "alive": True, "error": ""},
                        "top_window": {
                            "attempted": True,
                            "returned": False,
                            "duration_ms": 250,
                            "error": "timeout",
                        },
                        "window_inventory": {
                            "attempted": False,
                            "returned": False,
                            "window_count": 0,
                            "visible_window_count": 0,
                            "candidate_windows": [],
                        },
                        "selected_window": {"available": False},
                    },
                    "candidate_invocation_health": {
                        "subprocess_returncode": 0,
                        "subprocess_timed_out": False,
                    },
                }
            ],
            "candidate_generation_changed": False,
            "ranking_changed": False,
            "search_budget_changed": False,
            "beam_budget_topn_timeout_frontier_limit_expanded": False,
            "breakpoint_probe_allowed": False,
            "material_capture_allowed": False,
            "crypto_hook_allowed": False,
            "next_bounded_action": "review_narrower_post_entry_breakpoint_result",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_narrower_post_entry",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    assert artifact_index["latest_artifacts"][
        "compare_handoff_narrower_post_entry_breakpoint_audit"
    ].endswith("compare_handoff_narrower_post_entry_breakpoint_audit.json")
    assert artifact_index["latest_artifacts_v2"][
        "compare_handoff_narrower_post_entry_breakpoint_audit"
    ]["freshness"] == "current"
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_narrower_post_entry_breakpoint_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == "top_window_call_timeout"
    latest = current_state["latest_compare_handoff_narrower_post_entry_breakpoint_audit"]
    assert latest["classification"] == "top_window_call_timeout"
    assert latest["candidate_count"] == 3
    assert len(latest["fixed_candidates"]) == 3
    assert latest["runtime_scope"]["single_step_required"] is False
    assert latest["diagnostic_summary"]["breakpoint_install_ok_count"] == 12
    assert latest["lifecycle_schema_version"] == 1
    assert latest["ui_trigger_schema_version"] == 1
    assert latest["window_discovery_schema_version"] == 1
    assert latest["lifecycle_diagnostics"]["stage_counts"]["breakpoint_install_ok"] == 3
    assert latest["ui_trigger_diagnostics"]["classification"] == (
        "entry_breakpoint_not_hit_after_ui_trigger"
    )
    assert latest["window_discovery_diagnostics"]["classification"] == "top_window_call_timeout"
    assert latest["window_discovery_diagnostics"]["top_window_attempted_count"] == 3
    assert latest["candidates"][0]["window_discovery"]["last_window_stage"] == "top_window_timeout"
    assert latest["candidates"][0]["ui_trigger"]["trigger_methods"][0]["method"] == "invoke"
    assert latest["lifecycle_diagnostics"]["candidate_invocation_health"][
        "78d540b49c59077041414141414141"
    ]["subprocess_returncode"] == 0
    assert latest["breakpoint_plan"][1]["module_offset"] == "0x1b50"
    assert latest["breakpoint_probe_allowed"] is False
    assert current_state["latest_compare_handoff_post_entry_step_runtime_audit"][
        "classification"
    ] == "step_api_unavailable"


def test_project_state_projects_window_api_attribution_blocker(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_window_api")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    attribution = {
        "pywinauto_win32": {
            "attempted": True,
            "returned": False,
            "window_count": 0,
            "visible_window_count": 0,
            "owned_window_count": 0,
        },
        "pywinauto_uia": {
            "attempted": True,
            "returned": False,
            "window_count": 0,
            "visible_window_count": 0,
            "owned_window_count": 0,
        },
        "direct_enum_windows": {
            "attempted": True,
            "returned": True,
            "window_count": 1,
            "visible_window_count": 1,
            "owned_window_count": 1,
            "candidate_windows": [
                {
                    "handle": "101",
                    "title": "samplereverse",
                    "class_name": "Window",
                    "visible": True,
                    "enabled": True,
                    "owned_by_pid": True,
                }
            ],
        },
        "final_window_discovery_reason": "win32_enum_windows_succeeded_pywinauto_failed",
    }
    _write_json(
        artifacts_dir / "compare_handoff_narrower_post_entry_breakpoint_audit.json",
        {
            "artifact_kind": "compare_handoff_narrower_post_entry_breakpoint_audit",
            "lifecycle_schema_version": 1,
            "ui_trigger_schema_version": 1,
            "window_discovery_schema_version": 1,
            "classification": "win32_enum_windows_succeeded_pywinauto_failed",
            "overall_classification": "win32_enum_windows_succeeded_pywinauto_failed",
            "source_run": "sr_window_api",
            "candidate_count": 3,
            "fixed_candidates": [
                "78d540b49c59077041414141414141",
                "5a3e7f46ddd474d041414141414141",
                "78d540b49c59076f41414141414141",
            ],
            "runtime_scope": {
                "mode": "narrower_post_entry_breakpoint",
                "debugger_backend": "frida",
                "single_step_required": False,
                "breakpoint_probe_allowed": False,
                "material_capture_allowed": False,
                "crypto_hook_allowed": False,
            },
            "window_discovery_diagnostics": {
                "classification": "win32_enum_windows_succeeded_pywinauto_failed",
                "classification_counts": {
                    "win32_enum_windows_succeeded_pywinauto_failed": 3
                },
                "pid_alive": {"78d540b49c59077041414141414141": True},
                "backend_attempted_counts": {
                    "pywinauto_win32": 3,
                    "pywinauto_uia": 3,
                    "direct_enum_windows": 3,
                },
                "backend_returned_counts": {
                    "pywinauto_win32": 0,
                    "pywinauto_uia": 0,
                    "direct_enum_windows": 3,
                },
                "window_api_attribution": {
                    "78d540b49c59077041414141414141": attribution
                },
            },
            "cross_candidate": {
                "classification": "win32_enum_windows_succeeded_pywinauto_failed",
                "window_discovery_classification_counts": {
                    "win32_enum_windows_succeeded_pywinauto_failed": 3
                },
                "next_bounded_action": "review_narrower_post_entry_breakpoint_result",
            },
            "candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "classification": "win32_enum_windows_succeeded_pywinauto_failed",
                    "window_discovery": {
                        "classification": "win32_enum_windows_succeeded_pywinauto_failed",
                        "process_liveness": {"pid": 1234, "alive": True, "error": ""},
                        "api_attribution": attribution,
                        "selected_window": {"available": False},
                    },
                }
            ],
            "breakpoint_probe_allowed": False,
            "material_capture_allowed": False,
            "crypto_hook_allowed": False,
            "next_bounded_action": "review_narrower_post_entry_breakpoint_result",
        },
    )

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="sr_window_api",
    )

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_compare_handoff_narrower_post_entry_breakpoint_audit"]
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_handoff_narrower_post_entry_breakpoint_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == (
        "win32_enum_windows_succeeded_pywinauto_failed"
    )
    assert latest["window_discovery_diagnostics"]["backend_returned_counts"][
        "direct_enum_windows"
    ] == 3
    assert latest["candidates"][0]["window_discovery"]["api_attribution"][
        "final_window_discovery_reason"
    ] == "win32_enum_windows_succeeded_pywinauto_failed"
    assert task_packet["task"] == "Review bounded window discovery diagnostics"


def test_project_state_indexes_compare_lhs_producer_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_lhs_prod")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_lhs_producer_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_lhs_producer_audit" / "compare_lhs_producer_audit.json",
        {
            "artifact_kind": "compare_lhs_producer_audit",
            "classification": "producer_window_rejected",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "checked_windows": [
                {
                    "hook_name": "pre_lhs_slot_store",
                    "module_offset": "0x253a",
                    "runtime_backed_count": 3,
                    "candidate_dependent": True,
                    "connects_to_compare_lhs": False,
                }
            ],
            "relations": {
                "slot_to_compare_arg": "rejected",
                "eax_to_slot": "rejected",
                "esi_to_compare_arg": "rejected",
                "helper_return_to_lhs": "rejected",
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "move earlier than 0x253a..0x258b",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_lhs_producer_audit"].endswith(
        "compare_lhs_producer_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_lhs_producer_audit"
    assert current_state["current_bottleneck"]["reason"] == "producer_window_rejected"
    latest = current_state["latest_compare_lhs_producer_audit"]
    assert latest["classification"] == "producer_window_rejected"
    assert latest["candidate_count"] == 3
    assert latest["runtime_backed_count"] == 3
    assert latest["relations"]["slot_to_compare_arg"] == "rejected"
    assert latest["breakpoint_probe_allowed"] is False
    assert any(item.get("scope") == "compare_lhs_producer_audit" for item in negative_results)


def test_project_state_indexes_compare_lhs_upstream_writer_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_lhs_upstream")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_lhs_upstream_writer_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_lhs_upstream_writer_audit" / "compare_lhs_upstream_writer_audit.json",
        {
            "artifact_kind": "compare_lhs_upstream_writer_audit",
            "classification": "candidate_dependent_upstream_observed",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "checked_writers": [
                {
                    "hook_name": "producer_post_transform_slot_reload",
                    "module_offset": "0x2325",
                    "runtime_backed_count": 3,
                    "candidate_dependent": True,
                    "connects_to_compare_lhs": False,
                    "connects_to_lhs_store": False,
                }
            ],
            "relations": {
                "slot_1168_to_lhs_store": "inconclusive",
                "slot_116c_to_lhs_store": "inconclusive",
                "upstream_to_compare_arg": "inconclusive",
            },
            "candidate_dependent_writers": [
                {"hook_name": "producer_post_transform_slot_reload", "module_offset": "0x2325"}
            ],
            "identified_writers": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "add relation audit",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_lhs_upstream_writer_audit"].endswith(
        "compare_lhs_upstream_writer_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_lhs_upstream_writer_audit"
    assert current_state["current_bottleneck"]["reason"] == "candidate_dependent_upstream_observed"
    latest = current_state["latest_compare_lhs_upstream_writer_audit"]
    assert latest["classification"] == "candidate_dependent_upstream_observed"
    assert latest["candidate_count"] == 3
    assert latest["runtime_backed_count"] == 3
    assert latest["candidate_dependent_writers"][0]["hook_name"] == "producer_post_transform_slot_reload"
    assert latest["breakpoint_probe_allowed"] is False
    assert any(item.get("scope") == "compare_lhs_upstream_writer_audit" for item in negative_results)


def test_project_state_indexes_compare_callsite_reanchor_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_callsite_reanchor")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_callsite_reanchor_and_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_callsite_reanchor_and_lhs_provenance_audit",
            "classification": "frame_anchor_rejected",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "caller_module_offset": "0x258c",
                "lhs_side": "arg0",
                "flag_side": "arg1",
                "lhs_preview_varies_by_candidate": True,
            },
            "frame_anchor": {
                "old_slot_ebp_minus_1170_valid": False,
                "old_slot_ebp_minus_1170_status": "rejected",
            },
            "provenance": {
                "candidate_dependent": False,
                "connects_to_compare_lhs": False,
                "producer_instruction": "",
                "producer_call": "",
                "evidence": [
                    {
                        "hook_name": "upstream_slot_1168_reload",
                        "candidate_dependent": True,
                        "connects_to_compare_lhs": False,
                    }
                ],
            },
            "relation_table": [{"field": "lhs_side", "status": "arg0"}],
            "identified_producers": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "narrow real lhs provenance",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_callsite_reanchor_and_lhs_provenance_audit"].endswith(
        "compare_callsite_reanchor_and_lhs_provenance_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == (
        "compare_callsite_reanchor_and_lhs_provenance_audit"
    )
    assert current_state["current_bottleneck"]["reason"] == "frame_anchor_rejected"
    latest = current_state["latest_compare_callsite_reanchor_and_lhs_provenance_audit"]
    assert latest["classification"] == "frame_anchor_rejected"
    assert latest["actual_compare"]["lhs_side"] == "arg0"
    assert latest["frame_anchor"]["old_slot_ebp_minus_1170_valid"] is False
    assert latest["provenance"]["evidence"][0]["hook_name"] == "upstream_slot_1168_reload"
    assert latest["breakpoint_probe_allowed"] is False
    assert any(
        item.get("scope") == "compare_callsite_reanchor_and_lhs_provenance_audit"
        for item in negative_results
    )


def test_project_state_indexes_compare_real_lhs_provenance_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_real_lhs")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "lhs_register_source_confirmed",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "caller_module_offset": "0x258c",
                "lhs_side": "arg0",
                "flag_side": "arg1",
                "lhs_preview_varies_by_candidate": True,
            },
            "frame_anchor": {
                "old_slot_ebp_minus_1170_valid": False,
                "old_slot_ebp_minus_1170_status": "rejected",
            },
            "relations": {
                "esi_to_compare_arg0": "confirmed",
                "old_frame_anchor_to_compare_arg0": "rejected",
            },
            "provenance": {
                "candidate_dependent": False,
                "connects_to_compare_lhs": False,
                "producer_instruction": "",
                "producer_call": "",
                "evidence": [
                    {
                        "hook_name": "pre_compare_lhs_push",
                        "candidate_dependent": True,
                        "connects_to_compare_lhs": True,
                    }
                ],
            },
            "relation_table": [{"field": "esi_to_compare_arg0", "status": "confirmed"}],
            "identified_producers": [],
            "next_producer_window": {"start_rva": "0x2559", "end_rva": "0x258b"},
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "hook ESI source",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_real_lhs_provenance_audit"].endswith(
        "compare_real_lhs_provenance_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_real_lhs_provenance_audit"
    assert current_state["current_bottleneck"]["reason"] == "lhs_register_source_confirmed"
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["classification"] == "lhs_register_source_confirmed"
    assert latest["actual_compare"]["lhs_side"] == "arg0"
    assert latest["relations"]["esi_to_compare_arg0"] == "confirmed"
    assert latest["next_producer_window"]["start_rva"] == "0x2559"
    assert latest["next_producer_window"]["end_rva"] == "0x258b"
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Trace ESI source window 0x2559..0x258b"
    assert any(item.get("scope") == "compare_real_lhs_provenance_audit" for item in negative_results)
    assert any("Base64/RC4 breakpoint probe" in item["direction"] for item in negative_results)


def test_project_state_routes_compare_real_lhs_last_writer(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_real_lhs_last_writer")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "last_writer_identified",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "caller_module_offset": "0x258c",
                "lhs_side": "arg0",
                "flag_side": "arg1",
                "lhs_preview_varies_by_candidate": True,
            },
            "last_writer_summary": {
                "runtime_backed_count": 3,
                "connects_to_actual_arg0": True,
                "candidate_dependent": True,
                "transform_material_backed": False,
            },
            "write_monitor_health": {
                "enabled": True,
                "followed_thread_count": 3,
                "raw_write_count": 24,
                "filtered_intersecting_write_count": 3,
            },
            "lhs_writer_classification_blocker": "",
            "last_writer_candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "module_offset": "0x2400",
                    "after_preview_matches_arg0": True,
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "validate bounded material hook from confirmed compare lhs last writer",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["classification"] == "last_writer_identified"
    assert latest["lhs_writer_classification_blocker"] == ""
    assert current_state["current_bottleneck"]["blocker"] == ""
    assert latest["last_writer_summary"]["runtime_backed_count"] == 3
    assert latest["write_monitor_health"]["raw_write_count"] == 24
    assert latest["last_writer_candidates"][0]["module_offset"] == "0x2400"
    assert task_packet["task"] == "Validate bounded material hook from confirmed compare lhs last writer"


def test_project_state_routes_compare_real_lhs_last_writer_incomplete(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_real_lhs_writer_incomplete")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "instrumentation_incomplete",
            "candidate_count": 3,
            "runtime_backed_count": 2,
            "actual_compare": {"entry_status": "inconclusive", "lhs_side": "arg0"},
            "last_writer_summary": {"runtime_backed_count": 0, "missing_candidates": ["candidate"]},
            "lhs_writer_classification_blocker": "runtime_compare_arg0_not_ready",
            "last_writer_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "fix compare lhs last-writer instrumentation before new semantic claims",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["classification"] == "instrumentation_incomplete"
    assert latest["lhs_writer_classification_blocker"] == "runtime_compare_arg0_not_ready"
    assert current_state["current_bottleneck"]["blocker"] == "runtime_compare_arg0_not_ready"
    assert latest["last_writer_summary"]["runtime_backed_count"] == 0
    assert task_packet["task"] == "Improve compare lhs last-writer instrumentation"


def test_project_state_derives_real_lhs_raw_write_blocker_from_current_artifact(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_real_lhs_writer_raw_gap")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "compare_lhs_runtime_backed_writer_missing",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "lhs_side": "arg0",
                "arg0_value_by_candidate": {"78d540b49c59077041414141414141": "0x35cd018"},
                "arg0_preview_by_candidate": {
                    "78d540b49c59077041414141414141": "46006c004464830d311c7010"
                },
            },
            "write_monitor_health": {
                "observed_candidate_count": 3,
                "enabled": True,
                "followed_thread_count": 3,
                "raw_write_count": 27,
                "filtered_intersecting_write_count": 0,
            },
            "last_writer_summary": {
                "actual_compare_arg0_runtime_backed": True,
                "raw_write_event_count": 27,
                "retained_write_count": 0,
                "missing_candidate_reasons": [
                    {
                        "candidate_hex": "78d540b49c59077041414141414141",
                        "reason": "raw_writes_observed_but_none_intersect_actual_arg0",
                        "raw_write_event_count": 9,
                        "nearest_non_intersecting_writes": [
                            {
                                "sequence": 5,
                                "address": "0xd9dcf4",
                                "size": 4,
                                "thread_id": "10576",
                                "module_offset": "0x7851680e",
                                "instruction": "mov dword ptr [ecx], eax",
                                "distance_to_arg0": 42136352,
                                "bounded_failure_reason": "write_before_arg0_window",
                            }
                        ],
                    }
                ],
            },
            "last_writer_candidates": [],
            "breakpoint_probe_allowed": False,
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["classification"] == "compare_lhs_runtime_backed_writer_missing"
    assert latest["lhs_writer_classification_blocker"] == "arg0_pointer_origin_untracked"
    assert latest["raw_write_gap_summary"]["write_monitor_target_source"] == "static_compare_callsite_arg0"
    assert current_state["current_bottleneck"]["blocker"] == "arg0_pointer_origin_untracked"


def test_project_state_derives_arg0_pointer_carrier_without_final_writer(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_real_lhs_arg0_carrier")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "compare_lhs_runtime_backed_writer_missing",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "caller_module_offset": "0x258c",
                "lhs_side": "arg0",
                "arg0_value_by_candidate": {
                    "78d540b49c59077041414141414141": "0x35cd018",
                    "5a3e7f46ddd474d041414141414141": "0x378cfd8",
                    "78d540b49c59076f41414141414141": "0x421d018",
                },
                "arg0_preview_by_candidate": {
                    "78d540b49c59077041414141414141": "46",
                    "5a3e7f46ddd474d041414141414141": "47",
                    "78d540b49c59076f41414141414141": "48",
                },
            },
            "write_monitor_health": {
                "observed_candidate_count": 3,
                "enabled": True,
                "followed_thread_count": 3,
                "raw_write_count": 27,
                "filtered_intersecting_write_count": 0,
            },
            "last_writer_summary": {
                "actual_compare_arg0_runtime_backed": True,
                "connects_to_actual_arg0": False,
                "raw_write_event_count": 27,
                "retained_write_count": 0,
            },
            "last_writer_candidates": [],
            "candidate_results": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "runtime_backed": True,
                    "hook_observations": [
                        {
                            "hook_name": "static_compare_callsite",
                            "module_offset": "0x258c",
                            "esi_ptr": "0x35cd018",
                            "compare_args": {
                                "args": [
                                    {"index": 0, "role": "arg0", "value": "0x35cd018", "preview_hex": "46"},
                                    {"index": 1, "role": "arg1", "value": "0x1141c4c", "preview_hex": "66"},
                                ]
                            },
                        }
                    ],
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "runtime_backed": True,
                    "hook_observations": [
                        {
                            "hook_name": "static_compare_callsite",
                            "module_offset": "0x258c",
                            "esi_ptr": "0x378cfd8",
                            "compare_args": {
                                "args": [
                                    {"index": 0, "role": "arg0", "value": "0x378cfd8", "preview_hex": "47"},
                                    {"index": 1, "role": "arg1", "value": "0x1141c4c", "preview_hex": "66"},
                                ]
                            },
                        }
                    ],
                },
                {
                    "candidate_hex": "78d540b49c59076f41414141414141",
                    "runtime_backed": True,
                    "hook_observations": [
                        {
                            "hook_name": "static_compare_callsite",
                            "module_offset": "0x258c",
                            "esi_ptr": "0x421d018",
                            "compare_args": {
                                "args": [
                                    {"index": 0, "role": "arg0", "value": "0x421d018", "preview_hex": "48"},
                                    {"index": 1, "role": "arg1", "value": "0x1141c4c", "preview_hex": "66"},
                                ]
                            },
                        }
                    ],
                },
            ],
            "breakpoint_probe_allowed": False,
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    trace = latest["arg0_pointer_origin_trace"]
    assert trace["classification"] == "carrier_identified_writer_missing"
    assert trace["carrier_identified_count"] == 3
    assert trace["final_writer_status"] == "missing"
    assert trace["rows"][0]["pre_compare_esi_equals_arg0"] is True
    final_trace = latest["arg0_final_data_writer_trace"]
    assert final_trace["classification"] == "final_writer_trace_schema_gap"
    assert final_trace["rows"][0]["final_writer_gap_reason"] == "bounded_pointer_chain_rows_missing"
    assert latest["lhs_writer_classification_blocker"] == "arg0_final_writer_trace_schema_gap"
    assert current_state["current_bottleneck"]["blocker"] == "arg0_final_writer_trace_schema_gap"
    assert task_packet["task"] == "Refine bounded actual arg0 final data writer trace"


def test_project_state_projects_arg0_final_data_writer_trace_blocker(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_arg0_final_writer_trace")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "compare_lhs_runtime_backed_writer_missing",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"entry_status": "confirmed", "lhs_side": "arg0"},
            "arg0_final_data_writer_trace": {
                "classification": "pointer_chain_identified_writer_missing",
                "pointer_carrier_is_final_writer": False,
                "pointer_write_is_final_data_writer": False,
                "rows": [
                    {
                        "candidate_hex": "78d540b49c59077041414141414141",
                        "pre_push_esi_equals_arg0": True,
                        "slot_writer_equals_reload_source": True,
                        "nearest_write_intersects_arg0": False,
                        "final_writer_status": "pointer_chain_identified_writer_missing",
                    }
                ],
            },
            "last_writer_candidates": [],
            "breakpoint_probe_allowed": False,
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["arg0_final_data_writer_trace"]["classification"] == "pointer_chain_identified_writer_missing"
    assert latest["lhs_writer_classification_blocker"] == "arg0_pointer_chain_identified_writer_missing"
    assert current_state["current_bottleneck"]["blocker"] == "arg0_pointer_chain_identified_writer_missing"


def _write_sidecar_blocker_artifact(
    artifacts_dir: Path,
    candidate_health: list[dict[str, object]],
) -> None:
    _write_json(
        artifacts_dir / "compare_real_lhs_provenance_audit.json",
        {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "inconclusive",
            "candidate_count": len(candidate_health),
            "runtime_backed_count": len(candidate_health),
            "actual_compare": {"entry_status": "confirmed", "observed_count": len(candidate_health)},
            "arg0_final_data_writer_trace": {
                "classification": "final_writer_trace_schema_gap",
                "rows": [
                    {
                        "candidate_hex": item["candidate_hex"],
                        "final_writer_status": "final_writer_trace_schema_gap",
                        "final_writer_gap_reason": "actual_compare_arg0_missing",
                    }
                    for item in candidate_health
                ],
            },
            "candidate_execution_health": candidate_health,
            "breakpoint_probe_allowed": False,
        },
    )


def _sidecar_health_row(candidate_hex: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "candidate_hex": candidate_hex,
        "scripted_hook_status": "scripted_hook_no_observations",
        "scripted_returncode": 124,
        "scripted_error": "timeout",
        "hook_install_status": "installed",
        "hook_count": 4,
        "requested_hook_count": 4,
        "script_load_status": "loaded",
        "js_top_level_seen": True,
        "js_hooks_installed_seen": True,
        "python_message_callback_registered_before_load": True,
        "python_message_count_total": 12,
        "python_message_decode_error_count": 0,
        "frida_message_error_count": 0,
        "hook_install_error_count": 0,
        "module_base_resolution_status": "resolved",
        "spawn_attach_resume_status": "resumed",
        "ui_trigger_status": "button_triggered",
        "ui_trigger_after_hooks_installed": True,
        "observation_count": 0,
        "post_ui_observation_count": 0,
        "hook_hit_counts_by_name": {},
        "compare_probe_fallback_used": True,
        "compare_probe_fallback_status": "compare_probe_fallback_captured_compare_args",
        "compare_probe_fallback_is_provenance": False,
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {"ui_trigger_after_hooks_installed": False},
            "hooks_not_ready_before_ui_trigger",
        ),
        ({}, "hook_installed_but_compare_call_not_reached_after_ui_trigger"),
        (
            {
                "hook_hit_counts_by_name": {"static_compare_callsite": 1},
                "python_message_decode_error_count": 1,
            },
            "message_bridge_dropped_observation",
        ),
        (
            {
                "hooks_ready_before_ui_trigger": False,
                "ui_trigger_timing_status": "hooks_ready_barrier_timeout_before_ui_trigger",
                "root_cause_hypothesis": "hooks_ready_barrier_missing_before_ui_trigger",
            },
            "hooks_not_ready_before_ui_trigger",
        ),
        (
            {
                "ui_trigger_after_hooks_installed": False,
                "hooks_ready_before_ui_trigger": True,
                "ui_trigger_timing_status": "hooks_ready_before_ui_trigger",
            },
            "compare_arg_payload_schema_gap",
        ),
        (
            {
                "ui_trigger_status": "not_triggered_hooks_ready_timeout",
                "ui_trigger_after_hooks_installed": False,
                "hooks_ready_before_ui_trigger": False,
                "ui_trigger_timing_status": "hooks_ready_barrier_timeout_before_ui_trigger",
                "timeout_or_wait_reason": "hooks_installed_not_observed_before_ui_trigger_within_existing_window",
            },
            "sidecar_runtime_precondition_failed",
        ),
        (
            {"ui_trigger_status": "not_triggered"},
            "ui_trigger_not_executed",
        ),
        (
            {
                "python_message_count_total": 0,
            },
            "message_bridge_dropped_observation",
        ),
        (
            {
                "ui_trigger_status": "",
                "ui_trigger_after_hooks_installed": False,
            },
            "inconclusive_with_missing_required_telemetry",
        ),
        (
            {"module_base_resolution_status": "unresolved"},
            "arg0_target_path_or_process_mismatch",
        ),
    ],
)
def test_project_state_projects_sidecar_observation_blocker(
    tmp_path: Path,
    overrides: dict[str, object],
    expected: str,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_sidecar_observation_blocker")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    candidates = [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]
    _write_sidecar_blocker_artifact(
        artifacts_dir,
        [_sidecar_health_row(candidate, **overrides) for candidate in candidates],
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    latest = current_state["latest_compare_real_lhs_provenance_audit"]
    assert latest["arg0_final_data_writer_trace"]["classification"] == "final_writer_trace_schema_gap"
    assert latest["sidecar_observation_blocker"] == expected
    assert latest["lhs_writer_classification_blocker"] == expected
    assert current_state["current_bottleneck"]["blocker"] == expected
    assert task_packet["task"] == "Diagnose sidecar observation delivery blocker"


def test_project_state_indexes_compare_esi_source_window_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_esi_source")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_esi_source_window_audit.json",
        {
            "artifact_kind": "compare_esi_source_window_audit",
            "classification": "pre_compare_branch_bypasses_repair",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {
                "entry_status": "confirmed",
                "caller_module_offset": "0x258c",
                "lhs_side": "arg0",
                "flag_side": "arg1",
            },
            "relations": {
                "actual_compare_arg0": "confirmed",
                "pre_compare_esi_to_arg0": "confirmed",
                "repair_path_observed": "rejected",
            },
            "window_rows": [
                {
                    "hook_name": "pre_compare_branch",
                    "observed_count": 3,
                    "connects_to_compare_lhs": False,
                }
            ],
            "relation_table": [{"field": "repair_path_observed", "status": "rejected"}],
            "identified_producers": [],
            "branch_summary": {
                "pre_compare_branch_observed_count": 3,
                "repair_call_observed_count": 0,
            },
            "next_producer_window": {"start_rva": "0x2559", "end_rva": "0x258b"},
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "trace initial ESI source",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert artifact_index["latest_artifacts"]["compare_esi_source_window_audit"].endswith(
        "compare_esi_source_window_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_esi_source_window_audit"
    assert current_state["current_bottleneck"]["reason"] == "pre_compare_branch_bypasses_repair"
    latest = current_state["latest_compare_esi_source_window_audit"]
    assert latest["classification"] == "pre_compare_branch_bypasses_repair"
    assert latest["relations"]["pre_compare_esi_to_arg0"] == "confirmed"
    assert latest["branch_summary"]["repair_call_observed_count"] == 0
    assert latest["next_producer_window"]["start_rva"] == "0x2559"
    assert latest["breakpoint_probe_allowed"] is False
    assert task_packet["task"] == "Investigate stalled ESI source window path"
    assert any(item.get("scope") == "compare_esi_source_window_audit" for item in negative_results)
    assert any("ESI source window" in item["direction"] for item in negative_results)


def test_build_generates_state_files_and_artifact_index(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    assert artifact_index["latest_harness_run"]
    assert artifact_index["latest_summary"].endswith("summary.json")
    assert len(artifact_index["latest_case_results"]) == 1
    assert artifact_index["latest_artifacts"]["frontier_summary"].endswith(
        "samplereverse_compare_aware_frontier_summary.json"
    )
    assert artifact_index["latest_artifacts"]["guided_pool_validation"].endswith(
        "samplereverse_compare_aware_guided_pool_validation.json"
    )


def test_artifact_index_v2_contains_source_run_freshness_and_hash(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="current_run")
    legacy_artifact = (
        reports_dir
        / "tool_artifacts"
        / "samplereverse_legacy_static"
        / "base64_rc4_static_point_discovery.json"
    )
    _write_json(
        legacy_artifact,
        {
            "artifact_kind": "base64_rc4_static_point_discovery",
            "classification": "legacy_static_context",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    latest_artifacts = artifact_index["latest_artifacts"]
    latest_artifacts_v2 = artifact_index["latest_artifacts_v2"]
    assert isinstance(latest_artifacts["frontier_summary"], str)

    summary = latest_artifacts_v2["summary"]
    summary_path = run_dir / "summary.json"
    assert summary["path"] == latest_artifacts["summary"]
    assert summary["kind"] == "summary"
    assert summary["source_run"] == "current_run"
    assert summary["freshness"] == "current"
    assert summary["size_bytes"] == summary_path.stat().st_size
    assert summary["sha256"] == _sha256_file(summary_path)
    assert summary["modified_at"].endswith("Z")

    frontier = latest_artifacts_v2["frontier_summary"]
    assert frontier["source_run"] == "current_run"
    assert frontier["freshness"] == "current"
    assert frontier["sha256"] == _sha256_file(Path(frontier["path"]))

    legacy = latest_artifacts_v2["base64_rc4_static_point_discovery"]
    assert legacy["source_run"] == "legacy_tool_artifacts"
    assert legacy["freshness"] == "stale"
    assert legacy["size_bytes"] == legacy_artifact.stat().st_size
    assert legacy["sha256"] == _sha256_file(legacy_artifact)

    missing = latest_artifacts_v2["compare_real_lhs_provenance_audit"]
    assert missing["path"] is None
    assert missing["source_run"] == ""
    assert missing["freshness"] == "missing"
    assert missing["sha256"] is None


def test_artifact_index_v2_marks_explicit_run_name_as_current(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    selected_run = _make_minimal_harness_run(reports_dir, run_name="selected_run")
    _make_minimal_harness_run(reports_dir, run_name="other_run")

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        run_name="selected_run",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    frontier = artifact_index["latest_artifacts_v2"]["frontier_summary"]
    assert artifact_index["latest_harness_run"] == str(selected_run)
    assert frontier["source_run"] == "selected_run"
    assert frontier["freshness"] == "current"
    assert all(
        item.get("source_run") != "other_run" or item.get("freshness") != "current"
        for item in artifact_index["latest_artifacts_v2"].values()
    )


def test_artifact_index_uses_case_artifact_manifest_when_present(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="manifest_run")
    manifest_artifact = run_dir / "reports" / "tool_artifacts" / "samplereverse" / "manifest_only.json"
    _write_json(
        manifest_artifact,
        {
            "classification": "compare_lhs_runtime_backed_writer_missing",
        },
    )
    _write_json(
        run_dir / "case_results" / "samplereverse.json",
        {
            "case_id": "samplereverse",
            "status": "completed_no_expected",
            "artifact_manifest": [
                {
                    "kind": "compare_real_lhs_provenance_audit",
                    "path": str(manifest_artifact),
                    "size_bytes": manifest_artifact.stat().st_size,
                    "sha256": _sha256_file(manifest_artifact),
                    "classification": "compare_lhs_runtime_backed_writer_missing",
                    "tool_name": "CompareRealLhsAudit",
                    "owner_profile": "samplereverse",
                    "strategy_name": "CompareAwareSearchStrategy",
                }
            ],
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    legacy_path = artifact_index["latest_artifacts"]["compare_real_lhs_provenance_audit"]
    manifest_entry = artifact_index["latest_artifacts_v2"]["compare_real_lhs_provenance_audit"]
    assert legacy_path == str(manifest_artifact)
    assert manifest_entry["path"] == str(manifest_artifact)
    assert manifest_entry["freshness"] == "current"
    assert manifest_entry["source_run"] == "manifest_run"
    assert manifest_entry["sha256"] == _sha256_file(manifest_artifact)


def test_artifact_index_falls_back_to_legacy_scan_without_case_artifact_manifest(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="legacy_scan_run")

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    frontier = artifact_index["latest_artifacts_v2"]["frontier_summary"]
    assert frontier["path"] == str(
        run_dir
        / "reports"
        / "tool_artifacts"
        / "samplereverse"
        / "samplereverse_compare_aware_frontier_summary.json"
    )
    assert frontier["freshness"] == "current"


def test_artifact_index_manifest_missing_path_marked_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="missing_manifest_run")
    missing_artifact = run_dir / "reports" / "tool_artifacts" / "samplereverse" / "missing_compare_probe.json"
    _write_json(
        run_dir / "case_results" / "samplereverse.json",
        {
            "case_id": "samplereverse",
            "status": "completed_no_expected",
            "artifact_manifest": [
                {
                    "kind": "compare_probe",
                    "path": str(missing_artifact),
                    "size_bytes": None,
                    "sha256": None,
                    "classification": "",
                    "tool_name": "CompareProbe",
                    "owner_profile": "samplereverse",
                    "strategy_name": "CompareAwareSearchStrategy",
                }
            ],
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    compare_probe = artifact_index["latest_artifacts_v2"]["compare_probe"]
    assert artifact_index["latest_artifacts"]["compare_probe"] == str(missing_artifact)
    assert compare_probe["path"] == str(missing_artifact)
    assert compare_probe["freshness"] == "missing"
    assert compare_probe["source_run"] == ""
    assert compare_probe["size_bytes"] is None
    assert compare_probe["sha256"] is None


def test_current_state_negative_results_model_gate_and_task_packet_are_generated(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    model_gate = _read_json(state_dir / "model_gate.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert current_state["active_strategy"] == "CompareAwareSearchStrategy"
    assert current_state["best_candidates"]["exact2"]["runtime_ci_exact_wchars"] == 2
    assert current_state["current_bottleneck"]["stage"] == "pair_pool"
    assert any(item["severity"] == "hard_block" for item in negative_results)
    assert model_gate["should_call_model"] is True
    assert model_gate["context_level"] == 2
    assert task_packet["task"] == "Generate next decision for exact1 pair_pool bottleneck"
    assert task_packet["sufficiency_check"]["has_runtime_validation"] is True
    assert task_packet["expected_gpt_output"] == "project_state/decision_packet.md"
    assert "do not commit full solve_reports directory" in task_packet["do_not_do"]


def test_current_state_has_identity_fields(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    assert current_state["schema_version"] == 2
    assert current_state["state_build_id"].startswith("state_")
    assert current_state["round_id"].startswith("round_")
    assert current_state["workflow_status"] == "REPORT_AVAILABLE"
    assert current_state["current_owner"] == "web_gpt"
    assert current_state["review_status"] == "PENDING_REVIEW"
    assert current_state["source_git_commit"]
    assert current_state["source_harness_run"] == "samplereverse_stalled"
    assert len(current_state["state_digest"]) == 64


def test_task_packet_has_based_on_state_digest(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["schema_version"] == 2
    assert task_packet["state_build_id"] == current_state["state_build_id"]
    assert task_packet["round_id"] == current_state["round_id"]
    assert task_packet["based_on_state_digest"] == current_state["state_digest"]


def test_task_packet_distinguishes_derived_task_from_active_decision(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    task_packet = _read_json(state_dir / "task_packet.json")
    assert task_packet["task"]
    assert task_packet["state_scope"] == "sample_state"
    assert task_packet["task_source"] == "derived_from_sample_artifacts"
    assert task_packet["derived_task"] == task_packet["task"]
    assert task_packet["active_decision_packet"] == "project_state/decision_packet.md"
    assert task_packet["execution_scope"] == "decision_packet_controls_current_round"
    assert task_packet["expected_gpt_output"] == "project_state/decision_packet.md"


def test_status_summary_includes_task_source_and_active_decision(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    summary = status_summary(state_dir=state_dir)
    assert summary["task_source"] == "derived_from_sample_artifacts"
    assert summary["derived_task"] == summary["task"]
    assert summary["active_decision_packet"] == "project_state/decision_packet.md"
    assert summary["execution_scope"] == "decision_packet_controls_current_round"

    assert main(["status", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "task_source: derived_from_sample_artifacts" in output
    assert "active_decision_packet: project_state/decision_packet.md" in output
    assert "execution_scope: decision_packet_controls_current_round" in output


def test_lint_decision_ok_for_approved_matching_current_state(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_matching",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["decision_id"] == "decision_matching"
    assert result["decision_status"] == "APPROVED"
    assert result["based_on_state_digest"] == current_state["state_digest"]
    assert result["current_state_digest"] == current_state["state_digest"]


def test_lint_decision_fails_when_decision_meta_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n\nLegacy file.\n", encoding="utf-8")

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "decision_meta missing" in result["errors"]


def test_lint_decision_fails_when_decision_status_template_only(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "decision status is TEMPLATE_ONLY, expected APPROVED" in result["errors"]


def test_lint_decision_fails_when_decision_status_draft(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        status="DRAFT",
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "decision status is DRAFT, expected APPROVED" in result["errors"]


def test_lint_decision_fails_when_decision_id_empty(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "decision_id missing" in result["errors"]


def test_lint_decision_fails_when_based_on_state_digest_empty(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest="",
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "based_on_state_digest missing" in result["errors"]


def test_lint_decision_fails_when_based_on_state_digest_mismatch(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest="0" * 64,
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "based_on_state_digest does not match current_state.state_digest" in result["errors"]


def test_lint_decision_cli_returns_zero_on_ok(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )

    assert main(["lint-decision", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "lint-decision: OK" in output
    assert "decision_status: APPROVED" in output
    assert "execution_scope: decision_packet_controls_current_round" in output
    assert "active_decision_packet: project_state/decision_packet.md" in output


def test_lint_decision_cli_returns_nonzero_on_failure(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    assert main(["lint-decision", "--state-dir", str(state_dir)]) == 1
    output = capsys.readouterr().out
    assert "lint-decision: FAILED" in output
    assert "error: decision status is TEMPLATE_ONLY, expected APPROVED" in output


def test_lint_decision_reports_execution_scope_and_active_decision_packet(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    task_packet["active_decision_packet"] = "project_state/other_decision.md"
    _write_json(state_dir / "task_packet.json", task_packet)
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is True
    assert result["execution_scope"] == "decision_packet_controls_current_round"
    assert result["active_decision_packet"] == "project_state/other_decision.md"
    assert result["warnings"] == [
        "decision_meta.skill_profiles missing; legacy decision compatibility mode",
        "task_packet.active_decision_packet is project_state/other_decision.md, expected project_state/decision_packet.md"
    ]


def test_lint_decision_accepts_active_skill_profile_from_registry(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(tmp_path)
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_skill_profile",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v2"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["skill_profiles"] == ["reverse-agent-iteration@v2"]
    assert result["parsed_skill_profiles"][0]["skill_name"] == "reverse-agent-iteration"


def test_lint_decision_fails_on_skill_profile_version_mismatch(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(tmp_path)
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v999"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "skill profile 'reverse-agent-iteration@v999' version mismatch: registry version is 2" in result["errors"]


def test_lint_decision_fails_on_unknown_skill_profile(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(tmp_path)
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["unknown-skill@v1"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "skill profile 'unknown-skill@v1' references unknown skill 'unknown-skill'" in result["errors"]
    assert "decision_meta.skill_profiles contains no valid active skill profiles" in result["errors"]


def test_lint_decision_fails_on_bad_skill_profile_format(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(tmp_path)
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["skill-name"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "invalid skill profile 'skill-name'; expected skill-name@vN" in result["errors"]


def test_lint_decision_warns_on_draft_skill_profile_for_approved_decision(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(tmp_path)
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v2-draft"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is True
    assert "draft skill profile 'reverse-agent-iteration@v2-draft' should not be used in APPROVED decisions" in result[
        "warnings"
    ]


def test_lint_decision_missing_skill_profiles_is_legacy_warning(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
    )

    result = lint_decision(state_dir)

    assert result["ok"] is True
    assert result["warnings"] == ["decision_meta.skill_profiles missing; legacy decision compatibility mode"]


def test_lint_decision_fails_when_registry_missing_for_declared_profile(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v2"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert any(error.startswith("skill registry not found:") for error in result["errors"])


def test_lint_decision_fails_when_registry_invalid_for_declared_profile(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    registry_path = tmp_path / ".codex-skills" / "registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text("{", encoding="utf-8")
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v2"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "skill registry is invalid JSON" in result["errors"][0]


def test_lint_decision_fails_on_inactive_skill_profile(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _write_skill_registry(
        tmp_path,
        {
            "reverse-agent-iteration": {
                "path": ".codex-skills/reverse-agent-iteration/SKILL.md",
                "status": "deprecated",
                "scope": "generic_workflow",
                "version": 2,
            }
        },
    )
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
        mainline="engineering_branch",
        skill_profiles=["reverse-agent-iteration@v2"],
    )

    result = lint_decision(state_dir)

    assert result["ok"] is False
    assert "skill profile 'reverse-agent-iteration@v2' references non-active skill 'reverse-agent-iteration' status='deprecated'" in result[
        "errors"
    ]


def _prepare_lint_report_state(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    assert isinstance(current_state, dict)
    _write_decision_packet(
        state_dir,
        decision_id="decision_report",
        round_id=str(current_state["round_id"]),
        based_on_state_build_id=str(current_state["state_build_id"]),
        based_on_state_digest=str(current_state["state_digest"]),
    )
    _write_codex_report(
        state_dir,
        report_id="report_ok",
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        files_changed=["reverse_agent/project_state.py"],
        tests_ran=["python -m pytest -q tests\\test_project_state.py"],
        generated_artifacts=["project_state/pytest_result.txt"],
    )
    _write_pytest_result(
        state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_report",
            "report_id": "report_ok",
            "round_id": str(current_state["round_id"]),
            "generated_at": "2026-05-23T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q tests\\test_project_state.py"],
        },
    )
    archive_round(state_dir=state_dir)
    return state_dir, current_state


def test_lint_report_ok_for_matching_success_report(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["report_id"] == "report_ok"
    assert result["report_status"] == "SUCCESS"
    assert result["acceptance_recommendation"] == "ACCEPTED"
    assert result["based_on_decision_id"] == "decision_report"
    assert result["decision_id"] == "decision_report"
    assert result["decision_report_id_match"] is True
    assert result["round_id"] == current_state["round_id"]
    assert result["current_state_round_id"] == current_state["round_id"]
    assert result["tests_ran_count"] == 1
    assert result["generated_artifacts_count"] == 1
    assert result["pytest_result_present"] is True
    assert result["report_tests_ran_count"] == 1
    assert result["pytest_result_tests_ran_count"] == 1
    assert result["pytest_result_tests_cover_report"] is True
    assert result["pytest_result_missing_report_tests"] == []


def test_status_summary_exposes_pytest_result_tests_ran_coverage(tmp_path: Path) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)

    summary = status_summary(state_dir=state_dir)

    assert summary["report_tests_ran_count"] == 1
    assert summary["pytest_result_tests_ran_count"] == 1
    assert summary["pytest_result_tests_cover_report"] is True
    assert summary["pytest_result_missing_report_tests"] == []


def test_status_summary_exposes_round_consistency_fields(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)

    summary = status_summary(state_dir=state_dir)

    assert summary["report_round_id"] == current_state["round_id"]
    assert summary["decision_round_id"] == current_state["round_id"]
    assert summary["current_state_round_id"] == current_state["round_id"]
    assert summary["current_state_scope"] == "sample_state"
    assert summary["report_decision_round_id_match"] is True
    assert summary["report_current_state_round_relation"] == "same"
    assert summary["round_manifest_present"] is True
    assert summary["archive_status"] == "archived"
    assert summary["round_manifest_path"].endswith("round_manifest.json")
    assert summary["round_manifest_files"] == [
        "codex_execution_report.md",
        "decision_packet.md",
        "pytest_result.txt",
        "round_manifest.json",
    ]
    assert summary["round_manifest_forbidden_files"] == []
    assert summary["round_manifest_required_files_missing"] == []


def test_lint_report_fails_when_report_summary_missing(tmp_path: Path) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)
    (state_dir / "codex_execution_report.md").write_text("# CODEX_EXECUTION_REPORT\n", encoding="utf-8")

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "codex_report_summary missing" in result["errors"]


def test_lint_report_fails_when_generated_artifacts_missing(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    payload = {
        "schema_version": 1,
        "report_id": "report_ok",
        "round_id": str(current_state["round_id"]),
        "based_on_decision_id": "decision_report",
        "status": "SUCCESS",
        "acceptance_recommendation": "ACCEPTED",
        "files_changed": ["reverse_agent/project_state.py"],
        "tests_ran": ["python -m pytest -q tests\\test_project_state.py"],
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "generated_artifacts missing" in result["errors"]


def test_lint_report_fails_when_report_status_template_only(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "codex_report_summary is TEMPLATE_ONLY" in result["errors"]


def test_lint_report_fails_when_report_id_empty(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        report_id="",
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "report_id missing" in result["errors"]


def test_lint_report_fails_when_based_on_decision_id_empty(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "based_on_decision_id missing" in result["errors"]


def test_lint_report_fails_when_based_on_decision_id_mismatch(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_other",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "based_on_decision_id does not match current decision_id" in result["errors"]


def test_lint_report_fails_when_success_report_has_empty_tests_ran(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        tests_ran=[],
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "SUCCESS report requires non-empty tests_ran" in result["errors"]


def test_lint_report_fails_when_success_report_has_empty_pytest_result(tmp_path: Path) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)
    (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "SUCCESS report requires non-empty pytest_result.txt" in result["errors"]


def test_lint_report_fails_when_summary_lists_have_wrong_type(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        files_changed="reverse_agent/project_state.py",
        tests_ran="python -m pytest -q",
        generated_artifacts="project_state/pytest_result.txt",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert "files_changed must be a list" in result["errors"]
    assert "tests_ran must be a list" in result["errors"]
    assert "generated_artifacts must be a list" in result["errors"]


def test_lint_report_allows_engineering_round_with_sample_state(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    engineering_round = "round_engineering"
    _write_decision_packet(
        state_dir,
        decision_id="decision_report",
        round_id=engineering_round,
        based_on_state_build_id=str(current_state["state_build_id"]),
        based_on_state_digest=str(current_state["state_digest"]),
    )
    _write_codex_report(
        state_dir,
        round_id=engineering_round,
        based_on_decision_id="decision_report",
    )
    _write_pytest_result(
        state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_report",
            "report_id": "report_test",
            "round_id": engineering_round,
            "generated_at": "2026-05-23T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q"],
        },
    )

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert "report round_id does not match current_state.round_id" not in result["warnings"]
    assert result["report_decision_round_id_match"] is True
    assert result["report_current_state_round_relation"] == "different_but_allowed_sample_state"
    assert result["archive_status"] == "not_archived"
    assert result["round_manifest_present"] is False
    assert result["round_manifest_files"] == []
    assert result["round_manifest_forbidden_files"] == []
    assert result["round_manifest_required_files_missing"] == []
    assert "report round not archived yet" in result["warnings"]


def test_lint_report_fails_when_decision_report_round_id_mismatches(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_decision_packet(
        state_dir,
        decision_id="decision_report",
        round_id="round_decision",
        based_on_state_build_id=str(current_state["state_build_id"]),
        based_on_state_digest=str(current_state["state_digest"]),
    )
    _write_codex_report(
        state_dir,
        round_id="round_report",
        based_on_decision_id="decision_report",
    )

    result = lint_report(state_dir)

    assert result["ok"] is False
    assert result["report_decision_round_id_match"] is False
    assert "report round_id does not match current decision round_id" in result["errors"]


def test_lint_report_reports_manifest_present_for_archived_round(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["report_current_state_round_relation"] == "same"
    assert result["archive_status"] == "archived"
    assert result["round_manifest_present"] is True
    assert result["round_manifest_files"] == [
        "codex_execution_report.md",
        "decision_packet.md",
        "pytest_result.txt",
        "round_manifest.json",
    ]
    assert result["round_manifest_forbidden_files"] == []
    assert result["round_manifest_required_files_missing"] == []
    assert result["round_manifest_warning"] == ""


def test_lint_report_classifies_git_diff_manifest_as_polluted(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    manifest_path = state_dir / "rounds" / str(current_state["round_id"]) / "round_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["files"]["git_diff.patch"] = {
        "source_path": None,
        "archived_path": str(manifest_path.parent / "git_diff.patch"),
        "sha256": "digest",
    }
    _write_json(manifest_path, manifest)

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["archive_status"] == "polluted"
    assert result["round_manifest_forbidden_files"] == ["git_diff.patch"]
    assert result["round_manifest_required_files_missing"] == []
    assert "round_manifest includes forbidden files: git_diff.patch" in result["warnings"]


def test_lint_report_classifies_state_snapshot_manifest_as_non_minimal(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    manifest_path = state_dir / "rounds" / str(current_state["round_id"]) / "round_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["files"]["current_state.json"] = {
        "source_path": str(state_dir / "current_state.json"),
        "archived_path": str(manifest_path.parent / "current_state.json"),
        "sha256": "digest",
    }
    _write_json(manifest_path, manifest)

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["archive_status"] == "non_minimal"
    assert result["round_manifest_forbidden_files"] == ["current_state.json"]
    assert result["round_manifest_required_files_missing"] == []
    assert "forbidden files: current_state.json" in result["round_manifest_warning"]


def test_lint_report_classifies_missing_required_archive_file_as_non_minimal(
    tmp_path: Path,
) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    manifest_path = state_dir / "rounds" / str(current_state["round_id"]) / "round_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["files"].pop("pytest_result.txt")
    _write_json(manifest_path, manifest)

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["archive_status"] == "non_minimal"
    assert result["round_manifest_forbidden_files"] == []
    assert result["round_manifest_required_files_missing"] == ["pytest_result.txt"]
    assert "missing required files: pytest_result.txt" in result["round_manifest_warning"]


def test_lint_report_warns_for_unclassified_round_relation(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    task_packet = _read_json(state_dir / "task_packet.json")
    task_packet.pop("state_scope", None)
    task_packet.pop("task_source", None)
    task_packet.pop("execution_scope", None)
    _write_json(state_dir / "task_packet.json", task_packet)
    _write_decision_packet(
        state_dir,
        decision_id="decision_report",
        round_id="round_other",
        based_on_state_build_id=str(current_state["state_build_id"]),
        based_on_state_digest=str(current_state["state_digest"]),
    )
    _write_codex_report(
        state_dir,
        round_id="round_other",
        based_on_decision_id="decision_report",
    )
    _write_pytest_result(
        state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_report",
            "report_id": "report_test",
            "round_id": "round_other",
            "generated_at": "2026-05-23T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q"],
        },
    )

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["current_state_scope"] == "unknown"
    assert result["report_current_state_round_relation"] == "different_unclassified"
    assert "report round_id differs from current_state.round_id and relation is unclassified" in result["warnings"]


def test_lint_report_warns_for_structured_non_success_report(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        status="PARTIAL",
        acceptance_recommendation="NEEDS_REVIEW",
        tests_ran=[],
    )

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert "report_status is PARTIAL" in result["warnings"]


def test_lint_report_warns_when_pytest_result_tests_do_not_cover_report(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    report_tests = [
        "python -m pytest -q tests\\test_project_state.py",
        "python -m reverse_agent.project_state lint-report --state-dir project_state",
    ]
    _write_codex_report(
        state_dir,
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        tests_ran=report_tests,
    )

    result = lint_report(state_dir)

    assert result["ok"] is True
    assert result["report_tests_ran_count"] == 2
    assert result["pytest_result_tests_ran_count"] == 1
    assert result["pytest_result_tests_cover_report"] is False
    assert result["pytest_result_missing_report_tests"] == [
        "python -m reverse_agent.project_state lint-report --state-dir project_state"
    ]
    assert "pytest_result tests_ran does not cover codex_report_summary.tests_ran" in result["warnings"]


def test_lint_report_cli_returns_zero_on_ok(tmp_path: Path, capsys) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)

    assert main(["lint-report", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "lint-report: OK" in output
    assert "report_status: SUCCESS" in output
    assert "decision_report_id_match: True" in output
    assert "pytest_result_present: True" in output
    assert "pytest_result_status: PASSED" in output
    assert "pytest_result_matches_report: True" in output
    assert "report_tests_ran_count: 1" in output
    assert "pytest_result_tests_ran_count: 1" in output
    assert "pytest_result_tests_cover_report: True" in output
    assert "pytest_result_missing_report_tests: []" in output
    assert "round_manifest_files: ['codex_execution_report.md', 'decision_packet.md', 'pytest_result.txt', 'round_manifest.json']" in output
    assert "round_manifest_forbidden_files: []" in output
    assert "round_manifest_required_files_missing: []" in output


def test_lint_report_cli_returns_nonzero_on_failure(tmp_path: Path, capsys) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)
    (state_dir / "codex_execution_report.md").write_text("# CODEX_EXECUTION_REPORT\n", encoding="utf-8")

    assert main(["lint-report", "--state-dir", str(state_dir)]) == 1
    output = capsys.readouterr().out
    assert "lint-report: FAILED" in output
    assert "error: codex_report_summary missing" in output


def test_parse_pytest_result_header_parses_summary() -> None:
    text = """```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_test",
  "report_id": "report_test",
  "round_id": "round_test",
  "generated_at": "2026-05-23T00:00:00Z",
  "status": "PASSED",
  "tests_ran": ["python -m pytest -q"]
}
```

pytest output
"""
    parsed = parse_pytest_result_header(text)

    assert parsed["status"] == "PASSED"
    assert parsed["decision_id"] == "decision_test"
    assert parsed["report_id"] == "report_test"
    assert parsed["round_id"] == "round_test"
    assert parsed["tests_ran"] == ["python -m pytest -q"]


def test_parse_pytest_result_header_handles_legacy() -> None:
    parsed = parse_pytest_result_header("pytest passed\n")

    assert parsed["status"] == "LEGACY_WITHOUT_HEADER"
    assert parsed["found"] is False


def test_validate_pytest_result_for_report_matches() -> None:
    report_summary = {
        "based_on_decision_id": "decision_test",
        "report_id": "report_test",
        "round_id": "round_test",
        "tests_ran": ["python -m pytest -q"],
    }
    pytest_text = """```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_test",
  "report_id": "report_test",
  "round_id": "round_test",
  "generated_at": "2026-05-23T00:00:00Z",
  "status": "PASSED",
  "tests_ran": ["python -m pytest -q"]
}
```
"""
    result = validate_pytest_result_for_report(pytest_text, report_summary)

    assert result["matches_report"] is True
    assert result["report_tests_ran_count"] == 1
    assert result["pytest_result_tests_ran_count"] == 1
    assert result["tests_ran_covers_report"] is True
    assert result["missing_report_tests"] == []
    assert result["errors"] == []


def test_validate_pytest_result_for_report_warns_on_missing_report_tests() -> None:
    report_summary = {
        "based_on_decision_id": "decision_test",
        "report_id": "report_test",
        "round_id": "round_test",
        "tests_ran": [
            "python -m pytest -q",
            "python -m reverse_agent.project_state status --state-dir project_state",
        ],
    }
    pytest_text = """```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_test",
  "report_id": "report_test",
  "round_id": "round_test",
  "generated_at": "2026-05-23T00:00:00Z",
  "status": "PASSED",
  "tests_ran": ["python -m pytest -q"]
}
```
"""
    result = validate_pytest_result_for_report(pytest_text, report_summary)

    assert result["matches_report"] is True
    assert result["tests_ran_covers_report"] is False
    assert result["missing_report_tests"] == [
        "python -m reverse_agent.project_state status --state-dir project_state"
    ]
    assert "pytest_result tests_ran does not cover codex_report_summary.tests_ran" in result["warnings"]
    assert result["errors"] == []


def test_validate_pytest_result_for_report_legacy_tests_coverage_unknown() -> None:
    report_summary = {
        "based_on_decision_id": "decision_test",
        "tests_ran": ["python -m pytest -q"],
    }

    result = validate_pytest_result_for_report("pytest passed\n", report_summary)

    assert result["status"] == "LEGACY_WITHOUT_HEADER"
    assert result["tests_ran_covers_report"] == "unknown"
    assert result["missing_report_tests"] == []
    assert "pytest_result_summary missing" in result["warnings"]


@pytest.mark.parametrize("tests_ran", [None, "python -m pytest -q", ["python -m pytest -q", 1]])
def test_validate_pytest_result_for_report_handles_missing_or_invalid_report_tests(tests_ran: object) -> None:
    report_summary = {
        "based_on_decision_id": "decision_test",
        "tests_ran": tests_ran,
    }
    pytest_text = """```json pytest_result_summary
{"schema_version": 1, "decision_id": "decision_test", "status": "PASSED", "tests_ran": ["python -m pytest -q"]}
```
"""

    result = validate_pytest_result_for_report(pytest_text, report_summary)

    assert result["tests_ran_covers_report"] == "unknown"
    assert result["missing_report_tests"] == []
    assert result["errors"] == []


def test_validate_pytest_result_for_report_mismatch() -> None:
    report_summary = {"based_on_decision_id": "decision_report"}
    pytest_text = """```json pytest_result_summary
{"schema_version": 1, "decision_id": "decision_other", "status": "PASSED", "tests_ran": ["python -m pytest -q"]}
```
"""
    result = validate_pytest_result_for_report(pytest_text, report_summary)

    assert result["matches_report"] is False
    assert "decision_id does not match" in " ".join(result["errors"])


def test_write_pytest_result_overwrites_existing_text(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_a",
            "report_id": "report_a",
            "round_id": "round_a",
            "generated_at": "2026-05-23T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q"],
        },
        body="old body\n",
    )
    write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_b",
            "report_id": "report_b",
            "round_id": "round_b",
            "generated_at": "2026-05-23T01:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q"],
        },
        body="new body\n",
    )

    content = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    assert "decision_b" in content
    assert "new body" in content
    assert "decision_a" not in content


def test_extract_decision_meta_json() -> None:
    meta = extract_markdown_json_block(
        """```json decision_meta
{"schema_version": 1, "decision_id": "decision_test", "status": "APPROVED"}
```

# DECISION_PACKET
""",
        "decision_meta",
    )

    assert meta["found"] is True
    assert meta["parse_error"] is None
    assert meta["decision_id"] == "decision_test"
    assert meta["status"] == "APPROVED"


def test_extract_codex_report_summary_json() -> None:
    meta = extract_markdown_json_block(
        """```json codex_report_summary
{"schema_version": 1, "report_id": "report_test", "status": "PARTIAL", "acceptance_recommendation": "NEEDS_REVIEW"}
```

# CODEX_EXECUTION_REPORT
""",
        "codex_report_summary",
    )

    assert meta["found"] is True
    assert meta["parse_error"] is None
    assert meta["report_id"] == "report_test"
    assert meta["status"] == "PARTIAL"


def test_missing_decision_meta_is_not_approved(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n\nLegacy file.\n", encoding="utf-8")

    meta = read_decision_meta(state_dir)

    assert meta["status"] == "UNKNOWN"
    assert meta["status"] != "APPROVED"


def test_missing_codex_report_summary_is_not_success(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    (state_dir / "codex_execution_report.md").write_text(
        "# CODEX_EXECUTION_REPORT\n\nLegacy report.\n",
        encoding="utf-8",
    )

    summary = read_codex_report_summary(state_dir)

    assert summary["status"] == "UNKNOWN"
    assert summary["status"] != "SUCCESS"


def test_invalid_markdown_json_meta_is_reported_without_crashing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    (state_dir / "decision_packet.md").write_text(
        """```json decision_meta
{"schema_version": 1, "status": "APPROVED"
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_status"] == "UNKNOWN"
    assert "invalid JSON" in summary["decision_parse_error"]


def test_status_summary_exposes_decision_and_report_status(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    (state_dir / "decision_packet.md").write_text(
        """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED"
}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        """```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_test",
  "based_on_decision_id": "decision_test",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW"
}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    summary = status_summary(state_dir=state_dir)
    assert summary["decision_status"] == "APPROVED"
    assert summary["decision_id"] == "decision_test"
    assert summary["decision_based_on_state_digest"] == "digest_test"
    assert summary["report_status"] == "PARTIAL"


def test_status_summary_reports_pytest_result_mismatch(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(state_dir, decision_id="decision_report")
    _write_codex_report(
        state_dir,
        report_id="report_ok",
        round_id="round_ok",
        based_on_decision_id="decision_report",
    )
    _write_pytest_result(
        state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_other",
            "report_id": "report_ok",
            "round_id": "round_ok",
            "generated_at": "2026-05-23T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["python -m pytest -q"],
        },
    )

    summary = status_summary(state_dir=state_dir)

    assert summary["pytest_result_decision_id"] == "decision_other"
    assert summary["pytest_result_matches_report"] is False


def test_status_summary_decision_ready_for_execution_when_digest_matches(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_ready",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_old")

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_state_digest_match"] is True
    assert summary["decision_consumed_by_report"] is False
    assert summary["decision_execution_state"] == "READY_FOR_EXECUTION"
    assert summary["decision_ready_for_execution"] is True


def test_status_summary_consumed_success_takes_priority_over_ready_when_report_matches(
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_consumed_ready",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_consumed_ready", status="SUCCESS")

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_state_digest_match"] is True
    assert summary["decision_consumed_by_report"] is True
    assert summary["decision_execution_state"] == "CONSUMED_BY_SUCCESS_REPORT"
    assert summary["decision_ready_for_execution"] is False


def test_status_summary_decision_consumed_by_success_report_when_digest_stale_but_report_matches(
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(
        state_dir,
        decision_id="decision_consumed",
        based_on_state_build_id="state_old",
        based_on_state_digest="digest_old",
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_consumed", status="SUCCESS")

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_state_digest_match"] is False
    assert summary["decision_consumed_by_report"] is True
    assert summary["decision_execution_state"] == "CONSUMED_BY_SUCCESS_REPORT"
    assert summary["decision_ready_for_execution"] is False


@pytest.mark.parametrize("report_status", ["PARTIAL", "FAILED", "BLOCKED"])
def test_status_summary_decision_consumed_by_non_success_report_when_digest_stale_but_report_matches(
    tmp_path: Path,
    report_status: str,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(
        state_dir,
        decision_id="decision_non_success",
        based_on_state_build_id="state_old",
        based_on_state_digest="digest_old",
    )
    _write_codex_report(
        state_dir,
        based_on_decision_id="decision_non_success",
        status=report_status,
        acceptance_recommendation="NEEDS_REVIEW",
    )

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_state_digest_match"] is False
    assert summary["decision_consumed_by_report"] is True
    assert summary["decision_execution_state"] == "CONSUMED_BY_NON_SUCCESS_REPORT"
    assert summary["decision_ready_for_execution"] is False


def test_status_summary_decision_stale_without_matching_report_when_digest_stale_and_report_differs(
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(
        state_dir,
        decision_id="decision_stale",
        based_on_state_build_id="state_old",
        based_on_state_digest="digest_old",
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_other", status="SUCCESS")

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_report_id_match"] is False
    assert summary["decision_state_digest_match"] is False
    assert summary["decision_consumed_by_report"] is False
    assert summary["decision_execution_state"] == "STALE_WITHOUT_MATCHING_REPORT"
    assert summary["decision_ready_for_execution"] is False


def test_status_summary_decision_template_or_unknown_for_template_decision(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    summary = status_summary(state_dir=state_dir)

    assert summary["decision_status"] == "TEMPLATE_ONLY"
    assert summary["decision_execution_state"] == "TEMPLATE_OR_UNKNOWN"
    assert summary["decision_ready_for_execution"] is False


def test_status_cli_prints_decision_execution_state(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_cli",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )

    assert main(["status", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "decision_state_digest_match: True" in output
    assert "decision_consumed_by_report: False" in output
    assert "decision_execution_state: READY_FOR_EXECUTION" in output
    assert "decision_ready_for_execution: True" in output
    assert "pytest_result_status: LEGACY_WITHOUT_HEADER" in output
    assert "pytest_result_matches_report: unknown" in output


def test_lint_handoff_ready_for_codex_when_decision_ready(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_ready_handoff",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_old")

    result = lint_handoff(state_dir)

    assert result["ok"] is True
    assert result["handoff_state"] == "READY_FOR_CODEX"
    assert result["decision_execution_state"] == "READY_FOR_EXECUTION"
    assert result["decision_ready_for_execution"] is True
    assert result["lint_decision_ok"] is True
    assert result["lint_report_ok"] is False
    assert "previous report ignored for READY_FOR_CODEX: based_on_decision_id does not match current decision_id" in result[
        "warnings"
    ]


def test_lint_handoff_review_complete_when_success_report_consumed(tmp_path: Path) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)

    result = lint_handoff(state_dir)

    assert result["ok"] is True
    assert result["handoff_state"] == "REVIEW_COMPLETE"
    assert result["decision_execution_state"] == "CONSUMED_BY_SUCCESS_REPORT"
    assert result["decision_ready_for_execution"] is False
    assert result["lint_report_ok"] is True


def test_lint_handoff_report_needs_review_for_non_success_report(tmp_path: Path) -> None:
    state_dir, current_state = _prepare_lint_report_state(tmp_path)
    _write_codex_report(
        state_dir,
        report_id="report_partial",
        round_id=str(current_state["round_id"]),
        based_on_decision_id="decision_report",
        status="PARTIAL",
        acceptance_recommendation="NEEDS_REVIEW",
        tests_ran=[],
    )

    result = lint_handoff(state_dir)

    assert result["ok"] is True
    assert result["handoff_state"] == "REPORT_NEEDS_REVIEW"
    assert result["decision_execution_state"] == "CONSUMED_BY_NON_SUCCESS_REPORT"
    assert "matching report is non-success and needs review" in result["warnings"]


def test_lint_handoff_fails_for_stale_without_matching_report(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(
        state_dir,
        decision_id="decision_stale_handoff",
        based_on_state_build_id="state_old",
        based_on_state_digest="digest_old",
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_old")

    result = lint_handoff(state_dir)

    assert result["ok"] is False
    assert result["handoff_state"] == "STALE_OR_MISMATCH"
    assert "decision is stale and has no matching report" in result["errors"]


def test_lint_handoff_fails_for_template_or_unknown_decision(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = lint_handoff(state_dir)

    assert result["ok"] is False
    assert result["handoff_state"] == "TEMPLATE_OR_UNKNOWN"
    assert "decision is template or unknown" in result["errors"]


def test_lint_handoff_cli_returns_zero_on_ready_for_codex(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    _write_decision_packet(
        state_dir,
        decision_id="decision_ready_cli",
        based_on_state_build_id=current_state["state_build_id"],
        based_on_state_digest=current_state["state_digest"],
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_old")

    assert main(["lint-handoff", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "lint-handoff: OK" in output
    assert "handoff_state: READY_FOR_CODEX" in output
    assert "decision_ready_for_execution: True" in output


def test_lint_handoff_cli_returns_zero_on_review_complete(tmp_path: Path, capsys) -> None:
    state_dir, _current_state = _prepare_lint_report_state(tmp_path)

    assert main(["lint-handoff", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "lint-handoff: OK" in output
    assert "handoff_state: REVIEW_COMPLETE" in output
    assert "decision_ready_for_execution: False" in output


def test_lint_handoff_cli_returns_nonzero_on_stale_mismatch(tmp_path: Path, capsys) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    _write_decision_packet(
        state_dir,
        decision_id="decision_stale_cli",
        based_on_state_build_id="state_old",
        based_on_state_digest="digest_old",
    )
    _write_codex_report(state_dir, based_on_decision_id="decision_old")

    assert main(["lint-handoff", "--state-dir", str(state_dir)]) == 1
    output = capsys.readouterr().out
    assert "lint-handoff: FAILED" in output
    assert "handoff_state: STALE_OR_MISMATCH" in output


def test_template_decision_and_report_are_template_only(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    decision = read_decision_meta(state_dir)
    report = read_codex_report_summary(state_dir)
    summary = status_summary(state_dir=state_dir)

    assert decision["status"] == "TEMPLATE_ONLY"
    assert report["status"] == "TEMPLATE_ONLY"
    assert summary["decision_status"] == "TEMPLATE_ONLY"
    assert summary["report_status"] == "TEMPLATE_ONLY"
    assert summary["decision_report_id_match"] is False


def test_ensure_state_layout_upgrades_legacy_default_templates(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    (state_dir / "decision_packet.md").write_text(
        """# DECISION_PACKET

## Goal
本轮只做什么。

## Current Evidence
当前证据摘要。

## Do Not Do
禁止重复方向。

## Files To Inspect
Codex 优先审计的文件。

## Required Audit
Codex 执行前必须确认的内容。

## Implementation Scope
允许修改哪些文件。

## Tests
必须运行哪些测试。

## Stop Conditions
遇到什么情况必须停止并报告。
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        """# CODEX_EXECUTION_REPORT

## Summary
本轮做了什么。

## Files Changed
修改文件列表。

## Audit Result
审计发现。

## Implementation
实际实现内容。

## Tests
运行的测试命令和结果。

## Generated State Files
生成了哪些 project_state 文件。

## Problems / Uncertainty
仍然不确定的地方。

## Next Suggested Task
下一轮建议。
""",
        encoding="utf-8",
    )

    ensure_state_layout(state_dir)

    decision_text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    report_text = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")
    assert "```json decision_meta" in decision_text
    assert "```json codex_report_summary" in report_text
    assert read_decision_meta(state_dir)["status"] == "TEMPLATE_ONLY"
    assert read_codex_report_summary(state_dir)["status"] == "TEMPLATE_ONLY"


def test_handoff_consistency_is_false_for_missing_or_mismatched_report_decision_id(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    (state_dir / "decision_packet.md").write_text(
        """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_expected",
  "status": "APPROVED"
}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        """```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_empty_binding",
  "based_on_decision_id": "",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED"
}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    empty_binding = status_summary(state_dir=state_dir)
    assert empty_binding["decision_report_id_match"] is False
    assert empty_binding["handoff_consistency"]["report_based_on_decision_id"] == ""

    (state_dir / "codex_execution_report.md").write_text(
        """```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_mismatched_binding",
  "based_on_decision_id": "decision_other",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED"
}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    mismatch = status_summary(state_dir=state_dir)
    assert mismatch["decision_report_id_match"] is False
    assert mismatch["handoff_consistency"]["decision_id"] == "decision_expected"
    assert mismatch["handoff_consistency"]["report_based_on_decision_id"] == "decision_other"


def test_task_packet_does_not_cache_handoff_status(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    task_packet = _read_json(state_dir / "task_packet.json")
    assert "handoff_status" not in task_packet
    assert task_packet["active_decision_packet"] == "project_state/decision_packet.md"
    assert task_packet["task_source"] == "derived_from_sample_artifacts"
    assert task_packet["execution_scope"] == "decision_packet_controls_current_round"
    assert task_packet["expected_gpt_output"] == "project_state/decision_packet.md"


def test_status_summary_reads_live_handoff_status_after_task_packet_build(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    task_packet = _read_json(state_dir / "task_packet.json")
    assert "handoff_status" not in task_packet
    (state_dir / "codex_execution_report.md").write_text(
        """```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_live_after_build",
  "based_on_decision_id": "decision_live_after_build",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED"
}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    summary = status_summary(state_dir=state_dir)
    assert summary["report_status"] == "SUCCESS"
    assert summary["report_acceptance_recommendation"] == "ACCEPTED"
    assert summary["report_id"] == "report_live_after_build"
    assert summary["report_based_on_decision_id"] == "decision_live_after_build"


def test_state_digest_is_stable_for_same_inputs(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    first_digest = _read_json(state_dir / "current_state.json")["state_digest"]
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    second_digest = _read_json(state_dir / "current_state.json")["state_digest"]

    assert second_digest == first_digest


def test_state_digest_changes_when_current_state_changes(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    first_digest = _read_json(state_dir / "current_state.json")["state_digest"]
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_frontier_summary.json",
        {
            "frontier_active_lane": "frontier_exact1",
            "frontier_stall_stage": "changed_stage",
            "frontier_exact1_stall_reason": "changed_reason",
            "frontier_converged_reason": "changed_reason",
            "frontier_anchor_candidates": [],
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    second_digest = _read_json(state_dir / "current_state.json")["state_digest"]

    assert second_digest != first_digest


def test_task_packet_omits_full_progress_log_and_full_solve_reports(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    progress_log = tmp_path / "PROJECT_PROGRESS_LOG.txt"
    progress_log.write_text("VERY_LONG_SECRET_PROGRESS_LOG_SENTINEL", encoding="utf-8")
    _make_minimal_harness_run(reports_dir)

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        progress_log=progress_log,
    )

    packet_text = (state_dir / "task_packet.json").read_text(encoding="utf-8")
    assert "VERY_LONG_SECRET_PROGRESS_LOG_SENTINEL" not in packet_text
    assert "SOLVE_REPORTS_FULL_SENTINEL" not in packet_text
    task_packet = _read_json(state_dir / "task_packet.json")
    assert "artifact_refs" in task_packet
    assert any(item["name"] == "full solve_reports" for item in task_packet["omitted"])


def test_model_gate_returns_false_when_artifacts_are_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = reports_dir / "harness_runs" / "incomplete"
    _write_json(run_dir / "summary.json", {"run_name": "incomplete", "error_cases": 0})
    _write_json(run_dir / "run_manifest.json", {"run_name": "incomplete", "status": "completed"})
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "completed_no_expected"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert model_gate["should_call_model"] is False
    assert model_gate["next_local_action"] == "collect_artifacts"
    assert task_packet["task"] == "collect_missing_evidence"
    assert "frontier_summary" in model_gate["missing_evidence"]


def test_windows_path_style_outputs_are_compatible(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(
        reports_dir=Path(str(reports_dir)),
        state_dir=Path(str(state_dir)),
        sample="samplereverse",
        run_name="samplereverse_stalled",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    assert Path(artifact_index["latest_summary"]).name == "summary.json"
    assert Path(artifact_index["latest_artifacts"]["frontier_summary"]).name == (
        "samplereverse_compare_aware_frontier_summary.json"
    )


def test_new_round_status_and_archive_round_create_expected_files(tmp_path: Path, capsys) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    assert main(["status", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "latest_harness_run:" in output
    assert "expected_gpt_output:" in output

    result = archive_round(state_dir=state_dir)
    current_state = _read_json(state_dir / "current_state.json")
    round_dir = state_dir / "rounds" / current_state["round_id"]
    assert result["round_id"] == current_state["round_id"]
    assert result["status"] == "created"
    assert round_dir.exists()
    assert (round_dir / "decision_packet.md").exists()
    assert (round_dir / "codex_execution_report.md").exists()
    assert (round_dir / "pytest_result.txt").exists()
    assert (round_dir / "round_manifest.json").exists()
    assert not (round_dir / "current_state.json").exists()
    assert not (round_dir / "artifact_index.json").exists()
    assert not (round_dir / "negative_results.json").exists()
    assert not (round_dir / "model_gate.json").exists()
    assert not (round_dir / "task_packet.json").exists()
    assert not (round_dir / "git_diff.patch").exists()


def test_archive_round_writes_round_manifest(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir)
    manifest = _read_json(Path(result["round_dir"]) / "round_manifest.json")
    current_state = _read_json(state_dir / "current_state.json")

    assert manifest["schema_version"] == 1
    assert manifest["round_id"] == current_state["round_id"]
    assert manifest["source_git_commit"]
    assert manifest["source_git_commit"] != "593499f29508"
    assert manifest["source_harness_run"] == current_state["source_harness_run"]
    assert manifest["state_build_id"] == current_state["state_build_id"]
    assert manifest["state_digest"] == current_state["state_digest"]
    assert manifest["workflow_status"] == "REPORT_AVAILABLE"
    assert manifest["archive_mode"] == "minimal"
    assert manifest["included_diff"] is False
    assert manifest["included_state_snapshot"] is False
    assert "git_diff.patch" in manifest["omitted_files"]
    assert "current_state.json" in manifest["omitted_files"]


def test_build_project_state_records_git_commit_from_non_repo_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()
    _make_minimal_harness_run(reports_dir)
    monkeypatch.chdir(outside_cwd)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    expected_commit = subprocess.check_output(
        ["git", "-C", str(Path(__file__).resolve().parents[1]), "rev-parse", "--short=12", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()
    assert current_state["source_git_commit"] == expected_commit


def test_round_manifest_contains_expected_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir)
    manifest = _read_json(Path(result["round_dir"]) / "round_manifest.json")

    assert {
        "decision_packet.md",
        "codex_execution_report.md",
        "pytest_result.txt",
    }.issubset(set(manifest["files"]))


def test_round_manifest_file_digests_match(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir)
    round_dir = Path(result["round_dir"])
    manifest = _read_json(round_dir / "round_manifest.json")

    for name, info in manifest["files"].items():
        archived_path = Path(info["archived_path"])
        assert archived_path == round_dir / name
        assert archived_path.exists()
        assert info["sha256"] == _sha256_file(archived_path)


def test_round_manifest_records_source_and_archived_paths(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir)
    round_dir = Path(result["round_dir"])
    manifest = _read_json(round_dir / "round_manifest.json")

    for name in ("decision_packet.md", "codex_execution_report.md"):
        info = manifest["files"][name]
        assert info["source_path"] == str(state_dir / name)
        assert info["archived_path"] == str(round_dir / name)
    assert manifest["files"]["pytest_result.txt"]["source_path"] is None
    assert manifest["files"]["pytest_result.txt"]["archived_path"] == str(round_dir / "pytest_result.txt")


def test_archive_round_include_state_snapshot_archives_state_json(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir, include_state_snapshot=True)
    round_dir = Path(result["round_dir"])
    manifest = _read_json(round_dir / "round_manifest.json")

    assert manifest["archive_mode"] == "state_snapshot"
    assert manifest["included_state_snapshot"] is True
    assert manifest["included_diff"] is False
    assert (round_dir / "current_state.json").exists()
    assert (round_dir / "artifact_index.json").exists()
    assert (round_dir / "negative_results.json").exists()
    assert (round_dir / "model_gate.json").exists()
    assert (round_dir / "task_packet.json").exists()
    assert not (round_dir / "git_diff.patch").exists()


def test_archive_round_include_diff_archives_patch_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    result = archive_round(state_dir=state_dir, include_diff=True)
    round_dir = Path(result["round_dir"])
    manifest = _read_json(round_dir / "round_manifest.json")

    assert manifest["archive_mode"] == "minimal"
    assert manifest["included_state_snapshot"] is False
    assert manifest["included_diff"] is True
    assert (round_dir / "git_diff.patch").exists()
    assert not (round_dir / "current_state.json").exists()
def test_round_manifest_records_pytest_result_source_when_present(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    (state_dir / "pytest_result.txt").write_text("pytest passed\n", encoding="utf-8")

    result = archive_round(state_dir=state_dir)
    round_dir = Path(result["round_dir"])
    manifest = _read_json(round_dir / "round_manifest.json")

    assert manifest["files"]["pytest_result.txt"]["source_path"] == str(state_dir / "pytest_result.txt")
    assert manifest["files"]["pytest_result.txt"]["archived_path"] == str(round_dir / "pytest_result.txt")
    assert manifest["files"]["pytest_result.txt"]["sha256"] == _sha256_file(round_dir / "pytest_result.txt")


def test_archive_round_is_idempotent_for_same_round(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    first = archive_round(state_dir=state_dir)

    second = archive_round(state_dir=state_dir)

    assert second["round_id"] == first["round_id"]
    assert second["status"] == "no-op"
    assert _read_json(Path(first["round_dir"]) / "round_manifest.json") == _read_json(
        Path(second["round_dir"]) / "round_manifest.json"
    )


def test_archive_round_refuses_to_overwrite_changed_round(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    archive_round(state_dir=state_dir)
    (state_dir / "codex_execution_report.md").write_text("changed report\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="round manifest differs"):
        archive_round(state_dir=state_dir)


def test_archive_round_uses_incrementing_round_for_legacy_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    current_state = _read_json(state_dir / "current_state.json")
    current_state.pop("round_id", None)
    _write_json(state_dir / "current_state.json", current_state)
    archive_round(state_dir=state_dir)

    result = archive_round(state_dir=state_dir)

    assert result["round_id"] == "round_002"
    assert (state_dir / "rounds" / "round_002" / "decision_packet.md").exists()


def test_pack_contains_only_allowed_project_state_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    (reports_dir / "secret.exe").write_bytes(b"MZ")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    archive_round(state_dir=state_dir)
    out_path = tmp_path / "gpt_context_pack.zip"

    result = pack_context(state_dir=state_dir, out_path=out_path)

    assert out_path.exists()
    assert "project_state/task_packet.json" in result["files"]
    with zipfile.ZipFile(out_path) as archive:
        names = archive.namelist()
    assert "project_state/current_state.json" in names
    assert "project_state/decision_packet.md" in names
    assert not any(name.endswith("git_diff.patch") for name in names)
    assert not any(name.startswith("solve_reports/") for name in names)
    assert not any(name.endswith(".exe") for name in names)
    assert ".env" not in names
