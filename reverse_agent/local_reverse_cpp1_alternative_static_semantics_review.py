"""Alternative static semantics review for cpp1_2f6fcb63.

This module stays static-only: it reads current artifacts, classifies the
non-printable all-byte preimage, and records the next evidence route without
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

from reverse_agent.local_reverse_cpp1_signed_transform_recheck import byte_preimages_for_target


ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review"
ARTIFACT_KIND = "alternative_static_semantics_review"
SOURCE_RUN = "round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1"
SAMPLE_ID = "cpp1_2f6fcb63"
PRINTABLE_INVERSE_NEGATIVE_DIRECTION = "cpp1_2f6fcb63 current target bytes printable inverse path"


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


def _require_current_artifact(
    *,
    artifact_index: dict[str, Any],
    artifact_key: str,
    artifact: dict[str, Any],
    path: Path,
    expected_analysis_mode: str,
) -> dict[str, Any]:
    if artifact.get("sample_id") != SAMPLE_ID:
        raise ValueError(f"{artifact_key} sample_id mismatch")
    if artifact.get("analysis_mode") != expected_analysis_mode:
        raise ValueError(f"{artifact_key} analysis_mode mismatch")
    if artifact.get("executed_sample") is not False:
        raise ValueError(f"{artifact_key} must be static-only and must not execute the sample")
    if artifact.get("runtime_validated") is not False:
        raise ValueError(f"{artifact_key} must not be runtime validated")
    if artifact.get("candidate") is not None:
        raise ValueError(f"{artifact_key} candidate must be null")
    if artifact.get("known_candidate", "") != "":
        raise ValueError(f"{artifact_key} known_candidate must be empty")

    entry = _index_entry(artifact_index, artifact_key)
    if entry.get("freshness") != "current":
        raise ValueError(f"{artifact_key} is not current in artifact_index")
    if entry.get("sample_id") != SAMPLE_ID:
        raise ValueError(f"{artifact_key} artifact_index sample_id mismatch")
    indexed_path = str(entry.get("path", "")).replace("\\", "/")
    if indexed_path and indexed_path != _norm(path):
        raise ValueError(f"{artifact_key} artifact_index path mismatch")
    return entry


def _require_negative_result(negative_results: list[dict[str, Any]]) -> dict[str, Any]:
    for entry in negative_results:
        if entry.get("direction") == PRINTABLE_INVERSE_NEGATIVE_DIRECTION and entry.get("do_not_repeat") is True:
            return entry
    raise ValueError("negative_results is missing current printable inverse prohibition")


def _byte_class(value: int) -> str:
    if value == 0:
        return "nul"
    if value in {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20}:
        return "whitespace"
    if 0x20 <= value <= 0x7E:
        return "printable_ascii"
    if value < 0x20 or value == 0x7F:
        return "control"
    return "high_bit"


def _classify_preimage(preimage: list[int]) -> dict[str, Any]:
    per_byte = []
    buckets = {
        "nul_indices": [],
        "whitespace_indices": [],
        "control_indices": [],
        "high_bit_indices": [],
        "printable_ascii_indices": [],
    }
    for index, value in enumerate(preimage):
        cls = _byte_class(value)
        per_byte.append(
            {
                "index": index,
                "byte": value,
                "byte_hex": f"{value:02x}",
                "class": cls,
                "printable_text": chr(value) if cls == "printable_ascii" else "",
            }
        )
        if cls == "nul":
            buckets["nul_indices"].append(index)
        elif cls == "whitespace":
            buckets["whitespace_indices"].append(index)
        elif cls == "control":
            buckets["control_indices"].append(index)
        elif cls == "high_bit":
            buckets["high_bit_indices"].append(index)
        elif cls == "printable_ascii":
            buckets["printable_ascii_indices"].append(index)

    hard_blocker_indices = buckets["nul_indices"] + buckets["whitespace_indices"]
    nonprintable_indices = (
        buckets["nul_indices"]
        + buckets["whitespace_indices"]
        + buckets["control_indices"]
        + buckets["high_bit_indices"]
    )
    return {
        "preimage_hex": bytes(preimage).hex(),
        "preimage_length": len(preimage),
        "per_byte": per_byte,
        **buckets,
        "nonprintable_indices": sorted(nonprintable_indices),
        "scanf_token_hard_blocker_indices": sorted(hard_blocker_indices),
        "contains_nul": bool(buckets["nul_indices"]),
        "contains_whitespace": bool(buckets["whitespace_indices"]),
        "contains_control": bool(buckets["control_indices"]),
        "contains_high_bit": bool(buckets["high_bit_indices"]),
        "all_bytes_non_nul_non_whitespace": not hard_blocker_indices,
    }


def _extract_all_byte_preimage(inverse_handoff: dict[str, Any]) -> list[int]:
    signed = (
        inverse_handoff.get("per_byte_preimages", {})
        .get("all_byte_domain", {})
        .get("signed_instruction", {})
    )
    rows = signed.get("per_byte", [])
    if rows:
        preimage = [row.get("unique_preimage") for row in rows]
        if len(preimage) == 16 and all(isinstance(item, int) for item in preimage):
            return [int(item) & 0xFF for item in preimage]

    target = inverse_handoff.get("target_bytes", [])
    computed = byte_preimages_for_target([int(item) & 0xFF for item in target], model="signed_instruction")
    rows = computed.get("per_byte", [])
    preimage = [row.get("unique_preimage") for row in rows]
    if len(preimage) != 16 or not all(isinstance(item, int) for item in preimage):
        raise ValueError("inverse handoff does not contain a unique all-byte preimage")
    return [int(item) & 0xFF for item in preimage]


def _source_freshness(entry: dict[str, Any], artifact_key: str) -> dict[str, Any]:
    return {
        "artifact_key": artifact_key,
        "path": entry.get("path", ""),
        "freshness": entry.get("freshness", ""),
        "source_run": entry.get("source_run", ""),
        "sample_id": entry.get("sample_id", ""),
    }


def _recommended_next_action(classification: dict[str, Any]) -> str:
    if classification["contains_nul"] or classification["contains_whitespace"]:
        return "BLOCKED_NO_PRINTABLE_SOLUTION_UNDER_CURRENT_SEMANTICS"
    if classification["contains_control"] or classification["contains_high_bit"]:
        return "NEEDS_INPUT_DELIVERY_REVIEW"
    return "READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION"


def build_alternative_static_semantics_review(
    *,
    target_revalidation: dict[str, Any],
    inverse_handoff: dict[str, Any],
    triage: dict[str, Any],
    artifact_index: dict[str, Any],
    negative_results: list[dict[str, Any]],
    target_revalidation_path: Path,
    inverse_handoff_path: Path,
    triage_path: Path,
    artifact_index_path: Path,
    negative_results_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or _now_iso()
    target_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
        artifact=target_revalidation,
        path=target_revalidation_path,
        expected_analysis_mode="target_bytes_current_revalidation",
    )
    inverse_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_static_inverse_handoff",
        artifact=inverse_handoff,
        path=inverse_handoff_path,
        expected_analysis_mode="static_inverse_transform_handoff",
    )
    triage_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_static_triage",
        artifact=triage,
        path=triage_path,
        expected_analysis_mode="single_sample_static_triage",
    )
    negative_entry = _require_negative_result(negative_results)

    if target_revalidation.get("revalidation_status") != "PASSED":
        raise ValueError("target revalidation has not passed")
    if inverse_handoff.get("blocked_reason") != "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES":
        raise ValueError("inverse handoff is not the expected printable-preimage blocker")
    if inverse_handoff.get("printable_preimage_status", {}).get("complete_printable_preimage") is not False:
        raise ValueError("inverse handoff unexpectedly has a complete printable preimage")

    preimage = _extract_all_byte_preimage(inverse_handoff)
    classification = _classify_preimage(preimage)
    recommended = _recommended_next_action(classification)
    target_bytes_hex = str(target_revalidation.get("target_bytes_hex", ""))

    return {
        "schema_version": 1,
        "sample_id": SAMPLE_ID,
        "relative_path": target_revalidation.get("relative_path", ""),
        "sha256": target_revalidation.get("sha256", ""),
        "analysis_mode": "alternative_static_semantics_review",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "authoritative": False,
        "generated_at": generated,
        "source_artifacts": {
            "target_revalidation": _norm(target_revalidation_path),
            "static_inverse_handoff": _norm(inverse_handoff_path),
            "static_triage": _norm(triage_path),
            "artifact_index": _norm(artifact_index_path),
            "negative_results": _norm(negative_results_path),
        },
        "source_artifact_freshness": {
            "target_revalidation": _source_freshness(
                target_entry,
                "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
            ),
            "static_inverse_handoff": _source_freshness(
                inverse_entry,
                "local_reverse_cpp1_2f6fcb63_static_inverse_handoff",
            ),
            "static_triage": _source_freshness(triage_entry, "local_reverse_cpp1_2f6fcb63_static_triage"),
        },
        "negative_results_considered": [
            {
                "direction": negative_entry.get("direction", ""),
                "do_not_repeat": negative_entry.get("do_not_repeat"),
                "severity": negative_entry.get("severity", ""),
                "reason": negative_entry.get("reason", ""),
                "effect": "printable inverse path treated as consumed negative evidence, not rerun",
            }
        ],
        "input_domain_review": {
            "scanf_percent_s_requires_printable_ascii": False,
            "scanf_percent_s_token_constraints": [
                "NUL terminates C strings and cannot be embedded in the scanned token",
                "ASCII whitespace terminates a %s token",
                "printable ASCII is not a semantic requirement of %s or strlen",
            ],
            "strlen_required_length": 18,
            "strncpy_copied_length": 16,
            "first_16_target_constrained": True,
            "suffix_bytes_17_18_target_constrained": False,
            "suffix_bytes_17_18_review": (
                "They are not part of the 16-byte target preimage. Because the compare loop "
                "succeeds only when it stops at i == 16, suffix bytes should be chosen so "
                "the transformed byte at index 16 does not accidentally match adjacent data."
            ),
            "all_byte_preimage_has_scanf_hard_blocker": not classification[
                "all_bytes_non_nul_non_whitespace"
            ],
            "raw_stdin_or_file_redirected_delivery_possible": classification[
                "all_bytes_non_nul_non_whitespace"
            ],
            "windows_console_delivery_risk": "high",
        },
        "transform_semantics_review": {
            "current_formula": target_revalidation.get("forward_transform", {}).get("formula_c", ""),
            "is_single_byte_bit_permutation": True,
            "bit_mapping": [
                "y0=x0",
                "y1=x1",
                "y2=x4",
                "y3=x5",
                "y4=x6",
                "y5=x7",
                "y6=x2",
                "y7=x3",
            ],
            "signed_unsigned_equivalent_after_u8_truncation": inverse_handoff.get(
                "model_equivalence", {}
            ).get("models_equivalent_after_u8_truncation"),
            "forward_inverse_direction_review": (
                "The current handoff inverts the forward transform from byte_429A30 target "
                "bytes to input bytes. The unique all-byte preimage reproduces the target "
                "under the current forward formula, so the printable failure is not caused "
                "by simply using the inverse in the wrong direction."
            ),
            "extra_operation_evidence": {
                "xor_add_sub_table_lookup_or_previous_byte_dependency_seen": False,
                "basis": "current revalidation and static triage only; no new IDA/tool run in this round",
            },
            "interpretation": (
                "A unique full-byte preimage with an incomplete printable preimage is more "
                "consistent with raw-byte input semantics than with a printable password, "
                "subject to input-delivery review."
            ),
        },
        "target_symbol_review": {
            "target_symbol": target_revalidation.get("target_symbol", ""),
            "target_address": target_revalidation.get("target_address", ""),
            "target_length": target_revalidation.get("target_length"),
            "target_bytes_hex": target_bytes_hex,
            "target_length_matches_success_boundary": target_revalidation.get("target_length") == 16,
            "current_revalidation_status": target_revalidation.get("revalidation_status", ""),
            "current_revalidation_sufficient_for_this_review": True,
            "needs_target_xref_tool_recheck": False,
            "tool_recheck_not_run_this_round": True,
            "notes": [
                "Current target revalidation confirms byte_429A30, target length 16, and matching transform/compare fragments.",
                "No current-artifact conflict was found that would justify rerunning IDA in this round.",
            ],
        },
        "all_byte_preimage_review": {
            "target_bytes_hex": target_bytes_hex,
            "all_byte_unique_preimage": True,
            "nonprintable_static_preimage_preview_hex": classification["preimage_hex"],
            "printable_positions": classification["printable_ascii_indices"],
            "missing_printable_positions": inverse_handoff.get("printable_preimage_status", {}).get(
                "missing_printable_indices", []
            ),
            "byte_classes": {
                "nul_indices": classification["nul_indices"],
                "whitespace_indices": classification["whitespace_indices"],
                "control_indices": classification["control_indices"],
                "high_bit_indices": classification["high_bit_indices"],
                "printable_ascii_indices": classification["printable_ascii_indices"],
            },
            "per_byte": classification["per_byte"],
            "runtime_validated": False,
            "authoritative": False,
            "requires_input_delivery_review": True,
        },
        "nonprintable_input_delivery_risk": {
            "risk_level": "medium" if classification["all_bytes_non_nul_non_whitespace"] else "high",
            "console_unfriendly": classification["contains_control"] or classification["contains_high_bit"],
            "stdin_raw_possible": classification["all_bytes_non_nul_non_whitespace"],
            "requires_runtime_input_delivery_review": True,
            "scanf_hard_blockers": {
                "contains_nul": classification["contains_nul"],
                "contains_whitespace": classification["contains_whitespace"],
                "indices": classification["scanf_token_hard_blocker_indices"],
            },
            "recommended_delivery_hypothesis": (
                "raw stdin/file-redirection byte delivery with printable non-whitespace suffix bytes"
                if classification["all_bytes_non_nul_non_whitespace"]
                else "blocked until a different target or transform explains NUL/whitespace bytes"
            ),
        },
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended,
        "stop_conditions_for_next_round": [
            "Do not call the nonprintable preview a password or solved answer without runtime proof.",
            "Do not repeat the current target bytes printable inverse path.",
            "If runtime is proposed, require a separate bounded validation decision and an input-delivery plan.",
            "If target or transform evidence is contradicted, stop for tool/xref recheck rather than rerunning IDA ad hoc.",
        ],
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
    artifact_index.setdefault("latest_artifacts", {})[ARTIFACT_KEY] = normalized_path
    artifact_index.setdefault("artifact_refs", {})[ARTIFACT_KEY] = normalized_path
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


def run_alternative_static_semantics_review(
    *,
    target_revalidation_path: Path,
    inverse_handoff_path: Path,
    triage_path: Path,
    artifact_index_path: Path,
    negative_results_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    generated_at = _now_iso()
    artifact_index = _load_json(artifact_index_path)
    negative_results = _load_json(negative_results_path)
    if not isinstance(negative_results, list):
        raise ValueError("negative_results must be a list")
    result = build_alternative_static_semantics_review(
        target_revalidation=_load_json(target_revalidation_path),
        inverse_handoff=_load_json(inverse_handoff_path),
        triage=_load_json(triage_path),
        artifact_index=artifact_index,
        negative_results=negative_results,
        target_revalidation_path=target_revalidation_path,
        inverse_handoff_path=inverse_handoff_path,
        triage_path=triage_path,
        artifact_index_path=artifact_index_path,
        negative_results_path=negative_results_path,
        generated_at=generated_at,
    )
    _save_json(out_path, result)
    _update_artifact_index(
        artifact_index_path=artifact_index_path,
        out_path=out_path,
        generated_at=generated_at,
        sample_id=result["sample_id"],
    )
    print(f"cpp1 alternative static semantics review: action={result['recommended_next_action']}")
    print(
        "  nonprintable_static_preimage_preview_hex="
        f"{result['all_byte_preimage_review']['nonprintable_static_preimage_preview_hex']}"
    )
    print(f"  candidate={result['candidate']}")
    print(f"  runtime_validated={result['runtime_validated']}")
    print(f"  authoritative={result['authoritative']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cpp1 alternative static semantics review artifact.")
    parser.add_argument("--target-revalidation", type=Path, required=True)
    parser.add_argument("--inverse-handoff", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--artifact-index", type=Path, required=True)
    parser.add_argument("--negative-results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_alternative_static_semantics_review(
            target_revalidation_path=args.target_revalidation,
            inverse_handoff_path=args.inverse_handoff,
            triage_path=args.triage,
            artifact_index_path=args.artifact_index,
            negative_results_path=args.negative_results,
            out_path=args.out,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
