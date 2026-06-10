"""
IDAPython script: xref_boundary_audit.py
Extract XREFs for byte_429A30, byte_429A31, byte_429A34, Str
and dump data window 0x429A20-0x429A60.
Also decompile sub_401090 and sub_4011E0 for full pseudocode.
"""
import json
import os
import traceback

try:
    import ida_auto
    import ida_funcs
    import ida_name
    import ida_pro
    import idautils
    import idc
except Exception as e:
    with open("F:\\reverse-agent\\xref_boundary_audit_error.txt", "w") as f:
        f.write("import_error: %s\n%s" % (str(e), traceback.format_exc()))
    import sys; sys.exit(1)

ida_auto.auto_wait()

TARGET_SYMBOLS = ["byte_429A30", "byte_429A31", "byte_429A34", "Str"]
DATA_WINDOW_START = 0x429A20
DATA_WINDOW_END = 0x429A60
FORCE_DECOMPILE = ["sub_401090", "sub_4011E0"]

try:
    IMAGE_BASE = ida_pro.get_inf_attr(ida_pro.INF_MIN_EA)
except Exception:
    IMAGE_BASE = 0x400000

def fmt_ea(ea):
    return "0x%X" % ea

def get_byte(ea):
    try:
        import ida_bytes
        return ida_bytes.get_byte(ea)
    except Exception:
        return idc.get_wide_byte(ea)

def get_xrefs(sym_name):
    ea = idc.get_name_ea_simple(sym_name)
    if ea == idc.BADADDR:
        return {"symbol": sym_name, "ea": None, "xrefs": [], "error": "symbol_not_found"}
    result = {"symbol": sym_name, "ea": fmt_ea(ea), "xrefs": []}
    try:
        for xref in idautils.XrefsTo(ea, 0):
            frm = int(xref.frm)
            frm_func = idc.get_func_attr(frm, idc.FUNCATTR_START)
            func_name = ida_funcs.get_func_name(frm_func) if frm_func != idc.BADADDR else ""
            disasm = idc.generate_disasm_line(frm, 0) or ""
            xref_type = xref.type
            type_name = ""
            try:
                type_name = idc.get_xref_type_name(xref_type) if xref_type else "unknown"
            except Exception:
                type_name = "type_%d" % int(xref_type)
            result["xrefs"].append({
                "from_ea": fmt_ea(frm),
                "from_func": func_name,
                "from_func_start": fmt_ea(frm_func) if frm_func != idc.BADADDR else None,
                "disasm": disasm,
                "xref_type": type_name,
                "xref_type_int": int(xref_type)
            })
    except Exception as e:
        result["error"] = str(e)
    return result

def dump_data_window(start, end):
    result = {"start_va": fmt_ea(start), "end_va": fmt_ea(end), "bytes_hex": "", "bytes_decimal": []}
    data = []
    for ea in range(start, end):
        b = get_byte(ea)
        data.append(b)
    result["bytes_hex"] = " ".join("%02X" % b for b in data)
    result["bytes_decimal"] = data
    return result

def decompile_func(func_name):
    ea = idc.get_name_ea_simple(func_name)
    if ea == idc.BADADDR:
        return {"function": func_name, "error": "not_found"}
    func = ida_funcs.get_func(ea)
    if not func:
        return {"function": func_name, "error": "no_function_at_ea"}
    try:
        import ida_hexrays
        if not ida_hexrays.init_hexrays_plugin():
            return {"function": func_name, "error": "hexrays_unavailable"}
        cfunc = ida_hexrays.decompile(func.start_ea)
        text = str(cfunc)
        return {"function": func_name, "entry_ea": fmt_ea(int(func.start_ea)), "pseudocode": text}
    except Exception as e:
        return {"function": func_name, "error": str(e)}

def get_nearby_symbol_xrefs():
    results = []
    for offset in range(0, 20):
        ea = 0x429A34 + offset
        name = ""
        try:
            name = ida_name.get_name(ea) or ""
        except Exception:
            pass
        xrefs = []
        try:
            for xref in idautils.XrefsTo(ea, 0):
                frm = int(xref.frm)
                frm_func = idc.get_func_attr(frm, idc.FUNCATTR_START)
                func_name = ida_funcs.get_func_name(frm_func) if frm_func != idc.BADADDR else ""
                disasm = idc.generate_disasm_line(frm, 0) or ""
                xrefs.append({
                    "from_ea": fmt_ea(frm),
                    "from_func": func_name,
                    "disasm": disasm
                })
        except Exception:
            pass
        if xrefs:
            results.append({"ea": fmt_ea(ea), "name": name, "xrefs": xrefs})
    return results

# Build output
output = {
    "image_base": fmt_ea(IMAGE_BASE),
    "target_symbol_xrefs": [],
    "data_window": None,
    "decompiled_functions": [],
    "nearby_byte_429A34_xrefs": []
}

for sym in TARGET_SYMBOLS:
    output["target_symbol_xrefs"].append(get_xrefs(sym))

output["data_window"] = dump_data_window(DATA_WINDOW_START, DATA_WINDOW_END)

for fn in FORCE_DECOMPILE:
    output["decompiled_functions"].append(decompile_func(fn))

output["nearby_byte_429A34_xrefs"] = get_nearby_symbol_xrefs()

# Segment info
try:
    seg_start = idc.get_segm_start(DATA_WINDOW_START)
    seg_end = idc.get_segm_end(DATA_WINDOW_START)
    seg_name = idc.get_segm_name(DATA_WINDOW_START)
    if seg_start != idc.BADADDR:
        output["data_segment_info"] = {
            "start_va": fmt_ea(seg_start),
            "end_va": fmt_ea(seg_end),
            "name": seg_name
        }
except Exception:
    pass

out_path = "F:\\reverse-agent\\xref_boundary_audit.json"
try:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
except Exception as e:
    with open("F:\\reverse-agent\\xref_boundary_audit_error.txt", "w") as f:
        f.write("write_error: %s\n%s" % (str(e), traceback.format_exc()))

idc.qexit(0)
