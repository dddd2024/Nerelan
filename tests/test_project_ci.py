from pathlib import Path

from reverse_agent.project_ci import (
    build_artifact_manifest_artifact,
    build_observation_handoff_artifact,
    build_observation_schema_artifact,
    validate_observation_snapshot,
)


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
