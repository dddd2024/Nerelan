"""Tests for local_reverse_cpp1_ida_control_flow_recheck.

Coverage:
1. _analyze_control_flow with synthetic IDA output.
2. run_cpp1_ida_control_flow_recheck with synthetic artifacts (IDA unavailable).
3. Output invariants: candidate=null, known_candidate="", status=BLOCKED.
4. CLI generates JSON artifact.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.local_reverse_cpp1_ida_control_flow_recheck import (
    _analyze_control_flow,
    _find_binary_path,
    _resolve_ida_executable,
    run_cpp1_ida_control_flow_recheck,
)


def _make_artifact_index() -> dict:
    return {
        "schema_version": 1,
        "latest_artifacts_v2": {
            "local_reverse_cpp1_2f6fcb63_static_triage": {
                "path": "project_state/local_reverse_cpp1_2f6fcb63_static_triage.json",
                "freshness": "current",
            }
        }
    }


def _make_target_bytes() -> dict:
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


def _make_transform_recheck() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "candidate": None,
        "known_candidate": "",
        "status": "BLOCKED",
        "blocked_reason": "NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM",
    }


def _make_triage() -> dict:
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


def _make_ida_output() -> dict:
    """Synthetic IDA output with division instruction and transform evidence."""
    return {
        "main_function": "_main_0",
        "main_function_address": "0x00401190",
        "basic_blocks": [
            {"start": "0x00401190", "end": "0x00401200", "size": 112},
            {"start": "0x00401200", "end": "0x00401280", "size": 128},
        ],
        "division_instructions": [
            {"address": "0x00401210", "mnemonic": "idiv", "operand": "eax", "disasm": "idiv eax"},
        ],
        "transform_loop_evidence": [
            {"address": "0x00401230", "disasm": "and ebx, 3"},
            {"address": "0x00401234", "disasm": "and ecx, 0Ch"},
            {"address": "0x00401238", "disasm": "shl ecx, 4"},
            {"address": "0x0040123C", "disasm": "and edx, 0F0h"},
            {"address": "0x00401240", "disasm": "shr edx, 2"},
        ],
        "compare_loop_evidence": [
            {"address": "0x00401260", "disasm": "cmp al, [esi]"},
        ],
        "target_xref_evidence": {
            "target_name": "byte_429A30",
            "target_address": "0x00429A30",
            "xrefs": [
                {"from": "0x00401260", "type": "code"},
            ],
        },
        "seh_evidence": [],
        "success_branch_evidence": [
            {"string": "Congratulations! You are right!", "string_address": "0x00429000", "xref_from": "0x00401290"},
        ],
        "failure_branch_evidence": [
            {"string": "Sorry,you are wrong!", "string_address": "0x00429020", "xref_from": "0x004011A0"},
        ],
        "decompiler_snippets": [
            {
                "function": "_main_0",
                "address": "0x00401190",
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
                ),
            }
        ],
    }


# ---------------------------------------------------------------------------
# _analyze_control_flow tests
# ---------------------------------------------------------------------------

def test_analyze_control_flow_with_division() -> None:
    """Control flow analysis should detect division instruction."""
    ida_output = _make_ida_output()
    triage = _make_triage()
    analysis = _analyze_control_flow(ida_output, triage)

    assert analysis["main_function_found"] is True
    assert analysis["main_function"] == "_main_0"
    assert analysis["division_instruction_count"] == 1
    assert analysis["transform_loop_evidence_count"] == 5
    assert analysis["compare_loop_evidence_count"] == 1
    assert analysis["target_xref_count"] == 1
    assert analysis["seh_segment_found"] is False
    assert analysis["success_branch_found"] is True
    assert analysis["failure_branch_found"] is True
    assert analysis["decompiler_available"] is True

    consistency = analysis["decompiler_vs_instruction_consistency"]
    assert consistency["triage_has_strlen_check"] is True
    assert consistency["triage_has_strncpy"] is True
    assert consistency["triage_has_transform_loop"] is True
    assert consistency["triage_has_compare_loop"] is True
    assert consistency["triage_has_success_condition"] is True
    assert consistency["triage_has_division"] is True
    assert consistency["ida_has_strlen_check"] is True
    assert consistency["ida_has_strncpy"] is True
    assert consistency["ida_has_transform_loop"] is True
    assert consistency["ida_has_compare_loop"] is True
    assert consistency["ida_has_success_condition"] is True
    assert consistency["ida_has_division"] is True
    assert consistency["division_is_real_instruction"] is True
    assert consistency["division_near_main"] is True
    assert consistency["transform_instructions_found"] is True
    assert consistency["transform_formula_supported"] is True
    assert consistency["seh_present"] is False


def test_analyze_control_flow_no_division() -> None:
    """If no division instruction found, assessment should reflect that."""
    ida_output = _make_ida_output()
    ida_output["division_instructions"] = []
    triage = _make_triage()
    analysis = _analyze_control_flow(ida_output, triage)

    consistency = analysis["decompiler_vs_instruction_consistency"]
    assert consistency["division_is_real_instruction"] is False
    assert "dead code" in consistency.get("division_assessment", "")


def test_analyze_control_flow_no_transform() -> None:
    """If no transform instructions found, formula should be unsupported."""
    ida_output = _make_ida_output()
    ida_output["transform_loop_evidence"] = []
    triage = _make_triage()
    analysis = _analyze_control_flow(ida_output, triage)

    consistency = analysis["decompiler_vs_instruction_consistency"]
    assert consistency["transform_instructions_found"] is False
    assert consistency["transform_formula_supported"] is False


def test_analyze_control_flow_with_seh() -> None:
    """If SEH segments found, assessment should reflect that."""
    ida_output = _make_ida_output()
    ida_output["seh_evidence"] = [
        {"segment": ".except", "start": "0x0042A000", "end": "0x0042B000"},
    ]
    triage = _make_triage()
    analysis = _analyze_control_flow(ida_output, triage)

    consistency = analysis["decompiler_vs_instruction_consistency"]
    assert consistency["seh_present"] is True
    assert "caught by exception handler" in consistency.get("seh_assessment", "")


# ---------------------------------------------------------------------------
# Integration: run_cpp1_ida_control_flow_recheck
# ---------------------------------------------------------------------------

def test_run_ida_recheck_binary_not_found() -> None:
    """When binary not found, should produce BLOCKED with BINARY_NOT_FOUND."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx_path = Path(tmpdir) / "artifact_index.json"
        target_path = Path(tmpdir) / "target_bytes.json"
        recheck_path = Path(tmpdir) / "transform_recheck.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "ida_recheck.json"

        idx_path.write_text(json.dumps(_make_artifact_index()), encoding="utf-8")
        target_path.write_text(json.dumps(_make_target_bytes()), encoding="utf-8")
        recheck_path.write_text(json.dumps(_make_transform_recheck()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage()), encoding="utf-8")

        # Monkeypatch _find_binary_path to return None
        original_find = _find_binary_path
        try:
            import reverse_agent.local_reverse_cpp1_ida_control_flow_recheck as recheck_module
            recheck_module._find_binary_path = lambda *args, **kwargs: None
            result = run_cpp1_ida_control_flow_recheck(
                idx_path, target_path, recheck_path, triage_path, out_path
            )
        finally:
            recheck_module._find_binary_path = original_find

        # Verify artifact was written inside temp dir context
        assert out_path.exists()
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert written["sample_id"] == "cpp1_2f6fcb63"

    assert result["sample_id"] == "cpp1_2f6fcb63"
    assert result["analysis_mode"] == "ida_instruction_control_flow_recheck"
    assert result["mainline"] == "tool_integration"
    assert result["executed_sample"] is False
    assert result["static_only"] is True
    assert result["runtime_validated"] is False
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "BINARY_NOT_FOUND"
    assert result["ida_status"]["attempted"] is False
    assert result["ida_status"]["available"] is False
    assert result["ida_status"]["success"] is False


def test_run_ida_recheck_ida_unavailable() -> None:
    """When IDA not available, should produce BLOCKED with IDA_UNAVAILABLE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake binary file
        fake_binary = Path(tmpdir) / "cpp1_2f6fcb63.exe"
        fake_binary.write_bytes(b"MZ" + b"\x00" * 100)

        idx_path = Path(tmpdir) / "artifact_index.json"
        target_path = Path(tmpdir) / "target_bytes.json"
        recheck_path = Path(tmpdir) / "transform_recheck.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "ida_recheck.json"

        # Artifact index pointing to the fake binary
        idx = _make_artifact_index()
        idx["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_static_triage"]["path"] = str(fake_binary)
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        target_path.write_text(json.dumps(_make_target_bytes()), encoding="utf-8")
        recheck_path.write_text(json.dumps(_make_transform_recheck()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage()), encoding="utf-8")

        # Monkeypatch _resolve_ida_executable to return None (IDA unavailable)
        import reverse_agent.local_reverse_cpp1_ida_control_flow_recheck as recheck_module
        original_resolve = recheck_module._resolve_ida_executable
        try:
            recheck_module._resolve_ida_executable = lambda *args, **kwargs: None
            result = run_cpp1_ida_control_flow_recheck(
                idx_path, target_path, recheck_path, triage_path, out_path
            )
        finally:
            recheck_module._resolve_ida_executable = original_resolve

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "IDA_UNAVAILABLE"
    assert result["candidate"] is None
    assert result["known_candidate"] == ""


# ---------------------------------------------------------------------------
# Output invariants
# ---------------------------------------------------------------------------

def test_output_always_null_candidate_empty_known() -> None:
    """Output must have candidate=null and known_candidate=''."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx_path = Path(tmpdir) / "artifact_index.json"
        target_path = Path(tmpdir) / "target_bytes.json"
        recheck_path = Path(tmpdir) / "transform_recheck.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "ida_recheck.json"

        idx_path.write_text(json.dumps(_make_artifact_index()), encoding="utf-8")
        target_path.write_text(json.dumps(_make_target_bytes()), encoding="utf-8")
        recheck_path.write_text(json.dumps(_make_transform_recheck()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage()), encoding="utf-8")

        result = run_cpp1_ida_control_flow_recheck(
            idx_path, target_path, recheck_path, triage_path, out_path
        )

    assert result["candidate"] is None
    assert result["known_candidate"] == ""
