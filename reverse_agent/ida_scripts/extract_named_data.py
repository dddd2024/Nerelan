"""IDAPython script: extract named data bytes and targeted function pseudocode.

Runs inside IDA batch mode. Extracts:
1. Named data item (e.g., byte_429A30) bytes and length
2. Targeted function pseudocode (e.g., _main_0)
3. Compare context from the function

Output written to REVERSE_AGENT_NAMED_DATA_OUT env path.
"""

import ida_auto
import ida_name
import ida_bytes
import ida_funcs
import ida_hexrays
import idc
import json
import os


def get_output_path():
    env_path = os.environ.get("REVERSE_AGENT_NAMED_DATA_OUT", "").strip()
    if env_path:
        return env_path
    return os.path.join(os.getcwd(), "named_data_extract.json")


def extract_named_data(name: str) -> dict:
    """Extract bytes from a named data item.

    Honors REVERSE_AGENT_TARGET_LENGTH env var for explicit read length.
    Falls back to ida_bytes.get_item_size(ea) if env var not set.
    """
    result = {
        "name": name,
        "address": "",
        "length": 0,
        "bytes_hex": "",
        "bytes": [],
        "found": False,
    }
    ea = ida_name.get_name_ea(ida_idaapi.BADADDR, name)
    if ea == ida_idaapi.BADADDR:
        return result

    # Check for explicit target length from env
    env_len_str = os.environ.get("REVERSE_AGENT_TARGET_LENGTH", "").strip()
    if env_len_str:
        try:
            item_size = int(env_len_str)
            if item_size <= 0 or item_size > 256:
                item_size = 16
        except ValueError:
            item_size = ida_bytes.get_item_size(ea)
    else:
        item_size = ida_bytes.get_item_size(ea)

    if item_size <= 0:
        item_size = 16  # Default guess for byte arrays

    # Cap at 256 bytes for safety
    item_size = min(256, item_size)

    bytes_data = ida_bytes.get_bytes(ea, item_size) or b""
    if bytes_data:
        result["found"] = True
        result["address"] = f"0x{ea:08X}"
        result["length"] = len(bytes_data)
        result["bytes_hex"] = bytes_data.hex()
        result["bytes"] = list(bytes_data)

    return result


def extract_function_pseudocode(func_name: str) -> dict:
    """Extract decompiler pseudocode for a function."""
    result = {
        "name": func_name,
        "address": "",
        "pseudocode": "",
        "found": False,
    }
    ea = ida_name.get_name_ea(ida_idaapi.BADADDR, func_name)
    if ea == ida_idaapi.BADADDR:
        return result

    func = ida_funcs.get_func(ea)
    if not func:
        return result

    try:
        cfunc = ida_hexrays.decompile(func)
        if cfunc:
            result["found"] = True
            result["address"] = f"0x{ea:08X}"
            result["pseudocode"] = str(cfunc)
    except Exception:
        pass

    return result


def extract_compare_context(pseudocode: str, data_name: str) -> dict:
    """Extract compare loop context from pseudocode."""
    result = {
        "compare_expression": "",
        "loop_variable": "",
        "loop_bound": "",
        "notes": [],
    }
    lines = pseudocode.split("\n")
    for i, line in enumerate(lines):
        lower = line.lower()
        if data_name.lower() in lower and ("==" in line or "!=" in line):
            result["compare_expression"] = line.strip()
            # Look for surrounding loop context
            for j in range(max(0, i - 5), i):
                prev = lines[j].lower()
                if "for" in prev or "while" in prev:
                    result["loop_context"] = lines[j].strip()
                    break
            break

    return result


def main():
    ida_auto.auto_wait()

    out_path = get_output_path()

    # Read env vars for targets
    target_symbol = os.environ.get("REVERSE_AGENT_TARGET_SYMBOL", "byte_429A30")
    target_func = os.environ.get("REVERSE_AGENT_TARGET_FUNC", "_main_0")

    data_result = extract_named_data(target_symbol)
    func_result = extract_function_pseudocode(target_func)

    compare_ctx = {}
    if func_result["found"]:
        compare_ctx = extract_compare_context(func_result["pseudocode"], target_symbol)

    output = {
        "schema_version": 1,
        "target_symbol": target_symbol,
        "target_func": target_func,
        "named_data": data_result,
        "function": func_result,
        "compare_context": compare_ctx,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    idc.qexit(0)


if __name__ == "__main__":
    main()
