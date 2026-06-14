"""Static signed-instruction transform recheck for cpp1_2f6fcb63.

This module models the current _main_0 IDA evidence without rerunning IDA and
without executing the sample. It keeps any static preimage non-authoritative.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_signed_transform_recheck"
ARTIFACT_KIND = "local_reverse_cpp1_signed_transform_recheck"
SOURCE_RUN = "round_20260605_cpp1_signed_transform_semantics_recheck_v1"
STATIC_INVERSE_ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_static_inverse_handoff"
STATIC_INVERSE_ARTIFACT_KIND = "static_inverse_transform_handoff"
STATIC_INVERSE_SOURCE_RUN = "round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1"


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
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


def _update_artifact_index(
    artifact_index_path: Path,
    out_path: Path,
    sample_id: str,
    generated_at: str,
    *,
    artifact_key: str = ARTIFACT_KEY,
    artifact_kind: str = ARTIFACT_KIND,
    source_run: str = SOURCE_RUN,
) -> None:
    if not artifact_index_path.exists():
        return
    artifact_index = _load_json(artifact_index_path)
    normalized_path = str(out_path).replace("/", "\\")
    artifact_index.setdefault("latest_artifacts", {})[artifact_key] = normalized_path
    artifact_index.setdefault("artifact_refs", {})[artifact_key] = normalized_path
    artifact_index.setdefault("latest_artifacts_v2", {})[artifact_key] = {
        "kind": artifact_kind,
        "path": normalized_path,
        "freshness": "current",
        "source_run": source_run,
        "sha256": _sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "modified_at": generated_at,
        "sample_id": sample_id,
    }
    artifact_index["generated_at"] = generated_at
    _save_json(artifact_index_path, artifact_index)


def u8(x: int) -> int:
    return x & 0xFF


def s8(x: int) -> int:
    value = u8(x)
    return value - 0x100 if value & 0x80 else value


def _s32(x: int) -> int:
    value = x & 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def sar32(x: int, n: int) -> int:
    return _s32(x) >> n


def unsigned_formula_transform(x: int) -> int:
    b = u8(x)
    return u8((b & 0x03) | ((b & 0x0C) << 4) | ((b & 0xF0) >> 2))


def signed_instruction_transform(x: int) -> int:
    """Model movsx/and/sar/shl/or/mov al from the current IDA evidence."""
    first = sar32(s8(x) & 0xF0, 2)
    second = (s8(x) & 0x0C) << 4
    third = s8(x) & 0x03
    return u8(first | second | third)


def _logical_shr32(x: int, n: int) -> int:
    return (x & 0xFFFFFFFF) >> n


def compare_models_all_256() -> dict[str, Any]:
    rows = []
    differences = []
    for x in range(256):
        unsigned_out = unsigned_formula_transform(x)
        signed_out = signed_instruction_transform(x)
        row = {
            "input": x,
            "input_hex": f"{x:02x}",
            "input_s8": s8(x),
            "unsigned_formula_output": unsigned_out,
            "unsigned_formula_output_hex": f"{unsigned_out:02x}",
            "signed_instruction_output": signed_out,
            "signed_instruction_output_hex": f"{signed_out:02x}",
            "same": unsigned_out == signed_out,
        }
        rows.append(row)
        if not row["same"]:
            differences.append(row)
    return {
        "input_count": 256,
        "difference_count": len(differences),
        "models_equivalent_after_u8_truncation": len(differences) == 0,
        "rows": rows,
        "differences": differences,
    }


def printable_preimages_for_target(
    target_bytes: list[int],
    model: str = "signed_instruction",
) -> dict[str, Any]:
    transform = signed_instruction_transform if model == "signed_instruction" else unsigned_formula_transform
    per_byte = []
    preview: list[int] = []
    all_have_printable = True
    all_unique = True
    for index, target in enumerate(target_bytes):
        preimages = [x for x in range(0x20, 0x7F) if transform(x) == u8(target)]
        if not preimages:
            all_have_printable = False
        if len(preimages) != 1:
            all_unique = False
        if len(preimages) == 1:
            preview.append(preimages[0])
        per_byte.append(
            {
                "index": index,
                "target_byte": u8(target),
                "target_byte_hex": f"{u8(target):02x}",
                "preimage_count": len(preimages),
                "has_printable_preimage": bool(preimages),
                "unique_printable_preimage": preimages[0] if len(preimages) == 1 else None,
                "printable_preimages": preimages,
                "printable_preimages_hex": [f"{item:02x}" for item in preimages],
                "printable_preimages_text": "".join(chr(item) for item in preimages) if preimages else None,
            }
        )
    return {
        "model": model,
        "printable_domain": "0x20..0x7e",
        "target_length": len(target_bytes),
        "all_target_bytes_have_printable_preimage": all_have_printable,
        "all_target_bytes_have_unique_printable_preimage": all_have_printable and all_unique,
        "per_byte": per_byte,
        "static_preimage_preview_hex": "".join(f"{b:02x}" for b in preview)
        if len(preview) == len(target_bytes)
        else "",
        "static_preimage_preview_ascii_if_printable": "".join(chr(b) for b in preview)
        if len(preview) == len(target_bytes)
        else "",
    }


def byte_preimages_for_target(
    target_bytes: list[int],
    model: str = "signed_instruction",
    domain: range = range(256),
) -> dict[str, Any]:
    transform = signed_instruction_transform if model == "signed_instruction" else unsigned_formula_transform
    per_byte = []
    all_have = True
    all_unique = True
    for index, target in enumerate(target_bytes):
        preimages = [x for x in domain if transform(x) == u8(target)]
        if not preimages:
            all_have = False
        if len(preimages) != 1:
            all_unique = False
        per_byte.append(
            {
                "index": index,
                "target_byte": u8(target),
                "target_byte_hex": f"{u8(target):02x}",
                "preimage_count": len(preimages),
                "has_preimage": bool(preimages),
                "unique_preimage": preimages[0] if len(preimages) == 1 else None,
                "preimages": preimages,
                "preimages_hex": [f"{item:02x}" for item in preimages],
                "preimages_text": "".join(chr(item) if 0x20 <= item <= 0x7E else "." for item in preimages)
                if preimages
                else None,
            }
        )
    return {
        "model": model,
        "domain": "0x00..0xff",
        "target_length": len(target_bytes),
        "all_target_bytes_have_preimage": all_have,
        "all_target_bytes_have_unique_preimage": all_have and all_unique,
        "per_byte": per_byte,
    }


def _artifact_index_entry(artifact_index: dict[str, Any], key: str) -> dict[str, Any]:
    entry = artifact_index.get("latest_artifacts_v2", {}).get(key)
    if isinstance(entry, dict):
        return entry
    return {}


def _normalized_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _validate_current_revalidation(
    revalidation: dict[str, Any],
    artifact_index: dict[str, Any],
    revalidation_path: Path,
) -> dict[str, Any]:
    sample_id = str(revalidation.get("sample_id", ""))
    if sample_id != "cpp1_2f6fcb63":
        raise ValueError(f"current revalidation sample_id mismatch: {sample_id!r}")
    if revalidation.get("analysis_mode") != "target_bytes_current_revalidation":
        raise ValueError("source artifact is not target_bytes_current_revalidation")
    if revalidation.get("revalidation_status") != "PASSED":
        raise ValueError("current revalidation artifact did not pass")
    if revalidation.get("runtime_validated") is not False:
        raise ValueError("current revalidation runtime_validated must be false")
    if revalidation.get("executed_sample") is not False:
        raise ValueError("current revalidation executed_sample must be false")
    if revalidation.get("candidate") is not None:
        raise ValueError("current revalidation candidate must be null")
    if revalidation.get("known_candidate") != "":
        raise ValueError("current revalidation known_candidate must be empty")
    target = revalidation.get("target_bytes", [])
    if len(target) != 16:
        raise ValueError(f"target_bytes length must be 16, got {len(target)}")

    entry = _artifact_index_entry(artifact_index, "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation")
    if entry.get("freshness") != "current":
        raise ValueError("target bytes revalidation artifact is not current in artifact_index")
    if entry.get("sample_id") != "cpp1_2f6fcb63":
        raise ValueError("target bytes revalidation artifact_index sample_id mismatch")
    indexed_path = str(entry.get("path", "")).replace("\\", "/")
    expected_suffix = _normalized_path(revalidation_path)
    if indexed_path and indexed_path != expected_suffix:
        raise ValueError(f"artifact_index path mismatch: {indexed_path!r} != {expected_suffix!r}")
    return entry


def build_static_inverse_handoff_from_revalidation(
    revalidation: dict[str, Any],
    artifact_index: dict[str, Any],
    *,
    revalidation_path: Path,
    artifact_index_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or _now_iso()
    revalidation_entry = _validate_current_revalidation(
        revalidation,
        artifact_index,
        revalidation_path,
    )
    target = [u8(x) for x in revalidation["target_bytes"]]
    model_comparison = compare_models_all_256()
    signed_all_byte = byte_preimages_for_target(target, model="signed_instruction")
    unsigned_all_byte = byte_preimages_for_target(target, model="unsigned_formula")
    signed_printable = printable_preimages_for_target(target, model="signed_instruction")
    unsigned_printable = printable_preimages_for_target(target, model="unsigned_formula")
    missing_printable_indices = [
        row["index"]
        for row in signed_printable["per_byte"]
        if not row["has_printable_preimage"]
    ]
    complete_unique_printable = signed_printable["all_target_bytes_have_unique_printable_preimage"]
    static_candidate_preview = (
        signed_printable["static_preimage_preview_ascii_if_printable"]
        if complete_unique_printable
        else ""
    )
    status = "STATIC_CANDIDATE_PREVIEW_NEEDS_RUNTIME_VALIDATION" if complete_unique_printable else "BLOCKED"
    blocked_reason = "" if complete_unique_printable else "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES"

    return {
        "schema_version": 1,
        "sample_id": "cpp1_2f6fcb63",
        "relative_path": revalidation.get("relative_path", ""),
        "sha256": revalidation.get("sha256", ""),
        "analysis_mode": "static_inverse_transform_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "authoritative": False,
        "requires_runtime_validation": True,
        "generated_at": generated,
        "status": status,
        "blocked_reason": blocked_reason,
        "source_artifacts": {
            "current_revalidation": _normalized_path(revalidation_path),
            "artifact_index": _normalized_path(artifact_index_path),
        },
        "source_artifact_freshness": {
            "current_revalidation": {
                "artifact_key": "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
                "path": revalidation_entry.get("path", ""),
                "freshness": revalidation_entry.get("freshness", ""),
                "source_run": revalidation_entry.get("source_run", ""),
                "sample_id": revalidation_entry.get("sample_id", ""),
            }
        },
        "target_symbol": revalidation.get("target_symbol", "byte_429A30"),
        "target_address": revalidation.get("target_address", "0x00429A30"),
        "target_length": len(target),
        "target_bytes_hex": "".join(f"{item:02x}" for item in target),
        "target_bytes": target,
        "transform_models": {
            "unsigned_formula": {
                "formula": "u8((x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2))",
                "domain": "0x00..0xff",
            },
            "signed_instruction": {
                "formula": "u8((sar32((s8(x) & 0xF0), 2)) | ((s8(x) & 0x0C) << 4) | (s8(x) & 0x03))",
                "domain": "0x00..0xff",
            },
        },
        "model_equivalence": {
            "input_count": model_comparison["input_count"],
            "difference_count": model_comparison["difference_count"],
            "models_equivalent_after_u8_truncation": model_comparison[
                "models_equivalent_after_u8_truncation"
            ],
        },
        "per_byte_preimages": {
            "all_byte_domain": {
                "signed_instruction": signed_all_byte,
                "unsigned_formula": unsigned_all_byte,
            },
            "printable_ascii_domain": {
                "signed_instruction": signed_printable,
                "unsigned_formula": unsigned_printable,
            },
        },
        "printable_preimage_status": {
            "domain": "0x20..0x7e",
            "complete_printable_preimage": signed_printable[
                "all_target_bytes_have_printable_preimage"
            ],
            "unique_printable_preimage": complete_unique_printable,
            "missing_printable_indices": missing_printable_indices,
            "printable_available_count": len(target) - len(missing_printable_indices),
            "target_length": len(target),
            "static_candidate_preview": static_candidate_preview,
            "authoritative": False,
            "runtime_validated": False,
            "requires_runtime_validation": True,
        },
        "candidate": static_candidate_preview if complete_unique_printable else None,
        "known_candidate": "",
        "static_candidate_preview": static_candidate_preview if complete_unique_printable else "",
        "evidence_notes": [
            "computed from current target-bytes revalidation artifact",
            "old inverse handoff and signed transform artifacts are stale context only",
            "no sample execution, debugger, emulator, harness, brute force, or runtime validation was used",
        ],
        "recommended_next_action": (
            "Request a bounded runtime validation decision before accepting this static candidate preview."
            if complete_unique_printable
            else "Perform alternative static review of transform/target semantics; do not repeat printable inverse under current target bytes without new evidence."
        ),
    }


def run_static_inverse_handoff_from_revalidation(
    revalidation_path: Path,
    artifact_index_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    generated_at = _now_iso()
    artifact_index = _load_json(artifact_index_path)
    result = build_static_inverse_handoff_from_revalidation(
        revalidation=_load_json(revalidation_path),
        artifact_index=artifact_index,
        revalidation_path=revalidation_path,
        artifact_index_path=artifact_index_path,
        generated_at=generated_at,
    )
    _save_json(out_path, result)
    _update_artifact_index(
        artifact_index_path,
        out_path,
        result["sample_id"],
        generated_at,
        artifact_key=STATIC_INVERSE_ARTIFACT_KEY,
        artifact_kind=STATIC_INVERSE_ARTIFACT_KIND,
        source_run=STATIC_INVERSE_SOURCE_RUN,
    )
    print(f"cpp1 static inverse handoff: status={result['status']} sample_id={result['sample_id']}")
    print(f"  model_difference_count={result['model_equivalence']['difference_count']}")
    print(
        "  complete_printable_preimage="
        f"{result['printable_preimage_status']['complete_printable_preimage']}"
    )
    print(
        "  missing_printable_indices="
        f"{result['printable_preimage_status']['missing_printable_indices']}"
    )
    print(f"  candidate={result['candidate']}")
    print(f"  known_candidate={result['known_candidate']!r}")
    print(f"  runtime_validated={result['runtime_validated']}")
    return result


def _all_instructions(ida_control_flow: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = ida_control_flow.get("bounded_instruction_evidence", {})
    instructions: list[dict[str, Any]] = []
    for item in evidence.get("transform_candidate_windows_in_main", []):
        if isinstance(item.get("anchor"), dict):
            instructions.append(item["anchor"])
        for insn in item.get("window", []):
            if isinstance(insn, dict):
                instructions.append(insn)
    for item in evidence.get("compare_candidate_windows_in_main", []):
        if isinstance(item.get("anchor"), dict):
            instructions.append(item["anchor"])
        for insn in item.get("window", []):
            if isinstance(insn, dict):
                instructions.append(insn)
    xref_context = evidence.get("target_xref_context", {})
    for xref in xref_context.get("xrefs", []):
        for insn in xref.get("window", []):
            if isinstance(insn, dict):
                instructions.append(insn)
    return instructions


def _operand_text(insn: dict[str, Any]) -> str:
    return " ".join(str(item) for item in insn.get("operands", []))


def summarize_ida_instruction_evidence(ida_control_flow: dict[str, Any]) -> dict[str, Any]:
    instructions = _all_instructions(ida_control_flow)
    unique_by_address = {str(insn.get("address")): insn for insn in instructions if insn.get("address")}
    unique = list(unique_by_address.values())

    def has(mnemonic: str, operand_needles: tuple[str, ...] = ()) -> bool:
        for insn in unique:
            if str(insn.get("mnemonic", "")).lower() != mnemonic:
                continue
            text = _operand_text(insn).lower()
            if all(needle.lower() in text for needle in operand_needles):
                return True
        return False

    required = {
        "movsx_destination": has("movsx", ("destination",)),
        "and_0f0": has("and", ("0f0",)),
        "sar_2": has("sar", ("2",)),
        "and_0c": has("and", ("0c",)),
        "shl_4": has("shl", ("4",)),
        "or": has("or"),
        "and_3": has("and", ("3",)),
        "mov_destination_al": has("mov", ("destination", "al")),
        "movsx_target_byte": has("movsx", ("byte_429a30",)),
        "cmp": has("cmp"),
    }
    missing = [key for key, present in required.items() if not present]
    key_sequence = [
        {
            "address": insn.get("address", ""),
            "mnemonic": insn.get("mnemonic", ""),
            "operands": insn.get("operands", []),
            "disasm": insn.get("disasm", ""),
            "basic_block": insn.get("basic_block"),
        }
        for insn in unique
        if str(insn.get("address", "")).lower()
        in {
            "0x0040125c",
            "0x00401263",
            "0x00401268",
            "0x0040126e",
            "0x00401275",
            "0x00401278",
            "0x0040127b",
            "0x00401280",
            "0x00401287",
            "0x0040128a",
            "0x0040128f",
            "0x004012be",
            "0x004012c5",
            "0x004012c7",
        }
    ]
    return {
        "main_function": ida_control_flow.get("main_function", ""),
        "main_function_address": ida_control_flow.get("main_function_address", ""),
        "ida_status": ida_control_flow.get("ida_status", {}),
        "control_flow_assessment": ida_control_flow.get("control_flow_assessment", {}),
        "required_instruction_presence": required,
        "missing_required_instructions": missing,
        "sufficient_for_signed_model": not missing,
        "key_instruction_sequence": key_sequence,
        "compare_xref_related": any(
            item.get("in_main")
            for item in ida_control_flow.get("bounded_instruction_evidence", {})
            .get("target_xref_context", {})
            .get("xrefs", [])
        ),
        "success_failure_branch_verdict": ida_control_flow.get("success_failure_branch_assessment", {}).get(
            "verdict", ""
        ),
    }


def _sar_vs_shr_difference_summary() -> dict[str, Any]:
    after_mask_differences = []
    raw_movsx_differences = []
    for x in range(256):
        masked = s8(x) & 0xF0
        sar_masked = u8(sar32(masked, 2))
        shr_masked = u8(_logical_shr32(masked, 2))
        if sar_masked != shr_masked:
            after_mask_differences.append(
                {"input": x, "sar_masked": sar_masked, "shr_masked": shr_masked}
            )
        raw_signed = sar32(s8(x), 2)
        raw_logical = _logical_shr32(s8(x), 2)
        if raw_signed != raw_logical:
            raw_movsx_differences.append(
                {
                    "input": x,
                    "input_hex": f"{x:02x}",
                    "input_s8": s8(x),
                    "sar_raw_32": raw_signed,
                    "shr_raw_32": raw_logical,
                    "sar_raw_low8": u8(raw_signed),
                    "shr_raw_low8": u8(raw_logical),
                    "low8_same": u8(raw_signed) == u8(raw_logical),
                }
            )
    return {
        "after_and_0f0_difference_count": len(after_mask_differences),
        "after_and_0f0_difference_inputs": after_mask_differences,
        "raw_movsx_before_mask_difference_count": len(raw_movsx_differences),
        "raw_movsx_before_mask_difference_input_range": "0x80..0xff",
        "raw_movsx_before_mask_sample": raw_movsx_differences[:8],
        "conclusion": (
            "sar and shr differ for negative movsx values before masking, but the observed "
            "instruction masks with 0xF0 before sar; after that mask, final low-byte output "
            "matches the unsigned high-level model for all 0..255 inputs."
        ),
    }


def _movsx_effect_summary(model_comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "destination_movsx_before_masks": True,
        "target_movsx_before_compare": True,
        "final_store": "mov Destination[ecx], al",
        "output_byte_difference_count": model_comparison["difference_count"],
        "compare_semantics": (
            "movsx is applied to both transformed Destination[i] and byte_429A30[i]; "
            "signed 32-bit equality is equivalent to byte equality for equal low bytes."
        ),
        "conclusion": (
            "movsx affects intermediate 32-bit signs, but the observed masks and final AL "
            "truncation mean it does not change the final transform byte versus the old "
            "unsigned formula."
        ),
    }


def _first_16_compare_boundary(ida_control_flow: dict[str, Any], transform_recheck: dict[str, Any]) -> dict[str, Any]:
    length_semantics = transform_recheck.get("length_compare_semantics", {})
    return {
        "static_boundary": "first 16 transformed bytes",
        "success_condition_evidence": "cmp [ebp+var_C], 10h / jnz loc_4012EF",
        "compare_xref_related": ida_control_flow.get("bounded_instruction_evidence", {})
        .get("target_xref_context", {})
        .get("target_name", "")
        == "byte_429A30",
        "prior_length_observations": length_semantics.get("observations", []),
        "runtime_validation": False,
        "conclusion": "The first-16-byte compare is a static analysis boundary only, not runtime proof.",
    }


def _validate_source_artifact(name: str, artifact: dict[str, Any]) -> None:
    if artifact.get("runtime_validated") is not False:
        raise ValueError(f"{name} artifact runtime_validated must be false")
    if artifact.get("executed_sample") is not False:
        raise ValueError(f"{name} artifact executed_sample must be false")


def build_signed_transform_report(
    target_bytes: dict[str, Any],
    ida_control_flow: dict[str, Any],
    transform_recheck: dict[str, Any],
    source_artifacts: dict[str, str],
    generated_at: str | None = None,
) -> dict[str, Any]:
    _validate_source_artifact("target_bytes", target_bytes)
    _validate_source_artifact("ida_control_flow", ida_control_flow)
    _validate_source_artifact("transform_recheck", transform_recheck)
    sample_id = str(target_bytes.get("sample_id", ""))
    if not sample_id:
        raise ValueError("target_bytes artifact missing sample_id")
    target = target_bytes.get("target_bytes", [])
    if len(target) != 16:
        raise ValueError(f"target_bytes length must be 16, got {len(target)}")

    ida_summary = summarize_ida_instruction_evidence(ida_control_flow)
    if not ida_summary["sufficient_for_signed_model"]:
        raise ValueError(
            "IDA evidence missing required signed transform instructions: "
            + ", ".join(ida_summary["missing_required_instructions"])
        )

    model_comparison = compare_models_all_256()
    preimages = printable_preimages_for_target([u8(x) for x in target], model="signed_instruction")
    all_unique = preimages["all_target_bytes_have_unique_printable_preimage"]
    status = "STATIC_PREIMAGE_RECHECKED_NEEDS_VALIDATION" if all_unique else "BLOCKED"
    blocked_reason = (
        "STATIC_PREIMAGE_UNVALIDATED"
        if all_unique
        else "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_SIGNED_MODEL"
    )

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "signed_instruction_transform_recheck",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": generated_at or _now_iso(),
        "source_artifacts": source_artifacts,
        "source_artifact_freshness": {
            "expected": "current",
            "verified_before_execution": True,
        },
        "ida_instruction_evidence_summary": ida_summary,
        "unsigned_formula_model": {
            "formula": "u8((x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2))",
            "domain": "0..255",
        },
        "signed_instruction_model": {
            "formula": "u8((sar32((s8(x) & 0xF0), 2)) | ((s8(x) & 0x0C) << 4) | (s8(x) & 0x03))",
            "instruction_sequence": [
                "movsx eax, Destination[edx]",
                "and eax, 0F0h",
                "sar eax, 2",
                "movsx edx, Destination[ecx]",
                "and edx, 0Ch",
                "shl edx, 4",
                "or eax, edx",
                "movsx edx, Destination[ecx]",
                "and edx, 3",
                "or eax, edx",
                "mov Destination[ecx], al",
            ],
            "domain": "0..255",
        },
        "model_comparison_all_256": model_comparison,
        "sar_vs_shr_difference_summary": _sar_vs_shr_difference_summary(),
        "movsx_effect_summary": _movsx_effect_summary(model_comparison),
        "first_16_compare_boundary": _first_16_compare_boundary(ida_control_flow, transform_recheck),
        "per_byte_printable_preimage_signed_model": preimages,
        "static_preimage_status": {
            "complete_printable_preimage": preimages["all_target_bytes_have_printable_preimage"],
            "unique_printable_preimage": all_unique,
            "authoritative": False,
            "requires_runtime_validation": True,
        },
        "candidate": None,
        "known_candidate": "",
        "status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": (
            "Request a separate bounded runtime validation decision before accepting any static preimage."
            if all_unique
            else "Continue static refinement of the transform/target evidence; do not brute force or expand budget."
        ),
    }
    if all_unique:
        result["static_preimage_preview_hex"] = preimages["static_preimage_preview_hex"]
        result["static_preimage_preview_ascii_if_printable"] = preimages[
            "static_preimage_preview_ascii_if_printable"
        ]
    return result


def run_signed_transform_recheck(
    target_bytes_path: Path,
    ida_control_flow_path: Path,
    transform_recheck_path: Path,
    out_path: Path,
    artifact_index_path: Path = Path("project_state/artifact_index.json"),
) -> dict[str, Any]:
    generated_at = _now_iso()
    result = build_signed_transform_report(
        target_bytes=_load_json(target_bytes_path),
        ida_control_flow=_load_json(ida_control_flow_path),
        transform_recheck=_load_json(transform_recheck_path),
        source_artifacts={
            "target_bytes": str(target_bytes_path).replace("\\", "/"),
            "ida_control_flow": str(ida_control_flow_path).replace("\\", "/"),
            "transform_recheck": str(transform_recheck_path).replace("\\", "/"),
        },
        generated_at=generated_at,
    )
    _save_json(out_path, result)
    _update_artifact_index(artifact_index_path, out_path, result["sample_id"], generated_at)
    print(f"cpp1 signed transform recheck: status={result['status']} sample_id={result['sample_id']}")
    print(
        "  model_difference_count="
        f"{result['model_comparison_all_256']['difference_count']}"
    )
    print(
        "  after_mask_sar_shr_difference_count="
        f"{result['sar_vs_shr_difference_summary']['after_and_0f0_difference_count']}"
    )
    print(
        "  printable_preimage_complete="
        f"{result['static_preimage_status']['complete_printable_preimage']}"
    )
    print(f"  candidate={result['candidate']}")
    print(f"  known_candidate={result['known_candidate']!r}")
    print(f"  runtime_validated={result['runtime_validated']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Static signed-instruction transform recheck for cpp1_2f6fcb63.",
    )
    parser.add_argument("--target-bytes", type=Path)
    parser.add_argument("--ida-control-flow", type=Path)
    parser.add_argument("--transform-recheck", type=Path)
    parser.add_argument("--from-revalidation", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
    )
    args = parser.parse_args()
    try:
        if args.from_revalidation:
            run_static_inverse_handoff_from_revalidation(
                revalidation_path=args.from_revalidation,
                artifact_index_path=args.artifact_index,
                out_path=args.out,
            )
        else:
            missing = [
                name
                for name, value in (
                    ("--target-bytes", args.target_bytes),
                    ("--ida-control-flow", args.ida_control_flow),
                    ("--transform-recheck", args.transform_recheck),
                )
                if value is None
            ]
            if missing:
                raise ValueError("missing required arguments for signed recheck: " + ", ".join(missing))
            run_signed_transform_recheck(
                target_bytes_path=args.target_bytes,
                ida_control_flow_path=args.ida_control_flow,
                transform_recheck_path=args.transform_recheck,
                out_path=args.out,
                artifact_index_path=args.artifact_index,
            )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
