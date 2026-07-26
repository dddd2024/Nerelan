from __future__ import annotations

from dataclasses import replace

import pytest

from reverse_agent.base_platform import (
    PUBLICATION_BRANCH_AND_DRAFT_PR,
    PUBLICATION_DENIED,
    BasePlatformError,
    CapabilityManifest,
    PolicyResolver,
    canonical_digest,
    resolve_policy,
)


def test_identical_approved_inputs_produce_identical_policy_and_digest(
    approved_spec,
    capabilities,
) -> None:
    first = resolve_policy(approved_spec, capabilities)
    second = resolve_policy(approved_spec, capabilities)

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.digest() == second.digest()
    assert first.canonical_input_digest == canonical_digest(
        {
            "resolver_version": "0.1",
            "source_spec": approved_spec,
            "capability_manifest": capabilities,
        }
    )


def test_unapproved_spec_fails_before_policy_resolution(approved_spec, capabilities) -> None:
    with pytest.raises(BasePlatformError) as captured:
        resolve_policy(replace(approved_spec, approved=False), capabilities)

    assert captured.value.code == "SPEC_NOT_APPROVED"


def test_required_capability_mismatch_is_rejected(approved_spec, capabilities) -> None:
    reduced = replace(capabilities, supported_operations=("source_edit",))

    with pytest.raises(BasePlatformError) as captured:
        resolve_policy(approved_spec, reduced)

    assert captured.value.code == "CAPABILITY_OPERATION_MISMATCH"
    assert captured.value.details["operations"] == ["unit_test"]


def test_risk_capability_mismatch_is_rejected(approved_spec, capabilities) -> None:
    reduced = replace(capabilities, supported_risk_tiers=("R0",))

    with pytest.raises(BasePlatformError) as captured:
        resolve_policy(approved_spec, reduced)

    assert captured.value.code == "CAPABILITY_RISK_MISMATCH"


def test_forbidden_operations_override_allowed_operations(approved_spec, capabilities) -> None:
    policy = resolve_policy(
        replace(
            approved_spec,
            forbidden_operations=("source_edit", "merge"),
            required_operations=("unit_test",),
        ),
        capabilities,
    )

    assert "source_edit" not in policy.allowed_operations
    assert policy.forbidden_operations == ("merge", "source_edit")


def test_required_forbidden_operation_is_rejected(approved_spec, capabilities) -> None:
    with pytest.raises(BasePlatformError) as captured:
        resolve_policy(
            replace(
                approved_spec,
                forbidden_operations=("unit_test",),
            ),
            capabilities,
        )

    assert captured.value.code == "REQUIRED_OPERATION_FORBIDDEN"


def test_allowed_operations_are_bounded_intersection(approved_spec, capabilities) -> None:
    policy = resolve_policy(approved_spec, capabilities)

    assert policy.allowed_operations == ("source_edit", "unit_test")
    assert "draft_pr" not in policy.allowed_operations


def test_required_checks_are_deduplicated_and_stably_sorted(approved_spec, capabilities) -> None:
    policy = resolve_policy(approved_spec, capabilities)

    assert policy.required_checks == (
        "git diff --check",
        "pytest",
        "static-import-check",
    )


def test_publication_defaults_to_denied(approved_spec, capabilities) -> None:
    policy = resolve_policy(approved_spec, capabilities)

    assert policy.publication_permission == PUBLICATION_DENIED


def test_bounded_r1_publication_never_authorizes_merge(approved_spec, capabilities) -> None:
    publishing_spec = replace(
        approved_spec,
        requested_publication_permission=PUBLICATION_BRANCH_AND_DRAFT_PR,
    )
    publishing_capabilities = replace(
        capabilities,
        publication_permissions=(PUBLICATION_DENIED, PUBLICATION_BRANCH_AND_DRAFT_PR),
    )

    policy = resolve_policy(publishing_spec, publishing_capabilities)

    assert policy.publication_permission == PUBLICATION_BRANCH_AND_DRAFT_PR
    assert "merge" not in policy.allowed_operations
    assert "merge" in policy.forbidden_operations
    assert "merge" not in publishing_capabilities.publication_permissions


def test_publication_capability_mismatch_fails_closed(approved_spec, capabilities) -> None:
    publishing_spec = replace(
        approved_spec,
        requested_publication_permission=PUBLICATION_BRANCH_AND_DRAFT_PR,
    )

    with pytest.raises(BasePlatformError) as captured:
        resolve_policy(publishing_spec, capabilities)

    assert captured.value.code == "CAPABILITY_PUBLICATION_MISMATCH"


def test_resolver_binds_all_required_provenance(approved_spec, capabilities) -> None:
    resolver = PolicyResolver(version="0.1-test")
    policy = resolver.resolve(approved_spec, capabilities)

    assert policy.source_spec_identity == approved_spec.identity
    assert policy.capability_manifest_identity == capabilities.identity
    assert policy.resolver_version == "0.1-test"
    assert len(policy.canonical_input_digest) == 64
    assert policy.identity == f"policy:sha256:{policy.canonical_input_digest}"
    assert policy.retry_policy.max_attempts == 2


def test_resolver_is_sole_source_for_all_derived_policy_fields(
    approved_spec,
    capabilities,
) -> None:
    policy = resolve_policy(approved_spec, capabilities)

    assert {
        "risk_tier",
        "allowed_operations",
        "forbidden_operations",
        "required_approval",
        "required_checks",
        "retry_policy",
        "publication_permission",
    }.issubset(policy.to_dict())


def test_manifest_rejects_unknown_publication_capability() -> None:
    with pytest.raises(BasePlatformError) as captured:
        CapabilityManifest(
            identity="capabilities:bad",
            supported_operations=(),
            supported_risk_tiers=("R1",),
            publication_permissions=("merge",),
        )

    assert captured.value.code == "UNSUPPORTED_PUBLICATION_PERMISSION"
