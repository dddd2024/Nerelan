from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable

from .user_solve_contract import redact_internal_references


class FallbackStepName(StrEnum):
    FAST_STRINGS = "fast_strings"
    IDA_SUMMARY = "ida_summary"
    TARGETED_DECOMPILE = "targeted_decompile"
    CONSTANT_MATERIAL_EXTRACT = "constant_material_extract"
    SOLVER_ATTEMPT = "solver_attempt"
    RUNTIME_VALIDATION = "runtime_validation"


class FallbackRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FallbackCapability(StrEnum):
    STATIC_STRINGS = "static_strings"
    IDA_SUMMARY = "ida_summary"
    TARGETED_STATIC_ANALYSIS = "targeted_static_analysis"
    MATERIAL_EXTRACTION = "material_extraction"
    SOLVER = "solver"
    RUNTIME_VALIDATION = "runtime_validation"


class PermissionRequirement(StrEnum):
    AUTOMATIC = "automatic"
    EXPLICIT_PERMISSION = "explicit_permission"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class FallbackStep:
    name: FallbackStepName
    risk_level: FallbackRiskLevel
    timeout_seconds: int
    required_capability: FallbackCapability
    fast_mode_eligible: bool
    writes_artifact: bool
    permission_requirement: PermissionRequirement
    requires_local_execution: bool = False
    requires_dynamic_debug: bool = False
    requires_network: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", FallbackStepName(self.name))
        object.__setattr__(self, "risk_level", FallbackRiskLevel(self.risk_level))
        object.__setattr__(self, "required_capability", FallbackCapability(self.required_capability))
        object.__setattr__(self, "permission_requirement", PermissionRequirement(self.permission_requirement))
        if int(self.timeout_seconds) <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "timeout_seconds", int(self.timeout_seconds))

    @property
    def executable_by_default(self) -> bool:
        return (
            self.permission_requirement == PermissionRequirement.AUTOMATIC
            and not self.requires_local_execution
            and not self.requires_dynamic_debug
            and not self.requires_network
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name.value,
            "risk_level": self.risk_level.value,
            "timeout_seconds": self.timeout_seconds,
            "required_capability": self.required_capability.value,
            "fast_mode_eligible": self.fast_mode_eligible,
            "writes_artifact": self.writes_artifact,
            "permission_requirement": self.permission_requirement.value,
            "requires_local_execution": self.requires_local_execution,
            "requires_dynamic_debug": self.requires_dynamic_debug,
            "requires_network": self.requires_network,
            "executable_by_default": self.executable_by_default,
        }


@dataclass(frozen=True)
class FallbackPolicy:
    allowed_capabilities: set[FallbackCapability] = field(default_factory=set)
    explicit_permissions: set[PermissionRequirement] = field(default_factory=set)
    fast_mode: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "allowed_capabilities",
            {item if isinstance(item, FallbackCapability) else FallbackCapability(item) for item in self.allowed_capabilities},
        )
        object.__setattr__(
            self,
            "explicit_permissions",
            {
                item if isinstance(item, PermissionRequirement) else PermissionRequirement(item)
                for item in self.explicit_permissions
            },
        )


@dataclass(frozen=True)
class FallbackDecision:
    selected_step: FallbackStep | None
    eligible_steps: list[FallbackStep] = field(default_factory=list)
    blocked_steps: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    stop_reason: str = ""
    executed: bool = False

    def to_user_dict(self) -> dict[str, Any]:
        payload = {
            "selected_step": self.selected_step.to_dict() if self.selected_step else None,
            "eligible_steps": [step.name.value for step in self.eligible_steps],
            "blocked_steps": [
                {
                    "name": str(item.get("name") or ""),
                    "reasons": list(item.get("reasons") or []),
                }
                for item in self.blocked_steps
            ],
            "missing_evidence": list(self.missing_evidence),
            "stop_reason": self.stop_reason,
            "executed": self.executed,
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        return {
            "selected_step": self.selected_step.to_dict() if self.selected_step else None,
            "eligible_steps": [step.to_dict() for step in self.eligible_steps],
            "blocked_steps": list(self.blocked_steps),
            "missing_evidence": list(self.missing_evidence),
            "stop_reason": self.stop_reason,
            "executed": self.executed,
        }


class FallbackLadder:
    """Select the next safe fallback step from synthetic state only."""

    def __init__(self, steps: Iterable[FallbackStep] | None = None):
        self.steps = tuple(steps or default_fallback_steps())

    @classmethod
    def default(cls) -> "FallbackLadder":
        return cls()

    def select_next(
        self,
        *,
        completed_steps: Iterable[FallbackStepName | str] | None = None,
        missing_evidence: Iterable[str] | None = None,
        policy: FallbackPolicy | None = None,
    ) -> FallbackDecision:
        completed = {
            item if isinstance(item, FallbackStepName) else FallbackStepName(str(item))
            for item in (completed_steps or [])
        }
        gaps = [str(item) for item in (missing_evidence or []) if str(item).strip()]
        active_policy = policy or FallbackPolicy(
            allowed_capabilities={
                FallbackCapability.STATIC_STRINGS,
                FallbackCapability.IDA_SUMMARY,
                FallbackCapability.TARGETED_STATIC_ANALYSIS,
            }
        )
        eligible: list[FallbackStep] = []
        blocked: list[dict[str, Any]] = []
        for step in self.steps:
            if step.name in completed:
                continue
            reasons = self._block_reasons(step, active_policy)
            if reasons:
                blocked.append({"name": step.name.value, "reasons": reasons, "step": step.to_dict()})
                continue
            eligible.append(step)
            return FallbackDecision(
                selected_step=step,
                eligible_steps=eligible,
                blocked_steps=blocked,
                missing_evidence=gaps,
                stop_reason="selected_next_safe_step",
                executed=False,
            )
        return FallbackDecision(
            selected_step=None,
            eligible_steps=eligible,
            blocked_steps=blocked,
            missing_evidence=gaps,
            stop_reason="no_safe_step_available_without_permission",
            executed=False,
        )

    @staticmethod
    def _block_reasons(step: FallbackStep, policy: FallbackPolicy) -> list[str]:
        reasons: list[str] = []
        if policy.fast_mode and not step.fast_mode_eligible:
            reasons.append("not_fast_mode_eligible")
        if step.required_capability not in policy.allowed_capabilities:
            reasons.append(f"capability_not_allowed:{step.required_capability.value}")
        if (
            step.permission_requirement != PermissionRequirement.AUTOMATIC
            and step.permission_requirement not in policy.explicit_permissions
        ):
            reasons.append(f"permission_required:{step.permission_requirement.value}")
        if step.requires_local_execution:
            reasons.append("requires_local_execution")
        if step.requires_dynamic_debug:
            reasons.append("requires_dynamic_debug")
        if step.requires_network:
            reasons.append("requires_network")
        return reasons

    def to_dict(self) -> dict[str, Any]:
        return {"steps": [step.to_dict() for step in self.steps], "executes_steps": False}


def default_fallback_steps() -> tuple[FallbackStep, ...]:
    return (
        FallbackStep(
            name=FallbackStepName.FAST_STRINGS,
            risk_level=FallbackRiskLevel.LOW,
            timeout_seconds=20,
            required_capability=FallbackCapability.STATIC_STRINGS,
            fast_mode_eligible=True,
            writes_artifact=False,
            permission_requirement=PermissionRequirement.AUTOMATIC,
        ),
        FallbackStep(
            name=FallbackStepName.IDA_SUMMARY,
            risk_level=FallbackRiskLevel.LOW,
            timeout_seconds=60,
            required_capability=FallbackCapability.IDA_SUMMARY,
            fast_mode_eligible=True,
            writes_artifact=True,
            permission_requirement=PermissionRequirement.AUTOMATIC,
        ),
        FallbackStep(
            name=FallbackStepName.TARGETED_DECOMPILE,
            risk_level=FallbackRiskLevel.MEDIUM,
            timeout_seconds=180,
            required_capability=FallbackCapability.TARGETED_STATIC_ANALYSIS,
            fast_mode_eligible=True,
            writes_artifact=True,
            permission_requirement=PermissionRequirement.AUTOMATIC,
        ),
        FallbackStep(
            name=FallbackStepName.CONSTANT_MATERIAL_EXTRACT,
            risk_level=FallbackRiskLevel.MEDIUM,
            timeout_seconds=240,
            required_capability=FallbackCapability.MATERIAL_EXTRACTION,
            fast_mode_eligible=False,
            writes_artifact=True,
            permission_requirement=PermissionRequirement.EXPLICIT_PERMISSION,
            requires_local_execution=True,
        ),
        FallbackStep(
            name=FallbackStepName.SOLVER_ATTEMPT,
            risk_level=FallbackRiskLevel.HIGH,
            timeout_seconds=600,
            required_capability=FallbackCapability.SOLVER,
            fast_mode_eligible=False,
            writes_artifact=True,
            permission_requirement=PermissionRequirement.EXPLICIT_PERMISSION,
            requires_local_execution=True,
        ),
        FallbackStep(
            name=FallbackStepName.RUNTIME_VALIDATION,
            risk_level=FallbackRiskLevel.HIGH,
            timeout_seconds=300,
            required_capability=FallbackCapability.RUNTIME_VALIDATION,
            fast_mode_eligible=False,
            writes_artifact=True,
            permission_requirement=PermissionRequirement.EXPLICIT_PERMISSION,
            requires_local_execution=True,
            requires_dynamic_debug=True,
        ),
    )
