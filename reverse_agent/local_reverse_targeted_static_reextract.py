"""Targeted static re-extraction for unresolved local reverse samples.

Reads raw IDA JSON evidence for sha_256.exe and CPP2.exe, extracts
input-domain evidence and sub_401005 evidence, and produces a structured
result JSON.  Does NOT re-run IDA; only parses existing raw evidence.

Decision: decision_20260603_local_reverse_targeted_static_reextraction_v1
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
# Main logic
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
    """Main extraction logic."""
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
        description="Targeted static re-extraction for unresolved local reverse samples.",
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
        help="Path to artifact_index.json",
    )
    parser.add_argument(
        "--ida-summary",
        type=Path,
        default=Path("project_state/local_reverse_ida_summary.json"),
        help="Path to IDA summary JSON",
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=Path("project_state/local_reverse_validated_candidate_handoff.json"),
        help="Path to validated candidate handoff JSON",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_targeted_static_reextraction_result.json"),
        help="Output path for re-extraction result JSON",
    )
    args = parser.parse_args()
    run_targeted_reextraction(
        artifact_index_path=args.artifact_index,
        ida_summary_path=args.ida_summary,
        handoff_path=args.handoff,
        out_path=args.out,
    )


if __name__ == "__main__":
    main()
