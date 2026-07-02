import json
from pathlib import Path

from reverse_agent.project_ci import (
    build_artifact_manifest_artifact,
    build_audit_handoff_bundle_artifact,
    build_observation_handoff_artifact,
    build_observation_reconcile_artifact,
    build_observation_schema_artifact,
    validate_observation_snapshot,
)


def _write_gate(state_dir: Path, name: str, payload: dict[str, object]) -> None:
    path = state_dir / "gates" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _current_gate(
    *,
    decision_id: str = "decision_ci",
    round_id: str = "round_ci",
    gate_status: str = "PASSED",
    **extra: object,
) -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "round_id": round_id,
        "gate_status": gate_status,
        **extra,
    }


def test_validate_observation_snapshot_accepts_complete_shape() -> None:
    payload = {
        "commit_sha": "abc123",
        "workflow_name": "State Gate",
        "run_id": "12345",
        "status": "completed",
        "conclusion": "success",
        "job_summaries": [{"name": "state-gate", "conclusion": "success"}],
        "observed_commands": ["python -m reverse_agent.project_gate final-check --state-dir project_state"],
        "artifacts": [{"name": "project-gate-evidence"}],
        "provenance": {"source": "manual export"},
    }

    result = validate_observation_snapshot(payload)

    assert result["status"] == "PASSED"
    assert result["errors"] == []
    assert result["normalized_snapshot"]["run_id"] == "12345"


def test_validate_observation_snapshot_rejects_missing_fields() -> None:
    result = validate_observation_snapshot({"workflow_name": "State Gate"})

    assert result["status"] == "FAILED"
    assert "missing required field: commit_sha" in result["errors"]
    assert "missing required field: provenance" in result["errors"]


def test_observation_schema_artifact_is_evidence_only() -> None:
    payload = build_observation_schema_artifact(
        decision_id="decision_ci",
        round_id="round_ci",
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_observation_schema_result.json",
        output_path="project_state/gates/ci_observation_schema_result.json",
    )

    assert payload["gate_status"] == "PASSED"
    assert payload["schema_status"] == "DEFINED"
    assert payload["can_dispatch"] is False
    assert "commit_sha" in payload["required_fields"]


def test_observation_handoff_without_snapshot_awaits_external_observation() -> None:
    payload = build_observation_handoff_artifact(
        decision_id="decision_ci",
        round_id="round_ci",
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_observation_handoff_packet.json",
        output_path="project_state/gates/ci_observation_handoff_packet.json",
        snapshot_payload=None,
        snapshot_path=None,
    )

    assert payload["gate_status"] == "PASSED"
    assert payload["observation_state"] == "AWAITING_EXTERNAL_OBSERVATION"
    assert payload["handoff_contract"]["dispatch_performed"] is False


def test_artifact_manifest_requires_read_only_upload_exports() -> None:
    workflow_texts = {
        ".github/workflows/state-gate.yml": """
permissions:
  contents: read
jobs:
  state-gate:
    steps:
      - uses: actions/upload-artifact@v4
        with:
          path: |
            project_state/gates/*.json
            project_state/pytest_result.txt
""",
    }

    payload = build_artifact_manifest_artifact(
        workflow_texts=workflow_texts,
        decision_id="decision_ci",
        round_id="round_ci",
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_artifact_manifest_result.json",
        output_path="project_state/gates/ci_artifact_manifest_result.json",
    )

    assert payload["gate_status"] == "PASSED"
    assert payload["manifest_status"] == "READY"
    assert payload["unsafe_patterns_found"] == []


def test_artifact_manifest_rejects_write_permissions_and_missing_exports(tmp_path: Path) -> None:
    workflow_path = tmp_path / "workflow.yml"
    workflow_path.write_text(
        """
permissions:
  contents: write
jobs:
  state-gate:
    steps:
      - run: git push origin main
""",
        encoding="utf-8",
    )

    payload = build_artifact_manifest_artifact(
        workflow_texts={".github/workflows/state-gate.yml": workflow_path.read_text(encoding="utf-8")},
        decision_id="decision_ci",
        round_id="round_ci",
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_artifact_manifest_result.json",
        output_path="project_state/gates/ci_artifact_manifest_result.json",
    )

    assert payload["gate_status"] == "FAILED"
    assert payload["unsafe_patterns_found"]
    assert any("artifact export expectations missing" in error for error in payload["errors"])


def test_reconcile_records_non_final_diagnostic_status_for_failed_execution_log(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision_id = "decision_ci"
    round_id = "round_ci"
    for key, name in {
        "ci_observation_schema": "ci_observation_schema_result.json",
        "ci_observation_handoff": "ci_observation_handoff_packet.json",
        "ci_run_evidence": "ci_run_evidence_result.json",
        "local_ci_parity": "local_ci_parity_result.json",
        "ci_workflow_coverage": "ci_workflow_coverage_result.json",
        "ci_workflow_readiness": "ci_workflow_readiness_result.json",
        "command_plan": "command_plan.json",
        "report_summary": "report_summary_synthesis.json",
    }.items():
        payload = _current_gate(decision_id=decision_id, round_id=round_id)
        if key == "ci_observation_handoff":
            payload["observation_state"] = "AWAITING_EXTERNAL_OBSERVATION"
        _write_gate(state_dir, name, payload)
    _write_gate(
        state_dir,
        "execution_log.json",
        _current_gate(decision_id=decision_id, round_id=round_id, gate_status="FAILED"),
    )

    payload = build_observation_reconcile_artifact(
        state_dir=state_dir,
        decision_id=decision_id,
        round_id=round_id,
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_observation_reconcile_result.json",
        output_path="project_state/gates/ci_observation_reconcile_result.json",
        source_artifacts={
            "ci_observation_schema": "ci_observation_schema_result.json",
            "ci_observation_handoff": "ci_observation_handoff_packet.json",
            "ci_run_evidence": "ci_run_evidence_result.json",
            "local_ci_parity": "local_ci_parity_result.json",
            "ci_workflow_coverage": "ci_workflow_coverage_result.json",
            "ci_workflow_readiness": "ci_workflow_readiness_result.json",
            "command_plan": "command_plan.json",
            "execution_log": "execution_log.json",
            "report_summary": "report_summary_synthesis.json",
        },
    )

    assert payload["gate_status"] == "PASSED"
    assert payload["reconcile_status"] == "DIAGNOSTIC_GAPS_RECORDED"
    assert payload["final_consistency_status"] == "NON_FINAL_DIAGNOSTIC"
    assert payload["pending_diagnostic_sources"] == ["execution_log"]


def test_audit_bundle_requires_post_closeout_final_sources_for_ready(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    decision_id = "decision_ci"
    round_id = "round_ci"
    source_names = {
        "ci_observation_schema": "ci_observation_schema_result.json",
        "ci_observation_handoff": "ci_observation_handoff_packet.json",
        "ci_observation_reconcile": "ci_observation_reconcile_result.json",
        "ci_artifact_manifest": "ci_artifact_manifest_result.json",
        "ci_run_evidence": "ci_run_evidence_result.json",
        "local_ci_parity": "local_ci_parity_result.json",
        "ci_workflow_coverage": "ci_workflow_coverage_result.json",
        "ci_workflow_readiness": "ci_workflow_readiness_result.json",
        "report_summary": "report_summary_synthesis.json",
        "execution_log": "execution_log.json",
        "final_check": "final_gate_result.json",
        "run_closeout": "run_closeout_result.json",
    }
    for name in source_names.values():
        _write_gate(state_dir, name, _current_gate(decision_id=decision_id, round_id=round_id))
    _write_gate(
        state_dir,
        "final_gate_result.json",
        _current_gate(decision_id=decision_id, round_id=round_id, gate_status="FAILED"),
    )
    _write_gate(
        state_dir,
        "run_closeout_result.json",
        _current_gate(
            decision_id=decision_id,
            round_id=round_id,
            gate_status=None,
            closeout_status="IN_PROGRESS",
        ),
    )

    stale = build_audit_handoff_bundle_artifact(
        state_dir=state_dir,
        decision_id=decision_id,
        round_id=round_id,
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:00Z",
        artifact_name="ci_audit_handoff_bundle.json",
        output_path="project_state/gates/ci_audit_handoff_bundle.json",
        source_artifacts=source_names,
    )

    assert stale["gate_status"] == "PASSED"
    assert stale["handoff_status"] == "PENDING_DIAGNOSTIC_EVIDENCE"
    assert set(stale["audit_summary"]["pending_diagnostic_sources"]) == {
        "final_check",
        "run_closeout",
    }

    _write_gate(
        state_dir,
        "final_gate_result.json",
        _current_gate(decision_id=decision_id, round_id=round_id, gate_status="PASSED"),
    )
    _write_gate(
        state_dir,
        "run_closeout_result.json",
        _current_gate(
            decision_id=decision_id,
            round_id=round_id,
            gate_status=None,
            closeout_status="PASSED",
            close_round_result={"close_status": "CLOSED"},
        ),
    )
    ready = build_audit_handoff_bundle_artifact(
        state_dir=state_dir,
        decision_id=decision_id,
        round_id=round_id,
        report_id="codex_report_ci",
        generated_at="2026-07-02T00:00:01Z",
        artifact_name="ci_audit_handoff_bundle.json",
        output_path="project_state/gates/ci_audit_handoff_bundle.json",
        source_artifacts=source_names,
    )

    assert ready["handoff_status"] == "READY_FOR_AUDIT"
    assert ready["audit_summary"]["pending_diagnostic_sources"] == []
    assert ready["post_closeout_status"]["close_round_status"] == "CLOSED"
