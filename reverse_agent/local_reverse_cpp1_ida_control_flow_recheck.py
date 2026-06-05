"""Bounded IDA static control-flow / instruction-level / SEH recheck for cpp1_2f6fcb63.

Attempts a bounded headless IDA extraction targeting:
- _main_0 / 0x401190 control flow
- division instruction context
- transform loop
- compare loop
- byte_429A30 xrefs
- SEH/exception metadata

If IDA is unavailable, generates a BLOCKED artifact with IDA_UNAVAILABLE.
Does NOT dynamically execute the sample. Does NOT write candidate/known_candidate.
Does NOT mark solved.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.tool_runners import _resolve_ida_executable


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
# IDA extraction
# ---------------------------------------------------------------------------

def _find_binary_path(artifact_index: dict[str, Any], sample_id: str) -> Path | None:
    """Find binary path from artifact_index or default locations."""
    # Try to find from artifact_index evidence paths
    v2 = artifact_index.get("latest_artifacts_v2", {})
    triage_key = f"local_reverse_cpp1_{sample_id}_static_triage"
    triage_meta = v2.get(triage_key, {})
    triage_path = triage_meta.get("path", "")
    if triage_path:
        triage_dir = Path(triage_path).parent
        # Look for .exe in the same directory or parent
        for pattern in ("*.exe", "../*.exe", "../../*.exe"):
            candidates = list(triage_dir.glob(pattern))
            for c in candidates:
                if c.name.lower() == "cpp1.exe":
                    return c
                if sample_id.lower() in c.stem.lower():
                    return c
    # Fallback: try E:\reverse
    fallback = Path("E:\\reverse\\逆向课程2023春01\\CPP1.exe")
    if fallback.exists():
        return fallback
    return None


def _run_bounded_ida_control_flow(
    binary_path: Path,
    output_path: Path,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Run IDA in batch mode with a bounded control-flow extraction script."""
    result: dict[str, Any] = {
        "ida_attempted": True,
        "ida_available": False,
        "ida_success": False,
        "error": "",
    }

    ida_executable = _resolve_ida_executable("")
    if not ida_executable:
        result["error"] = "IDA executable not found (idat64.exe/idat.exe/ida64.exe/ida.exe)"
        result["blocked_reason"] = "IDA_UNAVAILABLE"
        return result

    result["ida_available"] = True

    # Use idat64 for headless batch mode if available
    idat_executable = ida_executable.replace("ida64.exe", "idat64.exe").replace("ida.exe", "idat.exe")
    if not Path(idat_executable).exists():
        idat_executable = ida_executable

    # Write a bounded IDAPython script inline
    script_content = _generate_ida_script()
    script_path = output_path.with_suffix(".ida_script.py")
    script_path.write_text(script_content, encoding="utf-8")

    log_path = output_path.with_suffix(".log")
    db_path = output_path.with_suffix(".i64")

    # Clean up sidecars before run
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar = db_path.with_suffix(suffix)
        try:
            sidecar.unlink(missing_ok=True)
        except OSError:
            pass

    command_args = [
        idat_executable,
        "-A",
        f"-L{log_path}",
        f"-o{db_path}",
        f"-S{script_path}",
        str(binary_path),
    ]

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(output_path)

    try:
        proc = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        result["error"] = f"IDA timeout (>{timeout_seconds}s)"
        result["blocked_reason"] = "IDA_TIMEOUT"
        return result
    except Exception as exc:
        result["error"] = f"IDA execution failed: {exc}"
        result["blocked_reason"] = "IDA_EXECUTION_ERROR"
        return result

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        if not details and log_path.exists():
            details = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        result["error"] = details[:2000] if details else f"IDA failed (exit code {proc.returncode})"
        result["blocked_reason"] = "IDA_FAILED"
        return result

    if not output_path.exists():
        result["error"] = "IDA completed but no output file"
        result["blocked_reason"] = "IDA_NO_OUTPUT"
        return result

    # Parse output
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["error"] = f"Failed to parse IDA output: {exc}"
        result["blocked_reason"] = "IDA_OUTPUT_PARSE_FAILED"
        return result

    result["ida_success"] = True
    result["ida_output"] = data

    # Clean up sidecars after successful run
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar = db_path.with_suffix(suffix)
        try:
            sidecar.unlink(missing_ok=True)
        except OSError:
            pass
    # Clean up log
    try:
        log_path.unlink(missing_ok=True)
    except OSError:
        pass

    return result


def _generate_ida_script() -> str:
    """Generate a bounded IDAPython script for control-flow extraction."""
    return '''
import json
import ida_auto
import ida_funcs
import ida_idaapi
import ida_name
import ida_search
import ida_segment
import ida_xref
import idautils
import idc

# Wait for auto-analysis
ida_auto.auto_wait()

import os
output_path = os.environ.get("REVERSE_AGENT_IDA_OUT", "")

result = {
    "main_function": "",
    "main_function_address": "",
    "basic_blocks": [],
    "division_instructions": [],
    "transform_loop_evidence": [],
    "compare_loop_evidence": [],
    "target_xref_evidence": [],
    "seh_evidence": [],
    "success_branch_evidence": [],
    "failure_branch_evidence": [],
    "decompiler_snippets": [],
}

# Find main function
main_ea = idc.get_name_ea_simple("_main_0")
if main_ea == idc.BADADDR:
    main_ea = idc.get_name_ea_simple("main")
if main_ea == idc.BADADDR:
    # Search for main by pattern
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if "main" in func_name.lower():
            main_ea = func_ea
            break

if main_ea != idc.BADADDR:
    result["main_function"] = idc.get_func_name(main_ea)
    result["main_function_address"] = f"0x{main_ea:08X}"

    # Get basic blocks
    func = ida_funcs.get_func(main_ea)
    if func:
        for block in idautils.Chunks(main_ea):
            start, end = block
            result["basic_blocks"].append({
                "start": f"0x{start:08X}",
                "end": f"0x{end:08X}",
                "size": end - start,
            })

# Search for division instructions (idiv, div)
for seg_ea in idautils.Segments():
    for head in idautils.Heads(seg_ea, ida_segment.getseg(seg_ea).end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            if mnem in ("idiv", "div"):
                op0 = idc.print_operand(head, 0)
                result["division_instructions"].append({
                    "address": f"0x{head:08X}",
                    "mnemonic": mnem,
                    "operand": op0,
                    "disasm": idc.generate_disasm_line(head, 0),
                })

# Search for transform pattern: and, shl, shr with specific constants
for seg_ea in idautils.Segments():
    for head in idautils.Heads(seg_ea, ida_segment.getseg(seg_ea).end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            if mnem == "and":
                op1 = idc.get_operand_value(head, 1)
                if op1 in (3, 0x0C, 0xF0):
                    result["transform_loop_evidence"].append({
                        "address": f"0x{head:08X}",
                        "disasm": idc.generate_disasm_line(head, 0),
                    })
            elif mnem in ("shl", "shr"):
                op1 = idc.get_operand_value(head, 1)
                if op1 in (2, 4):
                    result["transform_loop_evidence"].append({
                        "address": f"0x{head:08X}",
                        "disasm": idc.generate_disasm_line(head, 0),
                    })

# Search for compare loop: cmp, jz/jnz near target references
for seg_ea in idautils.Segments():
    for head in idautils.Heads(seg_ea, ida_segment.getseg(seg_ea).end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            if mnem == "cmp":
                result["compare_loop_evidence"].append({
                    "address": f"0x{head:08X}",
                    "disasm": idc.generate_disasm_line(head, 0),
                })

# Find byte_429A30 xrefs
target_name = "byte_429A30"
target_ea = idc.get_name_ea_simple(target_name)
if target_ea == idc.BADADDR:
    # Try to find by address
    target_ea = 0x00429A30

if target_ea != idc.BADADDR:
    xrefs = []
    for xref in idautils.XrefsTo(target_ea):
        xrefs.append({
            "from": f"0x{xref.frm:08X}",
            "type": "code" if xref.iscode else "data",
        })
    result["target_xref_evidence"] = {
        "target_name": target_name,
        "target_address": f"0x{target_ea:08X}",
        "xrefs": xrefs,
    }

# SEH/exception handling
for seg_ea in idautils.Segments():
    seg = ida_segment.getseg(seg_ea)
    if seg:
        seg_name = idc.get_segm_name(seg_ea)
        if seg_name and ("except" in seg_name.lower() or "seh" in seg_name.lower()):
            result["seh_evidence"].append({
                "segment": seg_name,
                "start": f"0x{seg.start_ea:08X}",
                "end": f"0x{seg.end_ea:08X}",
            })

# Search for success/failure strings
success_strings = ["Congratulations", "right", "correct", "success"]
failure_strings = ["Sorry", "wrong", "incorrect", "fail", "error"]

for s in idautils.Strings():
    str_val = str(s)
    lower = str_val.lower()
    if any(ss in lower for ss in success_strings):
        for xref in idautils.XrefsTo(s.ea):
            result["success_branch_evidence"].append({
                "string": str_val,
                "string_address": f"0x{s.ea:08X}",
                "xref_from": f"0x{xref.frm:08X}",
            })
    if any(fs in lower for fs in failure_strings):
        for xref in idautils.XrefsTo(s.ea):
            result["failure_branch_evidence"].append({
                "string": str_val,
                "string_address": f"0x{s.ea:08X}",
                "xref_from": f"0x{xref.frm:08X}",
            })

# Try decompiler for main function
if main_ea != idc.BADADDR:
    try:
        import ida_hexrays
        if ida_hexrays.init_hexrays_plugin():
            cfunc = ida_hexrays.decompile(main_ea)
            if cfunc:
                pseudocode = str(cfunc)
                result["decompiler_snippets"].append({
                    "function": result["main_function"],
                    "address": result["main_function_address"],
                    "text": pseudocode[:2000],
                })
    except Exception:
        pass

# Write output
if output_path:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

idc.qexit(0)
'''


def _analyze_control_flow(data: dict[str, Any], triage: dict[str, Any]) -> dict[str, Any]:
    """Analyze IDA output and compare with decompiler pseudocode from triage."""
    analysis: dict[str, Any] = {
        "main_function_found": bool(data.get("main_function")),
        "main_function": data.get("main_function", ""),
        "main_function_address": data.get("main_function_address", ""),
        "basic_block_count": len(data.get("basic_blocks", [])),
        "division_instruction_count": len(data.get("division_instructions", [])),
        "transform_loop_evidence_count": len(data.get("transform_loop_evidence", [])),
        "compare_loop_evidence_count": len(data.get("compare_loop_evidence", [])),
        "target_xref_count": len(data.get("target_xref_evidence", {}).get("xrefs", [])),
        "seh_segment_found": len(data.get("seh_evidence", [])) > 0,
        "success_branch_found": len(data.get("success_branch_evidence", [])) > 0,
        "failure_branch_found": len(data.get("failure_branch_evidence", [])) > 0,
        "decompiler_available": len(data.get("decompiler_snippets", [])) > 0,
    }

    # Compare with triage pseudocode
    triage_snippets = triage.get("triage", {}).get("decompiler_snippets", [])
    triage_text = triage_snippets[0].get("text", "") if triage_snippets else ""

    ida_snippets = data.get("decompiler_snippets", [])
    ida_text = ida_snippets[0].get("text", "") if ida_snippets else ""

    consistency: dict[str, Any] = {
        "triage_has_pseudocode": bool(triage_text),
        "ida_has_pseudocode": bool(ida_text),
        "both_have_pseudocode": bool(triage_text) and bool(ida_text),
    }

    # Check key patterns
    if triage_text:
        consistency["triage_has_strlen_check"] = "strlen(Str)" in triage_text or "v4 != 18" in triage_text
        consistency["triage_has_strncpy"] = "strncpy" in triage_text
        consistency["triage_has_transform_loop"] = "for ( i = 0; i < v4; ++i )" in triage_text
        consistency["triage_has_compare_loop"] = "Destination[i] == byte_429A30[i]" in triage_text
        consistency["triage_has_success_condition"] = "i == 16" in triage_text
        consistency["triage_has_division"] = "v6 = v9 / v8" in triage_text

    if ida_text:
        consistency["ida_has_strlen_check"] = "strlen" in ida_text
        consistency["ida_has_strncpy"] = "strncpy" in ida_text
        consistency["ida_has_transform_loop"] = "for" in ida_text and "i <" in ida_text
        consistency["ida_has_compare_loop"] = "==" in ida_text and "byte_429A30" in ida_text
        consistency["ida_has_success_condition"] = "16" in ida_text
        consistency["ida_has_division"] = "/" in ida_text

    # Division assessment
    div_instructions = data.get("division_instructions", [])
    if div_instructions:
        div_addrs = [d["address"] for d in div_instructions]
        consistency["division_instruction_addresses"] = div_addrs
        consistency["division_is_real_instruction"] = True
        # Check if division is in main function
        main_addr = data.get("main_function_address", "")
        if main_addr and div_addrs:
            main_start = int(main_addr, 16)
            # Simple check: is division address near main?
            div_near_main = any(
                abs(int(d, 16) - main_start) < 0x1000
                for d in div_addrs
            )
            consistency["division_near_main"] = div_near_main
    else:
        consistency["division_is_real_instruction"] = False
        consistency["division_assessment"] = "No division instruction found in binary; v6=v9/v8 may be dead code or decompiler artifact"

    # SEH assessment
    seh_evidence = data.get("seh_evidence", [])
    if seh_evidence:
        consistency["seh_present"] = True
        consistency["seh_assessment"] = "SEH/exception segments found; division by zero may be caught by exception handler"
    else:
        consistency["seh_present"] = False
        consistency["seh_assessment"] = "No SEH/exception segments found; division by zero would cause unhandled exception (likely dead code or anti-debug trap)"

    # Transform formula assessment
    transform_evidence = data.get("transform_loop_evidence", [])
    if transform_evidence:
        consistency["transform_instructions_found"] = True
        consistency["transform_formula_supported"] = True
        consistency["transform_assessment"] = "AND/shl/shr instructions with matching constants found; decompiler transform formula supported by instruction-level evidence"
    else:
        consistency["transform_instructions_found"] = False
        consistency["transform_formula_supported"] = False
        consistency["transform_assessment"] = "No matching AND/shl/shr instructions found; transform formula may be decompiler simplification or different encoding"

    analysis["decompiler_vs_instruction_consistency"] = consistency
    return analysis


def run_cpp1_ida_control_flow_recheck(
    artifact_index_path: Path,
    target_bytes_path: Path,
    transform_recheck_path: Path,
    triage_path: Path,
    out_path: Path,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Main logic: attempt bounded IDA extraction, analyze control flow."""
    artifact_index = _load_json(artifact_index_path)
    target_bytes = _load_json(target_bytes_path)
    transform_recheck = _load_json(transform_recheck_path)
    triage = _load_json(triage_path)

    sample_id = str(target_bytes.get("sample_id", ""))
    if not sample_id:
        raise ValueError("Target bytes artifact missing sample_id")

    # Validate freshness
    for artifact in (target_bytes, transform_recheck, triage):
        if artifact.get("runtime_validated") is not False:
            raise ValueError("Source artifact runtime_validated must be false")

    # Find binary
    binary_path = _find_binary_path(artifact_index, sample_id)

    # Attempt IDA extraction
    if binary_path and binary_path.exists():
        ida_result = _run_bounded_ida_control_flow(binary_path, out_path.with_suffix(".ida_raw.json"), timeout_seconds)
    else:
        ida_result = {
            "ida_attempted": False,
            "ida_available": False,
            "ida_success": False,
            "error": f"Binary not found for {sample_id}",
            "blocked_reason": "BINARY_NOT_FOUND",
        }

    # Build result
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "ida_instruction_control_flow_recheck",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "source_artifacts": {
            "artifact_index": str(artifact_index_path).replace("\\", "/"),
            "target_bytes": str(target_bytes_path).replace("\\", "/"),
            "transform_recheck": str(transform_recheck_path).replace("\\", "/"),
            "static_triage": str(triage_path).replace("\\", "/"),
        },
        "ida_status": {
            "attempted": ida_result["ida_attempted"],
            "available": ida_result["ida_available"],
            "success": ida_result["ida_success"],
            "error": ida_result.get("error", ""),
        },
    }

    if ida_result["ida_success"] and "ida_output" in ida_result:
        raw_output = ida_result["ida_output"]
        analysis = _analyze_control_flow(raw_output, triage)
        result["control_flow_analysis"] = analysis
        result["raw_ida_output_summary"] = {
            "basic_blocks": raw_output.get("basic_blocks", []),
            "division_instructions": raw_output.get("division_instructions", []),
            "transform_loop_evidence_count": len(raw_output.get("transform_loop_evidence", [])),
            "compare_loop_evidence_count": len(raw_output.get("compare_loop_evidence", [])),
            "target_xref_evidence": raw_output.get("target_xref_evidence", {}),
            "seh_evidence": raw_output.get("seh_evidence", []),
            "success_branch_evidence": raw_output.get("success_branch_evidence", [])[:4],
            "failure_branch_evidence": raw_output.get("failure_branch_evidence", [])[:4],
        }

        # Determine status based on findings
        consistency = analysis.get("decompiler_vs_instruction_consistency", {})

        if not consistency.get("transform_instructions_found"):
            status = "BLOCKED"
            blocked_reason = "TRANSFORM_INSTRUCTIONS_NOT_FOUND"
        elif not consistency.get("division_is_real_instruction"):
            status = "BLOCKED"
            blocked_reason = "DIVISION_INSTRUCTION_NOT_FOUND"
        else:
            status = "BLOCKED"
            blocked_reason = "NEEDS_STATIC_CONTROL_FLOW_RECHECK"

        result["status"] = status
        result["blocked_reason"] = blocked_reason
        result["control_flow_assessment"] = {
            "transform_formula_verdict": (
                "SUPPORTED" if consistency.get("transform_formula_supported")
                else "UNSUPPORTED"
            ),
            "division_verdict": (
                "REAL_INSTRUCTION_NEAR_MAIN" if consistency.get("division_near_main")
                else "NOT_FOUND_OR_NOT_NEAR_MAIN"
            ),
            "seh_verdict": (
                "PRESENT" if consistency.get("seh_present")
                else "NOT_PRESENT"
            ),
            "length_compare_semantics_verdict": (
                "SUPPORTED" if (
                    consistency.get("triage_has_strlen_check") and
                    consistency.get("triage_has_strncpy") and
                    consistency.get("triage_has_compare_loop") and
                    consistency.get("triage_has_success_condition")
                )
                else "PARTIALLY_SUPPORTED"
            ),
        }
    else:
        # IDA failed or unavailable
        result["status"] = "BLOCKED"
        result["blocked_reason"] = ida_result.get("blocked_reason", "IDA_UNAVAILABLE")
        result["control_flow_analysis"] = {}
        result["control_flow_assessment"] = {}

    result["candidate"] = None
    result["known_candidate"] = ""
    result["recommended_next_action"] = (
        "If IDA unavailable, require manual binary inspection or alternative static analysis. "
        "If transform instructions not found, decompiler formula may be incorrect; require instruction-level verification. "
        "If division not found, v6=v9/v8 is likely dead code or anti-debug trap. "
        "Next step: bounded runtime validation only if instruction-level evidence supports transform formula."
    )

    _save_json(out_path, result)

    print(f"cpp1 IDA control flow recheck: status={result['status']} sample_id={sample_id}")
    print(f"  ida_attempted={result['ida_status']['attempted']}")
    print(f"  ida_available={result['ida_status']['available']}")
    print(f"  ida_success={result['ida_status']['success']}")
    print(f"  blocked_reason={result['blocked_reason']}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded IDA static control-flow recheck for cpp1_2f6fcb63.",
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
        help="Path to artifact_index.json",
    )
    parser.add_argument(
        "--target-bytes",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json"),
        help="Path to target-bytes artifact",
    )
    parser.add_argument(
        "--transform-recheck",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json"),
        help="Path to transform-recheck artifact",
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
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json"),
        help="Output path for control-flow recheck JSON",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="IDA execution timeout in seconds (default: 180)",
    )
    args = parser.parse_args()

    try:
        run_cpp1_ida_control_flow_recheck(
            args.artifact_index,
            args.target_bytes,
            args.transform_recheck,
            args.triage,
            args.out,
            args.timeout,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
