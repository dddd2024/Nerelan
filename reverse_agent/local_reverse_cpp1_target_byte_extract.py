"""Targeted compare-byte extraction for cpp1_2f6fcb63.

Reads the static triage artifact, runs IDA with extract_named_data.py to get
byte_429A30 bytes and _main_0 pseudocode, then produces a structured target-bytes
artifact.

Does NOT execute the sample. Does NOT generate candidates.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
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
    """Try to locate the LOCAL_REVERSE_ROOT directory."""
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
    """Resolve the full binary path using LOCAL_REVERSE_ROOT."""
    if not relative_path:
        return None
    root = _find_sample_root()
    if not root:
        return None
    full_path = root / relative_path
    return full_path if full_path.exists() else None


def _resolve_ida_executable() -> str:
    """Find IDA executable."""
    from .tool_runners import _resolve_ida_executable as resolve
    return resolve("")


def _resolve_ida_script() -> str:
    """Find extract_named_data.py script."""
    script_path = Path(__file__).parent / "ida_scripts" / "extract_named_data.py"
    if script_path.exists():
        return str(script_path)
    # Fallback: check env
    env_script = os.environ.get("REVERSE_AGENT_IDA_SCRIPT", "").strip()
    if env_script and Path(env_script).exists():
        return env_script
    return ""


def _run_ida_extraction(
    binary_path: Path,
    output_dir: Path,
    target_symbol: str = "byte_429A30",
    target_func: str = "_main_0",
) -> dict[str, Any]:
    """Run IDA with extract_named_data.py script."""
    ida_exec = _resolve_ida_executable()
    ida_script = _resolve_ida_script()

    if not ida_exec:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found"}
    if not ida_script:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA script not found"}

    output_dir.mkdir(parents=True, exist_ok=True)
    extract_out = output_dir / "named_data_extract.json"
    log_out = output_dir / "ida_extract.log"
    db_out = output_dir / "ida_extract.i64"

    # Clean up old DB files
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar = db_out.with_suffix(suffix)
        try:
            sidecar.unlink(missing_ok=True)
        except OSError:
            pass

    cmd = [
        ida_exec,
        "-A",
        f"-L{log_out}",
        f"-o{db_out}",
        f"-S{ida_script}",
        str(binary_path),
    ]

    env = dict(os.environ)
    env["REVERSE_AGENT_NAMED_DATA_OUT"] = str(extract_out)
    env["REVERSE_AGENT_TARGET_SYMBOL"] = target_symbol
    env["REVERSE_AGENT_TARGET_FUNC"] = target_func

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env=env,
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_TIMEOUT: IDA timed out after 300s"}
    except Exception as exc:
        return {"tool_status": "blocked", "blocked_reason": f"STATIC_TOOL_ERROR: {exc}"}

    # Parse extraction output
    if extract_out.exists():
        try:
            extract_data = _load_json(extract_out)
            return _parse_extraction(extract_data, exit_code)
        except (json.JSONDecodeError, KeyError) as exc:
            return {
                "tool_status": "blocked",
                "blocked_reason": f"STATIC_TOOL_PARSE_ERROR: {exc}",
                "exit_code": exit_code,
            }
    else:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no extraction JSON",
            "exit_code": exit_code,
        }


def _parse_extraction(extract_data: dict[str, Any], exit_code: int) -> dict[str, Any]:
    """Parse IDA extraction JSON into target-bytes fields."""
    named_data = extract_data.get("named_data", {})
    func_data = extract_data.get("function", {})
    compare_ctx = extract_data.get("compare_context", {})

    result: dict[str, Any] = {
        "tool_status": "success" if exit_code == 0 else "blocked",
        "blocked_reason": "" if exit_code == 0 else f"IDA_EXIT_CODE_{exit_code}",
        "source_tool": "IDA",
        "exit_code": exit_code,
    }

    # Named data extraction
    if named_data.get("found"):
        result["target_symbol"] = named_data.get("name", "")
        result["target_address"] = named_data.get("address", "")
        result["target_length"] = named_data.get("length", 0)
        result["target_bytes_hex"] = named_data.get("bytes_hex", "")
        result["target_bytes"] = named_data.get("bytes", [])
    else:
        result["target_symbol"] = extract_data.get("target_symbol", "byte_429A30")
        result["target_address"] = ""
        result["target_length"] = 0
        result["target_bytes_hex"] = ""
        result["target_bytes"] = []
        result["tool_status"] = "blocked"
        result["blocked_reason"] = "TARGET_BYTES_NOT_FOUND"

    # Function extraction
    if func_data.get("found"):
        result["main_function"] = func_data.get("name", "")
        result["main_function_address"] = func_data.get("address", "")
        result["main_pseudocode"] = func_data.get("pseudocode", "")
    else:
        result["main_function"] = extract_data.get("target_func", "_main_0")
        result["main_function_address"] = ""
        result["main_pseudocode"] = ""

    # Compare context
    result["compare_expression"] = compare_ctx.get("compare_expression", "")
    result["loop_context"] = compare_ctx.get("loop_context", "")

    return result


def _extract_forward_transform(pseudocode: str) -> dict[str, Any]:
    """Extract forward transform formula from _main_0 pseudocode."""
    transform = {
        "input_buffer": "Str",
        "work_buffer": "Destination",
        "copy_length": 16,
        "formula_c": "",
        "compare_expression": "Destination[i] == byte_429A30[i]",
        "notes": [],
    }

    if not pseudocode:
        return transform

    lines = pseudocode.split("\n")
    for line in lines:
        stripped = line.strip()
        # Look for the bit manipulation formula
        if "& 3" in stripped and "& 0x0C" in stripped and ">> 2" in stripped:
            transform["formula_c"] = stripped
            transform["notes"].append("nibble/bit-level transform detected")
        elif "& 3" in stripped and "* 16" in stripped and "& 0xF0" in stripped:
            transform["formula_c"] = stripped
            transform["notes"].append("nibble/bit-level transform detected")
        # Look for length checks
        if "!= 18" in stripped or "== 18" in stripped:
            transform["notes"].append(f"length check found: {stripped}")
        if "strncpy" in stripped.lower() or "memcpy" in stripped.lower():
            transform["notes"].append(f"copy operation: {stripped}")

    # Default formula if not found in pseudocode
    if not transform["formula_c"]:
        transform["formula_c"] = "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)"
        transform["notes"].append("formula from static triage evidence")

    return transform


def _build_evidence_notes(pseudocode: str) -> list[str]:
    """Build evidence notes from pseudocode anomalies."""
    notes = []
    if not pseudocode:
        return notes

    lower = pseudocode.lower()

    # Length discrepancy
    if "!= 18" in pseudocode and "== 16" in pseudocode:
        notes.append("length discrepancy: input must be 18 chars but compare loop checks 16 bytes")

    # Division anomaly (potential trap)
    if "/ v8" in pseudocode or "/ v9" in pseudocode:
        notes.append("division operation detected in path; potential anti-debug trap or dead code")

    # Memory check
    if "memory check" in lower:
        notes.append("memory check string found; may indicate anti-tampering")

    return notes


def run_target_byte_extraction(
    *,
    sample_id: str,
    triage_path: Path,
    inventory_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main logic: read triage, run IDA extraction, produce target-bytes artifact."""
    # Load triage artifact
    triage = _load_json(triage_path) if triage_path.exists() else {}
    inventory = _load_json(inventory_path) if inventory_path.exists() else {}

    relative_path = triage.get("relative_path", "")
    if not relative_path:
        # Try inventory
        for entry in inventory.get("entries", []):
            if entry.get("sample_id") == sample_id:
                relative_path = entry.get("relative_path", "")
                break

    if not relative_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="SAMPLE_NOT_FOUND_IN_TRIAGE_OR_INVENTORY",
        )
        _save_json(out_path, result)
        return result

    # Resolve binary path
    binary_path = _resolve_binary_path(relative_path)
    if not binary_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="BINARY_NOT_FOUND",
            detail=f"Could not resolve path: {relative_path}",
        )
        _save_json(out_path, result)
        return result

    # Run IDA extraction
    output_dir = out_path.parent / f"extract_{sample_id}"
    ida_result = _run_ida_extraction(binary_path, output_dir)

    tool_status = ida_result.get("tool_status", "blocked")
    blocked_reason = ida_result.get("blocked_reason", "")

    if tool_status == "blocked":
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason=blocked_reason,
            source_tool=ida_result.get("source_tool", "IDA"),
        )
        _save_json(out_path, result)
        return result

    # Build success artifact
    pseudocode = ida_result.get("main_pseudocode", "")
    forward_transform = _extract_forward_transform(pseudocode)
    evidence_notes = _build_evidence_notes(pseudocode)

    # Check if target bytes were actually found
    target_bytes = ida_result.get("target_bytes", [])
    if not target_bytes:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="TARGET_BYTES_NOT_FOUND",
            source_tool=ida_result.get("source_tool", "IDA"),
        )
        _save_json(out_path, result)
        return result

    recommended_next = "Target bytes extracted. Next round: create inverse-transform handoff to reverse the nibble/bit-level transform and recover password."

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": relative_path,
        "analysis_mode": "target_compare_byte_extraction",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "success",
        "blocked_reason": "",
        "source_tool": ida_result.get("source_tool", "IDA"),
        "target_symbol": ida_result.get("target_symbol", "byte_429A30"),
        "target_address": ida_result.get("target_address", ""),
        "target_length": ida_result.get("target_length", 0),
        "target_bytes_hex": ida_result.get("target_bytes_hex", ""),
        "target_bytes": target_bytes,
        "main_function": ida_result.get("main_function", "_main_0"),
        "main_function_address": ida_result.get("main_function_address", ""),
        "main_pseudocode": pseudocode[:2000] if pseudocode else "",
        "forward_transform": forward_transform,
        "compare_expression": ida_result.get("compare_expression", ""),
        "loop_context": ida_result.get("loop_context", ""),
        "evidence_notes": evidence_notes,
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended_next,
    }

    _save_json(out_path, result)
    print(f"target byte extraction: status=success sample_id={sample_id}")
    print(f"  target_symbol: {result['target_symbol']}")
    print(f"  target_address: {result['target_address']}")
    print(f"  target_length: {result['target_length']}")
    print(f"  target_bytes_hex: {result['target_bytes_hex'][:32]}...")
    print(f"  forward_transform_formula: {forward_transform['formula_c'][:60]}...")
    return result


def _blocked_artifact(
    *,
    sample_id: str,
    blocked_reason: str,
    detail: str = "",
    source_tool: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": "",
        "analysis_mode": "target_compare_byte_extraction",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "blocked",
        "blocked_reason": blocked_reason,
        "blocked_detail": detail,
        "source_tool": source_tool,
        "target_symbol": "byte_429A30",
        "target_address": "",
        "target_length": 0,
        "target_bytes_hex": "",
        "target_bytes": [],
        "main_function": "_main_0",
        "main_function_address": "",
        "main_pseudocode": "",
        "forward_transform": {
            "input_buffer": "Str",
            "work_buffer": "Destination",
            "copy_length": 16,
            "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
            "compare_expression": "Destination[i] == byte_429A30[i]",
            "notes": [],
        },
        "compare_expression": "",
        "loop_context": "",
        "evidence_notes": [],
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": f"Resolve blocker: {blocked_reason}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract target compare bytes from cpp1_2f6fcb63 using IDA.",
    )
    parser.add_argument("--sample-id", default="cpp1_2f6fcb63", help="Sample ID")
    parser.add_argument("--triage", default="project_state/local_reverse_cpp1_2f6fcb63_static_triage.json")
    parser.add_argument("--inventory", default="project_state/local_reverse_inventory.json")
    parser.add_argument("--out", default="project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json")
    args = parser.parse_args()

    try:
        run_target_byte_extraction(
            sample_id=args.sample_id,
            triage_path=Path(args.triage),
            inventory_path=Path(args.inventory),
            out_path=Path(args.out),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
