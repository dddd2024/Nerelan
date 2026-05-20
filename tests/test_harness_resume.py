from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from reverse_agent.harness import (
    HarnessCase,
    HarnessCaseResult,
    HarnessConfig,
    HarnessSummary,
    main,
    run_harness,
)
from reverse_agent.pipeline import SolveResult


def test_harness_resume_skips_terminal_result(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _write_cached_result(tmp_path, status="passed")
    _patch_pipeline(monkeypatch, tmp_path, calls)

    summary = run_harness(_config(tmp_path), log=lambda _: None)

    assert summary.executed_cases == 0
    assert summary.resumed_cases == 1
    assert calls == []


def test_harness_resume_reruns_error_by_default_or_policy(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _write_cached_result(tmp_path, status="error")
    _patch_pipeline(monkeypatch, tmp_path, calls)

    summary = run_harness(_config(tmp_path), log=lambda _: None)

    assert summary.executed_cases == 1
    assert summary.resumed_cases == 0
    assert calls == ["demo.exe"]


def test_harness_resume_all_existing_keeps_old_behavior(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _write_cached_result(tmp_path, status="error")
    _patch_pipeline(monkeypatch, tmp_path, calls)

    summary = run_harness(_config(tmp_path, resume_policy="all-existing"), log=lambda _: None)

    assert summary.executed_cases == 0
    assert summary.resumed_cases == 1
    assert calls == []


def test_harness_resume_rerun_status_overrides_all_existing(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _write_cached_result(tmp_path, status="timeout")
    _patch_pipeline(monkeypatch, tmp_path, calls)

    summary = run_harness(
        _config(tmp_path, resume_policy="all-existing", rerun_statuses={"timeout"}),
        log=lambda _: None,
    )

    assert summary.executed_cases == 1
    assert summary.resumed_cases == 0
    assert calls == ["demo.exe"]


def test_harness_resume_rerun_error_aliases_error_status(tmp_path: Path, monkeypatch) -> None:
    captured: list[HarnessConfig] = []
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps([{"case_id": "demo", "input_value": "demo.exe"}]),
        encoding="utf-8",
    )

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
            summary_path="",
            case_result_paths=[],
        )

    monkeypatch.setattr("reverse_agent.harness.run_harness", _fake_run_harness)

    assert main(
        [
            "--dataset",
            str(dataset),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--run-name",
            "cli_suite",
            "--rerun-error",
        ]
    ) == 0
    assert captured[0].resume_policy == "terminal-only"
    assert captured[0].rerun_statuses == {"error"}


def test_harness_resume_unknown_or_missing_status_reruns_under_terminal_only(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[str] = []
    _write_cached_result(tmp_path, status="mystery")
    _patch_pipeline(monkeypatch, tmp_path, calls)

    unknown = run_harness(_config(tmp_path), log=lambda _: None)
    assert unknown.executed_cases == 1
    assert unknown.resumed_cases == 0

    calls.clear()
    _write_cached_result(tmp_path, status=None)
    missing = run_harness(_config(tmp_path), log=lambda _: None)

    assert missing.executed_cases == 1
    assert missing.resumed_cases == 0
    assert calls == ["demo.exe"]


def _config(
    tmp_path: Path,
    resume_policy: str = "terminal-only",
    rerun_statuses: set[str] | None = None,
) -> HarnessConfig:
    return HarnessConfig(
        cases=[HarnessCase(case_id="demo", input_value="demo.exe", expected_flag="flag{demo}")],
        reports_dir=tmp_path / "reports",
        run_name="resume_suite",
        analysis_mode="Static Analysis",
        resume_policy=resume_policy,
        rerun_statuses=rerun_statuses or set(),
    )


def _patch_pipeline(monkeypatch, tmp_path: Path, calls: list[str]) -> None:  # noqa: ANN001
    def _fake_run_pipeline(**kwargs):  # noqa: ANN001
        calls.append(kwargs["input_value"])
        return SolveResult(
            input_value=kwargs["input_value"],
            resolved_path=kwargs["input_value"],
            analysis_mode=kwargs["analysis_mode"],
            model_name="Copilot CLI",
            candidates=["flag{demo}"],
            selected_flag="flag{demo}",
            prompt="prompt",
            model_output="flag{demo}",
            extracted_strings_count=5,
            tool_artifacts=[],
            structured_evidence=[],
            candidate_validations=[],
            report_path=str(tmp_path / "reports" / "demo.md"),
        )

    monkeypatch.setattr("reverse_agent.harness.run_pipeline", _fake_run_pipeline)


def _write_cached_result(tmp_path: Path, status: str | None) -> None:
    result = HarnessCaseResult(
        case_id="demo",
        input_value="demo.exe",
        expected_flag="flag{demo}",
        selected_flag="flag{demo}",
        matched_expected=True,
        status=status or "passed",
        elapsed_seconds=0.1,
        analysis_mode="Static Analysis",
        report_path=str(tmp_path / "reports" / "demo.md"),
        resolved_path="demo.exe",
        model_name="Copilot CLI",
        candidate_count=1,
        extracted_strings_count=5,
        tool_artifact_count=0,
        structured_evidence_count=0,
        validation_count=0,
    )
    payload = asdict(result)
    if status is None:
        payload.pop("status")
    result_path = tmp_path / "reports" / "harness_runs" / "resume_suite" / "case_results" / "demo.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload), encoding="utf-8")
