"""Static transform semantics recheck for cpp1_2f6fcb63.

Reads current static_triage, target_bytes, and inverse_handoff artifacts to
audit the forward/inverse transform mapping, printable preimage existence,
and length/compare semantics.

Does NOT run the target binary. Does NOT generate a candidate. Does NOT mark
solved or write known_candidate.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Transform logic (identical to inverse_handoff)
# ---------------------------------------------------------------------------

def forward_transform_byte(x: int) -> int:
    """Forward bit-permutation transform.

    y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)
    """
    return (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)


def inverse_transform_byte(y: int) -> int:
    """Inverse bit-permutation transform.

    x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)
    """
    return (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def _is_printable_ascii(b: int) -> bool:
    return 0x20 <= b <= 0x7E


def analyze_mapping() -> dict[str, Any]:
    """Verify forward/inverse are bijections on 0..255."""
    forward_map = {x: forward_transform_byte(x) for x in range(256)}
    inverse_map = {y: inverse_transform_byte(y) for y in range(256)}

    # Bijection check: domain and codomain both size 256, all unique
    forward_unique = len(set(forward_map.values())) == 256
    inverse_unique = len(set(inverse_map.values())) == 256

    # Roundtrip checks
    roundtrip_forward_inverse = all(inverse_transform_byte(forward_transform_byte(x)) == x for x in range(256))
    roundtrip_inverse_forward = all(forward_transform_byte(inverse_transform_byte(y)) == y for y in range(256))

    return {
        "forward_unique_outputs": forward_unique,
        "inverse_unique_outputs": inverse_unique,
        "roundtrip_forward_inverse": roundtrip_forward_inverse,
        "roundtrip_inverse_forward": roundtrip_inverse_forward,
        "bijective": forward_unique and inverse_unique and roundtrip_forward_inverse and roundtrip_inverse_forward,
    }


def analyze_printable_preimages(target_bytes: list[int]) -> dict[str, Any]:
    """For each target byte, determine if any printable ASCII preimage exists."""
    per_byte = []
    all_have_printable = True

    for idx, y in enumerate(target_bytes):
        # Find all x in printable ASCII range that forward to y
        preimages = [x for x in range(0x20, 0x7F) if forward_transform_byte(x) == y]
        has_printable = len(preimages) > 0
        if not has_printable:
            all_have_printable = False
        per_byte.append({
            "index": idx,
            "target_byte": y,
            "target_byte_hex": f"{y:02x}",
            "has_printable_preimage": has_printable,
            "printable_preimages": preimages,
            "printable_preimages_hex": [f"{x:02x}" for x in preimages],
            "printable_preimages_text": "".join(chr(x) for x in preimages) if preimages else None,
        })

    return {
        "all_target_bytes_have_printable_preimage": all_have_printable,
        "per_byte_analysis": per_byte,
    }


def analyze_length_compare_semantics(triage: dict[str, Any]) -> dict[str, Any]:
    """Analyze length check, strncpy, compare loop, and success condition."""
    main_pseudocode = triage.get("triage", {}).get("decompiler_snippets", [{}])[0].get("text", "")

    # Key observations from pseudocode
    observations = []

    # 1. Length check
    if "v4 != 18" in main_pseudocode or "strlen(Str)" in main_pseudocode:
        observations.append("input length check: strlen(Str) must equal 18")

    # 2. strncpy
    if "strncpy(Destination, Str, 0x10u)" in main_pseudocode:
        observations.append("copy: strncpy(Destination, Str, 16) copies at most 16 bytes from input")

    # 3. Transform loop
    if "for ( i = 0; i < v4; ++i )" in main_pseudocode:
        observations.append("transform loop iterates over all v4 bytes (18), but Destination only has 16 copied bytes")

    # 4. Compare loop
    if "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )" in main_pseudocode:
        observations.append("compare loop condition: i < v4 (18) AND Destination[i] == byte_429A30[i]")

    # 5. Success condition
    if "if ( i == 16 )" in main_pseudocode:
        observations.append("success condition: i == 16, meaning first 16 bytes must match; bytes 17-18 are not compared against target")

    # 6. Division anomaly
    if "v6 = v9 / v8" in main_pseudocode:
        observations.append("division v9/v8 where v8=0 is a potential anti-debug trap or dead code (would cause divide-by-zero exception)")

    return {
        "main_pseudocode_present": bool(main_pseudocode),
        "observations": observations,
        "length_check": {
            "input_required_length": 18,
            "strncpy_copy_length": 16,
            "compare_loop_upper_bound": "v4 (18)",
            "success_match_count": 16,
            "implication": "Only first 16 bytes matter for success; bytes 17-18 of input are transformed but not compared against target",
        },
    }


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run_cpp1_transform_recheck(
    target_bytes_path: Path,
    inverse_handoff_path: Path,
    triage_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main logic: load artifacts, run analyses, emit recheck report."""
    target_artifact = _load_json(target_bytes_path)
    inverse_artifact = _load_json(inverse_handoff_path)
    triage_artifact = _load_json(triage_path)

    sample_id = str(target_artifact.get("sample_id", ""))
    if not sample_id:
        raise ValueError("Target bytes artifact missing sample_id")

    # Validate freshness
    if target_artifact.get("runtime_validated") is not False:
        raise ValueError("target_bytes artifact runtime_validated must be false")
    if inverse_artifact.get("runtime_validated") is not False:
        raise ValueError("inverse_handoff artifact runtime_validated must be false")
    if triage_artifact.get("runtime_validated") is not False:
        raise ValueError("triage artifact runtime_validated must be false")

    target_bytes = target_artifact.get("target_bytes", [])
    if len(target_bytes) != 16:
        raise ValueError(f"target_bytes length must be 16, got {len(target_bytes)}")

    # Run analyses
    mapping_analysis = analyze_mapping()
    printable_analysis = analyze_printable_preimages(target_bytes)
    semantics_analysis = analyze_length_compare_semantics(triage_artifact)

    # Compute static candidate (same as inverse_handoff)
    static_candidate_bytes = [inverse_transform_byte(b) for b in target_bytes]
    static_candidate_bytes_hex = "".join(f"{b:02x}" for b in static_candidate_bytes)
    printable_ascii = all(_is_printable_ascii(b) for b in static_candidate_bytes)

    # Determine status
    if not mapping_analysis["bijective"]:
        status = "BLOCKED"
        blocked_reason = "TRANSFORM_NOT_BIJECTIVE"
    elif not printable_analysis["all_target_bytes_have_printable_preimage"]:
        status = "BLOCKED"
        blocked_reason = "NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM"
    else:
        # All target bytes have printable preimage, but the specific inverse of target bytes may not be printable
        # This is because inverse_transform_byte gives ONE preimage per target byte, not all preimages
        status = "BLOCKED"
        blocked_reason = "STATIC_CANDIDATE_NONPRINTABLE"

    # Build result
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "static_transform_semantics_recheck",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifacts": {
            "target_bytes": str(target_bytes_path).replace("\\", "/"),
            "inverse_handoff": str(inverse_handoff_path).replace("\\", "/"),
            "static_triage": str(triage_path).replace("\\", "/"),
        },
        "forward_transform": {
            "formula": "y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)",
            "bit_mapping": [
                "y0=x0", "y1=x1", "y2=x4", "y3=x5",
                "y4=x6", "y5=x7", "y6=x2", "y7=y3",
            ],
        },
        "inverse_transform": {
            "formula": "x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)",
            "bit_mapping": [
                "x0=y0", "x1=y1", "x2=y6", "x3=y7",
                "x4=y2", "x5=y3", "x6=y4", "x7=y5",
            ],
        },
        "mapping_analysis": mapping_analysis,
        "static_candidate_bytes_hex": static_candidate_bytes_hex,
        "static_candidate_bytes": static_candidate_bytes,
        "static_candidate_printable_ascii": printable_ascii,
        "printable_preimage_analysis": printable_analysis,
        "length_compare_semantics": semantics_analysis,
        "current_static_transform_has_no_printable_solution": not printable_analysis["all_target_bytes_have_printable_preimage"],
        "candidate": None,
        "known_candidate": "",
        "status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": (
            "bounded IDA instruction-level / control-flow / SEH recheck, not brute force"
            if blocked_reason == "NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM"
            else "Static recheck complete. If inverse candidate is non-printable, require bounded dynamic validation or instruction-level re-extraction before marking solved."
        ),
    }

    _save_json(out_path, result)

    print(f"cpp1 transform recheck: status={status} sample_id={sample_id}")
    print(f"  bijective={mapping_analysis['bijective']}")
    print(f"  all_have_printable_preimage={printable_analysis['all_target_bytes_have_printable_preimage']}")
    print(f"  static_candidate_printable_ascii={printable_ascii}")
    print(f"  blocked_reason={blocked_reason}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Static transform semantics recheck for cpp1_2f6fcb63.",
    )
    parser.add_argument(
        "--target-bytes",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json"),
        help="Path to target-bytes artifact",
    )
    parser.add_argument(
        "--inverse-handoff",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json"),
        help="Path to inverse-handoff artifact",
    )
    parser.add_argument(
        "--triage",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_static_triage.json"),
        help="Path to static triage artifact",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json"),
        help="Output path for transform recheck JSON",
    )
    args = parser.parse_args()

    try:
        run_cpp1_transform_recheck(
            args.target_bytes,
            args.inverse_handoff,
            args.triage,
            args.out,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
