"""Tests for cpp1 input delivery review."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.local_reverse_cpp1_input_delivery_review import (
    ARTIFACT_KEY,
    SOURCE_RUN,
    build_input_delivery_review,
    run_input_delivery_review,
)
from reverse_agent.local_reverse_cpp1_signed_transform_recheck import signed_instruction_transform


TARGET_BYTES = [0xD5, 0x96, 0xC4, 0xF6, 0x07, 0x45, 0x57, 0x77, 0x76, 0xE5, 0xF6, 0x48, 0x47, 0xF7, 0x48, 0x17]
REAL_PREIMAGE = [0x5D, 0x5A, 0x1C, 0xDE, 0x13, 0x15, 0x57, 0xD7, 0xD6, 0x9D, 0xDE, 0x24, 0x17, 0xDF, 0x24, 0x53]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _target_revalidation(target_bytes: list[int] | None = None) -> dict:
    target = target_bytes or TARGET_BYTES
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
        "target_length": 16,
        "target_bytes_hex": bytes(target).hex(),
        "target_bytes": target,
        "forward_transform": {
            "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
        },
    }


def _inverse_handoff(preimage: list[int] | None = None) -> dict:
    preview = preimage or REAL_PREIMAGE
    target = [signed_instruction_transform(value) for value in preview]
    missing_printable = [index for index, value in enumerate(preview) if not 0x20 <= value <= 0x7E]
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": "逆向课程2023春01/CPP1.exe",
        "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
        "analysis_mode": "static_inverse_transform_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "authoritative": False,
        "status": "BLOCKED",
        "blocked_reason": "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES",
        "candidate": None,
        "known_candidate": "",
        "target_bytes": target,
        "target_bytes_hex": bytes(target).hex(),
        "model_equivalence": {
            "models_equivalent_after_u8_truncation": True,
        },
        "per_byte_preimages": {
            "all_byte_domain": {
                "signed_instruction": {
                    "per_byte": [
                        {
                            "index": index,
                            "unique_preimage": value,
                            "preimage_count": 1,
                        }
                        for index, value in enumerate(preview)
                    ],
                },
            },
        },
        "printable_preimage_status": {
            "complete_printable_preimage": False,
            "missing_printable_indices": missing_printable,
        },
    }


def _triage() -> dict:
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": "逆向课程2023春01/CPP1.exe",
        "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
        "analysis_mode": "single_sample_static_triage",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "tool_status": "success",
        "candidate": None,
        "known_candidate": "",
    }


def _alternative_review(preimage: list[int] | None = None) -> dict:
    preview = preimage or REAL_PREIMAGE
    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": "逆向课程2023春01/CPP1.exe",
        "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
        "analysis_mode": "alternative_static_semantics_review",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "authoritative": False,
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": "NEEDS_INPUT_DELIVERY_REVIEW",
        "nonprintable_static_preimage_preview_hex": bytes(preview).hex(),
        "all_byte_preimage_review": {
            "nonprintable_static_preimage_preview_hex": bytes(preview).hex(),
            "byte_classes": {},
        },
        "nonprintable_input_delivery_risk": {
            "scanf_hard_blockers": {"indices": []},
        },
    }


def _negative_results() -> list[dict]:
    return [
        {
            "direction": "cpp1_2f6fcb63 current target bytes printable inverse path",
            "do_not_repeat": True,
            "override_allowed": True,
            "override_reason_required": True,
            "reason": "no complete printable ASCII preimage under current target bytes",
            "severity": "soft_block",
        }
    ]


def _artifact_index(root: Path) -> dict:
    return {
        "schema_version": 1,
        "latest_artifacts": {},
        "artifact_refs": {},
        "latest_artifacts_v2": {
            "local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review": {
                "kind": "alternative_static_semantics_review",
                "path": str(root / "alternative_review.json").replace("\\", "/"),
                "freshness": "current",
                "source_run": "round_alternative",
                "sample_id": "cpp1_2f6fcb63",
            },
            "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation": {
                "kind": "target_bytes_current_revalidation",
                "path": str(root / "target_revalidation.json").replace("\\", "/"),
                "freshness": "current",
                "source_run": "round_target",
                "sample_id": "cpp1_2f6fcb63",
            },
            "local_reverse_cpp1_2f6fcb63_static_inverse_handoff": {
                "kind": "static_inverse_transform_handoff",
                "path": str(root / "inverse_handoff.json").replace("\\", "/"),
                "freshness": "current",
                "source_run": "round_inverse",
                "sample_id": "cpp1_2f6fcb63",
            },
            "local_reverse_cpp1_2f6fcb63_static_triage": {
                "kind": "local_reverse_single_sample_static_triage",
                "path": str(root / "triage.json").replace("\\", "/"),
                "freshness": "current",
                "source_run": "round_triage",
                "sample_id": "cpp1_2f6fcb63",
            },
        },
    }


def _write_sources(tmp_path: Path, *, preimage: list[int] | None = None) -> dict[str, Path]:
    root = tmp_path / "project_state"
    paths = {
        "input_review": root / "alternative_review.json",
        "target": root / "target_revalidation.json",
        "inverse": root / "inverse_handoff.json",
        "triage": root / "triage.json",
        "index": root / "artifact_index.json",
        "negative": root / "negative_results.json",
        "out": root / "input_delivery_review.json",
    }
    target = _target_revalidation([signed_instruction_transform(value) for value in preimage] if preimage else None)
    _write_json(paths["input_review"], _alternative_review(preimage))
    _write_json(paths["target"], target)
    _write_json(paths["inverse"], _inverse_handoff(preimage))
    _write_json(paths["triage"], _triage())
    _write_json(paths["index"], _artifact_index(root))
    _write_json(paths["negative"], _negative_results())
    return paths


def test_real_preimage_classified_without_hard_blocker_but_needs_boundary_recheck(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    report = build_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["analysis_mode"] == "input_delivery_review"
    assert report["executed_sample"] is False
    assert report["runtime_validated"] is False
    assert report["authoritative"] is False
    assert report["candidate"] is None
    assert report["known_candidate"] == ""

    # Byte classification for the real preimage
    domain = report["preimage_input_domain_review"]
    assert domain["nul_indices"] == []
    assert domain["whitespace_indices"] == []
    assert domain["control_indices"] == [2, 4, 5, 12]
    assert domain["high_bit_indices"] == [3, 7, 8, 9, 10, 13]
    assert domain["printable_ascii_indices"] == [0, 1, 6, 11, 14, 15]

    # No NUL/whitespace hard blocker
    assert domain["scanf_percent_s_hard_blocker_indices"] == []
    assert domain["strlen_hard_blocker_indices"] == []

    # But boundary is unknown, so action is NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK
    assert report["recommended_next_action"] == "NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK"


def test_review_refuses_non_current_source(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)
    index = json.loads(paths["index"].read_text(encoding="utf-8"))
    index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_static_inverse_handoff"]["freshness"] = "stale"
    _write_json(paths["index"], index)

    with pytest.raises(ValueError, match="not current"):
        build_input_delivery_review(
            input_review_path=paths["input_review"],
            target_revalidation_path=paths["target"],
            inverse_handoff_path=paths["inverse"],
            triage_path=paths["triage"],
            artifact_index_path=paths["index"],
            negative_results_path=paths["negative"],
        )


def test_review_requires_printable_inverse_negative_result(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)
    _write_json(paths["negative"], [])

    with pytest.raises(ValueError, match="negative_results"):
        build_input_delivery_review(
            input_review_path=paths["input_review"],
            target_revalidation_path=paths["target"],
            inverse_handoff_path=paths["inverse"],
            triage_path=paths["triage"],
            artifact_index_path=paths["index"],
            negative_results_path=paths["negative"],
        )


def test_review_keeps_candidate_null_and_not_authoritative(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    report = build_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["candidate"] is None
    assert report["known_candidate"] == ""
    assert report["runtime_validated"] is False
    assert report["authoritative"] is False


def test_payload_length_review_distinguishes_copied_and_suffix_bytes(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    report = build_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        generated_at="2026-06-14T00:00:00Z",
    )

    plr = report["payload_length_review"]
    assert plr["first_16_bytes_copied_by_strncpy"] is True
    assert plr["strncpy_length"] == 16
    assert plr["strlen_required"] == 18
    assert plr["suffix_bytes_17_18_purpose"] == "satisfy_strlen_18_only"
    assert plr["suffix_bytes_do_not_control_destination_16"] is True
    assert plr["suffix_must_be_non_nul_non_whitespace"] is True


def test_suffix_does_not_control_destination_16(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    report = build_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["suffix_policy"]["suffix_does_not_control_destination_16"] is True
    assert report["suffix_policy"]["suffix_length"] == 2
    assert report["suffix_policy"]["suffix_must_not_contain_nul"] is True
    assert report["suffix_policy"]["suffix_must_not_contain_whitespace"] is True


def test_needs_success_boundary_recheck_when_boundary_unknown(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    report = build_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        generated_at="2026-06-14T00:00:00Z",
    )

    assert report["recommended_next_action"] == "NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK"
    assert report["success_boundary_review"]["success_boundary_status"] == "UNKNOWN_NEEDS_STATIC_OR_TOOL_RECHECK"
    assert report["success_boundary_review"]["byte_429A30_index_16_known"] is False


def test_with_printable_preimage_still_needs_boundary_recheck(tmp_path: Path) -> None:
    printable_preimage = [ord(ch) for ch in "AbC123XYZxyz09!?"]
    paths = _write_sources(tmp_path, preimage=printable_preimage)

    report = run_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        out_path=paths["out"],
    )

    # Even with a printable preimage, the success boundary is still unknown
    # because target_length=16 means byte_429A30[16] is not available.
    assert report["recommended_next_action"] == "NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK"
    assert report["preimage_input_domain_review"]["scanf_percent_s_hard_blocker_indices"] == []
    assert report["candidate"] is None
    assert report["runtime_validated"] is False


def test_cli_writes_review_and_current_artifact_index(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)

    result = run_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        out_path=paths["out"],
    )
    written = json.loads(paths["out"].read_text(encoding="utf-8"))
    index = json.loads(paths["index"].read_text(encoding="utf-8"))

    assert result["candidate"] is None
    assert written["analysis_mode"] == "input_delivery_review"
    assert written["recommended_next_action"] == "NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK"
    entry = index["latest_artifacts_v2"][ARTIFACT_KEY]
    assert entry["kind"] == "input_delivery_review"
    assert entry["freshness"] == "current"
    assert entry["source_run"] == SOURCE_RUN
    assert entry["sample_id"] == "cpp1_2f6fcb63"


def test_blocked_when_preimage_has_whitespace(tmp_path: Path) -> None:
    preimage_with_space = [ord(ch) for ch in "AbC123XYZxyz09!?"]
    preimage_with_space[3] = 0x20  # space byte
    paths = _write_sources(tmp_path, preimage=preimage_with_space)

    report = run_input_delivery_review(
        input_review_path=paths["input_review"],
        target_revalidation_path=paths["target"],
        inverse_handoff_path=paths["inverse"],
        triage_path=paths["triage"],
        artifact_index_path=paths["index"],
        negative_results_path=paths["negative"],
        out_path=paths["out"],
    )

    assert report["recommended_next_action"] == "BLOCKED_INPUT_DELIVERY_HARD_BLOCKER"
    assert 3 in report["preimage_input_domain_review"]["whitespace_indices"]
    assert 3 in report["preimage_input_domain_review"]["scanf_percent_s_hard_blocker_indices"]
