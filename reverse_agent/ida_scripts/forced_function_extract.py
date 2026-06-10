"""IDAPython script for forced decompilation of specific functions.

Usage from IDA command line:
    idat64.exe -A -S"forced_function_extract.py --out=output.json --functions=sub_401005,sub_40100A" binary.exe

Or with environment variable:
    REVERSE_AGENT_IDA_OUT=output.json
    REVERSE_AGENT_FORCED_FUNCTIONS=sub_401005,sub_40100A
"""

import json
import os
import sys

import ida_auto
import ida_funcs
import ida_hexrays
import ida_name
import ida_pro
import idautils
import idc


def _parse_out_path() -> str:
    env_path = os.environ.get("REVERSE_AGENT_IDA_OUT", "").strip()
    if env_path:
        return env_path
    for arg in idc.ARGV[1:]:
        if arg.startswith("--out="):
            return arg.split("=", 1)[1]
    return os.path.join(os.getcwd(), "forced_extract.json")


def _parse_function_names() -> list[str]:
    env_funcs = os.environ.get("REVERSE_AGENT_FORCED_FUNCTIONS", "").strip()
    if env_funcs:
        return [f.strip() for f in env_funcs.split(",") if f.strip()]
    for arg in idc.ARGV[1:]:
        if arg.startswith("--functions="):
            return [f.strip() for f in arg.split("=", 1)[1].split(",") if f.strip()]
    return []


def _get_function_ea_by_name(name: str) -> int:
    """Resolve function name to effective address."""
    ea = idc.get_name_ea_simple(name)
    if ea != ida_idaapi.BADADDR:
        return ea
    # Try with sub_ prefix stripped
    if name.startswith("sub_"):
        try:
            addr = int(name[4:], 16)
            if ida_funcs.get_func(addr):
                return addr
        except ValueError:
            pass
    return ida_idaapi.BADADDR


def _decompile_function(ea: int, max_lines: int = 200) -> str:
    """Decompile a function using Hex-Rays."""
    if not ida_hexrays.init_hexrays_plugin():
        return ""
    try:
        cfunc = ida_hexrays.decompile(ea)
        if cfunc is None:
            return ""
        lines = str(cfunc).split("\n")
        return "\n".join(lines[:max_lines])
    except Exception:
        return ""


def _get_disasm(ea: int, max_insn: int = 100) -> list[str]:
    """Get disassembly for a function."""
    func = ida_funcs.get_func(ea)
    if func is None:
        return []
    insns = []
    for head in idautils.FuncItems(ea):
        insns.append(idc.generate_disasm_line(head, 0))
        if len(insns) >= max_insn:
            break
    return insns


def _get_function_constants(ea: int) -> list[int]:
    """Extract immediate constants from a function."""
    func = ida_funcs.get_func(ea)
    if func is None:
        return []
    constants = []
    for head in idautils.FuncItems(ea):
        for op_idx in range(6):  # UA_MAXOP = 6
            op_type = idc.get_operand_type(head, op_idx)
            if op_type == idc.o_imm:
                val = idc.get_operand_value(head, op_idx)
                if 0 < val < 0xFFFFFFFF:
                    constants.append(val)
    # Deduplicate and limit
    seen = set()
    result = []
    for c in constants:
        if c not in seen:
            seen.add(c)
            result.append(c)
            if len(result) >= 50:
                break
    return result


def _get_callgraph(ea: int, depth: int = 2) -> list[dict]:
    """Extract call graph from a function."""
    func = ida_funcs.get_func(ea)
    if func is None:
        return []
    calls = []
    seen = set()
    for head in idautils.FuncItems(ea):
        for ref in idautils.CodeRefsFrom(head, 0):
            callee_name = idc.get_func_name(ref)
            if callee_name and callee_name not in seen:
                seen.add(callee_name)
                calls.append({
                    "caller_ea": hex(head),
                    "callee_ea": hex(ref),
                    "callee_name": callee_name,
                })
                if len(calls) >= 20:
                    break
        if len(calls) >= 20:
            break
    return calls


def _get_string_refs(ea: int) -> list[dict]:
    """Extract string references from a function."""
    func = ida_funcs.get_func(ea)
    if func is None:
        return []
    refs = []
    seen = set()
    for head in idautils.FuncItems(ea):
        for ref in idautils.DataRefsFrom(head):
            s = idc.get_strlit_contents(ref)
            if s and isinstance(s, bytes):
                try:
                    s = s.decode("utf-8", errors="replace")
                except Exception:
                    continue
            if s and s not in seen and len(s) >= 2:
                seen.add(s)
                refs.append({
                    "ea": hex(ref),
                    "string": s,
                    "ref_ea": hex(head),
                })
                if len(refs) >= 20:
                    break
        if len(refs) >= 20:
            break
    return refs


def main() -> None:
    out_path = _parse_out_path()
    function_names = _parse_function_names()

    if not function_names:
        print("ERROR: no function names specified", file=sys.stderr)
        ida_pro.qexit(1)
        return

    # Wait for auto-analysis
    ida_auto.auto_wait()

    hexrays_available = ida_hexrays.init_hexrays_plugin()

    extracted: list[dict] = []
    for name in function_names:
        ea = _get_function_ea_by_name(name)
        if ea == ida_idaapi.BADADDR:
            extracted.append({
                "function_name": name,
                "resolved": False,
                "entry_ea": "",
                "pseudocode": "",
                "disassembly": [],
                "constants": [],
                "callgraph": [],
                "string_refs": [],
                "error": "function not found",
            })
            continue

        pseudocode = _decompile_function(ea) if hexrays_available else ""
        disasm = _get_disasm(ea)
        constants = _get_function_constants(ea)
        callgraph = _get_callgraph(ea)
        string_refs = _get_string_refs(ea)

        extracted.append({
            "function_name": name,
            "resolved": True,
            "entry_ea": hex(ea),
            "pseudocode": pseudocode,
            "disassembly": disasm,
            "constants": constants,
            "callgraph": callgraph,
            "string_refs": string_refs,
            "error": "",
        })

    result = {
        "schema_version": 1,
        "hexrays_available": hexrays_available,
        "function_count": len(function_names),
        "extracted_count": sum(1 for e in extracted if e["resolved"]),
        "functions": extracted,
    }

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(f"forced_function_extract: {result['extracted_count']}/{result['function_count']} functions extracted -> {out_path}")
    ida_pro.qexit(0)


if __name__ == "__main__":
    main()
