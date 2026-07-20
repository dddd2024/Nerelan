"""Narrow Trust Authorization Port backed by the transition kernel."""

from __future__ import annotations

from typing import Protocol

from reverse_agent.architecture.contracts import AuthorizationRequest, AuthorizationResult
from reverse_agent.architecture.risk import AuthorizationStatus, RiskTier
from reverse_agent.control_plane.models import ExecutionEnvelope as TransitionExecutionEnvelope
from reverse_agent.control_plane.models import TransitionAuthority
from reverse_agent.control_plane.transition import validate_transition


class TrustAuthorizationPort(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        ...


class TransitionKernelAuthorizationAdapter:
    """Reuse transition validation without importing legacy closeout state."""

    def __init__(self, authority: TransitionAuthority) -> None:
        self._authority = authority

    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        if request.risk_tier not in (RiskTier.R2, RiskTier.R3):
            return AuthorizationResult(AuthorizationStatus.BLOCKED, ("trust_port_only_accepts_r2_r3",))
        if request.decision_id != self._authority.decision.decision_id:
            return AuthorizationResult(AuthorizationStatus.BLOCKED, ("decision_identity_mismatch",))
        if request.round_id != self._authority.decision.round_id:
            return AuthorizationResult(AuthorizationStatus.BLOCKED, ("round_identity_mismatch",))
        if not request.command:
            return AuthorizationResult(AuthorizationStatus.APPROVAL_REQUIRED, ("command_authority_required",))
        envelope = TransitionExecutionEnvelope(
            command=request.command,
            execution_surface="local",
            mutated_paths=request.envelope.paths,
            operations=request.envelope.operations,
        )
        result = validate_transition(self._authority, (envelope,))
        if result.gate_status == "PASSED":
            return AuthorizationResult(AuthorizationStatus.AUTHORIZED)
        return AuthorizationResult(AuthorizationStatus.BLOCKED, result.blocking_reasons)
