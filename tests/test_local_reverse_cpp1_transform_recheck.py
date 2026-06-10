"""Tests for local_reverse_cpp1_transform_recheck.

Coverage:
1. forward_transform_byte and inverse_transform_byte roundtrip for 0..255.
2. analyze_mapping confirms bijection.
3. analyze_printable_preimages on real target bytes.
4. analyze_length_compare_semantics extracts expected observations.
5. run_cpp1_transform_recheck produces BLOCKED artifact with correct fields.
6. CLI generates JSON artifact.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.local_reverse_cpp1_transform_recheck import (
    analyze_length_compare_semantics,
    analyze_mapping,
    analyze_printable_preimages,
    forward_transform_byte,
    inverse_transform_byte,
    run_cpp1_transform_recheck,
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
# Mapping analysis
# ---------------------------------------------------------------------------

def test_analyze_mapping_bijective() -> None:
    """Transform must be bijective on 0..255."""
    result = analyze_mapping()
    assert result["forward_unique_outputs"] is True
    assert result["inverse_unique_outputs"] is True
    assert result["roundtrip_forward_inverse"] is True
    assert result["roundtrip_inverse_forward"] is True
    assert result["bijective"] is True


# ---------------------------------------------------------------------------
# Printable preimage analysis
# ---------------------------------------------------------------------------

def test_analyze_printable_preimages_real_target() -> None:
    """Real target bytes should be analyzed for printable preimages."""
    real_target = [213, 150, 196, 246, 7, 69, 87, 119, 118, 229, 246, 72, 71, 247, 72, 23]
    result = analyze_printable_preimages(real_target)

    assert "per_byte_analysis" in result
    assert len(result["per_byte_analysis"]) == 16

    # Check structure of per-byte entries
    for entry in result["per_byte_analysis"]:
        assert "index" in entry
        assert "target_byte" in entry
        assert "has_printable_preimage" in entry
        assert "printable_preimages" in entry

    # The specific inverse candidate may not be printable, but we need to check
    # if ANY printable preimage exists for each target byte
    # This depends on the transform properties


# ---------------------------------------------------------------------------
# Length/compare semantics analysis
# ---------------------------------------------------------------------------

def test_analyze_length_compare_semantics() -> None:
    """Semantics analysis should extract key observations from pseudocode."""
    triage = {
        "triage": {
            "decompiler_snippets": [
                {
                    "text": (
                        "v4 = strlen(Str);\n"
                        "if ( v4 != 18 )\n"
                        "  printf(\"Sorry,you are wrong!\\n\");\n"
                        "strncpy(Destination, Str, 0x10u);\n"
                        "v6 = v9 / v8;\n"
                        "for ( i = 0; i < v4; ++i )\n"
                        "  Destination[i] = ...;\n"
                        "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )\n"
                        "  ;\n"
                        "if ( i == 16 )\n"
                        "  printf(\"Congratulations!\");\n"
                    )
                }
            ]
        }
    }
    result = analyze_length_compare_semantics(triage)

    assert result["main_pseudocode_present"] is True
    observations = result["observations"]
    assert any("18" in obs for obs in observations)
    assert any("strncpy" in obs for obs in observations)
    assert any("16" in obs for obs in observations)
    assert any("division" in obs for obs in observations)

    length_check = result["length_check"]
    assert length_check["input_required_length"] == 18
    assert length_check["strncpy_copy_length"] == 16
    assert length_check["success_match_count"] == 16


# ---------------------------------------------------------------------------
# Integration: run_cpp1_transform_recheck
# ---------------------------------------------------------------------------

def _make_target_bytes_artifact() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "target_length": 16,
        "target_bytes_hex": "d596c4f60745577776e5f64847f74817",
        "target_bytes": [213, 150, 196, 246, 7, 69, 87, 119, 118, 229, 246, 72, 71, 247, 72, 23],
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "candidate": None,
        "known_candidate": "",
    }


def _make_inverse_handoff_artifact() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "candidate": None,
        "known_candidate": "",
        "status": "BLOCKED",
        "blocked_reason": "STATIC_CANDIDATE_NONPRINTABLE",
    }


def _make_triage_artifact() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "triage": {
            "decompiler_snippets": [
                {
                    "text": (
                        "v4 = strlen(Str);\n"
                        "if ( v4 != 18 )\n"
                        "  printf(\"Sorry,you are wrong!\\n\");\n"
                        "strncpy(Destination, Str, 0x10u);\n"
                        "v6 = v9 / v8;\n"
                        "for ( i = 0; i < v4; ++i )\n"
                        "  Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2);\n"
                        "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )\n"
                        "  ;\n"
                        "if ( i == 16 )\n"
                        "  printf(\"Congratulations! You are right!\\n\");\n"
                    )
                }
            ]
        },
    }


def test_run_cpp1_transform_recheck_integration() -> None:
    """Full integration test with synthetic artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "target_bytes.json"
        inverse_path = Path(tmpdir) / "inverse_handoff.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "transform_recheck.json"

        target_path.write_text(json.dumps(_make_target_bytes_artifact()), encoding="utf-8")
        inverse_path.write_text(json.dumps(_make_inverse_handoff_artifact()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage_artifact()), encoding="utf-8")

        result = run_cpp1_transform_recheck(target_path, inverse_path, triage_path, out_path)

        # Verify artifact was written inside temp dir context
        assert out_path.exists()
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert written["sample_id"] == "cpp1_2f6fcb63"

    # Verify key fields
    assert result["sample_id"] == "cpp1_2f6fcb63"
    assert result["analysis_mode"] == "static_transform_semantics_recheck"
    assert result["mainline"] == "reverse_solving"
    assert result["executed_sample"] is False
    assert result["static_only"] is True
    assert result["runtime_validated"] is False
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["status"] == "BLOCKED"

    # Verify mapping analysis
    assert result["mapping_analysis"]["bijective"] is True

    # Verify printable preimage analysis exists
    assert "printable_preimage_analysis" in result
    assert "per_byte_analysis" in result["printable_preimage_analysis"]
    assert len(result["printable_preimage_analysis"]["per_byte_analysis"]) == 16

    # Verify length/compare semantics
    assert "length_compare_semantics" in result
    semantics = result["length_compare_semantics"]
    assert semantics["length_check"]["input_required_length"] == 18
    assert semantics["length_check"]["strncpy_copy_length"] == 16
    assert semantics["length_check"]["success_match_count"] == 16


# ---------------------------------------------------------------------------
# Output invariants
# ---------------------------------------------------------------------------

def test_output_always_null_candidate_empty_known() -> None:
    """Output must have candidate=null and known_candidate=''."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "target_bytes.json"
        inverse_path = Path(tmpdir) / "inverse_handoff.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "transform_recheck.json"

        target_path.write_text(json.dumps(_make_target_bytes_artifact()), encoding="utf-8")
        inverse_path.write_text(json.dumps(_make_inverse_handoff_artifact()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage_artifact()), encoding="utf-8")

        result = run_cpp1_transform_recheck(target_path, inverse_path, triage_path, out_path)

    assert result["candidate"] is None
    assert result["known_candidate"] == ""
