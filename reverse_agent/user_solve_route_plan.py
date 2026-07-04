from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .tool_capabilities import RunnerCapability, capability_from_profiles
from .user_solve_contract import redact_internal_references


@dataclass(frozen=True)
class PlannedAction:
    kind: str
    label: str
    required_capability: str = ""
    risk_level: str = "low"
    permission_required: bool = False
    executable_now: bool = False
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not str(self.kind or "").strip():
            raise ValueError("planned action kind must be non-empty")
        if not str(self.label or "").strip():
            raise ValueError("planned action label must be non-empty")
        if self.executable_now:
            raise ValueError("route plans describe next actions only; they must not execute")
        object.__setattr__(self, "blocked_reasons", tuple(str(item) for item in self.blocked_reasons if str(item).strip()))

    def to_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "kind": self.kind,
                "label": self.label,
                "required_capability": self.required_capability,
                "risk_level": self.risk_level,
                "permission_required": self.permission_required,
                "executable_now": self.executable_now,
                "blocked_reasons": list(self.blocked_reasons),
            }
        )


@dataclass(frozen=True)
class RoutePlan:
    fixture_name: str
    status: str
    validation_status: str
    evidence_status: str
    planned_actions: tuple[PlannedAction, ...]
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)
    executed: bool = False

    def __post_init__(self) -> None:
        if self.executed:
            raise ValueError("route plans must not execute actions")
        if not self.planned_actions:
            raise ValueError("route plan must include at least one planned action")

    def to_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "fixture_name": self.fixture_name,
                "status": self.status,
                "validation_status": self.validation_status,
                "evidence_status": self.evidence_status,
                "missing_evidence": list(self.missing_evidence),
                "planned_actions": [item.to_dict() for item in self.planned_actions],
                "executed": self.executed,
                "fixture_only": True,
            }
        )


def build_route_plan(
    response: Mapping[str, Any],
    *,
    fixture_name: str,
    capability: RunnerCapability | None = None,
    missing_evidence: Iterable[str] | None = None,
) -> RoutePlan:
    active_capability = capability or capability_from_profiles()
    status = str(response.get("status") or "ready")
    validation_status = str(response.get("validation_status") or "unavailable")
    evidence_status = str(response.get("evidence_status") or "building")
    gaps = tuple(str(item) for item in (missing_evidence or []) if str(item).strip())
    actions: list[PlannedAction] = []

    if status == "verified" and validation_status == "passed":
        actions.append(PlannedAction(kind="return_answer", label="Return the verified fixture answer."))
    elif status == "candidate_found":
        actions.append(
            PlannedAction(
                kind="validate_candidate",
                label="Validate the candidate before accepting it.",
                required_capability="runtime_validation",
                risk_level="high",
                permission_required=True,
                blocked_reasons=("runtime_validation_disabled",),
            )
        )
    elif status == "blocked":
        actions.append(PlannedAction(kind="blocked", label="Resolve the fixture blocker before continuing."))
    else:
        required = "static_strings"
        blocked = () if required in active_capability.supported_features else ("static_strings_unavailable",)
        actions.append(
            PlannedAction(
                kind="collect_evidence",
                label="Collect more fixture evidence with the safest available metadata step.",
                required_capability=required,
                blocked_reasons=blocked,
            )
        )
    return RoutePlan(
        fixture_name=fixture_name,
        status=status,
        validation_status=validation_status,
        evidence_status=evidence_status,
        planned_actions=tuple(actions),
        missing_evidence=gaps,
    )


def route_plan_snapshot(response: Mapping[str, Any], *, fixture_name: str) -> dict[str, Any]:
    missing = []
    fallback = response.get("fallback_summary")
    if isinstance(fallback, Mapping):
        missing = list(fallback.get("missing_evidence") or [])
    return build_route_plan(response, fixture_name=fixture_name, missing_evidence=missing).to_dict()
