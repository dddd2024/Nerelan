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
    lint_report,
    read_codex_report_summary,
    read_decision_meta,
    status_summary,
    validate_pytest_result_for_report,
)


GATE_RESULT_SCHEMA_VERSION = 1
FINAL_GATE_NAME = "final-check"
FINAL_GATE_RESULT_NAME = "final_gate_result.json"
SELF_OUTPUT_PATH = f"project_state/gates/{FINAL_GATE_RESULT_NAME}"

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
    return str(value or "").replace("\\", "/").strip().lstrip("./")


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {_norm_path(item) for item in value if isinstance(item, str) and _norm_path(item)}


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
        )
    return result


def _print_result(result: dict[str, Any]) -> None:
    print(f"final-check: {result.get('gate_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"report_id: {result.get('report_id')}")
    print(f"round_id: {result.get('round_id')}")
    for check in result.get("checks", []):
        print(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    print(f"recommended_next_action: {result.get('recommended_next_action')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project closeout gate checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    final_parser = subparsers.add_parser("final-check", help="Run final closeout gate.")
    final_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    final_parser.add_argument("--json", action="store_true", help="Print JSON result.")

    args = parser.parse_args(argv)
    if args.command == "final-check":
        result = final_check(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return 1 if result.get("gate_status") == "FAILED" else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
