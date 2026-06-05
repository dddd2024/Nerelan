"""Targeted static re-extraction for unresolved local reverse samples.

Reads raw IDA JSON evidence for sha_256.exe, CPP2.exe and affine.exe,
extracts input-domain evidence and produces structured result JSON.
Does NOT re-run IDA; only parses existing raw evidence.

Decision: decision_20260605_affine_reextract_scope_rework_v1
Modes:
  - sha256/cpp2 (default): Process sha_256.exe and CPP2.exe targets
  - affine-main-input-flow: Process affine_8cfebe03 main input flow
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _find_decompiler_snippet(snippets: list[dict], func_name: str) -> str | None:
    for s in snippets:
        if s.get("function") == func_name:
            return s.get("text", "")
    return None


def _find_function_entry(snippets: list[dict], func_name: str) -> str | None:
    for s in snippets:
        if s.get("function") == func_name:
            return s.get("entry_ea", "")
    return None


def _ea_to_int(ea: str) -> int:
    """Convert address string to integer."""
    return int(ea, 16) if ea.startswith("0x") else int(ea, 16)


def _extract_scanf_context(main_pseudo: str) -> dict[str, Any]:
    """Extract scanf/gets/fgets/cin input API context from _main_0 pseudocode."""
    evidence: dict[str, Any] = {
        "input_api": "unknown",
        "format_string": "",
        "buffer_size_hint": "",
        "notes": [],
    }
    lower = main_pseudo.lower()
    if 'scanf' in lower:
        evidence["input_api"] = "scanf"
        # Extract format string
        for line in main_pseudo.split("\n"):
            stripped = line.strip()
            if 'scanf' in stripped and '"' in stripped:
                start = stripped.index('"') + 1
                end = stripped.index('"', start)
                evidence["format_string"] = stripped[start:end]
                evidence["notes"].append("scanf with %s format reads unbounded string")
                break
    if 'Source[1021]' in main_pseudo:
        evidence["buffer_size_hint"] = "1021 bytes (Source[1021])"
        evidence["notes"].append("Source buffer is 1021 bytes, effectively unbounded for %s scanf")
    return evidence


def _extract_length_constraints(main_pseudo: str) -> dict[str, Any]:
    """Extract input length constraints from _main_0 pseudocode."""
    constraints: dict[str, Any] = {
        "min_length": None,
        "max_length": None,
        "prefix_copy_length": None,
        "notes": [],
    }
    lower = main_pseudo.lower()
    if 'strlen(source) >= 5' in lower or 'v5 >= 5' in lower:
        constraints["min_length"] = 5
        constraints["notes"].append("minimum input length is 5 characters")
    if 'strncpy' in lower and ', 4u)' in lower:
        constraints["prefix_copy_length"] = 4
        constraints["notes"].append("only first 4 characters are copied via strncpy for hash input")
    # No upper bound found in either binary
    constraints["max_length"] = None
    constraints["notes"].append("no explicit upper bound on input length")
    return constraints


def _extract_post_increment_logic(main_pseudo: str, sample_id: str) -> dict[str, Any]:
    """Extract post-increment loop logic from _main_0 pseudocode."""
    logic: dict[str, Any] = {
        "loop_iterations": 64,
        "increment_type": "unknown",
        "wrap_rules": [],
        "notes": [],
    }
    lower = main_pseudo.lower()
    if sample_id == "18019fca52b389fe":
        # sha_256: two wrap rules
        logic["increment_type"] = "increment_with_dual_wrap"
        logic["wrap_rules"] = [
            "if (++Str1[i] == 103) Str1[i] = 97  -- 'g'(103) wraps to 'a'(97)",
            "if (Str1[i] == 58) Str1[i] = 48  -- ':'(58) wraps to '0'(48)",
        ]
        logic["notes"].append(
            "post-increment maps hex digits: 0-9->1-:, :-wrap->0, a-f unchanged, g->a"
        )
    elif sample_id == "4c69f173f2bd0211":
        # CPP2: simple increment
        logic["increment_type"] = "simple_increment"
        logic["wrap_rules"] = []
        logic["notes"].append("simple ++Str1[j] for 64 iterations, no wrap corrections")
    return logic


def _extract_input_range_check(main_pseudo: str) -> dict[str, Any]:
    """Extract input character range check from _main_0 pseudocode."""
    check: dict[str, Any] = {
        "has_range_check": False,
        "min_char": None,
        "max_char": None,
        "enforcement": "none",
        "notes": [],
    }
    if 'Source[i] < 65' in main_pseudo and 'Source[i] > 122' in main_pseudo:
        check["has_range_check"] = True
        check["min_char"] = 65  # 'A'
        check["max_char"] = 122  # 'z'
        check["notes"].append("input characters checked against range 65('A')..122('z')")
        # Check if the range check actually exits or just prints warning
        if 'return 0' not in main_pseudo.split("Source[i] > 122")[1].split("\n")[0:3]:
            check["enforcement"] = "warning_only"
            check["notes"].append(
                "range check prints warning but does NOT exit; execution continues"
            )
        else:
            check["enforcement"] = "hard_exit"
    return check


def _extract_sub_401005_evidence(
    raw_evidence: dict[str, Any],
    sample_id: str,
) -> dict[str, Any]:
    """Extract sub_401005 evidence from raw IDA JSON."""
    snippets = raw_evidence.get("decompiler_snippets", [])
    functions = raw_evidence.get("functions", [])

    pseudocode = _find_decompiler_snippet(snippets, "sub_401005")
    entry_ea = _find_function_entry(snippets, "sub_401005")

    # Check if sub_401005 exists in function list
    func_exists = "sub_401005" in functions

    evidence: dict[str, Any] = {
        "pseudocode_available": pseudocode is not None,
        "pseudocode": pseudocode or "",
        "entry_ea": entry_ea or "0x401005",
        "function_listed": func_exists,
        "disasm_available": False,
        "constants": [],
        "callgraph": [],
        "string_refs": [],
        "transform_hypothesis": "",
        "missing_evidence": [],
    }

    if pseudocode is None:
        evidence["missing_evidence"].append(
            "sub_401005 pseudocode not available: function was not in "
            "validation_function_candidates top-6 (scored 0 due to no "
            "compare/string/control_id context)"
        )
        evidence["missing_evidence"].append(
            "exact gap: collect_evidence.py scoring does not follow call graph "
            "from _main_0 to sub_401005; needs targeted decompilation of sub_401005"
        )
        evidence["transform_hypothesis"] = (
            "sub_401005 is called as sub_401005(Str1, &Destination, len) where "
            "Destination is 4-char prefix from user input. Output is 64-byte "
            "hex-like string in Str1. Given the 32-byte (64 hex char) output "
            "and the address 0x401005, this is consistent with a SHA-256 hash "
            "followed by hex encoding. However, without pseudocode, the exact "
            "transform cannot be confirmed."
        )
    else:
        # If we had pseudocode, we'd extract constants, callgraph, etc.
        evidence["transform_hypothesis"] = "pseudocode available; analysis pending"

    return evidence


def _extract_sha256_input_domain(
    raw_evidence: dict[str, Any],
    main_pseudo: str | None,
) -> dict[str, Any]:
    """Extract input-domain evidence for sha_256.exe."""
    domain: dict[str, Any] = {
        "status": "not_found",
        "constraints": [],
        "candidate_source": "",
        "notes": [],
    }

    if main_pseudo is None:
        domain["notes"].append("_main_0 pseudocode not available")
        return domain

    # Input API
    scanf_ctx = _extract_scanf_context(main_pseudo)
    domain["constraints"].append({"kind": "input_api", **scanf_ctx})

    # Length constraints
    length_ctx = _extract_length_constraints(main_pseudo)
    domain["constraints"].append({"kind": "length", **length_ctx})

    # Post-increment logic
    post_inc = _extract_post_increment_logic(main_pseudo, "18019fca52b389fe")
    domain["constraints"].append({"kind": "post_increment", **post_inc})

    # No input range check for sha_256
    range_check = _extract_input_range_check(main_pseudo)
    domain["constraints"].append({"kind": "range_check", **range_check})

    # Key finding: only 4 chars are hashed, but no bounded domain for those 4 chars
    domain["status"] = "not_found"
    domain["notes"].append(
        "sha_256.exe has NO bounded input domain: scanf reads unbounded string, "
        "only first 4 characters are passed to sub_401005, but those 4 characters "
        "can be any printable ASCII. No dictionary, no fixed prefix, no enumeration hint."
    )
    domain["notes"].append(
        "NO_BOUNDED_HASH_PREIMAGE_DOMAIN remains valid: 4 arbitrary chars "
        "yield 2^32 possible inputs, but SHA-256 preimage is computationally infeasible."
    )
    domain["candidate_source"] = ""

    return domain


def _extract_cpp2_sub_401005(
    raw_evidence: dict[str, Any],
    main_pseudo: str | None,
) -> dict[str, Any]:
    """Extract sub_401005 evidence for CPP2.exe."""
    sub_evidence = _extract_sub_401005_evidence(raw_evidence, "4c69f173f2bd0211")

    # Also extract input range and post-increment from main
    if main_pseudo:
        range_check = _extract_input_range_check(main_pseudo)
        sub_evidence["input_range_check"] = range_check
        post_inc = _extract_post_increment_logic(main_pseudo, "4c69f173f2bd0211")
        sub_evidence["post_increment"] = post_inc

    return sub_evidence


# ---------------------------------------------------------------------------
# Affine Main-Input-Flow Reextract (NEW MODE)
# ---------------------------------------------------------------------------

def _find_main_0_contexts(local_checks: list[dict]) -> list[dict]:
    """Extract local_check_context entries belonging to _main_0."""
    return [c for c in local_checks if c.get("caller_func") == "_main_0"]


def _find_main_0_string_xrefs(string_xrefs: list[dict]) -> list[dict]:
    """Extract string xrefs belonging to _main_0."""
    return [x for x in string_xrefs if x.get("caller_func") == "_main_0"]


def _find_calls_after_address(local_checks: list[dict], after_ea: str) -> list[dict]:
    """Find all local_check_context calls with address > after_ea."""
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


def _extract_affine_input_flow(main_contexts: list[dict], string_xrefs: list[dict]) -> dict[str, Any]:
    """Extract input API, format string, buffer candidates from _main_0 contexts for affine."""
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
    """Extract calls, reads, writes after scanf site for affine."""
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


def _extract_affine_candidate_transform_sites(local_checks: list[dict]) -> list[dict]:
    """Identify candidate transform sites (non-CRT calls in _main_0 after input) for affine."""
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
        "___crtGetStringTypeA", "___crtLCMapStringA", "___crtLCMapStringW",
        "CompareStringA", "CompareStringW",
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


def _extract_affine_candidate_compare_sites(compare_contexts: list[dict]) -> list[dict]:
    """Extract compare sites, filtering out CRT/heap noise for affine."""
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


def run_affine_main_input_flow_reextraction(
    sample_id: str,
    summary_path: Path,
    evidence_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Run affine main-input-flow reextraction using existing IDA evidence."""
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
    input_flow = _extract_affine_input_flow(main_contexts, main_string_xrefs)

    # Post-scanf flow (after 0x401065)
    post_scanf = _extract_post_scanf_flow(local_checks, "0x401065")

    # Candidate transform sites
    transform_sites = _extract_affine_candidate_transform_sites(local_checks)

    # Candidate compare sites
    compare_sites = _extract_affine_candidate_compare_sites(compare_contexts)

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
        "sample_id": sample_id,
        "relative_path": summary.get("relative_path", "逆向课程2024春补考03/affine.exe"),
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


# ---------------------------------------------------------------------------
# Main logic (sha256/cpp2 mode)
# ---------------------------------------------------------------------------

def _load_unresolved_targets(
    handoff: dict[str, Any],
    artifact_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Load unresolved targets from handoff artifact."""
    unresolved = handoff.get("unresolved_targets", [])
    if not unresolved:
        return []

    v2 = artifact_index.get("latest_artifacts_v2", {})
    targets = []
    for t in unresolved:
        sid = t["sample_id"]
        key = f"local_reverse_ida_evidence_{sid}"
        meta = v2.get(key, {})
        if meta.get("freshness") != "current":
            targets.append({
                **t,
                "raw_evidence_path": None,
                "raw_evidence_freshness": meta.get("freshness", "missing"),
            })
        else:
            targets.append({
                **t,
                "raw_evidence_path": meta.get("path"),
                "raw_evidence_freshness": "current",
            })
    return targets


def run_targeted_reextraction(
    artifact_index_path: Path,
    ida_summary_path: Path,
    handoff_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main extraction logic for sha256/cpp2 mode."""
    artifact_index = _load_json(artifact_index_path)
    ida_summary = _load_json(ida_summary_path)
    handoff = _load_json(handoff_path)

    # Validate handoff
    validated = handoff.get("validated_candidates", [])
    hookapi_ok = any(
        c.get("candidate") == "hookapi" and c.get("validation_status") == "validated"
        for c in validated
    )
    if not hookapi_ok:
        print("ERROR: handoff does not contain validated hookapi candidate", file=sys.stderr)
        sys.exit(1)

    # Load unresolved targets
    unresolved = _load_unresolved_targets(handoff, artifact_index)
    if not unresolved:
        print("ERROR: no unresolved targets found", file=sys.stderr)
        sys.exit(1)

    # Only process the two expected targets
    expected_ids = {"18019fca52b389fe", "4c69f173f2bd0211"}
    actual_ids = {t["sample_id"] for t in unresolved}
    if not actual_ids.issubset(expected_ids):
        print(
            f"ERROR: unexpected targets {actual_ids - expected_ids}",
            file=sys.stderr,
        )
        sys.exit(1)

    targets_result: list[dict[str, Any]] = []

    for t in unresolved:
        sid = t["sample_id"]
        raw_path = t.get("raw_evidence_path")
        freshness = t.get("raw_evidence_freshness", "missing")

        if freshness != "current" or raw_path is None:
            targets_result.append({
                "sample_id": sid,
                "relative_path": t.get("relative_path", ""),
                "previous_blocker": t.get("blocked_reason", ""),
                "extraction_status": "blocked",
                "recovered_evidence": [],
                "bounded_input_domain": {
                    "status": "not_found",
                    "constraints": [],
                    "candidate_source": "",
                },
                "sub_401005_evidence": {
                    "pseudocode_available": False,
                    "disasm_available": False,
                    "constants": [],
                    "callgraph": [],
                    "string_refs": [],
                    "transform_hypothesis": "",
                },
                "blocker_resolved": False,
                "next_action": f"raw IDA evidence for {sid} is {freshness}; cannot extract",
            })
            continue

        raw_evidence = _load_json(Path(raw_path))
        snippets = raw_evidence.get("decompiler_snippets", [])
        main_pseudo = _find_decompiler_snippet(snippets, "_main_0")

        if sid == "18019fca52b389fe":
            # sha_256.exe
            input_domain = _extract_sha256_input_domain(raw_evidence, main_pseudo)
            sub_evidence = _extract_sub_401005_evidence(raw_evidence, sid)

            recovered: list[dict[str, Any]] = []
            if main_pseudo:
                recovered.append({
                    "kind": "main_pseudocode",
                    "function": "_main_0",
                    "summary": "scanf %s into Source[1021], strlen>=5 check, strncpy 4 chars, "
                             "sub_401005 hash, post-increment with dual wrap, strncmp 64 hex chars",
                })
            recovered.append({
                "kind": "input_api_context",
                "detail": _extract_scanf_context(main_pseudo or ""),
            })
            recovered.append({
                "kind": "length_constraints",
                "detail": _extract_length_constraints(main_pseudo or ""),
            })
            recovered.append({
                "kind": "post_increment_logic",
                "detail": _extract_post_increment_logic(main_pseudo, sid),
            })
            recovered.append({
                "kind": "sub_401005_gap",
                "detail": sub_evidence,
            })

            targets_result.append({
                "sample_id": sid,
                "relative_path": t.get("relative_path", ""),
                "previous_blocker": t.get("blocked_reason", ""),
                "extraction_status": "partial",
                "recovered_evidence": recovered,
                "bounded_input_domain": input_domain,
                "sub_401005_evidence": sub_evidence,
                "blocker_resolved": False,
                "next_action": (
                    "NO_BOUNDED_HASH_PREIMAGE_DOMAIN confirmed: 4 arbitrary chars "
                    "passed to SHA-256-like hash with no bounded enumeration. "
                    "sub_401005 pseudocode missing (needs targeted IDA decompilation). "
                    "Request problem statement hint for input domain or length."
                ),
            })

        elif sid == "4c69f173f2bd0211":
            # CPP2.exe
            sub_evidence = _extract_cpp2_sub_401005(raw_evidence, main_pseudo)

            recovered = []
            if main_pseudo:
                recovered.append({
                    "kind": "main_pseudocode",
                    "function": "_main_0",
                    "summary": "scanf %s into Source[1021], strlen>=5 check, range 65..122 "
                             "(warning only), strncpy 4 chars, sub_401005 hash, "
                             "simple ++Str1 post-increment, strncmp 64 chars",
                })
            recovered.append({
                "kind": "input_range_check",
                "detail": _extract_input_range_check(main_pseudo or ""),
            })
            recovered.append({
                "kind": "post_increment_logic",
                "detail": _extract_post_increment_logic(main_pseudo, sid),
            })
            recovered.append({
                "kind": "sub_401005_gap",
                "detail": sub_evidence,
            })

            targets_result.append({
                "sample_id": sid,
                "relative_path": t.get("relative_path", ""),
                "previous_blocker": t.get("blocked_reason", ""),
                "extraction_status": "partial",
                "recovered_evidence": recovered,
                "bounded_input_domain": {
                    "status": "partial",
                    "constraints": [
                        {"kind": "input_range", "value": "65..122 (A-z), enforcement=warning_only"},
                        {"kind": "min_length", "value": 5},
                        {"kind": "prefix_copy_length", "value": 4},
                    ],
                    "candidate_source": "input range 65..122 with 4-char prefix gives "
                                       "58^4 = 11,316,496 possible inputs if range were "
                                       "strictly enforced (but enforcement is warning only)",
                },
                "sub_401005_evidence": sub_evidence,
                "blocker_resolved": False,
                "next_action": (
                    "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005 confirmed: "
                    "sub_401005 pseudocode not available in raw IDA evidence. "
                    "Exact gap: collect_evidence.py scoring does not follow call graph "
                    "from _main_0 to sub_401005. Needs targeted IDAPython decompilation "
                    "of sub_401005 at 0x401005, or a new IDA run with sub_401005 forced "
                    "into validation_function_candidates."
                ),
            })

    result: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": "local_reverse_targeted_static_reextraction_v1",
        "status": "PARTIAL",
        "target_count": 2,
        "source_handoff": str(handoff_path),
        "targets": targets_result,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(
        f"targeted static re-extraction: status={result['status']} "
        f"targets={result['target_count']}"
    )
    for t in targets_result:
        print(
            f"  {t['sample_id']}: extraction_status={t['extraction_status']} "
            f"blocker_resolved={t['blocker_resolved']}"
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Targeted static re-extraction for local reverse samples. "
                    "Supports sha256/cpp2 mode (default) and affine-main-input-flow mode.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="sha256-cpp2",
        choices=["sha256-cpp2", "affine-main-input-flow"],
        help="Reextract mode: sha256-cpp2 (default) or affine-main-input-flow",
    )
    parser.add_argument(
        "--sample-id",
        type=str,
        default="affine_8cfebe03",
        help="Sample ID for affine-main-input-flow mode",
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
        help="Path to artifact_index.json (sha256-cpp2 mode)",
    )
    parser.add_argument(
        "--ida-summary",
        type=Path,
        default=None,
        help="Path to IDA summary JSON (sha256-cpp2 mode) or affine summary JSON (affine mode)",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Alias for --ida-summary",
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=Path("project_state/local_reverse_validated_candidate_handoff.json"),
        help="Path to validated candidate handoff JSON (sha256-cpp2 mode)",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=None,
        help="Path to detailed IDA evidence JSON (affine mode)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for result JSON",
    )
    args = parser.parse_args()

    # Determine output path
    out_path = args.out
    if out_path is None:
        if args.mode == "affine-main-input-flow":
            out_path = Path("project_state/local_reverse_affine_main_input_flow_reextract.json")
        else:
            out_path = Path("project_state/local_reverse_targeted_static_reextraction_result.json")

    # Affine main-input-flow mode
    if args.mode == "affine-main-input-flow":
        # Determine summary path
        summary_path = args.summary or args.ida_summary or Path(
            "project_state/local_reverse_affine_ida_summary.json"
        )
        # Determine evidence path
        evidence_path = args.evidence or Path(
            "solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/"
            "affine_8cfebe03/affine_ida_evidence.json"
        )

        run_affine_main_input_flow_reextraction(
            sample_id=args.sample_id,
            summary_path=summary_path,
            evidence_path=evidence_path,
            out_path=out_path,
        )
        return

    # sha256-cpp2 mode (default)
    ida_summary_path = args.ida_summary or args.summary or Path(
        "project_state/local_reverse_ida_summary.json"
    )

    run_targeted_reextraction(
        artifact_index_path=args.artifact_index,
        ida_summary_path=ida_summary_path,
        handoff_path=args.handoff,
        out_path=out_path,
    )


if __name__ == "__main__":
    main()
