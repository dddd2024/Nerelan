"""Input delivery review for cpp1_2f6fcb63.

This module stays static-only: it reads current artifacts, classifies the
non-printable all-byte preimage, reviews input delivery options, and records
the next evidence route without executing the sample or rerunning static tools.
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


ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_input_delivery_review"
ARTIFACT_KIND = "input_delivery_review"
SOURCE_RUN = "round_20260614_cpp1_2f6fcb63_input_delivery_review_v1"
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

    scanf_hard_blocker = sorted(buckets["nul_indices"] + buckets["whitespace_indices"])
    strlen_hard_blocker = sorted(buckets["nul_indices"])
    return {
        "preimage_hex": bytes(preimage).hex(),
        "preimage_length": len(preimage),
        "per_byte": per_byte,
        **buckets,
        "scanf_percent_s_hard_blocker_indices": scanf_hard_blocker,
        "strlen_hard_blocker_indices": strlen_hard_blocker,
        "contains_nul": bool(buckets["nul_indices"]),
        "contains_whitespace": bool(buckets["whitespace_indices"]),
        "contains_control": bool(buckets["control_indices"]),
        "contains_high_bit": bool(buckets["high_bit_indices"]),
        "all_bytes_non_nul_non_whitespace": not scanf_hard_blocker,
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


def build_input_delivery_review(
    *,
    input_review_path: Path,
    target_revalidation_path: Path,
    inverse_handoff_path: Path,
    triage_path: Path,
    artifact_index_path: Path,
    negative_results_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or _now_iso()
    artifact_index = _load_json(artifact_index_path)
    negative_results = _load_json(negative_results_path)
    if not isinstance(negative_results, list):
        raise ValueError("negative_results must be a list")

    input_review = _load_json(input_review_path)
    target_revalidation = _load_json(target_revalidation_path)
    inverse_handoff = _load_json(inverse_handoff_path)
    triage = _load_json(triage_path)

    # (a) Validate all 4 source artifacts are current
    input_review_entry = _require_current_artifact(
        artifact_index=artifact_index,
        artifact_key="local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review",
        artifact=input_review,
        path=input_review_path,
        expected_analysis_mode="alternative_static_semantics_review",
    )
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

    # (b) Consume the printable inverse negative result
    negative_entry = _require_negative_result(negative_results)

    # (c) Validate target revalidation passed, inverse handoff is blocked
    if target_revalidation.get("revalidation_status") != "PASSED":
        raise ValueError("target revalidation has not passed")
    if inverse_handoff.get("blocked_reason") != "NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES":
        raise ValueError("inverse handoff is not the expected printable-preimage blocker")

    # (d) Extract the 16-byte preimage from inverse handoff
    preimage = _extract_all_byte_preimage(inverse_handoff)

    # (e) Classify the preimage bytes
    classification = _classify_preimage(preimage)

    # (f) Build preimage_input_domain_review
    preimage_input_domain_review = {
        "nul_indices": classification["nul_indices"],
        "whitespace_indices": classification["whitespace_indices"],
        "control_indices": classification["control_indices"],
        "high_bit_indices": classification["high_bit_indices"],
        "printable_ascii_indices": classification["printable_ascii_indices"],
        "scanf_percent_s_hard_blocker_indices": classification["scanf_percent_s_hard_blocker_indices"],
        "strlen_hard_blocker_indices": classification["strlen_hard_blocker_indices"],
        "windows_console_manual_entry_risk": (
            "high" if classification["contains_control"] or classification["contains_high_bit"] else "low"
        ),
    }

    # (g) Build payload_length_review
    payload_length_review = {
        "first_16_bytes_copied_by_strncpy": True,
        "strncpy_length": 16,
        "strlen_required": 18,
        "suffix_bytes_17_18_purpose": "satisfy_strlen_18_only",
        "suffix_bytes_do_not_control_destination_16": True,
        "suffix_must_be_non_nul_non_whitespace": True,
        "suggested_suffix_placeholder": "AA",
        "suggested_suffix_placeholder_hex": "4141",
    }

    # (h) Build suffix_policy
    suffix_policy = {
        "suffix_length": 2,
        "suffix_must_not_contain_nul": True,
        "suffix_must_not_contain_whitespace": True,
        "suffix_suggested_hex": "4141",
        "suffix_suggested_text": "AA",
        "suffix_participates_in_transform": True,
        "suffix_does_not_control_destination_16": True,
    }

    # (i) Build success_boundary_review
    success_boundary_review = {
        "compare_loop_condition": "i < v4 && Destination[i] == byte_429A30[i]",
        "v4_equals_strlen": 18,
        "success_condition": "i == 16",
        "strncpy_copies_only_16_bytes": True,
        "destination_index_16_source": "uninitialized/previous Destination buffer content, then transformed",
        "byte_429A30_index_16_known": False,
        "destination_16_equals_byte_429A30_16": "UNKNOWN",
        "success_boundary_status": "UNKNOWN_NEEDS_STATIC_OR_TOOL_RECHECK",
        "evidence_source": (
            "current static artifacts only; byte_429A30[16] not available in "
            "target_bytes_revalidation (target_length=16)"
        ),
        "risk_if_index_16_matches": (
            "loop continues to i=17/18, i != 16 at exit, success condition fails"
        ),
    }

    # (j) Build delivery_options_review
    delivery_options_review = {
        "windows_console_manual_entry": {
            "feasible": False,
            "risk": "high",
            "reason": "control and high-bit bytes cannot be reliably typed",
            "candidate_for_next_round": False,
        },
        "powershell_raw_byte_file_redirection": {
            "feasible": True,
            "risk": "low",
            "candidate_for_next_round": True,
            "command_template": (
                "$bytes = [byte[]]@(PREIMAGE_BYTES_PLACEHOLDER,0x41,0x41); "
                "[System.IO.File]::WriteAllBytes('input.bin', $bytes); "
                "Get-Content -Raw input.bin | .\\CPP1.exe"
            ),
        },
        "python_subprocess_raw_stdin": {
            "feasible": True,
            "risk": "low",
            "candidate_for_next_round": True,
            "command_template": (
                "import subprocess; "
                "payload = bytes(PREIMAGE_BYTES_PLACEHOLDER + b'AA'); "
                "proc = subprocess.run(['CPP1.exe'], input=payload, capture_output=True)"
            ),
        },
        "file_redirection": {
            "feasible": True,
            "risk": "low",
            "candidate_for_next_round": True,
            "notes": "write raw bytes to file, redirect to stdin",
        },
        "debugger_memory_write": {
            "feasible": "unknown",
            "risk": "medium",
            "candidate_for_next_round": False,
            "notes": "only if raw stdin/file redirection fails; needs separate tool_integration decision",
        },
    }

    # (k) Build payload_preview_hex
    payload_preview_hex = classification["preimage_hex"] + "4141"

    # (l) candidate and known_candidate
    # (m) Determine recommended_next_action
    has_hard_blocker = classification["contains_nul"] or classification["contains_whitespace"]
    if has_hard_blocker:
        recommended_next_action = "BLOCKED_INPUT_DELIVERY_HARD_BLOCKER"
    elif success_boundary_review["success_boundary_status"] == "UNKNOWN_NEEDS_STATIC_OR_TOOL_RECHECK":
        recommended_next_action = "NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK"
    else:
        recommended_next_action = "READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION"

    # (n) Build stop_conditions_for_next_round
    stop_conditions_for_next_round = [
        "Do not call the nonprintable preview a password or solved answer without runtime proof.",
        "Do not repeat the current target bytes printable inverse path.",
        "If runtime is proposed, require a separate bounded validation decision and an input-delivery plan.",
        "If success boundary remains UNKNOWN, do not proceed to runtime validation without static or tool recheck of byte_429A30[16].",
        "If target or transform evidence is contradicted, stop for tool/xref recheck rather than rerunning IDA ad hoc.",
    ]

    target_bytes_hex = str(target_revalidation.get("target_bytes_hex", ""))

    return {
        "schema_version": 1,
        "sample_id": SAMPLE_ID,
        "relative_path": target_revalidation.get("relative_path", ""),
        "sha256": target_revalidation.get("sha256", ""),
        "analysis_mode": "input_delivery_review",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "authoritative": False,
        "generated_at": generated,
        "source_artifacts": {
            "alternative_static_semantics_review": _norm(input_review_path),
            "target_revalidation": _norm(target_revalidation_path),
            "static_inverse_handoff": _norm(inverse_handoff_path),
            "static_triage": _norm(triage_path),
            "artifact_index": _norm(artifact_index_path),
            "negative_results": _norm(negative_results_path),
        },
        "source_artifact_freshness": {
            "alternative_static_semantics_review": _source_freshness(
                input_review_entry,
                "local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review",
            ),
            "target_revalidation": _source_freshness(
                target_entry,
                "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
            ),
            "static_inverse_handoff": _source_freshness(
                inverse_entry,
                "local_reverse_cpp1_2f6fcb63_static_inverse_handoff",
            ),
            "static_triage": _source_freshness(
                triage_entry,
                "local_reverse_cpp1_2f6fcb63_static_triage",
            ),
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
        "preimage_input_domain_review": preimage_input_domain_review,
        "payload_length_review": payload_length_review,
        "suffix_policy": suffix_policy,
        "success_boundary_review": success_boundary_review,
        "delivery_options_review": delivery_options_review,
        "payload_preview_hex": payload_preview_hex,
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended_next_action,
        "stop_conditions_for_next_round": stop_conditions_for_next_round,
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


def run_input_delivery_review(
    *,
    input_review_path: Path,
    target_revalidation_path: Path,
    inverse_handoff_path: Path,
    triage_path: Path,
    artifact_index_path: Path,
    negative_results_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    generated_at = _now_iso()
    result = build_input_delivery_review(
        input_review_path=input_review_path,
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
    print(f"cpp1 input delivery review: action={result['recommended_next_action']}")
    print(f"  payload_preview_hex={result['payload_preview_hex']}")
    print(f"  candidate={result['candidate']}")
    print(f"  runtime_validated={result['runtime_validated']}")
    print(f"  authoritative={result['authoritative']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cpp1 input delivery review artifact.")
    parser.add_argument("--input-review", type=Path, required=True,
                        help="path to alternative_static_semantics_review.json")
    parser.add_argument("--target-revalidation", type=Path, required=True)
    parser.add_argument("--inverse-handoff", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--artifact-index", type=Path, required=True)
    parser.add_argument("--negative-results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_input_delivery_review(
            input_review_path=args.input_review,
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
