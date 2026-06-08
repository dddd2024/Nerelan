from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.local_reverse_constraint_recovery import recover_constraints, recover_target


def _profile_evidence(profile: str, profile_evidence: dict) -> dict:
    return {
        "profile": profile,
        "profile_evidence": profile_evidence,
        "source_artifact": "synthetic_fixture.json",
        "source_run": "synthetic_unit_test",
        "freshness": "current",
        "provenance_notes": ["synthetic normalized evidence"],
    }


def test_recover_constraints_dispatches_xor_array_table_compare() -> None:
    candidate = b"Dispatch1"
    array_a = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99]
    array_b = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
    target = [
        candidate[index] ^ array_a[len(candidate) - 1 - index] ^ array_b[index]
        for index in range(len(candidate))
    ]

    constraints, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_xor",
        classification="xor_array_table_compare",
        evidence=_profile_evidence(
            "xor_array_table_compare",
            {
                "array_a": array_a,
                "array_b": array_b,
                "target": target,
                "reverse_a": True,
                "encoding": "latin-1",
            },
        ),
        max_candidates=64,
    )

    assert blocked_reason == ""
    assert generation["count"] == 1
    assert candidates[0]["candidate"] == candidate.decode("ascii")
    assert candidates[0]["validation_status"] == "unverified"
    assert constraints[0]["kind"] == "profile_normalized_evidence"


def test_recover_constraints_dispatches_digit_mod_affine_compare() -> None:
    digits = "24680"
    target = [((4 + 3 * int(ch)) % 10) + ord("0") for ch in digits]

    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_digit",
        classification="digit_mod_affine_transform_compare",
        evidence=_profile_evidence(
            "digit_mod_affine_transform_compare",
            {
                "target": target,
                "a": 4,
                "b": 3,
                "modulus": 10,
                "offset": ord("0"),
                "domain": list(range(10)),
            },
        ),
        max_candidates=64,
    )

    assert blocked_reason == ""
    assert generation["strategy"] == "digit_mod_affine_transform_compare_normalized_profile"
    assert candidates[0]["candidate"] == digits
    assert candidates[0]["validation_status"] == "unverified"


def test_recover_constraints_dispatches_bytewise_transform_compare() -> None:
    def swap_low_bits(value: int) -> int:
        return (value & ~0x06) | ((value & 0x02) << 1) | ((value & 0x04) >> 1)

    candidate = b"ByteMap"
    target = [swap_low_bits(value) for value in candidate]

    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_bytewise",
        classification="bytewise_reversible_transform_table_compare",
        evidence=_profile_evidence(
            "bytewise_reversible_transform_table_compare",
            {
                "target": target,
                "transform_kind": "swap_low_bits_1_2",
                "transform_params": {"bit_a": 1, "bit_b": 2},
                "domain": "byte",
                "encoding": "latin-1",
            },
        ),
        max_candidates=64,
    )

    assert blocked_reason == ""
    assert generation["count"] == 1
    assert candidates[0]["candidate"] == candidate.decode("ascii")


def test_missing_profile_evidence_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, next_action = recover_constraints(
        sample_id="synthetic_missing",
        classification="xor_array_table_compare",
        evidence={"profile": "xor_array_table_compare", "freshness": "current"},
        max_candidates=64,
    )

    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "MISSING_PROFILE_NORMALIZED_EVIDENCE"
    assert next_action == "supply profile-normalized evidence for solver profile dispatch"


def test_unknown_bytewise_transform_kind_blocks_without_expression_execution() -> None:
    _, candidates, _, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_unknown_transform",
        classification="bytewise_reversible_transform_table_compare",
        evidence=_profile_evidence(
            "bytewise_reversible_transform_table_compare",
            {
                "target": [65],
                "transform_kind": "__import__('os').system('echo no')",
                "transform_params": {},
                "domain": "byte",
            },
        ),
        max_candidates=64,
    )

    assert candidates == []
    assert blocked_reason == "BLOCKED:UNSUPPORTED_TRANSFORM_KIND"


def test_runtime_disabled_target_path_does_not_call_probe_runner(tmp_path: Path) -> None:
    evidence_path = tmp_path / "normalized.json"
    candidate = b"NoProbe"
    array_a = [10, 20, 30, 40, 50, 60, 70]
    array_b = [1, 2, 3, 4, 5, 6, 7]
    target = [
        candidate[index] ^ array_a[len(candidate) - 1 - index] ^ array_b[index]
        for index in range(len(candidate))
    ]
    evidence_path.write_text(
        json.dumps(
            _profile_evidence(
                "xor_array_table_compare",
                {
                    "array_a": array_a,
                    "array_b": array_b,
                    "target": target,
                    "reverse_a": True,
                    "encoding": "latin-1",
                },
            )
        ),
        encoding="utf-8",
    )

    def fail_probe(**_: object) -> dict:
        raise AssertionError("probe_runner must not be called when runtime_allowed is false")

    target_result, _ = recover_target(
        summary_target={"sample_id": "synthetic", "relative_path": "unused.exe"},
        solver_target={"sample_id": "synthetic", "classification": "xor_array_table_compare"},
        artifact_index={
            "latest_artifacts_v2": {
                "local_reverse_ida_evidence_synthetic": {
                    "path": str(evidence_path),
                    "freshness": "current",
                }
            }
        },
        root=tmp_path,
        timeout=1,
        runtime_allowed=False,
        probe_runner=fail_probe,
        preview_limit=80,
        global_blocked_reasons=[],
        max_candidates_per_target=64,
        remaining_validations=10,
    )

    assert target_result["constraint_status"] == "recovered"
    assert target_result["validation_results"] == []
    assert target_result["candidates"][0]["candidate"] == candidate.decode("ascii")


def test_legacy_api_assisted_profile_still_generates_expected_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="legacy_cpp1",
        classification="api_assisted_password_write_and_compare",
        evidence={
            "compare_contexts": [{"callee": "__imp_lstrcmpA"}],
            "local_check_contexts": [{"ref_strings": "realpwd | pwd.txt | WriteFile"}],
            "decompiler_snippets": [
                {
                    "function": "_main_0",
                    "text": (
                        'strcpy((char *)Buffer, "realpwd"); '
                        'CreateFileA("pwd.txt", 0x10000000u, 0, 0, 2u, 0x80u, 0); '
                        "WriteFile(hFile, Buffer, v3, (LPDWORD)&Buffer[2], 0); "
                        "lstrcmpA(Buffer, String2);"
                    ),
                },
                {
                    "function": "sub_401100",
                    "text": (
                        "Str[0] = 26; Str[1] = 10; Str[2] = 14; Str[3] = 7; "
                        "Str[4] = 17; Str[5] = 7; Str[6] = 13; "
                        "for ( i = 0; i < 7; ++i ) Str[i] ^= v11[i];"
                    ),
                },
            ],
        },
        max_candidates=64,
    )

    assert blocked_reason == ""
    assert generation["strategy"] == "xor_constants_against_evidence_strings"
    assert "hookapi" in {item["candidate"] for item in candidates}


def test_top_level_profile_mismatch_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_mismatch",
        classification="xor_array_table_compare",
        evidence={
            "profile": "bytewise_reversible_transform_table_compare",
            "profile_evidence": {
                "target": [65],
                "transform_kind": "swap_low_bits_1_2",
                "transform_params": {"bit_a": 1, "bit_b": 2},
                "domain": "byte",
            },
            "freshness": "current",
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:PROFILE_CLASSIFICATION_MISMATCH"


def test_nested_profile_mismatch_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_nested_mismatch",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {},
            "freshness": "current",
            "normalized_profile_evidence": {
                "profile": "bytewise_reversible_transform_table_compare",
                "profile_evidence": {
                    "target": [65],
                    "transform_kind": "swap_low_bits_1_2",
                    "transform_params": {"bit_a": 1, "bit_b": 2},
                    "domain": "byte",
                },
                "freshness": "current",
            },
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:PROFILE_CLASSIFICATION_MISMATCH"


def test_stale_freshness_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_stale",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {
                "array_a": [0x11, 0x22, 0x33],
                "array_b": [0x01, 0x02, 0x03],
                "target": [0x10, 0x20, 0x30],
            },
            "freshness": "stale",
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:NON_CURRENT_PROFILE_EVIDENCE"


def test_missing_freshness_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_missing_freshness",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {
                "array_a": [0x11, 0x22, 0x33],
                "array_b": [0x01, 0x02, 0x03],
                "target": [0x10, 0x20, 0x30],
            },
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:NON_CURRENT_PROFILE_EVIDENCE"


def test_unknown_freshness_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_unknown",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {
                "array_a": [0x11, 0x22, 0x33],
                "array_b": [0x01, 0x02, 0x03],
                "target": [0x10, 0x20, 0x30],
            },
            "freshness": "unknown",
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:NON_CURRENT_PROFILE_EVIDENCE"


def test_empty_string_freshness_blocks_without_candidate() -> None:
    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_empty_freshness",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {
                "array_a": [0x11, 0x22, 0x33],
                "array_b": [0x01, 0x02, 0x03],
                "target": [0x10, 0x20, 0x30],
            },
            "freshness": "",
        },
        max_candidates=64,
    )
    assert candidates == []
    assert generation["count"] == 0
    assert blocked_reason == "BLOCKED:NON_CURRENT_PROFILE_EVIDENCE"


def test_current_freshness_and_matching_profile_happy_path() -> None:
    candidate = b"HappyPath"
    array_a = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99]
    array_b = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
    target = [
        candidate[index] ^ array_a[len(candidate) - 1 - index] ^ array_b[index]
        for index in range(len(candidate))
    ]

    _, candidates, generation, blocked_reason, _ = recover_constraints(
        sample_id="synthetic_happy",
        classification="xor_array_table_compare",
        evidence={
            "profile": "xor_array_table_compare",
            "profile_evidence": {
                "array_a": array_a,
                "array_b": array_b,
                "target": target,
                "reverse_a": True,
                "encoding": "latin-1",
            },
            "freshness": "current",
        },
        max_candidates=64,
    )
    assert blocked_reason == ""
    assert generation["count"] == 1
    assert candidates[0]["candidate"] == candidate.decode("ascii")
    assert candidates[0]["validation_status"] == "unverified"


def test_dispatch_production_modules_have_no_real_solved_candidates_hardcoded() -> None:
    module_text = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "reverse_agent/local_reverse_solver_profiles.py",
            "reverse_agent/local_reverse_constraint_recovery.py",
        )
    )

    for forbidden in ("KEEP_DREAM", "WeKnowItOk", "10013", "hookapi"):
        assert forbidden not in module_text
