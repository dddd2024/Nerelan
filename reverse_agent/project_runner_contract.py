"""Non-dispatching runner contract builder for future job runners."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .project_jobs import FORBIDDEN_PERMISSION_FLAGS, load_job_file, validate_job_payload
from .project_state import read_decision_meta


RUNNER_CONTRACT_SCHEMA_VERSION = 1
RUNNER_CONTRACT_ARTIFACT_NAME = "runner_contract_result.json"
RUNNER_CONTRACT_ARTIFACT_PATH = f"project_state/gates/{RUNNER_CONTRACT_ARTIFACT_NAME}"
AGENT_RUNNER_DRY_RUN_ARTIFACT_PATH = "project_state/gates/agent_runner_dry_run_result.json"


def _norm_path(value: object) -> str:
    return str(value or "").replace("\\", "/").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _contract_id(round_id: str) -> str:
    text = str(round_id or "").strip()
    if text.startswith("round_"):
        return f"runner_contract_{text[len('round_'):]}"
    return f"runner_contract_{text}" if text else ""


def _command_entries(command_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return []
    entries: list[dict[str, Any]] = []
    for command in commands:
        if not isinstance(command, Mapping):
            continue
        entries.append(
            {
                "index": command.get("index"),
                "kind": str(command.get("kind") or ""),
                "phase": str(command.get("phase") or ""),
                "command": str(command.get("command") or ""),
                "expected_exit_codes": list(command.get("expected_exit_codes") or []),
                "required": bool(command.get("required")),
            }
        )
    return entries


def _omitted_entries(command_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    omitted = command_plan.get("omitted_commands")
    if not isinstance(omitted, list):
        return []
    entries: list[dict[str, Any]] = []
    for command in omitted:
        if not isinstance(command, Mapping):
            continue
        entries.append(
            {
                "kind": str(command.get("kind") or ""),
                "command": str(command.get("command") or ""),
                "reason": str(command.get("reason") or command.get("notes") or ""),
            }
        )
    return entries


def _unsafe_write_path_reason(path: str, *, round_id: str = "") -> str:
    text = _norm_path(path)
    lowered = text.lower()
    if not text:
        return "empty write path"
    if "://" in lowered or lowered.startswith(("http:", "https:", "ssh:", "git:")):
        return "URL or remote write path"
    if lowered.startswith("/") or re_match_windows_abs(text):
        return "absolute write path"
    parts = [part for part in lowered.split("/") if part]
    if ".." in parts:
        return "parent traversal write path"
    forbidden_prefixes = (
        "reverse_agent/",
        "tests/",
        ".github/",
        "docs/prompts/",
        ".codex-skills/",
        "solve_reports/",
    )
    if lowered.startswith(forbidden_prefixes):
        return "source, test, workflow, prompt, skill, or solve_reports write path"
    if lowered in {
        "project_state/codex_execution_report.md",
        "project_state/execution_report.md",
        "project_state/pytest_result.txt",
    }:
        return ""
    if lowered.startswith("project_state/gates/") and lowered.endswith(".json"):
        return ""
    if lowered.startswith("project_state/jobs/") and lowered.endswith(".json"):
        return ""
    round_prefix = f"project_state/rounds/{_norm_path(round_id).lower()}/"
    if round_id and lowered.startswith(round_prefix):
        return ""
    return "write path is outside approved job/gate/report artifacts"


def re_match_windows_abs(path: str) -> bool:
    return len(path) >= 3 and path[1:3] in {":/", ":\\"} and path[0].isalpha()


def load_command_plan(state_dir: str | Path) -> dict[str, Any]:
    return _read_json(Path(state_dir) / "gates" / "command_plan.json")


def build_runner_contract_payload(
    *,
    state_dir: str | Path,
    job_payload: Mapping[str, Any],
    command_plan_payload: Mapping[str, Any] | None = None,
    repo_root: str | Path | None = None,
    job_artifact_path: str = "",
) -> dict[str, Any]:
    """Build a runner-facing contract that cannot dispatch by itself."""

    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    command_plan = dict(command_plan_payload or load_command_plan(state_dir_path))
    commands = _command_entries(command_plan)
    omitted = _omitted_entries(command_plan)
    job_validation = validate_job_payload(job_payload)
    root = Path(repo_root) if repo_root is not None else state_dir_path.parent
    job_outputs = [
        _norm_path(output)
        for output in job_validation.get("required_outputs") or []
        if _norm_path(output)
    ]
    allowed_write_paths = sorted(
        {
            *job_outputs,
            RUNNER_CONTRACT_ARTIFACT_PATH,
            AGENT_RUNNER_DRY_RUN_ARTIFACT_PATH,
            "project_state/gates/job_orchestration_result.json",
            "project_state/gates/control_plane_snapshot.json",
        }
    )
    return {
        "schema_version": RUNNER_CONTRACT_SCHEMA_VERSION,
        "artifact_name": RUNNER_CONTRACT_ARTIFACT_NAME,
        "contract_id": _contract_id(str(decision.get("round_id") or "")),
        "contract_status": "READY",
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": str(decision.get("round_id") or ""),
        "mainline": str(decision.get("mainline") or ""),
        "repo_root": _norm_path(root),
        "task_contract_path": "project_state/decision_packet.md",
        "command_plan_path": "project_state/gates/command_plan.json",
        "job_artifact_path": _norm_path(job_artifact_path),
        "job_id": str(job_payload.get("job_id") or ""),
        "job_validation_status": str(job_validation.get("validation_status") or "FAILED"),
        "dispatch_enabled": False,
        "executable": False,
        "runner": dict(job_validation.get("runner") or {}),
        "permissions": dict(job_validation.get("permissions") or {}),
        "budgets": dict(job_validation.get("budgets") or {}),
        "allowed_commands": commands,
        "forbidden_commands": omitted,
        "allowed_write_paths": allowed_write_paths,
        "external_invocations": {
            "codex_cli": False,
            "trae": False,
            "claude_code": False,
            "aider": False,
            "github_actions": False,
            "model_api": False,
            "remote_mutation": False,
        },
        "policy": {
            "dispatch_policy": "non_dispatching",
            "command_plan_is_authority": True,
            "contract_cannot_broaden_command_plan": True,
            "future_runner_must_revalidate_before_execution": True,
        },
    }


def validate_runner_contract_payload(
    payload: Mapping[str, Any],
    *,
    command_plan_payload: Mapping[str, Any],
    job_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a runner contract without invoking any runner."""

    errors: list[str] = []
    warnings: list[str] = []
    job_validation = validate_job_payload(job_payload)
    command_plan_commands = {
        str(command.get("command") or "")
        for command in _command_entries(command_plan_payload)
        if str(command.get("command") or "")
    }
    omitted_commands = {
        str(command.get("command") or "")
        for command in _omitted_entries(command_plan_payload)
        if str(command.get("command") or "")
    }
    allowed_commands = payload.get("allowed_commands")
    if not isinstance(allowed_commands, list):
        errors.append("allowed_commands must be a list")
        allowed_commands = []
    allowed_command_text = {
        str(command.get("command") or "")
        for command in allowed_commands
        if isinstance(command, Mapping) and str(command.get("command") or "")
    }
    if allowed_command_text - command_plan_commands:
        errors.append("allowed_commands include commands outside command-plan")
    missing_required = sorted(command_plan_commands - allowed_command_text)
    if missing_required:
        errors.append("allowed_commands missing required command-plan commands")
    if allowed_command_text & omitted_commands:
        errors.append("allowed_commands include omitted command-plan commands")
    forbidden_commands = payload.get("forbidden_commands")
    if not isinstance(forbidden_commands, list):
        errors.append("forbidden_commands must be a list")
        forbidden_commands = []
    forbidden_command_text = {
        str(command.get("command") or "")
        for command in forbidden_commands
        if isinstance(command, Mapping) and str(command.get("command") or "")
    }
    missing_forbidden = sorted(omitted_commands - forbidden_command_text)
    if missing_forbidden:
        errors.append("forbidden_commands do not preserve omitted command-plan commands")
    allowed_write_paths = payload.get("allowed_write_paths")
    if not isinstance(allowed_write_paths, list):
        errors.append("allowed_write_paths must be a list")
        allowed_write_paths = []
    unsafe_write_paths = [
        {"path": _norm_path(path), "reason": reason}
        for path in allowed_write_paths
        for reason in [_unsafe_write_path_reason(str(path), round_id=str(payload.get("round_id") or ""))]
        if reason
    ]
    if unsafe_write_paths:
        errors.append("allowed_write_paths include unsafe or out-of-scope paths")
    if str(payload.get("schema_version") or "") != str(RUNNER_CONTRACT_SCHEMA_VERSION):
        errors.append(f"schema_version must be {RUNNER_CONTRACT_SCHEMA_VERSION}")
    if str(payload.get("contract_status") or "") != "READY":
        errors.append("contract_status must be READY")
    if payload.get("dispatch_enabled") is not False:
        errors.append("dispatch_enabled must be false")
    if payload.get("executable") is not False:
        errors.append("executable must be false")
    if str(payload.get("job_id") or "") != str(job_payload.get("job_id") or ""):
        errors.append("job_id mismatch")
    if str(payload.get("job_validation_status") or "") != "PASSED":
        errors.append("job_validation_status is not PASSED")
    if str(job_validation.get("validation_status") or "") != "PASSED":
        errors.extend(f"job: {error}" for error in job_validation.get("errors") or [])
    runner = payload.get("runner") if isinstance(payload.get("runner"), Mapping) else {}
    if runner.get("dispatch_enabled") is not False:
        errors.append("runner.dispatch_enabled must be false")
    permissions = payload.get("permissions") if isinstance(payload.get("permissions"), Mapping) else {}
    for flag in sorted(FORBIDDEN_PERMISSION_FLAGS):
        if permissions.get(flag) is not False:
            errors.append(f"permissions.{flag} must be false")
    external_invocations = (
        payload.get("external_invocations")
        if isinstance(payload.get("external_invocations"), Mapping)
        else {}
    )
    enabled_external = sorted(
        key for key, value in external_invocations.items() if value is not False
    )
    if enabled_external:
        errors.append(f"external invocations must be false: {enabled_external}")
    return {
        "schema_version": RUNNER_CONTRACT_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "warnings": warnings,
        "contract_id": str(payload.get("contract_id") or ""),
        "job_id": str(payload.get("job_id") or ""),
        "dispatch_enabled": False,
        "executable": False,
        "allowed_command_count": len(allowed_command_text),
        "forbidden_command_count": len(omitted_commands),
        "missing_required_commands": missing_required,
        "missing_forbidden_commands": missing_forbidden,
        "unsafe_write_paths": unsafe_write_paths,
    }


def load_job_payload_from_path(path: str | Path) -> dict[str, Any]:
    return load_job_file(path)
