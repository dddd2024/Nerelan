from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .project_state import (
    extract_markdown_json_block,
    parse_pytest_result_header,
    read_decision_meta,
)


SCHEMA_VERSION = 1
GATE_NAME = "control-plane-snapshot"
ARTIFACT_NAME = "control_plane_snapshot.json"
ARTIFACT_PATH = f"project_state/gates/{ARTIFACT_NAME}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm_path(value: object) -> str:
    normalized = str(value or "").replace("\\", "/").strip()
    return normalized[2:] if normalized.startswith("./") else normalized


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


def _read_report_summary(state_dir: Path) -> dict[str, Any]:
    for report_name, block_name in (
        ("execution_report.md", "execution_report_summary"),
        ("codex_execution_report.md", "codex_report_summary"),
    ):
        text = _read_text(state_dir / report_name)
        if not text:
            continue
        payload = extract_markdown_json_block(text, block_name)
        if payload.get("found") and not payload.get("parse_error"):
            return {
                key: value
                for key, value in payload.items()
                if key not in {"found", "parse_error"}
            }
    return {}


def _expected_report_id(round_id: str) -> str:
    if round_id.startswith("round_"):
        return f"codex_report_{round_id[len('round_'):]}"
    return f"codex_report_{round_id}" if round_id else ""


def _status_payload(
    payload: dict[str, Any],
    *,
    expected_decision_id: str,
    expected_round_id: str,
    required: bool,
) -> dict[str, Any]:
    if not payload:
        return {
            "status": "missing_required" if required else "missing_optional",
            "is_current": False,
            "nonblocking": not required,
        }
    actual_decision_id = str(payload.get("decision_id") or "")
    actual_round_id = str(payload.get("round_id") or "")
    mismatches: list[str] = []
    if actual_decision_id and actual_decision_id != expected_decision_id:
        mismatches.append("decision_id mismatch")
    if actual_round_id and actual_round_id != expected_round_id:
        mismatches.append("round_id mismatch")
    if mismatches:
        return {
            "status": "stale_required" if required else "historical_nonblocking",
            "is_current": False,
            "nonblocking": not required,
            "decision_id": actual_decision_id,
            "round_id": actual_round_id,
            "mismatches": mismatches,
        }
    return {
        "status": str(payload.get("gate_status") or payload.get("status") or "present"),
        "is_current": True,
        "nonblocking": False,
        "decision_id": actual_decision_id,
        "round_id": actual_round_id,
    }


def _inventory_entry(
    payload: dict[str, Any],
    *,
    expected_decision_id: str,
    expected_round_id: str,
    required: bool,
    count_field: str,
) -> dict[str, Any]:
    entry = _status_payload(
        payload,
        expected_decision_id=expected_decision_id,
        expected_round_id=expected_round_id,
        required=required,
    )
    entry.update(
        {
            "gate_name": payload.get("gate_name") if payload else "",
            "gate_status": payload.get("gate_status") if payload else "MISSING",
            "inventory_validation_status": payload.get("inventory_validation_status")
            if payload
            else "MISSING",
            count_field: payload.get(count_field, 0) if payload else 0,
            "validated_paths": payload.get("validated_paths") or [] if payload else [],
            "warnings": payload.get("warnings") or [] if payload else [],
        }
    )
    if "dispatch_enabled" in payload:
        entry["dispatch_enabled"] = bool(payload.get("dispatch_enabled"))
        entry["dispatch_safety_status"] = payload.get("dispatch_safety_status")
    return entry


def _append_identity_blockers(
    *,
    label: str,
    payload: dict[str, Any],
    expected_decision_id: str,
    expected_round_id: str,
    expected_report_id: str = "",
) -> list[str]:
    if not payload:
        return [f"{label} artifact missing"]
    blockers: list[str] = []
    actual_decision_id = str(payload.get("decision_id") or "")
    actual_round_id = str(payload.get("round_id") or "")
    actual_report_id = str(payload.get("report_id") or "")
    if actual_decision_id and actual_decision_id != expected_decision_id:
        blockers.append(f"{label} decision_id mismatch")
    if actual_round_id and actual_round_id != expected_round_id:
        blockers.append(f"{label} round_id mismatch")
    if expected_report_id and actual_report_id and actual_report_id != expected_report_id:
        blockers.append(f"{label} report_id mismatch")
    return blockers


_FINAL_STATE_TAIL_FAILURE_CHECKS = {
    "control_plane_snapshot_artifact",
    "execute_decision_contract",
    "execution_log_required_commands_recorded",
    "execution_log_provenance_valid",
    "pytest_result_exit_codes_match_command_plan",
    "status_policy_valid",
}


def _final_gate_failures_are_final_state_tail_only(final_gate: dict[str, Any]) -> bool:
    """Return true when final-check is blocked only by not-yet-written tail evidence."""
    if str(final_gate.get("gate_status") or "") == "PASSED":
        return True
    failed_names: set[str] = set()
    checks = final_gate.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            status = str(check.get("status") or "").upper()
            if status in {"FAIL", "FAILED"}:
                name = str(check.get("name") or "")
                if name:
                    failed_names.add(name)
    if not failed_names:
        for reason in final_gate.get("blocking_reasons") or []:
            reason_text = str(reason or "")
            if ":" in reason_text:
                failed_names.add(reason_text.split(":", 1)[0].strip())
    return bool(failed_names) and failed_names <= _FINAL_STATE_TAIL_FAILURE_CHECKS


def build_control_plane_snapshot(
    *,
    state_dir: Path,
    write_result: bool = True,
    final_state: bool = False,
) -> dict[str, Any]:
    state_dir = Path(state_dir)
    gates_dir = state_dir / "gates"
    decision = read_decision_meta(state_dir)
    report = _read_report_summary(state_dir)
    pytest_header = parse_pytest_result_header(_read_text(state_dir / "pytest_result.txt"))
    command_plan = _read_json(gates_dir / "command_plan.json")
    final_gate = _read_json(gates_dir / "final_gate_result.json")
    closeout = _read_json(gates_dir / "run_closeout_result.json")
    audit_inventory = _read_json(gates_dir / "audit_inventory_result.json")
    jobs_inventory = _read_json(gates_dir / "jobs_inventory_result.json")
    job_orchestration = _read_json(gates_dir / "job_orchestration_result.json")
    runner_contract = _read_json(gates_dir / "runner_contract_result.json")
    agent_runner_dry_run = _read_json(gates_dir / "agent_runner_dry_run_result.json")
    agent_runner_handoff_bundle = _read_json(gates_dir / "agent_runner_handoff_bundle.json")
    agent_runner_handoff_validation = _read_json(gates_dir / "agent_runner_handoff_validation.json")
    execution_log = _read_json(gates_dir / "execution_log.json")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    expected_report_id = _expected_report_id(round_id)
    report_id = str(report.get("report_id") or "")

    consumed_by_matching_report = bool(
        decision_id
        and report.get("based_on_decision_id") == decision_id
        and report.get("round_id") == round_id
    )

    blocking_reasons: list[str] = []
    warnings: list[str] = []
    if not decision_id or str(decision.get("status") or "") != "APPROVED":
        blocking_reasons.append("active decision is missing or not approved")
    blocking_reasons.extend(
        _append_identity_blockers(
            label="report",
            payload=report,
            expected_decision_id=decision_id,
            expected_round_id=round_id,
            expected_report_id=expected_report_id,
        )
    )
    if report and str(report.get("based_on_decision_id") or "") != decision_id:
        blocking_reasons.append("report based_on_decision_id mismatch")
    if not pytest_header.get("found"):
        blocking_reasons.append("pytest_result header missing")
    else:
        if str(pytest_header.get("decision_id") or "") != decision_id:
            blocking_reasons.append("pytest_result decision_id mismatch")
        if str(pytest_header.get("round_id") or "") != round_id:
            blocking_reasons.append("pytest_result round_id mismatch")
        if expected_report_id and str(pytest_header.get("report_id") or "") != expected_report_id:
            blocking_reasons.append("pytest_result report_id mismatch")
    blocking_reasons.extend(
        _append_identity_blockers(
            label="final_gate",
            payload=final_gate,
            expected_decision_id=decision_id,
            expected_round_id=round_id,
            expected_report_id=expected_report_id,
        )
    )
    if command_plan:
        blocking_reasons.extend(
            _append_identity_blockers(
                label="command_plan",
                payload=command_plan,
                expected_decision_id=decision_id,
                expected_round_id=round_id,
            )
        )
    else:
        blocking_reasons.append("command_plan artifact missing")

    audit_entry = _inventory_entry(
        audit_inventory,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
        count_field="audit_count",
    )
    jobs_entry = _inventory_entry(
        jobs_inventory,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
        count_field="job_count",
    )
    job_orchestration_entry = _status_payload(
        job_orchestration,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
    )
    job_orchestration_entry.update(
        {
            "gate_name": job_orchestration.get("gate_name") if job_orchestration else "",
            "gate_status": job_orchestration.get("gate_status") if job_orchestration else "MISSING",
            "job_id": job_orchestration.get("job_id") if job_orchestration else "",
            "job_status": job_orchestration.get("job_status") if job_orchestration else "",
            "job_artifact_path": job_orchestration.get("job_artifact_path")
            if job_orchestration
            else "",
            "dispatch_enabled": bool(job_orchestration.get("dispatch_enabled"))
            if job_orchestration
            else False,
            "dispatch_safety_status": job_orchestration.get("dispatch_safety_status")
            if job_orchestration
            else "MISSING",
        }
    )
    runner_contract_entry = _status_payload(
        runner_contract,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
    )
    runner_contract_entry.update(
        {
            "gate_name": runner_contract.get("gate_name") if runner_contract else "",
            "gate_status": runner_contract.get("gate_status") if runner_contract else "MISSING",
            "contract_id": runner_contract.get("contract_id") if runner_contract else "",
            "contract_validation_status": runner_contract.get("contract_validation_status")
            if runner_contract
            else "MISSING",
            "dispatch_enabled": runner_contract.get("dispatch_enabled")
            if runner_contract
            else False,
            "executable": runner_contract.get("executable") if runner_contract else False,
            "allowed_command_count": runner_contract.get("allowed_command_count", 0)
            if runner_contract
            else 0,
            "forbidden_command_count": runner_contract.get("forbidden_command_count", 0)
            if runner_contract
            else 0,
        }
    )
    agent_runner_dry_run_entry = _status_payload(
        agent_runner_dry_run,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
    )
    dry_run_preview = (
        agent_runner_dry_run.get("execution_preview")
        if isinstance(agent_runner_dry_run.get("execution_preview"), dict)
        else {}
    )
    dry_run_proof = (
        agent_runner_dry_run.get("non_execution_proof")
        if isinstance(agent_runner_dry_run.get("non_execution_proof"), dict)
        else {}
    )
    dry_run_policy = (
        agent_runner_dry_run.get("dispatch_policy")
        if isinstance(agent_runner_dry_run.get("dispatch_policy"), dict)
        else {}
    )
    agent_runner_dry_run_entry.update(
        {
            "gate_name": agent_runner_dry_run.get("gate_name") if agent_runner_dry_run else "",
            "gate_status": agent_runner_dry_run.get("gate_status") if agent_runner_dry_run else "MISSING",
            "dry_run_status": agent_runner_dry_run.get("dry_run_status") if agent_runner_dry_run else "MISSING",
            "planned_command_count": dry_run_preview.get("planned_command_count", 0),
            "forbidden_command_count": dry_run_preview.get("forbidden_command_count", 0),
            "omitted_command_count": dry_run_preview.get("omitted_command_count", 0),
            "commands_executed": dry_run_proof.get("commands_executed", False),
            "dispatch_enabled": dry_run_proof.get("dispatch_enabled", False),
            "executable": dry_run_proof.get("executable", False),
            "local_dry_run_readiness": dry_run_policy.get("local_dry_run_readiness", False),
            "real_dispatch_readiness": dry_run_policy.get("real_dispatch_readiness", False),
        }
    )
    handoff_bundle_entry = _status_payload(
        agent_runner_handoff_bundle,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
    )
    handoff_policy = (
        agent_runner_handoff_bundle.get("handoff_policy")
        if isinstance(agent_runner_handoff_bundle.get("handoff_policy"), dict)
        else {}
    )
    handoff_non_exec = (
        agent_runner_handoff_bundle.get("non_execution_policy")
        if isinstance(agent_runner_handoff_bundle.get("non_execution_policy"), dict)
        else {}
    )
    handoff_readiness = (
        agent_runner_handoff_bundle.get("readiness")
        if isinstance(agent_runner_handoff_bundle.get("readiness"), dict)
        else {}
    )
    handoff_bundle_entry.update(
        {
            "gate_name": agent_runner_handoff_bundle.get("gate_name") if agent_runner_handoff_bundle else "",
            "gate_status": agent_runner_handoff_bundle.get("gate_status") if agent_runner_handoff_bundle else "MISSING",
            "handoff_status": agent_runner_handoff_bundle.get("handoff_status") if agent_runner_handoff_bundle else "MISSING",
            "dispatch_prohibited": handoff_policy.get("dispatch_prohibited", False),
            "commands_executed": handoff_non_exec.get("commands_executed", False),
            "dispatch_enabled": handoff_non_exec.get("dispatch_enabled", False),
            "executable": handoff_non_exec.get("executable", False),
            "handoff_bundle_ready": handoff_readiness.get("handoff_bundle_ready", False),
            "real_dispatch_readiness": handoff_readiness.get("real_dispatch_readiness", False),
        }
    )
    handoff_validation_entry = _status_payload(
        agent_runner_handoff_validation,
        expected_decision_id=decision_id,
        expected_round_id=round_id,
        required=False,
    )
    handoff_validation_entry.update(
        {
            "gate_name": agent_runner_handoff_validation.get("gate_name") if agent_runner_handoff_validation else "",
            "gate_status": agent_runner_handoff_validation.get("gate_status") if agent_runner_handoff_validation else "MISSING",
            "validation_status": agent_runner_handoff_validation.get("validation_status")
            if agent_runner_handoff_validation
            else "MISSING",
            "validated_bundle_path": agent_runner_handoff_validation.get("validated_bundle_path")
            if agent_runner_handoff_validation
            else "",
        }
    )
    for name, entry in (
        ("audit inventory", audit_entry),
        ("jobs inventory", jobs_entry),
        ("job orchestration", job_orchestration_entry),
        ("runner contract", runner_contract_entry),
        ("agent runner dry-run", agent_runner_dry_run_entry),
        ("agent runner handoff bundle", handoff_bundle_entry),
        ("agent runner handoff validation", handoff_validation_entry),
    ):
        if entry.get("status") in {"historical_nonblocking", "missing_optional"}:
            warnings.append(f"{name} is {entry.get('status')}")

    close_round = closeout.get("close_round_result") if isinstance(closeout.get("close_round_result"), dict) else {}
    close_round_summary = (
        close_round.get("status_summary")
        if isinstance(close_round.get("status_summary"), dict)
        else {}
    )
    closeout_complete = (
        str(closeout.get("closeout_status") or "") == "PASSED"
        and str(close_round.get("close_status") or "") == "CLOSED"
    )
    final_tail_only = closeout_complete and _final_gate_failures_are_final_state_tail_only(final_gate)
    report_status = str(report.get("status") or "")
    acceptance_recommendation = str(report.get("acceptance_recommendation") or "")
    final_gate_status = str(final_gate.get("gate_status") or "")
    if final_state and final_tail_only:
        summary_report_status = str(close_round_summary.get("report_status") or "")
        summary_acceptance = str(close_round_summary.get("report_acceptance_recommendation") or "")
        if summary_report_status == "SUCCESS":
            report_status = "SUCCESS"
        if summary_acceptance == "ACCEPTED":
            acceptance_recommendation = "ACCEPTED"
        final_gate_status = "PASSED"
    final_state_complete = (
        report_status == "SUCCESS"
        and acceptance_recommendation == "ACCEPTED"
        and str(pytest_header.get("status") or "") == "PASSED"
        and final_gate_status == "PASSED"
        and closeout_complete
    )
    if final_state and not final_state_complete:
        if report_status != "SUCCESS":
            blocking_reasons.append("final-state report status is not SUCCESS")
        if acceptance_recommendation != "ACCEPTED":
            blocking_reasons.append("final-state report acceptance is not ACCEPTED")
        if str(pytest_header.get("status") or "") != "PASSED":
            blocking_reasons.append("final-state pytest_result status is not PASSED")
        if final_gate_status != "PASSED":
            blocking_reasons.append("final-state final_gate status is not PASSED")
        if str(closeout.get("closeout_status") or "") != "PASSED":
            blocking_reasons.append("final-state closeout status is not PASSED")
        if str(close_round.get("close_status") or "") != "CLOSED":
            blocking_reasons.append("final-state close_round status is not CLOSED")
    runner_jobs = jobs_inventory.get("jobs") if isinstance(jobs_inventory.get("jobs"), list) else []
    ready_or_running = [
        job
        for job in runner_jobs
        if isinstance(job, dict) and str(job.get("status") or "") in {"READY", "RUNNING"}
    ]
    status_counts = jobs_inventory.get("status_counts") if isinstance(jobs_inventory.get("status_counts"), dict) else {}
    current_job_status = str(job_orchestration.get("job_status") or "")
    current_job_id = str(job_orchestration.get("job_id") or "")
    explicit_safe_dispatch = bool(
        jobs_entry.get("is_current")
        and jobs_inventory.get("dispatch_safety_status") == "PASSED"
        and not jobs_inventory.get("dispatch_enabled")
        and ready_or_running
    )
    job_orchestration_ready = bool(
        job_orchestration_entry.get("is_current")
        and job_orchestration.get("gate_status") == "PASSED"
        and job_orchestration.get("dispatch_safety_status") == "PASSED"
        and job_orchestration.get("dispatch_enabled") is False
    )
    runner_contract_ready = bool(
        runner_contract_entry.get("is_current")
        and runner_contract.get("gate_status") == "PASSED"
        and runner_contract.get("contract_validation_status") == "PASSED"
        and runner_contract.get("dispatch_enabled") is False
        and runner_contract.get("executable") is False
    )
    local_dry_run_ready = bool(
        agent_runner_dry_run_entry.get("is_current")
        and agent_runner_dry_run.get("gate_status") == "PASSED"
        and agent_runner_dry_run.get("dry_run_status") == "PASSED"
        and dry_run_proof.get("commands_executed") is False
        and dry_run_proof.get("external_runner_invoked") is False
        and dry_run_proof.get("dispatch_enabled") is False
        and dry_run_proof.get("executable") is False
        and dry_run_policy.get("local_dry_run_readiness") is True
        and dry_run_policy.get("real_dispatch_readiness") is False
    )
    handoff_bundle_ready = bool(
        handoff_bundle_entry.get("is_current")
        and agent_runner_handoff_bundle.get("gate_status") == "PASSED"
        and agent_runner_handoff_bundle.get("handoff_status") == "PASSED"
        and handoff_policy.get("dispatch_prohibited") is True
        and handoff_non_exec.get("commands_executed") is False
        and handoff_non_exec.get("external_runner_invoked") is False
        and handoff_non_exec.get("dispatch_enabled") is False
        and handoff_non_exec.get("executable") is False
        and handoff_readiness.get("handoff_bundle_ready") is True
        and handoff_readiness.get("real_dispatch_readiness") is False
    )
    handoff_replay_validated = bool(
        handoff_validation_entry.get("is_current")
        and agent_runner_handoff_validation.get("gate_status") == "PASSED"
        and agent_runner_handoff_validation.get("validation_status") == "PASSED"
    )
    can_dispatch = False

    if blocking_reasons:
        headline = "Control plane has blocking state"
        next_action = "resolve_blocking_reasons_before_dispatch"
    elif warnings:
        headline = "Control plane snapshot ready with warnings"
        next_action = "review_warnings_before_dispatch"
    else:
        headline = "Control plane snapshot ready"
        next_action = str(command_plan.get("recommended_next_action") or "no_action_required")

    gate_status = "FAILED" if not decision_id or not command_plan or (final_state and blocking_reasons) else "PASSED"
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "artifact_name": ARTIFACT_NAME,
        "gate_name": GATE_NAME,
        "gate_status": gate_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "artifact_path": ARTIFACT_PATH,
        "snapshot_mode": "final_state" if final_state else "current_state",
        "active_decision": {
            "decision_id": decision_id,
            "round_id": round_id,
            "status": str(decision.get("status") or "UNKNOWN"),
            "mainline": mainline,
            "skill_profiles": list(decision.get("skill_profiles") or []),
            "consumed_by_matching_report": consumed_by_matching_report,
            "task_contract_path": "project_state/decision_packet.md",
        },
        "execution_status": {
            "snapshot_mode": "final_state" if final_state else "current_state",
            "final_state_complete": final_state_complete,
            "report_id": report_id,
            "expected_report_id": expected_report_id,
            "report_status": report_status or "MISSING",
            "acceptance_recommendation": acceptance_recommendation or "MISSING",
            "pytest_status": str(pytest_header.get("status") or "MISSING"),
            "final_gate_status": final_gate_status or "MISSING",
            "closeout_status": str(closeout.get("closeout_status") or "MISSING"),
            "close_round_status": str(close_round.get("close_status") or "MISSING"),
            "command_plan_status": str(command_plan.get("plan_status") or "MISSING"),
            "execution_log_source": str(execution_log.get("source") or "MISSING"),
            "warnings": warnings,
            "blocking_reasons": blocking_reasons,
        },
        "inventory_status": {
            "audit_inventory": audit_entry,
            "jobs_inventory": jobs_entry,
            "job_orchestration": job_orchestration_entry,
            "runner_contract": runner_contract_entry,
            "agent_runner_dry_run": agent_runner_dry_run_entry,
            "agent_runner_handoff_bundle": handoff_bundle_entry,
            "agent_runner_handoff_validation": handoff_validation_entry,
            "round_archive_inventory": {
                "status": "not_implemented",
                "nonblocking": True,
                "detail": "snapshot does not scan full project_state/rounds",
            },
        },
        "job_queue_status": {
            "job_count": int(jobs_inventory.get("job_count") or 0),
            "status_counts": status_counts,
            "current_job_id": current_job_id,
            "current_job_status": current_job_status,
            "ready_or_running_job_count": len(ready_or_running),
            "dispatch_safety_status": job_orchestration.get("dispatch_safety_status")
            or jobs_inventory.get("dispatch_safety_status")
            or "MISSING",
        },
        "runner_readiness": {
            "can_dispatch_next_decision": can_dispatch,
            "default_dispatch_policy": "non_dispatch",
            "explicit_safe_dispatch_evidence": explicit_safe_dispatch,
            "ready_or_running_job_count": len(ready_or_running),
            "job_orchestration_ready": job_orchestration_ready,
            "runner_contract_ready": runner_contract_ready,
            "local_dry_run_ready": local_dry_run_ready,
            "handoff_bundle_ready": handoff_bundle_ready,
            "handoff_replay_validated": handoff_replay_validated,
            "real_dispatch_readiness": False,
            "job_orchestration_status": str(job_orchestration.get("gate_status") or "MISSING"),
            "runner_contract_status": str(runner_contract.get("gate_status") or "MISSING"),
            "agent_runner_dry_run_status": str(agent_runner_dry_run.get("gate_status") or "MISSING"),
            "agent_runner_handoff_bundle_status": str(agent_runner_handoff_bundle.get("gate_status") or "MISSING"),
            "agent_runner_handoff_validation_status": str(agent_runner_handoff_validation.get("gate_status") or "MISSING"),
            "runner_contract_executable": runner_contract.get("executable")
            if runner_contract
            else False,
            "dispatch_safety_status": job_orchestration.get("dispatch_safety_status")
            or runner_contract.get("dispatch_enabled")
            or jobs_inventory.get("dispatch_safety_status")
            or "MISSING",
            "reason": "external dispatch stays disabled unless a future safe dispatch policy is explicit",
        },
        "authority_separation": {
            "task_contract": "project_state/decision_packet.md",
            "command_execution_authority": "project_state/gates/command_plan.json",
            "snapshot_role": "read_only_status_output",
        },
        "ui_summary": {
            "headline": headline,
            "next_action": next_action,
            "blocking_reasons": blocking_reasons,
            "warnings": warnings,
        },
        "generated_artifacts": [ARTIFACT_PATH],
    }

    if write_result:
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / ARTIFACT_NAME).write_text(
            json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return snapshot


def snapshot_exit_code(snapshot: dict[str, Any]) -> int:
    return 1 if snapshot.get("gate_status") == "FAILED" else 0
