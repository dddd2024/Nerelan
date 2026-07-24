"""Phase D: Decision-issued runtime risk policy provider.

The ``AuthorizedRiskPolicyProvider`` is the single authoritative source of
``RiskPolicySnapshot`` for a workflow run. It loads the active Decision
contract, produces a canonical snapshot, and computes the authorized
``policy_digest``. Callers cannot supply their own snapshot; the workflow
identity binds the authorized digest so the classifier can detect drift.

Tampering with path risk, capability risk, the digest, or the Decision
identity is rejected with :class:`PolicyTamperingError` (F6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import (
    CapabilityRiskRule,
    PathRiskFloorSnapshot,
    RiskPolicySnapshot,
    WorkflowIdentity,
    _compute_policy_digest,
    stable_json,
)


class PolicyTamperingError(ValueError):
    """Raised when a supplied policy snapshot diverges from the authorized one."""


@dataclass(frozen=True)
class AuthorizedRiskPolicyProvider:
    """Authorized source of ``RiskPolicySnapshot`` for the active Decision.

    The provider reads the Decision contract (``decision_id``, ``round_id``,
    ``path_risk_floor``, ``capability_risk_rules``) and produces a canonical
    snapshot. The ``policy_digest`` is computed from the canonical payload,
    not from any caller-supplied value.
    """

    contract: Mapping[str, Any]

    def provide(self) -> RiskPolicySnapshot:
        """Produce the canonical authorized ``RiskPolicySnapshot``."""

        decision_id = str(self.contract.get("decision_id") or "").strip()
        round_id = str(self.contract.get("round_id") or "").strip()
        if not decision_id:
            raise ValueError("missing_or_invalid:decision_id")
        if not round_id:
            raise ValueError("missing_or_invalid:round_id")

        floor_payload = self.contract.get("path_risk_floor")
        if not isinstance(floor_payload, (list, tuple)):
            raise ValueError("missing_or_invalid:path_risk_floor")
        path_risk_floor = PathRiskFloorSnapshot.from_mapping(
            {"entries": floor_payload}
        )

        rules_payload = self.contract.get("capability_risk_rules")
        if not isinstance(rules_payload, (list, tuple)) or not rules_payload:
            raise ValueError("missing_or_invalid:capability_risk_rules")
        rules = tuple(
            CapabilityRiskRule.from_mapping(item) if isinstance(item, Mapping)
            else CapabilityRiskRule.from_mapping({"operation": item[0], "risk_tier": item[1]})
            for item in rules_payload
        )

        digest = _compute_policy_digest(decision_id, round_id, path_risk_floor, rules)
        return RiskPolicySnapshot(
            decision_id=decision_id,
            round_id=round_id,
            path_risk_floor=path_risk_floor,
            capability_risk_rules=rules,
            policy_digest=digest,
        )

    def workflow_identity(
        self,
        *,
        workflow_id: str,
        work_item_identity: str,
        attempt: int = 1,
    ) -> WorkflowIdentity:
        """Produce a workflow identity bound to the authorized policy digest.

        The identity carries ``decision_id``, ``round_id`` and
        ``policy_digest`` so the classifier can verify them at runtime and
        detect drift or replay with a stale policy.
        """

        snapshot = self.provide()
        return WorkflowIdentity(
            workflow_id=workflow_id,
            work_item_identity=work_item_identity,
            attempt=attempt,
            decision_id=snapshot.decision_id,
            round_id=snapshot.round_id,
            policy_digest=snapshot.policy_digest,
        )

    def verify(self, snapshot: RiskPolicySnapshot) -> None:
        """Verify that a supplied snapshot matches the authorized policy.

        Raises :class:`PolicyTamperingError` if the snapshot's identity,
        digest, or content diverges from the authorized policy.
        """

        authorized = self.provide()

        # Identity check: decision_id and round_id must match.
        if (
            snapshot.decision_id != authorized.decision_id
            or snapshot.round_id != authorized.round_id
        ):
            raise PolicyTamperingError(
                "identity_mismatch:"
                f"expected={authorized.decision_id}/{authorized.round_id} "
                f"observed={snapshot.decision_id}/{snapshot.round_id}"
            )

        # Digest check: the supplied digest must match the authorized digest.
        if snapshot.policy_digest != authorized.policy_digest:
            raise PolicyTamperingError(
                "policy_digest_mismatch:"
                f"expected={authorized.policy_digest} "
                f"observed={snapshot.policy_digest}"
            )

        # Content check: even if the digest matches, verify the actual content
        # has not been tampered with (catches the case where both digest and
        # content are forged consistently).
        if snapshot.path_risk_floor.to_dict() != authorized.path_risk_floor.to_dict():
            raise PolicyTamperingError("path_risk_floor_tampered")
        if [r.to_dict() for r in snapshot.capability_risk_rules] != [
            r.to_dict() for r in authorized.capability_risk_rules
        ]:
            raise PolicyTamperingError("capability_risk_rules_tampered")
