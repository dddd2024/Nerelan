"""Synthetic tests for static triage type evidence normalization.

These tests do not run IDA, samples, solvers, harnesses, debuggers, or runtime
probes. They only exercise pure adapter helpers with synthetic dictionaries.
"""

import json

from reverse_agent.local_reverse_single_sample_static_triage import (
    TYPE_EVIDENCE_PROFILE_IDS,
    _blocked_artifact,
    _extract_type_evidence,
    _parse_ida_evidence,
)


def _profile(payload: dict, profile_id: str) -> dict:
    return payload["profiles"][profile_id]


def _statuses(payload: dict) -> set[str]:
    return {profile["status"] for profile in payload["profiles"].values()}


def test_parse_ida_evidence_adds_type_evidence_for_compare_context() -> None:
    triage = _parse_ida_evidence(
        {
            "compare_contexts": [
                {
                    "call_ea": "0x401000",
                    "callee": "strcmp",
                    "nearby": "push input || push expected",
                    "ref_strings": "correct",
                }
            ],
            "functions": ["main", "strcmp"],
        },
        0,
    )

    evidence = triage["type_evidence"]

    assert _profile(evidence, "string_comparison")["status"] == "candidate_static_signal"
    assert "static_verified" not in _statuses(evidence)
    assert set(evidence["profiles"]) == set(TYPE_EVIDENCE_PROFILE_IDS)


def test_xor_decompiler_text_marks_xor_and_bit_operations() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["for (i=0; i<n; i++) out[i] = input[i] xor key[i];"]},
        {},
    )

    assert _profile(evidence, "xor")["status"] == "candidate_static_signal"
    assert _profile(evidence, "bit_operations")["status"] == "candidate_static_signal"


def test_shift_affine_text_marks_candidate_signal() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["y = ((x << 3) + 7) mod 251; affine transform loop"]},
        {},
    )

    assert _profile(evidence, "shift_affine")["status"] == "candidate_static_signal"


def test_lookup_table_access_without_base_size_contents_is_blocked() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["value = lookup_table[input[i]]; indexed array access"]},
        {},
    )
    profile = _profile(evidence, "lookup_table")

    assert profile["status"] == "blocked_missing_required_evidence"
    assert profile["table_evidence"]["access"]["observed"] is True
    assert profile["table_evidence"]["base"]["observed"] is False
    assert profile["table_evidence"]["size"]["observed"] is False
    assert profile["table_evidence"]["contents"]["observed"] is False


def test_rc4_ksa_prga_sbox_key_text_marks_candidate_signal() -> None:
    evidence = _extract_type_evidence(
        {
            "decompiler_snippets": [
                "RC4 KSA and PRGA loop with 256-byte state array S-box; rc4 key material is read from const string"
            ]
        },
        {},
    )

    profile = _profile(evidence, "rc4")
    assert profile["status"] == "candidate_static_signal"
    assert "ksa_or_prga" in profile["observed_evidence"]
    assert "sbox" in profile["observed_evidence"]
    assert "key" in profile["observed_evidence"]


def test_des_sbox_permutation_key_schedule_marks_candidate_signal() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["DES round uses S-box, initial permutation PC1 PC2, and key schedule subkeys"]},
        {},
    )

    profile = _profile(evidence, "des")
    assert profile["status"] == "candidate_static_signal"
    assert "key_schedule" in profile["observed_evidence"]


def test_hash_constants_without_bounded_domain_are_blocked() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["SHA-256 constants include 0x6a09e667 and hash compare"]},
        {},
    )
    profile = _profile(evidence, "hash_md5_sha")

    assert profile["status"] == "blocked_missing_required_evidence"
    assert profile["bounded_domain_required"] is True
    assert profile["solver_ready"] is False
    assert all(not item["observed"] for item in profile["bounded_domain_evidence"].values())


def test_hash_bounded_domain_evidence_does_not_emit_static_verified() -> None:
    evidence = _extract_type_evidence(
        {
            "decompiler_snippets": [
                "SHA-256 hash compare with input length 8, charset digits lowercase, format flag{prefix}"
            ]
        },
        {},
    )
    profile = _profile(evidence, "hash_md5_sha")

    assert profile["status"] == "candidate_static_signal"
    assert profile["bounded_domain_evidence"]["length"]["observed"] is True
    assert profile["bounded_domain_evidence"]["charset"]["observed"] is True
    assert profile["bounded_domain_evidence"]["format"]["observed"] is True
    assert profile["solver_ready"] is False
    assert "static_verified" not in _statuses(evidence)


def test_antidebug_api_and_seh_mark_static_signal_only() -> None:
    evidence = _extract_type_evidence(
        {"decompiler_snippets": ["IsDebuggerPresent check with SEH anti-debug branch"]},
        {},
    )
    profile = _profile(evidence, "simple_antidebug")

    assert profile["status"] == "candidate_static_signal"
    assert any("debugger execution is outside" in blocker for blocker in profile["promotion_blockers"])


def test_blocked_artifact_contains_default_type_evidence() -> None:
    artifact = _blocked_artifact(
        sample_id="missing",
        relative_path="",
        sha256="",
        size_bytes=0,
        file_type="",
        category="",
        tags=[],
        blocked_reason="BINARY_NOT_FOUND",
    )
    evidence = artifact["triage"]["type_evidence"]

    assert evidence["source"] == "blocked_artifact_default"
    assert set(evidence["profiles"]) == set(TYPE_EVIDENCE_PROFILE_IDS)
    assert all(profile["status"] == "not_observed" for profile in evidence["profiles"].values())
    assert evidence["profiles"]["hash_md5_sha"]["bounded_domain_required"] is True
    assert evidence["profiles"]["lookup_table"]["table_evidence"]["access"]["observed"] is False
