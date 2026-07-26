"""The sole M1 computation source for all derived execution-policy facts."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import (
    PUBLICATION_BRANCH_AND_DRAFT_PR,
    PUBLICATION_DENIED,
    CapabilityManifest,
    ResolvedExecutionPolicy,
    RetryPolicy,
    SpecPackage,
)
from ..errors import fail
from ..serialization import canonical_digest


RESOLVER_VERSION = "0.1"


@dataclass(frozen=True)
class PolicyResolver:
    """Resolve approved specification intent against bounded capabilities."""

    version: str = RESOLVER_VERSION

    def resolve(
        self,
        spec: SpecPackage,
        capabilities: CapabilityManifest,
    ) -> ResolvedExecutionPolicy:
        if not isinstance(spec, SpecPackage) or not isinstance(capabilities, CapabilityManifest):
            fail(
                "INVALID_RESOLVER_INPUT",
                "Policy resolution requires a SpecPackage and CapabilityManifest.",
            )
        if not spec.approved:
            fail(
                "SPEC_NOT_APPROVED",
                "An unapproved SpecPackage cannot produce execution policy.",
                spec_identity=spec.identity,
            )

        risk_tier = spec.requested_risk_tier.upper()
        if risk_tier not in capabilities.supported_risk_tiers:
            fail(
                "CAPABILITY_RISK_MISMATCH",
                "The capability manifest does not support the requested risk tier.",
                risk_tier=risk_tier,
            )

        spec_allowed = set(spec.allowed_operations)
        supported = set(capabilities.supported_operations)
        forbidden = set(spec.forbidden_operations)
        allowed_operations = tuple(sorted((spec_allowed & supported) - forbidden))

        required = set(spec.required_operations)
        capability_missing = required - supported
        if capability_missing:
            fail(
                "CAPABILITY_OPERATION_MISMATCH",
                "Required operations are absent from the capability manifest.",
                operations=sorted(capability_missing),
            )
        outside_approved_scope = required - spec_allowed
        if outside_approved_scope:
            fail(
                "REQUIRED_OPERATION_OUTSIDE_SCOPE",
                "Required operations are absent from the approved specification scope.",
                operations=sorted(outside_approved_scope),
            )
        forbidden_required = required & forbidden
        if forbidden_required:
            fail(
                "REQUIRED_OPERATION_FORBIDDEN",
                "A forbidden operation cannot be required.",
                operations=sorted(forbidden_required),
            )

        required_checks = tuple(
            sorted(set(spec.goal.required_checks) | set(spec.required_checks) | set(capabilities.required_checks))
        )
        requested_retry = spec.requested_retry_policy
        if requested_retry is None:
            fail("INVALID_RETRY_POLICY", "SpecPackage retry policy was not normalized.")
        retry_policy = RetryPolicy(
            identity=f"{spec.identity}:resolved-retry",
            max_attempts=min(requested_retry.max_attempts, capabilities.max_retry_attempts),
            retryable_error_codes=requested_retry.retryable_error_codes,
        )
        publication_permission = self._resolve_publication(spec, capabilities, risk_tier)
        input_digest = canonical_digest(
            {
                "resolver_version": self.version,
                "source_spec": spec,
                "capability_manifest": capabilities,
            }
        )
        return ResolvedExecutionPolicy(
            identity=f"policy:sha256:{input_digest}",
            risk_tier=risk_tier,
            allowed_operations=allowed_operations,
            forbidden_operations=tuple(sorted(forbidden)),
            required_approval=spec.required_approval,
            required_checks=required_checks,
            retry_policy=retry_policy,
            publication_permission=publication_permission,
            source_spec_identity=spec.identity,
            capability_manifest_identity=capabilities.identity,
            resolver_version=self.version,
            canonical_input_digest=input_digest,
        )

    @staticmethod
    def _resolve_publication(
        spec: SpecPackage,
        capabilities: CapabilityManifest,
        risk_tier: str,
    ) -> str:
        requested = spec.requested_publication_permission
        if requested == PUBLICATION_DENIED:
            return PUBLICATION_DENIED
        if requested != PUBLICATION_BRANCH_AND_DRAFT_PR:
            fail(
                "UNSUPPORTED_PUBLICATION_PERMISSION",
                "Resolver only supports denied or bounded branch/Draft-PR publication.",
                permission=requested,
            )
        if risk_tier != "R1":
            fail(
                "PUBLICATION_RISK_MISMATCH",
                "Bounded branch/Draft-PR publication is only derivable for R1.",
                risk_tier=risk_tier,
            )
        if requested not in capabilities.publication_permissions:
            fail(
                "CAPABILITY_PUBLICATION_MISMATCH",
                "The capability manifest does not support the requested publication boundary.",
                permission=requested,
            )
        return PUBLICATION_BRANCH_AND_DRAFT_PR


def resolve_policy(
    spec: SpecPackage,
    capabilities: CapabilityManifest,
    *,
    resolver_version: str = RESOLVER_VERSION,
) -> ResolvedExecutionPolicy:
    return PolicyResolver(version=resolver_version).resolve(spec, capabilities)
