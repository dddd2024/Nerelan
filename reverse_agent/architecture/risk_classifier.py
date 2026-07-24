"""Deterministic, fail-closed R0-R3 classification."""

from __future__ import annotations

from typing import Protocol

from .contracts import ArchitectureDecision, ExecutionEnvelope
from .risk import RiskTier, WorkflowRoute


RISK_OPERATIONS: dict[RiskTier, frozenset[str]] = {
    RiskTier.R0: frozenset({"research", "planning", "code_read", "review", "read_only_audit"}),
    RiskTier.R1: frozenset({"source_edit", "unit_test", "format", "lint", "local_static_check"}),
    RiskTier.R2: frozenset({"workflow_change", "dependency_change", "network_access", "commit", "push", "draft_pr", "permission_policy", "migration"}),
    RiskTier.R3: frozenset({"unknown_binary_execution", "execute_binary", "debugger", "emulator", "hook", "dynamic_probe", "secrets", "destructive_delete", "privileged_remote_execution"}),
}


class PathRiskFloor(Protocol):
    """Duck-typed protocol for path-risk floor lookups.

    The architecture layer must not import from ``control_plane``; any object
    exposing ``risk_for_path(path) -> str | None`` satisfies this protocol.
    """

    def risk_for_path(self, path: str) -> str | None: ...


_TIER_RANK = {RiskTier.R0: 0, RiskTier.R1: 1, RiskTier.R2: 2, RiskTier.R3: 3}


def _tier_from_label(label: str) -> RiskTier | None:
    for tier in (RiskTier.R0, RiskTier.R1, RiskTier.R2, RiskTier.R3):
        if tier.value == label:
            return tier
    return None


def _path_risk(envelope: ExecutionEnvelope, path_risk_floor: PathRiskFloor | None) -> RiskTier | None:
    if path_risk_floor is None:
        return None
    highest: RiskTier | None = None
    for path in envelope.paths:
        label = path_risk_floor.risk_for_path(path)
        if label is None:
            continue
        tier = _tier_from_label(label)
        if tier is None:
            continue
        if highest is None or _TIER_RANK[tier] > _TIER_RANK[highest]:
            highest = tier
    return highest


def classify_risk(
    envelope: ExecutionEnvelope,
    *,
    path_risk_floor: PathRiskFloor | None = None,
    capability_flag_risk: RiskTier | None = None,
) -> ArchitectureDecision:
    """Classify risk using ``max(operation_risk, path_risk, capability_flag_risk)``.

    A caller cannot lower workflow, dependency, Decision, gate, secret, binary
    or destructive work by labeling it as a generic source edit. Unknown
    operations always block regardless of the path floor; operation
    under-reporting cannot reduce the final tier.
    """

    operations = tuple(operation.strip().lower() for operation in envelope.operations if operation.strip())
    if not operations:
        return ArchitectureDecision(None, WorkflowRoute.BLOCKED, ("missing_operations",))
    known = set().union(*RISK_OPERATIONS.values())
    unknown = tuple(operation for operation in operations if operation not in known)
    if unknown:
        return ArchitectureDecision(None, WorkflowRoute.BLOCKED, tuple(f"unknown_operation:{item}" for item in unknown))

    tiers: list[RiskTier] = [tier for tier, values in RISK_OPERATIONS.items() if any(item in values for item in operations)]
    if envelope.binary_execution_requested:
        tiers.append(RiskTier.R3)
    if envelope.network_requested:
        tiers.append(RiskTier.R2)

    path_tier = _path_risk(envelope, path_risk_floor)
    if path_tier is not None:
        tiers.append(path_tier)
    if capability_flag_risk is not None:
        tiers.append(capability_flag_risk)

    if not tiers:
        return ArchitectureDecision(None, WorkflowRoute.BLOCKED, ("no_applicable_risk_tier",))
    tier = max(tiers, key=lambda item: _TIER_RANK[item])
    route = WorkflowRoute.STANDARD_PATH if tier in (RiskTier.R0, RiskTier.R1) else WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED
    reasons: list[str] = [f"highest_risk:{tier.value}"]
    if path_tier is not None:
        reasons.append(f"path_risk_floor:{path_tier.value}")
    if capability_flag_risk is not None:
        reasons.append(f"capability_flag_risk:{capability_flag_risk.value}")
    return ArchitectureDecision(tier, route, tuple(reasons))
