"""Tests for local_reverse_cpp1_inverse_handoff.

Coverage:
1. forward_transform_byte and inverse_transform_byte roundtrip for 0..255.
2. Inverse formula on target bytes produces deterministic static_candidate_bytes_hex.
3. Non-printable static candidate -> BLOCKED / STATIC_CANDIDATE_NONPRINTABLE.
4. Printable synthetic target -> STATIC_CANDIDATE_DERIVED, runtime_validated=false.
5. Invalid target length -> BLOCKED / INVALID_TARGET_LENGTH.
6. Source artifact with candidate or known_candidate already set -> BLOCKED / UNEXPECTED_PRIOR_CANDIDATE.
7. Output artifact always has candidate=null and known_candidate="".
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.local_reverse_cpp1_inverse_handoff import (
    forward_transform_byte,
    inverse_transform_byte,
    run_cpp1_inverse_handoff,
)


# ---------------------------------------------------------------------------
# Roundtrip tests
# ---------------------------------------------------------------------------

def test_forward_inverse_roundtrip_all_bytes() -> None:
    """For every byte 0..255, inverse(forward(x)) == x."""
    for x in range(256):
        y = forward_transform_byte(x)
        assert 0 <= y <= 255
        x_recovered = inverse_transform_byte(y)
        assert x_recovered == x, f"roundtrip failed for x={x}: got {x_recovered}"


def test_inverse_forward_roundtrip_all_bytes() -> None:
    """For every byte 0..255, forward(inverse(y)) == y."""
    for y in range(256):
        x = inverse_transform_byte(y)
        assert 0 <= x <= 255
        y_recovered = forward_transform_byte(x)
        assert y_recovered == y, f"roundtrip failed for y={y}: got {y_recovered}"


# ---------------------------------------------------------------------------
# Helper to build synthetic target-bytes artifacts
# ---------------------------------------------------------------------------

def _make_target_bytes_artifact(
    *,
    target_bytes: list[int],
    candidate: None | str = None,
    known_candidate: str = "",
    executed_sample: bool = False,
    static_only: bool = True,
    runtime_validated: bool = False,
    extra_evidence_notes: list[str] | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": "逆向课程2023春01/CPP1.exe",
        "analysis_mode": "target_compare_byte_extraction",
        "mainline": "tool_integration",
        "executed_sample": executed_sample,
        "static_only": static_only,
        "runtime_validated": runtime_validated,
        "generated_at": "2026-06-05T09:11:46Z",
        "tool_status": "success",
        "blocked_reason": "",
        "expected_target_length": 16,
        "source_tool": "IDA",
        "target_symbol": "byte_429A30",
        "target_address": "0x00429A30",
        "target_length": len(target_bytes),
        "target_bytes_hex": "".join(f"{b:02x}" for b in target_bytes),
        "target_bytes": target_bytes,
        "main_function": "_main_0",
        "main_function_address": "0x00401190",
        "forward_transform": {
            "input_buffer": "Str",
            "work_buffer": "Destination",
            "copy_length": 16,
            "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
            "compare_expression": "Destination[i] == byte_429A30[i]",
            "notes": [],
        },
        "compare_expression": "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )",
        "loop_context": "for ( i = 0; i < v4; ++i )",
        "evidence_notes": extra_evidence_notes or [
            "length discrepancy: input must be 18 chars but compare loop checks 16 bytes",
            "division operation detected in path; potential anti-debug trap or dead code",
        ],
        "candidate": candidate,
        "known_candidate": known_candidate,
        "recommended_next_action": "Next round: create inverse-transform handoff.",
    }


# ---------------------------------------------------------------------------
# Deterministic inverse on real target bytes
# ---------------------------------------------------------------------------

def test_inverse_on_real_target_bytes() -> None:
    """Inverse of the real target bytes must produce the expected static candidate."""
    real_target = [213, 150, 196, 246, 7, 69, 87, 119, 118, 229, 246, 72, 71, 247, 72, 23]
    artifact = _make_target_bytes_artifact(target_bytes=real_target)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "STATIC_CANDIDATE_NONPRINTABLE"
    # static_candidate_bytes_hex is the INVERSE of target bytes, not the target itself
    assert result["static_candidate_bytes_hex"] == "5d5a1cde131557d7d69dde2417df2453"
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["runtime_validated"] is False
    assert result["static_only"] is True
    assert result["executed_sample"] is False


# ---------------------------------------------------------------------------
# Printable synthetic target -> STATIC_CANDIDATE_DERIVED
# ---------------------------------------------------------------------------

def test_printable_synthetic_target() -> None:
    """A synthetic target that inverses to printable ASCII should yield STATIC_CANDIDATE_DERIVED."""
    # Choose a printable plaintext, forward-transform it, then feed as target
    plaintext = b"HelloWorld123456"
    synthetic_target = [forward_transform_byte(b) for b in plaintext]
    artifact = _make_target_bytes_artifact(target_bytes=synthetic_target)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "STATIC_CANDIDATE_DERIVED"
    assert result["blocked_reason"] == ""
    assert result["static_candidate_text"] == plaintext.decode("ascii")
    assert result["printable_ascii"] is True
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["runtime_validated"] is False


# ---------------------------------------------------------------------------
# Non-printable target -> BLOCKED
# ---------------------------------------------------------------------------

def test_non_printable_target_blocked() -> None:
    """Target bytes that inverse to non-printable must be BLOCKED."""
    # Forward transform of bytes that include control chars
    plaintext = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    synthetic_target = [forward_transform_byte(b) for b in plaintext]
    artifact = _make_target_bytes_artifact(target_bytes=synthetic_target)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "STATIC_CANDIDATE_NONPRINTABLE"
    assert result["printable_ascii"] is False
    assert result["static_candidate_text"] is None


# ---------------------------------------------------------------------------
# Invalid target length -> BLOCKED
# ---------------------------------------------------------------------------

def test_invalid_target_length() -> None:
    """Target bytes length != 16 must be BLOCKED."""
    artifact = _make_target_bytes_artifact(target_bytes=[1, 2, 3])

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "INVALID_TARGET_LENGTH"


# ---------------------------------------------------------------------------
# Unexpected prior candidate -> BLOCKED
# ---------------------------------------------------------------------------

def test_unexpected_prior_candidate() -> None:
    """Artifact with candidate already set must be BLOCKED."""
    synthetic_target = [forward_transform_byte(b) for b in b"HelloWorld123456"]
    artifact = _make_target_bytes_artifact(target_bytes=synthetic_target, candidate="some_candidate")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "UNEXPECTED_PRIOR_CANDIDATE"


def test_unexpected_prior_known_candidate() -> None:
    """Artifact with known_candidate already set must be BLOCKED."""
    synthetic_target = [forward_transform_byte(b) for b in b"HelloWorld123456"]
    artifact = _make_target_bytes_artifact(target_bytes=synthetic_target, known_candidate="secret")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "UNEXPECTED_PRIOR_CANDIDATE"


# ---------------------------------------------------------------------------
# Output invariants
# ---------------------------------------------------------------------------

def test_output_always_null_candidate_empty_known() -> None:
    """Regardless of status, output must have candidate=null and known_candidate=''."""
    synthetic_target = [forward_transform_byte(b) for b in b"HelloWorld123456"]
    artifact = _make_target_bytes_artifact(target_bytes=synthetic_target)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "target_bytes.json"
        out_path = Path(tmpdir) / "inverse_handoff.json"
        input_path.write_text(json.dumps(artifact), encoding="utf-8")

        result = run_cpp1_inverse_handoff(input_path, out_path)

    assert result["candidate"] is None
    assert result["known_candidate"] == ""


# ---------------------------------------------------------------------------
# Bit mapping consistency
# ---------------------------------------------------------------------------

def test_bit_mapping_consistency() -> None:
    """forward and inverse bit_mapping arrays must be consistent."""
    # We verify that for a few known bit patterns the mapping holds.
    # x=0bABCDEFGH -> y bits according to mapping
    test_cases = [
        (0b00000000, 0b00000000),
        (0b11111111, 0b11111111),
        (0b10101010, (0b10101010 & 0x03) | ((0b10101010 & 0x0C) << 4) | ((0b10101010 & 0xF0) >> 2)),
        (0b01010101, (0b01010101 & 0x03) | ((0b01010101 & 0x0C) << 4) | ((0b01010101 & 0xF0) >> 2)),
    ]
    for x, expected_y in test_cases:
        assert forward_transform_byte(x) == expected_y
        assert inverse_transform_byte(expected_y) == x
