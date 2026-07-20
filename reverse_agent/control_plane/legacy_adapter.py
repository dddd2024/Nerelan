"""Narrow compatibility adapter between legacy artifacts and transition models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .models import TransitionCommandPlan, TransitionDecision


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


def dispatch_preflight(
    contract: Mapping[str, Any],
    *,
    transition_validator: Callable[[], Any],
    legacy_validator: Callable[[], Any],
) -> Any:
    """Preserve legacy behavior unless a Decision explicitly selects transition mode."""

    return transition_validator() if is_transition_decision(contract) else legacy_validator()
