"""Build a static direct-strcmp handoff from local reverse triage evidence.

This module reads an existing static triage artifact and extracts a literal
expected operand from a direct strcmp context. It does not execute the target
binary, run IDA/Ghidra, or perform runtime validation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DIRECT_STRCMP_CALLEES = {"strcmp", "_strcmp"}
BLOCKED_NO_CURRENT_TRIAGE = "NO_CURRENT_STATIC_TRIAGE"
BLOCKED_NO_DIRECT_STRCMP = "NO_DIRECT_STRCMP_CONTEXT"
BLOCKED_AMBIGUOUS = "AMBIGUOUS_STRCMP_CONTEXT"
BLOCKED_NO_LITERAL = "NO_LITERAL_EXPECTED_OPERAND"
BLOCKED_INTERNAL_CRT = "INTERNAL_CRT_CONTEXT_ONLY"


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


def _norm_callee(callee: str) -> str:
    return str(callee or "").strip().lower()


def _is_direct_strcmp(callee: str) -> bool:
    return _norm_callee(callee) in DIRECT_STRCMP_CALLEES


def _is_strncmp(callee: str) -> bool:
    return _norm_callee(callee).lstrip("_") == "strncmp"


def _extract_literals(text: str) -> list[str]:
    literals: list[str] = []
    for match in re.finditer(r'"((?:\\.|[^"\\])*)"', text or ""):
        raw = match.group(1)
        try:
            literals.append(bytes(raw, "utf-8").decode("unicode_escape"))
        except UnicodeDecodeError:
            literals.append(raw)
    return literals


def _is_internal_literal(literal: str) -> bool:
    upper = literal.upper()
    internal_markers = [
        "__GLOBAL_HEAP_SELECTED",
        "GLOBAL_HEAP",
        "MICROSOFT VISUAL C++",
        "RUNTIME ERROR",
        "ASSERTION",
        "CRT",
    ]
    return any(marker in upper for marker in internal_markers)


def _has_stack_local_input(nearby: str) -> bool:
    lowered = (nearby or "").lower()
    return (
        bool(re.search(r"\[ebp[+-][^\]]+\]", lowered))
        or "push    ecx" in lowered
        or "push ecx" in lowered
        or "; str1" in lowered
    )


def _context_priority(context: dict[str, Any]) -> int:
    caller = str(context.get("caller_func", ""))
    return 0 if caller == "_main_0" else 1


def _eligible_contexts(compare_contexts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    saw_internal_only = False
    eligible: list[dict[str, Any]] = []
    for context in compare_contexts:
        callee = str(context.get("callee", ""))
        nearby = str(context.get("nearby", ""))
        if _is_strncmp(callee):
            literals = _extract_literals(nearby)
            if literals and all(_is_internal_literal(lit) for lit in literals):
                saw_internal_only = True
            continue
        if not _is_direct_strcmp(callee):
            continue
        literals = [lit for lit in _extract_literals(nearby) if lit and not _is_internal_literal(lit)]
        if not literals:
            context = dict(context)
            context["_missing_literal"] = True
            eligible.append(context)
            continue
        if not _has_stack_local_input(nearby):
            continue
        context = dict(context)
        context["_candidate_literals"] = literals
        eligible.append(context)
    return eligible, saw_internal_only


def _select_context(compare_contexts: list[dict[str, Any]]) -> dict[str, Any]:
    eligible, saw_internal_only = _eligible_contexts(compare_contexts)
    literal_contexts = [ctx for ctx in eligible if ctx.get("_candidate_literals")]
    if not literal_contexts:
        if any(ctx.get("_missing_literal") for ctx in eligible):
            return {"status": "BLOCKED", "blocked_reason": BLOCKED_NO_LITERAL}
        if saw_internal_only:
            return {"status": "BLOCKED", "blocked_reason": BLOCKED_INTERNAL_CRT}
        return {"status": "BLOCKED", "blocked_reason": BLOCKED_NO_DIRECT_STRCMP}

    literal_contexts.sort(key=_context_priority)
    best_priority = _context_priority(literal_contexts[0])
    best_contexts = [ctx for ctx in literal_contexts if _context_priority(ctx) == best_priority]
    if len(best_contexts) != 1:
        return {"status": "BLOCKED", "blocked_reason": BLOCKED_AMBIGUOUS}

    selected = best_contexts[0]
    literals = selected.get("_candidate_literals", [])
    if len(literals) != 1:
        return {"status": "BLOCKED", "blocked_reason": BLOCKED_AMBIGUOUS}

    return {"status": "READY_FOR_RUNTIME_VALIDATION", "context": selected, "literal": literals[0]}


def _source_is_current_success(triage: dict[str, Any]) -> bool:
    return (
        triage.get("source_artifact_freshness") == "current"
        and triage.get("status") == "STATIC_TRIAGE_COMPLETE"
        and triage.get("tool_status") == "success"
        and triage.get("source_tool") == "IDA"
        and triage.get("solved") is False
    )


def _base_artifact(triage: dict[str, Any], triage_path: Path) -> dict[str, Any]:
    sample_id = str(triage.get("sample_id", ""))
    source_key = f"local_reverse_{sample_id}_static_triage" if sample_id else ""
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "direct_strcmp_static_handoff",
        "mainline": "reverse_solving",
        "source_artifacts": [source_key] if source_key else [],
        "source_artifact_freshness": triage.get("source_artifact_freshness", ""),
        "source_triage_artifact": str(triage_path).replace("\\", "/"),
        "relative_path": triage.get("relative_path", ""),
        "sha256": triage.get("sha256", ""),
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "source_tool": triage.get("source_tool", ""),
        "candidate": None,
        "known_candidate": "",
        "validation_status": "not_validated",
        "solved": False,
        "generated_at": _now_iso(),
    }


def _blocked_artifact(triage: dict[str, Any], triage_path: Path, blocked_reason: str) -> dict[str, Any]:
    result = _base_artifact(triage, triage_path)
    result.update(
        {
            "compare_call_ea": "",
            "compare_caller_func": "",
            "compare_callee": "",
            "compare_nearby": "",
            "input_operand_summary": "",
            "expected_operand_summary": "",
            "static_candidate_text": "",
            "static_candidate_hex": "",
            "static_candidate_printable": False,
            "extraction_method": "direct_strcmp_literal_operand",
            "status": "BLOCKED",
            "blocked_reason": blocked_reason,
            "recommended_next_action": f"Resolve blocker: {blocked_reason}",
        }
    )
    return result


def build_handoff(*, triage_path: Path, out_path: Path) -> dict[str, Any]:
    triage = _load_json(triage_path)
    if not _source_is_current_success(triage):
        result = _blocked_artifact(triage, triage_path, BLOCKED_NO_CURRENT_TRIAGE)
        _save_json(out_path, result)
        return result

    compare_contexts = triage.get("triage", {}).get("compare_contexts", [])
    if not isinstance(compare_contexts, list):
        compare_contexts = []

    selection = _select_context([ctx for ctx in compare_contexts if isinstance(ctx, dict)])
    if selection["status"] == "BLOCKED":
        result = _blocked_artifact(triage, triage_path, selection["blocked_reason"])
        _save_json(out_path, result)
        return result

    context = selection["context"]
    literal = selection["literal"]
    candidate_bytes = literal.encode("utf-8")
    result = _base_artifact(triage, triage_path)
    result.update(
        {
            "source_artifact_freshness": "current",
            "compare_call_ea": context.get("call_ea", ""),
            "compare_caller_func": context.get("caller_func", ""),
            "compare_callee": context.get("callee", ""),
            "compare_nearby": context.get("nearby", ""),
            "input_operand_summary": "stack/local input Str1",
            "expected_operand_summary": "literal string Str2",
            "static_candidate_text": literal,
            "static_candidate_hex": candidate_bytes.hex(),
            "static_candidate_printable": all(32 <= b < 127 for b in candidate_bytes),
            "extraction_method": "direct_strcmp_literal_operand",
            "status": "READY_FOR_RUNTIME_VALIDATION",
            "blocked_reason": "",
            "recommended_next_action": "Static direct-strcmp candidate extracted. Runtime validation is required before marking solved.",
        }
    )
    _save_json(out_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Static direct-strcmp handoff from local reverse triage evidence.")
    parser.add_argument("--triage", default="project_state/local_reverse_cpp2_2f64e68d_static_triage.json")
    parser.add_argument("--out", default="project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json")
    args = parser.parse_args()

    try:
        result = build_handoff(triage_path=Path(args.triage), out_path=Path(args.out))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"direct_strcmp_handoff: status={result['status']} sample_id={result.get('sample_id', '')}")
    if result["status"] == "READY_FOR_RUNTIME_VALIDATION":
        print(f"  static_candidate_text: {result['static_candidate_text']}")
        print(f"  static_candidate_hex: {result['static_candidate_hex']}")
        print(f"  compare_call_ea: {result['compare_call_ea']}")
    else:
        print(f"  blocked_reason: {result['blocked_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
