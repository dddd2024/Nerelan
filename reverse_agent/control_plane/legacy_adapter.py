"""Narrow compatibility adapter between legacy artifacts and transition models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .models import TransitionCommand, TransitionCommandPlan, TransitionDecision


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


def detect_control_plane_mode(path: Path) -> str:
    """Return one deterministic mode token, rejecting malformed authority."""

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
    return "transition" if flag else "legacy"


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


def build_transition_command_plan(
    decision: TransitionDecision,
    contract: Mapping[str, Any],
) -> TransitionCommandPlan:
    """Build deterministic local command authority from the active Decision."""

    if not decision.decision_id:
        raise ValueError("missing_decision_id")
    if not decision.round_id:
        raise ValueError("missing_round_id")
    _required_string(contract, "required_branch")
    _string_list(contract, "bootstrap_exception_files", required=True)
    raw_commands = _string_list(contract, "bootstrap_exception_commands", required=True)
    commands: list[TransitionCommand] = []
    for command in raw_commands:
        if command.startswith("python -m pytest"):
            phase = "test"
        elif command.startswith("git "):
            phase = "status"
        else:
            phase = "gate"
        commands.append(
            TransitionCommand(
                command=command,
                phase=phase,
                required=True,
                expected_exit_codes=(0,),
                execution_surface="local",
            )
        )
    return TransitionCommandPlan(
        decision_id=decision.decision_id,
        round_id=decision.round_id,
        commands=tuple(commands),
    )


def load_transition_scope(
    decision: TransitionDecision,
    contract: Mapping[str, Any],
) -> dict[str, tuple[str, ...] | str]:
    """Load branch, path and operation policy without legacy hard-coded scope."""

    required_branch = _required_string(contract, "required_branch")
    activation_base_sha = _required_string(contract, "activation_base_sha")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", activation_base_sha):
        raise ValueError("missing_or_invalid_contract_field:activation_base_sha")

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
    allowed: list[str] = []
    for name in allowed_fields:
        allowed.extend(_string_list(contract, name))
    for name in ("roadmap_path", "unified_long_term_roadmap"):
        value = contract.get(name)
        if value is not None:
            allowed.append(_required_string(contract, name))
    if not allowed:
        raise ValueError("missing_or_invalid_contract_field:allowed_paths")

    forbidden = _string_list(contract, "forbidden_mutated_paths", required=True)
    operations = list(_string_list(contract, "forbidden_operations"))
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

    if not decision.mainline:
        raise ValueError("missing_mainline")
    return {
        "required_branch": required_branch,
        "activation_base_sha": activation_base_sha.lower(),
        "allowed_paths": tuple(dict.fromkeys(allowed)),
        "forbidden_paths": tuple(dict.fromkeys(forbidden)),
        "forbidden_operations": tuple(dict.fromkeys(operations)),
        "legal_mainlines": (decision.mainline,),
    }


def dispatch_preflight(
    contract: Mapping[str, Any],
    *,
    transition_validator: Callable[[], Any],
    legacy_validator: Callable[[], Any],
) -> Any:
    """Preserve legacy behavior unless a Decision explicitly selects transition mode."""

    return transition_validator() if is_transition_decision(contract) else legacy_validator()
