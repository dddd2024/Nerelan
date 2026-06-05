"""Tests for cpp1 signed-instruction transform semantics recheck."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from reverse_agent.local_reverse_cpp1_signed_transform_recheck import (
    build_signed_transform_report,
    compare_models_all_256,
    printable_preimages_for_target,
    run_signed_transform_recheck,
    s8,
    sar32,
    signed_instruction_transform,
    u8,
    unsigned_formula_transform,
)


def _insn(address: str, mnemonic: str, operands: list[str]) -> dict:
    return {
        "address": address,
        "mnemonic": mnemonic,
        "operands": operands,
        "disasm": f"{mnemonic} {', '.join(operands)}",
        "basic_block": 5,
    }


def _target_bytes() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "target_bytes": [213, 150, 196, 246, 7, 69, 87, 119, 118, 229, 246, 72, 71, 247, 72, 23],
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "candidate": None,
        "known_candidate": "",
    }


def _transform_recheck() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "length_compare_semantics": {
            "observations": [
                "input length check: strlen(Str) must equal 18",
                "success condition: i == 16, meaning first 16 bytes must match",
            ]
        },
        "candidate": None,
        "known_candidate": "",
    }


def _ida_control_flow() -> dict:
    transform_window = [
        _insn("0x0040125C", "movsx", ["eax", "Destination[edx]"]),
        _insn("0x00401263", "and", ["eax", "0F0h"]),
        _insn("0x00401268", "sar", ["eax", "2"]),
        _insn("0x0040126E", "movsx", ["edx", "Destination[ecx]"]),
        _insn("0x00401275", "and", ["edx", "0Ch"]),
        _insn("0x00401278", "shl", ["edx", "4"]),
        _insn("0x0040127B", "or", ["eax", "edx"]),
        _insn("0x00401280", "movsx", ["edx", "Destination[ecx]"]),
        _insn("0x00401287", "and", ["edx", "3"]),
        _insn("0x0040128A", "or", ["eax", "edx"]),
        _insn("0x0040128F", "mov", ["Destination[ecx]", "al"]),
    ]
    compare_window = [
        _insn("0x004012B4", "movsx", ["edx", "Destination[ecx]"]),
        _insn("0x004012BE", "movsx", ["ecx", "byte_429A30[eax]"]),
        _insn("0x004012C5", "cmp", ["edx", "ecx"]),
        _insn("0x004012C7", "jz", ["loc_4012CB"]),
    ]
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "main_function": "_main_0",
        "main_function_address": "0x00401190",
        "ida_status": {"success": True},
        "control_flow_assessment": {
            "transform_formula_verdict": "PARTIALLY_SUPPORTED",
            "length_compare_semantics_verdict": "PARTIALLY_SUPPORTED",
        },
        "bounded_instruction_evidence": {
            "transform_candidate_windows_in_main": [
                {"anchor": transform_window[0], "window": transform_window}
            ],
            "compare_candidate_windows_in_main": [
                {"anchor": compare_window[2], "window": compare_window, "target_xref_related": True}
            ],
            "target_xref_context": {
                "target_name": "byte_429A30",
                "target_address": "0x00429A30",
                "xrefs": [
                    {
                        "from": "0x004012BE",
                        "in_main": True,
                        "basic_block": 9,
                        "window": compare_window,
                    }
                ],
            },
        },
        "success_failure_branch_assessment": {"verdict": "INSUFFICIENT"},
        "candidate": None,
        "known_candidate": "",
    }


def test_signed_helpers_and_model_equivalence() -> None:
    assert u8(-1) == 255
    assert s8(0x7F) == 127
    assert s8(0x80) == -128
    assert sar32(-128, 2) == -32

    comparison = compare_models_all_256()
    assert comparison["input_count"] == 256
    assert comparison["difference_count"] == 0
    assert comparison["models_equivalent_after_u8_truncation"] is True
    for x in range(256):
        assert signed_instruction_transform(x) == unsigned_formula_transform(x)


def test_printable_preimages_real_target_remain_incomplete() -> None:
    result = printable_preimages_for_target(_target_bytes()["target_bytes"])
    assert result["target_length"] == 16
    assert result["all_target_bytes_have_printable_preimage"] is False
    assert result["per_byte"][0]["printable_preimages_text"] == "]"
    assert result["per_byte"][2]["has_printable_preimage"] is False
    assert result["static_preimage_preview_hex"] == ""


def test_build_report_uses_ida_signed_instruction_evidence() -> None:
    report = build_signed_transform_report(
        target_bytes=_target_bytes(),
        ida_control_flow=_ida_control_flow(),
        transform_recheck=_transform_recheck(),
        source_artifacts={
            "target_bytes": "target.json",
            "ida_control_flow": "ida.json",
            "transform_recheck": "transform.json",
        },
        generated_at="2026-06-05T00:00:00Z",
    )

    assert report["analysis_mode"] == "signed_instruction_transform_recheck"
    assert report["mainline"] == "reverse_solving"
    assert report["ida_instruction_evidence_summary"]["sufficient_for_signed_model"] is True
    assert report["model_comparison_all_256"]["difference_count"] == 0
    assert report["sar_vs_shr_difference_summary"]["after_and_0f0_difference_count"] == 0
    assert report["sar_vs_shr_difference_summary"]["raw_movsx_before_mask_difference_count"] == 128
    assert report["movsx_effect_summary"]["output_byte_difference_count"] == 0
    assert report["first_16_compare_boundary"]["runtime_validation"] is False
    assert report["candidate"] is None
    assert report["known_candidate"] == ""
    assert report["runtime_validated"] is False
    assert report["executed_sample"] is False
    assert report["status"] == "BLOCKED"
    assert report["status"] != "SOLVED"


def test_missing_ida_instruction_blocks_report() -> None:
    ida = _ida_control_flow()
    ida["bounded_instruction_evidence"]["transform_candidate_windows_in_main"][0]["window"] = [
        item
        for item in ida["bounded_instruction_evidence"]["transform_candidate_windows_in_main"][0]["window"]
        if item["mnemonic"] != "sar"
    ]
    try:
        build_signed_transform_report(
            target_bytes=_target_bytes(),
            ida_control_flow=ida,
            transform_recheck=_transform_recheck(),
            source_artifacts={},
        )
    except ValueError as exc:
        assert "sar_2" in str(exc)
    else:
        raise AssertionError("missing sar instruction should block report generation")


def test_cli_writes_artifact_and_updates_index() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        target_path = root / "target.json"
        ida_path = root / "ida.json"
        transform_path = root / "transform.json"
        out_path = root / "signed.json"
        index_path = root / "artifact_index.json"
        target_path.write_text(json.dumps(_target_bytes()), encoding="utf-8")
        ida_path.write_text(json.dumps(_ida_control_flow()), encoding="utf-8")
        transform_path.write_text(json.dumps(_transform_recheck()), encoding="utf-8")
        index_path.write_text(
            json.dumps({"schema_version": 1, "latest_artifacts": {}, "latest_artifacts_v2": {}}),
            encoding="utf-8",
        )

        result = run_signed_transform_recheck(
            target_bytes_path=target_path,
            ida_control_flow_path=ida_path,
            transform_recheck_path=transform_path,
            out_path=out_path,
            artifact_index_path=index_path,
        )
        written = json.loads(out_path.read_text(encoding="utf-8"))
        index = json.loads(index_path.read_text(encoding="utf-8"))

    assert result["candidate"] is None
    assert written["known_candidate"] == ""
    entry = index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_signed_transform_recheck"]
    assert entry["freshness"] == "current"
    assert entry["source_run"] == "round_20260605_cpp1_signed_transform_semantics_recheck_v1"
