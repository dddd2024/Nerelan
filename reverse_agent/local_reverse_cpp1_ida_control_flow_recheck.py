"""Bounded IDA static control-flow precision recheck for cpp1_2f6fcb63.

This round is static-only. It does not execute the sample, does not perform
runtime validation, and never writes a candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.tool_runners import _resolve_ida_executable


ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck"
ARTIFACT_KIND = "local_reverse_cpp1_ida_control_flow_recheck"
SOURCE_RUN = "round_20260605_cpp1_ida_control_flow_recheck_precision_fix_v1"


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
) -> None:
    artifact_index = _load_json(artifact_index_path)
    v2 = artifact_index.setdefault("latest_artifacts_v2", {})
    v2[ARTIFACT_KEY] = {
        "kind": ARTIFACT_KIND,
        "path": str(out_path).replace("/", "\\"),
        "freshness": "current",
        "source_run": SOURCE_RUN,
        "sha256": _sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "modified_at": generated_at,
        "sample_id": sample_id,
    }
    latest = artifact_index.setdefault("latest_artifacts", {})
    latest[ARTIFACT_KEY] = str(out_path).replace("/", "\\")
    artifact_refs = artifact_index.setdefault("artifact_refs", {})
    artifact_refs[ARTIFACT_KEY] = str(out_path).replace("/", "\\")
    artifact_index["generated_at"] = generated_at
    _save_json(artifact_index_path, artifact_index)


def _find_binary_path(artifact_index: dict[str, Any], sample_id: str) -> Path | None:
    v2 = artifact_index.get("latest_artifacts_v2", {})
    triage_key = f"local_reverse_{sample_id}_static_triage"
    triage_meta = v2.get(triage_key, {})
    triage_path = triage_meta.get("path", "")
    if triage_path:
        triage_dir = Path(triage_path).parent
        for pattern in ("*.exe", "../*.exe", "../../*.exe"):
            for candidate in triage_dir.glob(pattern):
                if candidate.name.lower() == "cpp1.exe" or sample_id.lower() in candidate.stem.lower():
                    return candidate

    fallback = Path("E:\\reverse\\逆向课程2023春01\\CPP1.exe")
    if fallback.exists():
        return fallback
    return None


def _run_bounded_ida_control_flow(
    binary_path: Path,
    output_path: Path,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
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
    idat_executable = ida_executable.replace("ida64.exe", "idat64.exe").replace("ida.exe", "idat.exe")
    if not Path(idat_executable).exists():
        idat_executable = ida_executable

    script_path = output_path.with_suffix(".ida_script.py")
    log_path = output_path.with_suffix(".log")
    db_path = output_path.with_suffix(".i64")
    script_path.write_text(_generate_ida_script(), encoding="utf-8")

    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        try:
            db_path.with_suffix(suffix).unlink(missing_ok=True)
        except OSError:
            pass

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(output_path)
    command_args = [
        idat_executable,
        "-A",
        f"-L{log_path}",
        f"-o{db_path}",
        f"-S{script_path}",
        str(binary_path),
    ]

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
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except OSError:
            pass

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

    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["error"] = f"Failed to parse IDA output: {exc}"
        result["blocked_reason"] = "IDA_OUTPUT_PARSE_FAILED"
        return result

    result["ida_success"] = True
    result["ida_output"] = data

    for suffix in (".i64", ".id0", ".id1", ".nam", ".til", ".log"):
        try:
            db_path.with_suffix(suffix).unlink(missing_ok=True)
        except OSError:
            pass
    return result


def _generate_ida_script() -> str:
    return r'''
import json
import os

import ida_auto
import ida_funcs
import ida_gdl
import ida_segment
import ida_xref
import idautils
import idc

ida_auto.auto_wait()
output_path = os.environ.get("REVERSE_AGENT_IDA_OUT", "")
BAD = idc.BADADDR

TARGET_NAME = "byte_429A30"
TARGET_EA_FALLBACK = 0x00429A30
BRANCH_MNEMS = {
    "ja", "jae", "jb", "jbe", "jc", "je", "jg", "jge", "jl", "jle", "jna",
    "jnae", "jnb", "jnbe", "jnc", "jne", "jng", "jnge", "jnl", "jnle",
    "jno", "jnp", "jns", "jnz", "jo", "jp", "jpe", "jpo", "js", "jz",
}


def hx(ea):
    return f"0x{ea:08X}" if ea != BAD and ea is not None else ""


def insn(ea, block_id=None):
    return {
        "address": hx(ea),
        "mnemonic": idc.print_insn_mnem(ea),
        "operands": [idc.print_operand(ea, i) for i in range(3) if idc.print_operand(ea, i)],
        "disasm": idc.generate_disasm_line(ea, 0) or "",
        "basic_block": block_id,
    }


def bounded_heads(blocks):
    for block in blocks:
        for ea in idautils.Heads(block["start_ea"], block["end_ea"]):
            if idc.is_code(idc.get_full_flags(ea)):
                yield ea, block["id"]


def window_around(ea, block_id, blocks, radius=5):
    for block in blocks:
        if block["start_ea"] <= ea < block["end_ea"]:
            heads = [
                h for h in idautils.Heads(block["start_ea"], block["end_ea"])
                if idc.is_code(idc.get_full_flags(h))
            ]
            if ea in heads:
                index = heads.index(ea)
            else:
                index = 0
                for i, h in enumerate(heads):
                    if h >= ea:
                        index = i
                        break
            selected = heads[max(0, index - radius): index + radius + 1]
            return [insn(h, block_id) for h in selected]
    return []


def find_main():
    for name in ("_main_0", "main"):
        ea = idc.get_name_ea_simple(name)
        if ea != BAD:
            return ea
    for func_ea in idautils.Functions():
        if "main" in idc.get_func_name(func_ea).lower():
            return func_ea
    return BAD


result = {
    "main_function": "",
    "main_function_address": "",
    "basic_blocks": [],
    "division_instructions_in_main": [],
    "transform_candidate_windows_in_main": [],
    "compare_candidate_windows_in_main": [],
    "target_xref_context": {},
    "seh_static_scan": {
        "handler_symbols": [],
        "segments_scanned": [],
        "assessment": "SEH_NOT_CONFIRMED_BY_STATIC_SCAN",
    },
    "success_failure_branch_evidence": [],
    "decompiler_snippets": [],
}

main_ea = find_main()
main_func = ida_funcs.get_func(main_ea) if main_ea != BAD else None
blocks = []
if main_func:
    result["main_function"] = idc.get_func_name(main_ea)
    result["main_function_address"] = hx(main_ea)
    for idx, block in enumerate(ida_gdl.FlowChart(main_func)):
        block_record = {
            "id": idx,
            "start": hx(block.start_ea),
            "end": hx(block.end_ea),
            "start_ea": block.start_ea,
            "end_ea": block.end_ea,
            "size": block.end_ea - block.start_ea,
            "successors": [],
        }
        for succ in block.succs():
            block_record["successors"].append(hx(succ.start_ea))
        blocks.append(block_record)
    result["basic_blocks"] = [
        {k: v for k, v in block.items() if k not in ("start_ea", "end_ea")}
        for block in blocks
    ]

target_ea = idc.get_name_ea_simple(TARGET_NAME)
if target_ea == BAD:
    target_ea = TARGET_EA_FALLBACK

target_xrefs = []
if target_ea != BAD:
    for xref in idautils.XrefsTo(target_ea):
        block_id = None
        in_main = False
        for block in blocks:
            if block["start_ea"] <= xref.frm < block["end_ea"]:
                block_id = block["id"]
                in_main = True
                break
        xref_record = {
            "from": hx(xref.frm),
            "type": "code" if xref.iscode else "data",
            "in_main": in_main,
            "basic_block": block_id,
            "window": window_around(xref.frm, block_id, blocks),
        }
        target_xrefs.append(xref_record)
result["target_xref_context"] = {
    "target_name": TARGET_NAME,
    "target_address": hx(target_ea),
    "xrefs": target_xrefs,
}

for ea, block_id in bounded_heads(blocks):
    mnem = idc.print_insn_mnem(ea).lower()
    if mnem in ("idiv", "div"):
        result["division_instructions_in_main"].append(insn(ea, block_id))
    if mnem in ("and", "shl", "shr", "or"):
        op1 = idc.get_operand_value(ea, 1)
        if mnem == "or" or op1 in (2, 3, 4, 0x0C, 0xF0):
            result["transform_candidate_windows_in_main"].append({
                "anchor": insn(ea, block_id),
                "window": window_around(ea, block_id, blocks),
            })
    if mnem in {"cmp", *BRANCH_MNEMS}:
        result["compare_candidate_windows_in_main"].append({
            "anchor": insn(ea, block_id),
            "window": window_around(ea, block_id, blocks),
            "target_xref_related": any(
                item.get("in_main") and item.get("basic_block") == block_id
                for item in target_xrefs
            ),
        })

for seg_ea in idautils.Segments():
    seg = ida_segment.getseg(seg_ea)
    if not seg:
        continue
    seg_name = idc.get_segm_name(seg_ea) or ""
    result["seh_static_scan"]["segments_scanned"].append(seg_name)
    if "seh" in seg_name.lower() or "except" in seg_name.lower():
        result["seh_static_scan"]["handler_symbols"].append({
            "kind": "segment_name_hint",
            "name": seg_name,
            "address": hx(seg.start_ea),
        })

for func_ea in idautils.Functions():
    name = idc.get_func_name(func_ea)
    if name and "except_handler" in name.lower():
        result["seh_static_scan"]["handler_symbols"].append({
            "kind": "symbol_name_hint",
            "name": name,
            "address": hx(func_ea),
        })

strings = list(idautils.Strings())
interesting = [
    ("success", ("congratulations", "right")),
    ("failure", ("sorry", "wrong", "pity")),
]
for string_obj in strings:
    text = str(string_obj)
    lower = text.lower()
    role = ""
    for candidate_role, needles in interesting:
        if any(needle in lower for needle in needles):
            role = candidate_role
            break
    if not role:
        continue
    for xref in idautils.XrefsTo(string_obj.ea):
        block_id = None
        for block in blocks:
            if block["start_ea"] <= xref.frm < block["end_ea"]:
                block_id = block["id"]
                break
        local_window = window_around(xref.frm, block_id, blocks)
        branch_insns = [item for item in local_window if item["mnemonic"].lower() in BRANCH_MNEMS]
        result["success_failure_branch_evidence"].append({
            "role": role,
            "string": text,
            "string_address": hx(string_obj.ea),
            "xref_from": hx(xref.frm),
            "xref_in_main": block_id is not None,
            "basic_block": block_id,
            "related_branch_instruction": branch_insns[-1] if branch_insns else None,
            "association": "ASSOCIATED_WITH_LOCAL_JCC" if branch_insns else "INSUFFICIENT",
            "window": local_window,
        })

if main_ea != BAD:
    try:
        import ida_hexrays
        if ida_hexrays.init_hexrays_plugin():
            cfunc = ida_hexrays.decompile(main_ea)
            if cfunc:
                result["decompiler_snippets"].append({
                    "function": result["main_function"],
                    "address": result["main_function_address"],
                    "text": str(cfunc)[:2000],
                })
    except Exception:
        pass

if output_path:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

idc.qexit(0)
'''


def _triage_text(triage: dict[str, Any]) -> str:
    snippets = triage.get("triage", {}).get("decompiler_snippets", [])
    return snippets[0].get("text", "") if snippets else ""


def _has_complete_transform_sequence(windows: list[dict[str, Any]]) -> bool:
    mnems: set[str] = set()
    constants: set[int] = set()
    for item in windows:
        for insn_item in [item.get("anchor", {}), *item.get("window", [])]:
            mnemonic = str(insn_item.get("mnemonic", "")).lower()
            mnems.add(mnemonic)
            for operand in insn_item.get("operands", []):
                text = str(operand).lower().replace("h", "")
                for value, labels in {
                    3: ("3", "03"),
                    0x0C: ("0c", "12"),
                    0xF0: ("0f0", "f0", "240"),
                    2: ("2",),
                    4: ("4",),
                }.items():
                    if text in labels or any(label in text for label in labels):
                        constants.add(value)
    return {"and", "shl", "shr"}.issubset(mnems) and {3, 0x0C, 0xF0, 2, 4}.issubset(constants)


def _analyze_control_flow(data: dict[str, Any], triage: dict[str, Any]) -> dict[str, Any]:
    basic_blocks = data.get("basic_blocks", [])
    divisions = data.get("division_instructions_in_main", data.get("division_instructions", []))
    transform_windows = data.get("transform_candidate_windows_in_main", [])
    compare_windows = data.get("compare_candidate_windows_in_main", [])
    target_xrefs = data.get("target_xref_context", {}).get("xrefs", [])
    branch_evidence = data.get("success_failure_branch_evidence", [])
    seh_scan = data.get("seh_static_scan", {})
    triage_text = _triage_text(triage)
    ida_snippets = data.get("decompiler_snippets", [])
    ida_text = ida_snippets[0].get("text", "") if ida_snippets else ""

    in_main_target_xrefs = [item for item in target_xrefs if item.get("in_main")]
    branch_associations = [item for item in branch_evidence if item.get("association") == "ASSOCIATED_WITH_LOCAL_JCC"]
    transform_complete = _has_complete_transform_sequence(transform_windows)

    consistency: dict[str, Any] = {
        "triage_has_pseudocode": bool(triage_text),
        "ida_has_pseudocode": bool(ida_text),
        "both_have_pseudocode": bool(triage_text) and bool(ida_text),
        "triage_has_strlen_check": "strlen" in triage_text and ("18" in triage_text or "0x12" in triage_text),
        "triage_has_strncpy": "strncpy" in triage_text,
        "triage_has_transform_loop": "for" in triage_text and "0xF0" in triage_text,
        "triage_has_compare_loop": "byte_429A30" in triage_text,
        "triage_has_success_condition": "i == 16" in triage_text,
        "triage_has_division": "/" in triage_text,
        "ida_has_strlen_check": "strlen" in ida_text,
        "ida_has_strncpy": "strncpy" in ida_text,
        "ida_has_transform_loop": "for" in ida_text and "0xF0" in ida_text,
        "ida_has_compare_loop": "byte_429A30" in ida_text,
        "ida_has_success_condition": "16" in ida_text,
        "ida_has_division": "/" in ida_text,
        "division_is_bounded_to_main": bool(divisions),
        "transform_evidence_is_bounded_to_main": bool(transform_windows),
        "transform_sequence_complete": transform_complete,
        "compare_evidence_is_bounded_to_main": bool(compare_windows),
        "target_xref_in_main": bool(in_main_target_xrefs),
        "success_failure_branch_association_count": len(branch_associations),
        "seh_handler_symbols": seh_scan.get("handler_symbols", []),
        "seh_assessment": "SEH_NOT_CONFIRMED_BY_STATIC_SCAN",
    }

    return {
        "main_function_found": bool(data.get("main_function")),
        "main_function": data.get("main_function", ""),
        "main_function_address": data.get("main_function_address", ""),
        "basic_block_count": len(basic_blocks),
        "basic_block_source": "ida_gdl.FlowChart",
        "division_instruction_count": len(divisions),
        "transform_candidate_window_count": len(transform_windows),
        "compare_candidate_window_count": len(compare_windows),
        "target_xref_count": len(target_xrefs),
        "target_xref_in_main_count": len(in_main_target_xrefs),
        "seh_handler_hint_count": len(seh_scan.get("handler_symbols", [])),
        "success_failure_branch_evidence_count": len(branch_evidence),
        "success_failure_branch_association_count": len(branch_associations),
        "decompiler_available": bool(ida_text),
        "decompiler_vs_instruction_consistency": consistency,
    }


def _control_flow_assessment(analysis: dict[str, Any]) -> dict[str, str]:
    consistency = analysis.get("decompiler_vs_instruction_consistency", {})
    transform_supported = (
        consistency.get("transform_evidence_is_bounded_to_main")
        and consistency.get("transform_sequence_complete")
    )
    compare_supported = (
        consistency.get("compare_evidence_is_bounded_to_main")
        and consistency.get("target_xref_in_main")
        and analysis.get("success_failure_branch_association_count", 0) > 0
    )
    return {
        "transform_formula_verdict": "SUPPORTED" if transform_supported else "PARTIALLY_SUPPORTED",
        "division_verdict": "BOUNDED_MAIN_INSTRUCTION_FOUND"
        if consistency.get("division_is_bounded_to_main")
        else "INSUFFICIENT",
        "seh_verdict": consistency.get("seh_assessment", "SEH_NOT_CONFIRMED_BY_STATIC_SCAN"),
        "length_compare_semantics_verdict": "SUPPORTED" if compare_supported else "PARTIALLY_SUPPORTED",
    }


def run_cpp1_ida_control_flow_recheck(
    artifact_index_path: Path,
    target_bytes_path: Path,
    transform_recheck_path: Path,
    triage_path: Path,
    out_path: Path,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    artifact_index = _load_json(artifact_index_path)
    target_bytes = _load_json(target_bytes_path)
    transform_recheck = _load_json(transform_recheck_path)
    triage = _load_json(triage_path)

    sample_id = str(target_bytes.get("sample_id", ""))
    if not sample_id:
        raise ValueError("Target bytes artifact missing sample_id")
    for artifact in (target_bytes, transform_recheck, triage):
        if artifact.get("runtime_validated") is not False:
            raise ValueError("Source artifact runtime_validated must be false")

    binary_path = _find_binary_path(artifact_index, sample_id)
    if binary_path and binary_path.exists():
        with tempfile.TemporaryDirectory(prefix="cpp1_ida_recheck_") as tmpdir:
            raw_output_path = Path(tmpdir) / "ida_raw.json"
            ida_result = _run_bounded_ida_control_flow(binary_path, raw_output_path, timeout_seconds)
    else:
        ida_result = {
            "ida_attempted": False,
            "ida_available": False,
            "ida_success": False,
            "error": f"Binary not found for {sample_id}",
            "blocked_reason": "BINARY_NOT_FOUND",
        }

    generated_at = _now_iso()
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "ida_instruction_control_flow_precision_recheck",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": generated_at,
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
        "status": "BLOCKED",
        "blocked_reason": ida_result.get("blocked_reason", "NEEDS_STATIC_CONTROL_FLOW_RECHECK"),
        "candidate": None,
        "known_candidate": "",
    }

    if ida_result["ida_success"] and "ida_output" in ida_result:
        raw_output = ida_result["ida_output"]
        analysis = _analyze_control_flow(raw_output, triage)
        assessment = _control_flow_assessment(analysis)
        result.update(
            {
                "main_function": analysis.get("main_function", ""),
                "main_function_address": analysis.get("main_function_address", ""),
                "basic_blocks": raw_output.get("basic_blocks", []),
                "bounded_instruction_evidence": {
                    "division_instructions_in_main": raw_output.get("division_instructions_in_main", []),
                    "transform_candidate_windows_in_main": raw_output.get(
                        "transform_candidate_windows_in_main", []
                    ),
                    "compare_candidate_windows_in_main": raw_output.get("compare_candidate_windows_in_main", []),
                    "target_xref_context": raw_output.get("target_xref_context", {}),
                },
                "seh_assessment": raw_output.get("seh_static_scan", {}),
                "success_failure_branch_assessment": {
                    "evidence": raw_output.get("success_failure_branch_evidence", []),
                    "verdict": "ASSOCIATED_WITH_LOCAL_JCC"
                    if analysis.get("success_failure_branch_association_count", 0) > 0
                    else "INSUFFICIENT",
                },
                "decompiler_vs_instruction_consistency": analysis.get(
                    "decompiler_vs_instruction_consistency", {}
                ),
                "control_flow_analysis": analysis,
                "control_flow_assessment": assessment,
                "blocked_reason": "NEEDS_STATIC_CONTROL_FLOW_RECHECK",
            }
        )
    else:
        result.update(
            {
                "main_function": "",
                "main_function_address": "",
                "basic_blocks": [],
                "bounded_instruction_evidence": {
                    "division_instructions_in_main": [],
                    "transform_candidate_windows_in_main": [],
                    "compare_candidate_windows_in_main": [],
                    "target_xref_context": {},
                },
                "seh_assessment": {"assessment": "SEH_NOT_CONFIRMED_BY_STATIC_SCAN"},
                "success_failure_branch_assessment": {"evidence": [], "verdict": "INSUFFICIENT"},
                "decompiler_vs_instruction_consistency": {},
                "control_flow_analysis": {},
                "control_flow_assessment": {
                    "transform_formula_verdict": "INSUFFICIENT",
                    "division_verdict": "INSUFFICIENT",
                    "seh_verdict": "SEH_NOT_CONFIRMED_BY_STATIC_SCAN",
                    "length_compare_semantics_verdict": "INSUFFICIENT",
                },
            }
        )

    result["recommended_next_action"] = (
        "Keep cpp1_2f6fcb63 blocked/static-only. Use this bounded _main_0 evidence "
        "to decide a future separately-approved static refinement; do not mark solved "
        "or run runtime validation from this artifact."
    )

    _save_json(out_path, result)
    _update_artifact_index(artifact_index_path, out_path, sample_id, generated_at)

    print(f"cpp1 IDA control flow recheck: status={result['status']} sample_id={sample_id}")
    print(f"  ida_attempted={result['ida_status']['attempted']}")
    print(f"  ida_available={result['ida_status']['available']}")
    print(f"  ida_success={result['ida_status']['success']}")
    print(f"  main_function={result.get('main_function', '')}")
    print(f"  basic_blocks={len(result.get('basic_blocks', []))}")
    print(
        "  bounded_division="
        f"{len(result['bounded_instruction_evidence']['division_instructions_in_main'])}"
    )
    print(
        "  bounded_transform_windows="
        f"{len(result['bounded_instruction_evidence']['transform_candidate_windows_in_main'])}"
    )
    print(
        "  bounded_compare_windows="
        f"{len(result['bounded_instruction_evidence']['compare_candidate_windows_in_main'])}"
    )
    print(f"  seh_verdict={result['control_flow_assessment']['seh_verdict']}")
    print(f"  blocked_reason={result['blocked_reason']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded IDA static control-flow precision recheck for cpp1_2f6fcb63.",
    )
    parser.add_argument("--artifact-index", type=Path, default=Path("project_state/artifact_index.json"))
    parser.add_argument("--target-bytes", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json"))
    parser.add_argument("--transform-recheck", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json"))
    parser.add_argument("--triage", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_static_triage.json"))
    parser.add_argument("--out", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json"))
    parser.add_argument("--timeout", type=int, default=180)
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
