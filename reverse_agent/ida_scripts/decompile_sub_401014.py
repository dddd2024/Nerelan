"""IDAPython: decompile sub_401014 and get byte_42CCAC + 0x40004E data"""
import json, os, traceback

try:
    import ida_auto, ida_funcs, ida_name, ida_pro, idautils, idc
except Exception as e:
    with open("F:\\reverse-agent\\sub_401014_error.txt", "w") as f:
        f.write("import_error: %s\n%s" % (str(e), traceback.format_exc()))
    import sys; sys.exit(1)

ida_auto.auto_wait()

output = {}

# Decompile sub_401014
fn_name = "sub_401014"
ea = idc.get_name_ea_simple(fn_name)
if ea != idc.BADADDR:
    func = ida_funcs.get_func(ea)
    if func:
        instrs = []
        cur = func.start_ea
        while cur < func.end_ea:
            disasm = idc.generate_disasm_line(cur, 0) or ""
            instrs.append({"ea": "0x%X" % cur, "disasm": disasm})
            cur = idc.next_head(cur, func.end_ea)
        output["sub_401014"] = {"entry_ea": "0x%X" % func.start_ea, "instructions": instrs}
        try:
            import ida_hexrays
            if ida_hexrays.init_hexrays_plugin():
                cfunc = ida_hexrays.decompile(func.start_ea)
                output["sub_401014"]["pseudocode"] = str(cfunc)
        except Exception as e:
            output["sub_401014"]["decompile_error"] = str(e)
    else:
        output["sub_401014"] = {"error": "no_function"}
else:
    output["sub_401014"] = {"error": "not_found"}

# Dump byte_42CCAC (172 bytes = 43 * 4)
def get_byte(ea):
    try:
        import ida_bytes
        return ida_bytes.get_byte(ea)
    except Exception:
        return idc.get_wide_byte(ea)

key_init_data = []
for i in range(172):
    key_init_data.append(get_byte(0x42CCAC + i))
output["byte_42CCAC"] = {
    "va": "0x42CCAC",
    "length": 172,
    "bytes_hex": " ".join("%02X" % b for b in key_init_data),
    "bytes_decimal": key_init_data
}

# Dump 0x40004E (source of memcpy in sub_401120)
source_data = []
for i in range(43):
    source_data.append(get_byte(0x40004E + i))
output["source_0x40004E"] = {
    "va": "0x40004E",
    "length": 43,
    "bytes_hex": " ".join("%02X" % b for b in source_data),
    "bytes_decimal": source_data
}

with open("F:\\reverse-agent\\sub_401014_key_init_analysis.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

idc.qexit(0)
