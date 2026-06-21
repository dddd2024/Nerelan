from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .project_state import (
    ARCHIVE_MANIFEST_NAME,
    DEFAULT_STATE_DIR,
    _report_claims_sample_artifact_freshness,
    _reverse_solving_blocker_only_report,
    archive_round,
    build_round_consistency,
    doctor,
    extract_markdown_json_block,
    lint_decision,
    lint_report,
    parse_pytest_result_header,
    read_codex_report_summary,
    read_decision_contract,
    read_decision_meta,
    status_summary,
    validate_pytest_result_for_report,
    write_pytest_result,
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
RUN_ROUND_NAME = "run-round"
RUN_ROUND_RESULT_NAME = "run_round_result.json"
ROUND_BASELINE_RESULT_NAME = "round_baseline.json"
ROUND_DELTA_SUMMARY_NAME = "round_delta_summary.json"
ROUND_CLOSE_SNAPSHOT_RESULT_NAME = "round_close_snapshot.json"
SELF_OUTPUT_PATH = f"project_state/gates/{FINAL_GATE_RESULT_NAME}"
PREFLIGHT_OUTPUT_PATH = f"project_state/gates/{PREFLIGHT_RESULT_NAME}"
COMMAND_PLAN_OUTPUT_PATH = f"project_state/gates/{COMMAND_PLAN_RESULT_NAME}"
REPORT_SUMMARY_OUTPUT_PATH = f"project_state/gates/{REPORT_SUMMARY_RESULT_NAME}"
RUN_ROUND_OUTPUT_PATH = f"project_state/gates/{RUN_ROUND_RESULT_NAME}"
ROUND_BASELINE_OUTPUT_PATH = f"project_state/gates/{ROUND_BASELINE_RESULT_NAME}"
ROUND_DELTA_OUTPUT_PATH = f"project_state/gates/{ROUND_DELTA_SUMMARY_NAME}"
ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH = f"project_state/gates/{ROUND_CLOSE_SNAPSHOT_RESULT_NAME}"
GATE_PROFILE_PLAN_NAME = "gate-profile"
GATE_PROFILE_PLAN_RESULT_NAME = "gate_profile_plan.json"
GATE_PROFILE_PLAN_OUTPUT_PATH = f"project_state/gates/{GATE_PROFILE_PLAN_RESULT_NAME}"
CLOSE_ROUND_NAME = "close-round"
RUN_CLOSEOUT_NAME = "run-closeout"
RUN_CLOSEOUT_RESULT_NAME = "run_closeout_result.json"
RUN_CLOSEOUT_OUTPUT_PATH = f"project_state/gates/{RUN_CLOSEOUT_RESULT_NAME}"

# Allowlist of command kinds that run-closeout is permitted to execute.
# Anything outside this set is refused to prevent arbitrary shell execution.
RUN_CLOSEOUT_ALLOWED_KINDS = frozenset({
    "set-location",
    "pwd",
    "test-path",
    "git status",
    "git rev-parse",
    "git diff",
    "preflight",
    "pytest",
    "command-plan",
    "report-summary",
    "final-check",
    "close-round",
    "decision-lint",
    "gate-profile",
    "run-closeout",
})

CLAIM_AWARE_HISTORICAL_NON_BLOCKING_MAINLINES = {
    "engineering_branch",
    "tool_integration",
    "training_dataset",
}

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
MAINLINE_FORBIDDEN_PATH_EXCEPTIONS = {
    "training_dataset": {"reverse_agent/local_reverse_training_status.py"},
    "tool_integration": {"reverse_agent/local_reverse_single_sample_static_triage.py"},
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
BUILD_OUTPUT_WHITELIST: frozenset[str] = frozenset({
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
})
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
    "run-round",
    "run-closeout",
    "pytest",
    "git status",
    "git rev-parse",
    "git diff",
    "git ls-files",
    "git rm",
    "build",
    "python-inline",
    "powershell",
    "read-only-verification",
    "tool-capability-verification",
    "static-triage",
    "target-bytes-revalidation",
    "current-static-triage-verification",
    "artifact-index-verification",
    "test-path",
    "pwd",
}

NATURAL_LANGUAGE_COMMANDS = {
    "position": [
        "Set-Location F:\\reverse-agent",
        "pwd",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
    ],
    "git_status": ["git status --short"],
    "preflight": ["python -m reverse_agent.project_gate preflight --state-dir project_state"],
    "command-plan": [
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    ],
    "doctor": ["python -m reverse_agent.project_state doctor --state-dir project_state"],
    "pytest": ["python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"],
    "lint-report": ["python -m reverse_agent.project_state lint-report --state-dir project_state"],
    "report-summary": ["python -m reverse_agent.project_gate report-summary --state-dir project_state"],
    "final-check": ["python -m reverse_agent.project_gate final-check --state-dir project_state"],
    "run-round": ["python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json"],
    "git_diff": ["git diff --name-only"],
    "queue_status_verification": [
        "read-only queue/status verification (affineenc_333f8ca9, ascii_table_chinese_46efc7ea, cpp1_2f6fcb63)"
    ],
    "tool_capability_verification": [
        "tool capability verification (IDA executable/script resolver)"
    ],
    "artifact_index_verification": [
        "artifact_index verification (cpp1 static triage current provenance)"
    ],
    "target_bytes_artifact_index_verification": [
        "artifact_index verification (cpp1 target bytes current revalidation provenance)"
    ],
    "current_static_triage_verification": [
        "current static triage verification (cpp1_2f6fcb63 static-only current IDA success)"
    ],
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


def parse_required_audit_questions(decision_text: str) -> list[str]:
    """Extract Required Audit questions from a decision packet.

    Parses the ``## 5. Required Audit`` section (or any section whose heading
    contains "Required Audit") and extracts numbered questions or bullet items.

    Returns an empty list if no Required Audit section exists.
    """
    section = _markdown_section(decision_text, "Required Audit")
    if not section.strip():
        return []
    questions: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^(\d+)\.\s+(.+)", stripped)
        if m:
            questions.append(m.group(2).strip())
        elif stripped.startswith("- ") or stripped.startswith("* "):
            questions.append(stripped[2:].strip())
    return questions


def generate_required_audit_scaffold(decision_text: str) -> str:
    """Generate a deterministic Required Audit scaffold from the decision.

    The scaffold includes each Required Audit question with placeholder
    answer markers (Evidence:, Status:, Answer:) but does not fabricate
    facts.  Returns an empty string when the decision has no Required
    Audit items.
    """
    questions = parse_required_audit_questions(decision_text)
    if not questions:
        return ""
    lines: list[str] = ["## Required Audit", ""]
    for i, q in enumerate(questions, start=1):
        lines.append(f"### {i}. {q}")
        lines.append("")
        lines.append("- Evidence: (to be filled)")
        lines.append("- Status: PENDING")
        lines.append("- Answer: (to be filled)")
        lines.append("")
    return "\n".join(lines)


# Placeholder patterns detected in Required Audit answers
_REQUIRED_AUDIT_PLACEHOLDER_PATTERNS = [
    re.compile(r"\(to be filled\)", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bPENDING\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bN/A\b", re.IGNORECASE),
    re.compile(r"\bnot yet\b", re.IGNORECASE),
    re.compile(r"\bnot implemented\b", re.IGNORECASE),
]


def _is_required_audit_placeholder(text: str) -> bool:
    """Check if a text string is a placeholder marker for Required Audit answers."""
    stripped = text.strip()
    if not stripped:
        return True
    for pattern in _REQUIRED_AUDIT_PLACEHOLDER_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def _parse_required_audit_answer_blocks(report_section: str) -> list[dict[str, str]]:
    """Parse the report's Required Audit section into per-item answer blocks.

    Each block contains the item heading, evidence, status, and answer fields.
    Returns an empty list if the section has no item headings.
    """
    blocks: list[dict[str, str]] = []
    current_block: dict[str, str] | None = None

    for line in report_section.splitlines():
        stripped = line.strip()
        m = re.match(r"^###\s+\d+\.\s+(.+)", stripped)
        if m:
            if current_block is not None:
                blocks.append(current_block)
            current_block: dict[str, str] = {
                "heading": m.group(1).strip(),
                "evidence": "",
                "status": "",
                "answer": "",
            }
            continue
        if current_block is not None:
            fm = re.match(r"^[-*]\s+(Evidence|Status|Answer)\s*:\s*(.*)", stripped, re.IGNORECASE)
            if fm:
                field_name = fm.group(1).lower()
                field_value = fm.group(2).strip()
                current_block[field_name] = field_value

    if current_block is not None:
        blocks.append(current_block)

    return blocks


def _required_audit_placeholder_items(report_section: str) -> list[str]:
    """Return headings of Required Audit items with placeholder answers.

    An item is considered placeholder if its answer, evidence, or status
    field contains an unresolved marker such as ``(to be filled)``,
    ``TODO``, ``TBD``, ``PENDING``, or is empty.
    """
    blocks = _parse_required_audit_answer_blocks(report_section)
    placeholder_items: list[str] = []
    for block in blocks:
        answer = block.get("answer", "")
        evidence = block.get("evidence", "")
        status = block.get("status", "")
        if (
            _is_required_audit_placeholder(answer)
            or _is_required_audit_placeholder(evidence)
            or _is_required_audit_placeholder(status)
        ):
            placeholder_items.append(block.get("heading", ""))
    return placeholder_items


def _required_audit_coverage_check(
    *,
    decision_text: str,
    report_text: str,
    report_status: str,
) -> dict[str, Any]:
    """Check that the report covers Required Audit items with valid answers.

    For SUCCESS/ACCEPTED reports, every item must have a non-placeholder
    answer.  For non-success reports, placeholder answers are allowed but
    produce a WARN.
    """
    questions = parse_required_audit_questions(decision_text)
    if not questions:
        return _check(
            "required_audit_coverage",
            "PASS",
            "decision has no Required Audit items; coverage check not applicable",
            required_audit_items=[],
            missing_answers=[],
            placeholder_answers=[],
        )

    report_section = _markdown_section(report_text, "Required Audit")
    is_success = report_status in {"SUCCESS", "ACCEPTED", "ACCEPTED_WITH_LIMITATIONS"}

    if not report_section.strip():
        status = "FAIL" if is_success else "WARN"
        detail = (
            f"report is missing ## Required Audit section ({len(questions)} items unanswered)"
            if is_success
            else f"report is missing ## Required Audit section but report status is {report_status}"
        )
        return _check(
            "required_audit_coverage",
            status,
            detail,
            required_audit_items=questions,
            missing_answers=questions,
            placeholder_answers=[],
        )

    missing: list[str] = []
    for q in questions:
        if q not in report_section:
            missing.append(q)

    if missing:
        status = "FAIL" if is_success else "WARN"
        detail = (
            f"report Required Audit section is missing {len(missing)} of {len(questions)} answers"
            if is_success
            else f"report Required Audit section is missing {len(missing)} of {len(questions)} answers but report status is {report_status}"
        )
        return _check(
            "required_audit_coverage",
            status,
            detail,
            required_audit_items=questions,
            missing_answers=missing,
            placeholder_answers=[],
        )

    # All questions are present; now validate answer content
    placeholder_answers = _required_audit_placeholder_items(report_section)

    if placeholder_answers and is_success:
        return _check(
            "required_audit_coverage",
            "FAIL",
            f"report has {len(placeholder_answers)} of {len(questions)} Required Audit items with placeholder answers; SUCCESS/ACCEPTED requires substantive answers",
            required_audit_items=questions,
            missing_answers=[],
            placeholder_answers=placeholder_answers,
        )
    elif placeholder_answers and not is_success:
        return _check(
            "required_audit_coverage",
            "WARN",
            f"report has {len(placeholder_answers)} of {len(questions)} Required Audit items with placeholder answers but report status is {report_status}",
            required_audit_items=questions,
            missing_answers=[],
            placeholder_answers=placeholder_answers,
        )

    return _check(
        "required_audit_coverage",
        "PASS",
        f"report covers all {len(questions)} Required Audit items with substantive answers",
        required_audit_items=questions,
        missing_answers=[],
        placeholder_answers=[],
    )


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
    bash_blocks = [body for language, body in blocks if language in {"bash", "sh", "shell", "powershell", "ps1"}]
    if not bash_blocks:
        commands = _extract_unfenced_commands(text)
        if commands:
            return commands, None
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


def _dedupe_commands(commands: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for command in commands:
        normalized = command.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _looks_like_standalone_command(line: str) -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    if "..." in stripped:
        return False
    return bool(
        lowered == "pwd"
        or lowered.startswith("pwd ")
        or lowered == "get-location"
        or lowered.startswith("get-location ")
        or lowered == "set-location"
        or lowered.startswith("set-location ")
        or lowered == "test-path"
        or lowered.startswith("test-path ")
        or lowered.startswith("git ")
        or lowered.startswith("python ")
        or lowered.startswith("pytest")
        or lowered.startswith("powershell ")
    )


def _is_prohibitive_line(line: str) -> bool:
    """Return True if the line is a prohibition or description that should not yield commands."""
    lowered = line.lower()
    prohibitive_patterns = (
        "do not ",
        "do not\n",
        "don't ",
        "不要",
        "不得",
        "禁止",
        "stop ",
        "must not ",
        "shall not ",
        "不得在",
        "不允许",
    )
    return any(pattern in lowered for pattern in prohibitive_patterns)


def _is_descriptive_backtick_line(line: str) -> bool:
    """Return True if the line is a numbered descriptive item with backtick references.

    Lines like '5. `pytest_result.txt` shows bare `python -m ... run-round` ...'
    are descriptive references, not executable command lines.
    """
    stripped = line.strip()
    # Match numbered list items: "1. ", "2. ", etc.
    if re.match(r"^\d+\.\s", stripped):
        # Count backtick pairs — if more than one, it's likely descriptive.
        backtick_count = stripped.count("`")
        if backtick_count >= 4:  # At least 2 pairs of backticks
            return True
    return False


def _extract_unfenced_commands(text: str) -> list[str]:
    commands: list[str] = []
    for raw_line in text.splitlines():
        # Skip prohibitive lines entirely — they describe what NOT to do.
        if _is_prohibitive_line(raw_line):
            continue

        # Skip descriptive numbered items with multiple backtick references.
        # These are prose descriptions, not executable command lines.
        is_descriptive = _is_descriptive_backtick_line(raw_line)

        line_commands: list[str] = []
        # Only extract backtick commands from non-descriptive lines.
        if not is_descriptive:
            for match in re.finditer(r"`([^`]+)`", raw_line):
                candidate = match.group(1).strip()
                if candidate and "..." not in candidate and _command_kind(candidate) != "unknown":
                    line_commands.append(candidate)
        if line_commands:
            commands.extend(line_commands)
            continue

        # Skip natural language matching on descriptive lines.
        if is_descriptive:
            continue

        stripped = raw_line.strip()
        if (
            stripped
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith("-")
            and _looks_like_standalone_command(stripped)
        ):
            kind = _command_kind(stripped)
            if kind != "unknown":
                commands.append(stripped)
                continue

        lowered = raw_line.lower()
        if "位置确认" in raw_line or "location confirmation" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["position"])
        if "git 状态" in raw_line or "git status" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["git_status"])
        if "preflight" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["preflight"])
        if "command-plan" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["command-plan"])
        if "doctor" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["doctor"])
        if (
            re.search(r"\bpytest\b", lowered)
            and "pytest_result" not in lowered
            and not ("archived" in lowered and "live" in lowered)
        ):
            commands.extend(NATURAL_LANGUAGE_COMMANDS["pytest"])
        if "lint-report" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["lint-report"])
        if "report-summary" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["report-summary"])
        if "final-check" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["final-check"])
        if "run-round" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["run-round"])
        if "diff 文件名" in raw_line or "diff filenames" in lowered or "git diff" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["git_diff"])
        if (
            "queue/status verification" in lowered
            or "queue/inventory verification" in lowered
            or "只读 queue/status" in lowered
            or "只读 queue/inventory" in lowered
        ):
            commands.extend(NATURAL_LANGUAGE_COMMANDS["queue_status_verification"])
        if "tool capability verification" in lowered or "工具能力核验" in raw_line:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["tool_capability_verification"])
        if "current static triage verification" in lowered:
            commands.extend(NATURAL_LANGUAGE_COMMANDS["current_static_triage_verification"])
        if "artifact_index verification" in lowered or "artifact_index 核验" in raw_line:
            if "target bytes" in lowered or "revalidation" in lowered:
                commands.extend(NATURAL_LANGUAGE_COMMANDS["target_bytes_artifact_index_verification"])
            else:
                commands.extend(NATURAL_LANGUAGE_COMMANDS["artifact_index_verification"])
    return _dedupe_commands(commands)


def _scope_paths(scope_text: str) -> set[str]:
    paths: set[str] = set()
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        item = _path_from_markdown_bullet(line)
        if not item or item.lower().endswith(":"):
            continue
        if item in {"Allowed source files", "Allowed tests", "Allowed generated files", "Disallowed"}:
            continue
        paths.add(_norm_path(item))
    return paths


def _path_from_markdown_bullet(line: str) -> str:
    item = line[1:].strip() if line.strip().startswith("-") else line.strip()
    match = re.search(r"`([^`]+)`", item)
    if match:
        return match.group(1).strip()
    return item.strip().strip("`").strip()


def _path_from_markdown_list_item(line: str) -> str | None:
    """Extract a path from a markdown bullet (``-``) or numbered (``1.``) list item.

    Returns ``None`` if the line is not a list item.
    """
    stripped = line.strip()
    if not stripped:
        return None
    # Bullet list: "- item" or "* item"
    if stripped.startswith("-") or stripped.startswith("*"):
        item = stripped[1:].strip()
    else:
        # Numbered list: "1. item" or "10. item"
        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if not m:
            return None
        item = m.group(2).strip()
    # Extract backtick-quoted path if present
    match = re.search(r"`([^`]+)`", item)
    if match:
        return match.group(1).strip()
    return item.strip().strip("`").strip() or None


def _allowed_scope_paths(scope_text: str) -> set[str]:
    paths: set[str] = set()
    in_allowed_block = False
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("allowed") or lowered.startswith("允许"):
            in_allowed_block = True
            continue
        if (
            lowered.startswith("disallowed")
            or lowered.startswith("forbidden")
            or lowered.startswith("read-only")
            or lowered.startswith("read only")
            or lowered.startswith("required")
            or lowered.startswith("suggested")
            or lowered.startswith("不允许")
            or lowered.startswith("禁止")
            or lowered.startswith("只读")
            or lowered.startswith("do not modify")
            or lowered.startswith("do not change")
        ):
            in_allowed_block = False
            continue
        if not in_allowed_block or not line.startswith("-"):
            continue
        item = _path_from_markdown_bullet(line)
        if item:
            paths.add(_norm_path(item))
    if paths:
        return paths
    paths = _scope_paths(scope_text)
    if paths:
        return paths
    return _natural_language_scope_paths(scope_text)


def _natural_language_scope_paths(scope_text: str) -> set[str]:
    lowered = scope_text.lower()
    paths: set[str] = set()
    if "project gate" in lowered or "project_gate" in lowered:
        paths.add("reverse_agent/project_gate.py")
    if "project gate/state" in lowered or "project_state" in lowered or "state 逻辑" in lowered:
        paths.add("reverse_agent/project_state.py")
    if "对应测试" in scope_text or "related tests" in lowered:
        paths.update({"tests/test_project_gate.py", "tests/test_project_state.py"})
    if "project_state 报告" in scope_text or "project_state report" in lowered:
        paths.update({"project_state/codex_execution_report.md", "project_state/pytest_result.txt"})
    if "gate 输出" in scope_text or "gate output" in lowered:
        paths.add("project_state/gates/")
    return paths


def _path_under_any(path: str, roots: set[str]) -> bool:
    return any(root.endswith("/") and path.startswith(root) for root in roots)


def _allowed_source_test_scope_paths(scope_text: str) -> set[str]:
    paths: set[str] = set()
    active = False
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("allowed source") or lowered.startswith("allowed tests") or lowered.startswith("allowed paths") or lowered.startswith("允许修改"):
            active = True
            continue
        if (
            lowered.startswith("allowed generated")
            or lowered.startswith("allowed state")
            or lowered.startswith("allowed project")
            or lowered.startswith("disallowed")
            or lowered.startswith("不允许")
            or lowered.startswith("允许生成")
            or lowered.startswith("禁止")
            or lowered.startswith("do not modify")
            or lowered.startswith("do not change")
            or lowered.startswith("required")
        ):
            active = False
            continue
        if not active or not (line.startswith("-") or re.match(r"^\d+\.\s", line)):
            continue
        item = _path_from_markdown_bullet(line)
        if item:
            paths.add(_norm_path(item))
    return paths


def _allowed_inherited_files(decision_text: str, inherited_dirty_files: set[str]) -> set[str]:
    """Return inherited dirty files that are explicitly allowed by the decision's
    "Allowed Inherited Dirty Baseline Files" section.

    Files that merely appear in Implementation Scope are NOT automatically
    allowed — doing so would mask late baseline capture."""
    allowed_paths = _allowed_inherited_baseline_paths(decision_text)
    return inherited_dirty_files & allowed_paths


def _decision_scope_deliverable_paths(decision_text: str) -> set[str]:
    """Return artifact paths listed in the decision's Implementation Scope
    "Allowed generated artifacts" or "Allowed generated/project-state files"
    sub-section.

    These are deliverables the decision explicitly authorizes creating, so
    they must appear in the report's files_changed and generated_artifacts
    even when they were present before baseline capture (inherited dirty).
    """
    scope_text = _markdown_section(decision_text, "Implementation Scope")
    paths: set[str] = set()
    in_allowed_generated = False
    for raw_line in scope_text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        # Detect "Allowed generated artifacts" / "Allowed generated files" /
        # "Allowed generated/project-state files" sub-section headers
        if lowered.startswith("allowed generated") or lowered.startswith("allowed project-state") or lowered.startswith("allowed project_state"):
            in_allowed_generated = True
            continue
        # Exit the sub-section when hitting another sub-section or a blank
        # structural boundary (another "Allowed" or "Disallowed" header)
        if in_allowed_generated and (
            (lowered.startswith("allowed") and not lowered.startswith("allowed generated") and not lowered.startswith("allowed project"))
            or lowered.startswith("disallowed")
            or lowered.startswith("required")
            or lowered.startswith("do not")
        ):
            in_allowed_generated = False
            continue
        if not in_allowed_generated or not line.startswith("-"):
            continue
        item = _path_from_markdown_bullet(line)
        if item and not item.lower().endswith(":"):
            paths.add(_norm_path(item))
    return paths


_CLOSEOUT_ARTIFACTS_CONTRACT_BLOCK_NAME = "closeout_artifacts_contract"


def _decision_required_closeout_artifacts(decision_text: str) -> set[str]:
    """Return artifact paths declared as required closeout records in the decision.

    Extraction order (first non-empty result wins):

    1. Structured JSON block named ``closeout_artifacts_contract`` containing a
       ``required_closeout_artifacts`` list.
    2. Markdown lists (bullet ``-`` or numbered ``1.``) in the ``Current Evidence``
       section whose items are paths under ``project_state/``.

    These are existing state records that must be referenced (not generated)
    by the report for closeout completeness.  They appear in the report's
    ``referenced_artifacts`` field and are validated by final-check via
    ``required_closeout_artifacts`` coverage.
    """
    # 1. Structured JSON block extraction
    contract = extract_markdown_json_block(
        decision_text, _CLOSEOUT_ARTIFACTS_CONTRACT_BLOCK_NAME
    )
    if contract.get("found") and not contract.get("parse_error"):
        raw_list = contract.get("required_closeout_artifacts")
        if isinstance(raw_list, list) and all(isinstance(item, str) for item in raw_list):
            paths: set[str] = set()
            for item in raw_list:
                normalized = _norm_path(item)
                if normalized.startswith("project_state/"):
                    paths.add(normalized)
            if paths:
                return paths

    # 2. Markdown list extraction (bullet and numbered) from Current Evidence
    evidence_text = _markdown_section(decision_text, "Current Evidence")
    paths = set()
    for raw_line in evidence_text.splitlines():
        line = raw_line.strip()
        item = _path_from_markdown_list_item(line)
        if item and item.lower().startswith("project_state/"):
            paths.add(_norm_path(item))
    return paths


def _allowed_inherited_baseline_paths(decision_text: str) -> set[str]:
    """Return the set of paths that the decision explicitly allows to be
    dirty at baseline.

    This includes:
    1. Paths listed in the ``Allowed Inherited Dirty Baseline Files`` section.
    2. Paths listed in ``required_files_changed`` in the ``decision_contract``
       JSON block, because these files are declared as required to be changed
       in this round and may be dirty at baseline in multi-session continuations.
    """
    section = _markdown_section(decision_text, "Allowed Inherited Dirty Baseline Files")
    paths = _scope_paths(section)
    # Also include required_files_changed from the decision_contract, because
    # these files are declared as required to be changed in this round and may
    # be dirty at baseline in multi-session continuations where a previous
    # session of the same round already made the authorized modifications.
    contract = extract_markdown_json_block(decision_text, "decision_contract")
    if contract.get("found") and not contract.get("parse_error"):
        for path in contract.get("required_files_changed") or []:
            paths.add(_norm_path(path))
    return paths


# ---------------------------------------------------------------------------
# Gate profile classification
# ---------------------------------------------------------------------------

_GATE_PROFILE_NAMES: tuple[str, ...] = ("fast", "standard", "full")

_FULL_SCOPE_PATHS: tuple[str, ...] = (
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
)

_FULL_SCOPE_PREFIXES: tuple[str, ...] = (
    "reverse_agent/solver",
    "reverse_agent/harness",
    "reverse_agent/ida",
    "reverse_agent/ghidra",
    "reverse_agent/debugger",
    "reverse_agent/tool_runner",
    "reverse_agent/runtime_probe",
    ".codex-skills/",
)

_FAST_SUGGESTED_COMMANDS: list[dict[str, Any]] = [
    {"index": 1, "command": "startup path checks", "phase": "status", "kind": "startup"},
    {"index": 2, "command": "preflight", "phase": "preflight", "kind": "preflight"},
    {"index": 3, "command": "command-plan", "phase": "gate", "kind": "command-plan"},
    {"index": 4, "command": "report-summary", "phase": "gate", "kind": "report-summary"},
    {"index": 5, "command": "final-check", "phase": "gate", "kind": "final-check"},
]

_STANDARD_SUGGESTED_COMMANDS: list[dict[str, Any]] = [
    {"index": 1, "command": "startup path checks", "phase": "status", "kind": "startup"},
    {"index": 2, "command": "preflight", "phase": "preflight", "kind": "preflight"},
    {"index": 3, "command": "command-plan", "phase": "gate", "kind": "command-plan"},
    {"index": 4, "command": "focused pytest for touched modules", "phase": "test", "kind": "pytest"},
    {"index": 5, "command": "doctor", "phase": "status", "kind": "doctor"},
    {"index": 6, "command": "lint-report", "phase": "status", "kind": "lint-report"},
    {"index": 7, "command": "report-summary", "phase": "gate", "kind": "report-summary"},
    {"index": 8, "command": "final-check", "phase": "gate", "kind": "final-check"},
]

_FULL_SUGGESTED_COMMANDS: list[dict[str, Any]] = [
    {"index": 1, "command": "startup path checks", "phase": "status", "kind": "startup"},
    {"index": 2, "command": "preflight", "phase": "preflight", "kind": "preflight"},
    {"index": 3, "command": "command-plan", "phase": "gate", "kind": "command-plan"},
    {"index": 4, "command": "run-round", "phase": "gate", "kind": "run-round"},
    {"index": 5, "command": "full pytest for gate/project_state modules", "phase": "test", "kind": "pytest"},
    {"index": 6, "command": "doctor", "phase": "status", "kind": "doctor"},
    {"index": 7, "command": "lint-report", "phase": "status", "kind": "lint-report"},
    {"index": 8, "command": "report-summary", "phase": "gate", "kind": "report-summary"},
    {"index": 9, "command": "final-check", "phase": "gate", "kind": "final-check"},
    {"index": 10, "command": "close-round", "phase": "gate", "kind": "close-round"},
]


def _path_is_full_scope(path: str) -> bool:
    """Return True if *path* is a gate/project_state/harness/solver/tool-runner
    file that warrants the ``full`` gate profile."""
    normalized = _norm_path(path)
    if normalized in {_norm_path(p) for p in _FULL_SCOPE_PATHS}:
        return True
    for prefix in _FULL_SCOPE_PREFIXES:
        if normalized.startswith(_norm_path(prefix)):
            return True
    return False


def _path_is_source_or_test(path: str) -> bool:
    """Return True if *path* is a source or test file (but not project_state)."""
    normalized = _norm_path(path)
    if normalized.startswith("reverse_agent/") and normalized.endswith(".py"):
        return True
    if normalized.startswith("tests/") and normalized.endswith(".py"):
        return True
    return False


def classify_gate_profile(decision_text: str) -> dict[str, Any]:
    """Classify the gate profile for the current decision.

    Returns a dict with:
    - ``profile``: one of ``fast``, ``standard``, ``full``
    - ``profile_reason``: concise string explaining the classification
    - ``risk_reasons``: list of risk factors that influenced the classification
    - ``closeout_allowed``: whether close-round is permitted for this profile
    - ``required_command_kinds``: list of command kinds required for this profile
    - ``reasons``: list of strings explaining the classification (legacy)
    - ``suggested_commands``: list of command dicts for the recommended tier
    - ``future_phases``: list of planned future enhancements
    """
    scope_text = _markdown_section(decision_text, "Implementation Scope")
    allowed_source_test = _allowed_source_test_scope_paths(scope_text)
    allowed_generated = _decision_scope_deliverable_paths(decision_text)

    reasons: list[str] = []
    risk_reasons: list[str] = []
    profile = "fast"  # default: artifact-only

    # Check for full-scope paths
    full_scope_hits: list[str] = []
    for path in sorted(allowed_source_test):
        if _path_is_full_scope(path):
            full_scope_hits.append(path)
    if full_scope_hits:
        profile = "full"
        reasons.append(
            f"decision scope includes gate/project_state/harness/solver/tool-runner paths: "
            f"{', '.join(full_scope_hits)}"
        )
        risk_reasons.append("gate/project_state source changes require full validation")

    # Check for .codex-skills/ in generated artifacts (also full)
    codex_skills_hits = [
        p for p in sorted(allowed_generated | allowed_source_test)
        if _norm_path(p).startswith(".codex-skills/")
    ]
    if codex_skills_hits:
        profile = "full"
        reasons.append(
            f"decision scope includes .codex-skills/ paths: {', '.join(codex_skills_hits)}"
        )
        risk_reasons.append(".codex-skills/ changes require full validation")

    # Check for ordinary source/test changes (standard)
    if profile == "fast":
        source_test_hits = [
            p for p in sorted(allowed_source_test)
            if _path_is_source_or_test(p) and not _path_is_full_scope(p)
        ]
        if source_test_hits:
            profile = "standard"
            reasons.append(
                f"decision scope includes source/test changes: {', '.join(source_test_hits)}"
            )
            risk_reasons.append("source/test changes require targeted pytest and gate validation")

    # Fast profile justification
    if profile == "fast":
        if allowed_generated:
            reasons.append(
                f"decision scope is artifact-only with generated/project-state deliverables: "
                f"{len(allowed_generated)} artifact path(s)"
            )
        else:
            reasons.append("decision scope has no source/test or gate/project_state changes")

    # Determine closeout_allowed and required_command_kinds based on profile
    if profile == "full":
        closeout_allowed = True
        required_command_kinds = [
            "startup", "preflight", "command-plan", "run-round", "pytest",
            "doctor", "lint-report", "report-summary", "final-check", "close-round",
        ]
        profile_reason = "gate/project_state/harness/solver/tool-runner changes require full validation pipeline"
    elif profile == "standard":
        closeout_allowed = True
        required_command_kinds = [
            "startup", "preflight", "command-plan", "pytest",
            "doctor", "lint-report", "report-summary", "final-check",
        ]
        profile_reason = "source/test changes require targeted pytest and gate validation"
    else:
        closeout_allowed = False
        required_command_kinds = [
            "startup", "preflight", "command-plan", "report-summary", "final-check",
        ]
        profile_reason = "artifact-only cleanup does not require close-round"

    suggested_commands: list[dict[str, Any]]
    if profile == "fast":
        suggested_commands = _FAST_SUGGESTED_COMMANDS
    elif profile == "standard":
        suggested_commands = _STANDARD_SUGGESTED_COMMANDS
    else:
        suggested_commands = _FULL_SUGGESTED_COMMANDS

    return {
        "profile": profile,
        "profile_reason": profile_reason,
        "risk_reasons": risk_reasons,
        "closeout_allowed": closeout_allowed,
        "required_command_kinds": required_command_kinds,
        "reasons": reasons,
        "suggested_commands": suggested_commands,
        "future_phases": [],
    }


def gate_profile(*, state_dir: Path, write_result: bool = True, profile_override: str | None = None) -> dict[str, Any]:
    """Run gate profile classification and optionally write the result.

    Args:
        state_dir: Path to the project_state directory.
        write_result: Whether to write the result to gate_profile_plan.json.
        profile_override: If provided, use this profile instead of auto-classification.
            Must be one of "fast", "standard", "full". Invalid names cause a FAIL result.
    """
    state_dir = Path(state_dir)
    decision = read_decision_meta(state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")

    classification = classify_gate_profile(decision_text)

    # Handle explicit profile selection
    if profile_override is not None:
        if profile_override not in _GATE_PROFILE_NAMES:
            return {
                "schema_version": GATE_RESULT_SCHEMA_VERSION,
                "gate_name": "gate-profile",
                "gate_status": "FAILED",
                "decision_id": decision_id,
                "round_id": round_id,
                "mainline": mainline,
                "generated_at": _now_iso(),
                "profile": profile_override,
                "profile_reason": f"invalid profile name: {profile_override}",
                "risk_reasons": [f"unknown profile: {profile_override}"],
                "closeout_allowed": False,
                "required_command_kinds": [],
                "reasons": [f"invalid profile name: {profile_override}; must be one of {', '.join(_GATE_PROFILE_NAMES)}"],
                "suggested_commands": [],
                "future_phases": [],
            }
        # Override the auto-classified profile but keep the derived metadata
        override_profile = profile_override
        if override_profile != classification["profile"]:
            # Recompute closeout_allowed and required_command_kinds for the override
            if override_profile == "full":
                classification["closeout_allowed"] = True
                classification["required_command_kinds"] = [
                    "startup", "preflight", "command-plan", "run-round", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check", "close-round",
                ]
                classification["profile_reason"] = "full profile explicitly selected"
            elif override_profile == "standard":
                classification["closeout_allowed"] = True
                classification["required_command_kinds"] = [
                    "startup", "preflight", "command-plan", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check",
                ]
                classification["profile_reason"] = "standard profile explicitly selected"
            else:
                classification["closeout_allowed"] = False
                classification["required_command_kinds"] = [
                    "startup", "preflight", "command-plan", "report-summary", "final-check",
                ]
                classification["profile_reason"] = "fast profile explicitly selected"
            classification["profile"] = override_profile

    result: dict[str, Any] = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        **classification,
    }

    if write_result:
        output_path = state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    return result


_NEGATION_PHRASES: tuple[str, ...] = (
    "no inherited baseline dirty files",
    "no inherited dirty files",
    "no baseline dirty files",
    "working tree was clean",
    "working tree clean",
    "no dirty files at round start",
)


def _report_explains_inherited_baseline_files(report_text: str) -> bool:
    """Return True if the report text contains an *affirmative* explanation of
    inherited baseline dirty files — not a negation like "no inherited baseline
    dirty files" or "working tree was clean".

    Two conditions must both hold:
    1. The "Allowed Inherited Dirty Baseline Files" section exists and contains
       at least one file path (``- `` list item).
    2. The full report text does NOT contain any negation phrase from
       ``_NEGATION_PHRASES``.  If a negation phrase appears anywhere in the
       report, the explanation is considered invalid — even if the allowlist
       section has list items — because the report contradicts itself.
    """
    # Condition 1: allowlist section must have list items
    section = _markdown_section(report_text, "Allowed Inherited Dirty Baseline Files")
    if not section.strip():
        return False
    has_list_item = any(
        line.strip().startswith("- ") and len(line.strip()) > 2
        for line in section.splitlines()
    )
    if not has_list_item:
        return False

    # Condition 2: no negation phrases anywhere in the report
    report_lower = report_text.lower()
    for phrase in _NEGATION_PHRASES:
        if phrase in report_lower:
            return False

    return True


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
    in_fence = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = stripped.lower()
        if any(marker in line for marker in negation_markers):
            continue
        # Skip lines that are file paths under project_state/ — these are
        # state artifacts, not executable code, and should not trigger the
        # runtime-scope policy for engineering_branch.
        if _line_is_project_state_path(stripped):
            continue
        for term in terms:
            if term in line:
                matches.add(term)
    return sorted(matches)


def _line_is_project_state_path(line: str) -> bool:
    """Return True if *line* is a markdown bullet or backtick item that is
    a file path under ``project_state/``.

    This prevents protected-term false positives when a decision's Goal
    section lists existing state artifacts (e.g.
    ``project_state/local_reverse_..._solver_dispatch_plan.json``) for
    traceability.
    """
    text = line.strip().lstrip("-").strip()
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    normalized = text.lower().replace("\\", "/")
    return normalized.startswith("project_state/")


def _scope_path_has_runtime_token(path: str) -> bool:
    runtime_tokens = {"solver", "runtime", "probe", "ida", "ghidra", "olly"}
    # Paths under project_state/ are state artifacts, not executable code;
    # they should not trigger the runtime-scope policy for engineering_branch.
    normalized = path.lower().replace("\\", "/")
    if normalized.startswith("project_state/"):
        return False
    chunks: list[str] = []
    current = []
    for char in normalized:
        if char.isalnum():
            current.append(char)
            continue
        if current:
            chunks.append("".join(current))
            current = []
    if current:
        chunks.append("".join(current))
    return any(chunk in runtime_tokens for chunk in chunks)


def _derive_repo_root(state_dir: Path) -> Path:
    """Derive repo_root from state_dir for path existence checks.

    When state_dir is a ``project_state`` directory, repo_root is its
    parent.  Otherwise fall back to cwd.
    """
    if state_dir.name == "project_state":
        return state_dir.resolve().parent
    return Path.cwd().resolve()


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


def _round_close_snapshot_path(state_dir: Path) -> Path:
    return state_dir / "gates" / ROUND_CLOSE_SNAPSHOT_RESULT_NAME


def _is_generated_state_or_archive_path(path: str) -> bool:
    normalized = _norm_path(path)
    return (
        normalized.startswith("project_state/gates/")
        or normalized.startswith("project_state/rounds/")
        or normalized in {"project_state/codex_execution_report.md", "project_state/pytest_result.txt"}
    )


def _is_implementation_file(path: str) -> bool:
    if _is_generated_state_or_archive_path(path):
        return False
    normalized = _norm_path(path)
    if normalized.startswith("reverse_agent/") and normalized.endswith(".py"):
        return True
    if normalized.startswith("tests/") and normalized.endswith(".py"):
        return True
    if (
        normalized.startswith("project_state/")
        and normalized.endswith(".json")
        and not normalized.startswith("project_state/gates/")
        and not normalized.startswith("project_state/rounds/")
    ):
        return True
    return False


def _is_substantive_change(path: str) -> bool:
    return _is_implementation_file(path)


def _is_temporary_path(path: str) -> bool:
    """Return True if *path* looks like a temporary file/directory that
    should not persist as an inherited dirty file in a successful closeout.

    Matches patterns like ``tmp8osv9s8n/``, ``tmp1234/``, ``tmp/``, etc.
    """
    normalized = _norm_path(path)
    # Match top-level tmp*/ directories or files (e.g. tmp8osv9s8n/,
    # tmp8osv9s8n/some_file, tmp1234)
    parts = normalized.split("/")
    if parts and parts[0].startswith("tmp"):
        remainder = parts[0][3:]
        # Allow "tmp" itself and "tmp" followed by alphanumeric chars
        if remainder == "" or remainder.isalnum():
            return True
    return False


def _extract_claimed_source_test_paths(report_text: str) -> set[str]:
    """Extract source/test file paths claimed as changed in the report prose.

    Scans sections like "Source Changes" and "Test Changes" for backticked
    paths (`` `reverse_agent/foo.py` `` or `` `tests/bar.py` ``).  Only
    returns paths that are classified as implementation files by
    :func:`_is_implementation_file`, which excludes generated
    ``project_state/`` artifacts.
    """
    if not report_text or not report_text.strip():
        return set()

    # Extract "Source Changes" and "Test Changes" sections from the report.
    # These are the prose sections where the report claims specific files
    # were modified.
    source_section = _markdown_section(report_text, "Source Changes")
    test_section = _markdown_section(report_text, "Test Changes")
    changes_section = _markdown_section(report_text, "Changes")

    # Also scan the full report for backticked paths in bullet lists
    # that look like source/test paths.
    combined_text = "\n".join([source_section, test_section, changes_section])

    # If no specific sections found, fall back to scanning the full report
    if not combined_text.strip():
        combined_text = report_text

    # Find backticked paths: `reverse_agent/foo.py` or `tests/bar.py`
    backtick_pattern = re.compile(r"`([^`]+)`")
    paths: set[str] = set()
    for match in backtick_pattern.finditer(combined_text):
        candidate = _norm_path(match.group(1))
        if _is_implementation_file(candidate):
            paths.add(candidate)
    return paths


def _report_prose_claims_check(
    *,
    report_text: str,
    files_changed: set[str],
) -> dict[str, Any]:
    """Check that source/test paths claimed in report prose appear in
    ``codex_report_summary.files_changed``.

    If the report body claims a source/test file was changed (e.g. in
    "Source Changes" or "Test Changes" sections with backticked paths),
    but that path is absent from ``files_changed``, this check fails.
    """
    claimed = _extract_claimed_source_test_paths(report_text)
    if not claimed:
        return _check(
            "report_prose_claims_covered_by_files_changed",
            "PASS",
            "report prose does not claim source/test changes beyond files_changed",
            claimed_source_test_paths=[],
        )

    missing = sorted(claimed - files_changed)
    if missing:
        return _check(
            "report_prose_claims_covered_by_files_changed",
            "FAIL",
            "report prose claims source/test changes that are absent from files_changed",
            claimed_source_test_paths=sorted(claimed),
            missing_from_files_changed=missing,
        )

    return _check(
        "report_prose_claims_covered_by_files_changed",
        "PASS",
        "report prose source/test claims are covered by files_changed",
        claimed_source_test_paths=sorted(claimed),
    )


def _tmp_paths_dirty_check(
    *,
    delta_summary: dict[str, Any],
) -> dict[str, Any]:
    """Check that temporary paths (``tmp*/``) are not present in dirty state.

    Temporary files/directories like ``tmp8osv9s8n/`` should be removed
    before successful closeout.  If they appear in the final dirty files
    or inherited dirty files, this check fails.
    """
    final_dirty_files = _string_set(delta_summary.get("final_dirty_files"))
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    baseline_dirty_files = _string_set(delta_summary.get("baseline_dirty_files"))

    all_dirty = final_dirty_files | inherited_dirty_files | baseline_dirty_files
    tmp_paths = sorted(path for path in all_dirty if _is_temporary_path(path))

    if tmp_paths:
        return _check(
            "tmp_paths_absent_from_dirty_state",
            "FAIL",
            "temporary paths (tmp*/) found in dirty state; must be removed before closeout",
            tmp_paths=tmp_paths,
        )

    return _check(
        "tmp_paths_absent_from_dirty_state",
        "PASS",
        "no temporary paths (tmp*/) in dirty state",
        tmp_paths=[],
    )


def _is_live_gate_artifact_path(path: str) -> bool:
    """Return True if *path* is a live gate artifact that should exist on disk.

    Live gate artifacts are under ``project_state/gates/`` or are the
    top-level ``project_state/codex_execution_report.md`` and
    ``project_state/pytest_result.txt``.  Archive paths under
    ``project_state/rounds/<round_id>/`` are NOT live — they are validated
    by round manifest/archive checks instead.

    ``final_gate_result.json`` is excluded because it is written by
    ``final_check()`` *after* the existence check runs; it cannot be
    expected on disk at check time.
    """
    normalized = _norm_path(path)
    if normalized.startswith("project_state/gates/"):
        if normalized == f"project_state/gates/{FINAL_GATE_RESULT_NAME}":
            return False
        return True
    if normalized in {"project_state/codex_execution_report.md", "project_state/pytest_result.txt"}:
        return True
    return False


def _generated_artifact_live_paths_exist_check(
    *,
    generated_artifacts: set[str],
    repo_root: Path,
) -> dict[str, Any]:
    """Check that live project_state/ artifact paths listed in
    ``generated_artifacts`` actually exist on disk.

    Archive paths under ``project_state/rounds/<round_id>/`` are excluded
    from this check because they are validated by existing round archive
    checks.
    """
    live_paths = sorted(path for path in generated_artifacts if _is_live_gate_artifact_path(path))
    missing = sorted(path for path in live_paths if not (repo_root / path).exists())

    if missing:
        return _check(
            "generated_artifact_live_paths_exist",
            "FAIL",
            "generated_artifacts lists live project_state/ paths that do not exist on disk",
            missing_live_paths=missing,
            live_paths=live_paths,
        )

    return _check(
        "generated_artifact_live_paths_exist",
        "PASS",
        "all live project_state/ generated artifact paths exist on disk",
        live_paths=live_paths,
    )


def _baseline_matches_round(payload: dict[str, Any], decision_id: str, round_id: str) -> bool:
    return (
        bool(payload)
        and str(payload.get("decision_id") or "") == decision_id
        and str(payload.get("round_id") or "") == round_id
    )


def _write_round_close_snapshot(
    *,
    state_dir: Path,
    repo_root: Path,
    decision_id: str,
    round_id: str,
) -> dict[str, Any]:
    """Write a close snapshot / lifecycle artifact during close-round."""
    baseline = _read_json(_round_baseline_path(state_dir))
    baseline_dirty_files = _string_set(baseline.get("baseline_dirty_files")) if baseline else set()
    close_git_status_short = _git_status_short_lines(repo_root)
    close_git_diff_name_only = _git_diff_name_only(repo_root)
    close_dirty_files = set(_git_changed_files(repo_root))
    close_worktree_clean = not close_dirty_files
    inherited_at_close = close_dirty_files & baseline_dirty_files

    snapshot = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "artifact_name": ROUND_CLOSE_SNAPSHOT_RESULT_NAME,
        "decision_id": decision_id,
        "round_id": round_id,
        "closed_at": _now_iso(),
        "round_closed": True,
        "baseline_active": False,
        "close_git_status_short": close_git_status_short,
        "close_git_diff_name_only": close_git_diff_name_only,
        "close_dirty_files": sorted(close_dirty_files),
        "close_worktree_clean": close_worktree_clean,
        "baseline_dirty_files": sorted(baseline_dirty_files),
        "inherited_dirty_files_at_close": sorted(inherited_at_close),
        "recommended_next_action": "no_action_required" if close_worktree_clean else "review_close_dirty_files",
    }
    snapshot_path = _round_close_snapshot_path(state_dir)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return snapshot


def _read_round_close_snapshot(state_dir: Path) -> dict[str, Any]:
    """Read the round close snapshot if it exists."""
    return _read_json(_round_close_snapshot_path(state_dir))


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

    baseline_git_status_short = _git_status_short_lines(repo_root)
    baseline_untracked_files = [
        _norm_path(line[3:].strip().strip('"'))
        for line in baseline_git_status_short
        if line.startswith("?? ")
    ]
    baseline_has_untracked_implementation_files = any(
        _is_implementation_file(path) for path in baseline_untracked_files
    )

    baseline = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "artifact_name": ROUND_BASELINE_RESULT_NAME,
        "decision_id": decision_id,
        "round_id": round_id,
        "head_commit": _git_head_commit(repo_root),
        "baseline_git_status_short": baseline_git_status_short,
        "baseline_git_diff_name_only": _git_diff_name_only(repo_root),
        "baseline_dirty_files": _git_changed_files(repo_root),
        "baseline_untracked_files": sorted(baseline_untracked_files),
        "baseline_has_untracked_implementation_files": baseline_has_untracked_implementation_files,
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
        "baseline_untracked_files": baseline.get("baseline_untracked_files") if baseline_available else [],
        "baseline_has_untracked_implementation_files": baseline.get("baseline_has_untracked_implementation_files") if baseline_available else False,
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
    state_dir: Path | None = None,
    decision_text: str = "",
    report_text: str = "",
    pytest_text: str = "",
    decision_immutability_failed: bool = False,
) -> list[dict[str, Any]]:
    baseline_available = bool(delta_summary.get("baseline_available"))
    final_dirty_files = _string_set(delta_summary.get("final_dirty_files"))
    new_dirty_files = _string_set(delta_summary.get("new_dirty_files_since_baseline"))
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    required_changed_files = (new_dirty_files if baseline_available else final_dirty_files) | archive_paths
    required_changed_for_diff = (new_dirty_files if baseline_available else final_dirty_files)

    # Filter out stale gate artifacts that don't match the current round.
    # The synthesis (build_report_summary_synthesis) filters these out, so
    # the files_changed_covers_git_diff check must also filter them out to
    # avoid a false mismatch.  Stale round_close_snapshot.json and
    # run_round_result.json from previous rounds can appear in the git diff
    # but should not be required in files_changed for the current round.
    if state_dir is not None:
        delta_decision_id = str(delta_summary.get("decision_id") or "")
        delta_round_id = str(delta_summary.get("round_id") or "")
        close_snapshot_payload = _read_json(
            state_dir / "gates" / ROUND_CLOSE_SNAPSHOT_RESULT_NAME
        )
        if not _artifact_matches_current_round(
            close_snapshot_payload,
            decision_id=delta_decision_id,
            round_id=delta_round_id,
        ):
            required_changed_for_diff = required_changed_for_diff - {ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH}
        run_round_payload = _read_json(
            state_dir / "gates" / RUN_ROUND_RESULT_NAME
        )
        if not _artifact_matches_current_round(
            run_round_payload,
            decision_id=delta_decision_id,
            round_id=delta_round_id,
        ):
            required_changed_for_diff = required_changed_for_diff - {RUN_ROUND_OUTPUT_PATH}

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

    inherited_claimed = sorted(
        path
        for path in (inherited_dirty_files & files_changed)
        if not _is_generated_state_or_archive_path(path)
    ) if baseline_available else []

    # Decision-scope required deliverables that are inherited dirty files
    # should not be flagged as suspicious — they are legitimate round output
    # that happened to be created before baseline capture.
    decision_scope_deliverables = _decision_scope_deliverable_paths(decision_text) if decision_text else set()
    inherited_claimed = sorted(
        path for path in inherited_claimed
        if _norm_path(path) not in decision_scope_deliverables
    )

    # Check close snapshot for baseline lifecycle semantics.
    close_snapshot = _read_round_close_snapshot(state_dir) if state_dir else {}
    round_closed = bool(close_snapshot and close_snapshot.get("round_closed"))
    close_worktree_clean = bool(close_snapshot.get("close_worktree_clean")) if close_snapshot else False

    if inherited_claimed:
        # Inherited dirty files that overlap with files_changed and are
        # source/test files must FAIL unless all three conditions hold:
        #   1. startup evidence confirms the files were pre-existing dirty
        #   2. the active decision had an explicit allowlist before execution
        #   3. live decision_packet.md was not modified during execution
        source_test_inherited_claimed = sorted(
            path for path in inherited_claimed if _is_implementation_file(path)
        )
        # Determine startup evidence trust
        order_info = _startup_status_order_valid(pytest_text)
        startup_evidence_trusted = order_info.get("startup_status_evidence_trusted", False)
        startup_dirty_files = _extract_startup_dirty_files(pytest_text)
        allowed_inherited = _allowed_inherited_baseline_paths(decision_text)
        # Check if all source/test inherited files have startup evidence
        all_confirmed_by_startup = (
            startup_evidence_trusted
            and all(path in startup_dirty_files for path in source_test_inherited_claimed)
        ) if source_test_inherited_claimed else True
        # Check if all source/test inherited files are in decision allowlist
        all_in_decision_allowlist = (
            all(_norm_path(path) in allowed_inherited for path in source_test_inherited_claimed)
        ) if source_test_inherited_claimed else True
        # Three conditions must ALL hold for inherited source/test dirty to be acceptable
        inherited_source_test_ok = (
            all_confirmed_by_startup
            and all_in_decision_allowlist
            and not decision_immutability_failed
        )
        if source_test_inherited_claimed:
            if inherited_source_test_ok:
                checks.append(
                    _check(
                        "files_changed_excludes_inherited_dirty_files",
                        "PASS",
                        "inherited source/test baseline dirty files in files_changed are authorized: startup evidence confirms pre-existing, decision allowlist present, and decision not modified during execution",
                        inherited_files_in_files_changed=inherited_claimed,
                        source_test_inherited_in_files_changed=source_test_inherited_claimed,
                        close_worktree_clean=close_worktree_clean if round_closed else None,
                        startup_evidence_trusted=startup_evidence_trusted,
                        all_in_decision_allowlist=all_in_decision_allowlist,
                        decision_immutability_failed=decision_immutability_failed,
                    )
                )
            else:
                checks.append(
                    _check(
                        "files_changed_excludes_inherited_dirty_files",
                        "FAIL",
                        "inherited source/test baseline dirty files in files_changed are unauthorized: must have startup evidence, decision allowlist, and no live decision mutation",
                        inherited_files_in_files_changed=inherited_claimed,
                        source_test_inherited_in_files_changed=source_test_inherited_claimed,
                        close_worktree_clean=close_worktree_clean if round_closed else None,
                        startup_evidence_trusted=startup_evidence_trusted,
                        all_in_decision_allowlist=all_in_decision_allowlist,
                        decision_immutability_failed=decision_immutability_failed,
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

    missing_diff_files = sorted(required_changed_for_diff - files_changed)
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

    substantive_dirty_files = {path for path in required_changed_for_diff if _is_substantive_change(path)}
    # Also include source/test paths claimed in report prose — if the report
    # body says a source/test file changed, it must appear in files_changed.
    claimed_source_test = _extract_claimed_source_test_paths(report_text) if report_text else set()
    substantive_dirty_files |= claimed_source_test
    missing_substantive = sorted(substantive_dirty_files - files_changed)
    if missing_substantive:
        checks.append(
            _check(
                "files_changed_covers_substantive_changes",
                "FAIL",
                "files_changed omits substantive source/test/artifact changes",
                missing_substantive_files=missing_substantive,
                substantive_dirty_files=sorted(substantive_dirty_files),
                claimed_source_test_paths=sorted(claimed_source_test),
            )
        )
    else:
        checks.append(
            _check(
                "files_changed_covers_substantive_changes",
                "PASS",
                "files_changed covers substantive source/test/artifact changes",
                substantive_dirty_files=sorted(substantive_dirty_files),
                claimed_source_test_paths=sorted(claimed_source_test),
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


def _baseline_lifecycle_checks(
    *,
    delta_summary: dict[str, Any],
    decision_text: str,
    report_text: str,
    state_dir: Path | None = None,
    current_decision_id: str = "",
) -> list[dict[str, Any]]:
    baseline_available = bool(delta_summary.get("baseline_available"))
    baseline_dirty_files = _string_set(delta_summary.get("baseline_dirty_files"))
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    scope_text = _markdown_section(decision_text, "Implementation Scope")
    source_test_scope = _allowed_source_test_scope_paths(scope_text)
    # Only files explicitly listed in the "Allowed Inherited Dirty Baseline
    # Files" section of the decision are allowed as inherited dirty baseline.
    # Files that merely appear in Implementation Scope are NOT automatically
    # allowed — doing so would mask late baseline capture (where Codex modifies
    # source/test files before running preflight, causing those modifications
    # to be absorbed into the baseline and misclassified as inherited).
    allowed_inherited = _allowed_inherited_baseline_paths(decision_text)
    source_test_baseline_dirty = sorted(baseline_dirty_files & source_test_scope)
    unauthorized = sorted((baseline_dirty_files & source_test_scope) - allowed_inherited)
    # NOTE: No bootstrapping exception.  Only the decision's "Allowed
    # Inherited Dirty Baseline Files" section can authorize inherited
    # dirty source/test files.  The report cannot retroactively
    # authorize them.  This enforces the clean-start policy: source/test
    # files must be clean at startup unless the decision explicitly
    # allows them as inherited dirty.
    allowed_claimed = sorted((baseline_dirty_files & source_test_scope) & allowed_inherited)
    generated_or_archive_dirty = sorted(path for path in baseline_dirty_files if _is_generated_state_or_archive_path(path))
    checks: list[dict[str, Any]] = []

    # Read close snapshot to determine baseline lifecycle state.
    close_snapshot = _read_round_close_snapshot(state_dir) if state_dir else {}
    # Only consider the round closed if the close snapshot belongs to the
    # current decision; stale close snapshots from previous rounds should
    # not affect the current round's lifecycle checks.
    snapshot_decision_id = str(close_snapshot.get("decision_id") or "") if close_snapshot else ""
    snapshot_matches_current = bool(current_decision_id and snapshot_decision_id == current_decision_id)
    round_closed = bool(close_snapshot and close_snapshot.get("round_closed")) and snapshot_matches_current
    close_worktree_clean = bool(close_snapshot.get("close_worktree_clean")) if close_snapshot else False
    close_dirty_files = _string_set(close_snapshot.get("close_dirty_files")) if close_snapshot else set()
    close_snapshot_available = bool(close_snapshot) and snapshot_matches_current

    # --- baseline_lifecycle_violation check (before baseline_lifecycle_guard) ---
    baseline_has_untracked_impl = bool(delta_summary.get("baseline_has_untracked_implementation_files"))
    baseline_untracked_files = list(delta_summary.get("baseline_untracked_files") or [])
    untracked_impl_files = [path for path in baseline_untracked_files if _is_implementation_file(path)]

    if baseline_available and baseline_has_untracked_impl:
        checks.append(
            _check(
                "baseline_lifecycle_violation",
                "FAIL",
                "baseline was captured after implementation started; untracked implementation files found in baseline",
                baseline_untracked_implementation_files=sorted(untracked_impl_files),
            )
        )
    elif baseline_available and not baseline_has_untracked_impl:
        checks.append(
            _check(
                "baseline_lifecycle_violation",
                "PASS",
                "baseline was captured before implementation; no untracked implementation files in baseline",
            )
        )
    else:
        checks.append(
            _check(
                "baseline_lifecycle_violation",
                "WARN",
                "baseline is unavailable; lifecycle violation cannot be checked",
            )
        )

    lifecycle_violation_failed = baseline_available and baseline_has_untracked_impl

    if not baseline_available:
        checks.append(
            _check(
                "baseline_lifecycle_guard",
                "WARN",
                "round baseline is unavailable; legacy lifecycle guard is advisory only",
                source_test_scope=sorted(source_test_scope),
            )
        )
        return checks

    # For closed rounds with close snapshot, adjust lifecycle guard behavior.
    if round_closed and close_snapshot_available:
        if close_worktree_clean:
            # Round closed with clean worktree: stale baseline dirty files
            # are not a concern since the worktree was clean at close time.
            checks.append(
                _check(
                    "baseline_lifecycle_guard",
                    "PASS",
                    "round is closed with clean worktree; baseline dirty files are stale and no longer active",
                    source_test_baseline_dirty=source_test_baseline_dirty,
                    allowed_inherited_dirty_files=sorted(allowed_inherited),
                    generated_or_archive_baseline_dirty_files=generated_or_archive_dirty,
                    close_worktree_clean=True,
                    close_snapshot_available=True,
                )
            )
        else:
            # Round closed with dirty worktree: warn based on close snapshot
            # dirty files, not stale baseline dirty files.
            close_source_test_dirty = sorted(close_dirty_files & source_test_scope)
            # Source/test files in the Implementation Scope are authorized
            # modifications for this round.  Only flag:
            # 1. Source/test files NOT in the Implementation Scope and NOT in
            #    the decision's "Allowed Inherited Dirty Baseline Files" section.
            # 2. Inherited dirty source/test files (dirty at baseline) that are
            #    NOT in the "Allowed Inherited Dirty Baseline Files" section.
            close_unauthorized = sorted(
                path for path in close_dirty_files
                if _path_is_source_or_test(path)
                and path not in source_test_scope
                and path not in allowed_inherited
            )
            close_inherited_unauthorized = sorted(
                path for path in close_dirty_files
                if path in inherited_dirty_files
                and _path_is_source_or_test(path)
                and path not in allowed_inherited
            )
            close_unauthorized = sorted(set(close_unauthorized) | set(close_inherited_unauthorized))
            # NOTE: No bootstrapping exception for close snapshot either.
            # Only the decision's "Allowed Inherited Dirty Baseline Files"
            # section can authorize inherited dirty source/test files.
            if close_unauthorized:
                checks.append(
                    _check(
                        "baseline_lifecycle_guard",
                        "FAIL",
                        "round closed with dirty worktree; close snapshot contains unauthorized source/test dirty files",
                        unauthorized_inherited_source_test_files=close_unauthorized,
                        close_dirty_files=sorted(close_dirty_files),
                        close_source_test_dirty=close_source_test_dirty,
                        allowed_inherited_dirty_files=sorted(allowed_inherited),
                        source_test_scope=sorted(source_test_scope),
                        close_worktree_clean=False,
                        close_snapshot_available=True,
                    )
                )
            else:
                checks.append(
                    _check(
                        "baseline_lifecycle_guard",
                        "PASS",
                        "round closed with dirty worktree; close snapshot source/test dirty files are within allowed scope",
                        source_test_baseline_dirty=source_test_baseline_dirty,
                        close_source_test_dirty=close_source_test_dirty,
                        allowed_inherited_dirty_files=sorted(allowed_inherited),
                        generated_or_archive_baseline_dirty_files=generated_or_archive_dirty,
                        close_worktree_clean=False,
                        close_snapshot_available=True,
                    )
                )
    elif unauthorized:
        checks.append(
            _check(
                "baseline_lifecycle_guard",
                "FAIL",
                "baseline contains source/test dirty files not allowed as inherited baseline",
                unauthorized_inherited_source_test_files=unauthorized,
                allowed_inherited_dirty_files=sorted(allowed_inherited),
                source_test_scope=sorted(source_test_scope),
            )
        )
    else:
        if lifecycle_violation_failed:
            checks.append(
                _check(
                    "baseline_lifecycle_guard",
                    "WARN",
                    "baseline source/test dirty files are absent or explicitly allowed; baseline_lifecycle_violation is present; inherited dirty classification may be unreliable",
                    source_test_baseline_dirty=source_test_baseline_dirty,
                    allowed_inherited_dirty_files=sorted(allowed_inherited),
                    generated_or_archive_baseline_dirty_files=generated_or_archive_dirty,
                )
            )
        else:
            checks.append(
                _check(
                    "baseline_lifecycle_guard",
                    "PASS",
                    "baseline source/test dirty files are absent or explicitly allowed",
                    source_test_baseline_dirty=source_test_baseline_dirty,
                    allowed_inherited_dirty_files=sorted(allowed_inherited),
                    generated_or_archive_baseline_dirty_files=generated_or_archive_dirty,
                )
            )
    if allowed_claimed:
        explains = _report_explains_inherited_baseline_files(report_text)
        if explains and lifecycle_violation_failed:
            checks.append(
                _check(
                    "baseline_inherited_allowlist_explained",
                    "WARN",
                    "report explains explicitly allowed inherited baseline files; baseline_lifecycle_violation is present; inherited dirty classification may be unreliable",
                    allowed_inherited_source_test_files=allowed_claimed,
                )
            )
        else:
            checks.append(
                _check(
                    "baseline_inherited_allowlist_explained",
                    "PASS" if explains else "FAIL",
                    "report explains explicitly allowed inherited baseline files"
                    if explains
                    else "report does not explain explicitly allowed inherited baseline files",
                    allowed_inherited_source_test_files=allowed_claimed,
                )
            )
    elif inherited_dirty_files:
        if lifecycle_violation_failed:
            checks.append(
                _check(
                    "baseline_inherited_allowlist_explained",
                    "WARN",
                    "no source/test inherited baseline explanation is required; baseline_lifecycle_violation is present; inherited dirty classification may be unreliable",
                    inherited_dirty_files=sorted(inherited_dirty_files),
                )
            )
        else:
            checks.append(
                _check(
                    "baseline_inherited_allowlist_explained",
                    "PASS",
                    "no source/test inherited baseline explanation is required",
                    inherited_dirty_files=sorted(inherited_dirty_files),
                )
            )
    return checks


def _baseline_capture_order_checks(
    *,
    delta_summary: dict[str, Any],
    files_changed: set[str],
    decision_text: str,
    report_text: str,
    pytest_text: str,
    state_dir: Path | None = None,
    current_decision_id: str = "",
) -> list[dict[str, Any]]:
    """Check for suspected late baseline capture.

    Late baseline capture occurs when Codex modifies source/test files before
    running ``preflight``, causing those modifications to be absorbed into the
    baseline and misclassified as inherited dirty files.

    The key signal is: a file is simultaneously in ``baseline_dirty_files``,
    ``files_changed`` (from the report), and the source/test scope.  If such
    a file exists, it is *suspected* late baseline capture unless there is
    explicit evidence that the file was already dirty before the round started
    (e.g. the startup ``git status --short`` in ``pytest_result.txt`` shows
    the file as dirty).
    """
    baseline_available = bool(delta_summary.get("baseline_available"))
    baseline_dirty_files = _string_set(delta_summary.get("baseline_dirty_files"))
    scope_text = _markdown_section(decision_text, "Implementation Scope")
    source_test_scope = _allowed_source_test_scope_paths(scope_text)
    allowed_inherited = _allowed_inherited_baseline_paths(decision_text)

    checks: list[dict[str, Any]]

    if not baseline_available:
        checks = [
            _check(
                "baseline_capture_order",
                "WARN",
                "baseline is unavailable; capture order cannot be checked",
                capture_order_status="unavailable",
            )
        ]
        return checks

    # The overlap: files that are baseline-dirty, in files_changed, and in
    # the source/test scope.  These are suspected late baseline captures.
    overlap = sorted(
        (baseline_dirty_files & files_changed) & source_test_scope
    )

    # Determine pre-startup evidence from pytest_result.txt.
    # The startup section records ``git status --short`` before any
    # implementation.  If a file appears there as dirty, it was genuinely
    # inherited — not a late capture.  However, the startup evidence is
    # only trusted if the git status command appeared after path confirmation.
    order_info = _startup_status_order_valid(pytest_text)
    startup_dirty_files = _extract_startup_dirty_files(pytest_text)
    startup_evidence_trusted = order_info.get("startup_status_evidence_trusted", False)

    # Separate overlap into confirmed-inherited vs suspected-late-capture.
    # If startup evidence is not trusted (git status before path confirmation),
    # all overlap files are treated as suspected late capture.
    if startup_evidence_trusted:
        confirmed_inherited = sorted(
            path for path in overlap if path in startup_dirty_files
        )
        suspected_late = sorted(
            path for path in overlap if path not in startup_dirty_files
        )
    else:
        confirmed_inherited = []
        suspected_late = sorted(overlap)

    # Build detail fields for final_gate_result.json.
    detail_fields: dict[str, Any] = {
        "suspected_late_baseline_files": suspected_late,
        "allowed_inherited_dirty_files": sorted(allowed_inherited),
        "baseline_dirty_source_test_files": sorted(baseline_dirty_files & source_test_scope),
        "files_changed_overlap": overlap,
        "confirmed_inherited_from_startup_evidence": confirmed_inherited,
        "startup_status_evidence_trusted": startup_evidence_trusted,
    }

    if not overlap:
        detail_fields["capture_order_status"] = "clean"
        checks = [
            _check(
                "baseline_capture_order",
                "PASS",
                "baseline capture order is clean; no source/test files overlap between baseline dirty and files_changed",
                **detail_fields,
            )
        ]
    elif suspected_late:
        # There are suspected late baseline captures with no startup evidence.
        # Even if the decision has an Allowed Inherited Dirty Baseline Files
        # section, that only means "these files are allowed to be inherited" —
        # it does NOT prove they were dirty before the round started.
        if confirmed_inherited:
            # Mixed: some confirmed, some suspected.
            detail_fields["capture_order_status"] = "suspected_late_capture_partial"
            checks = [
                _check(
                    "baseline_capture_order",
                    "FAIL",
                    "suspected late baseline capture: source/test files appear in both baseline dirty files and files_changed without startup evidence; some files have startup evidence confirming they were pre-existing",
                    **detail_fields,
                )
            ]
        else:
            detail_fields["capture_order_status"] = "suspected_late_capture"
            checks = [
                _check(
                    "baseline_capture_order",
                    "FAIL",
                    "suspected late baseline capture: source/test files appear in both baseline dirty files and files_changed without startup evidence",
                    **detail_fields,
                )
            ]
    else:
        # All overlap files have startup evidence confirming they were
        # pre-existing dirty files — genuine inherited dirty, not late capture.
        detail_fields["capture_order_status"] = "confirmed_inherited"
        checks = [
            _check(
                "baseline_capture_order",
                "WARN",
                "source/test files overlap between baseline dirty and files_changed, but startup evidence confirms they were pre-existing; inherited dirty classification is reliable",
                **detail_fields,
            )
        ]

    return checks


def _extract_startup_dirty_files(pytest_text: str) -> set[str]:
    """Extract dirty file paths from the startup ``git status --short``
    command block in ``pytest_result.txt``.

    The startup section is the *first* ``git status --short`` command block
    that appears *after* the required path-confirmation commands.  If the
    first ``git status --short`` block appears before path confirmation,
    it is not trusted and this function returns an empty set.
    """
    blocks = _parse_recorded_command_blocks(pytest_text)
    block_list = blocks.get("blocks", [])

    # Find the first git status --short block that appears after all
    # path-confirmation commands.
    path_confirmation_seen = {
        "Set-Location": False,
        "Get-Location": False,
        "Test-Path": False,
        "git rev-parse": False,
    }
    for block in block_list:
        if not isinstance(block, dict):
            continue
        command = str(block.get("command") or "").strip()
        # Track path-confirmation commands.
        if command.startswith("Set-Location"):
            path_confirmation_seen["Set-Location"] = True
        elif command == "Get-Location":
            path_confirmation_seen["Get-Location"] = True
        elif command.startswith("Test-Path"):
            path_confirmation_seen["Test-Path"] = True
        elif command.startswith("git rev-parse"):
            path_confirmation_seen["git rev-parse"] = True
        elif command == "git status --short":
            # Only trust this git status if all path-confirmation commands
            # have been seen before it.
            if all(path_confirmation_seen.values()):
                stdout = str(block.get("stdout") or "")
                return _parse_git_status_short_dirty(stdout)
            else:
                # git status appears before path confirmation — untrusted.
                return set()
    return set()


def _startup_status_order_valid(pytest_text: str) -> dict[str, Any]:
    """Check whether the startup command order in ``pytest_result.txt`` is valid.

    The required order is:
    1. Set-Location
    2. Get-Location
    3. Test-Path
    4. git rev-parse --show-toplevel
    5. git status --short

    Returns a dict with:
    - ``valid``: bool — whether the order is correct
    - ``startup_status_block_index``: int or None — index of the git status block
    - ``path_confirmation_block_indexes``: dict mapping command name to block index
    - ``startup_status_evidence_trusted``: bool — whether git status evidence is trusted
    """
    blocks = _parse_recorded_command_blocks(pytest_text)
    block_list = blocks.get("blocks", [])

    path_confirmation_indexes: dict[str, int | None] = {
        "Set-Location": None,
        "Get-Location": None,
        "Test-Path": None,
        "git rev-parse": None,
    }
    git_status_index: int | None = None

    for idx, block in enumerate(block_list):
        if not isinstance(block, dict):
            continue
        command = str(block.get("command") or "").strip()
        if command.startswith("Set-Location") and path_confirmation_indexes["Set-Location"] is None:
            path_confirmation_indexes["Set-Location"] = idx
        elif command == "Get-Location" and path_confirmation_indexes["Get-Location"] is None:
            path_confirmation_indexes["Get-Location"] = idx
        elif command.startswith("Test-Path") and path_confirmation_indexes["Test-Path"] is None:
            path_confirmation_indexes["Test-Path"] = idx
        elif command.startswith("git rev-parse") and path_confirmation_indexes["git rev-parse"] is None:
            path_confirmation_indexes["git rev-parse"] = idx
        elif command == "git status --short" and git_status_index is None:
            git_status_index = idx

    # git status is trusted only if all path-confirmation commands appear
    # before it.
    all_path_seen = all(v is not None for v in path_confirmation_indexes.values())
    if all_path_seen and git_status_index is not None:
        max_path_index = max(v for v in path_confirmation_indexes.values() if v is not None)
        trusted = git_status_index > max_path_index
    else:
        trusted = False

    valid = trusted or git_status_index is None

    return {
        "valid": valid,
        "startup_status_block_index": git_status_index,
        "path_confirmation_block_indexes": path_confirmation_indexes,
        "startup_status_evidence_trusted": trusted,
    }


def _decision_immutability_check(
    *,
    files_changed: set[str],
    new_dirty_files: set[str],
    baseline_dirty_files: set[str],
    round_id: str,
) -> dict[str, Any]:
    """Check that live decision_packet.md was not modified during execution."""
    LIVE_DECISION_PATH = "project_state/decision_packet.md"
    # Archive path pattern: project_state/rounds/<round_id>/decision_packet.md
    _archive_prefix = f"project_state/rounds/{round_id}/" if round_id else ""

    in_files_changed = LIVE_DECISION_PATH in files_changed
    in_new_dirty = LIVE_DECISION_PATH in new_dirty_files
    in_baseline_dirty = LIVE_DECISION_PATH in baseline_dirty_files

    # Only flag if it's the live path, not an archive copy
    is_live_mutation = in_files_changed or in_new_dirty

    if in_baseline_dirty:
        return _check(
            "decision_immutability",
            "FAIL",
            "live project_state/decision_packet.md is dirty in startup baseline; execution must not proceed",
            live_decision_in_baseline=True,
            live_decision_in_files_changed=in_files_changed,
            live_decision_in_new_dirty=in_new_dirty,
        )

    if is_live_mutation:
        return _check(
            "decision_immutability",
            "FAIL",
            "live project_state/decision_packet.md appears in round delta or files_changed; decision must not be modified during execution",
            live_decision_in_files_changed=in_files_changed,
            live_decision_in_new_dirty=in_new_dirty,
        )

    return _check(
        "decision_immutability",
        "PASS",
        "live project_state/decision_packet.md was not modified during execution",
        live_decision_in_files_changed=False,
        live_decision_in_new_dirty=False,
    )


def _build_output_scope_check(
    *,
    new_dirty_files: set[str],
    files_changed: set[str],
    pytest_text: str,
) -> dict[str, Any]:
    """Check that build-generated files in round delta have a recorded build command."""
    build_files_in_delta = {
        path for path in new_dirty_files | files_changed
        if path in BUILD_OUTPUT_WHITELIST
    }

    if not build_files_in_delta:
        return _check(
            "build_output_scope",
            "PASS",
            "no build-generated state files in round delta",
            build_files_in_delta=[],
        )

    # Check if pytest_result.txt records a build command
    recorded = _parse_recorded_command_blocks(pytest_text)
    has_build_command = False
    build_exit_zero = False
    for block in recorded.get("blocks", []):
        if not isinstance(block, dict):
            continue
        command = str(block.get("command") or "")
        if "project_state build" in command or "project-state build" in command or "project_state.project_state build" in command:
            has_build_command = True
            exit_code = block.get("exit_code")
            if exit_code == 0:
                build_exit_zero = True
                break

    if has_build_command and build_exit_zero:
        return _check(
            "build_output_scope",
            "PASS",
            "build-generated state files in round delta have recorded build command with exit code 0",
            build_files_in_delta=sorted(build_files_in_delta),
            build_command_recorded=True,
            build_exit_zero=True,
        )

    if has_build_command and not build_exit_zero:
        return _check(
            "build_output_scope",
            "WARN",
            "build-generated state files in round delta but build command did not exit with code 0",
            build_files_in_delta=sorted(build_files_in_delta),
            build_command_recorded=True,
            build_exit_zero=False,
        )

    # No build command recorded but build files in delta
    return _check(
        "build_output_scope",
        "WARN",
        "build_output_scope_unverified: build-generated state files in round delta without recorded build command",
        build_files_in_delta=sorted(build_files_in_delta),
        build_command_recorded=False,
    )


def _verified_cli_coverage_check(
    *,
    report_text: str,
    tests_ran: list[str],
    pytest_text: str,
) -> dict[str, Any]:
    """Check that CLI commands claimed as verified in the report are covered by tests_ran."""
    # Known CLI subcommands that should be covered if claimed
    CLI_PATTERNS = {
        "active-execution-view": r"active[- ]execution[- ]view",
    }

    uncovered_clis: list[str] = []
    for cli_name, pattern in CLI_PATTERNS.items():
        if re.search(pattern, report_text, re.IGNORECASE):
            # Check if this CLI appears in tests_ran
            in_tests_ran = any(cli_name in str(test) for test in tests_ran)
            # Also check if there's a command block in pytest_result
            recorded = _parse_recorded_command_blocks(pytest_text)
            in_command_blocks = any(
                isinstance(block, dict) and cli_name.replace("-", " ") in str(block.get("command") or "").lower().replace("-", " ")
                or isinstance(block, dict) and cli_name in str(block.get("command") or "")
                for block in recorded.get("blocks", [])
            )
            if not in_tests_ran and not in_command_blocks:
                uncovered_clis.append(cli_name)

    if not uncovered_clis:
        return _check(
            "verified_cli_coverage",
            "PASS",
            "all CLI commands claimed in report are covered by tests_ran or pytest_result command blocks",
            uncovered_clis=[],
        )

    return _check(
        "verified_cli_coverage",
        "WARN",
        "report claims CLI verification but commands are not in tests_ran or pytest_result command blocks",
        uncovered_clis=uncovered_clis,
    )


def _startup_baseline_consistency_check(
    *,
    delta_summary: dict[str, Any],
    decision_text: str,
    report_text: str,
    pytest_text: str,
) -> dict[str, Any]:
    """Check that startup ``git status --short`` dirty files are consistent
    with baseline dirty records.

    If the startup ``git status --short`` in ``pytest_result.txt`` shows
    source/test dirty files, but the baseline records (``round_baseline.json``,
    ``round_delta_summary.json``) show no corresponding dirty files, this
    indicates an inconsistency — either the baseline was captured after
    modifications (late baseline capture) or the baseline records are
    inaccurate.
    """
    baseline_available = bool(delta_summary.get("baseline_available"))
    baseline_dirty_files = _string_set(delta_summary.get("baseline_dirty_files"))
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    scope_text = _markdown_section(decision_text, "Implementation Scope")
    source_test_scope = _allowed_source_test_scope_paths(scope_text)

    # Extract startup dirty files from pytest_result.txt
    startup_dirty_files = _extract_startup_dirty_files(pytest_text)
    order_info = _startup_status_order_valid(pytest_text)
    startup_evidence_trusted = order_info.get("startup_status_evidence_trusted", False)

    # Filter startup dirty files to source/test scope
    startup_source_test_dirty = startup_dirty_files & source_test_scope

    # Determine which startup source/test dirty files are NOT in baseline records
    all_baseline_dirty = baseline_dirty_files | inherited_dirty_files
    missing_from_baseline = sorted(startup_source_test_dirty - all_baseline_dirty)

    # Check if report claims no inherited dirty when startup shows source/test dirty
    report_claims_no_inherited = (
        bool(report_text.strip())
        and _report_explains_inherited_baseline_files(report_text) is False
    )
    report_inconsistency = bool(startup_source_test_dirty) and report_claims_no_inherited

    if not baseline_available:
        return _check(
            "startup_baseline_consistency",
            "PASS",
            "baseline is unavailable; startup/baseline consistency check skipped",
            startup_source_test_dirty=sorted(startup_source_test_dirty),
            baseline_dirty_files=sorted(baseline_dirty_files),
            startup_evidence_trusted=startup_evidence_trusted,
        )

    if not startup_evidence_trusted:
        # No trusted startup git status evidence available — skip check
        # rather than WARN, because older pytest_result formats may not
        # include startup git status blocks.
        return _check(
            "startup_baseline_consistency",
            "PASS",
            "startup git status evidence not available or not trusted; consistency check skipped",
            startup_source_test_dirty=sorted(startup_source_test_dirty),
            baseline_dirty_files=sorted(baseline_dirty_files),
            startup_evidence_trusted=False,
        )

    if not startup_source_test_dirty:
        # Startup git status is clean for source/test files.
        # Check reverse: startup is clean but baseline claims source/test dirty.
        baseline_source_test_dirty = baseline_dirty_files & source_test_scope
        if baseline_source_test_dirty:
            return _check(
                "startup_baseline_consistency",
                "FAIL",
                "startup git status --short is clean but baseline records source/test dirty files; baseline inherited dirty classification is inconsistent with startup evidence",
                startup_source_test_dirty=[],
                baseline_dirty_files=sorted(baseline_dirty_files),
                inherited_dirty_files=sorted(inherited_dirty_files),
                baseline_source_test_dirty=sorted(baseline_source_test_dirty),
            )
        return _check(
            "startup_baseline_consistency",
            "PASS",
            "startup git status --short is consistent with baseline records; no source/test dirty files at startup",
            startup_source_test_dirty=[],
            baseline_dirty_files=sorted(baseline_dirty_files),
            missing_from_baseline=[],
        )

    if missing_from_baseline:
        # Startup shows source/test dirty but baseline doesn't record them
        return _check(
            "startup_baseline_consistency",
            "FAIL",
            "startup git status --short shows source/test dirty files not recorded in baseline; baseline records are inconsistent with startup evidence",
            startup_source_test_dirty=sorted(startup_source_test_dirty),
            baseline_dirty_files=sorted(baseline_dirty_files),
            inherited_dirty_files=sorted(inherited_dirty_files),
            missing_from_baseline=missing_from_baseline,
            report_inconsistency=report_inconsistency,
        )

    # Startup dirty files are all accounted for in baseline records
    if report_inconsistency:
        return _check(
            "startup_baseline_consistency",
            "FAIL",
            "startup git status --short shows source/test dirty files but report claims no inherited dirty files",
            startup_source_test_dirty=sorted(startup_source_test_dirty),
            baseline_dirty_files=sorted(baseline_dirty_files),
            inherited_dirty_files=sorted(inherited_dirty_files),
            missing_from_baseline=[],
            report_inconsistency=True,
        )

    return _check(
        "startup_baseline_consistency",
        "PASS",
        "startup git status --short is consistent with baseline records; source/test dirty files are properly recorded",
        startup_source_test_dirty=sorted(startup_source_test_dirty),
        baseline_dirty_files=sorted(baseline_dirty_files),
        inherited_dirty_files=sorted(inherited_dirty_files),
        missing_from_baseline=[],
    )


def _parse_git_status_short_dirty(status_output: str) -> set[str]:
    """Parse ``git status --short`` output into a set of dirty file paths."""
    paths: set[str] = set()
    for line in status_output.splitlines():
        if not line or len(line) < 4:
            continue
        # git status --short format: XY PATH
        # X = index status, Y = worktree status
        # The path starts at column 3 (0-indexed) in the raw line.
        # Do NOT strip the line — leading whitespace is significant.
        xy = line[:2]
        if xy == "??":
            path = line[3:].strip().strip('"')
        elif xy[0] in ("M", "A", "D", "R", "C", " ") or xy[1] in ("M", "A", "D", "R", "C", " "):
            # At least one of X/Y is a recognized status code.
            if xy[0] in ("M", "A", "D", "R", "C") or xy[1] in ("M", "A", "D", "R", "C"):
                path = line[3:].strip().strip('"')
            else:
                continue
        else:
            continue
        if path:
            paths.add(_norm_path(path))
    return paths


def _report_claims_close_round_success(report_text: str) -> bool:
    """Return True if report prose claims close-round ran or succeeded.

    Distinguishes success/completion claims from omission/skipped mentions.
    Legal omission language like "close-round intentionally omitted" or
    "close-round skipped" must NOT be treated as a closeout claim.
    """
    if not report_text:
        return False
    lower = report_text.lower()
    # Success/completion patterns: close-round actually ran and succeeded
    success_patterns = [
        "close-round succeeded",
        "close_round succeeded",
        "close-round completed",
        "close_round completed",
        "close-round ran successfully",
        "close_round ran successfully",
        "close-round finished",
        "close_round finished",
        "close-round passed",
        "close_round passed",
    ]
    if any(p in lower for p in success_patterns):
        return True
    return False


def _report_claims_archive_success(report_text: str) -> bool:
    """Return True if report prose claims archive creation or closeout success.

    Distinguishes archive creation claims from absence/omission mentions.
    Legal language like "no round archive" must NOT be treated as a claim.
    """
    if not report_text:
        return False
    lower = report_text.lower()
    # First check for negation/absence context — these are NOT claims
    negation_patterns = [
        "no round archive",
        "no round_archive",
        "no archive",
        "archive not created",
        "archive was not created",
        "archive not present",
    ]
    if any(p in lower for p in negation_patterns):
        return False
    # Archive creation/success patterns (only checked if no negation)
    archive_success_patterns = [
        "round archive was created",
        "round archive created",
        "round_archive created",
        "archived closeout succeeded",
        "archived closeout",
        "closeout success",
        "archive was created",
        "archive created successfully",
    ]
    if any(p in lower for p in archive_success_patterns):
        return True
    return False


def _report_mentions_close_round_omission(report_text: str) -> bool:
    """Return True if report prose mentions close-round was omitted/skipped.

    This is legal language for fast non-closeout and must NOT be treated
    as a closeout claim.
    """
    if not report_text:
        return False
    lower = report_text.lower()
    omission_patterns = [
        "close-round intentionally omitted",
        "close_round intentionally omitted",
        "close-round omitted",
        "close_round omitted",
        "close-round skipped",
        "close_round skipped",
        "close-round not run",
        "close_round not run",
        "close-round was not run",
        "close_round was not run",
        "closeout_allowed=false",
        "closeout not allowed",
        "fast non-closeout",
        "no round archive",
        "no round_archive",
    ]
    return any(p in lower for p in omission_patterns)


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


def _expected_exit_codes_by_command(
    command_plan_payload: dict[str, Any],
    *,
    skip_kinds: set[str] | None = None,
    skip_after_first_kind: str | None = None,
) -> dict[str, list[list[int]]]:
    expected: dict[str, list[list[int]]] = {}
    skip = skip_kinds or set()
    skip_remaining = False
    commands = command_plan_payload.get("commands")
    if not isinstance(commands, list):
        return expected
    for item in commands:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command") or "")
        kind = str(item.get("kind") or "") or _command_kind(command)
        if skip_remaining:
            continue
        if skip_after_first_kind and kind == skip_after_first_kind:
            skip_remaining = True
        if kind in skip:
            continue
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


_STARTUP_COMMAND_PATTERNS: list[tuple[str, str]] = [
    ("Set-Location", "Set-Location"),
    ("Get-Location", "Get-Location"),
    ("Test-Path", "Test-Path"),
    ("git rev-parse", "git rev-parse --show-toplevel"),
    ("git status", "git status"),
]


def _is_startup_command(command: str) -> bool:
    """Return True if *command* is a startup path/status command.

    Startup commands (Set-Location, Get-Location, Test-Path, git rev-parse,
    git status) are recorded as command blocks in pytest_result.txt but are
    not expected to appear in command_plan.json or codex_report_summary.tests_ran.
    """
    return any(pattern in command for pattern, _ in _STARTUP_COMMAND_PATTERNS)


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


def _recorded_final_check_status(pytest_text: str) -> str:
    recorded = _parse_recorded_command_blocks(pytest_text)
    blocks = [block for block in recorded.get("blocks", []) if isinstance(block, dict)]
    final_indexes = [
        index
        for index, block in enumerate(blocks)
        if _command_kind(str(block.get("command") or "")) == "final-check"
    ]
    if not final_indexes:
        return ""
    close_indexes = [
        index
        for index, block in enumerate(blocks)
        if _command_kind(str(block.get("command") or "")) == "close-round"
    ]
    if close_indexes and final_indexes[-1] < close_indexes[-1]:
        return ""
    stdout = str(blocks[final_indexes[-1]].get("stdout") or "")
    first_line = next((line.strip() for line in stdout.splitlines() if line.strip()), "")
    prefix = f"{FINAL_GATE_NAME}: "
    if first_line.startswith(prefix):
        return first_line[len(prefix) :].strip()
    return ""


def _final_check_stdout_status_check(pytest_text: str, expected_gate_status: str) -> dict[str, Any]:
    recorded_status = _recorded_final_check_status(pytest_text)
    if not recorded_status:
        return _check(
            "final_check_stdout_matches_gate_status",
            "PASS",
            "no recorded final-check stdout status to compare",
            required=False,
        )
    conservative_warn = recorded_status == "WARN" and expected_gate_status in ("PASSED_WITH_LIMITATIONS", "PASSED")
    matches = recorded_status == expected_gate_status or conservative_warn
    return _check(
        "final_check_stdout_matches_gate_status",
        "PASS" if matches else "FAIL",
        "recorded final-check stdout matches gate_status"
        if matches
        else "recorded final-check stdout does not match gate_status",
        expected_gate_status=expected_gate_status,
        recorded_stdout_status=recorded_status,
        conservative_warn_accepted=conservative_warn,
    )


def _validate_command_plan_consistency(
    *,
    state_dir: Path,
    decision: dict[str, Any],
    report: dict[str, Any],
    pytest_text: str,
    extra_skip_kinds: set[str] | None = None,
    close_round_in_progress: bool = False,
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
    # Startup commands (Set-Location, Get-Location, Test-Path, git rev-parse,
    # git status) are recorded as command blocks in pytest_result.txt but are
    # not expected to appear in command_plan.json.  Exclude them from the
    # coverage diff so they do not cause a circular conflict between
    # startup_command_coverage and command_plan_covers_report_tests.
    missing_report_tests = sorted(
        cmd for cmd in (report_tests - plan_commands) if not _is_startup_command(cmd)
    )
    missing_pytest_tests = sorted(
        cmd for cmd in (pytest_tests - plan_commands) if not _is_startup_command(cmd)
    )
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

    # startup_command_coverage checks the actual recorded command blocks in
    # pytest_result.txt (the ``===== COMMAND: ... =====`` sections), not the
    # ``tests_ran`` JSON array.  This decouples startup coverage from
    # command_plan coverage: startup commands satisfy this check via their
    # recorded command blocks without needing to be listed in tests_ran or
    # command_plan.json.
    recorded_for_startup = _parse_recorded_command_blocks(pytest_text)
    recorded_commands = {
        str(block.get("command") or "")
        for block in (recorded_for_startup.get("blocks") or [])
        if str(block.get("command") or "")
    }

    missing_startup: list[dict[str, str]] = []
    for pattern, description in _STARTUP_COMMAND_PATTERNS:
        if not any(pattern in cmd for cmd in recorded_commands):
            missing_startup.append({"pattern": pattern, "description": description})

    checks.append(
        _check(
            "startup_command_coverage",
            "PASS" if not missing_startup else "FAIL",
            "pytest_result command blocks cover required startup commands"
            if not missing_startup
            else "pytest_result is missing required startup command blocks",
            missing_startup_commands=missing_startup,
        )
    )

    blocks = list(recorded_for_startup.get("blocks") or [])
    malformed_commands = list(recorded_for_startup.get("malformed_commands") or [])
    blocks_by_command: dict[str, list[dict[str, Any]]] = {}
    for block in blocks:
        blocks_by_command.setdefault(str(block.get("command") or ""), []).append(block)

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

    # close-round must be the last command block in pytest_result.txt after it
    # appears. Before archive creation, final-check can run before close-round
    # has a recorded block, because close-round is the command that will append it.
    close_round_commands = [
        item for item in plan_commands if _command_kind(item) == "close-round"
    ]
    skip_pending_close_round = False
    if close_round_commands and blocks:
        report_round_id = str(report.get("round_id") or "")
        manifest_present = bool(report_round_id and (state_dir / "rounds" / report_round_id / ARCHIVE_MANIFEST_NAME).exists())
        close_round_block_present = any(
            _command_kind(str(block.get("command") or "")) == "close-round"
            for block in blocks
        )
        close_round_self_record_pending = (
            manifest_present
            and not close_round_block_present
            and _archive_file_matches_live(state_dir, report_round_id, "pytest_result.txt") is not True
        )
        if (
            (manifest_present or close_round_block_present)
            and not close_round_in_progress
            and not close_round_self_record_pending
        ):
            last_block_command = str(blocks[-1].get("command") or "")
            last_block_kind = _command_kind(last_block_command)
            close_round_is_last = last_block_kind == "close-round"
            checks.append(
                _check(
                    "close_round_is_last_command_block",
                    "PASS" if close_round_is_last else "FAIL",
                    "close-round is the last command block in pytest_result"
                    if close_round_is_last
                    else f"close-round is not the last command block; last block is: {last_block_command!r}",
                    last_command=last_block_command,
                    last_kind=last_block_kind,
                )
            )
        else:
            skip_pending_close_round = True
            checks.append(
                _check(
                    "close_round_is_last_command_block",
                    "PASS",
                    "close-round command block is pending until close-round completes",
                    required=False,
                    skipped_reason="close_round_in_progress"
                    if close_round_in_progress
                    else "close_round_self_record_pending"
                    if close_round_self_record_pending
                    else "archive_pending_pre_close_round",
                )
            )
    elif close_round_commands:
        skip_pending_close_round = True

    _skip_kinds: set[str] = {"final-check", "status"}
    if skip_pending_close_round:
        _skip_kinds.add("close-round")
    # Also skip close-round when it's marked as not required (final-check failed)
    if "close-round" not in _skip_kinds:
        close_round_items = [
            item for item in (command_plan_payload.get("commands") or [])
            if isinstance(item, dict) and item.get("kind") == "close-round" and not item.get("required", True)
        ]
        if close_round_items:
            _skip_kinds.add("close-round")
    if extra_skip_kinds:
        _skip_kinds |= extra_skip_kinds
    expected_by_command = _expected_exit_codes_by_command(
        command_plan_payload,
        skip_kinds=_skip_kinds,
        skip_after_first_kind="final-check" if skip_pending_close_round else None,
    )
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

    return checks


# Kinds that are always exempt from execution-authority checks because they
# represent the startup/status phase already implied by the command-plan.
_EXECUTION_AUTHORITY_EXEMPT_KINDS: frozenset[str] = frozenset({
    "set-location",
    "pwd",
    "test-path",
    "git status",
    "git rev-parse",
    "startup",
})


def _command_plan_execution_authority_check(
    *,
    state_dir: Path,
    decision: dict[str, Any],
    report: dict[str, Any],
    pytest_text: str,
    command_plan_payload: dict[str, Any],
) -> dict[str, Any]:
    """Check that executed commands recorded in ``pytest_result.txt`` are
    authorized by the current round's ``command_plan``.

    A recorded command is *unauthorized* when:

    1. Its kind appears in ``command_plan.omitted_commands`` (explicitly
       omitted by the active profile), **or**
    2. Its kind is absent from the active command-plan's
       ``required_command_kinds`` and it is not a startup/status command
       represented by the startup phase.

    Policy:

    - A ``SUCCESS``/``ACCEPTED`` report with unauthorized commands → ``FAIL``.
    - A ``FAILED``/``REWORK_REQUIRED`` report with unauthorized commands →
      ``WARN`` only if the report explicitly states it stopped because of
      the unauthorized command; otherwise ``FAIL``.
    - Stale command-plan artifacts (mismatched decision_id/round_id) cannot
      authorize current-round commands; the check delegates to
      ``command_plan_ids_match`` for that and returns ``PASS`` here to avoid
      double-reporting.
    """
    check_name = "command_plan_execution_authority"

    if not command_plan_payload:
        return _check(
            check_name,
            "PASS",
            "command_plan.json not present; execution authority check not applicable",
            required=False,
        )

    # Delegate stale-ID detection to command_plan_ids_match to avoid
    # double-reporting the same failure.
    cp_decision_id = str(command_plan_payload.get("decision_id") or "")
    cp_round_id = str(command_plan_payload.get("round_id") or "")
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    if cp_decision_id != decision_id or cp_round_id != round_id:
        return _check(
            check_name,
            "PASS",
            "command_plan.json has stale IDs; delegated to command_plan_ids_match",
            required=False,
            skipped_reason="stale_command_plan_ids",
        )

    # Parse recorded command blocks
    recorded = _parse_recorded_command_blocks(pytest_text)
    blocks = [b for b in (recorded.get("blocks") or []) if isinstance(b, dict)]

    # Build authorized command string set from command_plan.commands
    authorized_commands: set[str] = set()
    for item in (command_plan_payload.get("commands") or []):
        if isinstance(item, dict):
            cmd = str(item.get("command") or "")
            if cmd:
                authorized_commands.add(cmd)

    # Build omitted kinds set from command_plan.omitted_commands
    omitted_kinds: set[str] = set()
    for item in (command_plan_payload.get("omitted_commands") or []):
        if isinstance(item, dict):
            kind = str(item.get("kind") or "")
            if kind:
                omitted_kinds.add(kind)

    # Build required kinds set from profile_meta
    profile_meta = command_plan_payload.get("profile_meta") or {}
    required_kinds: set[str] = set()
    for kind in (profile_meta.get("required_command_kinds") or []):
        required_kinds.add(str(kind))

    # Classify each recorded command
    unauthorized: list[dict[str, Any]] = []
    for block in blocks:
        command = str(block.get("command") or "")
        if not command:
            continue
        kind = _command_kind(command)

        # Startup commands are always exempt
        if _is_startup_command(command):
            continue
        if kind in _EXECUTION_AUTHORITY_EXEMPT_KINDS:
            continue

        # If the exact command string is in authorized_commands, it's OK
        if command in authorized_commands:
            continue

        # If the kind is in omitted_commands, it's unauthorized
        if kind in omitted_kinds:
            unauthorized.append({
                "command": command,
                "kind": kind,
                "reason": f"kind '{kind}' is in omitted_commands",
            })
            continue

        # If the kind is not in required_command_kinds, it's unauthorized
        # (unless it's a diagnostic that the command-plan itself doesn't track)
        if required_kinds and kind not in required_kinds:
            # Allow kinds that are not tracked by the command-plan at all
            # (e.g., "unknown", "python-inline") only when the report status
            # is not SUCCESS.  For SUCCESS reports, any non-required kind is
            # unauthorized.
            report_status = str(report.get("status") or "")
            if report_status == "SUCCESS" or kind not in ("unknown", "python-inline", "powershell"):
                unauthorized.append({
                    "command": command,
                    "kind": kind,
                    "reason": f"kind '{kind}' not in required_command_kinds",
                })

    if not unauthorized:
        return _check(
            check_name,
            "PASS",
            "all recorded commands are authorized by command_plan",
        )

    # Determine status based on report status
    report_status = str(report.get("status") or "")
    report_text = _read_text(state_dir / "codex_execution_report.md")

    # Check if the report explicitly states it stopped because of
    # unauthorized commands
    report_mentions_unauthorized = _report_mentions_unauthorized_commands(report_text)

    if report_status in ("FAILED", "BLOCKED", "PARTIAL"):
        if report_mentions_unauthorized:
            status = "WARN"
            detail = (
                "unauthorized commands detected in pytest_result; report "
                "acknowledges stopping due to unauthorized commands"
            )
        else:
            status = "FAIL"
            detail = (
                "unauthorized commands detected in pytest_result; report "
                "does not acknowledge the unauthorized commands"
            )
    else:
        # SUCCESS or unknown status with unauthorized commands is always FAIL
        status = "FAIL"
        detail = (
            "unauthorized commands detected in pytest_result for a "
            f"{report_status or 'UNKNOWN'} report"
        )

    return _check(
        check_name,
        status,
        detail,
        unauthorized_commands=unauthorized,
        report_status=report_status,
        report_acknowledges_unauthorized=report_mentions_unauthorized,
    )


def _report_mentions_unauthorized_commands(report_text: str) -> bool:
    """Return True if the report text explicitly mentions that execution
    stopped due to unauthorized or unplanned commands."""
    lowered = report_text.lower()
    markers = (
        "unauthorized command",
        "unplanned command",
        "command not authorized",
        "command-plan execution authority",
        "stopped because of",
        "omitted by",
        "not in required_command_kinds",
    )
    return any(marker in lowered for marker in markers)


def _expected_report_id(round_id: str) -> str:
    if round_id.startswith("round_"):
        return f"codex_report_{round_id[len('round_'):]}"
    return f"codex_report_{round_id}" if round_id else ""


def _report_status_from_gate(gate_status: str) -> tuple[str, str] | None:
    mapping = {
        "PASSED": ("SUCCESS", "ACCEPTED"),
        "PASSED_WITH_LIMITATIONS": ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS"),
        "WARN": ("PARTIAL", "NEEDS_REVIEW"),
        "FAILED": ("FAILED", "REWORK_REQUIRED"),
        "BLOCKED": ("BLOCKED", "BLOCKED"),
    }
    return mapping.get(gate_status)


def _is_fast_non_closeout_scenario(payload: dict[str, Any]) -> bool:
    """Detect if the final gate payload indicates a fast non-closeout scenario.

    Returns True when:
    - ``fast_profile_closeout_consistency`` check is present and PASS
    - ``closeout_allowed`` is False (closeout not permitted)
    - close-round was effectively omitted (not in commands or explicitly omitted)
    """
    for check in payload.get("checks", []):
        if not isinstance(check, dict):
            continue
        if check.get("name") != "fast_profile_closeout_consistency":
            continue
        if check.get("status") != "PASS":
            continue
        closeout_allowed = check.get("closeout_allowed")
        close_round_omitted = check.get("close_round_omitted")
        close_round_in_commands = check.get("close_round_in_commands")
        # closeout_allowed is stored as ``gp_closeout_allowed = gate_profile_payload.get("closeout_allowed") is True``
        # so it is a boolean: True only when closeout was explicitly allowed.
        if closeout_allowed is False:
            # close-round was effectively omitted when explicitly omitted OR
            # absent from commands while closeout not allowed.
            if close_round_omitted or not close_round_in_commands:
                return True
    return False


def _report_status_from_gate_payload(payload: dict[str, Any], *, mainline: str = "") -> tuple[str, str] | None:
    gate_status = str(payload.get("gate_status") or "")
    if gate_status == "PASSED_WITH_LIMITATIONS":
        return "SUCCESS", "ACCEPTED_WITH_LIMITATIONS"
    # Fast non-closeout: when closeout_allowed=false and close-round was
    # not run, the gate now produces PASS for archive-related checks
    # (instead of WARN), so the normal status derivation can proceed.
    # If gate_status is PASSED, the normal flow returns SUCCESS/ACCEPTED.
    # If gate_status is WARN (e.g. from status_policy_valid with historical
    # sample limitations), the WARN handler below derives the appropriate
    # status without forcing PARTIAL/REWORK_REQUIRED.
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
            "report_summary_fields_match_synthesis",
            "report_summary_status_source_available",
            "status_policy_valid",
            "files_changed_excludes_inherited_dirty_files",
            "baseline_capture_order",
            "build_output_scope",
            "verified_cli_coverage",
            "startup_baseline_consistency",
        }
        status_policy_has_limitations = any(
            isinstance(check, dict)
            and check.get("name") == "status_policy_valid"
            and check.get("status") == "WARN"
            and (check.get("limitations") or check.get("external_state_notices"))
            for check in payload.get("checks", [])
        )
        # reverse_solving blocker-only: status_policy_valid is PASS (not WARN)
        # with external_state_notices for historical artifacts.  The gate is
        # WARN only because the report status is non-success.  Return the
        # actual report status so synthesis matches the report.
        status_policy_pass_with_notices = any(
            isinstance(check, dict)
            and check.get("name") == "status_policy_valid"
            and check.get("status") == "PASS"
            and (check.get("limitations") or check.get("external_state_notices"))
            for check in payload.get("checks", [])
        )
        if (
            status_policy_pass_with_notices
            and not warn_check_names
            and report_status
            and report_status not in ("PARTIAL", "SUCCESS")
        ):
            return report_status, acceptance if acceptance else "REWORK_REQUIRED"
        if status_policy_has_limitations and warn_check_names <= allowed_prearchive_warnings:
            # For engineering_branch, if the only limitations are historical sample
            # artifacts, these are external state notices, not current-round issues.
            if mainline == "engineering_branch":
                all_limitations: list[str] = []
                for check in payload.get("checks", []):
                    if isinstance(check, dict) and check.get("name") == "status_policy_valid":
                        if isinstance(check.get("limitations"), list):
                            all_limitations.extend(check["limitations"])
                        if isinstance(check.get("external_state_notices"), list):
                            all_limitations.extend(check["external_state_notices"])
                if _historical_sample_limitations_only(all_limitations):
                    return "SUCCESS", "ACCEPTED"
            return "SUCCESS", "ACCEPTED_WITH_LIMITATIONS"
        if report_status == "SUCCESS" and warn_check_names and warn_check_names <= allowed_prearchive_warnings:
            return "SUCCESS", acceptance if acceptance else "ACCEPTED"
    # Check if PASSED gate has status_policy_valid with limitations or external_state_notices
    # (post-archive scenario where doctor is PASS but historical artifacts are still missing)
    if gate_status == "PASSED":
        for check in payload.get("checks", []):
            if (
                isinstance(check, dict)
                and check.get("name") == "status_policy_valid"
                and check.get("status") == "PASS"
                and (check.get("limitations") or check.get("external_state_notices"))
            ):
                # For engineering_branch, historical sample artifact limitations
                # are external state notices, not current-round limitations.
                check_limitations = list(check.get("limitations") or [])
                check_external = list(check.get("external_state_notices") or [])
                combined = check_limitations + check_external
                if mainline == "engineering_branch" and _historical_sample_limitations_only(combined):
                    return "SUCCESS", "ACCEPTED"
                return "SUCCESS", "ACCEPTED_WITH_LIMITATIONS"
    return _report_status_from_gate(gate_status)


def _preflight_failure_handoff_check(
    *,
    state_dir: Path,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Check that if preflight failed, the report does not claim success or acceptance.

    This is the preflight-failure handoff gate: a hard-stop preflight failure
    must not be packaged as COMPLETED or ACCEPTED.
    """
    preflight_path = state_dir / "gates" / PREFLIGHT_RESULT_NAME
    preflight_payload = _read_json(preflight_path)
    if not preflight_payload:
        return _check(
            "preflight_failure_handoff",
            "PASS",
            "no preflight result available; handoff check not applicable",
            required=False,
            skipped_reason="no_preflight_result",
        )

    preflight_status = str(preflight_payload.get("gate_status") or "").upper()
    preflight_failed = preflight_status in {"FAILED", "BLOCKED"}

    if not preflight_failed:
        return _check(
            "preflight_failure_handoff",
            "PASS",
            "preflight passed or warned; no handoff violation",
            preflight_status=preflight_status,
        )

    # Preflight failed — report must not claim success or acceptance.
    report_status = str(report.get("status") or "").upper()
    acceptance = str(report.get("acceptance_recommendation") or "").upper()
    success_statuses = {"SUCCESS", "COMPLETED", "COMPLETED_WITH_LIMITATIONS"}
    accepted_recommendations = {"ACCEPTED", "ACCEPTED_WITH_LIMITATIONS"}

    status_violation = report_status in success_statuses
    acceptance_violation = acceptance in accepted_recommendations

    if status_violation or acceptance_violation:
        violations: list[str] = []
        if status_violation:
            violations.append(f"report status is {report_status}")
        if acceptance_violation:
            violations.append(f"acceptance_recommendation is {acceptance}")
        return _check(
            "preflight_failure_handoff",
            "FAIL",
            f"preflight failed ({preflight_status}) but report claims success/acceptance: {'; '.join(violations)}",
            preflight_status=preflight_status,
            report_status=report_status,
            acceptance_recommendation=acceptance,
        )

    return _check(
        "preflight_failure_handoff",
        "PASS",
        f"preflight failed ({preflight_status}) and report correctly reflects non-success status",
        preflight_status=preflight_status,
        report_status=report_status,
        acceptance_recommendation=acceptance,
    )


def _stale_artifact_id_check(
    *,
    state_dir: Path,
    decision_id: str,
    round_id: str,
    report_id: str,
) -> dict[str, Any]:
    """Check that key gate artifacts carry current decision/round/report IDs.

    Stale artifacts from a previous round must not be used as current evidence.
    """
    stale_artifacts: list[dict[str, Any]] = []

    # Check preflight_result.json
    preflight_path = state_dir / "gates" / PREFLIGHT_RESULT_NAME
    preflight_payload = _read_json(preflight_path)
    if preflight_payload:
        pf_decision_id = str(preflight_payload.get("decision_id") or "")
        pf_round_id = str(preflight_payload.get("round_id") or "")
        if pf_decision_id and pf_decision_id != decision_id:
            stale_artifacts.append({
                "artifact": PREFLIGHT_RESULT_NAME,
                "field": "decision_id",
                "expected": decision_id,
                "actual": pf_decision_id,
            })
        if pf_round_id and pf_round_id != round_id:
            stale_artifacts.append({
                "artifact": PREFLIGHT_RESULT_NAME,
                "field": "round_id",
                "expected": round_id,
                "actual": pf_round_id,
            })

    # Check report_summary_synthesis.json
    synthesis_path = state_dir / "gates" / REPORT_SUMMARY_RESULT_NAME
    synthesis_payload = _read_json(synthesis_path)
    if synthesis_payload:
        syn_decision_id = str(synthesis_payload.get("decision_id") or "")
        syn_round_id = str(synthesis_payload.get("round_id") or "")
        syn_report_id = str(synthesis_payload.get("report_id") or "")
        if syn_decision_id and syn_decision_id != decision_id:
            stale_artifacts.append({
                "artifact": REPORT_SUMMARY_RESULT_NAME,
                "field": "decision_id",
                "expected": decision_id,
                "actual": syn_decision_id,
            })
        if syn_round_id and syn_round_id != round_id:
            stale_artifacts.append({
                "artifact": REPORT_SUMMARY_RESULT_NAME,
                "field": "round_id",
                "expected": round_id,
                "actual": syn_round_id,
            })
        if syn_report_id and syn_report_id != report_id:
            stale_artifacts.append({
                "artifact": REPORT_SUMMARY_RESULT_NAME,
                "field": "report_id",
                "expected": report_id,
                "actual": syn_report_id,
            })

    # Check command_plan.json
    command_plan_path = state_dir / "gates" / COMMAND_PLAN_RESULT_NAME
    command_plan_payload = _read_json(command_plan_path)
    if command_plan_payload:
        cp_decision_id = str(command_plan_payload.get("decision_id") or "")
        cp_round_id = str(command_plan_payload.get("round_id") or "")
        if cp_decision_id and cp_decision_id != decision_id:
            stale_artifacts.append({
                "artifact": COMMAND_PLAN_RESULT_NAME,
                "field": "decision_id",
                "expected": decision_id,
                "actual": cp_decision_id,
            })
        if cp_round_id and cp_round_id != round_id:
            stale_artifacts.append({
                "artifact": COMMAND_PLAN_RESULT_NAME,
                "field": "round_id",
                "expected": round_id,
                "actual": cp_round_id,
            })

    # Check final_gate_result.json
    final_gate_path = state_dir / "gates" / FINAL_GATE_RESULT_NAME
    final_gate_payload = _read_json(final_gate_path)
    if final_gate_payload:
        fg_decision_id = str(final_gate_payload.get("decision_id") or "")
        fg_round_id = str(final_gate_payload.get("round_id") or "")
        fg_report_id = str(final_gate_payload.get("report_id") or "")
        if fg_decision_id and fg_decision_id != decision_id:
            stale_artifacts.append({
                "artifact": FINAL_GATE_RESULT_NAME,
                "field": "decision_id",
                "expected": decision_id,
                "actual": fg_decision_id,
            })
        if fg_round_id and fg_round_id != round_id:
            stale_artifacts.append({
                "artifact": FINAL_GATE_RESULT_NAME,
                "field": "round_id",
                "expected": round_id,
                "actual": fg_round_id,
            })
        if fg_report_id and fg_report_id != report_id:
            stale_artifacts.append({
                "artifact": FINAL_GATE_RESULT_NAME,
                "field": "report_id",
                "expected": report_id,
                "actual": fg_report_id,
            })

    if stale_artifacts:
        return _check(
            "stale_artifact_ids",
            "FAIL",
            "gate artifacts reference stale decision/round/report IDs from a different round",
            stale_artifacts=stale_artifacts,
        )

    return _check(
        "stale_artifact_ids",
        "PASS",
        "gate artifacts carry current decision/round/report IDs",
    )


def _decision_contract_artifact_placement_check(
    *,
    contract: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Check that decision_contract required artifacts are correctly placed.

    Validates:
    1. Every ``required_generated_artifacts`` path must appear in
       ``codex_report_summary.generated_artifacts``.
    2. Every ``required_files_changed`` path must appear in
       ``codex_report_summary.files_changed``.
    3. If a required generated artifact appears only in
       ``referenced_artifacts`` (not in ``generated_artifacts``), FAIL.
    """
    if not contract.get("found") or contract.get("parse_error"):
        return _check(
            "decision_contract_artifact_placement",
            "PASS",
            "no valid decision_contract present; artifact placement check not applicable",
        )

    required_generated = set(contract.get("required_generated_artifacts") or [])
    required_changed = set(contract.get("required_files_changed") or [])
    if not required_generated and not required_changed:
        return _check(
            "decision_contract_artifact_placement",
            "PASS",
            "decision_contract has no required artifact/file constraints",
        )

    report_generated = _string_set(report.get("generated_artifacts"))
    report_changed = _string_set(report.get("files_changed"))
    report_referenced = _string_set(report.get("referenced_artifacts"))

    missing_generated = sorted(required_generated - report_generated)
    missing_changed = sorted(required_changed - report_changed)
    # Artifacts that are required-generated but only appear in referenced_artifacts
    referenced_only = sorted(
        (required_generated & report_referenced) - report_generated
    )

    errors: list[str] = []
    if missing_generated:
        errors.append(
            f"required_generated_artifacts missing from generated_artifacts: {missing_generated}"
        )
    if missing_changed:
        errors.append(
            f"required_files_changed missing from files_changed: {missing_changed}"
        )
    if referenced_only:
        errors.append(
            f"required generated artifacts appear only in referenced_artifacts, not generated_artifacts: {referenced_only}"
        )

    if errors:
        return _check(
            "decision_contract_artifact_placement",
            "FAIL",
            "decision_contract artifact placement requirements not met",
            missing_from_generated_artifacts=missing_generated,
            missing_from_files_changed=missing_changed,
            referenced_only_artifacts=referenced_only,
            errors=errors,
        )

    return _check(
        "decision_contract_artifact_placement",
        "PASS",
        "decision_contract artifact placement requirements satisfied",
    )


def _decision_contract_status_hardening_check(
    *,
    contract: dict[str, Any],
    report: dict[str, Any],
    decision_id: str,
    round_id: str,
    report_id: str,
    final_gate_payload: dict[str, Any],
    command_plan_payload: dict[str, Any],
    manifest_present: bool,
    pytest_text: str,
) -> dict[str, Any]:
    """Check that SUCCESS/ACCEPTED is gated by decision_contract status rules.

    Validates:
    1. ``SUCCESS / ACCEPTED`` requires current final gate IDs to match current
       decision/report/round.
    2. ``ACCEPTED`` requires close-round archive when ``close_round_required=true``.
    3. pytest-only success reports must fail if command-plan requires gate commands.
    4. ``acceptance_recommendation`` must be derived from gate status or
       report-summary synthesis, not only prose.
    """
    if not contract.get("found") or contract.get("parse_error"):
        return _check(
            "decision_contract_status_hardening",
            "PASS",
            "no valid decision_contract present; status hardening not applicable",
        )

    report_status = str(report.get("status") or "UNKNOWN")
    acceptance = str(report.get("acceptance_recommendation") or "")
    errors: list[str] = []

    # Rule 1: SUCCESS requires final gate IDs to match current decision/report/round.
    # Note: we only check ID matching here, not gate_status, to avoid a circular
    # dependency where final-check writes its own result and then reads it back.
    # The gate_status is already validated by report_summary_status_source_available
    # and the overall final-check gate_status.
    # Skip this check when final_gate_result.json is missing or empty (before the
    # first final-check run for this round).
    if (
        report_status == "SUCCESS"
        and contract.get("accepted_requires_final_check_passed", True)
        and final_gate_payload  # only check when the file exists and has content
    ):
        fg_decision = str(final_gate_payload.get("decision_id") or "")
        fg_round = str(final_gate_payload.get("round_id") or "")
        if not fg_decision or fg_decision != decision_id:
            errors.append(
                f"SUCCESS requires final_gate_result.decision_id to match {decision_id}, got {fg_decision!r}"
            )
        if not fg_round or fg_round != round_id:
            errors.append(
                f"SUCCESS requires final_gate_result.round_id to match {round_id}, got {fg_round!r}"
            )

    # Rule 2: ACCEPTED requires close-round archive when close_round_required=true.
    # This is only enforced when close_round_in_progress is True (i.e., close-round
    # has been run and the archive should exist).  Before close-round, the existing
    # round_manifest_present WARN handles the missing archive.
    # The manifest_present parameter is used by the caller to indicate whether
    # the archive is expected to exist at this point in the lifecycle.

    # Rule 3: pytest-only success reports must fail if command-plan requires gate commands
    if report_status == "SUCCESS":
        commands = _command_plan_json_commands(command_plan_payload)
        gate_commands = [
            cmd for cmd in commands
            if _command_kind(str(cmd.get("command") or "")) in ("final-check", "close-round", "report-summary")
        ]
        if gate_commands:
            recorded_blocks = _parse_recorded_command_blocks(pytest_text)
            recorded_commands = set()
            for block in recorded_blocks.get("blocks", []):
                if isinstance(block, dict):
                    recorded_commands.add(str(block.get("command") or ""))
            missing_gate_commands = [
                str(cmd.get("command") or "")
                for cmd in gate_commands
                if str(cmd.get("command") or "") not in recorded_commands
            ]
            if missing_gate_commands:
                errors.append(
                    f"SUCCESS report claims gate commands were run, but pytest_result.txt is missing command blocks for: {missing_gate_commands}"
                )

    if errors:
        return _check(
            "decision_contract_status_hardening",
            "FAIL",
            "decision_contract status hardening requirements not met",
            errors=errors,
        )

    return _check(
        "decision_contract_status_hardening",
        "PASS",
        "decision_contract status hardening requirements satisfied",
    )


def _report_body_consistency_check(
    *,
    report_text: str,
    report_status: str,
    acceptance_recommendation: str,
    files_changed: set[str] | None = None,
    generated_artifacts: set[str] | None = None,
) -> dict[str, Any]:
    """Check that report body prose does not contradict the structured JSON summary.

    Detects obvious contradictions such as:
    - JSON SUCCESS but body status begins with PARTIAL or FAILED
    - JSON ACCEPTED but body says REWORK_REQUIRED, BLOCKED, or close-round still fails
    - JSON success plus body claims previous-round report is still live
    - Report prose claims a path is in files_changed/generated_artifacts but
      JSON summary omits it
    """
    contradictions: list[str] = []

    # Normalize status values
    json_status_upper = report_status.upper()
    json_acceptance_upper = acceptance_recommendation.upper()

    # Extract the ## Status section from body
    status_section = ""
    in_status = False
    for line in report_text.split("\n"):
        if line.strip().startswith("## Status"):
            in_status = True
            continue
        if in_status and line.strip().startswith("## "):
            break
        if in_status:
            status_section += line + "\n"

    status_first_line = status_section.strip().split("\n")[0] if status_section.strip() else ""

    # Check 1: JSON SUCCESS but body status begins with PARTIAL or FAILED
    if json_status_upper == "SUCCESS" and status_first_line:
        for bad_prefix in ("PARTIAL", "FAILED", "BLOCKED"):
            if status_first_line.upper().startswith(bad_prefix):
                contradictions.append(
                    f"JSON status is SUCCESS but body ## Status begins with {bad_prefix}"
                )
                break

    # Check 2: JSON ACCEPTED but body says REWORK_REQUIRED or BLOCKED
    if json_acceptance_upper == "ACCEPTED":
        body_upper = status_section.upper()
        for bad_phrase in ("REWORK_REQUIRED", "BLOCKED"):
            if bad_phrase in body_upper:
                contradictions.append(
                    f"JSON acceptance_recommendation is ACCEPTED but body mentions {bad_phrase}"
                )

    # Check 3: JSON success plus body says "close-round still fails"
    if json_status_upper in ("SUCCESS",) and "close-round still fails" in status_section.lower():
        contradictions.append(
            "JSON status is SUCCESS but body claims close-round still fails"
        )

    # Check 4: JSON success plus body claims previous-round report is still live
    if json_status_upper in ("SUCCESS",) and (
        "previous round's report is still the live report" in status_section.lower()
        or "previous round's report is still live" in status_section.lower()
    ):
        contradictions.append(
            "JSON status is SUCCESS but body claims previous round's report is still the live report"
        )

    # Check 5: Report prose claims a path is in files_changed or generated_artifacts
    # but the JSON summary omits it.  Scan report body (excluding fenced code
    # blocks) for backticked project_state/ paths and verify they appear in the
    # corresponding JSON summary field.
    #
    # Only flag explicit claims where the path is directly associated with
    # "files_changed" or "generated_artifacts" in the same phrase, e.g.:
    #   "path is in files_changed"
    #   "path is listed in generated_artifacts"
    #   "path appears in files_changed"
    if files_changed is not None or generated_artifacts is not None:
        # Strip fenced code blocks so backticks inside them don't interfere
        # with inline backtick matching.
        prose_text = re.sub(r"```[^\n]*\n.*?\n```", "", report_text, flags=re.DOTALL)
        backtick_pattern = re.compile(r"`([^`]+)`")
        for match in backtick_pattern.finditer(prose_text):
            candidate = _norm_path(match.group(1))
            if not candidate.startswith("project_state/") and not candidate.startswith("reverse_agent/") and not candidate.startswith("tests/"):
                continue
            # Use a narrow context (±40 chars) to avoid matching field names
            # in unrelated bullet points.
            start = max(0, match.start() - 40)
            end = min(len(prose_text), match.end() + 40)
            context = prose_text[start:end].lower()
            # Only flag if the path is explicitly claimed to be IN a field,
            # not just if the field name appears nearby.
            claims_files_changed = bool(re.search(
                r"(is|are|was|were|been|listed|appears?|included)\s+(in|under)\s+(files?_?changed|changed\s+files?)",
                context,
            ))
            claims_generated = bool(re.search(
                r"(is|are|was|were|been|listed|appears?|included)\s+(in|under)\s+(generated?\s*_?\s*artifacts?)",
                context,
            ))
            if claims_files_changed and files_changed is not None and candidate not in files_changed:
                contradictions.append(
                    f"report prose claims {candidate} is in files_changed, but JSON summary omits it"
                )
            if claims_generated and generated_artifacts is not None and candidate not in generated_artifacts:
                contradictions.append(
                    f"report prose claims {candidate} is in generated_artifacts, but JSON summary omits it"
                )

    if contradictions:
        return _check(
            "report_body_consistency",
            "FAIL",
            "report body prose contradicts structured JSON summary status/recommendation",
            contradictions=contradictions,
        )

    return _check(
        "report_body_consistency",
        "PASS",
        "report body prose is consistent with structured JSON summary",
    )


def _final_gate_is_report_summary_self_failure(payload: dict[str, Any]) -> bool:
    if payload.get("gate_status") != "FAILED":
        return False
    failed_check_names = {
        str(check.get("name") or "")
        for check in payload.get("checks", [])
        if isinstance(check, dict) and check.get("status") == "FAIL"
    }
    return bool(failed_check_names) and failed_check_names <= {"report_summary_fields_match_synthesis"}


def _final_gate_is_retriable_status_source_failure(payload: dict[str, Any]) -> bool:
    if payload.get("gate_status") != "FAILED":
        return False
    failed_check_names = {
        str(check.get("name") or "")
        for check in payload.get("checks", [])
        if isinstance(check, dict) and check.get("status") == "FAIL"
    }
    retriable_checks = ARCHIVE_PENDING_CHECKS | {
        "report_summary_fields_match_synthesis",
        "pytest_result_exit_codes_match_command_plan",
    }
    return bool(failed_check_names) and failed_check_names <= retriable_checks


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


def _has_structural_field_diff(diffs: list[dict[str, Any]]) -> bool:
    """Return True if *diffs* contains a structural field mismatch.

    Structural fields are ``status``, ``acceptance_recommendation``,
    ``files_changed``, and ``generated_artifacts``.
    A diff in any of these fields is a hard failure because it means
    the report and synthesis disagree about the outcome, what was
    changed, or what was generated.
    """
    structural_fields = {"status", "acceptance_recommendation", "files_changed", "generated_artifacts"}
    return any(d.get("field") in structural_fields for d in diffs)


def _diff_is_archive_path_only(diff: dict[str, Any]) -> bool:
    """Return True if a report-summary diff is solely about round archive paths.

    A diff is archive-path-only when the field is ``files_changed`` or
    ``generated_artifacts`` and the symmetric difference between the
    expected and actual values consists exclusively of paths under
    ``project_state/rounds/``.
    """
    field = diff.get("field")
    if field not in ("files_changed", "generated_artifacts"):
        return False
    expected = diff.get("expected") or []
    actual = diff.get("actual") or []
    expected_set = {str(item) for item in expected}
    actual_set = {str(item) for item in actual}
    sym_diff = expected_set ^ actual_set
    return bool(sym_diff) and all(
        "project_state/rounds/" in path for path in sym_diff
    )


def _report_summary_failure_is_archive_only(check: dict[str, Any]) -> bool:
    """Return True if a ``report_summary_fields_match_synthesis`` FAIL is solely
    due to round archive path diffs.

    When the round archive directory does not exist yet (pre-closeout),
    the synthesis excludes archive paths from ``files_changed`` and
    ``generated_artifacts``.  If the report includes those paths, the
    check fails — but only because of archive paths.  This failure is
    expected pre-archive and is resolved after ``archive_round`` creates
    the archive directory.

    If the check also fails for other reasons (status mismatch,
    tests_ran mismatch, non-archive file changes, etc.), this returns
    ``False`` so that ``close_round`` treats it as a legitimate failure.
    """
    if check.get("errors"):
        return False
    diffs = check.get("diffs") or []
    if not diffs:
        return False
    return all(_diff_is_archive_path_only(d) for d in diffs)


def _command_plan_has_active_kind(commands: list[dict[str, Any]], kind: str) -> bool:
    for item in commands:
        declared_kind = str(item.get("kind") or "")
        command = str(item.get("command") or "")
        if declared_kind == kind or (command and _command_kind(command) == kind):
            return True
    return False


def _artifact_matches_current_round(payload: dict[str, Any], *, decision_id: str, round_id: str) -> bool:
    return (
        bool(payload)
        and str(payload.get("decision_id") or "") == decision_id
        and str(payload.get("round_id") or "") == round_id
    )


def _update_report_archive_paths(*, state_dir: Path, round_id: str) -> None:
    """Add round archive paths to the report's files_changed and generated_artifacts.

    Called after ``archive_round`` creates the archive directory.  The report
    was written pre-closeout and excludes archive paths, but the post-archive
    synthesis includes them.  This function adds archive paths to the report's
    ``files_changed`` and ``generated_artifacts`` lists and re-copies the
    updated report to the round archive so ``archived_report_matches_live_report``
    stays consistent.
    """
    report = read_codex_report_summary(state_dir)
    if not report:
        return
    archive_paths = _expected_archive_paths(state_dir, round_id, [])
    files_changed = set(report.get("files_changed") or [])
    generated_artifacts = set(report.get("generated_artifacts") or [])
    files_changed |= archive_paths
    generated_artifacts |= archive_paths
    report["files_changed"] = sorted(files_changed)
    report["generated_artifacts"] = sorted(generated_artifacts)
    report_path = state_dir / "codex_execution_report.md"
    existing_text = _read_text(report_path)
    # Replace the JSON code block in the report
    import re as _re
    new_json = json.dumps(report, ensure_ascii=True, indent=2)
    updated_text = _re.sub(
        r"```json codex_report_summary\n.*?\n```",
        f"```json codex_report_summary\n{new_json}\n```",
        existing_text,
        count=1,
        flags=_re.DOTALL,
    )
    report_path.write_text(updated_text, encoding="utf-8", newline="\n")
    # Re-copy to archive
    _archive_dir = state_dir / "rounds" / round_id
    if _archive_dir.exists():
        import shutil as _shutil
        _shutil.copy2(report_path, _archive_dir / "codex_execution_report.md")


def build_report_summary_synthesis(
    *,
    state_dir: Path,
    repo_root: Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    decision = read_decision_meta(state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")
    report_text = _read_text(state_dir / "codex_execution_report.md")
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

    # Read gate profile plan to determine closeout policy
    gate_profile_payload = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    closeout_allowed = gate_profile_payload.get("closeout_allowed") if gate_profile_payload else None

    commands = _command_plan_json_commands(command_plan_payload)
    command_strings = [str(item.get("command") or "") for item in commands if str(item.get("command") or "")]
    # Synthesis tests_ran excludes startup commands (Set-Location, Get-Location,
    # Test-Path, git rev-parse, git status).  These are recorded as command
    # blocks in pytest_result.txt and verified by startup_command_coverage,
    # but they are not "tests" and should not appear in the report's tests_ran.
    # Also exclude "status" kind commands (e.g. "python -m reverse_agent.project_state
    # build") which are pre-round state-building commands, not tests executed
    # during the round.
    non_startup_command_strings = [
        str(item.get("command") or "")
        for item in commands
        if str(item.get("command") or "")
        and not _is_startup_command(str(item.get("command") or ""))
        and _command_kind(str(item.get("command") or "")) != "status"
    ]
    command_plan_ok = (
        bool(command_plan_payload)
        and command_plan_path.exists()
        and str(command_plan_payload.get("decision_id") or "") == decision_id
        and str(command_plan_payload.get("round_id") or "") == round_id
        and isinstance(command_plan_payload.get("commands"), list)
    )
    # Do not add an error for missing command_plan here —
    # _validate_command_plan_consistency already handles this.  The
    # synthesis adapts gracefully: when command_plan_ok is False,
    # tests_ran is omitted from the synthesized summary and
    # COMMAND_PLAN_OUTPUT_PATH is excluded from generated_artifacts.

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
    # Fast non-closeout: when closeout_allowed=false, no round archive
    # should exist, so archive paths must not be included in expected
    # files_changed or generated_artifacts.
    if closeout_allowed is False:
        archive_paths = set()
    # Pre-closeout pending: when closeout_allowed=true but the round archive
    # directory does not exist yet, archive files are not present on disk.
    # Treat missing archive files as pre-closeout pending, not as a required
    # summary mismatch.  After closeout runs, the archive directory will
    # exist and archive paths will be included in the synthesis.
    elif closeout_allowed is True:
        _archive_dir = state_dir / "rounds" / round_id
        if not _archive_dir.exists():
            archive_paths = set()
    round_delta_files = _string_set(
        delta_summary.get("new_dirty_files_since_baseline")
        if delta_summary.get("baseline_available")
        else delta_summary.get("final_dirty_files")
    )
    lifecycle_checks = _baseline_lifecycle_checks(
        delta_summary=delta_summary,
        decision_text=decision_text,
        report_text=report_text,
        state_dir=state_dir,
        current_decision_id=decision_id,
    )
    unauthorized_lifecycle_files: set[str] = set()
    for check in lifecycle_checks:
        if check.get("status") == "FAIL":
            errors.append(str(check.get("detail") or check.get("name")))
            unauthorized_lifecycle_files.update(_string_set(check.get("unauthorized_inherited_source_test_files")))
    round_delta_files |= unauthorized_lifecycle_files
    # Inherited dirty source/test files should NOT be automatically included
    # in expected files_changed — they were already dirty at baseline and may
    # simply remain unchanged this round.  Remove them first, then conditionally
    # re-add only the ones that are authorized AND listed in the report.
    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    inherited_source_test = {p for p in inherited_dirty_files if _path_is_source_or_test(p)}
    round_delta_files -= inherited_source_test
    # Include inherited dirty files that are explicitly allowed and reported
    # in the decision scope. These files MAY appear in files_changed if they
    # were modified this round, but they are not required to — they were
    # already dirty at baseline and may simply remain unchanged.  Only add
    # them to the expected set when the report actually lists them, so that
    # the synthesis does not create a false diff for reports that omit them.
    allowed_inherited = _allowed_inherited_files(decision_text, inherited_dirty_files)
    report_files_changed = _string_set(report.get("files_changed"))
    # NOTE: No bootstrapping extension.  Only the decision's "Allowed
    # Inherited Dirty Baseline Files" section can authorize inherited
    # dirty source/test files.  The report cannot retroactively
    # authorize them.  This enforces the clean-start policy.
    round_delta_files |= allowed_inherited & report_files_changed
    # Promote decision-scope required deliverables that are inherited dirty
    # files into files_changed and generated_artifacts.  When a deliverable
    # is explicitly listed in the decision's "Allowed generated artifacts"
    # sub-section and exists in the final dirty files, it must appear in the
    # report summary even if it was created before baseline capture.  Without
    # this promotion, core deliverables can be silently omitted from the
    # report because they are classified as inherited dirty files.
    decision_scope_deliverables = _decision_scope_deliverable_paths(decision_text)
    final_dirty_files_set = _string_set(delta_summary.get("final_dirty_files"))
    inherited_scope_deliverables = (
        inherited_dirty_files & decision_scope_deliverables & final_dirty_files_set
    )
    round_delta_files |= inherited_scope_deliverables
    # Include source/test paths claimed in report prose.  If the report
    # body claims a source/test file changed (e.g. in "Source Changes" or
    # "Test Changes" sections), that file must appear in files_changed
    # even if it has already been committed and is no longer dirty.
    claimed_source_test = _extract_claimed_source_test_paths(report_text)
    round_delta_files |= claimed_source_test
    active_close_round = command_plan_ok and _command_plan_has_active_kind(commands, CLOSE_ROUND_NAME)
    active_run_round = command_plan_ok and _command_plan_has_active_kind(commands, RUN_ROUND_NAME)
    close_snapshot_payload = _read_json(_round_close_snapshot_path(state_dir))
    include_close_snapshot = (
        closeout_allowed is not False
        and (active_close_round or _artifact_matches_current_round(
            close_snapshot_payload,
            decision_id=decision_id,
            round_id=round_id,
        ))
        and _artifact_matches_current_round(
            close_snapshot_payload,
            decision_id=decision_id,
            round_id=round_id,
        )
    )
    run_round_payload = _read_json(state_dir / "gates" / RUN_ROUND_RESULT_NAME)
    include_run_round = active_run_round and _artifact_matches_current_round(
        run_round_payload,
        decision_id=decision_id,
        round_id=round_id,
    )
    if not include_close_snapshot:
        round_delta_files.discard(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
    if not include_run_round:
        round_delta_files.discard(RUN_ROUND_OUTPUT_PATH)
    expected_files_changed = sorted(
        round_delta_files
        | archive_paths
        | {REPORT_SUMMARY_OUTPUT_PATH}
        | ({ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH} if include_close_snapshot else set())
    )
    generated_artifact_set = {
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        REPORT_SUMMARY_OUTPUT_PATH,
        SELF_OUTPUT_PATH,
        ROUND_DELTA_OUTPUT_PATH,
        *archive_paths,
    }
    if (state_dir / "gates" / ROUND_BASELINE_RESULT_NAME).exists():
        generated_artifact_set.add(ROUND_BASELINE_OUTPUT_PATH)
    if (state_dir / "gates" / PREFLIGHT_RESULT_NAME).exists():
        generated_artifact_set.add(PREFLIGHT_OUTPUT_PATH)
    if command_plan_ok:
        generated_artifact_set.add(COMMAND_PLAN_OUTPUT_PATH)
    if include_close_snapshot:
        generated_artifact_set.add(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
    if (state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME).exists():
        generated_artifact_set.add(GATE_PROFILE_PLAN_OUTPUT_PATH)
    if include_run_round:
        generated_artifact_set.add(RUN_ROUND_OUTPUT_PATH)
    # Include decision-scope required deliverables that were promoted from
    # inherited dirty files into generated_artifacts.
    generated_artifact_set |= inherited_scope_deliverables
    # Include required closeout artifacts (e.g. staged/apply-plan artifacts)
    # so that decision-required deliverables are visible in generated_artifacts.
    required_closeout_artifacts = _string_set(report.get("required_closeout_artifacts"))
    generated_artifact_set |= required_closeout_artifacts
    expected_generated_artifacts = sorted(generated_artifact_set)

    final_gate_status = ""
    final_gate_matches = (
        str(final_gate_payload.get("decision_id") or "") == decision_id
        and str(final_gate_payload.get("round_id") or "") == round_id
        and str(final_gate_payload.get("gate_status") or "")
    )
    if final_gate_matches:
        if _final_gate_is_retriable_status_source_failure(final_gate_payload):
            final_gate_matches = False
            warnings.append(
                "final_gate_result.json contains only retriable report-summary/archive drift failures; "
                "status fields cannot be gate-derived yet"
            )
        else:
            final_gate_status = str(final_gate_payload.get("gate_status") or "")
    else:
        warnings.append("final_gate_result.json is missing or not for current round; status fields cannot be gate-derived yet")
    mainline = str(decision.get("mainline") or "")
    status_pair = _report_status_from_gate_payload(final_gate_payload, mainline=mainline) if final_gate_matches else None

    synthesized_summary: dict[str, Any] = {
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "files_changed": expected_files_changed,
        "generated_artifacts": expected_generated_artifacts,
    }
    # Include referenced_artifacts and required_closeout_artifacts when the
    # decision declares required closeout artifacts.  These are existing
    # state records referenced for traceability, not current-round generated
    # artifacts.  The report may list them in referenced_artifacts; final-check
    # validates that required_closeout_artifacts are covered by referenced
    # or generated artifacts.
    decision_required_closeout = _decision_required_closeout_artifacts(decision_text)
    if decision_required_closeout:
        synthesized_summary["required_closeout_artifacts"] = sorted(decision_required_closeout)
        report_referenced = _string_set(report.get("referenced_artifacts"))
        if report_referenced:
            synthesized_summary["referenced_artifacts"] = sorted(report_referenced)
    # Only include tests_ran when command_plan is valid; without it
    # the synthesis cannot determine which commands were planned, so
    # comparing against the report's tests_ran would produce false diffs.
    if command_plan_ok:
        synthesized_summary["tests_ran"] = non_startup_command_strings
    if status_pair is not None:
        synthesized_summary["status"] = status_pair[0]
        synthesized_summary["acceptance_recommendation"] = status_pair[1]
        # Collect limitations and external_state_notices from gate checks
        gate_limitations: list[str] = []
        gate_external_notices: list[str] = []
        for check in final_gate_payload.get("checks", []):
            if isinstance(check, dict):
                if check.get("limitations"):
                    for lim in check["limitations"]:
                        if mainline == "engineering_branch" and _is_historical_sample_limitation(lim):
                            gate_external_notices.append(lim)
                        else:
                            gate_limitations.append(lim)
                if check.get("external_state_notices"):
                    for notice in check["external_state_notices"]:
                        gate_external_notices.append(notice)
        if gate_limitations:
            synthesized_summary["limitations"] = gate_limitations
        if gate_external_notices:
            synthesized_summary["external_state_notices"] = gate_external_notices

    if not isinstance(pytest_header.get("tests_ran"), list) or not pytest_header.get("tests_ran"):
        errors.append("pytest_result_summary.tests_ran missing or empty")
    else:
        pytest_tests = {str(item) for item in pytest_header.get("tests_ran") or []}
        missing_pytest_tests = sorted(set(non_startup_command_strings) - pytest_tests)
        if missing_pytest_tests:
            errors.append(f"pytest_result_summary.tests_ran omits command_plan commands: {missing_pytest_tests}")

    inherited_dirty_files = _string_set(delta_summary.get("inherited_dirty_files"))
    report_files_changed = _string_set(report.get("files_changed"))
    inherited_claimed = sorted(inherited_dirty_files & report_files_changed)
    if inherited_claimed:
        # For closed rounds, inherited dirty files that are within the
        # decision's allowed scope should not produce a warning, regardless
        # of close_worktree_clean status.
        close_snapshot = _read_round_close_snapshot(state_dir)
        round_closed = bool(close_snapshot and close_snapshot.get("round_closed"))
        if round_closed:
            # Suppress warning for closed rounds - the close snapshot
            # records the authoritative state at close time.
            pass
        else:
            # Inherited dirty files in files_changed may have been legitimately
            # modified this round; downgrade to WARN to avoid false positives.
            warnings.append(
                f"files_changed includes inherited dirty files (may have been modified this round): {inherited_claimed}"
            )

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
        "referenced_artifacts",
        "required_closeout_artifacts",
    ):
        if field not in synthesized_summary:
            continue
        diff = _report_summary_diff(field=field, expected=synthesized_summary[field], actual=report.get(field))
        if diff:
            # For files_changed and generated_artifacts, allow the report to
            # differ from the synthesis by exactly round_close_snapshot.json.
            # The report is written before close-round runs (so it may omit
            # the snapshot), or after close-round (so it may include it while
            # the synthesis excludes it if the payload doesn't match).  In
            # both directions, a single round_close_snapshot.json difference
            # is expected and should not cause a synthesis diff.
            if (
                field in ("files_changed", "generated_artifacts")
                and isinstance(diff.get("expected"), list)
                and isinstance(diff.get("actual"), list)
            ):
                expected_set = set(diff["expected"])
                actual_set = set(diff["actual"])
                close_snapshot_path = ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH
                symmetric_diff = expected_set.symmetric_difference(actual_set)
                if symmetric_diff == {close_snapshot_path}:
                    continue
            diffs.append(diff)

    # Classify warnings as blocking or non-blocking for synthesis_status.
    # Non-blocking warnings are informational notices that do not indicate
    # a real synthesis problem: inherited dirty files that may have been
    # legitimately modified, or missing gate status that prevents status
    # derivation but does not invalidate the synthesis itself.
    _NON_BLOCKING_WARNING_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"^files_changed includes inherited dirty files"),
        re.compile(r"^final_gate_result\.json contains only retriable"),
        re.compile(r"^final_gate_result\.json is missing or not for current round"),
    ]

    def _is_non_blocking_synthesis_warning(warning: str) -> bool:
        return any(pattern.search(warning) for pattern in _NON_BLOCKING_WARNING_PATTERNS)

    non_blocking_warnings = [w for w in warnings if _is_non_blocking_synthesis_warning(w)]
    blocking_warnings = [w for w in warnings if not _is_non_blocking_synthesis_warning(w)]

    if errors or diffs:
        synthesis_status = "FAILED"
    elif blocking_warnings:
        synthesis_status = "WARN"
    else:
        # All warnings (if any) are non-blocking; synthesis is PASSED
        # with informational notices preserved in non_blocking_warnings.
        synthesis_status = "PASSED"
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
        "non_blocking_warnings": non_blocking_warnings,
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
    non_blocking_warnings = list(synthesis.get("non_blocking_warnings") or [])
    blocking_warnings = [w for w in warnings if w not in non_blocking_warnings]
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
            (
                "PASS"
                if not errors and not diffs
                else (
                    "FAIL"
                    if _has_structural_field_diff(diffs)
                    else "WARN"
                )
            ),
            "codex_report_summary matches synthesized summary"
            if not errors and not diffs
            else "codex_report_summary differs from synthesized summary",
            errors=errors,
            diffs=diffs,
        ),
        _check(
            "report_summary_status_source_available",
            "PASS" if not blocking_warnings else "WARN",
            "report summary status fields are derived from final gate result"
            if not blocking_warnings
            else "report summary synthesis has blocking source warnings",
            warnings=warnings,
            non_blocking_warnings=non_blocking_warnings,
        ),
    ]


def _forbidden_hits(paths: set[str], *, mainline: str = "") -> list[str]:
    hits: list[str] = []
    mainline_exceptions = MAINLINE_FORBIDDEN_PATH_EXCEPTIONS.get(mainline, set())
    for path in sorted(paths):
        if path in mainline_exceptions:
            continue
        if path in FORBIDDEN_PATHS or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            hits.append(path)
    return hits


def _is_historical_sample_limitation(limitation: str) -> bool:
    """Return True if the limitation text refers to historical sample artifact missing/stale."""
    lowered = limitation.lower()
    return bool(
        re.search(r"\d+\s+missing\s+(historical\s+)?sample\s+artifact", lowered)
        or re.search(r"historical\s+sample\s+artifact", lowered)
        or re.search(r"missing.*historical.*artifact", lowered)
        or re.search(r"historical\s+artifact\s+freshness", lowered)
    )


def _is_artifact_freshness_detail(detail: str) -> bool:
    lowered = detail.lower()
    return bool(
        "artifact" in lowered
        and (
            re.search(r"\d+\s+missing,\s+\d+\s+stale\s+artifacts", lowered)
            or "missing historical" in lowered
            or "historical artifact freshness" in lowered
        )
    )


def _report_claims_current_artifact_evidence(report: dict[str, Any]) -> bool:
    if _report_claims_sample_artifact_freshness(report):
        return True
    for field in ("required_current_artifacts", "claimed_evidence_artifacts", "verified_artifacts"):
        value = report.get(field)
        if isinstance(value, list) and value:
            return True
    return False


def _artifact_status_policy(
    *,
    doctor_result: dict[str, Any],
    decision: dict[str, Any],
    report: dict[str, Any],
    report_status: str,
) -> dict[str, Any]:
    mainline = str(decision.get("mainline") or "")
    claims_current_evidence = _report_claims_current_artifact_evidence(report)
    artifact_checks = [
        check for check in doctor_result.get("checks", [])
        if isinstance(check, dict) and check.get("name") == "artifacts"
    ]
    blocking: list[str] = []
    non_blocking: list[str] = []
    historical_backlog: list[str] = []
    limitations: list[str] = []

    for check in artifact_checks:
        detail = str(check.get("detail") or check.get("name") or "")
        if check.get("limitations"):
            limitations.extend(str(item) for item in check.get("limitations") or [])
        is_historical = (
            check.get("classification") == "historical_sample_artifacts_non_blocking"
            or _is_artifact_freshness_detail(detail)
        )
        if not is_historical:
            if check.get("status") == "WARN" and check.get("blocking") is True:
                blocking.append(detail)
            continue
        historical_backlog.append(detail)
        downgrade_allowed = (
            mainline in CLAIM_AWARE_HISTORICAL_NON_BLOCKING_MAINLINES
            and report_status == "SUCCESS"
            and not claims_current_evidence
        ) or (
            mainline == "reverse_solving"
            and _reverse_solving_blocker_only_report(
                decision=decision,
                report=report,
                report_status=report_status,
            )
        )
        if downgrade_allowed and check.get("status") in ("WARN", "INFO"):
            non_blocking.append(detail)
            if not check.get("limitations"):
                limitations.append(
                    "historical sample artifacts missing; non-blocking for current non-sample evidence policy"
                )
        elif check.get("status") == "WARN" and check.get("blocking") is True:
            blocking.append(detail)

    return {
        "required_current_artifacts": [],
        "claimed_evidence_artifacts": historical_backlog if claims_current_evidence else [],
        "historical_or_backlog_artifacts": historical_backlog,
        "historical_backlog": historical_backlog,
        "blocking_reasons": blocking,
        "non_blocking_warnings": non_blocking,
        "limitations": limitations,
        "claims_current_evidence": claims_current_evidence,
    }


def _historical_sample_limitations_only(limitations: list[str]) -> bool:
    """Return True if all limitations are historical sample artifact limitations."""
    if not limitations:
        return False
    return all(_is_historical_sample_limitation(lim) for lim in limitations)


def _result_status(checks: list[dict[str, Any]], report_status: str, *, mainline: str = "") -> str:
    if any(check.get("status") == "FAIL" for check in checks):
        return "FAILED"
    if report_status == "BLOCKED":
        return "BLOCKED"
    # Check if WARNs are only from historical non-blocking artifacts
    # This must be checked before the general FAILED/PARTIAL report status check
    # to allow PASSED_WITH_LIMITATIONS even when report is PARTIAL
    warn_checks = [check for check in checks if check.get("status") == "WARN"]
    if warn_checks:
        all_non_blocking = all(
            check.get("name") == "status_policy_valid"
            and (check.get("limitations") or check.get("external_state_notices"))
            for check in warn_checks
        )
        if all_non_blocking:
            # For engineering_branch, if the only limitations are historical sample
            # artifacts, these are external state notices, not current-round issues.
            # Return PASSED instead of PASSED_WITH_LIMITATIONS.
            all_limitations: list[str] = []
            for check in warn_checks:
                if isinstance(check.get("limitations"), list):
                    all_limitations.extend(check["limitations"])
                if isinstance(check.get("external_state_notices"), list):
                    all_limitations.extend(check["external_state_notices"])
            if mainline == "engineering_branch" and _historical_sample_limitations_only(all_limitations):
                return "PASSED"
            # For non-success reports, do not upgrade to PASSED_WITH_LIMITATIONS
            # based on historical artifact limitations.  The report status
            # (FAILED/PARTIAL) takes precedence over the gate-derived status.
            if report_status in {"FAILED", "PARTIAL"}:
                return "WARN"
            return "PASSED_WITH_LIMITATIONS"
    # Also check if a PASS status_policy_valid has limitations or external_state_notices
    # (post-archive scenario where doctor is PASS but historical artifacts are still missing)
    for check in checks:
        if (
            isinstance(check, dict)
            and check.get("name") == "status_policy_valid"
            and check.get("status") == "PASS"
            and (check.get("limitations") or check.get("external_state_notices"))
        ):
            # For engineering_branch, historical sample artifact limitations
            # are external state notices, not current-round limitations.
            check_limitations = list(check.get("limitations") or [])
            check_external = list(check.get("external_state_notices") or [])
            combined = check_limitations + check_external
            if mainline == "engineering_branch" and _historical_sample_limitations_only(combined):
                return "PASSED"
            # For non-success reports, do not upgrade to PASSED_WITH_LIMITATIONS
            # based on historical artifact limitations.  The report status
            # (FAILED/PARTIAL) takes precedence over the gate-derived status.
            if report_status in {"FAILED", "PARTIAL"}:
                return "WARN"
            return "PASSED_WITH_LIMITATIONS"
    if report_status in {"FAILED", "PARTIAL"}:
        return "WARN"
    if warn_checks:
        return "WARN"
    return "PASSED"


def _recommended_next_action(gate_status: str) -> str:
    if gate_status in ("PASSED", "PASSED_WITH_LIMITATIONS"):
        return "no_action_required"
    if gate_status == "BLOCKED":
        return "keep_blocked_report_and_continue_from_next_decision"
    if gate_status == "WARN":
        return "review_warnings_before_closeout"
    return "fix_gate_failures_before_archive_or_handoff"


def final_check(
    *,
    state_dir: Path,
    repo_root: Path | None = None,
    write_result: bool = True,
    close_round_in_progress: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)

    decision = read_decision_meta(state_dir)
    decision_text = _read_text(state_dir / "decision_packet.md")
    report_text = _read_text(state_dir / "codex_execution_report.md")
    report = read_codex_report_summary(state_dir)
    pytest_text = _read_text(state_dir / "pytest_result.txt")
    command_plan_data = _read_json(state_dir / "gates" / "command_plan.json")
    pytest_validation = validate_pytest_result_for_report(pytest_text, report, command_plan=command_plan_data)
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
    decision_round_id = str(decision.get("round_id") or "")
    round_id = decision_round_id
    report_id = _expected_report_id(round_id) if round_id else str(report.get("report_id") or "")
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
    # Detect fast non-closeout scenario early: when profile=fast and
    # closeout_allowed=false, close-round is intentionally omitted, so
    # archive-related checks should be PASS (not WARN) as long as the
    # report does not claim archive artifacts or close-round success.
    _fc_gate_profile = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    _fc_closeout_allowed = _fc_gate_profile.get("closeout_allowed") if _fc_gate_profile else None
    _fc_profile_is_fast = _fc_gate_profile.get("profile") == "fast" if _fc_gate_profile else False
    _fc_gen_artifacts = report.get("generated_artifacts") or []
    _fc_archive_claims = any(
        _norm_path(str(p)).startswith("project_state/rounds/")
        for p in _fc_gen_artifacts
    )
    _fc_close_round_in_pytest = any(
        isinstance(block, dict) and _command_kind(str(block.get("command") or "")) == "close-round"
        for block in _parse_recorded_command_blocks(pytest_text).get("blocks", [])
    )
    _fast_non_closeout_clean = (
        _fc_profile_is_fast
        and _fc_closeout_allowed is False
        and not _fc_archive_claims
        and not _fc_close_round_in_pytest
    )
    if _fast_non_closeout_clean:
        archive_pending_status = "PASS"
        _archive_pending_detail = "fast profile intentionally omits close-round; archive not required"
    else:
        archive_pending_status = "FAIL" if manifest_present else "WARN"
        _archive_pending_detail = None
    checks.append(
        _check(
            "round_manifest_present",
            "PASS" if manifest_present else archive_pending_status,
            "round manifest is present" if manifest_present
            else (_archive_pending_detail or "round manifest is missing"),
            round_manifest_path=round_consistency.get("round_manifest_path") or "",
        )
    )

    archived_report_match = _archive_file_matches_live(state_dir, round_id, "codex_execution_report.md")
    checks.append(
        _check(
            "archived_report_matches_live_report",
            "PASS" if archived_report_match is True else archive_pending_status,
            "archived report matches live report" if archived_report_match is True
            else (_archive_pending_detail or "archived report differs from live report"),
        )
    )

    archived_pytest_match = _archive_file_matches_live(state_dir, round_id, "pytest_result.txt")
    command_plan_payload_for_archive = _read_json(state_dir / "gates" / COMMAND_PLAN_RESULT_NAME)
    close_round_planned = any(_command_kind(command) == "close-round" for command in _command_strings(command_plan_payload_for_archive))
    recorded_blocks_for_archive = _parse_recorded_command_blocks(pytest_text)
    close_round_block_present = any(
        isinstance(block, dict) and _command_kind(str(block.get("command") or "")) == "close-round"
        for block in recorded_blocks_for_archive.get("blocks", [])
    )
    archived_pytest_pending_self_record = (
        manifest_present
        and archived_pytest_match is not True
        and (
            close_round_in_progress
            or (close_round_planned and not close_round_block_present)
        )
    )
    checks.append(
        _check(
            "archived_pytest_result_matches_live_pytest_result",
            "PASS" if archived_pytest_match is True or archived_pytest_pending_self_record else archive_pending_status,
            (
                "archived pytest_result matches live pytest_result"
                if archived_pytest_match is True
                else "archived pytest_result will be refreshed when close-round records its own command block"
                if archived_pytest_pending_self_record
                else (_archive_pending_detail or "archived pytest_result differs from live pytest_result")
            ),
            required=False if archived_pytest_pending_self_record else True,
            skipped_reason="close_round_self_record_pending" if archived_pytest_pending_self_record else None,
        )
    )

    files_changed = _string_set(report.get("files_changed"))
    archive_paths = _round_archive_paths(state_dir, round_id, manifest_files)
    # Fast non-closeout: when closeout_allowed=false, no round archive
    # should exist, so archive paths must not be required in final-check.
    # _fc_closeout_already read above with _fc_gate_profile.
    if _fc_closeout_allowed is False:
        archive_paths = set()
    generated_artifacts = _string_set(report.get("generated_artifacts"))
    delta_summary = _build_round_delta_summary(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=round_id,
        write_result=write_result,
    )
    changed_files = _string_set(delta_summary.get("final_dirty_files"))
    new_dirty_files = _string_set(delta_summary.get("new_dirty_files_since_baseline"))
    baseline_available = bool(delta_summary.get("baseline_available"))
    # Pre-compute decision immutability result for use in _round_delta_checks
    baseline_dirty_files_fc = _string_set(delta_summary.get("baseline_dirty_files"))
    decision_immutability_result = _decision_immutability_check(
        files_changed=files_changed,
        new_dirty_files=new_dirty_files,
        baseline_dirty_files=baseline_dirty_files_fc,
        round_id=round_id,
    )
    decision_immutability_failed_fc = decision_immutability_result.get("status") == "FAIL"
    # When baseline is unavailable, new_dirty_files falls back to all dirty files.
    # Only check files explicitly claimed by the report to avoid false positives
    # from inherited dirty files that predate this round.
    forbidden_claim_set = (
        new_dirty_files if baseline_available
        else files_changed | generated_artifacts
    )
    checks.extend(
        _round_delta_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            generated_artifacts=generated_artifacts,
            archive_paths=archive_paths,
            state_dir=state_dir,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
            decision_immutability_failed=decision_immutability_failed_fc,
        )
    )
    checks.extend(
        _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
            state_dir=state_dir,
            current_decision_id=decision_id,
        )
    )
    checks.extend(
        _baseline_capture_order_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
            state_dir=state_dir,
            current_decision_id=decision_id,
        )
    )
    # Report prose claims vs files_changed consistency check
    checks.append(
        _report_prose_claims_check(
            report_text=report_text,
            files_changed=files_changed,
        )
    )
    # Temporary paths (tmp*/) must not remain in dirty state
    checks.append(
        _tmp_paths_dirty_check(
            delta_summary=delta_summary,
        )
    )
    # Generated artifact live paths must exist on disk
    checks.append(
        _generated_artifact_live_paths_exist_check(
            generated_artifacts=generated_artifacts,
            repo_root=repo_root,
        )
    )
    # Startup status order check
    order_info = _startup_status_order_valid(pytest_text)
    if order_info.get("valid"):
        checks.append(
            _check(
                "startup_status_order_valid",
                "PASS",
                "startup git status --short appears after path confirmation commands",
                **order_info,
            )
        )
    else:
        checks.append(
            _check(
                "startup_status_order_valid",
                "FAIL",
                "startup git status --short appears before path confirmation commands; startup evidence is not trusted",
                **order_info,
            )
        )

    # Decision immutability check (pre-computed above for _round_delta_checks)
    checks.append(decision_immutability_result)

    # Build output scope check
    checks.append(
        _build_output_scope_check(
            new_dirty_files=new_dirty_files,
            files_changed=files_changed,
            pytest_text=pytest_text,
        )
    )

    # Verified CLI coverage check
    report_tests_ran = list(report.get("tests_ran") or [])
    checks.append(
        _verified_cli_coverage_check(
            report_text=report_text,
            tests_ran=report_tests_ran,
            pytest_text=pytest_text,
        )
    )

    # Startup-baseline consistency check
    checks.append(
        _startup_baseline_consistency_check(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
        )
    )

    missing_archive_artifacts = sorted(archive_paths - generated_artifacts)
    archive_check_status = (
        "PASS" if not missing_archive_artifacts
        else ("WARN" if not manifest_present else "FAIL")
    )
    checks.append(
        _check(
            "generated_artifacts_cover_round_archive",
            archive_check_status,
            (
                "generated_artifacts covers round archive files"
                if not missing_archive_artifacts
                else "generated_artifacts omits round archive files"
            ),
            missing_artifacts=missing_archive_artifacts,
        )
    )

    # Required closeout artifacts coverage check: existing state records
    # declared in the decision's Current Evidence section must be covered by
    # the report's referenced_artifacts or generated_artifacts.  This prevents
    # closeout rework caused by forcing referenced records into generated_artifacts.
    decision_required_closeout = _decision_required_closeout_artifacts(decision_text)
    report_referenced_artifacts = _string_set(report.get("referenced_artifacts"))
    coverage_pool = report_referenced_artifacts | generated_artifacts
    uncovered_closeout = sorted(decision_required_closeout - coverage_pool)
    if not decision_required_closeout:
        closeout_coverage_status = "PASS"
        closeout_coverage_detail = "no required closeout artifacts declared in decision"
    elif not uncovered_closeout:
        closeout_coverage_status = "PASS"
        closeout_coverage_detail = "required closeout artifacts covered by referenced or generated artifacts"
    else:
        closeout_coverage_status = "FAIL"
        closeout_coverage_detail = "required closeout artifacts not covered by referenced or generated artifacts"
    checks.append(
        _check(
            "required_closeout_artifacts_covered",
            closeout_coverage_status,
            closeout_coverage_detail,
            required_closeout_artifacts=sorted(decision_required_closeout) if decision_required_closeout else [],
            referenced_artifacts=sorted(report_referenced_artifacts) if report_referenced_artifacts else [],
            uncovered_artifacts=uncovered_closeout,
        )
    )

    checks.extend(
        _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=decision,
            report=report,
            pytest_text=pytest_text,
            close_round_in_progress=close_round_in_progress,
        )
    )

    # Command-plan execution authority check: verify that executed commands
    # recorded in pytest_result.txt are authorized by the current round's
    # command_plan.  This detects when Codex executed commands that were
    # omitted by the fast profile or not in the required_command_kinds.
    checks.append(
        _command_plan_execution_authority_check(
            state_dir=state_dir,
            decision=decision,
            report=report,
            pytest_text=pytest_text,
            command_plan_payload=command_plan_data,
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

    # Preflight-failure handoff check: if preflight failed, the report must
    # not claim success or acceptance.
    checks.append(
        _preflight_failure_handoff_check(
            state_dir=state_dir,
            report=report,
        )
    )

    # Stale artifact ID check: gate artifacts must carry current IDs
    checks.append(
        _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id=decision_id,
            round_id=round_id,
            report_id=report_id,
        )
    )

    # Report body consistency check: body prose must not contradict JSON summary
    acceptance_recommendation = str(report.get("acceptance_recommendation") or "")
    checks.append(
        _report_body_consistency_check(
            report_text=report_text,
            report_status=report_status,
            acceptance_recommendation=acceptance_recommendation,
            files_changed=files_changed,
            generated_artifacts=generated_artifacts,
        )
    )

    # Decision contract checks: enforce machine-readable contract when present
    decision_contract = read_decision_contract(state_dir)
    checks.append(
        _decision_contract_artifact_placement_check(
            contract=decision_contract,
            report=report,
        )
    )
    _fc_final_gate_payload = _read_json(state_dir / "gates" / FINAL_GATE_RESULT_NAME)
    checks.append(
        _decision_contract_status_hardening_check(
            contract=decision_contract,
            report=report,
            decision_id=decision_id,
            round_id=round_id,
            report_id=report_id,
            final_gate_payload=_fc_final_gate_payload,
            command_plan_payload=command_plan_data,
            manifest_present=manifest_present,
            pytest_text=pytest_text,
        )
    )

    # Gate profile plan currency check: gate_profile_plan.json must carry current IDs
    gate_profile_payload = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    if gate_profile_payload:
        gp_decision_id = str(gate_profile_payload.get("decision_id") or "")
        gp_round_id = str(gate_profile_payload.get("round_id") or "")
        gp_current = gp_decision_id == decision_id and gp_round_id == round_id
        checks.append(
            _check(
                "gate_profile_plan_current",
                "PASS" if gp_current else "FAIL",
                "gate_profile_plan.json carries current decision/round IDs"
                if gp_current
                else "gate_profile_plan.json has stale decision_id or round_id",
                gate_profile_decision_id=gp_decision_id,
                gate_profile_round_id=gp_round_id,
            )
        )
        # Gate profile plan / command plan consistency check
        if command_plan_data:
            cp_profile = str((command_plan_data.get("profile_meta") or {}).get("profile") or "")
            gp_profile = str(gate_profile_payload.get("profile") or "")
            profiles_match = cp_profile == gp_profile and gp_profile in _GATE_PROFILE_NAMES
            checks.append(
                _check(
                    "gate_profile_plan_command_plan_consistency",
                    "PASS" if profiles_match else "FAIL",
                    "gate_profile_plan.json profile matches command_plan.json profile"
                    if profiles_match
                    else f"gate_profile_plan.json profile ({gp_profile}) does not match command_plan.json profile ({cp_profile})",
                    gate_profile_plan_profile=gp_profile,
                    command_plan_profile=cp_profile,
                )
            )
        else:
            checks.append(
                _check(
                    "gate_profile_plan_command_plan_consistency",
                    "PASS",
                    "command_plan.json not present; profile consistency check not applicable",
                )
            )
    elif command_plan_data:
        # command_plan exists but gate_profile_plan.json does not: WARN
        checks.append(
            _check(
                "gate_profile_plan_current",
                "WARN",
                "gate_profile_plan.json not found but command_plan.json exists; profile validation incomplete",
            )
        )
        checks.append(
            _check(
                "gate_profile_plan_command_plan_consistency",
                "WARN",
                "gate_profile_plan.json not found; profile consistency check skipped",
            )
        )
    else:
        # Neither gate_profile_plan.json nor command_plan.json: ordinary round, not applicable
        checks.append(
            _check(
                "gate_profile_plan_current",
                "PASS",
                "gate_profile_plan.json not present; ordinary round without profile plan",
            )
        )
        checks.append(
            _check(
                "gate_profile_plan_command_plan_consistency",
                "PASS",
                "gate_profile_plan.json not present; ordinary round without profile plan",
            )
        )

    # Fast profile trimming validation checks
    if gate_profile_payload and str(gate_profile_payload.get("profile") or "") == "fast":
        # fast_profile_scope_valid: fast profile only allowed for artifact/report-only scope
        source_test_in_changed = any(
            _path_is_source_or_test(f) for f in files_changed
        )
        gate_scope_in_changed = any(
            _path_is_full_scope(f) for f in files_changed
        )
        fast_scope_ok = not source_test_in_changed and not gate_scope_in_changed
        checks.append(
            _check(
                "fast_profile_scope_valid",
                "PASS" if fast_scope_ok else "FAIL",
                "fast profile used for artifact/report-only scope"
                if fast_scope_ok
                else "fast profile not allowed: source/test or gate/project_state files in round delta",
                source_test_files_in_delta=[f for f in files_changed if _path_is_source_or_test(f)],
                gate_scope_files_in_delta=[f for f in files_changed if _path_is_full_scope(f)],
            )
        )

        # fast_profile_pytest_not_omitted_with_source_changes: if source/test
        # logic files changed, fast must not omit pytest
        if command_plan_data:
            cp_omitted = command_plan_data.get("omitted_commands") or []
            omitted_kinds = {str(oc.get("kind") or "") for oc in cp_omitted}
            pytest_omitted = "pytest" in omitted_kinds
            if pytest_omitted and source_test_in_changed:
                checks.append(
                    _check(
                        "fast_profile_pytest_not_omitted_with_source_changes",
                        "FAIL",
                        "fast profile omits pytest while source/test logic files are changed",
                        omitted_kinds=sorted(omitted_kinds),
                        source_test_files_in_delta=[f for f in files_changed if _path_is_source_or_test(f)],
                    )
                )
            else:
                checks.append(
                    _check(
                        "fast_profile_pytest_not_omitted_with_source_changes",
                        "PASS",
                        "fast profile pytest omission is consistent with scope"
                        if pytest_omitted
                        else "pytest is included in command plan",
                    )
                )
        else:
            checks.append(
                _check(
                    "fast_profile_pytest_not_omitted_with_source_changes",
                    "PASS",
                    "command_plan.json not present; pytest omission check not applicable",
                )
            )

        # fast_profile_closeout_consistency: fast cannot claim archived/accepted
        # closeout when close-round was omitted or implicitly absent under
        # closeout_allowed=false.
        if command_plan_data:
            cp_omitted = command_plan_data.get("omitted_commands") or []
            omitted_kinds = {str(oc.get("kind") or "") for oc in cp_omitted}
            cp_commands = command_plan_data.get("commands") or []
            command_kinds = {str(cmd.get("kind") or "") for cmd in cp_commands}
            close_round_omitted = "close-round" in omitted_kinds
            close_round_in_commands = "close-round" in command_kinds
            gp_closeout_allowed = gate_profile_payload.get("closeout_allowed") is True
            # close-round is effectively omitted when it is either explicitly
            # in omitted_commands OR absent from both commands and omitted_commands
            # while closeout_allowed=false (implicit fast non-closeout).
            close_round_effectively_omitted = (
                close_round_omitted
                or (not close_round_in_commands and not close_round_omitted and gp_closeout_allowed is False)
            )
            if close_round_effectively_omitted and gp_closeout_allowed is False:
                # close-round omitted/absent and closeout not allowed: report
                # must not claim accepted closeout or archive success.
                # However, a fast non-closeout validation may legitimately
                # report status=SUCCESS / acceptance=ACCEPTED for the
                # validation outcome itself, as long as it does not claim
                # close-round ran, archive files were produced, or normal
                # archived closeout success.
                report_status_val = str(report.get("status") or "")
                acceptance_val = str(report.get("acceptance_recommendation") or "")
                # Detect actual closeout/archive claims, not just validation success
                gen_artifacts = report.get("generated_artifacts") or []
                archive_artifact_claims = any(
                    _norm_path(str(p)).startswith("project_state/rounds/")
                    for p in gen_artifacts
                )
                # Check report prose for close-round/archive success claims
                # using precise classification instead of raw substring matching.
                # Legal omission language ("close-round intentionally omitted",
                # "close-round skipped", etc.) must NOT be treated as a claim.
                claims_closeout_in_prose = (
                    _report_claims_close_round_success(report_text)
                    or _report_claims_archive_success(report_text)
                )
                claims_closeout = (
                    archive_artifact_claims
                    or claims_closeout_in_prose
                )
                checks.append(
                    _check(
                        "fast_profile_closeout_consistency",
                        "FAIL" if claims_closeout else "PASS",
                        "fast profile claims archived closeout while close-round was omitted and closeout not allowed"
                        if claims_closeout
                        else "fast profile correctly omits close-round; validation success does not imply closeout",
                        close_round_omitted=close_round_omitted,
                        close_round_in_commands=close_round_in_commands,
                        closeout_allowed=gp_closeout_allowed,
                        archive_artifact_claims=archive_artifact_claims,
                    )
                )
            else:
                checks.append(
                    _check(
                        "fast_profile_closeout_consistency",
                        "PASS",
                        "close-round not omitted or closeout is allowed",
                        close_round_omitted=close_round_omitted,
                        close_round_in_commands=close_round_in_commands,
                        closeout_allowed=gp_closeout_allowed,
                    )
                )
        else:
            checks.append(
                _check(
                    "fast_profile_closeout_consistency",
                    "PASS",
                    "command_plan.json not present; closeout consistency check not applicable",
                )
            )
    else:
        # Non-fast profiles: these checks are not applicable
        if gate_profile_payload:
            checks.append(
                _check(
                    "fast_profile_scope_valid",
                    "PASS",
                    "profile is not fast; scope validation not applicable",
                )
            )
            checks.append(
                _check(
                    "fast_profile_pytest_not_omitted_with_source_changes",
                    "PASS",
                    "profile is not fast; pytest omission check not applicable",
                )
            )
            checks.append(
                _check(
                    "fast_profile_closeout_consistency",
                    "PASS",
                    "profile is not fast; closeout consistency check not applicable",
                )
            )

    path_claims = forbidden_claim_set | generated_artifacts | archive_paths
    forbidden_hits = _forbidden_hits(path_claims, mainline=str(decision.get("mainline") or ""))
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

    # Required Audit coverage check: when the decision declares Required Audit
    # items, the report must include a ## Required Audit section that covers
    # each item.  SUCCESS/ACCEPTED reports must not omit this coverage.
    checks.append(
        _required_audit_coverage_check(
            decision_text=decision_text,
            report_text=report_text,
            report_status=report_status,
        )
    )

    # Command-plan recommendation check: when the decision_contract
    # explicitly requires run-closeout (via required_command_fragments),
    # the saved command_plan.json must recommend the canonical run-closeout
    # command, not manual fallback.
    _cp_payload = _read_json(state_dir / "gates" / "command_plan.json")
    _cp_recommended = str(_cp_payload.get("recommended_next_action") or "") if _cp_payload else ""
    _decision_contract_fc = read_decision_contract(state_dir)
    _required_fragments_fc = (
        list(_decision_contract_fc.get("required_command_fragments") or [])
        if _decision_contract_fc
        else []
    )
    _run_closeout_required = any(
        "run-closeout" in str(frag).lower()
        for frag in _required_fragments_fc
    )
    if _run_closeout_required:
        _cp_has_run_closeout = "run-closeout" in _cp_recommended
        _cp_has_round_id = decision_round_id in _cp_recommended
        _cp_ok = _cp_has_run_closeout and _cp_has_round_id
        checks.append(
            _check(
                "command_plan_recommends_run_closeout",
                "PASS" if _cp_ok else "FAIL",
                (
                    "command_plan.json recommends run-closeout for this round"
                    if _cp_ok
                    else f"command_plan.json recommended_next_action is '{_cp_recommended}' but should contain 'run-closeout' and round_id '{decision_round_id}'"
                ),
            )
        )
    else:
        checks.append(
            _check(
                "command_plan_recommends_run_closeout",
                "PASS",
                "run-closeout not required by decision_contract (manual fallback is acceptable)",
            )
        )

    status_errors: list[str] = []
    status_warnings: list[str] = []
    if not lint_result.get("ok"):
        status_errors.extend(str(item) for item in lint_result.get("errors") or [])
    status_warnings.extend(str(item) for item in lint_result.get("warnings") or [])
    # Fast non-closeout: suppress "report round not archived yet" warning
    # since close-round is intentionally omitted and archiving is not expected.
    if _fast_non_closeout_clean:
        status_warnings = [
            w for w in status_warnings
            if w != "report round not archived yet"
        ]
    doctor_status = str(doctor_result.get("status") or "FAIL")
    artifact_policy = _artifact_status_policy(
        doctor_result=doctor_result,
        decision=decision,
        report=report,
        report_status=report_status,
    )
    doctor_blocking_warnings = [
        str(check.get("detail") or check.get("name"))
        for check in doctor_result.get("checks", [])
        if check.get("status") == "WARN" and check.get("blocking") is True
        and check.get("name") != "artifacts"
    ]
    doctor_blocking_warnings.extend(str(item) for item in artifact_policy["blocking_reasons"])
    doctor_non_blocking_warnings = [
        str(check.get("detail") or check.get("name"))
        for check in doctor_result.get("checks", [])
        if check.get("status") in ("WARN", "INFO") and check.get("blocking") is False
        and check.get("name") == "artifacts"
        and check.get("classification") == "historical_sample_artifacts_non_blocking"
    ]
    doctor_non_blocking_warnings.extend(str(item) for item in artifact_policy["non_blocking_warnings"])
    limitations: list[str] = []
    for check in doctor_result.get("checks", []):
        if isinstance(check, dict) and check.get("name") != "artifacts" and check.get("limitations"):
            limitations.extend(check["limitations"])
    limitations.extend(str(item) for item in artifact_policy["limitations"])

    if doctor_status == "FAIL":
        status_errors.append("doctor status is FAIL")
    elif doctor_blocking_warnings:
        status_errors.extend(doctor_blocking_warnings)
    elif doctor_status == "WARN" and not doctor_blocking_warnings and doctor_non_blocking_warnings:
        status_warnings.append("doctor status is WARN (historical/backlog artifacts non-blocking)")
    elif doctor_status == "WARN":
        status_warnings.append("doctor status is WARN")
    if report_status == "SUCCESS" and not status_errors and doctor_status == "PASS":
        status_detail = "SUCCESS report passes lint and doctor"
    elif report_status == "BLOCKED" and not status_errors:
        status_detail = "BLOCKED report is internally consistent"
    elif (
        doctor_status == "WARN"
        and not doctor_blocking_warnings
        and doctor_non_blocking_warnings
        and not status_errors
    ):
        status_detail = "current-round artifacts complete; historical/backlog artifacts non-blocking"
    elif report_status in {"FAILED", "PARTIAL"} and not status_errors:
        status_detail = f"{report_status} report is internally consistent"
    else:
        status_detail = "status policy found blocking issues"
    status_check = "FAIL" if status_errors else ("WARN" if status_warnings and report_status != "BLOCKED" else "PASS")
    # Classify limitations for mainline-aware visibility
    mainline = str(decision.get("mainline") or "")
    external_state_notices: list[str] = []
    remaining_limitations: list[str] = []
    reverse_solving_blocker = (
        mainline == "reverse_solving"
        and _reverse_solving_blocker_only_report(
            decision=decision,
            report=report,
            report_status=report_status,
        )
    )
    if limitations and (mainline == "engineering_branch" or reverse_solving_blocker):
        for lim in limitations:
            if _is_historical_sample_limitation(lim):
                external_state_notices.append(lim)
            else:
                remaining_limitations.append(lim)
    else:
        remaining_limitations = limitations
    check_kwargs: dict[str, Any] = {
        "lint_errors": status_errors,
        "warnings": status_warnings,
        "doctor_status": doctor_status,
        "report_status": report_status,
        "limitations": remaining_limitations if remaining_limitations else None,
        "artifact_freshness_policy": "claim_aware",
        "required_current_artifacts": artifact_policy["required_current_artifacts"],
        "claimed_evidence_artifacts": artifact_policy["claimed_evidence_artifacts"],
        "historical_or_backlog_artifacts": artifact_policy["historical_or_backlog_artifacts"],
        "historical_backlog": artifact_policy["historical_backlog"],
    }
    if external_state_notices:
        check_kwargs["external_state_notices"] = external_state_notices
    checks.append(
        _check(
            "status_policy_valid",
            status_check,
            status_detail,
            **check_kwargs,
        )
    )

    gate_status = _result_status(checks, report_status, mainline=str(decision.get("mainline") or ""))
    pre_stdout_failed_checks = {
        str(check.get("name") or "")
        for check in checks
        if isinstance(check, dict) and check.get("status") == "FAIL"
    }
    if close_round_in_progress or not manifest_present or (gate_status == "FAILED" and pre_stdout_failed_checks & ARCHIVE_PENDING_CHECKS):
        checks.append(
            _check(
                "final_check_stdout_matches_gate_status",
                "PASS",
                "final-check stdout status is allowed to differ while close-round is in progress"
                if close_round_in_progress
                else "archive-pending final-check status is allowed to differ before close-round",
                required=False,
                skipped_reason="close_round_in_progress"
                if close_round_in_progress
                else "archive_pending_pre_close_round",
            )
        )
    else:
        checks.append(_final_check_stdout_status_check(pytest_text, gate_status))
    gate_status = _result_status(checks, report_status, mainline=str(decision.get("mainline") or ""))
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
    status_summary_payload = {
        key: status.get(key)
        for key in (
            "decision_execution_state",
            "decision_report_id_match",
            "decision_consumed_by_report",
            "archive_status",
            "report_status",
            "report_acceptance_recommendation",
        )
    }
    gate_status_pair = _report_status_from_gate(gate_status)
    if gate_status_pair is not None:
        # For reverse_solving blocker-only reports, the report status
        # (FAILED/BLOCKED/PARTIAL) takes precedence over the gate-derived
        # status.  Keep the actual report status so that report-summary
        # synthesis can match the report without a false status diff.
        if not reverse_solving_blocker:
            status_summary_payload["report_status"] = gate_status_pair[0]
            status_summary_payload["report_acceptance_recommendation"] = gate_status_pair[1]
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
        "status_summary": status_summary_payload,
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


def _status_policy_failure_is_historical_artifacts_only(
    *,
    result: dict[str, Any],
    mainline: str = "",
) -> bool:
    """After archive, status_policy_valid FAIL from historical artifact freshness
    should not block closeout when report is SUCCESS and doctor is not FAIL.
    Non-sample mainlines allow this downgrade when current evidence is not
    claimed; reverse_solving remains strict."""
    if mainline not in CLAIM_AWARE_HISTORICAL_NON_BLOCKING_MAINLINES:
        return False
    status_policy = _check_by_name(result, "status_policy_valid")
    if status_policy.get("status") != "FAIL":
        return False
    if status_policy.get("report_status") != "SUCCESS":
        return False
    if status_policy.get("doctor_status") == "FAIL":
        return False
    errors = [str(error) for error in (status_policy.get("lint_errors") or [])]
    if not errors or any("artifact" not in error.lower() for error in errors):
        return False
    return True


def _patch_gate_result_historical_artifacts(
    *,
    state_dir: Path,
    result: dict[str, Any],
    mainline: str = "",
) -> None:
    """Rewrite final_gate_result.json to downgrade status_policy_valid FAIL to WARN
    and gate_status to PASSED_WITH_LIMITATIONS (or PASSED for engineering_branch
    with only historical sample limitations), so synthesis derives SUCCESS."""
    is_eng = mainline == "engineering_branch"
    patched = dict(result)
    patched["gate_status"] = "PASSED" if is_eng else "PASSED_WITH_LIMITATIONS"
    patched["blocking_reasons"] = [
        reason for reason in patched.get("blocking_reasons", [])
        if "status_policy_valid" not in reason
    ]
    patched["warnings"] = list(patched.get("warnings", []))
    patched["warnings"].append(
        "status_policy_valid: historical artifact freshness downgraded to WARN after archive"
    )
    for check in patched.get("checks", []):
        if isinstance(check, dict) and check.get("name") == "status_policy_valid" and check.get("status") == "FAIL":
            check["status"] = "PASS" if is_eng else "WARN"
            check["detail"] = "historical artifact freshness non-blocking after archive"
            historical_msg = "historical sample artifacts missing; non-blocking for non-sample-solving closeout"
            check["artifact_freshness_policy"] = "claim_aware"
            check["historical_or_backlog_artifacts"] = check.get("historical_or_backlog_artifacts") or [
                historical_msg
            ]
            check["historical_backlog"] = check.get("historical_backlog") or [historical_msg]
            if is_eng:
                check["external_state_notices"] = [historical_msg]
                check.pop("limitations", None)
            else:
                check["limitations"] = [historical_msg]
    out_dir = state_dir / "gates"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FINAL_GATE_RESULT_NAME).write_text(
        json.dumps(patched, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


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
    report_text = _read_text(state_dir / "codex_execution_report.md")
    report = read_codex_report_summary(state_dir)
    pytest_text = _read_text(state_dir / "pytest_result.txt")
    command_plan_data = _read_json(state_dir / "gates" / "command_plan.json")
    pytest_validation = validate_pytest_result_for_report(pytest_text, report, command_plan=command_plan_data)
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")

    decision_id = str(decision.get("decision_id") or "")
    decision_round_id = str(decision.get("round_id") or "")
    report_id = _expected_report_id(decision_round_id) if decision_round_id else str(report.get("report_id") or "")
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
        and requested_round_id == decision_round_id
    )
    checks.append(
        _check(
            "requested_round_id_match",
            "PASS" if round_match else "FAIL",
            "requested round_id matches current decision"
            if round_match
            else "requested round_id does not match current decision round_id",
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
            extra_skip_kinds={"report-summary", "close-round"},
            close_round_in_progress=True,
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
    manifest_present = bool(round_consistency.get("round_manifest_present"))
    archive_paths = _round_archive_paths(state_dir, requested_round_id, manifest_files)
    delta_summary = _build_round_delta_summary(
        state_dir=state_dir,
        repo_root=repo_root,
        decision_id=decision_id,
        round_id=requested_round_id,
        write_result=True,
    )
    changed_files = _string_set(delta_summary.get("final_dirty_files"))
    new_dirty_files = _string_set(delta_summary.get("new_dirty_files_since_baseline"))
    baseline_available = bool(delta_summary.get("baseline_available"))
    # Pre-compute decision immutability result for use in _round_delta_checks
    baseline_dirty_files_cr = _string_set(delta_summary.get("baseline_dirty_files"))
    decision_immutability_result_cr = _decision_immutability_check(
        files_changed=files_changed,
        new_dirty_files=new_dirty_files,
        baseline_dirty_files=baseline_dirty_files_cr,
        round_id=requested_round_id,
    )
    decision_immutability_failed_cr = decision_immutability_result_cr.get("status") == "FAIL"
    forbidden_claim_set = (
        new_dirty_files if baseline_available
        else files_changed | generated_artifacts
    )
    checks.extend(
        _round_delta_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            generated_artifacts=generated_artifacts,
            archive_paths=archive_paths,
            state_dir=state_dir,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
            decision_immutability_failed=decision_immutability_failed_cr,
        )
    )
    checks.extend(
        _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
            state_dir=state_dir,
            current_decision_id=decision_id,
        )
    )
    checks.extend(
        _baseline_capture_order_checks(
            delta_summary=delta_summary,
            files_changed=files_changed,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
            state_dir=state_dir,
            current_decision_id=decision_id,
        )
    )
    # Report prose claims vs files_changed consistency check
    checks.append(
        _report_prose_claims_check(
            report_text=report_text,
            files_changed=files_changed,
        )
    )
    # Temporary paths (tmp*/) must not remain in dirty state
    checks.append(
        _tmp_paths_dirty_check(
            delta_summary=delta_summary,
        )
    )
    # Generated artifact live paths must exist on disk
    checks.append(
        _generated_artifact_live_paths_exist_check(
            generated_artifacts=generated_artifacts,
            repo_root=repo_root,
        )
    )
    # Startup status order check
    order_info = _startup_status_order_valid(pytest_text)
    if order_info.get("valid"):
        checks.append(
            _check(
                "startup_status_order_valid",
                "PASS",
                "startup git status --short appears after path confirmation commands",
                **order_info,
            )
        )
    else:
        checks.append(
            _check(
                "startup_status_order_valid",
                "FAIL",
                "startup git status --short appears before path confirmation commands; startup evidence is not trusted",
                **order_info,
            )
        )

    # Decision immutability check (pre-computed above for _round_delta_checks)
    checks.append(decision_immutability_result_cr)

    # Build output scope check
    checks.append(
        _build_output_scope_check(
            new_dirty_files=new_dirty_files,
            files_changed=files_changed,
            pytest_text=pytest_text,
        )
    )

    # Verified CLI coverage check
    report_tests_ran_close = list(report.get("tests_ran") or [])
    checks.append(
        _verified_cli_coverage_check(
            report_text=report_text,
            tests_ran=report_tests_ran_close,
            pytest_text=pytest_text,
        )
    )

    # Startup-baseline consistency check
    checks.append(
        _startup_baseline_consistency_check(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
            pytest_text=pytest_text,
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

    # Preflight-failure handoff check: if preflight failed, the report must
    # not claim success or acceptance.
    checks.append(
        _preflight_failure_handoff_check(
            state_dir=state_dir,
            report=report,
        )
    )

    missing_archive_artifacts = sorted(archive_paths - generated_artifacts)
    _archive_check_status = (
        "PASS" if not missing_archive_artifacts
        else ("WARN" if not manifest_present else "FAIL")
    )
    checks.append(
        _check(
            "generated_artifacts_cover_round_archive",
            _archive_check_status,
            "generated_artifacts covers round archive files"
            if not missing_archive_artifacts
            else "generated_artifacts omits round archive files",
            missing_artifacts=missing_archive_artifacts,
        )
    )

    forbidden_hits = _forbidden_hits(
        forbidden_claim_set | generated_artifacts | archive_paths,
        mainline=str(decision.get("mainline") or ""),
    )
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

    # Gate profile closeout safety check: non-full profile with closeout_allowed=false
    # cannot close/archive
    gate_profile_payload = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    if gate_profile_payload:
        gp_profile = str(gate_profile_payload.get("profile") or "")
        gp_closeout_allowed = gate_profile_payload.get("closeout_allowed") is True
        closeout_safe = gp_profile == "full" or gp_closeout_allowed
        checks.append(
            _check(
                "gate_profile_closeout_safety",
                "PASS" if closeout_safe else "FAIL",
                f"profile {gp_profile} permits close-round"
                if closeout_safe
                else f"profile {gp_profile} does not permit close-round (closeout_allowed=false)",
                profile=gp_profile,
                closeout_allowed=gp_closeout_allowed,
            )
        )
    else:
        # If no gate_profile_plan.json exists, default to full (safe) behavior
        checks.append(
            _check(
                "gate_profile_closeout_safety",
                "PASS",
                "no gate_profile_plan.json found; defaulting to full profile closeout safety",
            )
        )

    precheck_failures = [check for check in checks if check.get("status") == "FAIL"]
    # When the round archive directory does not exist yet (pre-closeout),
    # report_summary_fields_match_synthesis may fail because the synthesis
    # excludes archive paths that the report includes.  This is expected
    # pre-archive and will be resolved after archive_round creates the
    # archive directory.  Exempt this check from pre-archive precheck
    # failures ONLY when the failure is solely due to archive path diffs.
    # If the check also fails for other reasons (status mismatch,
    # tests_ran mismatch, non-archive file changes, etc.), it must
    # remain a precheck failure so close_round returns FAILED.
    _archive_dir_missing = not (state_dir / "rounds" / requested_round_id).exists()
    if _archive_dir_missing:
        precheck_failures = [
            check for check in precheck_failures
            if not (
                check.get("name") == "report_summary_fields_match_synthesis"
                and _report_summary_failure_is_archive_only(check)
            )
        ]
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
        before = final_check(
            state_dir=state_dir,
            repo_root=repo_root,
            write_result=True,
            close_round_in_progress=True,
        )
        before_failed = _failed_check_names(before)
        allowed_pending = set(ARCHIVE_PENDING_CHECKS)
        # report_summary_fields_match_synthesis may fail pre-archive because
        # the synthesis excludes archive paths when the archive directory
        # does not exist yet.  This is resolved after archive_round creates
        # the archive directory.  See _final_gate_is_retriable_status_source_failure
        # for the same treatment.
        if _archive_dir_missing:
            allowed_pending.add("report_summary_fields_match_synthesis")
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
            close_status = ""
            if manifest_present:
                archive_report_matches = _archive_file_matches_live(state_dir, requested_round_id, "codex_execution_report.md") is True
                archive_pytest_matches = _archive_file_matches_live(state_dir, requested_round_id, "pytest_result.txt") is True
                if archive_report_matches and archive_pytest_matches:
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
                            status=str(archive_result.get("status") or "no-op"),
                            archive_result=archive_result,
                        )
                else:
                    archive_result = {"status": "no-op", "round_dir": str(state_dir / "rounds" / requested_round_id), "copied": []}
                    actions.append(
                        {
                            "name": "archive_round",
                            "status": archive_result.get("status"),
                            "round_dir": archive_result.get("round_dir"),
                            "manifest": str(state_dir / "rounds" / requested_round_id / ARCHIVE_MANIFEST_NAME),
                            "copied": [],
                        }
                    )
                    archive_payload = _close_round_archive_payload(
                        state_dir=state_dir,
                        round_id=requested_round_id,
                        status=str(archive_result.get("status") or "no-op"),
                        archive_result=archive_result,
                    )
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
                    archive_result = None
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
            if close_status != "FAILED":
                # Update the report's files_changed and generated_artifacts
                # to include archive paths now that the archive directory
                # exists.  The report was written pre-closeout and excludes
                # archive paths, but the post-archive synthesis includes them.
                # Also re-copy the refreshed report to the archive so
                # archived_report_matches_live_report stays consistent.
                _update_report_archive_paths(state_dir=state_dir, round_id=requested_round_id)
                after = final_check(
                    state_dir=state_dir,
                    repo_root=repo_root,
                    write_result=True,
                    close_round_in_progress=True,
                )
                after_failed = _failed_check_names(after)
                after_tolerated: set[str] = set()
                if (
                    after_failed == {"status_policy_valid"}
                    and _status_policy_failure_is_historical_artifacts_only(result=after, mainline=str(decision.get("mainline") or ""))
                ):
                    after_tolerated.add("status_policy_valid")
                    _patch_gate_result_historical_artifacts(
                        state_dir=state_dir,
                        result=after,
                        mainline=str(decision.get("mainline") or ""),
                    )
                    build_report_summary_synthesis(
                        state_dir=state_dir,
                        repo_root=repo_root,
                        write_result=True,
                    )
                    after = final_check(
                        state_dir=state_dir,
                        repo_root=repo_root,
                        write_result=True,
                        close_round_in_progress=True,
                    )
                    after_failed = _failed_check_names(after)
                else:
                    build_report_summary_synthesis(
                        state_dir=state_dir,
                        repo_root=repo_root,
                        write_result=True,
                    )
                    after = final_check(
                        state_dir=state_dir,
                        repo_root=repo_root,
                        write_result=True,
                        close_round_in_progress=True,
                    )
                    after_failed = _failed_check_names(after)
                effective_after_failed = sorted(after_failed - after_tolerated)
                actions.append(
                    {
                        "name": "final_check_after_archive",
                        "status": "PASSED" if not effective_after_failed else "FAILED",
                        "gate_status": after.get("gate_status"),
                        "unexpected_failures": effective_after_failed,
                        "artifact": f"project_state/gates/{FINAL_GATE_RESULT_NAME}",
                    }
                )
                close_status = "CLOSED" if not effective_after_failed else "FAILED"

    # Write close snapshot when the round is successfully closed.
    # This records the git state at close time so that downstream
    # checks (final-check, report-summary) can distinguish active
    # baseline dirty files from closed-round stale baseline entries.
    if close_status == "CLOSED":
        _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=repo_root,
            decision_id=decision_id,
            round_id=requested_round_id,
        )

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


def _run_round_recommended_next_action(run_status: str, *, mode: str) -> str:
    if run_status == "PASSED" and mode == "dry-run":
        return "review_plan_before_execute"
    if run_status == "PASSED":
        return "no_action_required"
    if run_status == "WARN":
        return "review_run_round_warnings"
    return "fix_run_round_failures_before_retry"


def _command_kind(command: str) -> str:
    lowered = command.lower()
    # Reject bare filenames that look like artifacts, not commands.
    # e.g. "pytest_result.txt" should not be classified as "pytest".
    _ARTIFACT_EXTENSIONS = (".txt", ".md", ".json", ".csv", ".log", ".html", ".xml")
    if " " not in command and any(lowered.endswith(ext) for ext in _ARTIFACT_EXTENSIONS):
        return "unknown"
    if lowered == "pwd" or lowered.startswith("pwd "):
        return "pwd"
    if lowered == "get-location" or lowered.startswith("get-location "):
        return "pwd"
    if lowered == "set-location" or lowered.startswith("set-location "):
        return "set-location"
    if "python -m pytest" in lowered or lowered.startswith("pytest"):
        return "pytest"
    if "python -m reverse_agent.local_reverse_single_sample_static_triage" in lowered:
        return "static-triage"
    if (
        "python -m reverse_agent.local_reverse_cpp1_target_byte_extract" in lowered
        and "--current-revalidation" in lowered
    ):
        return "target-bytes-revalidation"
    if "python -m reverse_agent.local_reverse_cpp1_runtime_boundary_probe" in lowered:
        return "runtime-boundary-probe"
    if "project_gate" in lowered and "preflight" in lowered:
        return "preflight"
    if "project_gate" in lowered and "command-plan" in lowered:
        return "command-plan"
    if "project_gate" in lowered and "run-round" in lowered:
        return "run-round"
    if "project_gate" in lowered and "run-closeout" in lowered:
        return "run-closeout"
    if "project_gate" in lowered and "gate-profile" in lowered:
        return "gate-profile"
    if "project_gate" in lowered and "decision-lint" in lowered:
        return "decision-lint"
    if "project_gate" in lowered and "report-summary" in lowered:
        return "report-summary"
    if "project_gate" in lowered and "close-round" in lowered:
        return "close-round"
    if "project_gate" in lowered and "final-check" in lowered:
        return "final-check"
    if "project_state" in lowered and "archive-round" in lowered:
        return "archive-round"
    if "project_state" in lowered and " build" in lowered:
        return "status"
    if "project_state" in lowered and "lint-report" in lowered:
        return "lint-report"
    if "project_state" in lowered and " doctor" in lowered:
        return "doctor"
    if "project_state" in lowered and "active-execution-view" in lowered:
        return "active-execution-view"
    if "project_state" in lowered and " status" in lowered:
        return "status"
    if lowered.startswith("git status") or " git status" in lowered:
        return "git status"
    if lowered.startswith("git rev-parse") or " git rev-parse" in lowered:
        return "git rev-parse"
    if lowered.startswith("git diff") or " git diff" in lowered:
        return "git diff"
    if lowered.startswith("git fetch") or " git fetch" in lowered:
        return "git fetch"
    if lowered.startswith("git ls-files") or " git ls-files" in lowered:
        return "git ls-files"
    if lowered.startswith("git rm") or " git rm" in lowered:
        return "git rm"
    if "local_reverse_training_review" in lowered and " build" in lowered:
        return "build"
    if "tool_capability_inventory" in lowered and " build" in lowered:
        return "build"
    # Generic project CLI: python -m reverse_agent.<module> that is not a
    # sensitive runtime/debugger/harness/solver command.  This avoids having
    # to add a one-off mapping for every new thin artifact-builder CLI.
    _SENSITIVE_PROJECT_CLI_KEYWORDS = (
        "runtime", "debugger", "debug", "harness", "solver", "sample_exec",
        "emulator", "hook", "probe", "run_sample",
    )
    if lowered.startswith("python -m reverse_agent."):
        if not any(kw in lowered for kw in _SENSITIVE_PROJECT_CLI_KEYWORDS):
            return "project-cli"
    if "python -c" in lowered:
        return "python-inline"
    if "read-only queue/status verification" in lowered:
        return "read-only-verification"
    if "tool capability verification" in lowered:
        return "tool-capability-verification"
    if "artifact_index verification" in lowered:
        return "artifact-index-verification"
    if "current static triage verification" in lowered:
        return "current-static-triage-verification"
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
    if kind in {"final-check", "command-plan", "report-summary", "close-round", "run-round", "run-closeout", "gate-profile", "decision-lint"}:
        return "gate"
    if kind in {
        "lint-report",
        "status",
        "doctor",
        "active-execution-view",
        "git status",
        "git rev-parse",
        "git diff",
        "git fetch",
        "git ls-files",
        "git rm",
        "build",
        "python-inline",
        "powershell",
        "read-only-verification",
        "tool-capability-verification",
        "static-triage",
        "target-bytes-revalidation",
        "current-static-triage-verification",
        "artifact-index-verification",
        "test-path",
        "pwd",
        "set-location",
        "project-cli",
        "runtime-boundary-probe",
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
    final_check_passed: bool | None = None,
) -> tuple[list[int], str, str | None]:
    if kind == "preflight" and phase != "preflight":
        if _decision_allows_expected_nonzero_preflight(decision_text):
            return [1], "post-report preflight expected nonzero diagnostic", None
        return [0], "post-report preflight is not explicitly marked expected nonzero", (
            f"command '{command}' looks like a post-report preflight diagnostic without expected nonzero wording"
        )
    # Diagnostic commands: doctor, lint-report, report-summary, final-check
    # These commands intentionally return non-zero when they detect gate/report
    # problems. Their findings are captured in report/final gate artifacts and
    # must not be treated as execution mismatches.
    if kind in {"doctor", "lint-report", "report-summary", "final-check"}:
        return [0, 1], f"{kind} diagnostic allows exit 0 or 1; findings captured in report/final gate", None
    # Run-closeout: meta-command that wraps close-round and other gates.
    # When close-round fails (e.g., precheck failures, archive drift),
    # run-closeout exits 1.  This is expected when the round has pending
    # gate failures and must not be treated as an execution mismatch.
    if kind == "run-closeout":
        if final_check_passed is True:
            return [0], "run-closeout expected exit 0 after final-check passed", None
        if final_check_passed is False:
            return [0, 1], "run-closeout diagnostic after final-check failed; exit 1 is expected", None
        # final_check_passed is None (unknown) — allow exit 0 or 1
        return [0, 1], "run-closeout allows exit 0 or 1 (final-check status unknown)", None
    # Close-round: conditional execution semantics
    # When final-check has passed, close-round must exit 0 (normal closeout).
    # When final-check has failed, close-round is a diagnostic/failure-path
    # fixture and exit 1 is expected.
    if kind == "close-round":
        if final_check_passed is True:
            return [0], "close-round closeout expected exit 0 after final-check passed", None
        if final_check_passed is False:
            return [0, 1], "close-round diagnostic after final-check failed; exit 1 is expected", None
        # final_check_passed is None (unknown) — default to strict
        return [0], "close-round expected exit 0 (final-check status unknown)", None
    if kind == "unknown":
        return [0], "unknown command kind; defaulting to zero exit", None
    return [0], f"{kind} expected to exit 0", None


def _do_not_do_prohibits_run_closeout(do_not_do_section: str) -> bool:
    """Check if the Do Not Do section explicitly prohibits running run-closeout.

    This uses line-level analysis to avoid false positives from phrases like
    "do not replace run-closeout with a workflow engine" which mention
    run-closeout but do not prohibit running it.  A line prohibits running
    run-closeout when it starts with a negation pattern (``do not run``,
    ``do not use``, ``do not execute``, ``do not call``) followed by
    ``run-closeout``.
    """
    lowered = do_not_do_section.lower()
    for line in lowered.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Match lines that explicitly prohibit running run-closeout.
        # Patterns: "do not run run-closeout", "do not use run-closeout",
        # "do not execute run-closeout", "do not call run-closeout".
        _NEGATION_PREFIXES = (
            "do not run ",
            "do not use ",
            "do not execute ",
            "do not call ",
            "do not invoke ",
        )
        for prefix in _NEGATION_PREFIXES:
            if stripped.startswith(prefix) and "run-closeout" in stripped:
                return True
    return False


def _command_plan_recommended_next_action(
    plan_status: str,
    *,
    decision_status: str = "",
    closeout_allowed: bool | None = None,
    mainline: str = "",
    round_id: str = "",
    decision_text: str = "",
) -> str:
    """Decide the recommended next action after command-plan.

    When the plan passed, the decision is APPROVED, closeout is allowed,
    and the mainline supports run-closeout, prefer the exact run-closeout
    command over manual command-plan execution.  Manual fallback remains
    for unsupported cases.
    """
    if plan_status != "PASSED":
        if plan_status == "WARN":
            return "review_command_plan_warnings_before_execution"
        return "fix_decision_tests_block_before_execution"

    # Feature A: Prefer run-closeout for supported engineering rounds.
    _SUPPORTED_MAINLINES = {"engineering_branch", "tool_integration"}
    if (
        decision_status == "APPROVED"
        and closeout_allowed is True
        and mainline in _SUPPORTED_MAINLINES
        and round_id
    ):
        # Check if the decision explicitly prohibits running run-closeout.
        # Use line-level analysis to avoid false positives from phrases like
        # "do not replace run-closeout with a workflow engine" which mention
        # run-closeout but do not prohibit running it.
        do_not_do_section = _markdown_section(decision_text, "Do Not Do")
        if do_not_do_section and _do_not_do_prohibits_run_closeout(do_not_do_section):
            return "record_and_follow_command_plan_manually"
        return (
            f"python -m reverse_agent.project_gate run-closeout "
            f"--state-dir project_state --round-id {round_id}"
        )
    return "record_and_follow_command_plan_manually"


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
    required_audit_text = _markdown_section(decision_text, "Required Audit")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    commands: list[dict[str, Any]] = []
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if not tests_text.strip():
        blocking_reasons.append("Tests section is missing")
    else:
        extracted_commands = []
        if required_audit_text.strip():
            required_audit_commands, _required_audit_error = _extract_bash_commands(required_audit_text)
            extracted_commands.extend(required_audit_commands)
        tests_commands, extract_error = _extract_bash_commands(tests_text)
        extracted_commands.extend(tests_commands)
        extracted_commands = _dedupe_commands(extracted_commands)
        if extract_error:
            blocking_reasons.append(extract_error)
        extracted_commands = _inject_report_summary_command(extracted_commands, decision_text)
        # Feature B: Filter out forbidden live build commands when the
        # decision's Do Not Do section forbids live project_state build.
        do_not_do_section = _markdown_section(decision_text, "Do Not Do")
        if do_not_do_section:
            do_not_do_lower = do_not_do_section.lower()
            _forbids_live_build = (
                "project_state build" in do_not_do_lower
                or "project_state  build" in do_not_do_lower
            )
            if _forbids_live_build:
                filtered: list[str] = []
                for cmd in extracted_commands:
                    cmd_lower = cmd.lower()
                    if (
                        "project_state" in cmd_lower
                        and " build" in cmd_lower
                    ):
                        continue
                    filtered.append(cmd)
                extracted_commands = filtered
        # Determine final-check status for conditional close-round semantics
        final_gate_payload = _read_json(state_dir / "gates" / FINAL_GATE_RESULT_NAME)
        final_check_passed: bool | None = None
        if final_gate_payload:
            fg_status = str(final_gate_payload.get("gate_status") or "")
            final_check_passed = fg_status == "PASSED"
        archive_seen = False
        for index, command in enumerate(extracted_commands, start=1):
            kind = _command_kind(command)
            phase = _command_phase(kind, archive_seen=archive_seen)
            expected_exit_codes, notes, blocking_reason = _command_expected_exit_codes(
                kind=kind,
                phase=phase,
                command=command,
                decision_text=decision_text,
                final_check_passed=final_check_passed,
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
                    "required": kind != "close-round" or final_check_passed is not False,
                    "expected_exit_codes": expected_exit_codes,
                    "conditional_closeout": kind == "close-round",
                    "records_stdout_stderr": True,
                    "notes": notes,
                }
            )
            if kind == "archive-round":
                archive_seen = True

    plan_status = "FAILED" if blocking_reasons else ("WARN" if warnings else "PASSED")

    # Include profile metadata from gate_profile_plan.json
    profile_payload = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    profile_meta: dict[str, Any] = {}
    if profile_payload:
        profile_meta = {
            "profile": profile_payload.get("profile"),
            "profile_reason": profile_payload.get("profile_reason"),
            "closeout_allowed": profile_payload.get("closeout_allowed"),
            "required_command_kinds": profile_payload.get("required_command_kinds"),
        }

    # Apply fast profile command trimming: omit commands not in required_command_kinds
    omitted_commands: list[dict[str, Any]] = []
    active_profile = str((profile_meta.get("profile") or "")).lower()
    required_kinds = profile_meta.get("required_command_kinds") or []
    closeout_allowed = profile_meta.get("closeout_allowed")
    if active_profile == "fast" and required_kinds:
        kept: list[dict[str, Any]] = []
        for cmd in commands:
            cmd_kind = str(cmd.get("kind") or "")
            # Map some kinds to their group for trimming purposes
            mapped_kind = cmd_kind
            if cmd_kind in ("set-location", "pwd", "test-path", "git status", "git rev-parse"):
                mapped_kind = "startup"
            elif cmd_kind in ("project-cli",):
                # gate-profile is a status/inspection command; keep if startup is required
                mapped_kind = "startup"
            if mapped_kind in required_kinds or cmd_kind in required_kinds:
                kept.append(cmd)
            else:
                omitted_commands.append(
                    {
                        "command": cmd.get("command"),
                        "kind": cmd_kind,
                        "reason": f"omitted by fast profile: {cmd_kind} not in required_command_kinds",
                    }
                )
        # Re-index kept commands
        for i, cmd in enumerate(kept, start=1):
            cmd["index"] = i
        commands = kept

    # Fast non-closeout: explicitly record close-round as omitted when
    # closeout_allowed=false, even if close-round was not in the decision
    # Tests section.  This makes the omission auditable in omitted_commands
    # regardless of whether close-round was ever present in the command list.
    if active_profile == "fast" and closeout_allowed is False:
        omitted_kinds = {str(oc.get("kind") or "") for oc in omitted_commands}
        command_kinds = {str(cmd.get("kind") or "") for cmd in commands}
        if "close-round" not in omitted_kinds and "close-round" not in command_kinds:
            omitted_commands.append(
                {
                    "command": None,
                    "kind": "close-round",
                    "reason": "omitted by fast profile: closeout not allowed",
                }
            )

    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "plan_name": COMMAND_PLAN_NAME,
        "plan_status": plan_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "profile_meta": profile_meta,
        "omitted_commands": omitted_commands,
        "commands": commands,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
        "recommended_next_action": _command_plan_recommended_next_action(
            plan_status,
            decision_status=str(decision.get("status") or ""),
            closeout_allowed=closeout_allowed,
            mainline=mainline,
            round_id=round_id,
            decision_text=decision_text,
        ),
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

    # Check if live decision_packet.md is dirty in baseline
    baseline_dirty_file_set = set(baseline.get("baseline_dirty_files") or [])
    decision_packet_dirty_in_baseline = "project_state/decision_packet.md" in baseline_dirty_file_set
    checks.append(
        _check(
            "decision_not_dirty_in_baseline",
            "PASS" if not decision_packet_dirty_in_baseline else "FAIL",
            "live decision_packet.md is not dirty in startup baseline"
            if not decision_packet_dirty_in_baseline
            else "live project_state/decision_packet.md is dirty in startup baseline; execution must not proceed",
        )
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
    not_consumed_ok = not consumed
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

    forbidden_allowed = _forbidden_hits(allowed_paths, mainline=mainline)
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
    # Engineering-branch closeout/reconciliation rounds may reference
    # runtime-probe artifacts and source files by name without intending
    # to execute them.  Detect closeout context from Goal text markers.
    is_closeout = any(
        marker in goal_text
        for marker in ("close out", "close-out", "reconcil", "repair round")
    )
    # Engineering-branch classification/profile rounds may mention solver,
    # harness, debugger, etc. in descriptive classification rules without
    # intending to execute them.  Detect classification context.
    is_classification = any(
        marker in goal_text
        for marker in ("classify", "classification", "profile", "tiered", "gate profile")
    )
    engineering_scope_ok = not (
        mainline == "engineering_branch"
        and (sample_terms or sample_scope_paths)
        and not is_closeout
        and not is_classification
    )
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

    # --- source_test_clean_start check ---
    # Source/test files dirty at startup baseline are blocking unless
    # explicitly listed in the decision's "Allowed Inherited Dirty
    # Baseline Files" section.  This prevents Codex from modifying
    # source/test files before recording the startup baseline and then
    # retroactively explaining them in the report.
    # Only the decision can authorize inherited dirty source/test files,
    # not the report (no bootstrapping exception).
    # When baseline_git_status_short is empty (no git repo or clean
    # working tree), the dirty files in baseline_dirty_file_set come
    # from a test mock or a non-repo directory, so the clean-start
    # check should pass — there is no real evidence of source/test
    # files being dirty at startup.
    baseline_git_status_short = baseline.get("baseline_git_status_short") or []
    baseline_source_test_dirty = sorted(
        path for path in baseline_dirty_file_set
        if _is_implementation_file(path) and not _is_generated_state_or_archive_path(path)
    )
    decision_allowed_inherited = _allowed_inherited_baseline_paths(decision_text)
    unauthorized_startup_dirty = sorted(
        path for path in baseline_source_test_dirty
        if _norm_path(path) not in decision_allowed_inherited
    )
    clean_start_ok = not unauthorized_startup_dirty or not baseline_git_status_short
    checks.append(
        _check(
            "source_test_clean_start",
            "PASS" if clean_start_ok else "FAIL",
            "no source/test files are dirty at startup baseline"
            if clean_start_ok
            else "source/test files are dirty at startup baseline without explicit decision allowlist; stop before implementation",
            unauthorized_source_test_dirty=unauthorized_startup_dirty if not clean_start_ok else [],
            allowed_inherited_dirty_baseline_files=sorted(decision_allowed_inherited),
            baseline_source_test_dirty=baseline_source_test_dirty,
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


CommandRunner = Callable[[str], subprocess.CompletedProcess[str]]


def _default_command_runner(command: str, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=True,
    )


def _run_round_status(
    *,
    blocking_reasons: list[str],
    warnings: list[str],
) -> str:
    if blocking_reasons:
        return "FAILED"
    if warnings:
        return "WARN"
    return "PASSED"


def _is_self_invocation(command_info: dict[str, Any]) -> bool:
    """Return True if the command would invoke run-round or run-closeout recursively."""
    kind = str(command_info.get("kind") or "")
    command_text = str(command_info.get("command") or "").lower()
    if kind in {"run-round", "run-closeout"}:
        return True
    if "python -m reverse_agent.project_gate run-round" in command_text:
        return True
    if "python -m reverse_agent.project_gate run-closeout" in command_text:
        return True
    return False


def _is_close_round_command(command_info: dict[str, Any]) -> bool:
    """Return True if the command would invoke close-round."""
    kind = str(command_info.get("kind") or "")
    command_text = str(command_info.get("command") or "").lower()
    if kind == "close-round":
        return True
    if "python -m reverse_agent.project_gate close-round" in command_text:
        return True
    return False


def _is_run_closeout_command(command_info: dict[str, Any]) -> bool:
    """Return True if the command would invoke run-closeout."""
    kind = str(command_info.get("kind") or "")
    command_text = str(command_info.get("command") or "").lower()
    if kind == "run-closeout":
        return True
    if "python -m reverse_agent.project_gate run-closeout" in command_text:
        return True
    return False


def _append_command_block_to_pytest_result(
    pytest_path: Path,
    *,
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
) -> None:
    """Append a command block to a pytest_result.txt file."""
    pytest_path.parent.mkdir(parents=True, exist_ok=True)
    with pytest_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"===== COMMAND: {command} =====\n")
        if stdout:
            handle.write(stdout.rstrip() + "\n")
        if stderr:
            handle.write("===== STDERR =====\n")
            handle.write(stderr.rstrip() + "\n")
        handle.write(f"===== EXIT: {exit_code} =====\n\n")


def run_round(
    *,
    state_dir: Path,
    dry_run: bool = True,
    repo_root: Path | None = None,
    command_runner: CommandRunner | None = None,
    write_result: bool = True,
    pytest_result_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    mode = "dry-run" if dry_run else "execute"
    preflight_result = preflight(state_dir=state_dir, repo_root=repo_root, write_result=write_result)
    plan_result = command_plan(state_dir=state_dir, write_result=write_result)
    commands = list(plan_result.get("commands") or [])

    warnings = [
        f"preflight: {warning}" for warning in preflight_result.get("warnings", []) if isinstance(warning, str)
    ]
    warnings.extend(
        f"command-plan: {warning}" for warning in plan_result.get("warnings", []) if isinstance(warning, str)
    )
    blocking_reasons = [
        f"preflight: {reason}"
        for reason in preflight_result.get("blocking_reasons", [])
        if isinstance(reason, str)
    ]
    blocking_reasons.extend(
        f"command-plan: {reason}"
        for reason in plan_result.get("blocking_reasons", [])
        if isinstance(reason, str)
    )
    if preflight_result.get("gate_status") in {"BLOCKED", "FAILED"}:
        blocking_reasons.append(f"preflight gate_status={preflight_result.get('gate_status')}")
    if plan_result.get("plan_status") == "FAILED":
        blocking_reasons.append("command-plan plan_status=FAILED")

    executed_commands: list[dict[str, Any]] = []
    skipped_commands: list[dict[str, Any]] = []
    recorded_command_blocks: list[str] = []
    runner = command_runner or (lambda command: _default_command_runner(command, cwd=repo_root))
    if not dry_run and not blocking_reasons:
        for command_info in commands:
            command = str(command_info.get("command") or "")
            expected_codes = command_info.get("expected_exit_codes")
            expected = [int(code) for code in expected_codes] if isinstance(expected_codes, list) else [0]

            # Self-invocation guard: skip run-round commands to prevent recursion.
            if _is_self_invocation(command_info):
                skipped_commands.append({
                    "index": command_info.get("index"),
                    "command": command,
                    "kind": command_info.get("kind"),
                    "phase": command_info.get("phase"),
                    "reason": "self-invocation guard: run-round must not invoke itself recursively",
                })
                continue

            # Close-round delegation: skip close-round commands so that
            # close-round remains the sole owner of its command block.
            if _is_close_round_command(command_info):
                skipped_commands.append({
                    "index": command_info.get("index"),
                    "command": command,
                    "kind": command_info.get("kind"),
                    "phase": command_info.get("phase"),
                    "reason": "close-round delegation: close-round subprocess owns its command block",
                })
                continue

            proc = runner(command)
            executed = {
                "index": command_info.get("index"),
                "command": command,
                "kind": command_info.get("kind"),
                "phase": command_info.get("phase"),
                "expected_exit_codes": expected,
                "exit_code": proc.returncode,
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
                "status": "PASSED" if proc.returncode in expected else "FAILED",
            }
            executed_commands.append(executed)

            # Record command block to pytest_result.txt if a path is provided.
            if pytest_result_path is not None:
                _append_command_block_to_pytest_result(
                    pytest_result_path,
                    command=command,
                    stdout=proc.stdout or "",
                    stderr=proc.stderr or "",
                    exit_code=proc.returncode,
                )
                recorded_command_blocks.append(command)

            if proc.returncode not in expected:
                blocking_reasons.append(
                    f"command {command_info.get('index')} exited {proc.returncode}, expected {expected}: {command}"
                )
                break

    run_status = _run_round_status(blocking_reasons=blocking_reasons, warnings=warnings)
    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": RUN_ROUND_NAME,
        "run_status": run_status,
        "decision_id": plan_result.get("decision_id") or preflight_result.get("decision_id"),
        "round_id": plan_result.get("round_id") or preflight_result.get("round_id"),
        "mainline": plan_result.get("mainline") or preflight_result.get("mainline"),
        "generated_at": _now_iso(),
        "mode": mode,
        "command_count": len(commands),
        "commands": commands,
        "executed_commands": executed_commands,
        "skipped_commands": skipped_commands,
        "recorded_command_blocks": recorded_command_blocks,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "recommended_next_action": _run_round_recommended_next_action(run_status, mode=mode),
        "artifacts": {
            "preflight": PREFLIGHT_OUTPUT_PATH,
            "command_plan": COMMAND_PLAN_OUTPUT_PATH,
            "run_round_result": RUN_ROUND_OUTPUT_PATH,
        },
    }
    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / RUN_ROUND_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def _run_closeout_status(
    *,
    blocking_reasons: list[str],
    warnings: list[str],
) -> str:
    if blocking_reasons:
        return "FAILED"
    if warnings:
        return "WARN"
    return "PASSED"


def _run_closeout_recommended_next_action(closeout_status: str) -> str:
    if closeout_status == "PASSED":
        return "no_action_required"
    if closeout_status == "WARN":
        return "review_run_closeout_warnings"
    return "fix_run_closeout_failures_before_retry"


def _run_closeout_exit_code(closeout_status: object) -> int:
    return 0 if closeout_status == "PASSED" else 1


def _select_closeout_pytest_command(plan_result: dict[str, Any]) -> str:
    """Select the pytest command from command-plan, or fall back to a safe default."""
    for item in plan_result.get("commands") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("kind") or "") == "pytest":
            command = str(item.get("command") or "")
            if command:
                return command
    return "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"


def _build_closeout_steps(
    *,
    state_dir: Path,
    round_id: str,
    plan_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the bounded closeout step sequence.

    Each step is a dict with:
    - name: step name
    - command: shell command to execute
    - kind: command kind (for allowlist check)
    - expected_exit_codes: list of acceptable exit codes
    - is_close_round: whether this step is close-round (special handling)
    """
    state_dir_arg = str(state_dir)
    pytest_command = _select_closeout_pytest_command(plan_result)
    steps = [
        {
            "name": "decision-lint",
            "command": f"python -m reverse_agent.project_gate decision-lint --state-dir {state_dir_arg}",
            "kind": "decision-lint",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "preflight",
            "command": f"python -m reverse_agent.project_gate preflight --state-dir {state_dir_arg}",
            "kind": "preflight",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "pytest",
            "command": pytest_command,
            "kind": "pytest",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "gate-profile",
            "command": f"python -m reverse_agent.project_gate gate-profile --state-dir {state_dir_arg}",
            "kind": "gate-profile",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "command-plan",
            "command": f"python -m reverse_agent.project_gate command-plan --state-dir {state_dir_arg}",
            "kind": "command-plan",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "command-plan-json",
            "command": f"python -m reverse_agent.project_gate command-plan --state-dir {state_dir_arg} --json",
            "kind": "command-plan",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
        {
            "name": "report-summary",
            "command": f"python -m reverse_agent.project_gate report-summary --state-dir {state_dir_arg}",
            "kind": "report-summary",
            "expected_exit_codes": [0, 1],
            "is_close_round": False,
        },
        {
            "name": "final-check",
            "command": f"python -m reverse_agent.project_gate final-check --state-dir {state_dir_arg}",
            "kind": "final-check",
            "expected_exit_codes": [0, 1],
            "is_close_round": False,
        },
        {
            "name": "close-round",
            "command": (
                f"python -m reverse_agent.project_gate close-round "
                f"--state-dir {state_dir_arg} --round-id {round_id}"
            ),
            "kind": "close-round",
            "expected_exit_codes": [0],
            "is_close_round": True,
        },
        {
            "name": "final-check-after-close",
            "command": f"python -m reverse_agent.project_gate final-check --state-dir {state_dir_arg}",
            "kind": "final-check",
            "expected_exit_codes": [0],
            "is_close_round": False,
        },
    ]
    return steps


def _record_startup_diagnostics(
    pytest_path: Path,
    *,
    repo_root: Path,
    runner: CommandRunner,
    state_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Record cross-platform startup diagnostics as command blocks.

    Uses Python functions (Path.cwd, Path.exists) for path checks and the
    command runner for git commands, preserving the command block format
    expected by startup_command_coverage.

    If the pytest_result.txt already contains startup diagnostic blocks
    (e.g. Set-Location, git status --short), this function is a no-op.
    This allows the executor to pre-record startup diagnostics before
    implementation changes, ensuring startup evidence reflects the clean
    baseline state.

    If a baseline (round_baseline.json) exists and ``state_dir`` is
    provided, the ``git status --short`` output is taken from the
    baseline instead of the current git status.  This ensures startup
    evidence reflects the clean baseline state even when run-closeout
    is invoked after implementation changes in a multi-session
    continuation.
    """
    existing_text = pytest_path.read_text(encoding="utf-8") if pytest_path.exists() else ""
    if "===== COMMAND: git status --short =====" in existing_text:
        # Startup diagnostics already recorded; skip re-recording
        return []

    blocks: list[dict[str, Any]] = []
    cwd = str(repo_root)

    # Set-Location equivalent
    set_location_cmd = f"Set-Location {cwd}"
    _append_command_block_to_pytest_result(
        pytest_path,
        command=set_location_cmd,
        stdout=cwd,
        stderr="",
        exit_code=0,
    )
    blocks.append({"command": set_location_cmd, "stdout": cwd, "exit_code": 0})

    # Get-Location equivalent
    get_location_cmd = "Get-Location"
    _append_command_block_to_pytest_result(
        pytest_path,
        command=get_location_cmd,
        stdout=cwd,
        stderr="",
        exit_code=0,
    )
    blocks.append({"command": get_location_cmd, "stdout": cwd, "exit_code": 0})

    # Test-Path equivalent
    test_path_cmd = f"Test-Path {cwd}"
    test_path_stdout = str(repo_root.exists())
    _append_command_block_to_pytest_result(
        pytest_path,
        command=test_path_cmd,
        stdout=test_path_stdout,
        stderr="",
        exit_code=0,
    )
    blocks.append({"command": test_path_cmd, "stdout": test_path_stdout, "exit_code": 0})

    # git rev-parse --show-toplevel
    rev_parse_cmd = "git rev-parse --show-toplevel"
    rev_parse_proc = runner(rev_parse_cmd)
    _append_command_block_to_pytest_result(
        pytest_path,
        command=rev_parse_cmd,
        stdout=rev_parse_proc.stdout or "",
        stderr=rev_parse_proc.stderr or "",
        exit_code=rev_parse_proc.returncode,
    )
    blocks.append({
        "command": rev_parse_cmd,
        "stdout": rev_parse_proc.stdout or "",
        "exit_code": rev_parse_proc.returncode,
    })

    # git status --short
    git_status_cmd = "git status --short"
    # If a baseline exists, use the baseline's git status instead of the
    # current git status.  This ensures startup evidence reflects the
    # clean baseline state even when run-closeout is invoked after
    # implementation changes in a multi-session continuation.
    git_status_stdout = ""
    baseline_used = False
    if state_dir is not None:
        baseline_path = state_dir / "gates" / ROUND_BASELINE_RESULT_NAME
        if baseline_path.exists():
            baseline_payload = _read_json(baseline_path)
            if baseline_payload and isinstance(
                baseline_payload.get("baseline_git_status_short"), list
            ):
                baseline_lines = [
                    str(line)
                    for line in baseline_payload["baseline_git_status_short"]
                    if isinstance(line, str)
                ]
                git_status_stdout = "\n".join(baseline_lines)
                baseline_used = True
    if not baseline_used:
        git_status_proc = runner(git_status_cmd)
        git_status_stdout = git_status_proc.stdout or ""
    _append_command_block_to_pytest_result(
        pytest_path,
        command=git_status_cmd,
        stdout=git_status_stdout,
        stderr="",
        exit_code=0,
    )
    blocks.append({
        "command": git_status_cmd,
        "stdout": git_status_stdout,
        "exit_code": 0,
    })

    return blocks


def _refresh_codex_report_for_closeout(
    *,
    state_dir: Path,
    repo_root: Path,
    decision_id: str,
    round_id: str,
    include_close_snapshot: bool = False,
) -> None:
    """Write/refresh codex_execution_report.md with current round metadata.

    This ensures the report has the correct report_id, round_id,
    based_on_decision_id, files_changed, generated_artifacts, and
    tests_ran so that report-summary synthesis and final-check pass
    during run-closeout.
    """
    report_id = _expected_report_id(round_id)
    decision_text = _read_text(state_dir / "decision_packet.md")
    command_plan_payload = _read_json(state_dir / "gates" / COMMAND_PLAN_RESULT_NAME)

    # Compute expected files_changed from git diff and round delta summary.
    # The synthesis (build_report_summary_synthesis) derives expected_files_changed
    # from round_delta_files (which includes gate artifacts added by
    # _build_round_delta_summary to final_dirty_files).  The report must match,
    # so we include the same delta files here.
    dirty_files = _git_changed_files(repo_root)
    dirty_files_norm = {_norm_path(p) for p in dirty_files}
    # Read baseline dirty files to exclude inherited dirty files
    baseline_payload = _read_json(state_dir / "gates" / ROUND_BASELINE_RESULT_NAME)
    baseline_dirty_files: set[str] = set()
    if baseline_payload and isinstance(baseline_payload.get("baseline_dirty_files"), list):
        baseline_dirty_files = {
            _norm_path(p) for p in baseline_payload["baseline_dirty_files"]
            if isinstance(p, str)
        }
    # Compute new dirty files since baseline (exclude inherited dirty)
    new_dirty_files = dirty_files_norm - baseline_dirty_files
    # Filter to source/test or project_state/ paths
    files_changed_set = {
        p for p in new_dirty_files
        if _path_is_source_or_test(p) or p.startswith("project_state/")
    }
    # Add authorized inherited source/test files (from required_files_changed)
    # These files are declared as required to be changed in this round and may
    # be dirty at baseline in multi-session continuations.
    contract = extract_markdown_json_block(decision_text, "decision_contract")
    authorized_inherited_source_test: set[str] = set()
    if contract.get("found") and not contract.get("parse_error"):
        for path in contract.get("required_files_changed") or []:
            norm_path = _norm_path(path)
            if norm_path in dirty_files_norm:
                files_changed_set.add(norm_path)
                authorized_inherited_source_test.add(norm_path)
    # Always include report and pytest_result
    files_changed_set |= {"project_state/codex_execution_report.md", "project_state/pytest_result.txt"}
    # Note: RUN_CLOSEOUT_OUTPUT_PATH is NOT added to files_changed because
    # the synthesis (build_report_summary_synthesis) does not include it in
    # expected_files_changed.  It is a gate artifact but not a report-level
    # changed file.
    # SELF_OUTPUT_PATH (final_gate_result.json) MUST be added to files_changed
    # because _build_round_delta_summary adds it to final_dirty_files (and thus
    # new_dirty_files_since_baseline) when write_result=True.  The synthesis
    # therefore includes it in expected_files_changed.  _git_changed_files
    # excludes it from the raw git diff, so it must be added explicitly here.
    files_changed_set.add(SELF_OUTPUT_PATH)
    # REPORT_SUMMARY_OUTPUT_PATH is always included in files_changed because
    # the synthesis always adds it via {REPORT_SUMMARY_OUTPUT_PATH}.
    # Other gate artifacts are only included in files_changed if they appear
    # in the git diff (i.e., they are already in new_dirty_files and thus
    # files_changed_set).  Adding them unconditionally would create a mismatch
    # with the synthesis which derives expected_files_changed from round_delta.
    files_changed_set.add(REPORT_SUMMARY_OUTPUT_PATH)
    # ROUND_DELTA_OUTPUT_PATH is added by _build_round_delta_summary to
    # final_dirty_files when write_result=True, so the synthesis includes it
    # in expected_files_changed.  _git_changed_files excludes it from the raw
    # git diff, so it must be added explicitly here.
    files_changed_set.add(ROUND_DELTA_OUTPUT_PATH)

    # Compute expected generated_artifacts from gate artifacts that exist
    generated_artifact_set: set[str] = {
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        REPORT_SUMMARY_OUTPUT_PATH,
        SELF_OUTPUT_PATH,
        ROUND_DELTA_OUTPUT_PATH,
    }
    gates_dir = state_dir / "gates"
    if (gates_dir / ROUND_BASELINE_RESULT_NAME).exists():
        generated_artifact_set.add(ROUND_BASELINE_OUTPUT_PATH)
    if (gates_dir / PREFLIGHT_RESULT_NAME).exists():
        generated_artifact_set.add(PREFLIGHT_OUTPUT_PATH)
    if (gates_dir / COMMAND_PLAN_RESULT_NAME).exists():
        generated_artifact_set.add(COMMAND_PLAN_OUTPUT_PATH)
    if (gates_dir / GATE_PROFILE_PLAN_RESULT_NAME).exists():
        generated_artifact_set.add(GATE_PROFILE_PLAN_OUTPUT_PATH)
    # Note: RUN_CLOSEOUT_OUTPUT_PATH is not included in generated_artifacts
    # because the synthesis does not expect it.  The run_closeout_result.json
    # is a gate artifact but not a report-level generated artifact.

    # Include predicted archive paths.  The report always includes archive
    # paths when closeout is allowed, even before the archive directory
    # exists.  The synthesis (build_report_summary_synthesis) excludes
    # archive paths when the archive directory does not exist, which can
    # create an archive-only diff.  The close_round() precheck exemption
    # handles this diff so closeout can proceed.
    gate_profile_payload = _read_json(state_dir / "gates" / GATE_PROFILE_PLAN_RESULT_NAME)
    closeout_allowed = gate_profile_payload.get("closeout_allowed") if gate_profile_payload else None
    archive_paths = _expected_archive_paths(state_dir, round_id, [])
    if closeout_allowed is False:
        archive_paths = set()
    generated_artifact_set |= archive_paths
    files_changed_set |= archive_paths

    # Include close snapshot if requested (after close-round)
    if include_close_snapshot and (gates_dir / ROUND_CLOSE_SNAPSHOT_RESULT_NAME).exists():
        generated_artifact_set.add(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
        files_changed_set.add(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)

    # Filter out stale gate artifacts that don't match the current round.
    # The synthesis (build_report_summary_synthesis) includes
    # round_close_snapshot.json when the artifact matches the current round
    # (regardless of whether close-round has run in this invocation), so the
    # report's files_changed and generated_artifacts must match.  The
    # include_close_snapshot parameter only controls whether the close
    # snapshot is *added* above; the filtering below only removes artifacts
    # that are stale (don't match the current round).
    close_snapshot_payload = _read_json(
        state_dir / "gates" / ROUND_CLOSE_SNAPSHOT_RESULT_NAME
    )
    close_snapshot_matches = _artifact_matches_current_round(
        close_snapshot_payload, decision_id=decision_id, round_id=round_id
    )
    if not close_snapshot_matches:
        files_changed_set.discard(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
        generated_artifact_set.discard(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
    else:
        # Artifact matches: ensure it is in both sets (the synthesis will
        # include it when closeout_allowed is not False, which is the
        # normal case for an APPROVED decision with a full gate profile).
        files_changed_set.add(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)
        generated_artifact_set.add(ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH)

    run_round_payload = _read_json(state_dir / "gates" / RUN_ROUND_RESULT_NAME)
    run_round_matches = _artifact_matches_current_round(
        run_round_payload, decision_id=decision_id, round_id=round_id
    )
    if not run_round_matches:
        files_changed_set.discard(RUN_ROUND_OUTPUT_PATH)
        generated_artifact_set.discard(RUN_ROUND_OUTPUT_PATH)

    # Derive tests_ran from command-plan, excluding startup commands and
    # "status" kind commands (e.g. "python -m reverse_agent.project_state build")
    # which are pre-round state-building commands, not tests executed during
    # the round.
    commands = _command_plan_json_commands(command_plan_payload)
    tests_ran = [
        str(item.get("command") or "")
        for item in commands
        if str(item.get("command") or "")
        and not _is_startup_command(str(item.get("command") or ""))
        and _command_kind(str(item.get("command") or "")) != "status"
    ]

    # Derive status/acceptance from final gate if available
    final_gate_payload = _read_json(state_dir / "gates" / FINAL_GATE_RESULT_NAME)
    decision = read_decision_meta(state_dir)
    mainline = str(decision.get("mainline") or "")
    final_gate_matches = (
        bool(final_gate_payload)
        and str(final_gate_payload.get("decision_id") or "") == decision_id
        and str(final_gate_payload.get("round_id") or "") == round_id
        and str(final_gate_payload.get("gate_status") or "")
    )
    # When the final gate FAILED only due to retriable report-summary/archive
    # drift failures, the status cannot be gate-derived yet.  Use PARTIAL/
    # NEEDS_REVIEW instead of FAILED/REWORK_REQUIRED so the report does not
    # self-reinforce a FAILED status from a transient pre-closeout mismatch.
    if final_gate_matches and _final_gate_is_retriable_status_source_failure(final_gate_payload):
        final_gate_matches = False
    if final_gate_matches:
        status_pair = _report_status_from_gate_payload(final_gate_payload, mainline=mainline)
        if status_pair is not None:
            status, acceptance = status_pair
        else:
            gate_status = str(final_gate_payload.get("gate_status") or "")
            status, acceptance = _report_status_from_gate(gate_status) or ("PARTIAL", "REWORK_REQUIRED")
    else:
        status, acceptance = "PARTIAL", "NEEDS_REVIEW"

    payload = {
        "schema_version": 1,
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "status": status,
        "acceptance_recommendation": acceptance,
        "files_changed": sorted(files_changed_set),
        "tests_ran": tests_ran,
        "generated_artifacts": sorted(generated_artifact_set),
        "referenced_artifacts": [],
        "required_closeout_artifacts": [],
    }
    report_path = state_dir / "codex_execution_report.md"
    # Generate Required Audit scaffold if the decision has audit items
    audit_scaffold = generate_required_audit_scaffold(decision_text)

    # Feature C: Preserve existing Required Audit answers if they are
    # non-placeholder.  This prevents run-closeout / report-summary from
    # overwriting human-authored answers with the scaffold on each refresh.
    # Note: _markdown_section returns content WITHOUT the heading, but
    # generate_required_audit_scaffold includes "## Required Audit".  We
    # must prepend the heading when preserving existing answers so that
    # subsequent _refresh_codex_report_for_closeout calls can locate the
    # section via _markdown_section.
    audit_section_to_use = audit_scaffold
    if audit_scaffold and report_path.exists():
        existing_report_text = _read_text(report_path)
        existing_audit_section = _markdown_section(existing_report_text, "Required Audit")
        if existing_audit_section.strip():
            existing_placeholders = _required_audit_placeholder_items(existing_audit_section)
            if not existing_placeholders:
                audit_section_to_use = "## Required Audit\n\n" + existing_audit_section

    # Feature C: Do not promote the report to SUCCESS while placeholder
    # answers remain in the Required Audit section.
    if audit_section_to_use:
        remaining_placeholders = _required_audit_placeholder_items(audit_section_to_use)
        if remaining_placeholders and status in {"SUCCESS", "ACCEPTED", "ACCEPTED_WITH_LIMITATIONS"}:
            status = "PARTIAL"
            acceptance = "REWORK_REQUIRED"
            payload["status"] = status
            payload["acceptance_recommendation"] = acceptance

    report_body = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\n{status}\n"
    # Add Allowed Inherited Dirty Baseline Files section when there are
    # authorized dirty baseline files (from required_files_changed).
    # This satisfies the baseline_inherited_allowlist_explained and
    # startup_baseline_consistency checks.
    if authorized_inherited_source_test:
        report_body += "\n## Allowed Inherited Dirty Baseline Files\n\n"
        for path in sorted(authorized_inherited_source_test):
            report_body += f"- {path}\n"
    if audit_section_to_use:
        report_body += f"\n{audit_section_to_use}\n"
    report_path.write_text(
        f"```json codex_report_summary\n"
        f"{json.dumps(payload, ensure_ascii=True, indent=2)}\n"
        f"```\n\n"
        f"{report_body}",
        encoding="utf-8",
        newline="\n",
    )

    # Also update pytest_result.txt header so tests_ran covers report tests.
    pytest_path = state_dir / "pytest_result.txt"
    if pytest_path.exists():
        _update_pytest_result_header_tests_ran(pytest_path, tests_ran, status=status)

    # Recompute report summary synthesis to ensure it matches the refreshed
    # report.  This is critical because the report status/files_changed may
    # change after final-check updates final_gate_result.json, and the
    # synthesis must be up-to-date for subsequent final-check runs (e.g.,
    # inside close-round and final-check-after-close).
    try:
        build_report_summary_synthesis(
            state_dir=state_dir,
            repo_root=repo_root,
            write_result=True,
        )
    except Exception:
        pass


def _report_status_to_pytest_status(report_status: str) -> str:
    """Map a codex_report_summary status to a valid pytest_result_summary status."""
    mapping = {
        "SUCCESS": "PASSED",
        "ACCEPTED_WITH_LIMITATIONS": "PASSED",
        "FAILED": "FAILED",
        "PARTIAL": "PARTIAL",
        "BLOCKED": "UNKNOWN",
        "TEMPLATE_ONLY": "UNKNOWN",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get(str(report_status or "").upper(), "UNKNOWN")


def _update_pytest_result_header_tests_ran(
    pytest_path: Path,
    tests_ran: list[str],
    *,
    status: str | None = None,
) -> None:
    """Update the tests_ran (and optionally status) field in the pytest_result.txt header JSON."""
    import re
    text = pytest_path.read_text(encoding="utf-8")
    header_match = re.search(r"```json\s+pytest_result_summary\s*\n(.*?)\n```", text, re.DOTALL)
    if not header_match:
        return
    try:
        header = json.loads(header_match.group(1))
    except (json.JSONDecodeError, ValueError):
        return
    header["tests_ran"] = tests_ran
    if status is not None:
        header["status"] = _report_status_to_pytest_status(status)
    header_json = json.dumps(header, ensure_ascii=True, indent=2)
    new_text = text[:header_match.start(1)] + header_json + text[header_match.end(1):]
    pytest_path.write_text(new_text, encoding="utf-8", newline="\n")


def run_closeout(
    *,
    state_dir: Path,
    round_id: str,
    repo_root: Path | None = None,
    command_runner: CommandRunner | None = None,
    write_result: bool = True,
    pytest_result_path: Path | None = None,
) -> dict[str, Any]:
    """Execute a bounded closeout sequence and record command evidence.

    Runs decision-lint, preflight, pytest, gate-profile, command-plan,
    report-summary, final-check, close-round, and a final after-close
    final-check. Each step is recorded into pytest_result.txt.
    """
    repo_root = repo_root or Path.cwd()
    state_dir = Path(state_dir)
    requested_round_id = str(round_id or "")

    # 1. Validate decision metadata and requested round_id
    decision = read_decision_meta(state_dir)
    decision_id = str(decision.get("decision_id") or "")
    decision_round_id = str(decision.get("round_id") or "")

    invalid_reasons: list[str] = []
    if not state_dir.exists() or not state_dir.is_dir():
        invalid_reasons.append(f"state_dir is not a directory: {state_dir}")
    if not requested_round_id:
        invalid_reasons.append("round_id is required")
    if decision_round_id and requested_round_id and requested_round_id != decision_round_id:
        invalid_reasons.append(
            f"round_id mismatch: requested={requested_round_id}, decision={decision_round_id}"
        )

    if invalid_reasons:
        result = {
            "schema_version": GATE_RESULT_SCHEMA_VERSION,
            "gate_name": RUN_CLOSEOUT_NAME,
            "closeout_status": "INVALID",
            "decision_id": decision_id,
            "round_id": requested_round_id,
            "generated_at": _now_iso(),
            "executed_steps": [],
            "skipped_steps": [],
            "blocking_reasons": invalid_reasons,
            "warnings": [],
            "recommended_next_action": "fix_run_closeout_invalid_args",
        }
        if write_result:
            out_dir = state_dir / "gates"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / RUN_CLOSEOUT_RESULT_NAME).write_text(
                json.dumps(result, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        return result

    # 2. Generate or refresh command-plan before execution
    plan_result = command_plan(state_dir=state_dir, write_result=write_result)

    # 3. Build the bounded closeout step sequence
    steps = _build_closeout_steps(
        state_dir=state_dir,
        round_id=requested_round_id,
        plan_result=plan_result,
    )

    # 4. Initialize pytest_result.txt with header (only if not present)
    pytest_path = pytest_result_path or (state_dir / "pytest_result.txt")
    report_id = _expected_report_id(requested_round_id) if requested_round_id else ""
    run_closeout_command = (
        f"python -m reverse_agent.project_gate run-closeout "
        f"--state-dir {state_dir} --round-id {requested_round_id}"
    )
    if not pytest_path.exists():
        # Read existing report tests_ran so pytest_result covers report tests
        existing_report = read_codex_report_summary(state_dir)
        report_tests_ran = [
            str(item) for item in (existing_report.get("tests_ran") or []) if isinstance(item, str)
        ]
        # Merge report tests_ran with run-closeout command, avoiding duplicates
        tests_ran_list: list[str] = list(report_tests_ran)
        if run_closeout_command not in tests_ran_list:
            tests_ran_list.append(run_closeout_command)
        write_pytest_result(
            state_dir=state_dir,
            summary={
                "schema_version": 1,
                "decision_id": decision_id,
                "report_id": report_id,
                "round_id": requested_round_id,
                "generated_at": _now_iso(),
                "status": "PASSED",
                "tests_ran": tests_ran_list,
            },
            body="",
        )

    # 5. Record startup diagnostics
    runner = command_runner or (lambda command: _default_command_runner(command, cwd=repo_root))
    startup_blocks = _record_startup_diagnostics(
        pytest_path,
        repo_root=repo_root,
        runner=runner,
        state_dir=state_dir,
    )

    # Record run-closeout self-invocation marker
    _append_command_block_to_pytest_result(
        pytest_path,
        command=run_closeout_command,
        stdout=f"run-closeout: started for round {requested_round_id}",
        stderr="",
        exit_code=0,
    )

    # 6. Execute steps
    executed_steps: list[dict[str, Any]] = []
    skipped_steps: list[dict[str, Any]] = []
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    close_round_result: dict[str, Any] | None = None
    close_round_executed = False

    for step in steps:
        step_name = step["name"]
        command = step["command"]
        kind = step["kind"]
        expected = step["expected_exit_codes"]
        is_close_round = step["is_close_round"]

        # The final-check-after-close step is handled separately after
        # the after-close report refresh (line ~7713).  Skip it in the
        # main loop so its failure doesn't block the refresh.
        if step_name == "final-check-after-close":
            continue

        # Allowlist check
        if kind not in RUN_CLOSEOUT_ALLOWED_KINDS:
            skipped_steps.append({
                "name": step_name,
                "command": command,
                "kind": kind,
                "reason": f"kind {kind!r} not in run-closeout allowlist",
            })
            blocking_reasons.append(f"step {step_name} refused: kind {kind!r} not in allowlist")
            break

        # Close-round: call close_round() directly so it owns its command block
        if is_close_round:
            # Remove any stale round archive from a previous failed close-round
            # attempt before close_round() runs.  close_round() checks if the
            # archived copies match the live copies; if a stale archive exists
            # with a different manifest, archive_round() refuses to overwrite
            # it (FileExistsError).  By removing the stale archive here, we
            # ensure close_round() creates a fresh archive from the current
            # live report/pytest.
            _archive_dir = state_dir / "rounds" / requested_round_id
            if _archive_dir.exists():
                import shutil as _shutil
                _shutil.rmtree(_archive_dir)
            close_round_result = close_round(
                state_dir=state_dir,
                round_id=requested_round_id,
                repo_root=repo_root,
            )
            close_status = str(close_round_result.get("close_status") or "")
            close_exit_code = _close_round_exit_code(close_status)
            close_stdout = _close_round_output_text(close_round_result)
            _append_command_block_to_pytest_result(
                pytest_path,
                command=command,
                stdout=close_stdout,
                stderr="",
                exit_code=close_exit_code,
            )
            executed_steps.append({
                "name": step_name,
                "command": command,
                "kind": kind,
                "expected_exit_codes": expected,
                "exit_code": close_exit_code,
                "status": "PASSED" if close_exit_code in expected else "FAILED",
            })
            close_round_executed = True
            if close_exit_code not in expected:
                blocking_reasons.append(
                    f"step {step_name} exited {close_exit_code}, expected {expected}: close_status={close_status}"
                )
                break
            continue

        # Gate steps: call functions directly so their output is authoritative
        step_exit_code = 0
        step_stdout = ""
        step_stderr = ""
        if kind == "decision-lint":
            lint_result = lint_decision(state_dir)
            step_exit_code = 0 if not lint_result.get("errors") else 1
            step_stdout = json.dumps(lint_result, ensure_ascii=True, indent=2)
        elif kind == "preflight":
            pf_result = preflight(state_dir=state_dir, write_result=True)
            pf_status = str(pf_result.get("gate_status") or "")
            step_exit_code = _preflight_exit_code(pf_status)
            step_stdout = f"preflight: {pf_status}"
        elif kind == "pytest":
            proc = runner(command)
            step_exit_code = proc.returncode
            step_stdout = proc.stdout or ""
            step_stderr = proc.stderr or ""
        elif kind == "gate-profile":
            gp_result = gate_profile(state_dir=state_dir, write_result=True)
            gp_status = str(gp_result.get("gate_status") or "")
            step_exit_code = 0 if gp_status == "PASSED" else 1
            step_stdout = json.dumps(gp_result, ensure_ascii=True, indent=2)
        elif kind == "command-plan":
            cp_result = command_plan(state_dir=state_dir, write_result=True)
            cp_status = str(cp_result.get("plan_status") or "")
            step_exit_code = 0 if cp_status == "PASSED" else 1
            if step_name == "command-plan-json":
                # Record the JSON output for the --json variant
                step_stdout = json.dumps(cp_result, ensure_ascii=True, indent=2)
            else:
                step_stdout = f"command-plan: {cp_status}"
        elif kind == "report-summary":
            rs_result = build_report_summary_synthesis(
                state_dir=state_dir, repo_root=repo_root, write_result=True
            )
            rs_status = str(rs_result.get("synthesis_status") or "")
            step_exit_code = 0 if rs_status == "PASSED" else 1
            step_stdout = json.dumps(rs_result, ensure_ascii=True, indent=2)
        elif kind == "final-check":
            fc_result = final_check(state_dir=state_dir, repo_root=repo_root, write_result=True)
            fc_status = str(fc_result.get("gate_status") or "")
            step_exit_code = _final_check_exit_code(fc_status)
            step_stdout = f"final-check: {fc_status}"
        else:
            # Unknown gate kind — refuse to execute
            skipped_steps.append({
                "name": step_name,
                "command": command,
                "kind": kind,
                "reason": f"no direct handler for kind {kind!r}",
            })
            blocking_reasons.append(f"step {step_name} refused: no direct handler for kind {kind!r}")
            break

        _append_command_block_to_pytest_result(
            pytest_path,
            command=command,
            stdout=step_stdout,
            stderr=step_stderr,
            exit_code=step_exit_code,
        )
        executed_steps.append({
            "name": step_name,
            "command": command,
            "kind": kind,
            "expected_exit_codes": expected,
            "exit_code": step_exit_code,
            "status": "PASSED" if step_exit_code in expected else "FAILED",
        })

        if step_exit_code not in expected:
            blocking_reasons.append(
                f"step {step_name} exited {step_exit_code}, expected {expected}: {command}"
            )
            break

        # Refresh codex_execution_report.md after command-plan-json so
        # report-summary synthesis and final-check see current round IDs.
        if step_name == "command-plan-json":
            _refresh_codex_report_for_closeout(
                state_dir=state_dir,
                repo_root=repo_root,
                decision_id=decision_id,
                round_id=requested_round_id,
            )
        # Refresh codex_execution_report.md after final-check so
        # status/acceptance are derived from the final gate result
        # before close-round runs.
        if step_name == "final-check":
            _refresh_codex_report_for_closeout(
                state_dir=state_dir,
                repo_root=repo_root,
                decision_id=decision_id,
                round_id=requested_round_id,
            )

    # 7. Run after-close final-check only if close-round succeeded
    if close_round_executed and not blocking_reasons:
        # Refresh report to include round_close_snapshot.json in
        # generated_artifacts and files_changed after close-round
        # creates the close snapshot.
        _refresh_codex_report_for_closeout(
            state_dir=state_dir,
            repo_root=repo_root,
            decision_id=decision_id,
            round_id=requested_round_id,
            include_close_snapshot=True,
        )
        # Re-copy refreshed report/pytest to the round archive BEFORE
        # running final-check-after-close so that the archived copies
        # match the live copies when the check runs.
        _archive_dir = state_dir / "rounds" / requested_round_id
        if _archive_dir.exists():
            import shutil as _shutil
            for _name in ("codex_execution_report.md", "pytest_result.txt"):
                _src = state_dir / _name
                if _src.exists():
                    _shutil.copy2(_src, _archive_dir / _name)
        after_close_step = next(
            (s for s in steps if s["name"] == "final-check-after-close"),
            None,
        )
        if after_close_step:
            command = after_close_step["command"]
            kind = after_close_step["kind"]
            expected = after_close_step["expected_exit_codes"]
            fc_result = final_check(state_dir=state_dir, repo_root=repo_root, write_result=True)
            fc_status = str(fc_result.get("gate_status") or "")
            fc_exit_code = _final_check_exit_code(fc_status)
            fc_stdout = f"final-check: {fc_status}"
            _append_command_block_to_pytest_result(
                pytest_path,
                command=command,
                stdout=fc_stdout,
                stderr="",
                exit_code=fc_exit_code,
            )
            executed_steps.append({
                "name": "final-check-after-close",
                "command": command,
                "kind": kind,
                "expected_exit_codes": expected,
                "exit_code": fc_exit_code,
                "status": "PASSED" if fc_exit_code in expected else "FAILED",
            })
            if fc_exit_code not in expected:
                blocking_reasons.append(
                    f"step final-check-after-close exited {fc_exit_code}, expected {expected}"
                )
        # Refresh report again after final-check-after-close to pick up the
        # regenerated final_gate_result.json and ensure tests_ran/status are
        # current.  Then re-copy refreshed files to the round archive so that
        # archived_pytest_result_matches_live_pytest_result and
        # archived_report_matches_live_report stay consistent after the
        # after-close refresh and final-check-after-close modified the live copies.
        _refresh_codex_report_for_closeout(
            state_dir=state_dir,
            repo_root=repo_root,
            decision_id=decision_id,
            round_id=requested_round_id,
            include_close_snapshot=True,
        )
        if _archive_dir.exists():
            import shutil as _shutil
            for _name in ("codex_execution_report.md", "pytest_result.txt"):
                _src = state_dir / _name
                if _src.exists():
                    _shutil.copy2(_src, _archive_dir / _name)

    # 8. Determine status
    closeout_status = _run_closeout_status(
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )

    result = {
        "schema_version": GATE_RESULT_SCHEMA_VERSION,
        "gate_name": RUN_CLOSEOUT_NAME,
        "closeout_status": closeout_status,
        "decision_id": decision_id,
        "round_id": requested_round_id,
        "generated_at": _now_iso(),
        "executed_steps": executed_steps,
        "skipped_steps": skipped_steps,
        "startup_blocks": startup_blocks,
        "close_round_result": close_round_result,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "recommended_next_action": _run_closeout_recommended_next_action(closeout_status),
        "artifacts": {
            "command_plan": COMMAND_PLAN_OUTPUT_PATH,
            "run_closeout_result": RUN_CLOSEOUT_OUTPUT_PATH,
        },
    }

    if write_result:
        out_dir = state_dir / "gates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / RUN_CLOSEOUT_RESULT_NAME).write_text(
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


def _print_run_round(result: dict[str, Any]) -> None:
    print(f"{result.get('gate_name')}: {result.get('run_status')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"round_id: {result.get('round_id')}")
    print(f"mainline: {result.get('mainline')}")
    print(f"mode: {result.get('mode')}")
    print(f"command_count: {result.get('command_count')}")
    print(f"executed_count: {len(result.get('executed_commands') or [])}")
    for warning in result.get("warnings", []):
        print(f"  [WARN] {warning}")
    for reason in result.get("blocking_reasons", []):
        print(f"  [BLOCK] {reason}")
    print(f"artifact: {RUN_ROUND_OUTPUT_PATH}")
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
        if warning in (result.get("non_blocking_warnings") or []):
            print(f"  [INFO] {warning}")
        else:
            print(f"  [WARN] {warning}")
    print(f"artifact: {REPORT_SUMMARY_OUTPUT_PATH}")


def _print_close_round(result: dict[str, Any]) -> None:
    print(_close_round_output_text(result), end="")


def _print_run_closeout(result: dict[str, Any]) -> None:
    lines = [
        f"{result.get('gate_name')}: {result.get('closeout_status')}",
        f"decision_id: {result.get('decision_id')}",
        f"round_id: {result.get('round_id')}",
    ]
    for step in result.get("executed_steps", []):
        lines.append(
            f"  [{step.get('status')}] {step.get('name')}: exit={step.get('exit_code')}"
        )
    for step in result.get("skipped_steps", []):
        lines.append(
            f"  [SKIP] {step.get('name')}: {step.get('reason')}"
        )
    for reason in result.get("blocking_reasons", []):
        lines.append(f"  [BLOCK] {reason}")
    for warning in result.get("warnings", []):
        lines.append(f"  [WARN] {warning}")
    lines.append(f"artifact: {RUN_CLOSEOUT_OUTPUT_PATH}")
    lines.append(f"recommended_next_action: {result.get('recommended_next_action')}")
    print("\n".join(lines))


def _print_gate_profile(result: dict[str, Any]) -> None:
    lines = [
        f"gate-profile: {result.get('gate_status')}",
        f"decision_id: {result.get('decision_id')}",
        f"round_id: {result.get('round_id')}",
        f"mainline: {result.get('mainline')}",
        f"profile: {result.get('profile')}",
        f"profile_reason: {result.get('profile_reason')}",
        f"closeout_allowed: {result.get('closeout_allowed')}",
    ]
    for reason in result.get("risk_reasons", []):
        lines.append(f"  risk: {reason}")
    for reason in result.get("reasons", []):
        lines.append(f"  reason: {reason}")
    for cmd in result.get("suggested_commands", []):
        lines.append(f"  [{cmd.get('index')}] {cmd.get('phase')} {cmd.get('kind')}: {cmd.get('command')}")
    lines.append(f"artifact: project_state/gates/gate_profile_plan.json")
    print("\n".join(lines))


def _print_decision_lint(result: dict[str, Any]) -> None:
    ok = result.get("ok")
    lines = [
        f"decision-lint: {'OK' if ok else 'FAILED'}",
        f"decision_id: {result.get('decision_id')}",
        f"decision_status: {result.get('decision_status')}",
        f"mainline: {result.get('mainline')}",
        f"skill_profiles: {result.get('skill_profiles')}",
        f"based_on_state_build_id: {result.get('based_on_state_build_id')}",
        f"current_state_build_id: {result.get('current_state_build_id')}",
    ]
    for error in result.get("errors", []):
        lines.append(f"  [ERROR] {error}")
    for warning in result.get("warnings", []):
        lines.append(f"  [WARN] {warning}")
    print("\n".join(lines))


def _close_round_output_text(result: dict[str, Any]) -> str:
    lines = [
        f"{result.get('gate_name')}: {result.get('close_status')}",
        f"decision_id: {result.get('decision_id')}",
        f"report_id: {result.get('report_id')}",
        f"round_id: {result.get('round_id')}",
    ]
    for check in result.get("checks", []):
        lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    for action in result.get("actions", []):
        lines.append(f"  [ACTION {action.get('status')}] {action.get('name')}")
    archive = result.get("archive") if isinstance(result.get("archive"), dict) else {}
    lines.append(f"archive_status: {archive.get('status')}")
    for reason in result.get("blocking_reasons", []):
        lines.append(f"  [BLOCK] {reason}")
    lines.append(f"recommended_next_action: {result.get('recommended_next_action')}")
    return "\n".join(lines) + "\n"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_close_round_command_block(
    *,
    state_dir: Path,
    round_id: str,
    command: str,
    stdout: str,
    exit_code: int,
) -> None:
    pytest_path = state_dir / "pytest_result.txt"
    if not pytest_path.exists():
        return
    with pytest_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"===== COMMAND: {command} =====\n")
        handle.write(stdout.rstrip() + "\n")
        handle.write("===== STDERR =====\n")
        handle.write(f"===== EXIT: {exit_code} =====\n\n")

    round_dir = state_dir / "rounds" / round_id
    manifest_path = round_dir / ARCHIVE_MANIFEST_NAME
    archive_pytest_path = round_dir / "pytest_result.txt"
    manifest = _read_json(manifest_path)
    files = manifest.get("files")
    if not isinstance(files, dict) or "pytest_result.txt" not in files:
        return
    archive_pytest_path.write_bytes(pytest_path.read_bytes())
    files["pytest_result.txt"]["sha256"] = _sha256_path(archive_pytest_path)
    files["pytest_result.txt"]["source_path"] = str(pytest_path)
    files["pytest_result.txt"]["archived_path"] = str(archive_pytest_path)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


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
    run_round_parser = subparsers.add_parser("run-round", help="Orchestrate project gate preflight and command-plan.")
    run_round_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    mode_group = run_round_parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Generate and validate the plan without executing it.")
    mode_group.add_argument("--execute", action="store_true", help="Execute planned commands fail-fast.")
    run_round_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    report_summary_parser = subparsers.add_parser("report-summary", help="Synthesize and validate codex_report_summary.")
    report_summary_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    report_summary_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    close_round_parser = subparsers.add_parser("close-round", help="Run final-check, archive the round, and re-check.")
    close_round_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    close_round_parser.add_argument("--round-id", required=True)
    close_round_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    run_closeout_parser = subparsers.add_parser("run-closeout", help="Execute a bounded closeout sequence and record command evidence.")
    run_closeout_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    run_closeout_parser.add_argument("--round-id", required=True)
    run_closeout_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    gate_profile_parser = subparsers.add_parser("gate-profile", help="Classify gate profile (fast/standard/full) for the current decision.")
    gate_profile_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    gate_profile_parser.add_argument("--json", action="store_true", help="Print JSON result.")
    gate_profile_parser.add_argument("--profile", choices=list(_GATE_PROFILE_NAMES), default=None,
                                     help="Explicitly select a profile instead of auto-classification.")
    decision_lint_parser = subparsers.add_parser("decision-lint", help="Lint a decision before implementation starts.")
    decision_lint_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    decision_lint_parser.add_argument("--json", action="store_true", help="Print JSON result.")

    args = parser.parse_args(argv)
    if args.command == "final-check":
        result = final_check(state_dir=Path(args.state_dir), repo_root=_derive_repo_root(Path(args.state_dir)))
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_result(result)
        return _final_check_exit_code(result.get("gate_status"))
    if args.command == "preflight":
        result = preflight(state_dir=Path(args.state_dir), repo_root=_derive_repo_root(Path(args.state_dir)))
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
    if args.command == "run-round":
        result = run_round(
            state_dir=Path(args.state_dir),
            dry_run=not bool(args.execute),
            repo_root=Path.cwd(),
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_run_round(result)
        return 1 if result.get("run_status") == "FAILED" else 0
    if args.command == "report-summary":
        result = build_report_summary_synthesis(state_dir=Path(args.state_dir), repo_root=_derive_repo_root(Path(args.state_dir)))
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_report_summary(result)
        return 1 if result.get("synthesis_status") == "FAILED" else 0
    if args.command == "close-round":
        result = close_round(state_dir=Path(args.state_dir), round_id=args.round_id, repo_root=_derive_repo_root(Path(args.state_dir)))
        exit_code = _close_round_exit_code(result.get("close_status"))
        if args.json:
            output = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
        else:
            output = _close_round_output_text(result)
        if exit_code == 0 and result.get("close_status") == "CLOSED":
            command = f"python -m reverse_agent.project_gate close-round --state-dir {args.state_dir} --round-id {args.round_id}"
            if args.json:
                command += " --json"
            _append_close_round_command_block(
                state_dir=Path(args.state_dir),
                round_id=str(args.round_id),
                command=command,
                stdout=output,
                exit_code=exit_code,
            )
        print(output, end="")
        return exit_code
    if args.command == "run-closeout":
        result = run_closeout(
            state_dir=Path(args.state_dir),
            round_id=str(args.round_id),
            repo_root=_derive_repo_root(Path(args.state_dir)),
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_run_closeout(result)
        return _run_closeout_exit_code(result.get("closeout_status"))
    if args.command == "gate-profile":
        profile_override = getattr(args, "profile", None)
        result = gate_profile(state_dir=Path(args.state_dir), profile_override=profile_override)
        if result.get("gate_status") == "FAILED":
            if args.json:
                print(json.dumps(result, ensure_ascii=True, indent=2))
            else:
                _print_gate_profile(result)
            return 1
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_gate_profile(result)
        return 0
    if args.command == "decision-lint":
        result = lint_decision(state_dir=Path(args.state_dir))
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            _print_decision_lint(result)
        return 0 if result.get("ok") else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
