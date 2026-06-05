"""Bit-permutation inverse handoff generator for cpp1_2f6fcb63.

Reads a structured target-bytes artifact and produces an inverse-transform
handoff artifact with explicit forward/inverse bit mapping and static candidate
derivation.

Does NOT run the target binary. Does NOT generate a candidate unless target
bytes are present and auditable. Does NOT mark solved or write known_candidate.
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
# Transform logic
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


def _is_printable_ascii(b: int) -> bool:
    return 0x20 <= b <= 0x7E


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run_cpp1_inverse_handoff(
    input_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main logic: parse target bytes artifact, compute inverse, emit handoff."""
    artifact = _load_json(input_path)

    sample_id = str(artifact.get("sample_id", ""))
    if not sample_id:
        raise ValueError("Input artifact missing sample_id")

    # Validate target bytes artifact fields
    expected_target_length = artifact.get("expected_target_length")
    target_length = artifact.get("target_length")
    target_bytes_hex = str(artifact.get("target_bytes_hex", ""))
    target_bytes = artifact.get("target_bytes", [])

    executed_sample = artifact.get("executed_sample")
    static_only = artifact.get("static_only")
    runtime_validated = artifact.get("runtime_validated")
    candidate = artifact.get("candidate")
    known_candidate = str(artifact.get("known_candidate", ""))

    # Pre-flight checks
    if expected_target_length != 16:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="INVALID_TARGET_LENGTH",
            detail=f"expected_target_length={expected_target_length}, required=16",
        )
        _save_json(out_path, result)
        return result

    if target_length != 16:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="INVALID_TARGET_LENGTH",
            detail=f"target_length={target_length}, required=16",
        )
        _save_json(out_path, result)
        return result

    if len(target_bytes) != 16:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="INVALID_TARGET_LENGTH",
            detail=f"len(target_bytes)={len(target_bytes)}, required=16",
        )
        _save_json(out_path, result)
        return result

    if executed_sample is not False:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNEXPECTED_EXECUTED_SAMPLE",
            detail=f"executed_sample={executed_sample}, must be false for static-only handoff",
        )
        _save_json(out_path, result)
        return result

    if static_only is not True:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNEXPECTED_STATIC_ONLY",
            detail=f"static_only={static_only}, must be true",
        )
        _save_json(out_path, result)
        return result

    if runtime_validated is not False:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNEXPECTED_RUNTIME_VALIDATED",
            detail=f"runtime_validated={runtime_validated}, must be false",
        )
        _save_json(out_path, result)
        return result

    if candidate is not None:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNEXPECTED_PRIOR_CANDIDATE",
            detail="Input artifact has candidate set; expected null for static inverse handoff.",
        )
        _save_json(out_path, result)
        return result

    if known_candidate != "":
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNEXPECTED_PRIOR_CANDIDATE",
            detail=f"known_candidate='{known_candidate}', expected empty string",
        )
        _save_json(out_path, result)
        return result

    # Compute inverse transform on target bytes
    static_candidate_bytes = [inverse_transform_byte(b) for b in target_bytes]
    static_candidate_bytes_hex = "".join(f"{b:02x}" for b in static_candidate_bytes)

    # Check printable ASCII
    printable_ascii = all(_is_printable_ascii(b) for b in static_candidate_bytes)
    static_candidate_text = "".join(chr(b) for b in static_candidate_bytes) if printable_ascii else None

    if printable_ascii:
        status = "STATIC_CANDIDATE_DERIVED"
        blocked_reason = ""
    else:
        status = "BLOCKED"
        blocked_reason = "STATIC_CANDIDATE_NONPRINTABLE"

    # Build evidence notes from source artifact
    evidence_notes = list(artifact.get("evidence_notes", []))
    if not any("length discrepancy" in note for note in evidence_notes):
        evidence_notes.append("length discrepancy: input must be 18 chars but compare loop checks 16 bytes")
    if not any("division operation" in note for note in evidence_notes):
        evidence_notes.append("division operation detected in path; potential anti-debug trap or dead code")

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "static_inverse_transform_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifact": str(input_path).replace("\\", "/"),
        "target_bytes_hex": target_bytes_hex,
        "expected_target_length": 16,
        "forward_transform": {
            "formula": "y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)",
            "bit_mapping": [
                "y0=x0", "y1=x1", "y2=x4", "y3=x5",
                "y4=x6", "y5=x7", "y6=x2", "y7=x3",
            ],
        },
        "inverse_transform": {
            "formula": "x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)",
            "bit_mapping": [
                "x0=y0", "x1=y1", "x2=y6", "x3=y7",
                "x4=y2", "x5=y3", "x6=y4", "x7=y5",
            ],
        },
        "static_candidate_bytes_hex": static_candidate_bytes_hex,
        "static_candidate_bytes": static_candidate_bytes,
        "static_candidate_text": static_candidate_text,
        "printable_ascii": printable_ascii,
        "candidate": None,
        "known_candidate": "",
        "status": status,
        "blocked_reason": blocked_reason,
        "evidence_notes": evidence_notes,
        "recommended_next_action": (
            "If candidate is non-printable, require static re-check of transform semantics or allowed dynamic validation; do not mark solved."
            if not printable_ascii
            else "Static candidate derived from inverse transform. Runtime validation required before marking solved."
        ),
    }

    _save_json(out_path, result)

    print(f"cpp1 inverse handoff: status={status} sample_id={sample_id}")
    print(f"  target_bytes_hex={target_bytes_hex}")
    print(f"  static_candidate_bytes_hex={static_candidate_bytes_hex}")
    print(f"  printable_ascii={printable_ascii}")
    if static_candidate_text:
        print(f"  static_candidate_text={static_candidate_text}")
    if blocked_reason:
        print(f"  blocked_reason={blocked_reason}")

    return result


def _blocked_result(
    sample_id: str,
    source_artifact: str,
    blocked_reason: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "static_inverse_transform_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifact": source_artifact.replace("\\", "/"),
        "target_bytes_hex": "",
        "expected_target_length": 16,
        "forward_transform": {
            "formula": "y = (x & 0x03) | ((x & 0x0C) << 4) | ((x & 0xF0) >> 2)",
            "bit_mapping": [
                "y0=x0", "y1=x1", "y2=x4", "y3=x5",
                "y4=x6", "y5=x7", "y6=x2", "y7=x3",
            ],
        },
        "inverse_transform": {
            "formula": "x = (y & 0x03) | ((y & 0xC0) >> 4) | ((y & 0x3C) << 2)",
            "bit_mapping": [
                "x0=y0", "x1=y1", "x2=y6", "x3=y7",
                "x4=y2", "x5=y3", "x6=y4", "x7=y5",
            ],
        },
        "static_candidate_bytes_hex": "",
        "static_candidate_bytes": [],
        "static_candidate_text": None,
        "printable_ascii": False,
        "candidate": None,
        "known_candidate": "",
        "status": "BLOCKED",
        "blocked_reason": blocked_reason,
        "blocked_detail": detail,
        "evidence_notes": [
            "length discrepancy: input must be 18 chars but compare loop checks 16 bytes",
            "division operation detected in path; potential anti-debug trap or dead code",
        ],
        "recommended_next_action": "Review input artifact and resolve blocker before inverse transform handoff.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate bit-permutation inverse handoff from static target-bytes artifact.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json"),
        help="Path to target-bytes artifact",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json"),
        help="Output path for inverse handoff JSON",
    )
    args = parser.parse_args()

    try:
        run_cpp1_inverse_handoff(args.input, args.out)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
