"""Local non-executing AgentRunner dry-run artifact builder."""

from __future__ import annotations

import json
import hashlib
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
HANDOFF_BUNDLE_GATE_NAME = "agent-runner-handoff-bundle"
HANDOFF_BUNDLE_ARTIFACT_NAME = "agent_runner_handoff_bundle.json"
HANDOFF_BUNDLE_ARTIFACT_PATH = f"project_state/gates/{HANDOFF_BUNDLE_ARTIFACT_NAME}"
HANDOFF_VALIDATION_GATE_NAME = "agent-runner-handoff-validate"
HANDOFF_VALIDATION_ARTIFACT_NAME = "agent_runner_handoff_validation.json"
HANDOFF_VALIDATION_ARTIFACT_PATH = f"project_state/gates/{HANDOFF_VALIDATION_ARTIFACT_NAME}"


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


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def _input_record(
    *,
    repo_root: Path,
    relative_path: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    path = repo_root / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "decision_id": str(payload.get("decision_id") or ""),
        "round_id": str(payload.get("round_id") or ""),
        "gate_status": payload.get("gate_status") or payload.get("plan_status") or payload.get("status"),
    }


def _non_execution_policy() -> dict[str, bool]:
    return {
        "commands_executed": False,
        "subprocess_spawned": False,
        "external_runner_invoked": False,
        "model_api_called": False,
        "github_actions_triggered": False,
        "remote_mutation": False,
        "dispatch_enabled": False,
        "executable": False,
        "can_dispatch": False,
        "allow_agent_dispatch": False,
    }


def build_agent_runner_handoff_bundle(
    *,
    state_dir: str | Path,
    repo_root: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    """Seal a local, non-executing AgentRunner handoff bundle."""

    state_dir_path = Path(state_dir)
    repo_root_path = Path(repo_root) if repo_root is not None else state_dir_path.parent
    gates_dir = state_dir_path / "gates"
    decision = read_decision_meta(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    expected_job_id = planned_job_id_for_round(round_id)
    job_artifact_path = planned_job_artifact_path(expected_job_id)

    input_paths = {
        "decision_packet": "project_state/decision_packet.md",
        "job_artifact": job_artifact_path,
        "command_plan": "project_state/gates/command_plan.json",
        "runner_contract": "project_state/gates/runner_contract_result.json",
        "agent_runner_dry_run": "project_state/gates/agent_runner_dry_run_result.json",
        "control_plane_snapshot": "project_state/gates/control_plane_snapshot.json",
    }
    input_payloads: dict[str, dict[str, Any]] = {
        "decision_packet": decision,
        "job_artifact": _read_json(repo_root_path / job_artifact_path),
        "command_plan": load_command_plan(state_dir_path),
        "runner_contract": _read_json(gates_dir / "runner_contract_result.json"),
        "agent_runner_dry_run": _read_json(gates_dir / "agent_runner_dry_run_result.json"),
        "control_plane_snapshot": _read_json(gates_dir / "control_plane_snapshot.json"),
    }

    errors: list[str] = []
    warnings: list[str] = []
    for label, relative_path in input_paths.items():
        if label != "decision_packet" and not input_payloads[label]:
            errors.append(f"{label} artifact missing or invalid")
        if not (repo_root_path / relative_path).exists():
            errors.append(f"{label} path missing: {relative_path}")
    for label in ("job_artifact", "command_plan", "runner_contract", "agent_runner_dry_run", "control_plane_snapshot"):
        payload = input_payloads[label]
        if not payload:
            continue
        if str(payload.get("decision_id") or "") != decision_id:
            errors.append(f"{label} decision_id mismatch")
        if str(payload.get("round_id") or "") != round_id:
            errors.append(f"{label} round_id mismatch")

    command_plan = input_payloads["command_plan"]
    runner_contract = input_payloads["runner_contract"]
    dry_run = input_payloads["agent_runner_dry_run"]
    control_plane = input_payloads["control_plane_snapshot"]
    preview = dry_run.get("execution_preview") if isinstance(dry_run.get("execution_preview"), dict) else {}
    proof = dry_run.get("non_execution_proof") if isinstance(dry_run.get("non_execution_proof"), dict) else {}
    dispatch_policy = dry_run.get("dispatch_policy") if isinstance(dry_run.get("dispatch_policy"), dict) else {}
    runner_readiness = control_plane.get("runner_readiness") if isinstance(control_plane.get("runner_readiness"), dict) else {}

    for field in (
        "commands_executed",
        "subprocess_spawned",
        "external_runner_invoked",
        "model_api_called",
        "github_actions_triggered",
        "remote_mutation",
        "dispatch_enabled",
        "executable",
        "can_dispatch",
    ):
        observed = proof.get(field, dispatch_policy.get(field, runner_contract.get(field)))
        if observed is not False:
            errors.append(f"non-execution field {field} is not false")
    if runner_readiness.get("real_dispatch_readiness") is True:
        errors.append("control-plane real_dispatch_readiness is true")

    input_records = {
        label: _input_record(
            repo_root=repo_root_path,
            relative_path=relative_path,
            payload=input_payloads.get(label, {}),
        )
        for label, relative_path in input_paths.items()
    }
    command_texts = _command_texts(command_plan.get("commands")) if command_plan else []
    dry_run_texts = preview.get("planned_command_texts") if isinstance(preview.get("planned_command_texts"), list) else []
    if command_texts and dry_run_texts and command_texts != [str(item) for item in dry_run_texts]:
        warnings.append("command_plan command texts differ from dry-run planned command texts")

    status = "FAILED" if errors else "PASSED"
    payload_without_seal: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_name": HANDOFF_BUNDLE_ARTIFACT_NAME,
        "artifact_path": HANDOFF_BUNDLE_ARTIFACT_PATH,
        "gate_name": HANDOFF_BUNDLE_GATE_NAME,
        "gate_status": status,
        "handoff_status": status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "repo_root": _norm_path(repo_root_path),
        "sealed_inputs": input_records,
        "handoff_policy": {
            "policy_name": "local_non_executing_handoff",
            "dispatch_prohibited": True,
            "external_calls_prohibited": True,
            "write_scope": "project_state_only",
        },
        "non_execution_policy": _non_execution_policy(),
        "commands": {
            "allowed_commands": runner_contract.get("allowed_commands") or [],
            "allowed_command_texts": command_texts,
            "dry_run_command_texts": dry_run_texts,
            "forbidden_commands": runner_contract.get("forbidden_commands") or preview.get("forbidden_commands") or [],
            "omitted_commands": command_plan.get("omitted_commands") or preview.get("omitted_commands") or [],
        },
        "write_paths": {
            "allowed_write_paths": [_norm_path(path) for path in runner_contract.get("allowed_write_paths") or preview.get("allowed_write_paths") or []],
            "generated_artifacts": [HANDOFF_BUNDLE_ARTIFACT_PATH],
        },
        "readiness": {
            "local_dry_run_ready": dispatch_policy.get("local_dry_run_readiness") is True,
            "handoff_bundle_ready": status == "PASSED",
            "handoff_replay_validated": False,
            "real_dispatch_readiness": False,
        },
        "errors": errors,
        "warnings": warnings,
        "generated_artifacts": [HANDOFF_BUNDLE_ARTIFACT_PATH],
    }
    payload_without_seal["seal"] = {
        "algorithm": "sha256-canonical-json",
        "bundle_fingerprint": _canonical_hash({
            key: value for key, value in payload_without_seal.items()
            if key not in {"generated_at", "seal"}
        }),
    }
    if write_result:
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / HANDOFF_BUNDLE_ARTIFACT_NAME).write_text(
            json.dumps(payload_without_seal, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return payload_without_seal


def _safe_write_path(path: object) -> bool:
    normalized = _norm_path(path)
    if not normalized or normalized.startswith("/") or ":" in normalized or ".." in normalized.split("/"):
        return False
    forbidden_prefixes = ("reverse_agent/", "tests/", "solve_reports/", ".github/")
    return normalized.startswith("project_state/") and not normalized.startswith(forbidden_prefixes)


def validate_agent_runner_handoff_bundle(
    *,
    state_dir: str | Path,
    repo_root: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    """Replay-validate the sealed handoff bundle without executing commands."""

    state_dir_path = Path(state_dir)
    repo_root_path = Path(repo_root) if repo_root is not None else state_dir_path.parent
    gates_dir = state_dir_path / "gates"
    decision = read_decision_meta(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    mainline = str(decision.get("mainline") or "")
    bundle_path = gates_dir / HANDOFF_BUNDLE_ARTIFACT_NAME
    bundle = _read_json(bundle_path)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            errors.append(detail)

    add_check("bundle_present", bool(bundle), "handoff bundle is present")
    if bundle:
        add_check("bundle_decision_id_current", str(bundle.get("decision_id") or "") == decision_id, "bundle decision_id matches current decision")
        add_check("bundle_round_id_current", str(bundle.get("round_id") or "") == round_id, "bundle round_id matches current round")
        add_check("bundle_gate_status_passed", str(bundle.get("gate_status") or "") == "PASSED", "bundle gate_status is PASSED")

        seal = bundle.get("seal") if isinstance(bundle.get("seal"), dict) else {}
        recomputed = _canonical_hash({
            key: value for key, value in bundle.items()
            if key not in {"generated_at", "seal"}
        })
        add_check("bundle_fingerprint_matches", seal.get("bundle_fingerprint") == recomputed, "bundle canonical fingerprint matches payload")

        sealed_inputs = bundle.get("sealed_inputs") if isinstance(bundle.get("sealed_inputs"), dict) else {}
        for label, record in sealed_inputs.items():
            if not isinstance(record, Mapping):
                add_check(f"{label}_record_shape", False, f"{label} sealed input record is invalid")
                continue
            relative_path = str(record.get("path") or "")
            current_sha = _sha256_file(repo_root_path / relative_path)
            add_check(f"{label}_digest_current", current_sha and current_sha == str(record.get("sha256") or ""), f"{label} digest matches current artifact")
            rec_decision_id = str(record.get("decision_id") or "")
            rec_round_id = str(record.get("round_id") or "")
            if rec_decision_id:
                add_check(f"{label}_decision_id_current", rec_decision_id == decision_id, f"{label} decision_id is current")
            if rec_round_id:
                add_check(f"{label}_round_id_current", rec_round_id == round_id, f"{label} round_id is current")

        non_exec = bundle.get("non_execution_policy") if isinstance(bundle.get("non_execution_policy"), dict) else {}
        for field in _non_execution_policy():
            add_check(f"non_execution_{field}", non_exec.get(field) is False, f"non_execution_policy.{field} is false")
        readiness = bundle.get("readiness") if isinstance(bundle.get("readiness"), dict) else {}
        add_check("real_dispatch_not_ready", readiness.get("real_dispatch_readiness") is False, "real dispatch readiness remains false")
        add_check("handoff_bundle_ready", readiness.get("handoff_bundle_ready") is True, "handoff bundle readiness is true")

        command_plan = load_command_plan(state_dir_path)
        dry_run = _read_json(gates_dir / "agent_runner_dry_run_result.json")
        preview = dry_run.get("execution_preview") if isinstance(dry_run.get("execution_preview"), dict) else {}
        commands = bundle.get("commands") if isinstance(bundle.get("commands"), dict) else {}
        bundle_plan_texts = [str(item) for item in commands.get("allowed_command_texts") or []]
        current_plan_texts = _command_texts(command_plan.get("commands")) if command_plan else []
        add_check("command_plan_texts_match", bundle_plan_texts == current_plan_texts, "bundle command texts match command_plan")
        dry_run_texts = [str(item) for item in preview.get("planned_command_texts") or []]
        if dry_run_texts:
            add_check("dry_run_texts_match", [str(item) for item in commands.get("dry_run_command_texts") or []] == dry_run_texts, "bundle dry-run texts match dry-run artifact")
        write_paths = bundle.get("write_paths") if isinstance(bundle.get("write_paths"), dict) else {}
        allowed_write_paths = write_paths.get("allowed_write_paths") if isinstance(write_paths.get("allowed_write_paths"), list) else []
        unsafe = [str(path) for path in allowed_write_paths if not _safe_write_path(path)]
        add_check("allowed_write_paths_safe", not unsafe, "allowed write paths stay under project_state")

    status = "FAILED" if errors else "PASSED"
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_name": HANDOFF_VALIDATION_ARTIFACT_NAME,
        "artifact_path": HANDOFF_VALIDATION_ARTIFACT_PATH,
        "gate_name": HANDOFF_VALIDATION_GATE_NAME,
        "gate_status": status,
        "validation_status": status,
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": mainline,
        "generated_at": _now_iso(),
        "validated_bundle_path": HANDOFF_BUNDLE_ARTIFACT_PATH,
        "checks": checks,
        "errors": errors,
        "warnings": [],
        "generated_artifacts": [HANDOFF_VALIDATION_ARTIFACT_PATH],
    }
    if write_result:
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / HANDOFF_VALIDATION_ARTIFACT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
