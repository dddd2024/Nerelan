from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .pipeline import SolveResult, run_pipeline
from .tool_runners import ToolAutomationConfig

LogFn = Callable[[str], None]
SCHEMA_VERSION = 1
RESUME_POLICY_TERMINAL_ONLY = "terminal-only"
RESUME_POLICY_ALL_EXISTING = "all-existing"
RESUME_POLICIES = {RESUME_POLICY_TERMINAL_ONLY, RESUME_POLICY_ALL_EXISTING}
TERMINAL_CASE_STATUSES = {
    "passed",
    "failed_expected",
    "completed_no_expected",
    "not_found",
}
NON_TERMINAL_RERUN_CASE_STATUSES = {
    "error",
    "timeout",
    "interrupted",
    "partial",
    "blocked",
}


@dataclass
class HarnessCase:
    case_id: str
    input_value: str
    expected_flag: str = ""
    analysis_mode: str | None = None
    runtime_validation_enabled: bool | None = None
    category: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ResourceBudget:
    max_case_seconds: int | None = 21600
    max_tool_seconds: int | None = 300
    max_artifact_bytes: int | None = 52428800
    max_recent_artifacts: int | None = 20
    max_context_pack_bytes: int | None = 1048576
    max_candidate_count: int | None = 5000
    max_probe_candidates: int | None = 50


@dataclass
class HarnessConfig:
    cases: list[HarnessCase]
    reports_dir: Path
    run_name: str = ""
    dataset_path: str = ""
    analysis_mode: str = "Auto"
    model_type: str = "Copilot CLI"
    copilot_command: str = 'gh copilot -p "{prompt}" --allow-all-tools --allow-all-paths -s'
    local_base_url: str = "http://127.0.0.1:11434"
    local_model: str = "qwen2.5-coder:7b"
    local_api_key: str = ""
    tool_config: ToolAutomationConfig = field(default_factory=ToolAutomationConfig)
    runtime_validation_enabled: bool = False
    copilot_timeout_seconds: int = 300
    resource_budget: ResourceBudget = field(default_factory=ResourceBudget)
    ctf_skill_enabled: bool = True
    ctf_skill_profile: str = "compact"
    resume: bool = True
    resume_policy: str = RESUME_POLICY_TERMINAL_ONLY
    rerun_statuses: set[str] = field(default_factory=set)
    fail_fast: bool = False


@dataclass
class HarnessCaseResult:
    case_id: str
    input_value: str
    expected_flag: str
    selected_flag: str
    matched_expected: bool | None
    status: str
    elapsed_seconds: float
    analysis_mode: str
    report_path: str
    resolved_path: str
    model_name: str
    candidate_count: int
    extracted_strings_count: int
    tool_artifact_count: int
    structured_evidence_count: int
    validation_count: int
    profile_name: str = ""
    matched_profiles: list[str] = field(default_factory=list)
    applied_strategies: list[str] = field(default_factory=list)
    category: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    artifact_manifest: list[dict[str, object]] = field(default_factory=list)
    error: str = ""
    traceback_text: str = ""
    cached: bool = False


@dataclass
class HarnessSummary:
    run_name: str
    run_dir: str
    total_cases: int
    executed_cases: int
    resumed_cases: int
    passed_cases: int
    failed_cases: int
    completed_without_expected: int
    error_cases: int
    not_found_cases: int
    labeled_cases: int
    accuracy_when_labeled: float | None
    evidence_coverage: float | None
    candidate_quality: float | None
    solve_rate_by_category: dict[str, float]
    elapsed_seconds: float
    manifest_path: str
    summary_path: str
    case_result_paths: list[str]


def load_harness_cases(dataset_path: Path) -> list[HarnessCase]:
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    items = raw.get("cases", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("Harness dataset must be a JSON list or an object with a 'cases' list.")

    cases: list[HarnessCase] = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Case #{idx} is not a JSON object.")
        case_id = str(item.get("case_id") or item.get("id") or f"case-{idx:03d}").strip()
        input_value = str(item.get("input_value") or item.get("input") or "").strip()
        if not case_id:
            raise ValueError(f"Case #{idx} is missing 'case_id'.")
        if not input_value:
            raise ValueError(f"Case '{case_id}' is missing 'input_value'.")
        tags = item.get("tags") or []
        if not isinstance(tags, list):
            raise ValueError(f"Case '{case_id}' has non-list 'tags'.")
        cases.append(
            HarnessCase(
                case_id=case_id,
                input_value=input_value,
                expected_flag=str(item.get("expected_flag") or item.get("expected") or "").strip(),
                analysis_mode=_optional_str(item.get("analysis_mode")),
                runtime_validation_enabled=_optional_bool(item.get("runtime_validation_enabled")),
                category=str(item.get("category") or "").strip(),
                tags=[str(tag) for tag in tags],
                notes=str(item.get("notes") or "").strip(),
            )
        )
    return cases


def filter_harness_cases(
    cases: list[HarnessCase],
    case_ids: list[str] | None = None,
    tags: list[str] | None = None,
    limit: int | None = None,
) -> list[HarnessCase]:
    selected = cases
    if case_ids:
        wanted = {item.strip() for item in case_ids if item.strip()}
        selected = [case for case in selected if case.case_id in wanted]
    if tags:
        wanted_tags = {item.strip() for item in tags if item.strip()}
        selected = [
            case
            for case in selected
            if wanted_tags.intersection(case.tags)
        ]
    if limit is not None:
        selected = selected[: max(0, limit)]
    return selected


def run_harness(config: HarnessConfig, log: LogFn) -> HarnessSummary:
    if not config.cases:
        raise ValueError("Harness config contains no cases.")
    if config.resume_policy not in RESUME_POLICIES:
        raise ValueError(f"Unknown resume policy: {config.resume_policy}")
    _resource_budget_payload(config.resource_budget)
    config.rerun_statuses = {str(status).strip() for status in config.rerun_statuses if str(status).strip()}

    run_name = _resolve_run_name(config)
    run_dir = config.reports_dir / "harness_runs" / run_name
    reports_dir = run_dir / "reports"
    case_results_dir = run_dir / "case_results"
    manifest_path = run_dir / "run_manifest.json"
    summary_path = run_dir / "summary.json"
    started_at = _now_iso()
    manifest = _build_manifest(config=config, run_name=run_name, run_dir=run_dir, started_at=started_at)
    if manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        existing_digest = str(existing_manifest.get("config_digest") or "")
        current_digest = str(manifest.get("config_digest") or "")
        if existing_digest and existing_digest != current_digest:
            raise ValueError(
                f"Run '{run_name}' already exists with a different harness config. "
                "Please use a new --run-name."
            )
        if not config.resume:
            raise ValueError(
                f"Run '{run_name}' already exists. Reuse --run-name only with resume enabled."
            )

    reports_dir.mkdir(parents=True, exist_ok=True)
    case_results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(manifest_path, manifest)

    results: list[HarnessCaseResult] = []
    executed_cases = 0
    resumed_cases = 0

    start_ts = datetime.now(timezone.utc)
    summary_payload: HarnessSummary | None = None
    try:
        for index, case in enumerate(config.cases, start=1):
            result_path = case_results_dir / f"{_sanitize_token(case.case_id)}.json"
            if config.resume and _should_resume_case(result_path, config.resume_policy, config.rerun_statuses):
                cached = _load_case_result(result_path)
                cached.cached = True
                results.append(cached)
                resumed_cases += 1
                log(f"[harness] 跳过可恢复样本 {index}/{len(config.cases)}: {case.case_id}")
                continue

            log(f"[harness] 运行样本 {index}/{len(config.cases)}: {case.case_id}")
            executed_cases += 1
            case_start = datetime.now(timezone.utc)
            try:
                solve_result = run_pipeline(
                    input_value=case.input_value,
                    analysis_mode=case.analysis_mode or config.analysis_mode,
                    model_type=config.model_type,
                    copilot_command=config.copilot_command,
                    local_base_url=config.local_base_url,
                    local_model=config.local_model,
                    local_api_key=config.local_api_key,
                    tool_config=config.tool_config,
                    runtime_validation_enabled=(
                        config.runtime_validation_enabled
                        if case.runtime_validation_enabled is None
                        else case.runtime_validation_enabled
                    ),
                    reports_dir=reports_dir,
                    log=lambda message, cid=case.case_id: log(f"[{cid}] {message}"),
                    copilot_timeout_seconds=config.copilot_timeout_seconds,
                    ctf_skill_enabled=config.ctf_skill_enabled,
                    ctf_skill_profile=config.ctf_skill_profile,
                )
                case_result = _case_result_from_solve_result(
                    case=case,
                    solve_result=solve_result,
                    elapsed_seconds=(datetime.now(timezone.utc) - case_start).total_seconds(),
                )
            except Exception as exc:
                case_result = HarnessCaseResult(
                    case_id=case.case_id,
                    input_value=case.input_value,
                    expected_flag=case.expected_flag,
                    selected_flag="",
                    matched_expected=False if case.expected_flag else None,
                    status="error",
                    elapsed_seconds=(datetime.now(timezone.utc) - case_start).total_seconds(),
                    analysis_mode=case.analysis_mode or config.analysis_mode,
                    report_path="",
                    resolved_path="",
                    model_name=config.model_type,
                    candidate_count=0,
                    extracted_strings_count=0,
                    tool_artifact_count=0,
                    structured_evidence_count=0,
                    validation_count=0,
                    category=case.category,
                    tags=case.tags[:],
                    notes=case.notes,
                    error=str(exc),
                    traceback_text=traceback.format_exc(),
                )
                log(f"[harness] 样本失败 {case.case_id}: {exc}")
                _write_json(result_path, asdict(case_result))
                results.append(case_result)
                if config.fail_fast:
                    manifest["status"] = "failed"
                    manifest["failure_case_id"] = case.case_id
                    raise
            else:
                _write_json(result_path, asdict(case_result))
                results.append(case_result)
    except Exception:
        manifest["status"] = "failed"
        manifest["failure_traceback"] = traceback.format_exc()
        raise
    finally:
        elapsed_seconds = (datetime.now(timezone.utc) - start_ts).total_seconds()
        summary_payload = _build_summary(
            run_name=run_name,
            run_dir=run_dir,
            elapsed_seconds=elapsed_seconds,
            executed_cases=executed_cases,
            resumed_cases=resumed_cases,
            manifest_path=manifest_path,
            summary_path=summary_path,
            results=results,
        )
        _write_json(summary_path, asdict(summary_payload))
        _write_summary_markdown(run_dir / "summary.md", summary_payload, results)
        manifest["completed_at"] = _now_iso()
        manifest["summary_path"] = str(summary_path)
        manifest["summary_digest"] = _sha256_json(asdict(summary_payload))
        if manifest.get("status") == "running":
            manifest["status"] = "completed"
        _write_json(manifest_path, manifest)

    return summary_payload


def compare_harness_runs(base_run: str, head_run: str, reports_dir: Path) -> dict[str, object]:
    base_run_dir = reports_dir / "harness_runs" / base_run
    head_run_dir = reports_dir / "harness_runs" / head_run
    base_cases = _load_compare_case_results(base_run_dir)
    head_cases = _load_compare_case_results(head_run_dir)

    case_deltas: list[dict[str, object]] = []
    for case_id in sorted(set(base_cases) | set(head_cases)):
        base_case = base_cases.get(case_id)
        head_case = head_cases.get(case_id)
        presence = _compare_presence(base_case, head_case)
        artifact_deltas = _compare_artifact_manifests(
            _list_field(base_case, "artifact_manifest"),
            _list_field(head_case, "artifact_manifest"),
            reports_dir=reports_dir,
        )
        case_deltas.append(
            {
                "artifact_deltas": artifact_deltas,
                "candidate_count_delta": _numeric_delta(base_case, head_case, "candidate_count"),
                "case_id": case_id,
                "presence": presence,
                "selected_flag_change": _value_change(
                    _optional_text_from_dict(base_case, "selected_flag"),
                    _optional_text_from_dict(head_case, "selected_flag"),
                ),
                "status_change": _value_change(
                    _optional_text_from_dict(base_case, "status"),
                    _optional_text_from_dict(head_case, "status"),
                ),
                "structured_evidence_count_delta": _numeric_delta(
                    base_case,
                    head_case,
                    "structured_evidence_count",
                ),
                "tool_artifact_count_delta": _numeric_delta(base_case, head_case, "tool_artifact_count"),
                "validation_count_delta": _numeric_delta(base_case, head_case, "validation_count"),
            }
        )

    return {
        "base_run": base_run,
        "base_run_dir": str(base_run_dir),
        "case_deltas": case_deltas,
        "head_run": head_run,
        "head_run_dir": str(head_run_dir),
        "summary": {
            "artifact_classification_changes": sum(
                1
                for case_delta in case_deltas
                for artifact_delta in case_delta["artifact_deltas"]  # type: ignore[index]
                if artifact_delta.get("presence") == "both"
                and artifact_delta.get("classification_change") not in {None, ""}
            ),
            "cases_added": sum(1 for item in case_deltas if item["presence"] == "head_only"),
            "cases_compared": len(case_deltas),
            "cases_removed": sum(1 for item in case_deltas if item["presence"] == "base_only"),
            "status_changes": sum(
                1
                for item in case_deltas
                if item["presence"] == "both" and item["status_change"] not in {None, ""}
            ),
        },
    }


def _parse_optional_positive_int(value: str) -> int | None:
    text = str(value).strip()
    if text.lower() in {"null", "none"}:
        return None
    try:
        parsed = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected a positive integer or null") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer or null")
    return parsed


def _resource_budget_payload(resource_budget: ResourceBudget) -> dict[str, int | None]:
    payload = asdict(resource_budget)
    for key, value in payload.items():
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"resource_budget.{key} must be a positive integer or None.")
    return payload


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "compare":
        return _main_compare(argv[1:])

    parser = argparse.ArgumentParser(description="Run reverse-agent as a reproducible harness.")
    parser.add_argument("--dataset", required=True, help="Path to a JSON dataset file.")
    parser.add_argument("--run-name", default="", help="Stable run name. Reuse it to resume.")
    parser.add_argument("--reports-dir", default="solve_reports", help="Reports root directory.")
    parser.add_argument(
        "--analysis-mode",
        default="Auto",
        choices=["Auto", "Static Analysis", "Dynamic Debug"],
        help="Default analysis mode for cases.",
    )
    parser.add_argument(
        "--model-type",
        default="Copilot CLI",
        choices=["Copilot CLI", "Local Model"],
        help="Pipeline model backend.",
    )
    parser.add_argument("--copilot-command", default='gh copilot -p "{prompt}" --allow-all-tools --allow-all-paths -s')
    parser.add_argument("--copilot-timeout-seconds", type=int, default=300)
    parser.add_argument("--max-case-seconds", type=_parse_optional_positive_int, default=21600)
    parser.add_argument("--max-tool-seconds", type=_parse_optional_positive_int, default=300)
    parser.add_argument("--max-artifact-bytes", type=_parse_optional_positive_int, default=52428800)
    parser.add_argument("--max-recent-artifacts", type=_parse_optional_positive_int, default=20)
    parser.add_argument("--max-context-pack-bytes", type=_parse_optional_positive_int, default=1048576)
    parser.add_argument("--max-candidate-count", type=_parse_optional_positive_int, default=5000)
    parser.add_argument("--max-probe-candidates", type=_parse_optional_positive_int, default=50)
    parser.add_argument("--local-base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--local-model", default="qwen2.5-coder:7b")
    parser.add_argument("--local-api-key", default="")
    parser.add_argument("--runtime-validation-enabled", action="store_true")
    parser.add_argument("--tool-enabled", action="store_true")
    parser.add_argument("--ida-enabled", action="store_true")
    parser.add_argument("--ida-executable", default="")
    parser.add_argument("--ida-script-path", default="")
    parser.add_argument("--ida-timeout-seconds", type=int, default=180)
    parser.add_argument("--olly-enabled", action="store_true")
    parser.add_argument("--olly-executable", default="")
    parser.add_argument("--olly-script-path", default="")
    parser.add_argument("--olly-timeout-seconds", type=int, default=120)
    parser.add_argument("--ctf-skill-profile", default="compact", choices=["compact", "full"])
    parser.add_argument("--disable-ctf-skill", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--resume-policy",
        default=RESUME_POLICY_TERMINAL_ONLY,
        choices=sorted(RESUME_POLICIES),
        help="Resume policy for existing case results.",
    )
    parser.add_argument(
        "--rerun-status",
        action="append",
        default=[],
        help="Force rerun for existing case results with this status. May be repeated.",
    )
    parser.add_argument("--rerun-error", action="store_true", help="Alias for --rerun-status error.")
    parser.add_argument("--case-id", action="append", default=[], help="Run only selected case ids.")
    parser.add_argument("--tag", action="append", default=[], help="Run only cases matching at least one tag.")
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N selected cases.")
    args = parser.parse_args(argv)

    dataset_path = Path(args.dataset)
    cases = load_harness_cases(dataset_path)
    cases = filter_harness_cases(cases, case_ids=args.case_id, tags=args.tag, limit=args.limit)
    if not cases:
        raise SystemExit("No cases selected for the harness run.")
    rerun_statuses = {str(status).strip() for status in args.rerun_status if str(status).strip()}
    if args.rerun_error:
        rerun_statuses.add("error")

    config = HarnessConfig(
        cases=cases,
        reports_dir=Path(args.reports_dir),
        run_name=args.run_name,
        dataset_path=str(dataset_path),
        analysis_mode=args.analysis_mode,
        model_type=args.model_type,
        copilot_command=args.copilot_command,
        local_base_url=args.local_base_url,
        local_model=args.local_model,
        local_api_key=args.local_api_key,
        tool_config=ToolAutomationConfig(
            enabled=args.tool_enabled,
            ida_enabled=args.ida_enabled,
            ida_executable=args.ida_executable,
            ida_script_path=args.ida_script_path,
            ida_timeout_seconds=args.ida_timeout_seconds,
            ollydbg_enabled=args.olly_enabled,
            ollydbg_executable=args.olly_executable,
            ollydbg_script_path=args.olly_script_path,
            ollydbg_timeout_seconds=args.olly_timeout_seconds,
        ),
        runtime_validation_enabled=args.runtime_validation_enabled,
        copilot_timeout_seconds=args.copilot_timeout_seconds,
        resource_budget=ResourceBudget(
            max_case_seconds=args.max_case_seconds,
            max_tool_seconds=args.max_tool_seconds,
            max_artifact_bytes=args.max_artifact_bytes,
            max_recent_artifacts=args.max_recent_artifacts,
            max_context_pack_bytes=args.max_context_pack_bytes,
            max_candidate_count=args.max_candidate_count,
            max_probe_candidates=args.max_probe_candidates,
        ),
        ctf_skill_enabled=not args.disable_ctf_skill,
        ctf_skill_profile=args.ctf_skill_profile,
        resume=not args.no_resume,
        resume_policy=args.resume_policy,
        rerun_statuses=rerun_statuses,
        fail_fast=args.fail_fast,
    )

    summary = run_harness(config, log=_safe_console_log)
    _safe_console_log(
        "[harness] completed "
        f"total={summary.total_cases} executed={summary.executed_cases} resumed={summary.resumed_cases} "
        f"passed={summary.passed_cases} failed={summary.failed_cases} errors={summary.error_cases} "
        f"accuracy={summary.accuracy_when_labeled}"
    )
    _safe_console_log(f"[harness] summary: {summary.summary_path}")
    return 0


def _main_compare(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compare two reverse-agent harness runs.")
    parser.add_argument("--base-run", required=True, help="Base harness run name.")
    parser.add_argument("--head-run", required=True, help="Head harness run name.")
    parser.add_argument("--reports-dir", default="solve_reports", help="Reports root directory.")
    parser.add_argument("--output", default="", help="Optional path to write the compare JSON.")
    args = parser.parse_args(argv)

    payload = compare_harness_runs(
        base_run=args.base_run,
        head_run=args.head_run,
        reports_dir=Path(args.reports_dir),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _safe_console_log(message: object) -> None:
    text = str(message)
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        sys.stdout.write(safe_text + "\n")


def _case_result_from_solve_result(
    case: HarnessCase,
    solve_result: SolveResult,
    elapsed_seconds: float,
) -> HarnessCaseResult:
    selected_flag = solve_result.selected_flag or ""
    expected_flag = case.expected_flag.strip()
    matched_expected: bool | None
    if expected_flag:
        matched_expected = selected_flag == expected_flag
        status = "passed" if matched_expected else "failed_expected"
    else:
        matched_expected = None
        status = "completed_no_expected"

    if selected_flag == "NOT_FOUND":
        status = "not_found" if not expected_flag else "failed_expected"

    return HarnessCaseResult(
        case_id=case.case_id,
        input_value=case.input_value,
        expected_flag=expected_flag,
        selected_flag=selected_flag,
        matched_expected=matched_expected,
        status=status,
        elapsed_seconds=elapsed_seconds,
        analysis_mode=solve_result.analysis_mode,
        report_path=solve_result.report_path,
        resolved_path=solve_result.resolved_path,
        model_name=solve_result.model_name,
        candidate_count=len(solve_result.candidates),
        extracted_strings_count=solve_result.extracted_strings_count,
        tool_artifact_count=len(solve_result.tool_artifacts),
        structured_evidence_count=len(solve_result.structured_evidence),
        validation_count=len(solve_result.candidate_validations),
        profile_name=solve_result.active_profile,
        matched_profiles=solve_result.matched_profiles[:],
        applied_strategies=solve_result.applied_strategies[:],
        category=case.category,
        tags=case.tags[:],
        notes=case.notes,
        artifact_manifest=_build_case_artifact_manifest(solve_result.tool_artifacts),
    )


def _path_for_artifact_manifest(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _artifact_kind_from_path(path: Path, tool_name: str = "") -> str:
    lower_name = path.name.lower()
    if lower_name.endswith("_compare_probe.json"):
        return "compare_probe"
    if lower_name.endswith("_compare_probe.log"):
        return "compare_probe_log"
    if path.suffix.lower() in {".json", ".log", ".txt"}:
        return path.stem
    return tool_name or path.stem


def _json_top_level_fields(path: Path) -> dict[str, object]:
    if path.suffix.lower() != ".json":
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_compare_case_results(run_dir: Path) -> dict[str, dict[str, object]]:
    case_results_dir = run_dir / "case_results"
    if not case_results_dir.exists():
        return {}
    cases: dict[str, dict[str, object]] = {}
    for path in sorted(case_results_dir.glob("*.json"), key=lambda item: item.name):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        case_id = str(data.get("case_id") or path.stem).strip() or path.stem
        cases[case_id] = data
    return cases


def _compare_artifact_manifests(
    base_manifest: list[object],
    head_manifest: list[object],
    reports_dir: Path,
) -> list[dict[str, object]]:
    base_artifacts = _artifact_manifest_by_kind(base_manifest, reports_dir)
    head_artifacts = _artifact_manifest_by_kind(head_manifest, reports_dir)
    deltas: list[dict[str, object]] = []
    for kind in sorted(set(base_artifacts) | set(head_artifacts)):
        base_artifact = base_artifacts.get(kind)
        head_artifact = head_artifacts.get(kind)
        deltas.append(
            {
                "base_path": _artifact_path_text(base_artifact),
                "candidate_count_delta": _artifact_numeric_delta(base_artifact, head_artifact, "candidate_count"),
                "classification_change": _value_change(
                    _artifact_classification(base_artifact),
                    _artifact_classification(head_artifact),
                ),
                "evidence_gate_changed": _artifact_value_changed(base_artifact, head_artifact, "evidence_gate"),
                "head_path": _artifact_path_text(head_artifact),
                "kind": kind,
                "presence": _compare_presence(base_artifact, head_artifact),
                "runtime_backed_count_delta": _artifact_numeric_delta(
                    base_artifact,
                    head_artifact,
                    "runtime_backed_count",
                ),
            }
        )
    return deltas


def _artifact_manifest_by_kind(manifest: list[object], reports_dir: Path) -> dict[str, dict[str, object]]:
    entries: list[dict[str, object]] = []
    for item in manifest:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if not kind:
            continue
        path_text = str(item.get("path") or "").strip()
        artifact_json = _read_manifest_artifact_json(path_text, reports_dir)
        entries.append(
            {
                "classification": str(item.get("classification") or artifact_json.get("classification") or ""),
                "evidence_gate": artifact_json.get("evidence_gate"),
                "kind": kind,
                "candidate_count": _as_int_or_none(artifact_json.get("candidate_count")),
                "path": path_text or None,
                "runtime_backed_count": _as_int_or_none(artifact_json.get("runtime_backed_count")),
            }
        )
    selected: dict[str, dict[str, object]] = {}
    for entry in sorted(entries, key=lambda item: (str(item.get("kind") or ""), str(item.get("path") or ""))):
        selected.setdefault(str(entry["kind"]), entry)
    return selected


def _read_manifest_artifact_json(path_text: str, reports_dir: Path) -> dict[str, object]:
    if not path_text:
        return {}
    raw_path = Path(path_text)
    candidates = [raw_path] if raw_path.is_absolute() else [Path.cwd() / raw_path, reports_dir / raw_path]
    for candidate in candidates:
        if candidate.exists():
            return _json_top_level_fields(candidate)
    return {}


def _build_case_artifact_manifest(tool_artifacts: list[object]) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for artifact in tool_artifacts:
        output_path = str(getattr(artifact, "output_path", "") or "").strip()
        if not output_path:
            continue

        path = Path(output_path)
        json_fields = _json_top_level_fields(path) if path.exists() else {}
        kind = str(json_fields.get("kind") or "").strip()
        if not kind:
            kind = _artifact_kind_from_path(path, str(getattr(artifact, "tool_name", "") or ""))

        size_bytes: int | None = None
        sha256: str | None = None
        if path.exists() and path.is_file():
            try:
                size_bytes = path.stat().st_size
                sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                size_bytes = None
                sha256 = None

        manifest.append(
            {
                "kind": kind,
                "path": _path_for_artifact_manifest(path),
                "size_bytes": size_bytes,
                "sha256": sha256,
                "classification": str(json_fields.get("classification") or ""),
                "tool_name": str(getattr(artifact, "tool_name", "") or ""),
                "owner_profile": str(getattr(artifact, "owner_profile", "") or ""),
                "strategy_name": str(getattr(artifact, "strategy_name", "") or ""),
            }
        )
    return manifest


def _build_manifest(
    config: HarnessConfig,
    run_name: str,
    run_dir: Path,
    started_at: str,
) -> dict[str, object]:
    resource_budget = _resource_budget_payload(config.resource_budget)
    config_payload = {
        "dataset_path": config.dataset_path,
        "analysis_mode": config.analysis_mode,
        "model_type": config.model_type,
        "copilot_command": config.copilot_command,
        "local_base_url": config.local_base_url,
        "local_model": config.local_model,
        "runtime_validation_enabled": config.runtime_validation_enabled,
        "copilot_timeout_seconds": config.copilot_timeout_seconds,
        "resource_budget": resource_budget,
        "ctf_skill_enabled": config.ctf_skill_enabled,
        "ctf_skill_profile": config.ctf_skill_profile,
        "resume": config.resume,
        "fail_fast": config.fail_fast,
        "tool_config": asdict(config.tool_config),
        "cases": [asdict(case) for case in config.cases],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "run_name": run_name,
        "run_dir": str(run_dir),
        "started_at": started_at,
        "dataset_digest": _sha256_json(config_payload["cases"]),
        "config_digest": _sha256_json(config_payload),
        "git_commit": _git_commit(),
        "resource_budget": resource_budget,
        "pipeline_defaults": config_payload,
        "case_ids": [case.case_id for case in config.cases],
    }


def _build_summary(
    run_name: str,
    run_dir: Path,
    elapsed_seconds: float,
    executed_cases: int,
    resumed_cases: int,
    manifest_path: Path,
    summary_path: Path,
    results: list[HarnessCaseResult],
) -> HarnessSummary:
    passed_cases = sum(1 for item in results if item.status == "passed")
    failed_cases = sum(1 for item in results if item.status == "failed_expected")
    completed_without_expected = sum(1 for item in results if item.status == "completed_no_expected")
    error_cases = sum(1 for item in results if item.status == "error")
    not_found_cases = sum(1 for item in results if item.selected_flag == "NOT_FOUND")
    labeled_cases = sum(1 for item in results if item.expected_flag)
    accuracy = (passed_cases / labeled_cases) if labeled_cases else None
    evidence_coverage = (
        sum(1 for item in results if item.structured_evidence_count > 0) / len(results)
        if results
        else None
    )
    candidate_quality = (
        sum(1 for item in results if item.candidate_count > 0 and item.selected_flag != "NOT_FOUND") / len(results)
        if results
        else None
    )
    category_counts: dict[str, dict[str, int]] = {}
    for item in results:
        category = item.category or "uncategorized"
        bucket = category_counts.setdefault(category, {"total": 0, "solved": 0})
        bucket["total"] += 1
        if item.selected_flag and item.selected_flag != "NOT_FOUND":
            bucket["solved"] += 1
    return HarnessSummary(
        run_name=run_name,
        run_dir=str(run_dir),
        total_cases=len(results),
        executed_cases=executed_cases,
        resumed_cases=resumed_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        completed_without_expected=completed_without_expected,
        error_cases=error_cases,
        not_found_cases=not_found_cases,
        labeled_cases=labeled_cases,
        accuracy_when_labeled=accuracy,
        evidence_coverage=evidence_coverage,
        candidate_quality=candidate_quality,
        solve_rate_by_category={
            key: (value["solved"] / value["total"]) if value["total"] else 0.0
            for key, value in sorted(category_counts.items())
        },
        elapsed_seconds=elapsed_seconds,
        manifest_path=str(manifest_path),
        summary_path=str(summary_path),
        case_result_paths=_materialized_case_result_paths(run_dir, results),
    )


def _materialized_case_result_paths(run_dir: Path, results: Sequence[HarnessCaseResult]) -> list[str]:
    case_result_paths: list[str] = []
    case_results_dir = Path(run_dir) / "case_results"
    for result in results:
        result_path = case_results_dir / f"{_sanitize_token(result.case_id)}.json"
        if not result_path.is_file():
            raise FileNotFoundError(f"Case result file for case_id {result.case_id!r} is missing: {result_path}")
        try:
            raw_result = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(
                f"Case result file for case_id {result.case_id!r} is not readable JSON: {result_path}"
            ) from exc
        if not isinstance(raw_result, Mapping):
            raise ValueError(
                f"Case result file for case_id {result.case_id!r} must contain a JSON object: {result_path}"
            )
        materialized_case_id = raw_result.get("case_id")
        if materialized_case_id != result.case_id:
            raise ValueError(
                "Case result file case_id mismatch: "
                f"expected {result.case_id!r}, found {materialized_case_id!r} in {result_path}"
            )
        case_result_paths.append(str(result_path))
    return case_result_paths


def _write_summary_markdown(
    path: Path,
    summary: HarnessSummary,
    results: list[HarnessCaseResult],
) -> None:
    category_lines = [
        f"| `{category}` | {rate:.2f} |"
        for category, rate in summary.solve_rate_by_category.items()
    ] or ["| `uncategorized` | 0.00 |"]
    lines = [
        "# Reverse Agent Harness Summary",
        "",
        f"- Run: `{summary.run_name}`",
        f"- Total cases: `{summary.total_cases}`",
        f"- Executed now: `{summary.executed_cases}`",
        f"- Resumed from cache: `{summary.resumed_cases}`",
        f"- Passed: `{summary.passed_cases}`",
        f"- Failed: `{summary.failed_cases}`",
        f"- Errors: `{summary.error_cases}`",
        f"- Not found: `{summary.not_found_cases}`",
        f"- Accuracy (labeled only): `{summary.accuracy_when_labeled}`",
        f"- Evidence coverage: `{summary.evidence_coverage}`",
        f"- Candidate quality: `{summary.candidate_quality}`",
        "",
        "## Solve Rate By Category",
        "",
        "| category | solve_rate |",
        "|---|---:|",
        *category_lines,
        "",
        "| case_id | category | status | profile | selected | expected | elapsed_s | cached | report |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for item in results:
        report = Path(item.report_path).name if item.report_path else "-"
        lines.append(
            f"| `{item.case_id}` | `{item.category or '-'}` | {item.status} | `{item.profile_name or '-'}` | `{item.selected_flag or '-'}` | "
            f"`{item.expected_flag or '-'}` | {item.elapsed_seconds:.2f} | "
            f"{'yes' if item.cached else 'no'} | `{report}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_case_result(path: Path) -> HarnessCaseResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    return HarnessCaseResult(**data)


def _compare_presence(base_item: object | None, head_item: object | None) -> str:
    if base_item is not None and head_item is not None:
        return "both"
    if base_item is not None:
        return "base_only"
    return "head_only"


def _list_field(data: dict[str, object] | None, field_name: str) -> list[object]:
    if data is None:
        return []
    value = data.get(field_name)
    return value if isinstance(value, list) else []


def _optional_text_from_dict(data: dict[str, object] | None, field_name: str) -> str | None:
    if data is None:
        return None
    value = data.get(field_name)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _numeric_delta(
    base_data: dict[str, object] | None,
    head_data: dict[str, object] | None,
    field_name: str,
) -> int | None:
    if base_data is None or head_data is None:
        return None
    base_value = _as_int_or_none(base_data.get(field_name))
    head_value = _as_int_or_none(head_data.get(field_name))
    if base_value is None or head_value is None:
        return None
    return head_value - base_value


def _artifact_numeric_delta(
    base_artifact: dict[str, object] | None,
    head_artifact: dict[str, object] | None,
    field_name: str,
) -> int | None:
    if base_artifact is None or head_artifact is None:
        return None
    base_value = _as_int_or_none(base_artifact.get(field_name))
    head_value = _as_int_or_none(head_artifact.get(field_name))
    if base_value is None or head_value is None:
        return None
    return head_value - base_value


def _artifact_value_changed(
    base_artifact: dict[str, object] | None,
    head_artifact: dict[str, object] | None,
    field_name: str,
) -> bool | None:
    if base_artifact is None or head_artifact is None:
        return None
    base_value = base_artifact.get(field_name)
    head_value = head_artifact.get(field_name)
    if base_value is None or head_value is None:
        return None
    return base_value != head_value


def _artifact_path_text(artifact: dict[str, object] | None) -> str | None:
    if artifact is None:
        return None
    value = artifact.get("path")
    return str(value) if value else None


def _artifact_classification(artifact: dict[str, object] | None) -> str | None:
    if artifact is None:
        return None
    value = artifact.get("classification")
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _value_change(base_value: object | None, head_value: object | None) -> str | None:
    if base_value == head_value:
        return ""
    return f"{_change_value_text(base_value)} -> {_change_value_text(head_value)}"


def _change_value_text(value: object | None) -> str:
    return "null" if value is None else str(value)


def _as_int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _case_result_status(result_path: Path) -> str | None:
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    if status is None:
        return None
    text = str(status).strip()
    return text or None


def _should_resume_case(result_path: Path, resume_policy: str, rerun_statuses: set[str]) -> bool:
    if not result_path.exists():
        return False
    status = _case_result_status(result_path)
    if status in rerun_statuses:
        return False
    if resume_policy == RESUME_POLICY_ALL_EXISTING:
        return True
    if resume_policy == RESUME_POLICY_TERMINAL_ONLY:
        return status in TERMINAL_CASE_STATUSES
    raise ValueError(f"Unknown resume policy: {resume_policy}")


def _resolve_run_name(config: HarnessConfig) -> str:
    if config.run_name.strip():
        return _sanitize_token(config.run_name)
    stem = Path(config.dataset_path).stem if config.dataset_path else "manual"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _sanitize_token(f"{stem}_{ts}")


def _sanitize_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return token.strip("._") or "run"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _git_commit() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
