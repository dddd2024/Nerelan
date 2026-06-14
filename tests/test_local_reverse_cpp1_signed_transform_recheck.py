"""Tests for cpp1 signed-instruction transform semantics recheck."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from reverse_agent.local_reverse_cpp1_signed_transform_recheck import (
    STATIC_INVERSE_SOURCE_RUN,
    build_static_inverse_handoff_from_revalidation,
    build_signed_transform_report,
    byte_preimages_for_target,
    compare_models_all_256,
    printable_preimages_for_target,
    run_static_inverse_handoff_from_revalidation,
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


def _current_revalidation(target_bytes: list[int] | None = None) -> dict:
    target = target_bytes or _target_bytes()["target_bytes"]
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": "逆向课程2023春01/CPP1.exe",
        "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
        "analysis_mode": "target_bytes_current_revalidation",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "revalidation_status": "PASSED",
        "candidate": None,
        "known_candidate": "",
        "target_symbol": "byte_429A30",
        "target_address": "0x00429A30",
        "target_length": len(target),
        "target_bytes_hex": bytes(target).hex(),
        "target_bytes": target,
    }


def _artifact_index_for_revalidation(revalidation_path: Path) -> dict:
    return {
        "schema_version": 1,
        "latest_artifacts": {},
        "artifact_refs": {},
        "latest_artifacts_v2": {
            "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation": {
                "kind": "target_bytes_current_revalidation",
                "path": str(revalidation_path).replace("\\", "/"),
                "freshness": "current",
                "source_run": "round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1",
                "sample_id": "cpp1_2f6fcb63",
            }
        },
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


def test_full_byte_preimages_real_target_are_recorded() -> None:
    result = byte_preimages_for_target(_target_bytes()["target_bytes"])
    assert result["target_length"] == 16
    assert result["all_target_bytes_have_preimage"] is True
    assert result["all_target_bytes_have_unique_preimage"] is True
    assert result["per_byte"][0]["unique_preimage"] == 0x5D
    assert result["per_byte"][2]["unique_preimage"] == 0x1C


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


def test_static_inverse_handoff_from_current_revalidation_blocks_without_printable_preimage(tmp_path: Path) -> None:
    revalidation_path = tmp_path / "project_state" / "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json"
    artifact_index_path = tmp_path / "project_state" / "artifact_index.json"
    revalidation = _current_revalidation()
    artifact_index = _artifact_index_for_revalidation(revalidation_path)

    report = build_static_inverse_handoff_from_revalidation(
        revalidation=revalidation,
        artifact_index=artifact_index,
        revalidation_path=revalidation_path,
        artifact_index_path=artifact_index_path,
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["analysis_mode"] == "static_inverse_transform_handoff"
    assert report["mainline"] == "reverse_solving"
    assert report["executed_sample"] is False
    assert report["runtime_validated"] is False
    assert report["authoritative"] is False
    assert report["candidate"] is None
    assert report["known_candidate"] == ""
    assert report["status"] == "BLOCKED"
    assert report["blocked_reason"] == "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES"
    assert report["model_equivalence"]["difference_count"] == 0
    assert report["per_byte_preimages"]["all_byte_domain"]["signed_instruction"]["per_byte"][2]["unique_preimage"] == 0x1C
    assert report["per_byte_preimages"]["printable_ascii_domain"]["signed_instruction"]["per_byte"][2]["has_printable_preimage"] is False
    assert report["printable_preimage_status"]["missing_printable_indices"] == [2, 3, 4, 5, 7, 8, 9, 10, 12, 13]


def test_static_inverse_handoff_preview_is_non_authoritative_for_unique_printable_preimage(tmp_path: Path) -> None:
    preview = "AbC123XYZxyz09!?"
    target = [signed_instruction_transform(ord(ch)) for ch in preview]
    revalidation_path = tmp_path / "project_state" / "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json"
    artifact_index_path = tmp_path / "project_state" / "artifact_index.json"
    revalidation = _current_revalidation(target)
    artifact_index = _artifact_index_for_revalidation(revalidation_path)

    report = build_static_inverse_handoff_from_revalidation(
        revalidation=revalidation,
        artifact_index=artifact_index,
        revalidation_path=revalidation_path,
        artifact_index_path=artifact_index_path,
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["status"] == "STATIC_CANDIDATE_PREVIEW_NEEDS_RUNTIME_VALIDATION"
    assert report["candidate"] == preview
    assert report["known_candidate"] == ""
    assert report["static_candidate_preview"] == preview
    assert report["runtime_validated"] is False
    assert report["authoritative"] is False
    assert report["requires_runtime_validation"] is True
    assert report["printable_preimage_status"]["complete_printable_preimage"] is True
    assert report["printable_preimage_status"]["unique_printable_preimage"] is True


def test_static_inverse_cli_writes_artifact_and_updates_current_index(tmp_path: Path) -> None:
    root = tmp_path / "project_state"
    revalidation_path = root / "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json"
    artifact_index_path = root / "artifact_index.json"
    out_path = root / "local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json"
    root.mkdir()
    revalidation_path.write_text(json.dumps(_current_revalidation()), encoding="utf-8")
    artifact_index_path.write_text(
        json.dumps(_artifact_index_for_revalidation(revalidation_path)),
        encoding="utf-8",
    )

    result = run_static_inverse_handoff_from_revalidation(
        revalidation_path=revalidation_path,
        artifact_index_path=artifact_index_path,
        out_path=out_path,
    )
    written = json.loads(out_path.read_text(encoding="utf-8"))
    index = json.loads(artifact_index_path.read_text(encoding="utf-8"))

    assert result["candidate"] is None
    assert written["blocked_reason"] == "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES"
    entry = index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_static_inverse_handoff"]
    assert entry["freshness"] == "current"
    assert entry["source_run"] == STATIC_INVERSE_SOURCE_RUN
    assert entry["sample_id"] == "cpp1_2f6fcb63"
