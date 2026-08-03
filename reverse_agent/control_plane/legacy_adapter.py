"""Narrow compatibility adapter between legacy artifacts and transition models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .evidence_source import normalize_evidence_source
from .models import (
    BootstrapState,
    CapabilityPolicy,
    ExecutionEnvelope,
    PathRiskFloor,
    TransitionCommand,
    TransitionCommandPlan,
    TransitionDecision,
)


def extract_json_block(text: str, name: str) -> dict[str, Any]:
    pattern = rf"```json\s+{re.escape(name)}\s*\n(.*?)\n```"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"missing_json_block:{name}")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_block:{name}")
    return payload


def load_transition_decision(path: Path) -> tuple[TransitionDecision, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    meta = extract_json_block(text, "decision_meta")
    contract = extract_json_block(text, "decision_contract")
    return TransitionDecision.from_mapping(meta), contract


def is_transition_decision(contract: Mapping[str, Any]) -> bool:
    return contract.get("transition_kernel_required") is True


def detect_control_plane_mode(
    path: Path,
    *,
    event: Mapping[str, Any] | None = None,
) -> str:
    """Return one deterministic mode token, rejecting malformed authority.

    Without an event (or a non-pull-request event) the Decision-selected mode
    (``transition`` or ``legacy``) is returned.  When a pull-request event is
    supplied, a PR whose head ref does NOT equal the active Decision's
    ``required_branch`` is routed to ``path_a_r1`` for ordinary R1 authority
    verification; a PR bound to the Decision's branch keeps the Decision mode.
    """

    decision, contract = load_transition_decision(path)
    if not decision.decision_id:
        raise ValueError("missing_decision_id")
    if not decision.round_id:
        raise ValueError("missing_round_id")
    if not decision.status:
        raise ValueError("missing_decision_status")
    if not decision.mainline:
        raise ValueError("missing_mainline")
    if not decision.skill_profiles:
        raise ValueError("missing_skill_profiles")
    flag = contract.get("transition_kernel_required", False)
    if not isinstance(flag, bool):
        raise ValueError("transition_kernel_required_must_be_boolean")
    decision_mode = "transition" if flag else "legacy"

    if event is None or not isinstance(event.get("pull_request"), Mapping):
        return decision_mode

    pr = event["pull_request"]
    head_ref = str((pr.get("head") or {}).get("ref") or "")
    required_branch = _required_string(contract, "required_branch")
    if head_ref == required_branch:
        return decision_mode
    return "path_a_r1"


def load_legacy_command_plan(path: Path) -> TransitionCommandPlan:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("command_plan_must_be_object")
    normalized = dict(payload)
    commands = []
    for raw in payload.get("commands", []):
        if not isinstance(raw, dict):
            continue
        command = dict(raw)
        command.setdefault("execution_surface", "local")
        commands.append(command)
    normalized["commands"] = commands
    return TransitionCommandPlan.from_mapping(normalized)


def _required_string(contract: Mapping[str, Any], name: str) -> str:
    value = contract.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_or_invalid_contract_field:{name}")
    return value.strip()


def _string_list(
    contract: Mapping[str, Any],
    name: str,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    value = contract.get(name)
    if value is None and not required:
        return ()
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing_or_invalid_contract_field:{name}")
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"missing_or_invalid_contract_field:{name}")
    return items


def _exception_list(payload: Mapping[str, Any], name: str) -> tuple[str, ...]:
    """Parse an optional string-list field that may legitimately be empty.

    ``None`` and ``[]`` both yield an empty tuple; a non-list value or any
    non-string/blank entry is rejected. Used for fields like
    ``bootstrap_exception_commands`` and network exception lists where an
    empty set is a valid, fail-closed declaration.
    """

    value = payload.get(name)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"missing_or_invalid_contract_field:{name}")
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"missing_or_invalid_contract_field:{name}")
    return items


_VALID_EXECUTION_SURFACES = frozenset({"local", "ci_only", "remote_observation"})


def _parse_structured_command(raw: Mapping[str, Any], *, bootstrap_exception: bool) -> TransitionCommand:
    command = str(raw.get("command") or "").strip()
    if not command:
        raise ValueError("empty_command_in_allowed_commands")
    phase = str(raw.get("phase") or "").strip()
    if not phase:
        raise ValueError(f"missing_phase_for_command:{command}")
    raw_codes = raw.get("expected_exit_codes")
    if not isinstance(raw_codes, list) or not raw_codes:
        raise ValueError(f"missing_expected_exit_codes:{command}")
    codes = tuple(int(code) for code in raw_codes)
    surface = str(raw.get("execution_surface") or "local")
    if surface not in _VALID_EXECUTION_SURFACES:
        raise ValueError(f"invalid_execution_surface:{surface}:{command}")
    operations_raw = raw.get("operations") or []
    if not isinstance(operations_raw, list):
        raise ValueError(f"invalid_operations_for_command:{command}")
    operations = tuple(str(item).strip() for item in operations_raw if isinstance(item, str) and item.strip())
    return TransitionCommand(
        command=command,
        phase=phase,
        required=bool(raw.get("required", False)),
        expected_exit_codes=codes,
        execution_surface=surface,
        operations=operations,
        network_access=bool(raw.get("network_access", False)),
        diagnostic_only=bool(raw.get("diagnostic_only", False)),
        allowed_only_after_validation=bool(raw.get("allowed_only_after_validation", False)),
        bootstrap_exception=bootstrap_exception,
        command_id=str(raw.get("command_id") or ""),
        required_evidence_source=normalize_evidence_source(
            str(raw.get("required_evidence_source") or "")
        ),
        authority_origin=(
            "bootstrap_exception" if bootstrap_exception
            else str(raw.get("authority_origin") or "normal_plan")
        ),
        subject_to_reconciliation=bool(raw.get("subject_to_reconciliation", True)),
        allowed_mutated_paths=tuple(
            str(p).strip() for p in (raw.get("allowed_mutated_paths") or [])
            if isinstance(p, str) and p.strip()
        ),
        produced_artifacts=tuple(
            str(p).strip() for p in (raw.get("produced_artifacts") or [])
            if isinstance(p, str) and p.strip()
        ),
    )


def _bootstrap_command_phase(command: str) -> str:
    if command.startswith("python -m pytest"):
        return "test"
    if command.startswith("git "):
        return "status"
    return "gate"


def build_transition_command_plan(
    decision: TransitionDecision,
    contract: Mapping[str, Any],
) -> TransitionCommandPlan:
    """Build deterministic local command authority from the active Decision.

    When ``allowed_commands`` is present in the contract, the structured entries
    form the normal plan-authorized command set. Bootstrap exception commands
    are appended as a separately-marked group so they can be distinguished
    during reconciliation; they never replace the normal plan.
    """

    if not decision.decision_id:
        raise ValueError("missing_decision_id")
    if not decision.round_id:
        raise ValueError("missing_round_id")
    _required_string(contract, "required_branch")
    _string_list(contract, "bootstrap_exception_files", required=True)

    structured_commands: list[TransitionCommand] = []
    allowed_commands = contract.get("allowed_commands")
    if allowed_commands is not None:
        if not isinstance(allowed_commands, list) or not allowed_commands:
            raise ValueError("missing_or_invalid_contract_field:allowed_commands")
        for raw in allowed_commands:
            if not isinstance(raw, Mapping):
                raise ValueError("invalid_allowed_commands_entry")
            structured_commands.append(
                _parse_structured_command(raw, bootstrap_exception=False)
            )

    bootstrap_raw = _exception_list(contract, "bootstrap_exception_commands")
    bootstrap_commands = [
        TransitionCommand(
            command=command,
            phase=_bootstrap_command_phase(command),
            required=True,
            expected_exit_codes=(0,),
            execution_surface="local",
            operations=(),
            network_access=False,
            diagnostic_only=False,
            allowed_only_after_validation=False,
            bootstrap_exception=True,
            command_id=f"bootstrap.{command[:64]}",
            required_evidence_source=normalize_evidence_source("local_provenance"),
            authority_origin="bootstrap_exception",
        )
        for command in bootstrap_raw
    ]

    # Normal plan-authorized commands first, then bootstrap exception commands
    # so the plan is deterministic but reconciliation can tell them apart.
    commands = (*structured_commands, *bootstrap_commands)
    if not commands:
        raise ValueError("missing_or_invalid_contract_field:commands")

    # De-duplicate by (canonical_command, execution_surface) keeping first occurrence.
    seen: set[tuple[str, str]] = set()
    deduped: list[TransitionCommand] = []
    for entry in commands:
        identity = (canonical_command(entry.command), entry.execution_surface)
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(entry)

    return TransitionCommandPlan(
        decision_id=decision.decision_id,
        round_id=decision.round_id,
        commands=tuple(deduped),
    )


def canonical_command(command: str) -> str:
    """Return a stable command identity without interpreting shell syntax."""

    return " ".join(str(command).split())


def load_capability_policy(contract: Mapping[str, Any]) -> CapabilityPolicy:
    """Build a machine-enforced capability policy from the contract.

    Unknown fields default to fail-closed (``False``). The structured
    ``capability_policy`` mapping is preferred; legacy boolean fields remain
    supported for backward compatibility.
    """

    structured = contract.get("capability_policy")
    if isinstance(structured, Mapping):
        local_exceptions = _exception_list(structured, "local_network_exceptions")
        ci_exceptions = _exception_list(structured, "ci_network_exceptions")
        return CapabilityPolicy(
            runner_dispatch_allowed=bool(structured.get("runner_dispatch_allowed", False)),
            model_api_invocation_allowed=bool(structured.get("model_api_invocation_allowed", False)),
            external_reverse_tool_invocation_allowed=bool(
                structured.get("external_reverse_tool_invocation_allowed", False)
            ),
            unknown_binary_execution_allowed=bool(
                structured.get("unknown_binary_execution_allowed", False)
            ),
            destructive_operations_allowed=bool(
                structured.get("destructive_operations_allowed", False)
            ),
            bmad_installation_allowed=bool(structured.get("bmad_installation_allowed", False)),
            network_access_default_allowed=bool(
                structured.get("network_access_default_allowed", False)
            ),
            direct_push_to_main_allowed=bool(
                structured.get("direct_push_to_main_allowed", False)
            ),
            merge_allowed=bool(structured.get("merge_allowed", False)),
            force_push_allowed=bool(structured.get("force_push_allowed", False)),
            rebase_during_execution_allowed=bool(
                structured.get("rebase_during_execution_allowed", False)
            ),
            tag_or_release_allowed=bool(structured.get("tag_or_release_allowed", False)),
            local_network_exceptions=local_exceptions,
            ci_network_exceptions=ci_exceptions,
            remote_observation_read_only_allowed=bool(
                structured.get("remote_observation_read_only_allowed", False)
            ),
        )

    # Legacy fallback: read flat boolean fields from the contract.
    def _flag(name: str) -> bool:
        value = contract.get(name)
        if not isinstance(value, bool):
            raise ValueError(f"missing_or_invalid_contract_field:{name}")
        return value

    return CapabilityPolicy(
        runner_dispatch_allowed=_flag("runner_dispatch_allowed") if "runner_dispatch_allowed" in contract else False,
        model_api_invocation_allowed=_flag("model_api_invocation_allowed") if "model_api_invocation_allowed" in contract else False,
        external_reverse_tool_invocation_allowed=_flag("external_reverse_tool_invocation_allowed") if "external_reverse_tool_invocation_allowed" in contract else False,
        unknown_binary_execution_allowed=_flag("unknown_binary_execution_allowed") if "unknown_binary_execution_allowed" in contract else False,
        destructive_operations_allowed=_flag("destructive_operations_allowed") if "destructive_operations_allowed" in contract else False,
        bmad_installation_allowed=False,
        network_access_default_allowed=False,
        direct_push_to_main_allowed=_flag("direct_push_to_main_allowed") if "direct_push_to_main_allowed" in contract else False,
        merge_allowed=_flag("merge_allowed") if "merge_allowed" in contract else False,
        force_push_allowed=_flag("force_push_allowed") if "force_push_allowed" in contract else False,
        rebase_during_execution_allowed=_flag("rebase_during_execution_allowed") if "rebase_during_execution_allowed" in contract else False,
        tag_or_release_allowed=False,
        local_network_exceptions=(),
        ci_network_exceptions=(),
        remote_observation_read_only_allowed=False,
    )


def load_path_risk_floor(contract: Mapping[str, Any]) -> PathRiskFloor:
    """Load path-risk floor entries from the contract."""

    raw = contract.get("path_risk_floor")
    if raw is None:
        return PathRiskFloor(entries=())
    if not isinstance(raw, list):
        raise ValueError("missing_or_invalid_contract_field:path_risk_floor")
    entries: list[tuple[str, str]] = []
    valid_risks = {"R0", "R1", "R2", "R3"}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("invalid_path_risk_floor_entry")
        pattern = str(item.get("pattern") or "").strip()
        if not pattern:
            raise ValueError("missing_or_invalid_contract_field:path_risk_floor_pattern")
        risk = str(item.get("minimum_risk") or "").strip()
        if risk not in valid_risks:
            raise ValueError(f"invalid_path_risk_floor_risk:{risk}")
        entries.append((pattern, risk))
    return PathRiskFloor(entries=tuple(entries))


def load_reference_paths(contract: Mapping[str, Any]) -> tuple[str, ...]:
    """Load read-only reference paths declared by the Decision.

    Reference paths are distinct from ``allowed_mutated_paths``: being named in
    the Decision does not grant write access.
    """

    raw = contract.get("reference_paths")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("missing_or_invalid_contract_field:reference_paths")
    return tuple(str(item).strip() for item in raw if isinstance(item, str) and item.strip())


def load_generated_artifact_paths(contract: Mapping[str, Any]) -> tuple[str, ...]:
    """Load generated-artifact paths declared by the Decision.

    Phase E: generated artifacts (gate outputs, reports, etc.) are a separate
    group from reference, allowed, and forbidden paths. They may only be
    written by their designated generator command, not by arbitrary mutation.
    """

    raw = contract.get("generated_artifact_paths")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("missing_or_invalid_contract_field:generated_artifact_paths")
    return tuple(str(item).strip() for item in raw if isinstance(item, str) and item.strip())


def load_transition_scope(
    decision: TransitionDecision,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Load branch, path and operation policy without legacy hard-coded scope."""

    required_branch = _required_string(contract, "required_branch")
    activation_base_sha = _required_string(contract, "activation_base_sha")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", activation_base_sha):
        raise ValueError("missing_or_invalid_contract_field:activation_base_sha")

    # Structured contract uses ``allowed_mutated_paths``; legacy contract uses
    # the per-category ``allowed_*`` fields. Support both for compatibility.
    allowed: list[str] = []
    structured_paths = contract.get("allowed_mutated_paths")
    if structured_paths is not None:
        allowed.extend(_string_list(contract, "allowed_mutated_paths"))
    else:
        allowed_fields = (
            "allowed_packaging_files",
            "allowed_workflow_files",
            "allowed_control_plane_files",
            "allowed_source_paths",
            "allowed_test_files",
            "allowed_documentation_files",
            "allowed_project_state_files",
            "bootstrap_exception_files",
        )
        for name in allowed_fields:
            allowed.extend(_string_list(contract, name))

    # ``reference_paths`` must NOT be added to allowed mutable scope.
    reference_paths = load_reference_paths(contract)

    # Phase E: ``generated_artifact_paths`` is a separate group. It must not
    # overlap with reference_paths, allowed_mutated_paths, or forbidden_mutated_paths.
    # Generated artifacts may only be written by their designated generator.
    generated_artifact_paths = load_generated_artifact_paths(contract)

    forbidden = _string_list(contract, "forbidden_mutated_paths", required=True)
    operations = list(_string_list(contract, "forbidden_operations"))

    # If the contract declares capability_policy, derive forbidden operations
    # from the structured flags as well so the machine gate stays in sync.
    structured_policy = contract.get("capability_policy")
    if isinstance(structured_policy, Mapping):
        capability_forbidden = {
            "direct_push_to_main_allowed": "direct_push_main",
            "merge_allowed": "merge",
            "force_push_allowed": "force_push",
            "rebase_during_execution_allowed": "rebase",
            "destructive_operations_allowed": "destructive",
            "unknown_binary_execution_allowed": "unknown_binary_execution",
            "model_api_invocation_allowed": "model_api_invocation",
            "external_reverse_tool_invocation_allowed": "external_reverse_tool_invocation",
            "runner_dispatch_allowed": "runner_dispatch",
            "bmad_installation_allowed": "bmad_installation",
        }
        for field, operation in capability_forbidden.items():
            value = structured_policy.get(field)
            if isinstance(value, bool) and not value:
                operations.append(operation)
    else:
        boolean_operation_fields = {
            "direct_push_to_main_allowed": "direct_push_main",
            "merge_allowed": "merge",
            "force_push_allowed": "force_push",
            "rebase_during_execution_allowed": "rebase",
            "destructive_operations_allowed": "destructive",
            "unknown_binary_execution_allowed": "unknown_binary_execution",
            "model_api_invocation_allowed": "model_api_invocation",
            "external_reverse_tool_invocation_allowed": "external_reverse_tool_invocation",
        }
        for field, operation in boolean_operation_fields.items():
            value = contract.get(field)
            if not isinstance(value, bool):
                raise ValueError(f"missing_or_invalid_contract_field:{field}")
            if not value:
                operations.append(operation)

    # Detect explicit allowed/forbidden path conflicts.
    allowed_set = {p for p in allowed}
    forbidden_set = {p for p in forbidden}
    reference_set = {p for p in reference_paths}
    generated_set = {p for p in generated_artifact_paths}
    overlap = allowed_set & forbidden_set
    if overlap:
        raise ValueError(f"allowed_forbidden_path_conflict:{sorted(overlap)}")
    # Phase E: four-group mutual exclusivity checks.
    reference_generated_overlap = reference_set & generated_set
    if reference_generated_overlap:
        raise ValueError(
            f"reference_generated_path_conflict:{sorted(reference_generated_overlap)}"
        )
    generated_forbidden_overlap = generated_set & forbidden_set
    if generated_forbidden_overlap:
        raise ValueError(
            f"generated_forbidden_path_conflict:{sorted(generated_forbidden_overlap)}"
        )
    # Phase E v2 (attestation policy seal): generated_artifact_paths MAY
    # overlap with allowed_mutated_paths. The global generated-artifact
    # exemption is replaced by command-bound mutation grants
    # (``produced_artifacts`` on each command). A path that is both an
    # authorized mutable path and a generated artifact is permitted; the
    # binding to a specific generator command_id is enforced at
    # execution-record validation time, not at scope loading.

    # F9: load the active Decision's authorized risk tier and authorized risk
    # paths so the path-risk floor can distinguish authorized R2 mutations
    # (e.g. project_state/gates/**) from unauthorized sensitive mutations.
    authorized_risk_tier = str(contract.get("authorized_risk_tier") or "").strip()
    raw_authorized_risk_paths = contract.get("authorized_risk_paths")
    if raw_authorized_risk_paths is None:
        authorized_risk_paths: tuple[str, ...] = ()
    elif isinstance(raw_authorized_risk_paths, list):
        authorized_risk_paths = tuple(
            str(item).strip() for item in raw_authorized_risk_paths
            if isinstance(item, str) and item.strip()
        )
    else:
        raise ValueError("missing_or_invalid_contract_field:authorized_risk_paths")

    # F4/F6: runner-managed artifact paths are executor provenance written by
    # the TrustedExecutionContext itself. They are excluded from the subprocess
    # mutation delta but remain part of the local evidence bundle.
    raw_runner_managed = contract.get("runner_managed_artifact_paths")
    if raw_runner_managed is None:
        runner_managed_artifact_paths: tuple[str, ...] = ()
    elif isinstance(raw_runner_managed, list):
        runner_managed_artifact_paths = tuple(
            str(item).strip() for item in raw_runner_managed
            if isinstance(item, str) and item.strip()
        )
    else:
        raise ValueError("missing_or_invalid_contract_field:runner_managed_artifact_paths")

    if not decision.mainline:
        raise ValueError("missing_mainline")
    return {
        "required_branch": required_branch,
        "activation_base_sha": activation_base_sha.lower(),
        "allowed_paths": tuple(dict.fromkeys(allowed)),
        "forbidden_paths": tuple(dict.fromkeys(forbidden)),
        "forbidden_operations": tuple(dict.fromkeys(operations)),
        "legal_mainlines": (decision.mainline,),
        "reference_paths": reference_paths,
        "generated_artifact_paths": generated_artifact_paths,
        "authorized_risk_paths": authorized_risk_paths,
        "authorized_risk_tier": authorized_risk_tier,
        "runner_managed_artifact_paths": runner_managed_artifact_paths,
    }


def load_execution_envelopes_from_log(path: Path) -> tuple[ExecutionEnvelope, ...]:
    """Parse ``execution_log.json`` into typed execution envelopes.

    The execution log preserves the observed transcript. This loader does not
    synthesize envelopes when evidence is missing; callers must distinguish
    ``PRE_EXECUTION_AUTHORIZED`` from ``POST_EXECUTION_RECONCILED`` elsewhere.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("execution_log_must_be_object")
    raw_commands = payload.get("commands")
    if not isinstance(raw_commands, list):
        return ()
    envelopes: list[ExecutionEnvelope] = []
    for entry in raw_commands:
        if not isinstance(entry, Mapping):
            continue
        command = str(entry.get("command") or "").strip()
        if not command:
            continue
        exit_code = entry.get("exit_code")
        if not isinstance(exit_code, int):
            exit_code = None
        phase = str(entry.get("phase") or "").strip()
        # Map execution-log phase to an execution surface. ``ci_*`` phases map
        # to ``ci_only``; everything else is treated as ``local`` for now.
        surface = "ci_only" if phase.startswith("ci_") else "local"
        operations = tuple(
            str(item).strip()
            for item in entry.get("operations", [])
            if isinstance(item, str) and item.strip()
        ) if isinstance(entry.get("operations"), list) else ()
        mutated_paths = tuple(
            str(item).strip()
            for item in entry.get("mutated_paths", [])
            if isinstance(item, str) and item.strip()
        ) if isinstance(entry.get("mutated_paths"), list) else ()
        bootstrap_exception = bool(entry.get("bootstrap_exception", False)) or phase in {
            "bootstrap_gate",
            "bootstrap_test",
        }
        command_id = str(entry.get("command_id") or "").strip()
        envelopes.append(
            ExecutionEnvelope(
                command=command,
                execution_surface=surface,
                mutated_paths=mutated_paths,
                operations=operations,
                exit_code=exit_code,
                started_at=str(entry.get("started_at") or ""),
                observed_at=str(entry.get("observed_at") or ""),
                bootstrap_exception=bootstrap_exception,
                command_id=command_id,
            )
        )
    return tuple(envelopes)


def select_validator(
    contract: Mapping[str, Any],
    *,
    transition_validator: Callable[[], Any],
    legacy_validator: Callable[[], Any],
) -> Any:
    """Preserve legacy behavior unless a Decision explicitly selects transition mode."""

    return transition_validator() if is_transition_decision(contract) else legacy_validator()


# Backwards-compatible alias used by legacy dispatch tests.
dispatch_preflight = select_validator


def load_bootstrap_state(state_path: Path) -> BootstrapState:
    """Load bootstrap state from ``bootstrap_state.json``.

    If the file does not exist, bootstrap defaults to ``BOOTSTRAP_OPEN``
    (the decision contract declares ``bootstrap_state_initial``).
    """

    if not state_path.exists():
        return BootstrapState(status="BOOTSTRAP_OPEN")
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return BootstrapState.from_mapping(payload)


def persist_bootstrap_state(
    state_path: Path,
    *,
    status: str,
    decision_id: str = "",
    round_id: str = "",
    expired_at: str = "",
) -> BootstrapState:
    """Persist a bootstrap state file, validating the status first."""

    state = BootstrapState(
        status=status,
        decision_id=decision_id,
        round_id=round_id,
        expired_at=expired_at,
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state.to_dict(), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return state
