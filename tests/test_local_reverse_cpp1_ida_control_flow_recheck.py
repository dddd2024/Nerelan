"""Tests for local_reverse_cpp1_ida_control_flow_recheck precision rules."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from reverse_agent.local_reverse_cpp1_ida_control_flow_recheck import (
    _analyze_control_flow,
    _control_flow_assessment,
    _find_binary_path,
    run_cpp1_ida_control_flow_recheck,
)


def _make_artifact_index() -> dict:
    return {
        "schema_version": 1,
        "latest_artifacts": {},
        "latest_artifacts_v2": {
            "local_reverse_cpp1_2f6fcb63_static_triage": {
                "path": "project_state/local_reverse_cpp1_2f6fcb63_static_triage.json",
                "freshness": "current",
            }
        },
    }


def _make_target_bytes() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
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
                        "if ( v4 != 18 ) printf(\"Sorry,you are wrong!\\n\");\n"
                        "strncpy(Destination, Str, 0x10u);\n"
                        "v6 = v9 / v8;\n"
                        "for ( i = 0; i < v4; ++i )\n"
                        "  Destination[i] = Destination[i] & 3 | "
                        "(16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2);\n"
                        "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i ) ;\n"
                        "if ( i == 16 ) printf(\"Congratulations! You are right!\\n\");\n"
                    )
                }
            ]
        },
    }


def _insn(address: str, mnemonic: str, operands: list[str], basic_block: int = 0) -> dict:
    return {
        "address": address,
        "mnemonic": mnemonic,
        "operands": operands,
        "disasm": f"{mnemonic} {', '.join(operands)}",
        "basic_block": basic_block,
    }


def _make_precise_ida_output() -> dict:
    transform_window = [
        _insn("0x00401230", "and", ["eax", "3"]),
        _insn("0x00401234", "and", ["ecx", "0Ch"]),
        _insn("0x00401238", "shl", ["ecx", "4"]),
        _insn("0x0040123C", "and", ["edx", "0F0h"]),
        _insn("0x00401240", "shr", ["edx", "2"]),
        _insn("0x00401244", "or", ["eax", "ecx"]),
    ]
    compare_window = [
        _insn("0x004012B8", "mov", ["al", "[Destination+ecx]"]),
        _insn("0x004012BE", "cmp", ["al", "byte_429A30[ecx]"]),
        _insn("0x004012C4", "jnz", ["0x004012EF"]),
    ]
    return {
        "main_function": "_main_0",
        "main_function_address": "0x00401190",
        "basic_blocks": [
            {
                "id": 0,
                "start": "0x00401190",
                "end": "0x00401337",
                "size": 423,
                "successors": ["0x004012EF"],
            }
        ],
        "division_instructions_in_main": [
            _insn("0x00401239", "idiv", ["[ebp+var_8]"]),
        ],
        "transform_candidate_windows_in_main": [
            {"anchor": transform_window[0], "window": transform_window},
        ],
        "compare_candidate_windows_in_main": [
            {"anchor": compare_window[1], "window": compare_window, "target_xref_related": True},
        ],
        "target_xref_context": {
            "target_name": "byte_429A30",
            "target_address": "0x00429A30",
            "xrefs": [
                {
                    "from": "0x004012BE",
                    "type": "data",
                    "in_main": True,
                    "basic_block": 0,
                    "window": compare_window,
                }
            ],
        },
        "seh_static_scan": {
            "handler_symbols": [],
            "segments_scanned": [".text", ".rdata"],
            "assessment": "SEH_NOT_CONFIRMED_BY_STATIC_SCAN",
        },
        "success_failure_branch_evidence": [
            {
                "role": "success",
                "string": "Congratulations! You are right!",
                "string_address": "0x00427040",
                "xref_from": "0x004012D3",
                "xref_in_main": True,
                "basic_block": 0,
                "related_branch_instruction": _insn("0x004012C4", "jnz", ["0x004012EF"]),
                "association": "ASSOCIATED_WITH_LOCAL_JCC",
                "window": compare_window,
            }
        ],
        "decompiler_snippets": [
            {
                "function": "_main_0",
                "address": "0x00401190",
                "text": (
                    "strlen(Str); strncpy(Destination, Str, 0x10u); "
                    "v6 = v9 / v8; for ( i = 0; i < v4; ++i ) "
                    "Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | "
                    "((Destination[i] & 0xF0) >> 2); "
                    "Destination[i] == byte_429A30[i]; if ( i == 16 )"
                ),
            }
        ],
    }


def test_analyze_control_flow_requires_bounded_main_evidence() -> None:
    analysis = _analyze_control_flow(_make_precise_ida_output(), _make_triage())

    assert analysis["main_function_found"] is True
    assert analysis["main_function"] == "_main_0"
    assert analysis["basic_block_source"] == "ida_gdl.FlowChart"
    assert analysis["basic_block_count"] == 1
    assert analysis["division_instruction_count"] == 1
    assert analysis["transform_candidate_window_count"] == 1
    assert analysis["compare_candidate_window_count"] == 1
    assert analysis["target_xref_in_main_count"] == 1

    consistency = analysis["decompiler_vs_instruction_consistency"]
    assert consistency["division_is_bounded_to_main"] is True
    assert consistency["transform_evidence_is_bounded_to_main"] is True
    assert consistency["transform_sequence_complete"] is True
    assert consistency["compare_evidence_is_bounded_to_main"] is True
    assert consistency["target_xref_in_main"] is True
    assert consistency["seh_assessment"] == "SEH_NOT_CONFIRMED_BY_STATIC_SCAN"


def test_assessment_is_conservative_without_local_compare_branch_association() -> None:
    raw = _make_precise_ida_output()
    raw["success_failure_branch_evidence"] = [
        {
            "role": "success",
            "association": "INSUFFICIENT",
            "xref_in_main": True,
            "window": [],
        }
    ]
    analysis = _analyze_control_flow(raw, _make_triage())
    assessment = _control_flow_assessment(analysis)

    assert assessment["transform_formula_verdict"] == "SUPPORTED"
    assert assessment["division_verdict"] == "BOUNDED_MAIN_INSTRUCTION_FOUND"
    assert assessment["seh_verdict"] == "SEH_NOT_CONFIRMED_BY_STATIC_SCAN"
    assert assessment["length_compare_semantics_verdict"] == "PARTIALLY_SUPPORTED"


def test_global_style_counts_do_not_earn_supported_verdict() -> None:
    raw = _make_precise_ida_output()
    raw["division_instructions_in_main"] = []
    raw["transform_candidate_windows_in_main"] = []
    raw["compare_candidate_windows_in_main"] = []
    raw["target_xref_context"]["xrefs"] = [{"from": "0x00405743", "in_main": False}]
    analysis = _analyze_control_flow(raw, _make_triage())
    assessment = _control_flow_assessment(analysis)

    assert assessment["transform_formula_verdict"] == "PARTIALLY_SUPPORTED"
    assert assessment["division_verdict"] == "INSUFFICIENT"
    assert assessment["length_compare_semantics_verdict"] == "PARTIALLY_SUPPORTED"


def test_run_ida_recheck_binary_not_found_writes_safe_blocked_artifact() -> None:
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

        import reverse_agent.local_reverse_cpp1_ida_control_flow_recheck as recheck_module

        original_find = _find_binary_path
        try:
            recheck_module._find_binary_path = lambda *args, **kwargs: None
            result = run_cpp1_ida_control_flow_recheck(
                idx_path, target_path, recheck_path, triage_path, out_path
            )
        finally:
            recheck_module._find_binary_path = original_find

        written = json.loads(out_path.read_text(encoding="utf-8"))
        updated_index = json.loads(idx_path.read_text(encoding="utf-8"))

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "BINARY_NOT_FOUND"
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["runtime_validated"] is False
    assert result["executed_sample"] is False
    assert written["control_flow_assessment"]["seh_verdict"] == "SEH_NOT_CONFIRMED_BY_STATIC_SCAN"
    assert (
        updated_index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck"][
            "source_run"
        ]
        == "round_20260605_cpp1_ida_control_flow_recheck_precision_fix_v1"
    )


def test_output_invariants_with_ida_unavailable() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_binary = Path(tmpdir) / "cpp1_2f6fcb63.exe"
        fake_binary.write_bytes(b"MZ" + b"\x00" * 100)

        idx = _make_artifact_index()
        idx["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_static_triage"]["path"] = str(fake_binary)
        idx_path = Path(tmpdir) / "artifact_index.json"
        target_path = Path(tmpdir) / "target_bytes.json"
        recheck_path = Path(tmpdir) / "transform_recheck.json"
        triage_path = Path(tmpdir) / "triage.json"
        out_path = Path(tmpdir) / "ida_recheck.json"
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        target_path.write_text(json.dumps(_make_target_bytes()), encoding="utf-8")
        recheck_path.write_text(json.dumps(_make_transform_recheck()), encoding="utf-8")
        triage_path.write_text(json.dumps(_make_triage()), encoding="utf-8")

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
    assert result["runtime_validated"] is False
    assert result["executed_sample"] is False
