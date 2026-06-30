"""Local non-executing AgentRunner dry-run artifact builder."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_jobs import (
    planned_job_artifact_path,
    planned_job_id_for_round,
    validate_job_payload,
    validate_job_transition,
)
from .project_runner_contract import (
    load_command_plan,
    validate_runner_contract_payload,
)
from .project_state import read_decision_meta


SCHEMA_VERSION = 1
GATE_NAME = "agent-runner-dry-run"
ARTIFACT_NAME = "agent_runner_dry_run_result.json"
ARTIFACT_PATH = f"project_state/gates/{ARTIFACT_NAME}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm_path(value: object) -> str:
    return str(value or "").replace("\\", "/").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _command_texts(commands: object) -> list[str]:
    if not isinstance(commands, list):
        return []
    result: list[str] = []
    for command in commands:
        if isinstance(command, Mapping):
            text = str(command.get("command") or "").strip()
            if text:
                result.append(text)
    return result


def _external_invocation_enabled(payload: Mapping[str, Any]) -> list[str]:
    external = payload.get("external_invocations")
    if not isinstance(external, Mapping):
        return []
    return sorted(str(key) for key, value in external.items() if value is not False)


def _build_lifecycle_preview(job_payload: Mapping[str, Any]) -> dict[str, Any]:
    current = str(job_payload.get("status") or "").strip().upper()
    target = "READY" if current == "DRAFT" else current
    transition = validate_job_transition(current, target) if target != current else {
        "validation_status": "PASSED",
        "errors": [],
        "from_status": current,
        "to_status": target,
        "allowed_to": [],
        "terminal_from_status": False,
    }
    return {
        "current_job_status": current,
        "proposed_job_status": target,
        "local_dry_run_state": "DRY_RUN_PLANNED",
        "state_is_evidence_only": True,
        "job_status_mutated": False,
        "transition_validation": transition,
    }


def build_agent_runner_dry_run(
    *,
    state_dir: str | Path,
    repo_root: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    """Build a deterministic dry-run preview without dispatching or executing commands."""

    state_dir_path = Path(state_dir)
    repo_root_path = Path(repo_root) if repo_root is not None else state_dir_path.parent
    gates_dir = state_dir_path / "gates"
    decision = read_decision_meta(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    expected_job_id = planned_job_id_for_round(round_id)
    job_artifact_path = planned_job_artifact_path(expected_job_id)

    job_payload = _read_json(repo_root_path / job_artifact_path)
    command_plan = load_command_plan(state_dir_path)
    runner_contract = _read_json(gates_dir / "runner_contract_result.json")

    errors: list[str] = []
    warnings: list[str] = []
    if not job_payload:
        errors.append("job artifact missing or invalid")
    if not command_plan:
        errors.append("command_plan artifact missing or invalid")
    if not runner_contract:
        errors.append("runner_contract artifact missing or invalid")

    for label, payload in (
        ("job", job_payload),
        ("command_plan", command_plan),
        ("runner_contract", runner_contract),
    ):
        if payload:
            if str(payload.get("decision_id") or "") != decision_id:
                errors.append(f"{label} decision_id mismatch")
            if str(payload.get("round_id") or "") != round_id:
                errors.append(f"{label} round_id mismatch")

    job_validation = validate_job_payload(job_payload) if job_payload else {
        "validation_status": "FAILED",
        "errors": ["job artifact unavailable"],
    }
    if job_validation.get("validation_status") != "PASSED":
        errors.extend(f"job: {error}" for error in job_validation.get("errors") or [])

    contract_validation = validate_runner_contract_payload(
        runner_contract,
        command_plan_payload=command_plan,
        job_payload=job_payload,
    ) if runner_contract and command_plan and job_payload else {
        "validation_status": "FAILED",
        "errors": ["runner contract validation inputs unavailable"],
    }
    if contract_validation.get("validation_status") != "PASSED":
        errors.extend(
            f"runner_contract: {error}"
            for error in contract_validation.get("errors") or []
        )

    if runner_contract.get("dispatch_enabled") is not False:
        errors.append("runner_contract dispatch_enabled must be false")
    if runner_contract.get("executable") is not False:
        errors.append("runner_contract executable must be false")
    enabled_external = _external_invocation_enabled(runner_contract)
    if enabled_external:
        errors.append(f"runner_contract external invocations enabled: {enabled_external}")

    allowed_commands = runner_contract.get("allowed_commands")
    if not isinstance(allowed_commands, list):
        allowed_commands = []
    forbidden_commands = runner_contract.get("forbidden_commands")
    if not isinstance(forbidden_commands, list):
        forbidden_commands = []
    omitted_commands = command_plan.get("omitted_commands")
    if not isinstance(omitted_commands, list):
        omitted_commands = []
    allowed_write_paths = runner_contract.get("allowed_write_paths")
    if not isinstance(allowed_write_paths, list):
        allowed_write_paths = []

    status = "FAILED" if errors else "PASSED"
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_name": ARTIFACT_NAME,
        "gate_name": GATE_NAME,
        "gate_status": status,
        "dry_run_status": status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "artifact_path": ARTIFACT_PATH,
        "repo_root": _norm_path(repo_root_path),
        "inputs_consumed": {
            "decision_packet": "project_state/decision_packet.md",
            "job_artifact": job_artifact_path,
            "command_plan": "project_state/gates/command_plan.json",
            "runner_contract": "project_state/gates/runner_contract_result.json",
        },
        "input_validation": {
            "job_validation_status": job_validation.get("validation_status"),
            "runner_contract_validation_status": contract_validation.get("validation_status"),
            "command_plan_status": command_plan.get("plan_status") if command_plan else "MISSING",
        },
        "execution_preview": {
            "planned_command_count": len(allowed_commands),
            "planned_commands": allowed_commands,
            "planned_command_texts": _command_texts(allowed_commands),
            "forbidden_command_count": len(forbidden_commands),
            "forbidden_commands": forbidden_commands,
            "omitted_command_count": len(omitted_commands),
            "omitted_commands": omitted_commands,
            "allowed_write_paths": [_norm_path(path) for path in allowed_write_paths],
        },
        "non_execution_proof": {
            "commands_executed": False,
            "subprocess_spawned": False,
            "external_runner_invoked": False,
            "model_api_called": False,
            "github_actions_triggered": False,
            "remote_mutation": False,
            "dispatch_enabled": False,
            "executable": False,
            "reason": "local AgentRunner dry-run previews the handoff only",
        },
        "lifecycle_preview": _build_lifecycle_preview(job_payload) if job_payload else {},
        "dispatch_policy": {
            "can_dispatch": False,
            "real_dispatch_readiness": False,
            "local_dry_run_readiness": status == "PASSED",
        },
        "errors": errors,
        "warnings": warnings,
        "generated_artifacts": [ARTIFACT_PATH],
    }
    if write_result:
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / ARTIFACT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
