"""Tests for reverse_agent.solver_dispatch_plan."""

from __future__ import annotations

import pytest

from reverse_agent.evidence import (
    StructuredEvidence,
    static_compare_evidence,
    static_constant_evidence,
    static_crypto_signature_evidence,
    static_input_evidence,
    static_transform_hint_evidence,
)
from reverse_agent.solver_dispatch_plan import (
    PROFILE_AFFINE_SHIFT,
    PROFILE_ANTI_DEBUG_PRECONDITION,
    PROFILE_DES,
    PROFILE_GUI_CHECK,
    PROFILE_LOOKUP_TABLE,
    PROFILE_RC4,
    PROFILE_STRING_COMPARE,
    PROFILE_XOR,
    READINESS_NEEDS_CURRENT_STATIC_PROVENANCE,
    READINESS_NOT_SOLVE_READY,
    READINESS_SOLVER_PROFILE_HINT_ONLY,
    SolverDispatchPlan,
    build_solver_dispatch_plan,
)


def test_plan_defaults_conservative():
    plan = SolverDispatchPlan()
    assert plan.readiness == READINESS_SOLVER_PROFILE_HINT_ONLY
    assert plan.recommended_solver_profiles == []
    assert plan.required_missing_evidence == []
    assert plan.source_artifacts == []
    assert plan.provenance_notes == []


def test_plan_validate_rejects_invalid_readiness():
    plan = SolverDispatchPlan(readiness="bogus")
    with pytest.raises(ValueError):
        plan.validate()


def test_plan_to_dict_roundtrip():
    plan = SolverDispatchPlan(
        readiness=READINESS_NEEDS_CURRENT_STATIC_PROVENANCE,
        recommended_solver_profiles=[PROFILE_STRING_COMPARE],
        required_missing_evidence=["comparison_sink_evidence"],
        source_artifacts=["artifact.json"],
        provenance_notes=["static-only"],
    )
    d = plan.to_dict()
    assert d["readiness"] == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE
    assert d["recommended_solver_profiles"] == [PROFILE_STRING_COMPARE]
    assert d["required_missing_evidence"] == ["comparison_sink_evidence"]
    assert d["source_artifacts"] == ["artifact.json"]
    assert d["provenance_notes"] == ["static-only"]


def test_empty_evidence_yields_hint_only_with_missing():
    plan = build_solver_dispatch_plan([])
    assert plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE
    assert "input_source_evidence" in plan.required_missing_evidence
    assert "comparison_sink_evidence" in plan.required_missing_evidence


def test_input_and_compare_yields_string_compare():
    evidence = [
        static_input_evidence("IDA", input_apis=["scanf"]),
        static_compare_evidence("IDA", compare_apis=["_strncmp"]),
    ]
    plan = build_solver_dispatch_plan(evidence, has_current_provenance=True)
    assert PROFILE_STRING_COMPARE in plan.recommended_solver_profiles
    # input + compare present means no missing input/compare
    assert "input_source_evidence" not in plan.required_missing_evidence
    assert "comparison_sink_evidence" not in plan.required_missing_evidence


def test_xor_transform_yields_xor_profile():
    evidence = [
        static_input_evidence("IDA", input_apis=["scanf"]),
        static_compare_evidence("IDA", compare_apis=["_strncmp"]),
        static_transform_hint_evidence("IDA", transform_kind="xor"),
    ]
    plan = build_solver_dispatch_plan(evidence, has_current_provenance=True)
    assert PROFILE_XOR in plan.recommended_solver_profiles
    # transform without constants -> missing transform_constant_evidence
    assert "transform_constant_evidence" in plan.required_missing_evidence


def test_affine_transform_yields_affine_profile():
    evidence = [
        static_transform_hint_evidence("IDA", transform_kind="affine"),
    ]
    plan = build_solver_dispatch_plan(evidence)
    assert PROFILE_AFFINE_SHIFT in plan.recommended_solver_profiles


def test_lookup_table_transform_yields_lookup_profile():
    evidence = [
        static_transform_hint_evidence("IDA", transform_kind="lookup", table_lookup=True),
    ]
    plan = build_solver_dispatch_plan(evidence)
    assert PROFILE_LOOKUP_TABLE in plan.recommended_solver_profiles


def test_rc4_crypto_yields_rc4_profile():
    evidence = [
        static_crypto_signature_evidence("IDA", algorithm="rc4", markers=["ksa"]),
    ]
    plan = build_solver_dispatch_plan(evidence)
    assert PROFILE_RC4 in plan.recommended_solver_profiles
    # crypto without constants -> missing key_or_constant_evidence
    assert "key_or_constant_evidence" in plan.required_missing_evidence


def test_des_crypto_yields_des_profile():
    evidence = [
        static_crypto_signature_evidence("IDA", algorithm="des", markers=["sbox"]),
    ]
    plan = build_solver_dispatch_plan(evidence)
    assert PROFILE_DES in plan.recommended_solver_profiles


def test_crypto_with_constants_no_missing_key():
    evidence = [
        static_crypto_signature_evidence("IDA", algorithm="rc4", markers=["ksa"]),
        static_constant_evidence("IDA", constants=[0x00, 0x01]),
    ]
    plan = build_solver_dispatch_plan(evidence, has_current_provenance=True)
    assert "key_or_constant_evidence" not in plan.required_missing_evidence


def test_no_current_provenance_caps_readiness():
    evidence = [
        static_input_evidence("IDA", input_apis=["scanf"]),
        static_compare_evidence("IDA", compare_apis=["_strncmp"]),
        static_constant_evidence("IDA", constants=[0x01]),
    ]
    plan = build_solver_dispatch_plan(evidence, has_current_provenance=False)
    assert plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE


def test_full_evidence_with_provenance_still_hint_only():
    """Even with full evidence and provenance, readiness is hint-only.

    The bridge never claims solve-readiness; solver_profile_hint_only is the
    strongest readiness for static-only evidence.
    """
    evidence = [
        static_input_evidence("IDA", input_apis=["scanf"]),
        static_compare_evidence("IDA", compare_apis=["_strncmp"]),
        static_constant_evidence("IDA", constants=[0x01]),
        static_crypto_signature_evidence("IDA", algorithm="rc4", markers=["ksa", "prga"]),
    ]
    plan = build_solver_dispatch_plan(evidence, has_current_provenance=True)
    assert plan.readiness == READINESS_SOLVER_PROFILE_HINT_ONLY
    assert plan.required_missing_evidence == []


def test_profiles_dedupe():
    evidence = [
        static_transform_hint_evidence("IDA", transform_kind="xor"),
        static_transform_hint_evidence("IDA", transform_kind="xor"),
    ]
    plan = build_solver_dispatch_plan(evidence)
    assert plan.recommended_solver_profiles.count(PROFILE_XOR) == 1


def test_source_artifacts_and_provenance_notes_passed_through():
    evidence = [static_input_evidence("IDA", input_apis=["scanf"])]
    plan = build_solver_dispatch_plan(
        evidence,
        source_artifacts=["triage.json"],
        provenance_notes=["static-only"],
    )
    assert plan.source_artifacts == ["triage.json"]
    assert plan.provenance_notes == ["static-only"]
