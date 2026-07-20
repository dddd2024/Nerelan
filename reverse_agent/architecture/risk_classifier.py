"""Deterministic, fail-closed R0-R3 classification."""

from __future__ import annotations

from .contracts import ArchitectureDecision, ExecutionEnvelope
from .risk import RiskTier, WorkflowRoute


RISK_OPERATIONS: dict[RiskTier, frozenset[str]] = {
    RiskTier.R0: frozenset({"research", "planning", "code_read", "review", "read_only_audit"}),
    RiskTier.R1: frozenset({"source_edit", "unit_test", "format", "lint", "local_static_check"}),
    RiskTier.R2: frozenset({"workflow_change", "dependency_change", "network_access", "commit", "push", "draft_pr", "permission_policy", "migration"}),
    RiskTier.R3: frozenset({"unknown_binary_execution", "execute_binary", "debugger", "emulator", "hook", "dynamic_probe", "secrets", "destructive_delete", "privileged_remote_execution"}),
}


def classify_risk(envelope: ExecutionEnvelope) -> ArchitectureDecision:
    operations = tuple(operation.strip().lower() for operation in envelope.operations if operation.strip())
    if not operations:
        return ArchitectureDecision(None, WorkflowRoute.BLOCKED, ("missing_operations",))
    known = set().union(*RISK_OPERATIONS.values())
    unknown = tuple(operation for operation in operations if operation not in known)
    if unknown:
        return ArchitectureDecision(None, WorkflowRoute.BLOCKED, tuple(f"unknown_operation:{item}" for item in unknown))

    tiers = [tier for tier, values in RISK_OPERATIONS.items() if any(item in values for item in operations)]
    if envelope.binary_execution_requested:
        tiers.append(RiskTier.R3)
    if envelope.network_requested:
        tiers.append(RiskTier.R2)
    tier = max(tiers, key=lambda item: int(item.value[1]))
    route = WorkflowRoute.STANDARD_PATH if tier in (RiskTier.R0, RiskTier.R1) else WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED
    return ArchitectureDecision(tier, route, (f"highest_risk:{tier.value}",))
