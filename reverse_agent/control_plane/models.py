"""Typed, deterministic models used by the transition control plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
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
    operations: tuple[str, ...] = ()
    network_access: bool = False
    diagnostic_only: bool = False
    allowed_only_after_validation: bool = False
    bootstrap_exception: bool = False

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
            operations=_strings(payload.get("operations")),
            network_access=bool(payload.get("network_access", False)),
            diagnostic_only=bool(payload.get("diagnostic_only", False)),
            allowed_only_after_validation=bool(payload.get("allowed_only_after_validation", False)),
            bootstrap_exception=bool(payload.get("bootstrap_exception", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "phase": self.phase,
            "required": self.required,
            "expected_exit_codes": list(self.expected_exit_codes),
            "execution_surface": self.execution_surface,
            "operations": list(self.operations),
            "network_access": self.network_access,
            "diagnostic_only": self.diagnostic_only,
            "allowed_only_after_validation": self.allowed_only_after_validation,
            "bootstrap_exception": self.bootstrap_exception,
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
    exit_code: int | None = None
    started_at: str = ""
    observed_at: str = ""
    bootstrap_exception: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "execution_surface": self.execution_surface,
            "mutated_paths": list(self.mutated_paths),
            "operations": list(self.operations),
            "exit_code": self.exit_code,
            "started_at": self.started_at,
            "observed_at": self.observed_at,
            "bootstrap_exception": self.bootstrap_exception,
        }


@dataclass(frozen=True)
class CapabilityPolicy:
    runner_dispatch_allowed: bool = False
    model_api_invocation_allowed: bool = False
    external_reverse_tool_invocation_allowed: bool = False
    unknown_binary_execution_allowed: bool = False
    destructive_operations_allowed: bool = False
    bmad_installation_allowed: bool = False
    network_access_default_allowed: bool = False
    direct_push_to_main_allowed: bool = False
    merge_allowed: bool = False
    force_push_allowed: bool = False
    rebase_during_execution_allowed: bool = False
    tag_or_release_allowed: bool = False
    local_network_exceptions: tuple[str, ...] = ()
    ci_network_exceptions: tuple[str, ...] = ()
    remote_observation_read_only_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "runner_dispatch_allowed": self.runner_dispatch_allowed,
            "model_api_invocation_allowed": self.model_api_invocation_allowed,
            "external_reverse_tool_invocation_allowed": self.external_reverse_tool_invocation_allowed,
            "unknown_binary_execution_allowed": self.unknown_binary_execution_allowed,
            "destructive_operations_allowed": self.destructive_operations_allowed,
            "bmad_installation_allowed": self.bmad_installation_allowed,
            "network_access_default_allowed": self.network_access_default_allowed,
            "direct_push_to_main_allowed": self.direct_push_to_main_allowed,
            "merge_allowed": self.merge_allowed,
            "force_push_allowed": self.force_push_allowed,
            "rebase_during_execution_allowed": self.rebase_during_execution_allowed,
            "tag_or_release_allowed": self.tag_or_release_allowed,
            "local_network_exceptions": list(self.local_network_exceptions),
            "ci_network_exceptions": list(self.ci_network_exceptions),
            "remote_observation_read_only_allowed": self.remote_observation_read_only_allowed,
        }


@dataclass(frozen=True)
class PathRiskFloor:
    entries: tuple[tuple[str, str], ...]

    def risk_for_path(self, path: str) -> str | None:
        normalized = path.replace("\\", "/").lstrip("./")
        for pattern, risk in self.entries:
            candidate = pattern.replace("\\", "/").lstrip("./")
            if self._matches(candidate, normalized):
                return risk
        return None

    @staticmethod
    def _matches(candidate: str, normalized: str) -> bool:
        # Strip leading "**/" - matches anything before the rest.
        leading_any = candidate.startswith("**/")
        if leading_any:
            candidate = candidate[3:]
        # Strip trailing "/**" - matches anything after the rest.
        trailing_any = candidate.endswith("/**")
        if trailing_any:
            candidate = candidate[:-3]
        candidate = candidate.strip("/")

        if leading_any and trailing_any:
            # **/foo/** -> path contains /foo/
            if not candidate:
                return True
            return (
                normalized == candidate
                or normalized.startswith(f"{candidate}/")
                or normalized.endswith(f"/{candidate}")
                or f"/{candidate}/" in f"/{normalized}/"
            )
        if leading_any:
            # **/foo     -> any path named foo at any depth
            # **/*.exe   -> any path ending with .ext
            if "*" in candidate or "?" in candidate:
                return fnmatch(normalized, candidate) or fnmatch(normalized, f"*/{candidate}")
            return normalized == candidate or normalized.endswith(f"/{candidate}")
        if trailing_any:
            # foo/**     -> prefix match
            return normalized == candidate or normalized.startswith(f"{candidate}/")
        return normalized == candidate or fnmatch(normalized, candidate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                {"pattern": pattern, "minimum_risk": risk}
                for pattern, risk in self.entries
            ],
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
    reference_paths: tuple[str, ...] = ()
    capability_policy: CapabilityPolicy | None = None
    path_risk_floor: PathRiskFloor | None = None

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
            "reference_paths": list(self.reference_paths),
            "capability_policy": self.capability_policy.to_dict() if self.capability_policy else None,
            "path_risk_floor": self.path_risk_floor.to_dict() if self.path_risk_floor else None,
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
