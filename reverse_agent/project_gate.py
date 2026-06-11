from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .project_state import (
    ARCHIVE_MANIFEST_NAME,
    DEFAULT_STATE_DIR,
    build_round_consistency,
    doctor,
    lint_decision,
    lint_report,
    read_codex_report_summary,
    read_decision_meta,
    status_summary,
    validate_pytest_result_for_report,
)


GATE_RESULT_SCHEMA_VERSION = 1
FINAL_GATE_NAME = "final-check"
FINAL_GATE_RESULT_NAME = "final_gate_result.json"
PREFLIGHT_GATE_NAME = "preflight"
PREFLIGHT_RESULT_NAME = "preflight_result.json"
SELF_OUTPUT_PATH = f"project_state/gates/{FINAL_GATE_RESULT_NAME}"
PREFLIGHT_OUTPUT_PATH = f"project_state/gates/{PREFLIGHT_RESULT_NAME}"

ALLOWED_MAINLINES = {"engineering_branch", "reverse_solving", "tool_integration", "training_dataset"}
CAPABILITY_MAINLINES = {"reverse_solving", "tool_integration", "training_dataset"}

FORBIDDEN_PATHS = {
    ".codex-skills/registry.json",
    "reverse_agent/local_reverse_training_status.py",
    "reverse_agent/local_reverse_single_sample_static_triage.py",
}
FORBIDDEN_PREFIXES = (
    ".codex-skills/",
    "solve_reports/",
    "reverse_agent/ida_scripts/",
    "reverse_agent/olly_scripts/",
    "reverse_agent/probes/",
    "reverse_agent/strategies/",
    "reverse_agent/transforms/",
)
SAMPLE_SOLVING_TERMS = (
    "sample_solver",
    "candidate search",
    "runtime probe",
    "debugger",
    "hook",
    "emulator",
    "sidecar",
    "run sample",
    "run solver",
    "solver",
    "运行样本",
    "样本求解",
    "推进样本",
)
CAPABILITY_TERMS = ("ida", "ghidra", "debugger", "solver", "harness", "tool capability", "能力")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _rel(path: Path) -> str:
    try:
        text = str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        text = str(path)
    return _norm_path(text)


def _norm_path(value: object) -> str:
    normalized = str(value or "").replace("\\", "/").strip()
    return normalized[2:] if normalized.startswith("./") else normalized


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {_norm_path(item) for item in value if isinstance(item, str) and _norm_path(item)}


def _markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    start_level = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        hashes = len(stripped) - len(stripped.lstrip("#"))
        title = stripped.lstrip("#").strip()
        if heading.lower() in title.lower():
            start = index + 1
            start_level = hashes
            break
    if start is None:
        return ""
    section: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if hashes <= start_level:
                break
        section.append(line)
    return "\n".join(section)


def _without_section(text: str, heading: str) -> str:
    section = _markdown_section(text, heading)
    return text.replace(section, "") if section else text


def _scope_paths(scope_text: str) -> set[str]:
    paths: set[str] = set()
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        item = line[1:].strip().strip("`").strip()
        if not item or item.lower().endswith(":"):
            continue
        if item in {"Allowed source files", "Allowed tests", "Allowed generated files", "Disallowed"}:
            continue
        paths.add(_norm_path(item))
    return paths


def _allowed_scope_paths(scope_text: str) -> set[str]:
    paths: set[str] = set()
    in_allowed_block = False
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("allowed"):
            in_allowed_block = True
            continue
        if lowered.startswith("disallowed") or lowered.startswith("禁止"):
            in_allowed_block = False
            continue
        if not in_allowed_block or not line.startswith("-"):
            continue
        item = line[1:].strip().strip("`").strip()
        if item:
            paths.add(_norm_path(item))
    if paths:
        return paths
    return _scope_paths(scope_text)


def _decision_text_without_do_not_do(decision_text: str) -> str:
    text = decision_text
    for heading in ("Do Not Do", "Stop Conditions", "Disallowed"):
        section = _markdown_section(text, heading)
        if section:
            text = text.replace(section, "")
    return text.lower()


def _matched_non_negated_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    negation_markers = (
        "do not",
        "not ",
        "no ",
        "without",
        "forbidden",
        "audit",
        "check",
        "require",
        "不",
        "不得",
        "禁止",
        "不能",
        "检查",
        "审计",
        "能力",
        "要求",
    )
    matches: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.lower()
        if any(marker in line for marker in negation_markers):
            continue
        for term in terms:
            if term in line:
                matches.add(term)
    return sorted(matches)


def _git_changed_files(repo_root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=repo_root,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []

    files: list[str] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        path_text = line[3:] if len(line) > 3 else line
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        path_text = path_text.strip().strip('"')
        normalized = _norm_path(path_text)
        if normalized and normalized != SELF_OUTPUT_PATH:
            files.append(normalized)
    return sorted(set(files))


def _check(name: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    item.update(extra)
    return item


def _state_relative_path(state_dir: Path, path: Path) -> str:
    try:
        return _norm_path(str(path.resolve().relative_to(state_dir.parent.resolve())))
    except ValueError:
        return _norm_path(str(path))


def _round_archive_paths(state_dir: Path, round_id: str, manifest_files: list[str]) -> set[str]:
    if not round_id:
        return set()
    return {
        _state_relative_path(state_dir, state_dir / "rounds" / round_id / name)
        for name in manifest_files
        if name and name != ARCHIVE_MANIFEST_NAME
    } | {_state_relative_path(state_dir, state_dir / "rounds" / round_id / ARCHIVE_MANIFEST_NAME)}


def _archive_file_matches_live(state_dir: Path, round_id: str, name: str) -> bool | str:
    if not round_id:
        return "unknown"
    live_path = state_dir / name
    archived_path = state_dir / "rounds" / round_id / name
    if not live_path.exists() or not archived_path.exists():
        return False
    return live_path.read_bytes() == archived_path.read_bytes()


def _forbidden_hits(paths: set[str]) -> list[str]:
    hits: list[str] = []
    for path in sorted(paths):
        if path in FORBIDDEN_PATHS or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            hits.append(path)
    return hits


def _result_status(checks: list[dict[str, Any]], report_status: str) -> str:
    if any(check.get("status") == "FAIL" for check in checks):
        return "FAILED"
    if report_status == "BLOCKED":
        return "BLOCKED"
    if report_status in {"FAILED", "PARTIAL"}:
        return "WARN"
    if any(check.get("status") == "WARN" for check in checks):
        return "WARN"
    return "PASSED"


def _recommended_next_action(gate_status: str) -> str:
    if gate_status == "PASSED":
        return "no_action_required"
    if gate_status == "BLOCKED":
        return "keep_blocked_report_and_continue_from_next_decision"
    if gate_status == "WARN":
        return "review_warnings_before_closeout"
    return "fix_gate_failures_before_archive_or_handoff"


def final_check(*, state_dir: Path, repo_root: Path | None = None, write_result: bool = True) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)

    decision = read_decision_meta(state_dir)
    report = read_codex_report_summary(state_dir)
    pytest_text = _read_text(state_dir / "pytest_result.txt")
    pytest_validation = validate_pytest_result_for_report(pytest_text, report)
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    round_consistency = build_round_consistency(
        decision=decision,
        report=report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    lint_result = lint_report(state_dir)
    with contextlib.redirect_stdout(io.StringIO()):
        doctor_result = doctor(state_dir=state_dir)

    decision_id = str(decision.get("decision_id") or "")
    report_id = str(report.get("report_id") or "")
    round_id = str(report.get("round_id") or "")
    report_status = str(report.get("status") or "UNKNOWN")
    checks: list[dict[str, Any]] = []

    decision_report_ok = bool(
        decision_id
        and report.get("based_on_decision_id")
        and decision_id == str(report.get("based_on_decision_id"))
        and round_id
        and round_id == str(decision.get("round_id") or "")
    )
    checks.append(
        _check(
            "decision_report_match",
            "PASS" if decision_report_ok else "FAIL",
            "decision/report ids and round_id match" if decision_report_ok else "decision/report id or round_id mismatch",
        )
    )

    pytest_match_ok = pytest_validation.get("matches_report") is True and not pytest_validation.get("errors")
    checks.append(
        _check(
            "pytest_result_match",
            "PASS" if pytest_match_ok else "FAIL",
            "pytest_result matches report" if pytest_match_ok else "pytest_result does not match report",
            errors=pytest_validation.get("errors") or [],
        )
    )

    pytest_covers = pytest_validation.get("tests_ran_covers_report")
    checks.append(
        _check(
            "pytest_result_covers_report_tests",
            "PASS" if pytest_covers is True else "WARN",
            "pytest_result covers report tests" if pytest_covers is True else "pytest_result coverage is incomplete or unknown",
            missing_report_tests=pytest_validation.get("missing_report_tests") or [],
        )
    )

    manifest_present = bool(round_consistency.get("round_manifest_present"))
    manifest_files = list(round_consistency.get("round_manifest_files") or [])
    checks.append(
        _check(
            "round_manifest_present",
            "PASS" if manifest_present else "FAIL",
            "round manifest is present" if manifest_present else "round manifest is missing",
            round_manifest_path=round_consistency.get("round_manifest_path") or "",
        )
    )

    archived_report_match = _archive_file_matches_live(state_dir, round_id, "codex_execution_report.md")
    checks.append(
        _check(
            "archived_report_matches_live_report",
            "PASS" if archived_report_match is True else "FAIL",
            "archived report matches live report" if archived_report_match is True else "archived report differs from live report",
        )
    )

    archived_pytest_match = _archive_file_matches_live(state_dir, round_id, "pytest_result.txt")
    checks.append(
        _check(
            "archived_pytest_result_matches_live_pytest_result",
            "PASS" if archived_pytest_match is True else "FAIL",
            (
                "archived pytest_result matches live pytest_result"
                if archived_pytest_match is True
                else "archived pytest_result differs from live pytest_result"
            ),
        )
    )

    changed_files = set(_git_changed_files(repo_root))
    files_changed = _string_set(report.get("files_changed"))
    missing_diff_files = sorted(changed_files - files_changed)
    checks.append(
        _check(
            "files_changed_covers_git_diff",
            "PASS" if not missing_diff_files else "FAIL",
            "files_changed covers git status files" if not missing_diff_files else "files_changed omits git status files",
            missing_files=missing_diff_files,
            git_changed_files=sorted(changed_files),
        )
    )

    archive_paths = _round_archive_paths(state_dir, round_id, manifest_files)
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    missing_archive_artifacts = sorted(archive_paths - generated_artifacts)
    checks.append(
        _check(
            "generated_artifacts_cover_round_archive",
            "PASS" if not missing_archive_artifacts else "FAIL",
            (
                "generated_artifacts covers round archive files"
                if not missing_archive_artifacts
                else "generated_artifacts omits round archive files"
            ),
            missing_artifacts=missing_archive_artifacts,
        )
    )

    path_claims = changed_files | files_changed | generated_artifacts | archive_paths
    forbidden_hits = _forbidden_hits(path_claims)
    manifest_forbidden = list(round_consistency.get("round_manifest_forbidden_files") or [])
    if manifest_forbidden:
        forbidden_hits.extend(f"round_manifest:{name}" for name in manifest_forbidden)
    checks.append(
        _check(
            "forbidden_paths_absent",
            "PASS" if not forbidden_hits else "FAIL",
            "no forbidden paths detected" if not forbidden_hits else "forbidden paths detected",
            forbidden_paths=sorted(set(forbidden_hits)),
        )
    )

    status_errors: list[str] = []
    status_warnings: list[str] = []
    if not lint_result.get("ok"):
        status_errors.extend(str(item) for item in lint_result.get("errors") or [])
    status_warnings.extend(str(item) for item in lint_result.get("warnings") or [])
    doctor_status = str(doctor_result.get("status") or "FAIL")
    doctor_blocking_warnings = [
        str(check.get("detail") or check.get("name"))
        for check in doctor_result.get("checks", [])
        if check.get("status") == "WARN" and check.get("blocking") is True
    ]
    if doctor_status == "FAIL":
        status_errors.append("doctor status is FAIL")
    elif report_status == "SUCCESS" and doctor_blocking_warnings:
        status_errors.extend(doctor_blocking_warnings)
    elif doctor_status == "WARN":
        status_warnings.append("doctor status is WARN")
    if report_status == "SUCCESS" and not status_errors and doctor_status == "PASS":
        status_detail = "SUCCESS report passes lint and doctor"
    elif report_status == "BLOCKED" and not status_errors:
        status_detail = "BLOCKED report is internally consistent"
    elif report_status in {"FAILED", "PARTIAL"} and not status_errors:
        status_detail = f"{report_status} report is internally consistent"
    else:
        status_detail = "status policy found blocking issues"
    status_check = "FAIL" if status_errors else ("WARN" if status_warnings and report_status != "BLOCKED" else "PASS")
    checks.append(
        _check(
            "status_policy_valid",
            status_check,
            status_detail,
            lint_errors=status_errors,
            warnings=status_warnings,
            doctor_status=doctor_status,
            report_status=report_status,
        )
    )

    gate_status = _result_status(checks, report_status)
    warnings = [
        f"{check['name']}: {check['detail']}"
        for check in checks
        if check.get("status") == "WARN"
    ]
    blocking_reasons = [
        f"{check['name']}: {check['detail']}"
        for check in checks
        if check.get("status") == "FAIL"
    ]
    status = status_summary(state_dir=state_dir)
    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": FINAL_GATE_NAME,
        "gate_status": gate_status,
        "decision_id": decision_id,
        "report_id": report_id,
        "round_id": round_id,
        "generated_at": _now_iso(),
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "recommended_next_action": _recommended_next_action(gate_status),
        "status_summary": {
            key: status.get(key)
            for key in (
                "decision_execution_state",
                "decision_report_id_match",
                "decision_consumed_by_report",
                "archive_status",
                "report_status",
                "report_acceptance_recommendation",
            )
        },
    }

    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / FINAL_GATE_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def _preflight_recommended_next_action(gate_status: str) -> str:
    if gate_status == "PASSED":
        return "proceed_with_decision_scope"
    if gate_status == "BLOCKED":
        return "do_not_start_consumed_or_stale_decision"
    if gate_status == "WARN":
        return "review_preflight_warnings_before_starting"
    return "fix_preflight_failures_before_starting"


def preflight(*, state_dir: Path, repo_root: Path | None = None, write_result: bool = True) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    decision = read_decision_meta(state_dir)
    lint_decision_result = lint_decision(state_dir)
    status = status_summary(state_dir=state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")
    task_packet = _read_json(state_dir / "task_packet.json")
    current_state = _read_json(state_dir / "current_state.json")
    artifact_index = _read_json(state_dir / "artifact_index.json")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    decision_status = str(decision.get("status") or "UNKNOWN")
    checks: list[dict[str, Any]] = []

    parse_error = decision.get("parse_error")
    parse_ok = bool(decision_id and round_id and not parse_error and decision_status != "UNKNOWN")
    checks.append(
        _check(
            "decision_meta_parse",
            "PASS" if parse_ok else "FAIL",
            "decision_meta parsed" if parse_ok else "decision_meta missing or invalid",
            parse_error=parse_error,
        )
    )

    checks.append(
        _check(
            "decision_approved",
            "PASS" if decision_status == "APPROVED" else "FAIL",
            "decision status is APPROVED" if decision_status == "APPROVED" else f"decision status is {decision_status}",
        )
    )

    checks.append(
        _check(
            "mainline_valid",
            "PASS" if mainline in ALLOWED_MAINLINES else "FAIL",
            f"mainline is {mainline}" if mainline in ALLOWED_MAINLINES else f"mainline is invalid: {mainline}",
            allowed_mainlines=sorted(ALLOWED_MAINLINES),
        )
    )

    skill_errors = [
        error
        for error in lint_decision_result.get("errors", [])
        if "skill" in str(error).lower() or "profile" in str(error).lower()
    ]
    parsed_profiles = lint_decision_result.get("parsed_skill_profiles") or []
    inactive_profiles = [
        profile
        for profile in parsed_profiles
        if isinstance(profile, dict) and profile.get("registry_status") != "active"
    ]
    skill_ok = bool(parsed_profiles) and not skill_errors and not inactive_profiles
    checks.append(
        _check(
            "skill_profiles_active",
            "PASS" if skill_ok else "FAIL",
            "skill profiles are active" if skill_ok else "skill profiles are missing, inactive, or unknown",
            parsed_skill_profiles=parsed_profiles,
            errors=skill_errors,
        )
    )

    consumed = bool(status.get("decision_consumed_by_report"))
    stale_report_match = bool(status.get("decision_report_id_match"))
    not_consumed_ok = not consumed and not stale_report_match
    checks.append(
        _check(
            "decision_not_consumed_by_report",
            "PASS" if not_consumed_ok else "FAIL",
            "decision has not been consumed by a report" if not_consumed_ok else "decision already appears consumed by report",
            decision_execution_state=status.get("decision_execution_state"),
            report_id=status.get("report_id"),
        )
    )

    task = str(task_packet.get("task") or "")
    derived_task = str(task_packet.get("derived_task") or "")
    active_decision_packet = str(task_packet.get("active_decision_packet") or "")
    task_packet_ok = active_decision_packet in {"", "project_state/decision_packet.md"}
    checks.append(
        _check(
            "task_packet_is_non_authoritative",
            "PASS" if task_packet_ok else "WARN",
            "decision_packet remains authoritative over task_packet suggestions"
            if task_packet_ok
            else "task_packet points at a nonstandard decision packet",
            task=task,
            derived_task=derived_task,
            active_decision_packet=active_decision_packet,
        )
    )

    scope_text = _markdown_section(decision_text, "Implementation Scope")
    allowed_paths = _allowed_scope_paths(scope_text)
    scope_ok = bool(scope_text.strip()) and bool(allowed_paths)
    checks.append(
        _check(
            "implementation_scope_present",
            "PASS" if scope_ok else "FAIL",
            "implementation scope is present and parseable"
            if scope_ok
            else "implementation scope is missing or has no parseable allowed paths",
            allowed_paths=sorted(allowed_paths),
        )
    )

    forbidden_allowed = _forbidden_hits(allowed_paths)
    checks.append(
        _check(
            "forbidden_paths_not_allowed",
            "PASS" if not forbidden_allowed else "FAIL",
            "allowed scope contains no forbidden paths"
            if not forbidden_allowed
            else "allowed scope includes forbidden paths",
            forbidden_paths=forbidden_allowed,
        )
    )

    actionable_text = _decision_text_without_do_not_do(decision_text)
    goal_text = _markdown_section(decision_text, "Goal").lower()
    sample_terms = _matched_non_negated_terms(goal_text, SAMPLE_SOLVING_TERMS)
    sample_scope_paths = [
        path
        for path in sorted(allowed_paths)
        if any(token in path for token in ("solver", "runtime", "probe", "ida", "ghidra", "olly"))
    ]
    engineering_scope_ok = not (mainline == "engineering_branch" and (sample_terms or sample_scope_paths))
    checks.append(
        _check(
            "mainline_scope_policy",
            "PASS" if engineering_scope_ok else "FAIL",
            "mainline scope policy is satisfied"
            if engineering_scope_ok
            else "engineering_branch decision includes sample-solving/runtime terms",
            matched_terms=sample_terms,
            matched_paths=sample_scope_paths,
        )
    )

    current_evidence = _markdown_section(decision_text, "Current Evidence").lower()
    stale_terms_present = "stale" in current_evidence or "missing" in current_evidence
    has_negation = any(term in current_evidence for term in ("cannot", "not current", "historical", "历史", "不能", "不得"))
    artifact_policy_ok = not (stale_terms_present and "current evidence" in current_evidence and not has_negation)
    freshness = status.get("artifact_freshness") or {}
    checks.append(
        _check(
            "artifact_freshness_policy",
            "PASS" if artifact_policy_ok else "FAIL",
            "stale/missing artifacts are not claimed as current evidence"
            if artifact_policy_ok
            else "stale/missing artifact is described as current evidence",
            artifact_freshness=freshness,
            latest_harness_run=artifact_index.get("latest_harness_run"),
        )
    )

    capability_required = mainline in CAPABILITY_MAINLINES
    capability_text_present = any(term in actionable_text for term in CAPABILITY_TERMS) and any(
        term in actionable_text for term in ("audit", "check", "检查", "审计")
    )
    capability_ok = not capability_required or capability_text_present
    checks.append(
        _check(
            "tool_capability_audit_required_when_applicable",
            "PASS" if capability_ok else "FAIL",
            "tool capability audit requirement is satisfied"
            if capability_ok
            else "reverse/tool/training mainline lacks required tool capability audit wording",
            capability_required=capability_required,
        )
    )

    status_errors = [check for check in checks if check.get("status") == "FAIL"]
    warnings = [
        f"{check['name']}: {check['detail']}"
        for check in checks
        if check.get("status") == "WARN"
    ]
    blocking_reasons = [f"{check['name']}: {check['detail']}" for check in status_errors]
    if status_errors:
        gate_status = "BLOCKED" if any(check["name"] == "decision_not_consumed_by_report" for check in status_errors) else "FAILED"
    elif warnings:
        gate_status = "WARN"
    else:
        gate_status = "PASSED"

    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": PREFLIGHT_GATE_NAME,
        "gate_status": gate_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "recommended_next_action": _preflight_recommended_next_action(gate_status),
        "status_summary": {
            "decision_execution_state": status.get("decision_execution_state"),
            "decision_report_id_match": status.get("decision_report_id_match"),
            "decision_consumed_by_report": status.get("decision_consumed_by_report"),
            "task": task,
            "derived_task": derived_task,
            "current_state_round_id": current_state.get("round_id"),
        },
    }

    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / PREFLIGHT_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def _print_result(result: dict[str, Any]) -> None:
    print(f"{result.get('gate_name')}: {result.get('gate_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    if result.get("report_id") is not None:
        print(f"report_id: {result.get('report_id')}")
    print(f"round_id: {result.get('round_id')}")
    if result.get("mainline") is not None:
        print(f"mainline: {result.get('mainline')}")
    for check in result.get("checks", []):
        print(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    print(f"recommended_next_action: {result.get('recommended_next_action')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project closeout gate checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    final_parser = subparsers.add_parser("final-check", help="Run final closeout gate.")
    final_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    final_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    preflight_parser = subparsers.add_parser("preflight", help="Run preflight start gate.")
    preflight_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    preflight_parser.add_argument("--json", action="store_true", help="Print JSON result.")

    args = parser.parse_args(argv)
    if args.command == "final-check":
        result = final_check(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return 1 if result.get("gate_status") == "FAILED" else 0
    if args.command == "preflight":
        result = preflight(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return 1 if result.get("gate_status") == "FAILED" else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
