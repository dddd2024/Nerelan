import json
import os

import ida_auto
import ida_funcs
import ida_name
import ida_pro
import idautils
import idc

INTERESTING_KEYWORDS = [
    "flag",
    "key",
    "password",
    "correct",
    "wrong",
    "error",
    "success",
    "fail",
    "input",
    "check",
    "verify",
    "cmp",
    "strcmp",
    "memcmp",
    "debug",
    "decrypt",
    "encrypt",
    "xor",
    "md5",
    "sha",
]


def _parse_out_path() -> str:
    env_path = os.environ.get("REVERSE_AGENT_IDA_OUT", "").strip()
    if env_path:
        return env_path
    for arg in idc.ARGV[1:]:
        if arg.startswith("--out="):
            return arg.split("=", 1)[1]
    return os.path.join(os.getcwd(), "ida_evidence.json")


def _text_score(text: str) -> int:
    value = (text or "").lower()
    score = 0
    for kw in INTERESTING_KEYWORDS:
        if kw in value:
            score += 3
    if "{" in value or "}" in value:
        score += 3
    if any(ch.isdigit() for ch in value):
        score += 1
    if len(value) <= 64:
        score += 1
    return score


def _collect_strings(limit: int = 800) -> list[str]:
    values: list[tuple[int, str]] = []
    seen: set[str] = set()
    st = idautils.Strings()
    st.setup(minlen=4)
    for item in st:
        s = str(item)
        if s and s not in seen:
            seen.add(s)
            values.append((_text_score(s), s))
            if len(values) >= 20000:
                break

    values.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return [s for _, s in values[:limit]]


def _collect_functions(limit: int = 1000) -> list[str]:
    values: list[tuple[int, str]] = []
    seen: set[str] = set()
    for ea in idautils.Functions():
        name = ida_name.get_short_name(ea) or ida_funcs.get_func_name(ea)
        if not name or name in seen:
            continue
        seen.add(name)
        score = _text_score(name)
        if name.lower().startswith(("sub_", "nullsub_")):
            score -= 2
        values.append((score, name))
    values.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in values[:limit]]


def _format_ea(ea: int) -> str:
    return f"0x{ea:X}"


def _safe_disasm(ea: int) -> str:
    try:
        return idc.generate_disasm_line(ea, 0) or ""
    except Exception:
        return ""


def _safe_strlit(ea: int) -> str:
    for strtype in (idc.STRTYPE_C, idc.STRTYPE_C_16):
        try:
            raw = idc.get_strlit_contents(ea, -1, strtype)
        except Exception:
            raw = None
        if not raw:
            continue
        if isinstance(raw, bytes):
            enc = "utf-16-le" if strtype == idc.STRTYPE_C_16 else "utf-8"
            return raw.decode(enc, errors="ignore").strip()
        return str(raw).strip()
    return ""


def _nearby_before(ea: int, func_ea: int, limit: int = 5) -> list[str]:
    nearby: list[str] = []
    cur = ea
    for _ in range(limit):
        cur = idc.prev_head(cur, func_ea)
        if cur == idc.BADADDR or cur < func_ea:
            break
        line = _safe_disasm(cur)
        if line:
            nearby.append(line)
    nearby.reverse()
    return nearby


def _collect_compare_contexts(limit: int = 60) -> list[dict[str, str]]:
    compare_names = ("strcmp", "memcmp", "lstrcmp", "strncmp")
    imports: list[tuple[int, str]] = []
    for ea, name in idautils.Names():
        lower_name = (name or "").lower()
        if any(key in lower_name for key in compare_names):
            imports.append((ea, name))
    contexts: list[dict[str, str]] = []
    seen: set[tuple[int, int]] = set()
    for callee_ea, callee_name in imports:
        for xref in idautils.XrefsTo(callee_ea, 0):
            call_ea = int(xref.frm)
            func_ea = idc.get_func_attr(call_ea, idc.FUNCATTR_START)
            if func_ea == idc.BADADDR:
                continue
            key = (func_ea, call_ea)
            if key in seen:
                continue
            seen.add(key)
            disasm = _safe_disasm(call_ea)
            nearby: list[str] = []
            cur = call_ea
            for _ in range(4):
                cur = idc.prev_head(cur, func_ea)
                if cur == idc.BADADDR or cur < func_ea:
                    break
                line = _safe_disasm(cur)
                if line:
                    nearby.append(line)
            nearby.reverse()

            ref_strings: list[str] = []
            scan_eas = [*([idc.prev_head(call_ea, func_ea)] if func_ea != idc.BADADDR else []), call_ea]
            for insn_ea in scan_eas:
                if insn_ea == idc.BADADDR:
                    continue
                for ref in idautils.DataRefsFrom(insn_ea):
                    s = _safe_strlit(int(ref))
                    if s and s not in ref_strings:
                        ref_strings.append(s)
            contexts.append(
                {
                    "call_ea": _format_ea(call_ea),
                    "caller_func": ida_funcs.get_func_name(func_ea) or "",
                    "callee": callee_name,
                    "call_disasm": disasm,
                    "nearby": " || ".join(nearby[:4]),
                    "ref_strings": " | ".join(ref_strings[:3]),
                }
            )
            if len(contexts) >= limit:
                return contexts
    contexts.sort(key=lambda item: (-_text_score(item.get("ref_strings", "")), item["call_ea"]))
    return contexts[:limit]


def _collect_string_xrefs(limit: int = 80) -> list[dict[str, str]]:
    contexts: list[dict[str, str]] = []
    seen: set[tuple[int, int]] = set()
    st = idautils.Strings()
    st.setup(minlen=4)
    scored_strings: list[tuple[int, int, str]] = []
    for item in st:
        value = str(item)
        if not value or _text_score(value) <= 0:
            continue
        try:
            ea = int(item.ea)
        except Exception:
            continue
        scored_strings.append((_text_score(value), ea, value))
        if len(scored_strings) >= 5000:
            break
    scored_strings.sort(key=lambda item: (-item[0], len(item[2]), item[2]))

    for _, string_ea, value in scored_strings:
        for xref in idautils.XrefsTo(string_ea, 0):
            xref_ea = int(xref.frm)
            key = (string_ea, xref_ea)
            if key in seen:
                continue
            seen.add(key)
            func_ea = idc.get_func_attr(xref_ea, idc.FUNCATTR_START)
            nearby = _nearby_before(xref_ea, func_ea, limit=5) if func_ea != idc.BADADDR else []
            contexts.append(
                {
                    "string_ea": _format_ea(string_ea),
                    "xref_ea": _format_ea(xref_ea),
                    "caller_func": ida_funcs.get_func_name(func_ea) if func_ea != idc.BADADDR else "",
                    "string": value,
                    "xref_disasm": _safe_disasm(xref_ea),
                    "nearby": " || ".join(nearby),
                    "score": str(_text_score(value)),
                }
            )
            if len(contexts) >= limit:
                return contexts
    contexts.sort(key=lambda item: (-int(item.get("score", "0") or "0"), item["xref_ea"]))
    return contexts[:limit]


def _collect_local_check_contexts(limit: int = 60) -> list[dict[str, str]]:
    contexts: list[dict[str, str]] = []
    seen: set[int] = set()
    for func_ea in idautils.Functions():
        fn = ida_funcs.get_func(func_ea)
        if not fn:
            continue
        for ea in idautils.FuncItems(func_ea):
            if idc.print_insn_mnem(ea).lower() != "call":
                continue
            call_ea = int(ea)
            if call_ea in seen:
                continue
            seen.add(call_ea)

            nearby_insn: list[tuple[int, str]] = []
            cur = call_ea
            for _ in range(8):
                cur = idc.prev_head(cur, func_ea)
                if cur == idc.BADADDR or cur < func_ea:
                    break
                line = _safe_disasm(cur)
                if line:
                    nearby_insn.append((int(cur), line))
            nearby_insn.reverse()

            ref_strings: list[str] = []
            imm_args: list[str] = []
            for insn_ea, line in nearby_insn:
                for ref in idautils.DataRefsFrom(insn_ea):
                    s = _safe_strlit(int(ref))
                    if s and s not in ref_strings:
                        ref_strings.append(s)
                low = line.lower()
                if low.startswith("push "):
                    token = line.split(" ", 1)[1].strip()
                    if token.startswith("0x") or token.isdigit():
                        imm_args.append(token)

            if not ref_strings:
                continue
            score = _text_score(" | ".join(ref_strings))
            # Heuristic: keep contexts that look like key checking nearby.
            if score < 2 and not imm_args:
                continue

            callee = idc.print_operand(call_ea, 0) or ""
            contexts.append(
                {
                    "call_ea": _format_ea(call_ea),
                    "caller_func": ida_funcs.get_func_name(func_ea) or "",
                    "callee": callee,
                    "call_disasm": _safe_disasm(call_ea),
                    "nearby": " || ".join(line for _, line in nearby_insn[:6]),
                    "ref_strings": " | ".join(ref_strings[:4]),
                    "imm_args": " | ".join(imm_args[:4]),
                    "kind": "local_call_context",
                }
            )
            if len(contexts) >= limit:
                return contexts
    contexts.sort(
        key=lambda item: (
            -_text_score(f"{item.get('ref_strings', '')} {item.get('nearby', '')}"),
            item["call_ea"],
        )
    )
    return contexts[:limit]


def _collect_validation_function_candidates(
    compare_contexts: list[dict[str, str]],
    local_check_contexts: list[dict[str, str]],
    control_id_contexts: list[dict[str, str]],
    string_xrefs: list[dict[str, str]],
    limit: int = 20,
) -> list[dict[str, str]]:
    by_func: dict[str, dict[str, object]] = {}

    def add(func: str, points: int, reason: str, evidence: str = "") -> None:
        if not func:
            return
        item = by_func.setdefault(func, {"function": func, "score": 0, "reasons": [], "evidence": []})
        item["score"] = int(item["score"]) + points
        reasons = item["reasons"]
        if isinstance(reasons, list) and reason not in reasons:
            reasons.append(reason)
        evidence_items = item["evidence"]
        if evidence and isinstance(evidence_items, list) and evidence not in evidence_items:
            evidence_items.append(evidence)

    for ctx in compare_contexts:
        add(ctx.get("caller_func", ""), 8, "compare_context", ctx.get("call_ea", ""))
    for ctx in local_check_contexts:
        score = 5 + min(5, _text_score(ctx.get("ref_strings", "")))
        add(ctx.get("caller_func", ""), score, "local_check_context", ctx.get("call_ea", ""))
    for ctx in control_id_contexts:
        add(ctx.get("caller_func", ""), 3, "control_id_context", ctx.get("ea", ""))
    for ctx in string_xrefs:
        score = min(6, _text_score(ctx.get("string", "")))
        add(ctx.get("caller_func", ""), score, "interesting_string_xref", ctx.get("xref_ea", ""))

    candidates: list[dict[str, str]] = []
    for item in by_func.values():
        reasons = item.get("reasons", [])
        evidence = item.get("evidence", [])
        candidates.append(
            {
                "function": str(item.get("function", "")),
                "score": str(item.get("score", 0)),
                "reason": " | ".join(str(reason) for reason in reasons[:6]) if isinstance(reasons, list) else "",
                "evidence": " | ".join(str(ea) for ea in evidence[:8]) if isinstance(evidence, list) else "",
            }
        )
    candidates.sort(key=lambda item: (-int(item.get("score", "0") or "0"), item["function"]))
    return candidates[:limit]


def _collect_decompiler_snippets(
    validation_function_candidates: list[dict[str, str]],
    limit: int = 6,
    chars_per_snippet: int = 1400,
) -> tuple[bool, list[dict[str, str]]]:
    try:
        import ida_hexrays  # type: ignore
    except Exception:
        return False, []
    try:
        if not ida_hexrays.init_hexrays_plugin():
            return False, []
    except Exception:
        return False, []

    snippets: list[dict[str, str]] = []
    for candidate in validation_function_candidates:
        func_name = candidate.get("function", "")
        if not func_name:
            continue
        ea = idc.get_name_ea_simple(func_name)
        if ea == idc.BADADDR:
            continue
        func = ida_funcs.get_func(ea)
        if not func:
            continue
        try:
            cfunc = ida_hexrays.decompile(func.start_ea)
        except Exception:
            continue
        if not cfunc:
            continue
        text = str(cfunc)
        snippets.append(
            {
                "function": func_name,
                "entry_ea": _format_ea(int(func.start_ea)),
                "text": text[:chars_per_snippet],
            }
        )
        if len(snippets) >= limit:
            break
    return True, snippets


def _infer_solver_hints(
    compare_contexts: list[dict[str, str]],
    local_check_contexts: list[dict[str, str]],
    string_xrefs: list[dict[str, str]],
    validation_function_candidates: list[dict[str, str]],
) -> list[dict[str, str]]:
    text = " ".join(
        [
            *(str(ctx.get("callee", "")) for ctx in compare_contexts),
            *(str(ctx.get("ref_strings", "")) for ctx in compare_contexts),
            *(str(ctx.get("ref_strings", "")) for ctx in local_check_contexts),
            *(str(ctx.get("string", "")) for ctx in string_xrefs),
        ]
    ).lower()
    hints: list[dict[str, str]] = []
    if any(name in text for name in ("strcmp", "strncmp", "lstrcmp", "memcmp")):
        hints.append({"kind": "direct_strcmp", "reason": "compare API context recovered"})
    if any(name in text for name in ("md5", "sha", "hash")):
        hints.append({"kind": "hash_compare", "reason": "hash-related string or context recovered"})
    if validation_function_candidates and any(("xor" in text, "decrypt" in text, "encrypt" in text)):
        hints.append({"kind": "transform_then_compare", "reason": "transform keyword near validation context"})
    if any(name in text for name in ("input", "password", "flag")):
        hints.append({"kind": "gui_input", "reason": "input-oriented strings recovered"})
    if not hints:
        hints.append({"kind": "unknown", "reason": "no decisive solver pattern in bounded IDA summary"})
    return hints[:6]


def _collect_control_id_contexts(limit: int = 40) -> list[dict[str, str]]:
    target_ids = {"3E8", "3E9", "3EA", "1000", "1001", "1002"}
    contexts: list[dict[str, str]] = []
    seen: set[int] = set()
    for func_ea in idautils.Functions():
        fn = ida_funcs.get_func(func_ea)
        if not fn:
            continue
        for ea in idautils.FuncItems(func_ea):
            line = _safe_disasm(ea)
            if not line:
                continue
            low = line.lower()
            if not low.startswith("push "):
                continue
            operand = low.split(" ", 1)[1].strip()
            token = operand.replace("0x", "").upper()
            if token not in target_ids:
                continue
            if int(ea) in seen:
                continue
            seen.add(int(ea))
            nearby: list[str] = []
            cur = int(ea)
            for _ in range(5):
                cur = idc.prev_head(cur, func_ea)
                if cur == idc.BADADDR or cur < func_ea:
                    break
                prev_line = _safe_disasm(cur)
                if prev_line:
                    nearby.append(prev_line)
            nearby.reverse()
            contexts.append(
                {
                    "ea": _format_ea(int(ea)),
                    "caller_func": ida_funcs.get_func_name(func_ea) or "",
                    "insn": line,
                    "nearby": " || ".join(nearby[:5]),
                    "kind": "control_id_context",
                }
            )
            if len(contexts) >= limit:
                return contexts
    contexts.sort(key=lambda item: item["ea"])
    return contexts[:limit]


def main() -> None:
    ida_auto.auto_wait()
    out_path = _parse_out_path()
    try:
        entry_ea = idc.get_inf_attr(idc.INF_START_IP)
    except Exception:
        entry_ea = idc.get_inf_attr(idc.INF_START_EA)
    compare_contexts = _collect_compare_contexts()
    local_check_contexts = _collect_local_check_contexts()
    control_id_contexts = _collect_control_id_contexts()
    string_xrefs = _collect_string_xrefs()
    validation_function_candidates = _collect_validation_function_candidates(
        compare_contexts=compare_contexts,
        local_check_contexts=local_check_contexts,
        control_id_contexts=control_id_contexts,
        string_xrefs=string_xrefs,
    )
    hexrays_available, decompiler_snippets = _collect_decompiler_snippets(validation_function_candidates)
    payload = {
        "entry": hex(entry_ea),
        "strings": _collect_strings(),
        "functions": _collect_functions(),
        "compare_contexts": compare_contexts,
        "local_check_contexts": local_check_contexts,
        "control_id_contexts": control_id_contexts,
        "string_xrefs": string_xrefs,
        "validation_function_candidates": validation_function_candidates,
        "hexrays_available": hexrays_available,
        "decompiler_snippets": decompiler_snippets,
        "solver_hints": _infer_solver_hints(
            compare_contexts=compare_contexts,
            local_check_contexts=local_check_contexts,
            string_xrefs=string_xrefs,
            validation_function_candidates=validation_function_candidates,
        ),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    ida_pro.qexit(0)


if __name__ == "__main__":
    main()
