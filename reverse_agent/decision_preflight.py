"""Local decision-preflight validation without dispatching runners."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .post_final_evidence_sync import POST_FINAL_EVIDENCE_SYNC_RESULT_NAME
from .project_jobs import planned_job_id_for_round, validate_jobs_dir
from .project_state import read_decision_contract, read_decision_meta


DECISION_PREFLIGHT_RESULT_NAME = "decision_preflight_result.json"
DECISION_PREFLIGHT_WORKFLOW_READINESS_NAME = "decision_preflight_workflow_readiness.json"
DECISION_PREFLIGHT_OUTPUT_PATH = f"project_state/gates/{DECISION_PREFLIGHT_RESULT_NAME}"
DECISION_PREFLIGHT_WORKFLOW_READINESS_OUTPUT_PATH = (
    f"project_state/gates/{DECISION_PREFLIGHT_WORKFLOW_READINESS_NAME}"
)


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _registry_active_skill_profiles(repo_root: Path) -> set[str]:
    registry = _read_json(repo_root / ".codex-skills" / "registry.json")
    active: set[str] = set()
    skills = registry.get("skills")
    if isinstance(skills, Mapping):
        for name, entry in skills.items():
            if not isinstance(entry, Mapping):
                continue
            version = str(entry.get("version") or "")
            status = str(entry.get("status") or "").lower()
            if name and version and status == "active":
                active.add(f"{name}@v{version}")
                active.add(f"{name}@{version}")
    for entry in skills or registry.get("skill_profiles") or []:
        if not isinstance(entry, Mapping):
            continue
        name = str(entry.get("name") or entry.get("skill") or "")
        version = str(entry.get("version") or "")
        status = str(entry.get("status") or "").lower()
        if name and version and status == "active":
            active.add(f"{name}@v{version}")
            active.add(f"{name}@{version}")
    if not active:
        # Current registry format is object keyed by skill id.
        for name, entry in registry.items():
            if not isinstance(entry, Mapping):
                continue
            version = str(entry.get("version") or "")
            status = str(entry.get("status") or "").lower()
            if name and version and status == "active":
                active.add(f"{name}@{version}")
    return active


def _workflow_readiness(repo_root: Path) -> dict[str, Any]:
    workflow_rel = ".github/workflows/decision-preflight.yml"
    state_gate_rel = ".github/workflows/state-gate.yml"
    workflow_text = _read_text(repo_root / workflow_rel)
    state_gate_text = _read_text(repo_root / state_gate_rel)
    required_snippets = [
        "permissions:",
        "contents: read",
        "python -m reverse_agent.project_gate decision-preflight --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    ]
    state_gate_required = [
        "python -m reverse_agent.project_gate decision-preflight --state-dir project_state",
    ]
    forbidden = [
        "git push",
        "gh pr create",
        "gh pr merge",
        "openai",
        "chatgpt",
        "execute-decision",
        "run-closeout",
        "archive-round",
        "self-hosted",
        "project_state build",
        "solve_reports",
        "samplereverse.exe",
    ]
    lowered = "\n".join([workflow_text, state_gate_text]).lower()
    missing = [snippet for snippet in required_snippets if snippet not in workflow_text]
    missing_state_gate = [snippet for snippet in state_gate_required if snippet not in state_gate_text]
    forbidden_hits = [item for item in forbidden if item in lowered]
    return {
        "workflow_path": workflow_rel,
        "workflow_exists": bool(workflow_text),
        "state_gate_path": state_gate_rel,
        "state_gate_exists": bool(state_gate_text),
        "missing_workflow_snippets": missing,
        "missing_state_gate_snippets": missing_state_gate,
        "forbidden_hits": forbidden_hits,
        "readiness_status": "READY" if not missing and not missing_state_gate and not forbidden_hits else "REWORK_REQUIRED",
        "read_only": True,
        "dispatch_enabled": False,
        "remote_mutation": False,
    }


def build_decision_preflight_result(
    *,
    state_dir: str | Path = "project_state",
    repo_root: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    repo_root_path = Path(repo_root) if repo_root is not None else state_dir_path.parent
    decision = read_decision_meta(state_dir_path)
    contract = read_decision_contract(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    report_id = f"codex_report_{round_id.removeprefix('round_')}" if round_id else ""

    errors: list[str] = []
    warnings: list[str] = []
    if decision.get("status") != "APPROVED":
        errors.append("decision status is not APPROVED")
    if decision.get("mainline") != "engineering_branch":
        errors.append("decision mainline is not engineering_branch")

    active_profiles = _registry_active_skill_profiles(repo_root_path)
    requested_profiles = [str(item) for item in decision.get("skill_profiles") or []]
    missing_profiles = [item for item in requested_profiles if item not in active_profiles]
    if missing_profiles:
        errors.append("skill_profiles missing from active registry: " + ", ".join(missing_profiles))

    command_plan = _read_json(state_dir_path / "gates" / "command_plan.json")
    if not command_plan:
        errors.append("command_plan.json is missing")
    elif (
        str(command_plan.get("decision_id") or "") != decision_id
        or str(command_plan.get("round_id") or "") != round_id
        or str(command_plan.get("plan_status") or "") != "PASSED"
    ):
        errors.append("command_plan.json is stale or not PASSED")

    sync_payload = _read_json(state_dir_path / "gates" / POST_FINAL_EVIDENCE_SYNC_RESULT_NAME)
    sync_current = (
        str(sync_payload.get("decision_id") or "") == decision_id
        and str(sync_payload.get("round_id") or "") == round_id
    )
    if not sync_current:
        errors.append("post_final_evidence_sync_result.json is missing or stale")
    elif str(sync_payload.get("gate_status") or "") != "PASSED":
        errors.append("post-final evidence sync gate is not PASSED")

    job_validation = validate_jobs_dir(state_dir_path)
    expected_job_id = planned_job_id_for_round(round_id)
    current_jobs = [
        job for job in job_validation.get("jobs") or []
        if isinstance(job, Mapping)
        and job.get("job_id") == expected_job_id
        and job.get("decision_id") == decision_id
        and job.get("round_id") == round_id
    ]
    if job_validation.get("validation_status") != "PASSED":
        errors.append("jobs directory validation failed")
    if not current_jobs:
        errors.append("current READY job artifact is missing")
    elif str(current_jobs[0].get("status") or "") != "READY":
        errors.append("current job status is not READY")

    workflow = _workflow_readiness(repo_root_path)
    if workflow["readiness_status"] != "READY":
        errors.append("decision-preflight workflow readiness is not READY")

    forbidden = set(contract.get("forbidden_capabilities_this_round") or [])
    forbidden_ok = {
        "runner_dispatch": "automatic_runner_dispatch" in forbidden or "manual_runner_dispatch" in forbidden,
        "model_api": "model_api_invocation" in forbidden,
        "workflow_dispatch_trigger": "workflow_dispatch_trigger" in forbidden,
        "sample_solving": "real_sample_analysis_execution" in forbidden,
        "database_creation": "sqlite_database_creation" in forbidden,
    }
    if not all(forbidden_ok.values()):
        warnings.append("decision contract does not explicitly forbid every checked external capability")

    gate_status = "FAILED" if errors else "PASSED"
    result = {
        "schema_version": 1,
        "artifact_name": DECISION_PREFLIGHT_RESULT_NAME,
        "gate_name": "decision-preflight",
        "gate_status": gate_status,
        "preflight_status": gate_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": _now_iso(),
        "decision_status": decision.get("status"),
        "mainline": decision.get("mainline"),
        "requested_skill_profiles": requested_profiles,
        "active_skill_profiles": sorted(active_profiles),
        "command_plan_status": command_plan.get("plan_status"),
        "post_final_sync_status": sync_payload.get("gate_status"),
        "job_validation_status": job_validation.get("validation_status"),
        "expected_job_id": expected_job_id,
        "current_job_count": len(current_jobs),
        "workflow_readiness_status": workflow["readiness_status"],
        "forbidden_capability_checks": forbidden_ok,
        "non_dispatching": True,
        "runner_dispatch": False,
        "model_api_invocation": False,
        "github_actions_dispatch": False,
        "remote_mutation": False,
        "database_write": False,
        "sample_solving": False,
        "errors": errors,
        "warnings": warnings,
        "generated_artifacts": [
            DECISION_PREFLIGHT_OUTPUT_PATH,
            DECISION_PREFLIGHT_WORKFLOW_READINESS_OUTPUT_PATH,
        ],
    }
    workflow_payload = {
        "schema_version": 1,
        "artifact_name": DECISION_PREFLIGHT_WORKFLOW_READINESS_NAME,
        "gate_name": "decision-preflight-workflow-readiness",
        "gate_status": "PASSED" if workflow["readiness_status"] == "READY" else "FAILED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": result["generated_at"],
        **workflow,
        "generated_artifacts": [DECISION_PREFLIGHT_WORKFLOW_READINESS_OUTPUT_PATH],
    }

    if write_result:
        gates_dir = state_dir_path / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / DECISION_PREFLIGHT_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (gates_dir / DECISION_PREFLIGHT_WORKFLOW_READINESS_NAME).write_text(
            json.dumps(workflow_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def validate_decision_preflight_result(
    payload: Mapping[str, Any],
    *,
    decision_id: str,
    round_id: str,
) -> list[str]:
    errors: list[str] = []
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    if str(payload.get("gate_status") or "") != "PASSED":
        errors.append("gate_status is not PASSED")
    for field in (
        "runner_dispatch",
        "model_api_invocation",
        "github_actions_dispatch",
        "remote_mutation",
        "database_write",
        "sample_solving",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    return errors
