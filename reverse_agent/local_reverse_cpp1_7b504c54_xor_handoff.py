"""Static XOR inverse handoff for cpp1_7b504c54.

Reads the static triage artifact, extracts three 10-byte arrays from the PE
binary at known virtual addresses, and computes the static candidate using the
confirmed double-XOR inverse formula.

Does NOT execute the target binary. Does NOT validate at runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
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


def _find_sample_root() -> Path | None:
    candidates = [
        os.environ.get("LOCAL_REVERSE_ROOT", ""),
        r"E:\reverse",
        r"D:\reverse",
        r"C:\reverse",
    ]
    home_reverse = str(Path.home() / "reverse")
    candidates.append(home_reverse)
    for c_str in candidates:
        c_str = c_str.strip()
        if not c_str:
            continue
        if os.path.isdir(c_str):
            return Path(c_str)
    return None


def _resolve_binary_path(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    root = _find_sample_root()
    if not root:
        return None
    full_path = root / relative_path
    return full_path if full_path.exists() else None


def _va_to_file_offset(data: bytearray, image_base: int, target_va: int) -> int | None:
    target_rva = target_va - image_base
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
    opt_header_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    section_table = pe_offset + 24 + opt_header_size
    for i in range(num_sections):
        sec_off = section_table + i * 40
        vaddr = struct.unpack_from("<I", data, sec_off + 12)[0]
        raw_addr = struct.unpack_from("<I", data, sec_off + 20)[0]
        raw_size = struct.unpack_from("<I", data, sec_off + 16)[0]
        if vaddr <= target_rva < vaddr + raw_size:
            return raw_addr + (target_rva - vaddr)
    return None


def _extract_arrays(binary_path: Path) -> dict[str, Any]:
    with open(binary_path, "rb") as f:
        data = bytearray(f.read())

    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    image_base = struct.unpack_from("<I", data, pe_offset + 24 + 28)[0]

    arrays = {}
    for name, va in [
        ("byte_427A30", 0x427A30),
        ("byte_427A3C", 0x427A3C),
        ("byte_427A48", 0x427A48),
    ]:
        offset = _va_to_file_offset(data, image_base, va)
        if offset is None:
            return {"status": "BLOCKED", "blocked_reason": f"MISSING_STATIC_ARRAY_BYTES: {name} not found in PE sections"}
        arr = data[offset:offset + 10]
        if len(arr) < 10:
            return {"status": "BLOCKED", "blocked_reason": f"MISSING_STATIC_ARRAY_BYTES: {name} truncated ({len(arr)} bytes)"}
        arrays[name] = {"address": f"0x{va:06X}", "bytes_hex": arr.hex(), "length": 10}

    # Compute candidate: Str[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]
    arr1 = bytes.fromhex(arrays["byte_427A30"]["bytes_hex"])
    arr2 = bytes.fromhex(arrays["byte_427A3C"]["bytes_hex"])
    arr3 = bytes.fromhex(arrays["byte_427A48"]["bytes_hex"])

    candidate = bytearray(10)
    for i in range(10):
        candidate[i] = arr1[9 - i] ^ arr2[i] ^ arr3[i]

    candidate_hex = candidate.hex()
    candidate_text = "".join(chr(b) if 32 <= b < 127 else "?" for b in candidate)
    printable = all(32 <= b < 127 for b in candidate)

    # Verify forward transform
    v4_20 = bytearray(10)
    v4 = bytearray(10)
    for i in range(10):
        v4_20[i] = arr1[9 - i] ^ candidate[i]
        v4[i] = arr2[i] ^ v4_20[i]
    forward_match = v4 == arr3

    return {
        "status": "READY_FOR_STATIC_REVIEW",
        "blocked_reason": "",
        "arrays": arrays,
        "candidate_hex": candidate_hex,
        "candidate_text": candidate_text,
        "candidate_printable": printable,
        "forward_transform_verified": forward_match,
    }


def run_xor_handoff(
    *,
    static_triage_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    triage = _load_json(static_triage_path)
    sample_id = triage.get("sample_id", "")
    relative_path = triage.get("relative_path", "")
    sha256 = triage.get("sha256", "")

    if sample_id != "cpp1_7b504c54":
        raise ValueError(f"Expected sample_id=cpp1_7b504c54, got {sample_id}")

    binary_path = _resolve_binary_path(relative_path)
    if not binary_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            sha256=sha256,
            blocked_reason="BINARY_NOT_FOUND",
        )
        _save_json(out_path, result)
        return result

    extraction = _extract_arrays(binary_path)

    if extraction["status"] == "BLOCKED":
        result = _blocked_artifact(
            sample_id=sample_id,
            sha256=sha256,
            blocked_reason=extraction["blocked_reason"],
        )
        _save_json(out_path, result)
        return result

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "cpp1_7b504c54_static_xor_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifacts": ["local_reverse_cpp1_7b504c54_static_triage"],
        "source_artifact_freshness": "current",
        "source_triage_artifact": "project_state/local_reverse_cpp1_7b504c54_static_triage.json",
        "main_function": "_main_0",
        "main_entry_ea": "0x401110",
        "input_length": 10,
        "transform_formula": "candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]",
        "arrays": extraction["arrays"],
        "static_candidate_hex": extraction["candidate_hex"],
        "static_candidate_text": extraction["candidate_text"],
        "static_candidate_printable": extraction["candidate_printable"],
        "forward_transform_verified": extraction["forward_transform_verified"],
        "candidate": None,
        "known_candidate": "",
        "validation_status": "not_validated",
        "solved": False,
        "recommended_next_action": "Static candidate computed. Runtime validation or manual review required before marking solved.",
        "status": extraction["status"],
        "blocked_reason": "",
    }

    _save_json(out_path, result)
    print(f"xor_handoff: status={extraction['status']} sample_id={sample_id}")
    print(f"  candidate_hex: {extraction['candidate_hex']}")
    print(f"  candidate_text: {extraction['candidate_text']}")
    print(f"  printable: {extraction['candidate_printable']}")
    print(f"  forward_verified: {extraction['forward_transform_verified']}")
    return result


def _blocked_artifact(
    *,
    sample_id: str,
    sha256: str,
    blocked_reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "cpp1_7b504c54_static_xor_handoff",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifacts": ["local_reverse_cpp1_7b504c54_static_triage"],
        "source_artifact_freshness": "current",
        "source_triage_artifact": "project_state/local_reverse_cpp1_7b504c54_static_triage.json",
        "main_function": "_main_0",
        "main_entry_ea": "0x401110",
        "input_length": 10,
        "transform_formula": "candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]",
        "arrays": {},
        "static_candidate_hex": "",
        "static_candidate_text": "",
        "static_candidate_printable": False,
        "forward_transform_verified": False,
        "candidate": None,
        "known_candidate": "",
        "validation_status": "not_validated",
        "solved": False,
        "recommended_next_action": f"Resolve blocker: {blocked_reason}",
        "status": "BLOCKED",
        "blocked_reason": blocked_reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Static XOR inverse handoff for cpp1_7b504c54.",
    )
    parser.add_argument("--static-triage", default="project_state/local_reverse_cpp1_7b504c54_static_triage.json")
    parser.add_argument("--out", default="project_state/local_reverse_cpp1_7b504c54_xor_handoff.json")
    args = parser.parse_args()

    try:
        run_xor_handoff(
            static_triage_path=Path(args.static_triage),
            out_path=Path(args.out),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
