from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.harness import (
    HarnessCase,
    HarnessConfig,
    HarnessSummary,
    ResourceBudget,
    main,
    run_harness,
)
from reverse_agent.pipeline import SolveResult


def test_resource_budget_defaults_are_written_to_manifest(tmp_path: Path, monkeypatch) -> None:
    _patch_pipeline(monkeypatch, tmp_path)

    run_harness(_config(tmp_path, run_name="budget_defaults"), log=lambda _: None)

    manifest = _read_manifest(tmp_path, "budget_defaults")
    expected = {
        "max_artifact_bytes": 52428800,
        "max_candidate_count": 5000,
        "max_case_seconds": 21600,
        "max_context_pack_bytes": 1048576,
        "max_probe_candidates": 50,
        "max_recent_artifacts": 20,
        "max_tool_seconds": 300,
    }
    assert manifest["resource_budget"] == expected
    assert manifest["pipeline_defaults"]["resource_budget"] == expected
    assert "config_digest" in manifest
    assert "pipeline_defaults" in manifest


def test_resource_budget_changes_are_part_of_config_digest(tmp_path: Path, monkeypatch) -> None:
    _patch_pipeline(monkeypatch, tmp_path)

    run_harness(_config(tmp_path, run_name="budget_digest"), log=lambda _: None)
    changed = _config(
        tmp_path,
        run_name="budget_digest",
        resource_budget=ResourceBudget(max_candidate_count=123),
    )

    with pytest.raises(ValueError, match="different harness config"):
        run_harness(changed, log=lambda _: None)


def test_resource_budget_accepts_null_cli_values(tmp_path: Path, monkeypatch) -> None:
    captured: list[HarnessConfig] = []
    dataset = _write_dataset(tmp_path)

    def _fake_run_harness(config: HarnessConfig, log):  # noqa: ANN001
        captured.append(config)
        return _summary(tmp_path)

    monkeypatch.setattr("reverse_agent.harness.run_harness", _fake_run_harness)

    assert main(
        [
            "--dataset",
            str(dataset),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--run-name",
            "cli_budget",
            "--max-case-seconds",
            "none",
            "--max-tool-seconds",
            "null",
        ]
    ) == 0

    assert captured[0].resource_budget.max_case_seconds is None
    assert captured[0].resource_budget.max_tool_seconds is None
    assert captured[0].resource_budget.max_candidate_count == 5000


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
def test_resource_budget_cli_rejects_invalid_values(tmp_path: Path, value: str) -> None:
    dataset = _write_dataset(tmp_path)

    with pytest.raises(SystemExit):
        main(
            [
                "--dataset",
                str(dataset),
                "--reports-dir",
                str(tmp_path / "reports"),
                "--max-candidate-count",
                value,
            ]
        )


def test_resource_budget_does_not_change_runtime_kwargs(tmp_path: Path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []

    def _fake_run_pipeline(**kwargs):  # noqa: ANN001
        captured.append(kwargs)
        return _solve_result(tmp_path, kwargs)

    monkeypatch.setattr("reverse_agent.harness.run_pipeline", _fake_run_pipeline)

    run_harness(
        _config(
            tmp_path,
            run_name="budget_runtime",
            copilot_timeout_seconds=123,
            resource_budget=ResourceBudget(max_tool_seconds=7),
        ),
        log=lambda _: None,
    )

    assert captured[0]["copilot_timeout_seconds"] == 123
    assert "resource_budget" not in captured[0]


def test_resource_budget_rejects_non_positive_programmatic_values(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="resource_budget.max_case_seconds"):
        run_harness(
            _config(
                tmp_path,
                run_name="bad_budget",
                resource_budget=ResourceBudget(max_case_seconds=0),
            ),
            log=lambda _: None,
        )


def _config(
    tmp_path: Path,
    *,
    run_name: str,
    copilot_timeout_seconds: int = 300,
    resource_budget: ResourceBudget | None = None,
) -> HarnessConfig:
    return HarnessConfig(
        cases=[HarnessCase(case_id="demo", input_value="demo.exe", expected_flag="flag{demo}")],
        reports_dir=tmp_path / "reports",
        run_name=run_name,
        analysis_mode="Static Analysis",
        copilot_timeout_seconds=copilot_timeout_seconds,
        resource_budget=resource_budget or ResourceBudget(),
    )


def _patch_pipeline(monkeypatch, tmp_path: Path) -> None:  # noqa: ANN001
    def _fake_run_pipeline(**kwargs):  # noqa: ANN001
        return _solve_result(tmp_path, kwargs)

    monkeypatch.setattr("reverse_agent.harness.run_pipeline", _fake_run_pipeline)


def _solve_result(tmp_path: Path, kwargs: dict[str, object]) -> SolveResult:
    return SolveResult(
        input_value=str(kwargs["input_value"]),
        resolved_path=str(kwargs["input_value"]),
        analysis_mode=str(kwargs["analysis_mode"]),
        model_name="Copilot CLI",
        candidates=["flag{demo}"],
        selected_flag="flag{demo}",
        prompt="prompt",
        model_output="flag{demo}",
        extracted_strings_count=1,
        tool_artifacts=[],
        structured_evidence=[],
        candidate_validations=[],
        report_path=str(tmp_path / "reports" / "demo.md"),
    )


def _write_dataset(tmp_path: Path) -> Path:
    dataset = tmp_path / "dataset.json"
    dataset.write_text(json.dumps([{"case_id": "demo", "input_value": "demo.exe"}]), encoding="utf-8")
    return dataset


def _read_manifest(tmp_path: Path, run_name: str) -> dict[str, object]:
    return json.loads(
        (tmp_path / "reports" / "harness_runs" / run_name / "run_manifest.json").read_text(encoding="utf-8")
    )


def _summary(tmp_path: Path) -> HarnessSummary:
    return HarnessSummary(
        run_name="cli_budget",
        run_dir=str(tmp_path / "reports" / "harness_runs" / "cli_budget"),
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
