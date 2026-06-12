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
    archive_round,
    build_round_consistency,
    doctor,
    lint_decision,
    lint_report,
    parse_pytest_result_header,
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
COMMAND_PLAN_NAME = "command-plan"
COMMAND_PLAN_RESULT_NAME = "command_plan.json"
REPORT_SUMMARY_NAME = "report-summary"
REPORT_SUMMARY_RESULT_NAME = "report_summary_synthesis.json"
ROUND_BASELINE_RESULT_NAME = "round_baseline.json"
ROUND_DELTA_SUMMARY_NAME = "round_delta_summary.json"
SELF_OUTPUT_PATH = f"project_state/gates/{FINAL_GATE_RESULT_NAME}"
PREFLIGHT_OUTPUT_PATH = f"project_state/gates/{PREFLIGHT_RESULT_NAME}"
COMMAND_PLAN_OUTPUT_PATH = f"project_state/gates/{COMMAND_PLAN_RESULT_NAME}"
REPORT_SUMMARY_OUTPUT_PATH = f"project_state/gates/{REPORT_SUMMARY_RESULT_NAME}"
ROUND_BASELINE_OUTPUT_PATH = f"project_state/gates/{ROUND_BASELINE_RESULT_NAME}"
ROUND_DELTA_OUTPUT_PATH = f"project_state/gates/{ROUND_DELTA_SUMMARY_NAME}"
CLOSE_ROUND_NAME = "close-round"

ARCHIVE_PENDING_CHECKS = {
    "round_manifest_present",
    "archived_report_matches_live_report",
    "archived_pytest_result_matches_live_pytest_result",
}

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
COMMAND_PLAN_KINDS = {
    "preflight",
    "final-check",
    "lint-report",
    "status",
    "doctor",
    "archive-round",
    "command-plan",
    "report-summary",
    "close-round",
    "pytest",
    "git status",
    "git rev-parse",
    "git diff",
    "git ls-files",
    "git rm",
    "build",
    "python-inline",
    "powershell",
    "test-path",
    "pwd",
}


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


def _fenced_code_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    lines = text.splitlines()
    in_block = False
    language = ""
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            fence_tail = stripped[3:].strip().lower()
            if not in_block:
                in_block = True
                language = fence_tail
                body = []
                continue
            blocks.append((language, "\n".join(body)))
            in_block = False
            language = ""
            body = []
            continue
        if in_block:
            body.append(line)
    return blocks


def _extract_bash_commands(text: str) -> tuple[list[str], str | None]:
    blocks = _fenced_code_blocks(text)
    bash_blocks = [body for language, body in blocks if language in {"bash", "sh", "shell"}]
    if not bash_blocks:
        return [], "Tests section has no fenced bash command block"
    commands = [
        line.strip()
        for body in bash_blocks
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not commands:
        return [], "fenced bash command block is empty"
    return commands, None


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
        if lowered.startswith("allowed") or lowered.startswith("允许"):
            in_allowed_block = True
            continue
        if lowered.startswith("disallowed") or lowered.startswith("不允许") or lowered.startswith("禁止"):
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


def _scope_path_has_runtime_token(path: str) -> bool:
    runtime_tokens = {"solver", "runtime", "probe", "ida", "ghidra", "olly"}
    chunks: list[str] = []
    current = []
    for char in path.lower().replace("\\", "/"):
        if char.isalnum():
            current.append(char)
            continue
        if current:
            chunks.append("".join(current))
            current = []
    if current:
        chunks.append("".join(current))
    return any(chunk in runtime_tokens for chunk in chunks)


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


def _git_status_short_lines(repo_root: Path) -> list[str]:
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
    return [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]


def _git_diff_name_only(repo_root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only"],
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
    return sorted({_norm_path(line) for line in proc.stdout.splitlines() if _norm_path(line)})


def _git_head_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=repo_root,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _round_baseline_path(state_dir: Path) -> Path:
    return state_dir / "gates" / ROUND_BASELINE_RESULT_NAME


def _round_delta_summary_path(state_dir: Path) -> Path:
    return state_dir / "gates" / ROUND_DELTA_SUMMARY_NAME


def _baseline_matches_round(payload: dict[str, Any], decision_id: str, round_id: str) -> bool:
    return (
        bool(payload)
        and str(payload.get("decision_id") or "") == decision_id
        and str(payload.get("round_id") or "") == round_id
    )


def _capture_round_baseline(
    *,
    state_dir: Path,
    repo_root: Path,
    decision_id: str,
    round_id: str,
    write_result: bool,
) -> dict[str, Any]:
    baseline_path = _round_baseline_path(state_dir)
    existing = _read_json(baseline_path)
    if _baseline_matches_round(existing, decision_id, round_id):
        return existing

    baseline = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "artifact_name": ROUND_BASELINE_RESULT_NAME,
        "decision_id": decision_id,
        "round_id": round_id,
        "head_commit": _git_head_commit(repo_root),
        "baseline_git_status_short": _git_status_short_lines(repo_root),
        "baseline_git_diff_name_only": _git_diff_name_only(repo_root),
        "baseline_dirty_files": _git_changed_files(repo_root),
        "generated_at": _now_iso(),
    }
    if write_result:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(baseline, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return baseline


def _build_round_delta_summary(
    *,
    state_dir: Path,
    repo_root: Path,
    decision_id: str,
    round_id: str,
    write_result: bool,
) -> dict[str, Any]:
    baseline = _read_json(_round_baseline_path(state_dir))
    baseline_available = _baseline_matches_round(baseline, decision_id, round_id)
    baseline_dirty_files = _string_set(baseline.get("baseline_dirty_files")) if baseline_available else set()
    final_dirty_files = set(_git_changed_files(repo_root))
    if write_result:
        final_dirty_files.add(SELF_OUTPUT_PATH)
        final_dirty_files.add(ROUND_DELTA_OUTPUT_PATH)

    inherited_dirty_files = final_dirty_files & baseline_dirty_files if baseline_available else set()
    new_dirty_files = final_dirty_files - baseline_dirty_files if baseline_available else final_dirty_files
    resolved_dirty_files = baseline_dirty_files - final_dirty_files if baseline_available else set()

    summary = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "artifact_name": ROUND_DELTA_SUMMARY_NAME,
        "decision_id": decision_id,
        "round_id": round_id,
        "head_commit": _git_head_commit(repo_root),
        "baseline_available": baseline_available,
        "baseline_git_status_short": baseline.get("baseline_git_status_short") if baseline_available else [],
        "baseline_git_diff_name_only": baseline.get("baseline_git_diff_name_only") if baseline_available else [],
        "baseline_dirty_files": sorted(baseline_dirty_files),
        "final_git_status_short": _git_status_short_lines(repo_root),
        "final_git_diff_name_only": _git_diff_name_only(repo_root),
        "final_dirty_files": sorted(final_dirty_files),
        "new_dirty_files_since_baseline": sorted(new_dirty_files),
        "inherited_dirty_files": sorted(inherited_dirty_files),
        "baseline_dirty_files_resolved": sorted(resolved_dirty_files),
        "generated_at": _now_iso(),
    }
    if write_result:
        summary_path = _round_delta_summary_path(state_dir)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return summary


def _round_delta_checks(
    *,
    delta_summary: dict[str, Any],
    files_changed: set[str],
    generated_artifacts: set[str],
    archive_paths: set[str],
) -> list[dict[str, Any]]:
    baseline_available = bool(delta_summary.get("baseline_available"))
    final_dirty_files = _string_set(delta_summary.get("final_dirty_files"))
    new_dirty_files = _string_set(delta_summary.get("new_dirty_files_since_baseline"))
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    required_changed_files = (new_dirty_files if baseline_available else final_dirty_files) | archive_paths

    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "round_delta_summary_present",
            "PASS" if baseline_available else "WARN",
            "round delta summary is baseline-aware"
            if baseline_available
            else "round baseline is missing; falling back to legacy git diff coverage",
            path=ROUND_DELTA_OUTPUT_PATH,
            baseline_available=baseline_available,
            inherited_dirty_files=sorted(inherited_dirty_files),
            new_dirty_files_since_baseline=sorted(new_dirty_files),
            final_dirty_files=sorted(final_dirty_files),
        )
    )

    inherited_claimed = sorted(inherited_dirty_files & files_changed) if baseline_available else []
    if inherited_claimed:
        checks.append(
            _check(
                "files_changed_excludes_inherited_dirty_files",
                "FAIL",
                "files_changed includes inherited baseline dirty files",
                inherited_files_in_files_changed=inherited_claimed,
            )
        )
    else:
        checks.append(
            _check(
                "files_changed_excludes_inherited_dirty_files",
                "PASS" if baseline_available else "WARN",
                "files_changed excludes inherited baseline dirty files"
                if baseline_available
                else "no baseline summary is available for inherited dirty file classification",
                inherited_dirty_files=sorted(inherited_dirty_files),
            )
        )

    missing_diff_files = sorted(required_changed_files - files_changed)
    checks.append(
        _check(
            "files_changed_covers_git_diff",
            "PASS" if not missing_diff_files else "FAIL",
            "files_changed covers round delta files"
            if not missing_diff_files
            else "files_changed omits round delta files",
            missing_files=missing_diff_files,
            git_changed_files=sorted(final_dirty_files),
            required_round_delta_files=sorted(required_changed_files),
            inherited_dirty_files=sorted(inherited_dirty_files),
        )
    )

    required_delta_artifacts = {ROUND_DELTA_OUTPUT_PATH}
    if baseline_available:
        required_delta_artifacts.add(ROUND_BASELINE_OUTPUT_PATH)
    missing_delta_artifacts = sorted(required_delta_artifacts - generated_artifacts)
    checks.append(
        _check(
            "generated_artifacts_cover_round_delta",
            "PASS" if not missing_delta_artifacts else "FAIL",
            "generated_artifacts covers round baseline/delta artifacts"
            if not missing_delta_artifacts
            else "generated_artifacts omits round baseline/delta artifacts",
            missing_artifacts=missing_delta_artifacts,
        )
    )
    return checks


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


def _report_mentions_command_plan(report: dict[str, Any]) -> bool:
    report_tests = _string_set(report.get("tests_ran"))
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    return any("command-plan" in item for item in report_tests) or COMMAND_PLAN_OUTPUT_PATH in generated_artifacts


def _report_summary_required(
    *,
    decision_text: str,
    report: dict[str, Any],
    command_plan_payload: dict[str, Any] | None = None,
) -> bool:
    lowered = decision_text.lower()
    report_tests = _string_set(report.get("tests_ran"))
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    plan_commands = _command_strings(command_plan_payload or {})
    return (
        "report-summary" in lowered
        or "synth-report" in lowered
        or any("report-summary" in item for item in report_tests)
        or any("report-summary" in item for item in plan_commands)
        or REPORT_SUMMARY_OUTPUT_PATH in generated_artifacts
    )


def _expected_exit_codes_by_command(command_plan_payload: dict[str, Any]) -> dict[str, list[list[int]]]:
    expected: dict[str, list[list[int]]] = {}
    commands = command_plan_payload.get("commands")
    if not isinstance(commands, list):
        return expected
    for item in commands:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command") or "")
        codes = item.get("expected_exit_codes")
        if not command or not isinstance(codes, list):
            continue
        normalized_codes: list[int] = []
        for code in codes:
            try:
                normalized_codes.append(int(code))
            except (TypeError, ValueError):
                continue
        expected.setdefault(command, []).append(normalized_codes)
    return expected


def _command_strings(command_plan_payload: dict[str, Any]) -> set[str]:
    commands = command_plan_payload.get("commands")
    if not isinstance(commands, list):
        return set()
    return {
        _norm_path(item.get("command"))
        for item in commands
        if isinstance(item, dict) and _norm_path(item.get("command"))
    }


def _command_plan_json_commands(command_plan_payload: dict[str, Any]) -> list[dict[str, Any]]:
    commands = command_plan_payload.get("commands")
    if not isinstance(commands, list):
        return []
    return [dict(item) for item in commands if isinstance(item, dict)]


def _parse_recorded_command_blocks(pytest_text: str) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    malformed: list[str] = []
    current: dict[str, Any] | None = None
    section = "stdout"
    for raw_line in pytest_text.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("===== COMMAND: ") and line.endswith(" ====="):
            if current is not None:
                malformed.append(str(current.get("command") or "<unknown>"))
                blocks.append(current)
            command = line[len("===== COMMAND: ") : -len(" =====")]
            current = {"command": command, "stdout_lines": [], "stderr_lines": [], "exit_code": None}
            section = "stdout"
            continue
        if current is None:
            continue
        if line == "===== STDERR =====":
            section = "stderr"
            continue
        if line.startswith("===== EXIT: ") and line.endswith(" ====="):
            exit_text = line[len("===== EXIT: ") : -len(" =====")].strip()
            try:
                current["exit_code"] = int(exit_text)
            except ValueError:
                malformed.append(str(current.get("command") or "<unknown>"))
            blocks.append(current)
            current = None
            section = "stdout"
            continue
        if section == "stderr":
            current["stderr_lines"].append(line)
        else:
            current["stdout_lines"].append(line)
    if current is not None:
        malformed.append(str(current.get("command") or "<unknown>"))
        blocks.append(current)
    for block in blocks:
        block["stdout"] = "\n".join(block.pop("stdout_lines", []))
        block["stderr"] = "\n".join(block.pop("stderr_lines", []))
    return {"blocks": blocks, "malformed_commands": malformed}


def _validate_command_plan_consistency(
    *,
    state_dir: Path,
    decision: dict[str, Any],
    report: dict[str, Any],
    pytest_text: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    command_plan_required = _report_mentions_command_plan(report)
    command_plan_path = state_dir / "gates" / COMMAND_PLAN_RESULT_NAME
    command_plan_payload = _read_json(command_plan_path)
    command_plan_present = command_plan_path.exists() and bool(command_plan_payload)
    if not command_plan_required:
        checks.append(
            _check(
                "command_plan_present",
                "PASS",
                "command-plan consistency is not required for this report",
                required=False,
            )
        )
        return checks

    checks.append(
        _check(
            "command_plan_present",
            "PASS" if command_plan_present else "FAIL",
            "command_plan.json is present" if command_plan_present else "command_plan.json is missing or invalid",
            path=COMMAND_PLAN_OUTPUT_PATH,
            required=True,
        )
    )
    if not command_plan_present:
        for name in (
            "command_plan_ids_match",
            "command_plan_covers_report_tests",
            "pytest_result_exit_codes_match_command_plan",
            "command_plan_json_stdout_full",
            "command_plan_generated_artifact_recorded",
        ):
            checks.append(_check(name, "FAIL", "command_plan.json is unavailable"))
        return checks

    plan_status_ok = command_plan_payload.get("plan_status") == "PASSED"
    ids_ok = (
        plan_status_ok
        and str(command_plan_payload.get("decision_id") or "") == str(decision.get("decision_id") or "")
        and str(command_plan_payload.get("round_id") or "") == str(decision.get("round_id") or "")
        and str(command_plan_payload.get("round_id") or "") == str(report.get("round_id") or "")
    )
    checks.append(
        _check(
            "command_plan_ids_match",
            "PASS" if ids_ok else "FAIL",
            "command_plan ids and status match current decision/report"
            if ids_ok
            else "command_plan ids, round_id, or status do not match",
            plan_status=command_plan_payload.get("plan_status"),
            command_plan_decision_id=command_plan_payload.get("decision_id"),
            command_plan_round_id=command_plan_payload.get("round_id"),
        )
    )

    plan_commands = _command_strings(command_plan_payload)
    report_tests = _string_set(report.get("tests_ran"))
    pytest_header = parse_pytest_result_header(pytest_text)
    pytest_tests = {_norm_path(item) for item in (pytest_header.get("tests_ran") or []) if _norm_path(item)}
    missing_report_tests = sorted(report_tests - plan_commands)
    missing_pytest_tests = sorted(pytest_tests - plan_commands)
    coverage_ok = not missing_report_tests and not missing_pytest_tests
    checks.append(
        _check(
            "command_plan_covers_report_tests",
            "PASS" if coverage_ok else "FAIL",
            "command_plan commands cover report and pytest_result tests"
            if coverage_ok
            else "command_plan commands do not cover report or pytest_result tests",
            missing_report_tests=missing_report_tests,
            missing_pytest_result_tests=missing_pytest_tests,
        )
    )

    recorded = _parse_recorded_command_blocks(pytest_text)
    blocks = list(recorded.get("blocks") or [])
    malformed_commands = list(recorded.get("malformed_commands") or [])
    blocks_by_command: dict[str, list[dict[str, Any]]] = {}
    for block in blocks:
        blocks_by_command.setdefault(str(block.get("command") or ""), []).append(block)

    expected_by_command = _expected_exit_codes_by_command(command_plan_payload)
    exit_errors: list[dict[str, Any]] = []
    for command, expected_entries in expected_by_command.items():
        recorded_entries = blocks_by_command.get(command, [])
        if len(recorded_entries) < len(expected_entries):
            exit_errors.append(
                {
                    "command": command,
                    "error": "missing recorded command block",
                    "expected_count": len(expected_entries),
                    "recorded_count": len(recorded_entries),
                }
            )
            continue
        for index, expected_codes in enumerate(expected_entries):
            exit_code = recorded_entries[index].get("exit_code")
            if exit_code not in expected_codes:
                exit_errors.append(
                    {
                        "command": command,
                        "exit_code": exit_code,
                        "expected_exit_codes": expected_codes,
                    }
                )
    if malformed_commands:
        exit_errors.append({"error": "malformed recorded command block", "commands": malformed_commands})
    checks.append(
        _check(
            "pytest_result_exit_codes_match_command_plan",
            "PASS" if not exit_errors else "FAIL",
            "recorded command exit codes match command_plan expected_exit_codes"
            if not exit_errors
            else "recorded command exit codes do not match command_plan expected_exit_codes",
            errors=exit_errors,
        )
    )

    json_commands = [
        str(item.get("command") or "")
        for item in _command_plan_json_commands(command_plan_payload)
        if "command-plan" in str(item.get("command") or "") and "--json" in str(item.get("command") or "")
    ]
    json_stdout_errors: list[dict[str, Any]] = []
    for command in json_commands:
        matching_blocks = blocks_by_command.get(command, [])
        if not matching_blocks:
            json_stdout_errors.append({"command": command, "error": "missing recorded stdout"})
            continue
        stdout = str(matching_blocks[0].get("stdout") or "").strip()
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            json_stdout_errors.append({"command": command, "error": f"stdout is not JSON: {exc.msg}"})
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("commands"), list):
            json_stdout_errors.append({"command": command, "error": "stdout commands is not a full list"})
    checks.append(
        _check(
            "command_plan_json_stdout_full",
            "PASS" if not json_stdout_errors else "FAIL",
            "command-plan --json recorded stdout contains full commands array"
            if not json_stdout_errors
            else "command-plan --json recorded stdout is missing a full commands array",
            errors=json_stdout_errors,
        )
    )

    generated_artifacts = _string_set(report.get("generated_artifacts"))
    artifact_recorded = COMMAND_PLAN_OUTPUT_PATH in generated_artifacts
    checks.append(
        _check(
            "command_plan_generated_artifact_recorded",
            "PASS" if artifact_recorded else "FAIL",
            "report generated_artifacts includes command_plan.json"
            if artifact_recorded
            else "report generated_artifacts omits command_plan.json",
            path=COMMAND_PLAN_OUTPUT_PATH,
        )
    )
    return checks


def _expected_report_id(round_id: str) -> str:
    if round_id.startswith("round_"):
        return f"codex_report_{round_id[len('round_'):]}"
    return f"codex_report_{round_id}" if round_id else ""


def _report_status_from_gate(gate_status: str) -> tuple[str, str] | None:
    mapping = {
        "PASSED": ("SUCCESS", "ACCEPTED"),
        "WARN": ("PARTIAL", "NEEDS_REVIEW"),
        "FAILED": ("FAILED", "REWORK_REQUIRED"),
        "BLOCKED": ("BLOCKED", "BLOCKED"),
    }
    return mapping.get(gate_status)


def _report_status_from_gate_payload(payload: dict[str, Any]) -> tuple[str, str] | None:
    gate_status = str(payload.get("gate_status") or "")
    if gate_status == "WARN":
        status_summary_payload = payload.get("status_summary")
        status_summary_map = status_summary_payload if isinstance(status_summary_payload, dict) else {}
        report_status = str(status_summary_map.get("report_status") or "")
        acceptance = str(status_summary_map.get("report_acceptance_recommendation") or "")
        warn_check_names = {
            str(check.get("name") or "")
            for check in payload.get("checks", [])
            if isinstance(check, dict) and check.get("status") == "WARN"
        }
        allowed_prearchive_warnings = ARCHIVE_PENDING_CHECKS | {
            "report_summary_status_source_available",
            "status_policy_valid",
        }
        if report_status == "SUCCESS" and warn_check_names and warn_check_names <= allowed_prearchive_warnings:
            return "SUCCESS", acceptance if acceptance else "ACCEPTED"
    return _report_status_from_gate(gate_status)


def _final_gate_is_report_summary_self_failure(payload: dict[str, Any]) -> bool:
    if payload.get("gate_status") != "FAILED":
        return False
    failed_check_names = {
        str(check.get("name") or "")
        for check in payload.get("checks", [])
        if isinstance(check, dict) and check.get("status") == "FAIL"
    }
    return bool(failed_check_names) and failed_check_names <= {"report_summary_fields_match_synthesis"}


def _expected_archive_paths(state_dir: Path, round_id: str, manifest_files: list[str]) -> set[str]:
    if manifest_files:
        return _round_archive_paths(state_dir, round_id, manifest_files)
    return _round_archive_paths(
        state_dir,
        round_id,
        [
            "codex_execution_report.md",
            "decision_packet.md",
            "pytest_result.txt",
            ARCHIVE_MANIFEST_NAME,
        ],
    )


def _report_summary_diff(
    *,
    field: str,
    expected: object,
    actual: object,
) -> dict[str, Any] | None:
    if isinstance(expected, list):
        if field == "tests_ran":
            expected_list = sorted(str(item) for item in expected)
            actual_list = sorted(str(item) for item in actual) if isinstance(actual, list) else []
        else:
            expected_list = sorted(_norm_path(item) for item in expected)
            actual_list = sorted(_norm_path(item) for item in actual) if isinstance(actual, list) else []
        if expected_list == actual_list:
            return None
        return {"field": field, "expected": expected_list, "actual": actual_list}
    if expected == actual:
        return None
    return {"field": field, "expected": expected, "actual": actual}


def build_report_summary_synthesis(
    *,
    state_dir: Path,
    repo_root: Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    decision = read_decision_meta(state_dir)
    report = read_codex_report_summary(state_dir)
    pytest_text = _read_text(state_dir / "pytest_result.txt")
    pytest_header = parse_pytest_result_header(pytest_text)
    command_plan_path = state_dir / "gates" / COMMAND_PLAN_RESULT_NAME
    command_plan_payload = _read_json(command_plan_path)
    final_gate_payload = _read_json(state_dir / "gates" / FINAL_GATE_RESULT_NAME)

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or report.get("round_id") or "")
    report_id = _expected_report_id(round_id)
    errors: list[str] = []
    warnings: list[str] = []

    commands = _command_plan_json_commands(command_plan_payload)
    command_strings = [str(item.get("command") or "") for item in commands if str(item.get("command") or "")]
    command_plan_ok = (
        bool(command_plan_payload)
        and command_plan_path.exists()
        and str(command_plan_payload.get("decision_id") or "") == decision_id
        and str(command_plan_payload.get("round_id") or "") == round_id
        and isinstance(command_plan_payload.get("commands"), list)
    )
    if not command_plan_ok:
        errors.append("command_plan.json missing, invalid, or for a different decision/round")

    delta_summary = _build_round_delta_summary(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=round_id,
        write_result=write_result,
    )
    delta_ok = (
        bool(delta_summary)
        and bool(delta_summary.get("baseline_available"))
        and str(delta_summary.get("decision_id") or "") == decision_id
        and str(delta_summary.get("round_id") or "") == round_id
    )
    if not delta_ok:
        errors.append("round_delta_summary.json missing, invalid, or not baseline-aware for current round")

    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    round_consistency = build_round_consistency(
        decision=decision,
        report=report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    archive_paths = _expected_archive_paths(state_dir, round_id, list(round_consistency.get("round_manifest_files") or []))
    round_delta_files = _string_set(
        delta_summary.get("new_dirty_files_since_baseline")
        if delta_summary.get("baseline_available")
        else delta_summary.get("final_dirty_files")
    )
    expected_files_changed = sorted(round_delta_files | archive_paths | {REPORT_SUMMARY_OUTPUT_PATH})
    expected_generated_artifacts = sorted(
        {
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            PREFLIGHT_OUTPUT_PATH,
            COMMAND_PLAN_OUTPUT_PATH,
            REPORT_SUMMARY_OUTPUT_PATH,
            SELF_OUTPUT_PATH,
            ROUND_BASELINE_OUTPUT_PATH,
            ROUND_DELTA_OUTPUT_PATH,
            *archive_paths,
        }
    )

    final_gate_status = ""
    final_gate_matches = (
        str(final_gate_payload.get("decision_id") or "") == decision_id
        and str(final_gate_payload.get("round_id") or "") == round_id
        and str(final_gate_payload.get("gate_status") or "")
    )
    if final_gate_matches:
        if _final_gate_is_report_summary_self_failure(final_gate_payload):
            final_gate_matches = False
            warnings.append(
                "final_gate_result.json contains only a self-referential report-summary failure; "
                "status fields cannot be gate-derived yet"
            )
        else:
            final_gate_status = str(final_gate_payload.get("gate_status") or "")
    else:
        warnings.append("final_gate_result.json is missing or not for current round; status fields cannot be gate-derived yet")
    status_pair = _report_status_from_gate_payload(final_gate_payload) if final_gate_matches else None

    synthesized_summary: dict[str, Any] = {
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "files_changed": expected_files_changed,
        "tests_ran": command_strings,
        "generated_artifacts": expected_generated_artifacts,
    }
    if status_pair is not None:
        synthesized_summary["status"] = status_pair[0]
        synthesized_summary["acceptance_recommendation"] = status_pair[1]

    if not isinstance(pytest_header.get("tests_ran"), list) or not pytest_header.get("tests_ran"):
        errors.append("pytest_result_summary.tests_ran missing or empty")
    else:
        pytest_tests = {str(item) for item in pytest_header.get("tests_ran") or []}
        missing_pytest_tests = sorted(set(command_strings) - pytest_tests)
        if missing_pytest_tests:
            errors.append(f"pytest_result_summary.tests_ran omits command_plan commands: {missing_pytest_tests}")

    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    report_files_changed = _string_set(report.get("files_changed"))
    inherited_claimed = sorted(inherited_dirty_files & report_files_changed)
    if inherited_claimed:
        errors.append(f"files_changed includes inherited dirty files: {inherited_claimed}")

    diffs: list[dict[str, Any]] = []
    for field in (
        "report_id",
        "round_id",
        "based_on_decision_id",
        "status",
        "acceptance_recommendation",
        "files_changed",
        "tests_ran",
        "generated_artifacts",
    ):
        if field not in synthesized_summary:
            continue
        diff = _report_summary_diff(field=field, expected=synthesized_summary[field], actual=report.get(field))
        if diff:
            diffs.append(diff)

    synthesis_status = "FAILED" if errors or diffs else ("WARN" if warnings else "PASSED")
    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "artifact_name": REPORT_SUMMARY_RESULT_NAME,
        "gate_name": REPORT_SUMMARY_NAME,
        "synthesis_status": synthesis_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report.get("report_id") or "",
        "generated_at": _now_iso(),
        "synthesized_summary": synthesized_summary,
        "diffs": diffs,
        "errors": errors,
        "warnings": warnings,
        "sources": {
            "decision_meta": "project_state/decision_packet.md",
            "command_plan": COMMAND_PLAN_OUTPUT_PATH,
            "round_delta_summary": ROUND_DELTA_OUTPUT_PATH,
            "final_gate_result": SELF_OUTPUT_PATH,
            "pytest_result": "project_state/pytest_result.txt",
        },
    }
    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / REPORT_SUMMARY_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def _report_summary_checks(
    *,
    state_dir: Path,
    repo_root: Path,
    decision_text: str,
    report: dict[str, Any],
    write_result: bool,
) -> list[dict[str, Any]]:
    command_plan_payload = _read_json(state_dir / "gates" / COMMAND_PLAN_RESULT_NAME)
    required = _report_summary_required(
        decision_text=decision_text,
        report=report,
        command_plan_payload=command_plan_payload,
    )
    if not required:
        return [
            _check(
                "report_summary_synthesis_required",
                "PASS",
                "report-summary synthesis is not required for this report",
                required=False,
            )
        ]

    synthesis = build_report_summary_synthesis(
        state_dir=state_dir,
        repo_root=repo_root,
        write_result=write_result,
    )
    errors = list(synthesis.get("errors") or [])
    diffs = list(synthesis.get("diffs") or [])
    warnings = list(synthesis.get("warnings") or [])
    return [
        _check(
            "report_summary_synthesis_required",
            "PASS",
            "report-summary synthesis is required for this report",
            required=True,
            artifact=REPORT_SUMMARY_OUTPUT_PATH,
        ),
        _check(
            "report_summary_fields_match_synthesis",
            "PASS" if not errors and not diffs else "FAIL",
            "codex_report_summary matches synthesized summary"
            if not errors and not diffs
            else "codex_report_summary differs from synthesized summary",
            errors=errors,
            diffs=diffs,
        ),
        _check(
            "report_summary_status_source_available",
            "PASS" if not warnings else "WARN",
            "report summary status fields are derived from final gate result"
            if not warnings
            else "report summary synthesis has source warnings",
            warnings=warnings,
        ),
    ]


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
    decision_text = _read_text(state_dir / "decision_packet.md")
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
    archive_pending_status = "FAIL" if manifest_present else "WARN"
    checks.append(
        _check(
            "round_manifest_present",
            "PASS" if manifest_present else archive_pending_status,
            "round manifest is present" if manifest_present else "round manifest is missing",
            round_manifest_path=round_consistency.get("round_manifest_path") or "",
        )
    )

    archived_report_match = _archive_file_matches_live(state_dir, round_id, "codex_execution_report.md")
    checks.append(
        _check(
            "archived_report_matches_live_report",
            "PASS" if archived_report_match is True else archive_pending_status,
            "archived report matches live report" if archived_report_match is True else "archived report differs from live report",
        )
    )

    archived_pytest_match = _archive_file_matches_live(state_dir, round_id, "pytest_result.txt")
    checks.append(
        _check(
            "archived_pytest_result_matches_live_pytest_result",
            "PASS" if archived_pytest_match is True else archive_pending_status,
            (
                "archived pytest_result matches live pytest_result"
                if archived_pytest_match is True
                else "archived pytest_result differs from live pytest_result"
            ),
        )
    )

    files_changed = _string_set(report.get("files_changed"))
    archive_paths = _round_archive_paths(state_dir, round_id, manifest_files)
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    delta_summary = _build_round_delta_summary(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=round_id,
        write_result=write_result,
    )
    changed_files = _string_set(delta_summary.get("final_dirty_files"))
    checks.extend(
        _round_delta_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            generated_artifacts=generated_artifacts,
            archive_paths=archive_paths,
        )
    )
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

    checks.extend(
        _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=decision,
            report=report,
            pytest_text=pytest_text,
        )
    )

    checks.extend(
        _report_summary_checks(
            state_dir=state_dir,
            repo_root=repo_root,
            decision_text=decision_text,
            report=report,
            write_result=write_result,
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


def _failed_check_names(result: dict[str, Any]) -> set[str]:
    return {
        str(check.get("name") or "")
        for check in result.get("checks", [])
        if isinstance(check, dict) and check.get("status") == "FAIL"
    }


def _check_by_name(result: dict[str, Any], name: str) -> dict[str, Any]:
    for check in result.get("checks", []):
        if isinstance(check, dict) and check.get("name") == name:
            return check
    return {}


def _status_policy_failure_is_archive_pending(
    *,
    result: dict[str, Any],
    decision: dict[str, Any],
) -> bool:
    status_policy = _check_by_name(result, "status_policy_valid")
    if status_policy.get("status") != "FAIL":
        return False
    if status_policy.get("report_status") != "SUCCESS":
        return False
    if str(decision.get("mainline") or "") != "engineering_branch":
        return False

    failed = _failed_check_names(result)
    allowed = ARCHIVE_PENDING_CHECKS | {"status_policy_valid"}
    if not failed <= allowed:
        return False

    status_summary_payload = result.get("status_summary")
    status_summary_map = status_summary_payload if isinstance(status_summary_payload, dict) else {}
    if status_summary_map.get("archive_status") != "not_archived":
        return False

    errors = [str(error) for error in (status_policy.get("lint_errors") or [])]
    if not errors or any("artifact" not in error.lower() for error in errors):
        return False

    warnings = {str(warning) for warning in (status_policy.get("warnings") or [])}
    return warnings <= {"report round not archived yet", "doctor status is WARN"}


def _valid_close_round_id(round_id: str) -> bool:
    if not round_id:
        return False
    return "/" not in round_id and "\\" not in round_id and ".." not in round_id


def _close_round_archive_payload(
    *,
    state_dir: Path,
    round_id: str,
    status: str,
    archive_result: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    manifest_path = state_dir / "rounds" / round_id / ARCHIVE_MANIFEST_NAME if round_id else state_dir / "rounds" / ARCHIVE_MANIFEST_NAME
    manifest = _read_json(manifest_path)
    manifest_files = sorted(str(name) for name in (manifest.get("files") or {}).keys())
    files = [*manifest_files, ARCHIVE_MANIFEST_NAME] if manifest_files else []
    payload: dict[str, Any] = {
        "status": status,
        "round_manifest_path": _state_relative_path(state_dir, manifest_path) if round_id else "",
        "files": files,
        "included_diff": bool(manifest.get("included_diff")) if manifest else False,
        "included_state_snapshot": bool(manifest.get("included_state_snapshot")) if manifest else False,
        "copied": list((archive_result or {}).get("copied") or []),
        "idempotent": (archive_result or {}).get("status") == "no-op",
    }
    if error:
        payload["error"] = error
    return payload


def _close_round_recommended_next_action(close_status: str) -> str:
    if close_status == "CLOSED":
        return "no_action_required"
    if close_status == "INVALID":
        return "fix_close_round_usage_or_metadata_before_retry"
    if close_status == "BLOCKED":
        return "fix_blocking_closeout_preconditions_before_archive"
    return "fix_close_round_failures_before_retry"


def close_round(*, state_dir: Path, round_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    requested_round_id = str(round_id or "")

    invalid_reasons: list[str] = []
    if not state_dir.exists() or not state_dir.is_dir():
        invalid_reasons.append(f"state_dir is not a directory: {state_dir}")
    if not _valid_close_round_id(requested_round_id):
        invalid_reasons.append(f"invalid round_id: {requested_round_id}")
    if invalid_reasons:
        return {
            "schema_version": GATE_RESULT_SCHEMA_VERSION,
            "gate_name": CLOSE_ROUND_NAME,
            "close_status": "INVALID",
            "decision_id": "",
            "report_id": "",
            "round_id": requested_round_id,
            "generated_at": _now_iso(),
            "checks": [
                _check("close_round_usage_valid", "FAIL", reason)
                for reason in invalid_reasons
            ],
            "actions": [],
            "archive": _close_round_archive_payload(
                state_dir=state_dir,
                round_id=requested_round_id,
                status="not_attempted",
            ),
            "blocking_reasons": invalid_reasons,
            "warnings": [],
            "recommended_next_action": _close_round_recommended_next_action("INVALID"),
            "status_summary": {},
        }

    decision = read_decision_meta(state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")
    report = read_codex_report_summary(state_dir)
    pytest_text = _read_text(state_dir / "pytest_result.txt")
    pytest_validation = validate_pytest_result_for_report(pytest_text, report)
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")

    decision_id = str(decision.get("decision_id") or "")
    report_id = str(report.get("report_id") or "")
    decision_round_id = str(decision.get("round_id") or "")
    report_round_id = str(report.get("round_id") or "")
    decision_status = str(decision.get("status") or "UNKNOWN")
    report_status = str(report.get("status") or "UNKNOWN")
    checks: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    archive_payload = _close_round_archive_payload(
        state_dir=state_dir,
        round_id=requested_round_id,
        status="not_attempted",
    )

    parse_error = decision.get("parse_error")
    decision_parse_ok = bool(decision_id and decision_round_id and not parse_error)
    checks.append(
        _check(
            "decision_meta_parse",
            "PASS" if decision_parse_ok else "FAIL",
            "decision_meta parsed" if decision_parse_ok else "decision_meta missing or invalid",
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

    report_parse_error = report.get("parse_error")
    critical_metadata_errors = [str(error) for error in (parse_error, report_parse_error) if error]
    report_present = bool(report_id and report_round_id and not report_parse_error)
    checks.append(
        _check(
            "report_present",
            "PASS" if report_present else "FAIL",
            "codex report summary parsed" if report_present else "codex report summary missing or invalid",
            parse_error=report_parse_error,
        )
    )

    round_match = bool(
        requested_round_id
        and decision_round_id
        and report_round_id
        and requested_round_id == decision_round_id == report_round_id
    )
    checks.append(
        _check(
            "requested_round_id_match",
            "PASS" if round_match else "FAIL",
            "requested round_id matches decision and report"
            if round_match
            else "requested round_id does not match decision/report round_id",
            requested_round_id=requested_round_id,
            decision_round_id=decision_round_id,
            report_round_id=report_round_id,
        )
    )

    report_decision_ok = bool(decision_id and report.get("based_on_decision_id") == decision_id)
    checks.append(
        _check(
            "report_decision_match",
            "PASS" if report_decision_ok else "FAIL",
            "report is based on current decision" if report_decision_ok else "report based_on_decision_id does not match decision",
            report_based_on_decision_id=report.get("based_on_decision_id"),
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
            "PASS" if pytest_covers is True else "FAIL",
            "pytest_result covers report tests" if pytest_covers is True else "pytest_result does not cover report tests",
            missing_report_tests=pytest_validation.get("missing_report_tests") or [],
        )
    )

    checks.extend(
        _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=decision,
            report=report,
            pytest_text=pytest_text,
        )
    )

    files_changed = _string_set(report.get("files_changed"))
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    round_consistency = build_round_consistency(
        decision=decision,
        report=report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    manifest_files = list(round_consistency.get("round_manifest_files") or [])
    archive_paths = _round_archive_paths(state_dir, requested_round_id, manifest_files)
    delta_summary = _build_round_delta_summary(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=requested_round_id,
        write_result=True,
    )
    changed_files = _string_set(delta_summary.get("final_dirty_files"))
    checks.extend(
        _round_delta_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            generated_artifacts=generated_artifacts,
            archive_paths=archive_paths,
        )
    )

    checks.extend(
        _report_summary_checks(
            state_dir=state_dir,
            repo_root=repo_root,
            decision_text=decision_text,
            report=report,
            write_result=True,
        )
    )

    missing_archive_artifacts = sorted(archive_paths - generated_artifacts)
    checks.append(
        _check(
            "generated_artifacts_cover_round_archive",
            "PASS" if not missing_archive_artifacts else "FAIL",
            "generated_artifacts covers round archive files"
            if not missing_archive_artifacts
            else "generated_artifacts omits round archive files",
            missing_artifacts=missing_archive_artifacts,
        )
    )

    forbidden_hits = _forbidden_hits(changed_files | files_changed | generated_artifacts | archive_paths)
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

    status = status_summary(state_dir=state_dir)
    state_package_ok = str(status.get("state_package_classification_status") or "PASS") != "FAIL"
    checks.append(
        _check(
            "state_package_compact",
            "PASS" if state_package_ok else "FAIL",
            "state package classification is compact or non-blocking"
            if state_package_ok
            else "state package classification reports blocking expansion",
            state_package_classification_status=status.get("state_package_classification_status"),
            state_package_entries_compacted=status.get("state_package_entries_compacted"),
        )
    )

    precheck_failures = [check for check in checks if check.get("status") == "FAIL"]
    if critical_metadata_errors:
        close_status = "INVALID"
        archive_payload = _close_round_archive_payload(
            state_dir=state_dir,
            round_id=requested_round_id,
            status="not_attempted",
            error="; ".join(critical_metadata_errors),
        )
    elif precheck_failures:
        close_status = "FAILED"
    else:
        before = final_check(state_dir=state_dir, repo_root=repo_root, write_result=True)
        before_failed = _failed_check_names(before)
        allowed_pending = set(ARCHIVE_PENDING_CHECKS)
        if _status_policy_failure_is_archive_pending(result=before, decision=decision):
            allowed_pending.add("status_policy_valid")
        unexpected_before = sorted(before_failed - allowed_pending)
        expected_archive_pending = sorted(before_failed & allowed_pending)
        actions.append(
            {
                "name": "final_check_before_archive",
                "status": "PASSED" if not unexpected_before else "FAILED",
                "gate_status": before.get("gate_status"),
                "allowed_archive_pending_failures": expected_archive_pending,
                "unexpected_failures": unexpected_before,
                "artifact": f"project_state/gates/{FINAL_GATE_RESULT_NAME}",
            }
        )
        if unexpected_before:
            close_status = "FAILED"
        else:
            try:
                archive_result = archive_round(state_dir=state_dir, round_id=requested_round_id)
            except FileExistsError as exc:
                actions.append({"name": "archive_round", "status": "FAILED", "error": str(exc)})
                archive_payload = _close_round_archive_payload(
                    state_dir=state_dir,
                    round_id=requested_round_id,
                    status="FAILED",
                    error=str(exc),
                )
                close_status = "FAILED"
            else:
                actions.append(
                    {
                        "name": "archive_round",
                        "status": archive_result.get("status"),
                        "round_dir": archive_result.get("round_dir"),
                        "manifest": archive_result.get("manifest"),
                        "copied": archive_result.get("copied") or [],
                    }
                )
                archive_payload = _close_round_archive_payload(
                    state_dir=state_dir,
                    round_id=requested_round_id,
                    status=str(archive_result.get("status") or "archived"),
                    archive_result=archive_result,
                )
                after = final_check(state_dir=state_dir, repo_root=repo_root, write_result=True)
                after_failed = _failed_check_names(after)
                actions.append(
                    {
                        "name": "final_check_after_archive",
                        "status": "PASSED" if not after_failed else "FAILED",
                        "gate_status": after.get("gate_status"),
                        "unexpected_failures": sorted(after_failed),
                        "artifact": f"project_state/gates/{FINAL_GATE_RESULT_NAME}",
                    }
                )
                close_status = "CLOSED" if not after_failed else "FAILED"

    warnings = [f"{check['name']}: {check['detail']}" for check in checks if check.get("status") == "WARN"]
    blocking_reasons = [f"{check['name']}: {check['detail']}" for check in checks if check.get("status") == "FAIL"]
    for action in actions:
        if action.get("status") == "FAILED":
            blocking_reasons.append(f"{action.get('name')}: {action.get('error') or action.get('unexpected_failures')}")
    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": CLOSE_ROUND_NAME,
        "close_status": close_status,
        "decision_id": decision_id,
        "report_id": report_id,
        "round_id": requested_round_id,
        "decision_round_id": decision_round_id,
        "report_round_id": report_round_id,
        "report_status": report_status,
        "generated_at": _now_iso(),
        "checks": checks,
        "actions": actions,
        "archive": archive_payload,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "recommended_next_action": _close_round_recommended_next_action(close_status),
        "status_summary": {
            "decision_execution_state": status.get("decision_execution_state"),
            "archive_status": status.get("archive_status"),
            "report_status": status.get("report_status"),
            "report_acceptance_recommendation": status.get("report_acceptance_recommendation"),
        },
    }
    return result


def _preflight_recommended_next_action(gate_status: str) -> str:
    if gate_status == "PASSED":
        return "proceed_with_decision_scope"
    if gate_status == "BLOCKED":
        return "do_not_start_consumed_or_stale_decision"
    if gate_status == "WARN":
        return "review_preflight_warnings_before_starting"
    return "fix_preflight_failures_before_starting"


def _command_kind(command: str) -> str:
    lowered = command.lower()
    if lowered == "pwd" or lowered.startswith("pwd "):
        return "pwd"
    if "python -m pytest" in lowered or lowered.startswith("pytest"):
        return "pytest"
    if "project_gate" in lowered and "preflight" in lowered:
        return "preflight"
    if "project_gate" in lowered and "command-plan" in lowered:
        return "command-plan"
    if "project_gate" in lowered and "report-summary" in lowered:
        return "report-summary"
    if "project_gate" in lowered and "close-round" in lowered:
        return "close-round"
    if "project_gate" in lowered and "final-check" in lowered:
        return "final-check"
    if "project_state" in lowered and "archive-round" in lowered:
        return "archive-round"
    if "project_state" in lowered and "lint-report" in lowered:
        return "lint-report"
    if "project_state" in lowered and " doctor" in lowered:
        return "doctor"
    if "project_state" in lowered and " status" in lowered:
        return "status"
    if lowered.startswith("git status") or " git status" in lowered:
        return "git status"
    if lowered.startswith("git rev-parse") or " git rev-parse" in lowered:
        return "git rev-parse"
    if lowered.startswith("git diff") or " git diff" in lowered:
        return "git diff"
    if lowered.startswith("git ls-files") or " git ls-files" in lowered:
        return "git ls-files"
    if lowered.startswith("git rm") or " git rm" in lowered:
        return "git rm"
    if "local_reverse_training_review" in lowered and " build" in lowered:
        return "build"
    if "python -c" in lowered:
        return "python-inline"
    if "test-path" in lowered:
        return "test-path"
    if lowered.startswith("powershell ") or lowered == "powershell":
        return "powershell"
    return "unknown"


def _command_phase(kind: str, *, archive_seen: bool) -> str:
    if archive_seen and kind != "archive-round":
        return "post_archive"
    if kind == "preflight":
        return "preflight"
    if kind == "pytest":
        return "test"
    if kind == "archive-round":
        return "archive"
    if kind in {"final-check", "command-plan", "report-summary", "close-round"}:
        return "gate"
    if kind in {
        "lint-report",
        "status",
        "doctor",
        "git status",
        "git rev-parse",
        "git diff",
        "git ls-files",
        "git rm",
        "build",
        "python-inline",
        "powershell",
        "test-path",
        "pwd",
    }:
        return "status"
    return "unknown"


def _decision_allows_expected_nonzero_preflight(decision_text: str) -> bool:
    lowered = decision_text.lower()
    return (
        "preflight" in lowered
        and (
            "expected nonzero" in lowered
            or "expected non-zero" in lowered
            or "expected non zero" in lowered
            or "expected nonzero diagnostic" in lowered
            or "expected nonzero diagnostic" in lowered.replace("-", "")
            or "预期非 0" in lowered
            or "预期非0" in lowered
        )
    )


def _command_expected_exit_codes(
    *,
    kind: str,
    phase: str,
    command: str,
    decision_text: str,
) -> tuple[list[int], str, str | None]:
    if kind == "preflight" and phase != "preflight":
        if _decision_allows_expected_nonzero_preflight(decision_text):
            return [1], "post-report preflight expected nonzero diagnostic", None
        return [0], "post-report preflight is not explicitly marked expected nonzero", (
            f"command '{command}' looks like a post-report preflight diagnostic without expected nonzero wording"
        )
    if kind == "unknown":
        return [0], "unknown command kind; defaulting to zero exit", None
    return [0], f"{kind} expected to exit 0", None


def _command_plan_recommended_next_action(plan_status: str) -> str:
    if plan_status == "PASSED":
        return "record_and_follow_command_plan_manually"
    if plan_status == "WARN":
        return "review_command_plan_warnings_before_execution"
    return "fix_decision_tests_block_before_execution"


def _decision_requests_report_summary(decision_text: str) -> bool:
    lowered = decision_text.lower()
    return "report-summary" in lowered or "synth-report" in lowered or "report summary" in lowered


def _inject_report_summary_command(extracted_commands: list[str], decision_text: str) -> list[str]:
    command = "python -m reverse_agent.project_gate report-summary --state-dir project_state"
    if not _decision_requests_report_summary(decision_text):
        return extracted_commands
    if any("project_gate" in item and "report-summary" in item for item in extracted_commands):
        return extracted_commands
    insert_at = next(
        (
            index
            for index, item in enumerate(extracted_commands)
            if "lint-report" in item or ("project_gate" in item and "final-check" in item)
        ),
        len(extracted_commands),
    )
    return [*extracted_commands[:insert_at], command, *extracted_commands[insert_at:]]


def command_plan(*, state_dir: Path, write_result: bool = True) -> dict[str, Any]:
    state_dir = Path(state_dir)
    decision = read_decision_meta(state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")
    tests_text = _markdown_section(decision_text, "Tests")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if not tests_text.strip():
        blocking_reasons.append("Tests section is missing")
    else:
        extracted_commands, extract_error = _extract_bash_commands(tests_text)
        if extract_error:
            blocking_reasons.append(extract_error)
        extracted_commands = _inject_report_summary_command(extracted_commands, decision_text)
        archive_seen = False
        for index, command in enumerate(extracted_commands, start=1):
            kind = _command_kind(command)
            phase = _command_phase(kind, archive_seen=archive_seen)
            expected_exit_codes, notes, blocking_reason = _command_expected_exit_codes(
                kind=kind,
                phase=phase,
                command=command,
                decision_text=decision_text,
            )
            if kind == "unknown":
                warnings.append(f"command {index} has unknown kind: {command}")
            if blocking_reason:
                blocking_reasons.append(blocking_reason)
            commands.append(
                {
                    "index": index,
                    "command": command,
                    "phase": phase,
                    "kind": kind,
                    "required": True,
                    "expected_exit_codes": expected_exit_codes,
                    "records_stdout_stderr": True,
                    "notes": notes,
                }
            )
            if kind == "archive-round":
                archive_seen = True

    plan_status = "FAILED" if blocking_reasons else ("WARN" if warnings else "PASSED")
    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "plan_name": COMMAND_PLAN_NAME,
        "plan_status": plan_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "commands": commands,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
        "recommended_next_action": _command_plan_recommended_next_action(plan_status),
    }

    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / COMMAND_PLAN_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


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
    baseline = _capture_round_baseline(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=round_id,
        write_result=write_result,
    )

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
        if _scope_path_has_runtime_token(path)
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
        "round_baseline": {
            "path": ROUND_BASELINE_OUTPUT_PATH,
            "baseline_dirty_files": baseline.get("baseline_dirty_files") or [],
            "head_commit": baseline.get("head_commit") or "",
        },
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


def _print_command_plan(result: dict[str, Any]) -> None:
    print(f"{result.get('plan_name')}: {result.get('plan_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"round_id: {result.get('round_id')}")
    print(f"mainline: {result.get('mainline')}")
    for command in result.get("commands", []):
        print(
            "  "
            f"[{command.get('index')}] "
            f"{command.get('phase')} "
            f"{command.get('kind')}: "
            f"{command.get('command')} "
            f"expected_exit={command.get('expected_exit_codes')}"
        )
    for warning in result.get("warnings", []):
        print(f"  [WARN] {warning}")
    for reason in result.get("blocking_reasons", []):
        print(f"  [BLOCK] {reason}")
    print(f"recommended_next_action: {result.get('recommended_next_action')}")


def _print_report_summary(result: dict[str, Any]) -> None:
    print(f"{result.get('gate_name')}: {result.get('synthesis_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"report_id: {result.get('report_id')}")
    print(f"round_id: {result.get('round_id')}")
    for error in result.get("errors", []):
        print(f"  [ERROR] {error}")
    for diff in result.get("diffs", []):
        print(f"  [DIFF] {diff.get('field')}")
    for warning in result.get("warnings", []):
        print(f"  [WARN] {warning}")
    print(f"artifact: {REPORT_SUMMARY_OUTPUT_PATH}")


def _print_close_round(result: dict[str, Any]) -> None:
    print(f"{result.get('gate_name')}: {result.get('close_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"report_id: {result.get('report_id')}")
    print(f"round_id: {result.get('round_id')}")
    for check in result.get("checks", []):
        print(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    for action in result.get("actions", []):
        print(f"  [ACTION {action.get('status')}] {action.get('name')}")
    archive = result.get("archive") if isinstance(result.get("archive"), dict) else {}
    print(f"archive_status: {archive.get('status')}")
    for reason in result.get("blocking_reasons", []):
        print(f"  [BLOCK] {reason}")
    print(f"recommended_next_action: {result.get('recommended_next_action')}")


def _final_check_exit_code(gate_status: object) -> int:
    return 1 if gate_status == "FAILED" else 0


def _preflight_exit_code(gate_status: object) -> int:
    # WARN remains non-blocking so teams can review warnings without hiding hard stops.
    return 1 if gate_status in {"BLOCKED", "FAILED"} else 0


def _close_round_exit_code(close_status: object) -> int:
    if close_status == "INVALID":
        return 2
    return 0 if close_status == "CLOSED" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project closeout gate checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    final_parser = subparsers.add_parser("final-check", help="Run final closeout gate.")
    final_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    final_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    preflight_parser = subparsers.add_parser("preflight", help="Run preflight start gate.")
    preflight_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    preflight_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    command_plan_parser = subparsers.add_parser("command-plan", help="Generate a read-only command execution plan.")
    command_plan_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    command_plan_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    report_summary_parser = subparsers.add_parser("report-summary", help="Synthesize and validate codex_report_summary.")
    report_summary_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    report_summary_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    close_round_parser = subparsers.add_parser("close-round", help="Run final-check, archive the round, and re-check.")
    close_round_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    close_round_parser.add_argument("--round-id", required=True)
    close_round_parser.add_argument("--json", action="store_true", help="Print JSON result.")

    args = parser.parse_args(argv)
    if args.command == "final-check":
        result = final_check(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return _final_check_exit_code(result.get("gate_status"))
    if args.command == "preflight":
        result = preflight(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return _preflight_exit_code(result.get("gate_status"))
    if args.command == "command-plan":
        result = command_plan(state_dir=Path(args.state_dir))
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_command_plan(result)
        return 1 if result.get("plan_status") == "FAILED" else 0
    if args.command == "report-summary":
        result = build_report_summary_synthesis(state_dir=Path(args.state_dir), repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_report_summary(result)
        return 1 if result.get("synthesis_status") == "FAILED" else 0
    if args.command == "close-round":
        result = close_round(state_dir=Path(args.state_dir), round_id=args.round_id, repo_root=Path.cwd())
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_close_round(result)
        return _close_round_exit_code(result.get("close_status"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
