from __future__ import annotations

import json
from pathlib import Path

from reverse_agent.harness import HarnessConfig, HarnessSummary, compare_harness_runs, main


def test_harness_compare_detects_status_change(tmp_path: Path) -> None:
    _write_case(tmp_path, "base", "demo", status="completed_no_expected", selected_flag="NOT_FOUND")
    _write_case(tmp_path, "head", "demo", status="passed", selected_flag="flag{demo}")

    payload = compare_harness_runs("base", "head", tmp_path)

    case_delta = payload["case_deltas"][0]
    assert case_delta["presence"] == "both"
    assert case_delta["status_change"] == "completed_no_expected -> passed"
    assert case_delta["selected_flag_change"] == "NOT_FOUND -> flag{demo}"
    assert payload["summary"]["status_changes"] == 1


def test_harness_compare_detects_artifact_classification_change(tmp_path: Path) -> None:
    base_artifact = _write_artifact(
        tmp_path,
        "base_artifact.json",
        classification="compare_lhs_runtime_backed_writer_missing",
    )
    head_artifact = _write_artifact(tmp_path, "head_artifact.json", classification="instrumentation_incomplete")
    _write_case(
        tmp_path,
        "base",
        "demo",
        artifact_manifest=[
            {
                "classification": "compare_lhs_runtime_backed_writer_missing",
                "kind": "compare_real_lhs_provenance_audit",
                "path": str(base_artifact),
            }
        ],
    )
    _write_case(
        tmp_path,
        "head",
        "demo",
        artifact_manifest=[
            {
                "classification": "instrumentation_incomplete",
                "kind": "compare_real_lhs_provenance_audit",
                "path": str(head_artifact),
            }
        ],
    )

    artifact_delta = compare_harness_runs("base", "head", tmp_path)["case_deltas"][0]["artifact_deltas"][0]

    assert artifact_delta["classification_change"] == (
        "compare_lhs_runtime_backed_writer_missing -> instrumentation_incomplete"
    )
    assert artifact_delta["presence"] == "both"


def test_harness_compare_detects_candidate_and_validation_count_delta(tmp_path: Path) -> None:
    _write_case(tmp_path, "base", "demo", candidate_count=2, validation_count=1)
    _write_case(tmp_path, "head", "demo", candidate_count=5, validation_count=4)

    case_delta = compare_harness_runs("base", "head", tmp_path)["case_deltas"][0]

    assert case_delta["candidate_count_delta"] == 3
    assert case_delta["validation_count_delta"] == 3


def test_harness_compare_handles_base_only_and_head_only_cases(tmp_path: Path) -> None:
    _write_case(tmp_path, "base", "removed", status="passed")
    _write_case(tmp_path, "head", "added", status="completed_no_expected")

    payload = compare_harness_runs("base", "head", tmp_path)

    assert [(item["case_id"], item["presence"]) for item in payload["case_deltas"]] == [
        ("added", "head_only"),
        ("removed", "base_only"),
    ]
    assert payload["summary"]["cases_added"] == 1
    assert payload["summary"]["cases_removed"] == 1


def test_harness_compare_cli_outputs_json_without_dataset(tmp_path: Path, capsys) -> None:
    _write_case(tmp_path, "base", "demo", status="passed")
    _write_case(tmp_path, "head", "demo", status="failed_expected")

    assert main(["compare", "--base-run", "base", "--head-run", "head", "--reports-dir", str(tmp_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["base_run"] == "base"
    assert payload["head_run"] == "head"
    assert payload["case_deltas"][0]["status_change"] == "passed -> failed_expected"


def test_harness_compare_preserves_existing_run_cli(tmp_path: Path, monkeypatch) -> None:
    captured: list[HarnessConfig] = []
    dataset = tmp_path / "dataset.json"
    dataset.write_text(json.dumps([{"case_id": "demo", "input_value": "demo.exe"}]), encoding="utf-8")

    def _fake_run_harness(config: HarnessConfig, log):  # noqa: ANN001
        captured.append(config)
        return HarnessSummary(
            run_name="cli_suite",
            run_dir=str(tmp_path / "reports" / "harness_runs" / "cli_suite"),
            total_cases=1,
            executed_cases=1,
            resumed_cases=0,
            passed_cases=1,
            failed_cases=0,
            completed_without_expected=0,
            error_cases=0,
            not_found_cases=0,
            labeled_cases=0,
            accuracy_when_labeled=None,
            evidence_coverage=None,
            candidate_quality=None,
            solve_rate_by_category={},
            elapsed_seconds=0.0,
            manifest_path="",
            summary_path="summary.json",
            case_result_paths=[],
        )

    monkeypatch.setattr("reverse_agent.harness.run_harness", _fake_run_harness)

    assert main(["--dataset", str(dataset), "--reports-dir", str(tmp_path / "reports")]) == 0
    assert captured[0].cases[0].case_id == "demo"


def test_harness_compare_handles_missing_or_invalid_artifact_json(tmp_path: Path) -> None:
    invalid_artifact = tmp_path / "invalid.json"
    invalid_artifact.write_text("{not json", encoding="utf-8")
    missing_artifact = tmp_path / "missing.json"
    _write_case(
        tmp_path,
        "base",
        "demo",
        artifact_manifest=[{"classification": "", "kind": "audit", "path": str(invalid_artifact)}],
    )
    _write_case(
        tmp_path,
        "head",
        "demo",
        artifact_manifest=[{"classification": "", "kind": "audit", "path": str(missing_artifact)}],
    )

    artifact_delta = compare_harness_runs("base", "head", tmp_path)["case_deltas"][0]["artifact_deltas"][0]

    assert artifact_delta["classification_change"] == ""
    assert artifact_delta["runtime_backed_count_delta"] is None
    assert artifact_delta["candidate_count_delta"] is None
    assert artifact_delta["evidence_gate_changed"] is None


def test_harness_compare_output_is_stably_sorted(tmp_path: Path) -> None:
    b_artifact = _write_artifact(tmp_path, "b.json", classification="same")
    a_artifact = _write_artifact(tmp_path, "a.json", classification="same")
    _write_case(
        tmp_path,
        "base",
        "z-case",
        artifact_manifest=[
            {"classification": "same", "kind": "z-kind", "path": str(b_artifact)},
            {"classification": "same", "kind": "a-kind", "path": str(a_artifact)},
        ],
    )
    _write_case(tmp_path, "base", "a-case")
    _write_case(
        tmp_path,
        "head",
        "z-case",
        artifact_manifest=[
            {"classification": "same", "kind": "z-kind", "path": str(b_artifact)},
            {"classification": "same", "kind": "a-kind", "path": str(a_artifact)},
        ],
    )
    _write_case(tmp_path, "head", "a-case")

    payload = compare_harness_runs("base", "head", tmp_path)

    assert [item["case_id"] for item in payload["case_deltas"]] == ["a-case", "z-case"]
    assert [item["kind"] for item in payload["case_deltas"][1]["artifact_deltas"]] == ["a-kind", "z-kind"]


def test_harness_compare_reads_top_level_artifact_fields(tmp_path: Path) -> None:
    base_artifact = _write_artifact(
        tmp_path,
        "base_fields.json",
        classification="from_json",
        candidate_count=2,
        evidence_gate="weak",
        runtime_backed_count=3,
    )
    head_artifact = _write_artifact(
        tmp_path,
        "head_fields.json",
        classification="from_json",
        candidate_count=5,
        evidence_gate="strong",
        runtime_backed_count=4,
    )
    _write_case(
        tmp_path,
        "base",
        "demo",
        artifact_manifest=[{"classification": "", "kind": "audit", "path": str(base_artifact)}],
    )
    _write_case(
        tmp_path,
        "head",
        "demo",
        artifact_manifest=[{"classification": "", "kind": "audit", "path": str(head_artifact)}],
    )

    artifact_delta = compare_harness_runs("base", "head", tmp_path)["case_deltas"][0]["artifact_deltas"][0]

    assert artifact_delta["candidate_count_delta"] == 3
    assert artifact_delta["runtime_backed_count_delta"] == 1
    assert artifact_delta["evidence_gate_changed"] is True


def _write_case(
    tmp_path: Path,
    run_name: str,
    case_id: str,
    *,
    artifact_manifest: list[dict[str, object]] | None = None,
    candidate_count: int = 0,
    selected_flag: str = "NOT_FOUND",
    status: str = "completed_no_expected",
    validation_count: int = 0,
) -> None:
    case_path = tmp_path / "harness_runs" / run_name / "case_results" / f"{case_id}.json"
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(
        json.dumps(
            {
                "artifact_manifest": artifact_manifest or [],
                "candidate_count": candidate_count,
                "case_id": case_id,
                "selected_flag": selected_flag,
                "status": status,
                "structured_evidence_count": 0,
                "tool_artifact_count": len(artifact_manifest or []),
                "validation_count": validation_count,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_artifact(
    tmp_path: Path,
    name: str,
    *,
    classification: str,
    candidate_count: int | None = None,
    evidence_gate: str | None = None,
    runtime_backed_count: int | None = None,
) -> Path:
    path = tmp_path / name
    payload: dict[str, object] = {"classification": classification}
    if candidate_count is not None:
        payload["candidate_count"] = candidate_count
    if evidence_gate is not None:
        payload["evidence_gate"] = evidence_gate
    if runtime_backed_count is not None:
        payload["runtime_backed_count"] = runtime_backed_count
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path
