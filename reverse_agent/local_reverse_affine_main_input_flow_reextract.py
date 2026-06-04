"""Affine main-input-flow targeted static re-extraction.

Reads existing affine IDA evidence JSON and summary, extracts _main_0
input-flow evidence without re-running IDA or the sample.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _find_main_0_contexts(local_checks: list[dict]) -> list[dict]:
    """Extract local_check_context entries belonging to _main_0."""
    return [c for c in local_checks if c.get("caller_func") == "_main_0"]


def _find_main_0_string_xrefs(string_xrefs: list[dict]) -> list[dict]:
    """Extract string xrefs belonging to _main_0."""
    return [x for x in string_xrefs if x.get("caller_func") == "_main_0"]


def _find_calls_after_address(local_checks: list[dict], after_ea: str) -> list[dict]:
    """Find all local_check_context calls with address > after_ea."""
    def _ea_to_int(ea: str) -> int:
        return int(ea, 16) if ea.startswith("0x") else int(ea, 16)
    after = _ea_to_int(after_ea)
    results = []
    for c in local_checks:
        ea = c.get("call_ea", "")
        try:
            val = _ea_to_int(ea)
            if val > after:
                results.append(c)
        except ValueError:
            continue
    # Sort by address
    results.sort(key=lambda x: _ea_to_int(x.get("call_ea", "0")))
    return results


def _extract_input_flow(main_contexts: list[dict], string_xrefs: list[dict]) -> dict[str, Any]:
    """Extract input API, format string, buffer candidates from _main_0 contexts."""
    flow: dict[str, Any] = {
        "input_api": "unknown",
        "format_string": "",
        "buffer_candidates": [],
        "stack_variables": [],
        "notes": [],
    }

    # Find scanf context
    scanf_ctx = [c for c in main_contexts if c.get("callee") == "_scanf"]
    if scanf_ctx:
        flow["input_api"] = "scanf"
        ctx = scanf_ctx[0]
        ref_strings = ctx.get("ref_strings", "")
        if "%s" in ref_strings:
            flow["format_string"] = "%s"
            flow["notes"].append("scanf with %s format reads unbounded string")
        # Extract buffer candidates from nearby disassembly
        nearby = ctx.get("nearby", "")
        if "[ebp+Str]" in nearby:
            flow["buffer_candidates"].append("[ebp+Str] (local stack buffer)")
        if "[ebp+Buffer]" in nearby:
            flow["buffer_candidates"].append("[ebp+Buffer] (local stack buffer)")
        # Stack variables from nearby
        for var in ["var_6B", "var_4", "var_8", "var_C", "var_10", "var_14"]:
            if var in nearby:
                flow["stack_variables"].append(var)
        flow["notes"].append("scanf reads into local stack buffer; buffer size not confirmed from static evidence")

    # Find puts context
    puts_ctx = [c for c in main_contexts if c.get("callee") == "_puts"]
    if puts_ctx:
        flow["notes"].append("puts prompt precedes scanf: 'please input a string:'")

    return flow


def _extract_post_scanf_flow(
    all_local_checks: list[dict],
    after_ea: str,
) -> dict[str, Any]:
    """Extract calls, reads, writes after scanf site."""
    calls_after = _find_calls_after_address(all_local_checks, after_ea)

    post_flow: dict[str, Any] = {
        "calls_after_scanf": [],
        "reads_from_input_buffer": [],
        "writes_to_input_buffer": [],
        "notes": [],
    }

    for c in calls_after:
        callee = c.get("callee", "")
        caller = c.get("caller_func", "")
        ea = c.get("call_ea", "")
        nearby = c.get("nearby", "")
        ref_strings = c.get("ref_strings", "")

        entry = {
            "call_ea": ea,
            "caller_func": caller,
            "callee": callee,
            "nearby": nearby,
            "ref_strings": ref_strings,
        }
        post_flow["calls_after_scanf"].append(entry)

        # Detect reads/writes to input buffer
        if any(v in nearby for v in ["[ebp+Str]", "[ebp+Buffer]", "Str", "Buffer"]):
            if any(w in nearby for w in ["mov", "push"]):
                post_flow["reads_from_input_buffer"].append({
                    "call_ea": ea,
                    "callee": callee,
                    "evidence": nearby,
                })

    # Filter to _main_0 only for business logic
    main_calls = [c for c in post_flow["calls_after_scanf"] if c["caller_func"] == "_main_0"]
    post_flow["calls_after_scanf_in_main_0"] = main_calls
    post_flow["notes"].append(
        f"Total {len(post_flow['calls_after_scanf'])} calls after scanf; "
        f"{len(main_calls)} within _main_0"
    )

    return post_flow


def _extract_candidate_transform_sites(local_checks: list[dict]) -> list[dict]:
    """Identify candidate transform sites (non-CRT calls in _main_0 after input)."""
    crt_funcs = {
        "_puts", "_scanf", "__CrtDbgReport", "__malloc_dbg", "__calloc_dbg",
        "_strlen", "_strcpy", "_strncpy", "_memcpy", "_memset",
        "__heap_alloc_dbg", "_realloc_help", "sub_407A90", "sub_4073D0",
        "sub_407ED0", "_CheckBytes", "__msize_dbg", "__stbuf", "__ftbuf",
        "sub_4028D0", "_CrtMessageWindow", "__NMSG_WRITE", "__vsnprintf",
        "__snprintf", "_printf", "_sprintf", "_strcat", "_strchr",
        "_strstr", "_strrchr", "_strtol", "_strtoul", "_strtoxl",
        "_toupper", "_tolower", "_isalpha", "_isdigit", "_isalnum",
        "_isspace", "_isupper", "_islower", "_isxdigit", "_isprint",
        "_ispunct", "_iscntrl", "_isgraph", "__itoa", "__ltoa", "__ultoa",
        "__i64toa", "__ui64toa", "_get_int_arg", "_get_short_arg",
        "_get_int64_arg", "_xtoa", "__hextodec", "__mbschr", "__mbsrchr",
        "__mbsnbicoll", "__whiteout", "__un_inc", "__inc", "__unwind_handler",
        "__except_handler3", "__global_unwind2", "__local_unwind2",
        "__abnormal_termination", "__NLG_Notify", "__NLG_Notify1",
        "__XcptFilter", "__FF_MSGBANNER", "__GET_RTERRMSG", "__NMSG_WRITE",
        "_fast_error_exit", "__amsg_exit", "__callnewh", "__chkesp",
        "__alloca_probe", "__allshl", "__aulldiv", "__aullrem",
        "_doexit", "__c_exit", "__cexit", "__exit", "_exit",
        "__close", "__commit", "__open_osfhandle", "__get_osfhandle",
        "__free_osfhnd", "__set_osfnd", "__lseek", "__read", "__write",
        "__filbuf", "__flsbuf", "__getbuf", "__freebuf", "__stbuf",
        "__ftbuf", "__flush", "__fcloseall", "__fptrap", "_fclose",
        "_fflush", "_flsall", "_fwrite", "__ioinit", "___initstdio",
        "___endstdio", "__ioterm", "__isatty", "_setSBCS", "_setSBUpLow",
        "__setargv", "__setenvp", "_copy_environ", "_findenv", "_getenv",
        "___crtsetenv", "___wtomb_environ", "__getmbcp", "__setmbcp",
        "___initmbctable", "___isascii", "___iscsym", "___iscsymf",
        "___toascii", "_mbtowc", "_wctomb", "__access", "__getpath",
        "_parse_cmdline", "_comexecmd", "__dospawn", "__spawnve",
        "__spawnvpe", "__dosmaperr", "__set_sbh_threshold",
        "___sbh_heap_init", "___sbh_heapmin", "___sbh_new_region",
        "___sbh_release_region", "___sbh_alloc_block", "___sbh_alloc_block_0",
        "___sbh_alloc_block_from_page", "___sbh_alloc_new_group",
        "___sbh_alloc_new_region", "___sbh_decommit_pages",
        "___sbh_find_block", "___sbh_find_block_0", "___sbh_free_block",
        "___sbh_resize_block", "___sbh_resize_block_0", "___sbh_heap_check",
        "___sbh_heap_check_0", "___sbh_verify_block",
        "_CPtoLCID", "___crtCompareStringA", "___crtGetEnvironmentStringsA",
        "___crtGetStringTypeA", "___crtLCMapStringA", "___crtMessageBoxA",
        "___crtCompareStringW", "CompareStringA", "CompareStringW",
        "LCMapStringA", "LCMapStringW", "GetStringTypeA", "GetStringTypeW",
        "MultiByteToWideChar", "WideCharToMultiByte",
        "GetACP", "GetOEMCP", "GetCPInfo", "SetEnvironmentVariableA",
        "GetEnvironmentVariableA", "FreeEnvironmentStringsA",
        "FreeEnvironmentStringsW", "GetEnvironmentStrings",
        "GetEnvironmentStringsW", "GetCommandLineA", "GetVersion",
        "GetVersionExA", "GetModuleHandleA", "GetModuleFileNameA",
        "GetProcAddress", "LoadLibraryA", "GetStartupInfoA",
        "GetStdHandle", "SetStdHandle", "GetFileType", "SetFilePointer",
        "SetHandleCount", "FlushFileBuffers", "CreateProcessA",
        "ExitProcess", "TerminateProcess", "GetCurrentProcess",
        "GetExitCodeProcess", "WaitForSingleObject", "CloseHandle",
        "ReadFile", "WriteFile", "VirtualAlloc", "VirtualFree",
        "HeapAlloc", "HeapFree", "HeapReAlloc", "HeapCreate",
        "HeapDestroy", "HeapValidate", "IsBadReadPtr", "IsBadWritePtr",
        "RtlUnwind", "UnhandledExceptionFilter", "SetConsoleCtrlHandler",
        "InterlockedIncrement", "InterlockedDecrement",
        "OutputDebugStringA", "GetLastError", "DebugBreak",
        "MessageBoxA", "wsprintfA",
    }

    candidates = []
    for c in local_checks:
        if c.get("caller_func") != "_main_0":
            continue
        callee = c.get("callee", "")
        # Skip CRT and known non-business functions
        if callee in crt_funcs or callee.startswith("__") or callee.startswith("_Crt"):
            continue
        if callee in ("_puts", "_scanf"):
            continue
        # Skip imports
        if callee.startswith("ds:__imp_") or callee.startswith("__imp_"):
            continue
        candidates.append({
            "call_ea": c.get("call_ea"),
            "callee": callee,
            "nearby": c.get("nearby"),
            "ref_strings": c.get("ref_strings"),
            "reason": "non-CRT call in _main_0 after input",
        })
    return candidates


def _extract_candidate_compare_sites(compare_contexts: list[dict]) -> list[dict]:
    """Extract compare sites, filtering out CRT/heap noise."""
    noise_strings = {"__GLOBAL_HEAP_SELECTED"}
    candidates = []
    for ctx in compare_contexts:
        ref = ctx.get("ref_strings", "")
        if ref in noise_strings:
            candidates.append({
                "call_ea": ctx.get("call_ea"),
                "caller_func": ctx.get("caller_func"),
                "callee": ctx.get("callee"),
                "nearby": ctx.get("nearby"),
                "ref_strings": ref,
                "reason": "CRT/heap-related compare; NOT business final compare",
                "confidence": "noise",
            })
        else:
            candidates.append({
                "call_ea": ctx.get("call_ea"),
                "caller_func": ctx.get("caller_func"),
                "callee": ctx.get("callee"),
                "nearby": ctx.get("nearby"),
                "ref_strings": ref,
                "reason": "potential business compare",
                "confidence": "low",
            })
    return candidates


def run_affine_reextraction(
    summary_path: Path,
    evidence_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    evidence = _load_json(evidence_path)

    local_checks = evidence.get("local_check_contexts", [])
    string_xrefs = evidence.get("string_xrefs", [])
    compare_contexts = evidence.get("compare_contexts", [])
    decompiler_snippets = evidence.get("decompiler_snippets", [])

    # _main_0 contexts
    main_contexts = _find_main_0_contexts(local_checks)
    main_string_xrefs = _find_main_0_string_xrefs(string_xrefs)

    # Input flow
    input_flow = _extract_input_flow(main_contexts, main_string_xrefs)

    # Post-scanf flow (after 0x401065)
    post_scanf = _extract_post_scanf_flow(local_checks, "0x401065")

    # Candidate transform sites
    transform_sites = _extract_candidate_transform_sites(local_checks)

    # Candidate compare sites
    compare_sites = _extract_candidate_compare_sites(compare_contexts)

    # Check for _main_0 decompiler snippet
    main_pseudo = None
    for s in decompiler_snippets:
        if s.get("function") == "_main_0":
            main_pseudo = s.get("text", "")
            break

    # Noise sites (CRT in _main_0)
    noise_sites = []
    for c in main_contexts:
        callee = c.get("callee", "")
        if callee in ("__CrtDbgReport", "__malloc_dbg", "__calloc_dbg",
                       "_strlen", "_strcpy", "_strncpy") or callee.startswith("__"):
            noise_sites.append({
                "call_ea": c.get("call_ea"),
                "callee": callee,
                "reason": "CRT/debug/standard library call; not business logic",
            })

    # Build result
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": summary.get("sample_id", "affine_8cfebe03"),
        "relative_path": summary.get("relative_path", ""),
        "analysis_mode": "targeted_static_reextract_main_input_flow",
        "executed_sample": False,
        "source_summary": str(summary_path).replace("\\", "/"),
        "source_evidence": str(evidence_path).replace("\\", "/"),
        "focus": {
            "function": "_main_0",
            "input_prompt_site": "0x401054",
            "scanf_site": "0x401065",
        },
        "input_flow": input_flow,
        "post_scanf_flow": post_scanf,
        "candidate_transform_sites": transform_sites,
        "candidate_compare_sites": compare_sites,
        "noise_or_low_priority_sites": noise_sites,
        "decompiler_status": {
            "_main_0_pseudocode_available": main_pseudo is not None,
            "_main_0_pseudocode_length": len(main_pseudo) if main_pseudo else 0,
            "notes": [] if main_pseudo else [
                "_main_0 pseudocode NOT available in raw IDA evidence. "
                "collect_evidence.py scoring did not include _main_0 in top-6 decompiler snippets. "
                "Input flow extracted from local_check_contexts and string_xrefs only."
            ],
        },
        "confidence": "low" if not main_pseudo else "medium",
        "blockers": [] if main_pseudo else [
            "MISSING_MAIN_0_PSEUDOCODE: _main_0 decompiler snippet not in raw evidence; "
            "core affine transform logic cannot be confirmed without targeted IDA decompilation of _main_0"
        ],
        "recommended_next_action": (
            "targeted_ida_decompile_specific_function"
            if not main_pseudo else
            "affine_constraint_recovery"
        ),
        "recommended_next_focus": (
            "_main_0 full decompilation at 0x401000-0x401100 range"
            if not main_pseudo else
            "_main_0 post-scanf data flow analysis"
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(f"affine main-input-flow re-extraction: confidence={result['confidence']}")
    print(f"  _main_0 contexts: {len(main_contexts)}")
    print(f"  candidate transforms: {len(transform_sites)}")
    print(f"  candidate compares: {len(compare_sites)}")
    print(f"  noise sites: {len(noise_sites)}")
    print(f"  blockers: {len(result['blockers'])}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Affine main-input-flow targeted static re-extraction.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("project_state/local_reverse_affine_ida_summary.json"),
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path(
            "solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/"
            "affine_8cfebe03/affine_ida_evidence.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_affine_main_input_flow_reextract.json"),
    )
    args = parser.parse_args()
    run_affine_reextraction(
        summary_path=args.summary,
        evidence_path=args.evidence,
        out_path=args.out,
    )


if __name__ == "__main__":
    main()
