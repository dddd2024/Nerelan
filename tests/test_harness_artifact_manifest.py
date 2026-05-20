import hashlib
import json
from pathlib import Path

from reverse_agent.evidence import StructuredEvidence
from reverse_agent.harness import HarnessCase, HarnessConfig, _load_case_result, run_harness
from reverse_agent.pipeline import SolveResult
from reverse_agent.tool_runners import ToolAutomationConfig, ToolRunArtifact


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_case_result_includes_artifact_manifest(tmp_path: Path, monkeypatch) -> None:
    reports_dir = tmp_path / "reports"

    def _fake_run_pipeline(**kwargs):  # noqa: ANN001
        artifact_path = reports_dir / "tool_artifacts" / "demo" / "compare_real_lhs_provenance_audit.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(
                {
                    "kind": "compare_real_lhs_provenance_audit",
                    "classification": "compare_lhs_runtime_backed_writer_missing",
                }
            ),
            encoding="utf-8",
        )
        return SolveResult(
            input_value=kwargs["input_value"],
            resolved_path=kwargs["input_value"],
            analysis_mode=kwargs["analysis_mode"],
            model_name="Copilot CLI",
            candidates=["NOT_FOUND"],
            selected_flag="NOT_FOUND",
            prompt="prompt",
            model_output="NOT_FOUND",
            extracted_strings_count=3,
            tool_artifacts=[
                ToolRunArtifact(
                    tool_name="CompareRealLhsAudit",
                    enabled=True,
                    attempted=True,
                    success=True,
                    output_path=str(artifact_path),
                    owner_profile="samplereverse",
                    strategy_name="CompareAwareSearchStrategy",
                )
            ],
            structured_evidence=[StructuredEvidence(kind="audit", source_tool="fake")],
            report_path=str(reports_dir / "demo.md"),
        )

    monkeypatch.setattr("reverse_agent.harness.run_pipeline", _fake_run_pipeline)

    run_harness(
        HarnessConfig(
            cases=[HarnessCase(case_id="demo", input_value="demo.exe")],
            reports_dir=reports_dir,
            run_name="manifest_suite",
            tool_config=ToolAutomationConfig(enabled=False),
        ),
        log=lambda _: None,
    )

    case_result = _read_json(reports_dir / "harness_runs" / "manifest_suite" / "case_results" / "demo.json")
    manifest = case_result["artifact_manifest"]
    assert len(manifest) == 1
    entry = manifest[0]
    artifact_path = Path(entry["path"])
    assert entry["kind"] == "compare_real_lhs_provenance_audit"
    assert entry["size_bytes"] == artifact_path.stat().st_size
    assert entry["sha256"] == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    assert entry["classification"] == "compare_lhs_runtime_backed_writer_missing"
    assert entry["tool_name"] == "CompareRealLhsAudit"
    assert entry["owner_profile"] == "samplereverse"
    assert entry["strategy_name"] == "CompareAwareSearchStrategy"


def test_case_result_artifact_manifest_handles_missing_or_invalid_artifact(tmp_path: Path, monkeypatch) -> None:
    reports_dir = tmp_path / "reports"

    def _fake_run_pipeline(**kwargs):  # noqa: ANN001
        invalid_json = reports_dir / "tool_artifacts" / "demo" / "invalid_artifact.json"
        invalid_json.parent.mkdir(parents=True, exist_ok=True)
        invalid_json.write_text("{not json", encoding="utf-8")
        missing_json = reports_dir / "tool_artifacts" / "demo" / "missing_artifact.json"
        return SolveResult(
            input_value=kwargs["input_value"],
            resolved_path=kwargs["input_value"],
            analysis_mode=kwargs["analysis_mode"],
            model_name="Copilot CLI",
            candidates=["NOT_FOUND"],
            selected_flag="NOT_FOUND",
            prompt="prompt",
            model_output="NOT_FOUND",
            extracted_strings_count=0,
            tool_artifacts=[
                ToolRunArtifact(
                    tool_name="InvalidTool",
                    enabled=True,
                    attempted=True,
                    success=False,
                    output_path=str(invalid_json),
                ),
                ToolRunArtifact(
                    tool_name="MissingTool",
                    enabled=True,
                    attempted=True,
                    success=False,
                    output_path=str(missing_json),
                ),
            ],
            report_path=str(reports_dir / "demo.md"),
        )

    monkeypatch.setattr("reverse_agent.harness.run_pipeline", _fake_run_pipeline)

    run_harness(
        HarnessConfig(
            cases=[HarnessCase(case_id="demo", input_value="demo.exe")],
            reports_dir=reports_dir,
            run_name="manifest_missing_suite",
            tool_config=ToolAutomationConfig(enabled=False),
        ),
        log=lambda _: None,
    )

    case_result = _read_json(
        reports_dir / "harness_runs" / "manifest_missing_suite" / "case_results" / "demo.json"
    )
    manifest = case_result["artifact_manifest"]
    assert [entry["classification"] for entry in manifest] == ["", ""]
    assert manifest[0]["kind"] == "invalid_artifact"
    assert manifest[0]["size_bytes"] == len("{not json")
    assert manifest[0]["sha256"] == hashlib.sha256(b"{not json").hexdigest()
    assert manifest[1]["kind"] == "missing_artifact"
    assert manifest[1]["size_bytes"] is None
    assert manifest[1]["sha256"] is None


def test_load_old_case_result_without_artifact_manifest_remains_compatible(tmp_path: Path) -> None:
    case_result_path = tmp_path / "old_case.json"
    case_result_path.write_text(
        json.dumps(
            {
                "case_id": "old",
                "input_value": "old.exe",
                "expected_flag": "",
                "selected_flag": "NOT_FOUND",
                "matched_expected": None,
                "status": "not_found",
                "elapsed_seconds": 0.1,
                "analysis_mode": "Static Analysis",
                "report_path": "",
                "resolved_path": "old.exe",
                "model_name": "Copilot CLI",
                "candidate_count": 0,
                "extracted_strings_count": 0,
                "tool_artifact_count": 0,
                "structured_evidence_count": 0,
                "validation_count": 0,
            }
        ),
        encoding="utf-8",
    )

    result = _load_case_result(case_result_path)

    assert result.case_id == "old"
    assert result.artifact_manifest == []
