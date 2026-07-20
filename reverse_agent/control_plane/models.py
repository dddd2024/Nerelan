"""Typed, deterministic models used by the transition control plane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class TransitionDecision:
    decision_id: str
    round_id: str
    status: str
    mainline: str
    skill_profiles: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TransitionDecision":
        return cls(
            decision_id=str(payload.get("decision_id") or ""),
            round_id=str(payload.get("round_id") or ""),
            status=str(payload.get("status") or ""),
            mainline=str(payload.get("mainline") or ""),
            skill_profiles=_strings(payload.get("skill_profiles")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "status": self.status,
            "mainline": self.mainline,
            "skill_profiles": list(self.skill_profiles),
        }


@dataclass(frozen=True)
class TransitionCommand:
    command: str
    phase: str
    required: bool
    expected_exit_codes: tuple[int, ...]
    execution_surface: str = "local"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TransitionCommand":
        raw_codes = payload.get("expected_exit_codes")
        codes = tuple(int(code) for code in raw_codes) if isinstance(raw_codes, list) else ()
        return cls(
            command=str(payload.get("command") or ""),
            phase=str(payload.get("phase") or ""),
            required=bool(payload.get("required", False)),
            expected_exit_codes=codes,
            execution_surface=str(payload.get("execution_surface") or "local"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "phase": self.phase,
            "required": self.required,
            "expected_exit_codes": list(self.expected_exit_codes),
            "execution_surface": self.execution_surface,
        }


@dataclass(frozen=True)
class TransitionCommandPlan:
    decision_id: str
    round_id: str
    commands: tuple[TransitionCommand, ...]
    schema_version: int = 1

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TransitionCommandPlan":
        raw_commands = payload.get("commands")
        commands = tuple(
            TransitionCommand.from_mapping(item)
            for item in raw_commands
            if isinstance(item, Mapping)
        ) if isinstance(raw_commands, list) else ()
        return cls(
            decision_id=str(payload.get("decision_id") or ""),
            round_id=str(payload.get("round_id") or ""),
            commands=commands,
            schema_version=int(payload.get("schema_version") or 1),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "commands": [command.to_dict() for command in self.commands],
        }


@dataclass(frozen=True)
class ExecutionEnvelope:
    command: str
    execution_surface: str
    mutated_paths: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "execution_surface": self.execution_surface,
            "mutated_paths": list(self.mutated_paths),
            "operations": list(self.operations),
        }


@dataclass(frozen=True)
class TransitionAuthority:
    decision: TransitionDecision
    command_plan: TransitionCommandPlan
    expected_decision_id: str
    expected_round_id: str
    active_skills: tuple[str, ...]
    legal_mainlines: tuple[str, ...]
    expected_branch: str
    actual_branch: str
    base_sha: str
    merge_base_sha: str
    decision_commit_sha: str
    decision_is_ancestor: bool
    observed_paths: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "command_plan": self.command_plan.to_dict(),
            "expected_decision_id": self.expected_decision_id,
            "expected_round_id": self.expected_round_id,
            "active_skills": list(self.active_skills),
            "legal_mainlines": list(self.legal_mainlines),
            "expected_branch": self.expected_branch,
            "actual_branch": self.actual_branch,
            "base_sha": self.base_sha,
            "merge_base_sha": self.merge_base_sha,
            "decision_commit_sha": self.decision_commit_sha,
            "decision_is_ancestor": self.decision_is_ancestor,
            "observed_paths": list(self.observed_paths),
            "allowed_paths": list(self.allowed_paths),
            "forbidden_paths": list(self.forbidden_paths),
            "forbidden_operations": list(self.forbidden_operations),
        }


@dataclass(frozen=True)
class TransitionPreflightResult:
    decision_id: str
    round_id: str
    gate_status: str
    checks: tuple[Mapping[str, Any], ...]
    blocking_reasons: tuple[str, ...]
    schema_version: int = 1
    gate_name: str = "transition-preflight"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_name": self.gate_name,
            "gate_status": self.gate_status,
            "decision_id": self.decision_id,
            "round_id": self.round_id,
            "checks": [dict(check) for check in self.checks],
            "blocking_reasons": list(self.blocking_reasons),
        }
