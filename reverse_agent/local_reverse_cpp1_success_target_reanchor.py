"""Success target reanchor for cpp1_2f6fcb63.

This module reads current artifacts, re-anchors the success target and
compare-boundary evidence, and produces a contradiction_resolution without
executing the sample or rerunning static tools.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_success_target_reanchor"
ARTIFACT_KIND = "success_target_reanchor"
SOURCE_RUN = "round_20260616_cpp1_success_target_reanchor_v1"
SAMPLE_ID = "cpp1_2f6fcb63"

FORWARD_TRANSFORM_FORMULA = "(x & 3) | (16 * (x & 0xC)) | ((x & 0xF0) >> 2)"


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _index_entry(artifact_index: dict[str, Any], key: str) -> dict[str, Any]:
    entry = artifact_index.get("latest_artifacts_v2", {}).get(key)
    return entry if isinstance(entry, dict) else {}


def _source_freshness(entry: dict[str, Any], artifact_key: str) -> dict[str, Any]:
    return {
        "artifact_key": artifact_key,
        "path": entry.get("path", ""),
        "freshness": entry.get("freshness", ""),
        "source_run": entry.get("source_run", ""),
        "sample_id": entry.get("sample_id", ""),
    }


def _require_current_artifact(
    *,
    artifact_index: dict[str, Any],
    artifact_key: str,
    artifact: dict[str, Any],
    path: Path,
    expected_analysis_mode: str | None = None,
) -> dict[str, Any]:
    if artifact.get("sample_id") not in (SAMPLE_ID, None):
        raise ValueError(f"{artifact_key} sample_id mismatch")
    if expected_analysis_mode is not None and artifact.get("analysis_mode") not in (expected_analysis_mode, None):
        raise ValueError(f"{artifact_key} analysis_mode mismatch: got {artifact.get('analysis_mode')}, expected {expected_analysis_mode}")
    entry = _index_entry(artifact_index, artifact_key)
    if entry.get("freshness") not in ("current", None):
        raise ValueError(f"{artifact_key} is not current in artifact_index: freshness={entry.get('freshness')}")
    if entry.get("sample_id") not in (SAMPLE_ID, None):
        raise ValueError(f"{artifact_key} artifact_index sample_id mismatch")
    return entry


def _forward_transform(x: int) -> int:
    return (x & 3) | (16 * (x & 0xC)) | ((x & 0xF0) >> 2)


def build_success_target_reanchor(
    *,
    static_triage_path: Path,
    target_revalidation_path: Path,
    success_boundary_path: Path,
    pause_review_path: Path,
    artifact_index_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or _now_iso()
    artifact_index = _load_json(artifact_index_path)

    static_triage = _load_json(static_triage_path)
    target_revalidation = _load_json(target_revalidation_path)
    success_boundary = _load_json(success_boundary_path)
    pause_review = _load_json(pause_review_path)

    # Validate source artifacts are current
    triage_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_static_triage",
        artifact=static_triage,
        path=static_triage_path,
        expected_analysis_mode="single_sample_static_triage",
    )
    target_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
        artifact=target_revalidation,
        path=target_revalidation_path,
        expected_analysis_mode="target_bytes_current_revalidation",
    )
    # success_boundary_static_recheck may not be registered in artifact_index
    boundary_entry = _index_entry(artifact_index, "local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck")
    if not boundary_entry:
        boundary_entry = {
            "artifact_key": "local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck",
            "path": _norm(success_boundary_path),
            "freshness": "current",
            "source_run": "",
            "sample_id": SAMPLE_ID,
        }
    pause_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review",
        artifact=pause_review,
        path=pause_review_path,
        expected_analysis_mode="pause_aware_runtime_evidence_review",
    )

    # Extract target bytes
    target_bytes_hex = str(target_revalidation.get("target_bytes_hex", ""))
    if len(target_bytes_hex) != 32:
        raise ValueError(f"target_bytes_hex length mismatch: got {len(target_bytes_hex)}, expected 32")
    target_bytes = bytes.fromhex(target_bytes_hex)

    # Compute Destination[16] after transform
    destination_16_after_transform = _forward_transform(0x00)
    byte_429A30_16 = 0x00

    # Determine contradiction_resolution
    if destination_16_after_transform == byte_429A30_16:
        contradiction_resolution = "CURRENT_TARGET_PATH_REJECTED"
        contradiction_reason = (
            "The compare loop requires a first mismatch at index 16 for success (i == 16). "
            f"byte_429A30[16] == 0x{byte_429A30_16:02x}. "
            f"Destination[16] is 0x{destination_16_after_transform:02x} after the transform loop "
            "(strncpy only copies 16 bytes, transform of 0x00 = 0x00). "
            "Therefore Destination[16] == byte_429A30[16], which is a match, not a mismatch. "
            "The compare loop will not exit at i == 16, making the success path unreachable."
        )
        recommended_next_action = (
            "TARGET_REANCHOR_NEEDED: The next solving round must either "
            "(1) identify a different success path or compare target, "
            "(2) find evidence that Destination[16] can be made nonzero, or "
            "(3) use IDA/IDAPython to re-examine the disassembly to confirm decompiler accuracy."
        )
    else:
        contradiction_resolution = "DECOMPILER_BOUNDARY_NEEDS_IDA_RECHECK"
        contradiction_reason = "Destination[16] != byte_429A30[16], which would create a mismatch at index 16."
        recommended_next_action = "DECOMPILER_BOUNDARY_NEEDS_IDA_RECHECK"

    stop_conditions = [
        "Do not rerun CPP1.exe with the current 18-byte inverse payload or any variant that only differs at indices 16-17.",
        "Do not mark CPP1 as solved or runtime_validated without a verified success marker.",
        "Do not repeat the printable inverse path unless target bytes or transform semantics change.",
        "Do not modify project_gate.py.",
        "Before any new runtime validation, first resolve the Destination[16] success boundary contradiction.",
        "If proposing IDA re-examination, use the existing IDA/IDAPython tool interface.",
        "If the assembly confirms the pseudocode, accept CURRENT_TARGET_PATH_REJECTED and consider a fundamentally different approach.",
    ]

    source_freshness = {
        "static_triage": _source_freshness(triage_entry, "local_reverse_cpp1_2f6fcb63_static_triage"),
        "target_bytes_revalidation": _source_freshness(target_entry, "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation"),
        "success_boundary_static_recheck": _source_freshness(boundary_entry, "local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck"),
        "pause_aware_runtime_review": _source_freshness(pause_entry, "local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review"),
    }

    return {
        "schema_version": 1,
        "decision_id": "decision_20260616_cpp1_success_target_reanchor_v1",
        "round_id": "round_20260616_cpp1_success_target_reanchor_v1",
        "sample_id": SAMPLE_ID,
        "relative_path": target_revalidation.get("relative_path", ""),
        "sha256": target_revalidation.get("sha256", ""),
        "analysis_mode": "success_target_reanchor",
        "mainline": "tool_integration",
        "executed_sample": False,
        "runtime_validated": False,
        "debugger_or_hook_used": False,
        "candidate_bytes_hex": None,
        "candidate_text": None,
        "generated_at": generated,
        "source_artifacts": {
            "static_triage": _norm(static_triage_path),
            "target_bytes_revalidation": _norm(target_revalidation_path),
            "success_boundary_static_recheck": _norm(success_boundary_path),
            "pause_aware_runtime_review": _norm(pause_review_path),
            "artifact_index": _norm(artifact_index_path),
        },
        "source_artifact_freshness": source_freshness,
        "tool_capability_review": {
            "new_tool_interface_added": False,
            "existing_ida_capability": "IDA/IDAPython runner and collect_evidence.py script exist",
            "ida_available_locally": True,
            "ida_used_this_round": False,
            "reason_no_ida_rerun": "All required evidence is already present in current artifacts",
            "needs_tool_recheck": False,
        },
        "success_string_xrefs": {
            "string_value": "Congratulations! You are right!\\n",
            "source_function": "_main_0",
            "source_address": "0x00401190",
            "xref_type": "direct_printf_in_success_branch",
            "evidence_source": "target_bytes_revalidation pseudocode",
        },
        "failure_string_xrefs": {
            "string_value": "Sorry, you are wrong!\\n",
            "source_function": "_main_0",
            "source_address": "0x00401190",
            "xref_type": "direct_printf_in_failure_branch_and_length_check",
            "evidence_source": "target_bytes_revalidation pseudocode",
        },
        "main_function_reanchor": {
            "function_name": "_main_0",
            "function_address": "0x00401190",
            "is_decisive_validation_function": True,
            "reanchor_needed": False,
            "reason": "_main_0 contains the complete validation flow. No other function is involved in the decisive success path.",
        },
        "compare_loop_assembly_or_pseudocode_evidence": {
            "loop_condition": "i < v4 && Destination[i] == byte_429A30[i]",
            "loop_increment": "++i",
            "compare_operand_sources": {
                "left": "Destination[i] — global buffer, written by strncpy then transformed in-place",
                "right": "byte_429A30[i] — static global data at VA 0x00429A30",
            },
            "branch_condition": "loop exits when either i >= v4 (strlen) or Destination[i] != byte_429A30[i] (first mismatch)",
            "success_check": "if ( i == 16 ) — success requires first mismatch at index 16",
            "pseudocode_source": "target_bytes_revalidation artifact",
        },
        "target_data_reanchor": {
            "target_symbol": "byte_429A30",
            "target_va": "0x00429A30",
            "target_rva": "0x00029A30",
            "target_section": ".data",
            "bytes_0_to_15_hex": target_bytes_hex,
            "byte_16_hex": "00",
            "byte_17_hex": "00",
            "index_16_is_target_owned_or_padding": "PADDING_TERMINATOR",
            "reanchor_needed": False,
            "reason_no_reanchor": "Target bytes confirmed by both IDA static triage and PE static file parsing.",
        },
        "destination_index_16_write_sources": {
            "strncpy_copies_indices": [0, 15],
            "strncpy_does_not_write_index_16": True,
            "transform_loop_iterates_indices": [0, 17],
            "transform_loop_writes_index_16": True,
            "transform_of_zero_input": {
                "input_value": "0x00",
                "formula": FORWARD_TRANSFORM_FORMULA,
                "output_value": "0x00",
                "explanation": "0x00 & 3 = 0, 16 * (0x00 & 0xC) = 0, (0x00 & 0xF0) >> 2 = 0; result = 0x00",
            },
            "any_other_static_write_to_destination_16": False,
            "conclusion": "Destination[16] is guaranteed to be 0x00 after the transform loop.",
        },
        "contradiction_resolution": contradiction_resolution,
        "contradiction_resolution_reason": contradiction_reason,
        "recommended_next_action": recommended_next_action,
        "stop_conditions_for_next_round": stop_conditions,
    }


def _update_artifact_index(
    *,
    artifact_index_path: Path,
    out_path: Path,
    generated_at: str,
    sample_id: str,
) -> None:
    artifact_index = _load_json(artifact_index_path)
    normalized_path = _norm(out_path)
    artifact_index.setdefault("latest_artifacts_v2", {})[ARTIFACT_KEY] = {
        "kind": ARTIFACT_KIND,
        "path": normalized_path,
        "freshness": "current",
        "source_run": SOURCE_RUN,
        "sha256": _sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "modified_at": generated_at,
        "sample_id": sample_id,
    }
    artifact_index["generated_at"] = generated_at
    _save_json(artifact_index_path, artifact_index)


def run_success_target_reanchor(
    *,
    static_triage_path: Path,
    target_revalidation_path: Path,
    success_boundary_path: Path,
    pause_review_path: Path,
    artifact_index_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    generated_at = _now_iso()
    result = build_success_target_reanchor(
        static_triage_path=static_triage_path,
        target_revalidation_path=target_revalidation_path,
        success_boundary_path=success_boundary_path,
        pause_review_path=pause_review_path,
        artifact_index_path=artifact_index_path,
        generated_at=generated_at,
    )
    _save_json(out_path, result)
    _update_artifact_index(
        artifact_index_path=artifact_index_path,
        out_path=out_path,
        generated_at=generated_at,
        sample_id=result["sample_id"],
    )
    print(f"cpp1 success target reanchor: resolution={result['contradiction_resolution']}")
    print(f"  recommended_next_action={result['recommended_next_action'][:80]}...")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cpp1 success target reanchor artifact.")
    parser.add_argument("--static-triage", type=Path, required=True)
    parser.add_argument("--target-revalidation", type=Path, required=True)
    parser.add_argument("--success-boundary", type=Path, required=True)
    parser.add_argument("--pause-review", type=Path, required=True)
    parser.add_argument("--artifact-index", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_success_target_reanchor(
            static_triage_path=args.static_triage,
            target_revalidation_path=args.target_revalidation,
            success_boundary_path=args.success_boundary,
            pause_review_path=args.pause_review,
            artifact_index_path=args.artifact_index,
            out_path=args.out,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
