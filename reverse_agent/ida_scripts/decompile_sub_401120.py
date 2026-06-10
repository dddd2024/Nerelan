"""IDAPython: decompile sub_401120 only"""
import json, os, traceback

try:
    import ida_auto, ida_funcs, ida_name, ida_pro, idautils, idc
except Exception as e:
    with open("F:\\reverse-agent\\sub_401120_decompile_error.txt", "w") as f:
        f.write("import_error: %s\n%s" % (str(e), traceback.format_exc()))
    import sys; sys.exit(1)

ida_auto.auto_wait()

output = {}
for fn_name in ["sub_401120", "sub_401005", "sub_40100A", "_main_0"]:
    ea = idc.get_name_ea_simple(fn_name)
    if ea == idc.BADADDR:
        output[fn_name] = {"error": "not_found"}
        continue
    func = ida_funcs.get_func(ea)
    if not func:
        output[fn_name] = {"error": "no_function"}
        continue
    # Get disassembly of the full function
    instrs = []
    cur = func.start_ea
    while cur < func.end_ea:
        disasm = idc.generate_disasm_line(cur, 0) or ""
        instrs.append({"ea": "0x%X" % cur, "disasm": disasm})
        cur = idc.next_head(cur, func.end_ea)
    output[fn_name] = {
        "entry_ea": "0x%X" % func.start_ea,
        "end_ea": "0x%X" % func.end_ea,
        "instructions": instrs
    }
    # Try decompile
    try:
        import ida_hexrays
        if ida_hexrays.init_hexrays_plugin():
            cfunc = ida_hexrays.decompile(func.start_ea)
            output[fn_name]["pseudocode"] = str(cfunc)
    except Exception as e:
        output[fn_name]["decompile_error"] = str(e)

with open("F:\\reverse-agent\\sub_401120_analysis.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

idc.qexit(0)
