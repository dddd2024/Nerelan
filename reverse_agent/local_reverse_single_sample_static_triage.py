"""Single-sample static triage adapter.

Reads a sample from the evaluation queue / inventory, runs IDA static
evidence collection (reusing existing tool_runners / collect_evidence.py),
and produces a compact triage artifact.

Does NOT execute the target binary. Does NOT generate candidates.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_sample_root() -> Path | None:
    """Try to locate the LOCAL_REVERSE_ROOT directory."""
    candidates = [
        os.environ.get("LOCAL_REVERSE_ROOT", ""),
        r"E:\reverse",
        r"D:\reverse",
        r"C:\reverse",
    ]
    home_reverse = str(Path.home() / "reverse")
    candidates.append(home_reverse)

    for c_str in candidates:
        c_str = c_str.strip()
        if not c_str:
            continue
        # Use os.path to check existence (handles drive letters correctly)
        if os.path.isdir(c_str):
            return Path(c_str)
    return None


def _locate_sample(
    sample_id: str,
    queue_path: Path,
    inventory_path: Path,
) -> dict[str, Any]:
    """Locate sample metadata from queue and inventory."""
    # Load queue
    queue = _load_json(queue_path) if queue_path.exists() else {}
    inventory = _load_json(inventory_path) if inventory_path.exists() else {}

    # Find in queue
    queue_entry: dict[str, Any] = {}
    for item in queue.get("items", []):
        if item.get("sample_id") == sample_id:
            queue_entry = item
            break

    # Find in inventory
    inv_entry: dict[str, Any] = {}
    for entry in inventory.get("entries", []):
        if entry.get("sample_id") == sample_id:
            inv_entry = entry
            break

    return {
        "queue": queue_entry,
        "inventory": inv_entry,
        "relative_path": queue_entry.get("relative_path", inv_entry.get("relative_path", "")),
        "sha256": queue_entry.get("sha256", inv_entry.get("sha256", "")),
        "size_bytes": queue_entry.get("size_bytes", inv_entry.get("size_bytes", 0)),
        "file_type": inv_entry.get("guessed_file_type", queue_entry.get("file_type", "")),
        "category": inv_entry.get("category", queue_entry.get("category", "")),
        "tags": inv_entry.get("tags", queue_entry.get("tags", [])),
        "queue_rank": queue_entry.get("rank", -1),
        "allowed_actions": queue_entry.get("allowed_actions", []),
        "forbidden_actions": queue_entry.get("forbidden_actions", []),
    }


def _resolve_binary_path(relative_path: str) -> Path | None:
    """Resolve the full binary path using LOCAL_REVERSE_ROOT."""
    if not relative_path:
        return None
    root = _find_sample_root()
    if not root:
        return None
    full_path = root / relative_path
    return full_path if full_path.exists() else None


def _run_ida_static_triage(
    binary_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run IDA static evidence collection and return parsed results.

    Reuses existing tool_runners and collect_evidence.py.
    Returns a dict with triage fields.
    """
    from .tool_runners import _resolve_ida_executable, _resolve_ida_script

    ida_exec = _resolve_ida_executable("")
    ida_script = _resolve_ida_script("")

    if not ida_exec:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found"}
    if not ida_script:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA script not found"}

    import subprocess

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_out = output_dir / "ida_evidence.json"
    log_out = output_dir / "ida_triage.log"
    db_out = output_dir / "ida_triage.i64"

    # Clean up old DB files
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar = db_out.with_suffix(suffix)
        try:
            sidecar.unlink(missing_ok=True)
        except OSError:
            pass

    cmd = [
        ida_exec,
        "-A",
        f"-L{log_out}",
        f"-o{db_out}",
        f"-S{ida_script}",
        str(binary_path),
    ]

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(evidence_out)
    env["REVERSE_AGENT_IDA_FORCE_FUNCS"] = ""  # No forced funcs for triage

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env=env,
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_TIMEOUT: IDA timed out after 300s"}
    except Exception as exc:
        return {"tool_status": "blocked", "blocked_reason": f"STATIC_TOOL_ERROR: {exc}"}

    # Parse IDA output
    if evidence_out.exists():
        try:
            evidence = _load_json(evidence_out)
            return _parse_ida_evidence(evidence, exit_code)
        except (json.JSONDecodeError, KeyError) as exc:
            return {
                "tool_status": "blocked",
                "blocked_reason": f"STATIC_TOOL_PARSE_ERROR: {exc}",
                "exit_code": exit_code,
            }
    else:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
            "exit_code": exit_code,
        }


def _parse_ida_evidence(evidence: dict[str, Any], exit_code: int) -> dict[str, Any]:
    """Parse IDA evidence JSON into triage summary fields."""
    triage: dict[str, Any] = {
        "tool_status": "success" if exit_code == 0 else "blocked",
        "blocked_reason": "" if exit_code == 0 else f"IDA_EXIT_CODE_{exit_code}",
        "source_tool": "IDA",
        "exit_code": exit_code,
    }

    # Extract interesting strings
    strings = evidence.get("strings", [])
    interesting_strings = []
    for s in strings[:50]:
        if isinstance(s, dict):
            val = s.get("value", s.get("string", ""))
            addr = s.get("address", "")
            if val and len(str(val)) > 1:
                interesting_strings.append({"address": addr, "value": str(val)[:200]})
        elif isinstance(s, str) and len(s) > 1:
            interesting_strings.append({"address": "", "value": s[:200]})
    triage["interesting_strings"] = interesting_strings

    # Extract functions
    functions = evidence.get("functions", [])
    function_names = []
    for f in functions[:30]:
        if isinstance(f, dict):
            name = f.get("name", "")
            addr = f.get("address", "")
            if name:
                function_names.append({"name": name, "address": addr})
        elif isinstance(f, str):
            function_names.append({"name": f, "address": ""})
    triage["functions"] = function_names

    # Extract compare contexts
    compare_contexts = evidence.get("compare_contexts", [])
    triage["compare_contexts"] = compare_contexts[:20]

    # Extract validation function candidates
    val_candidates = evidence.get("validation_function_candidates", [])
    triage["validation_function_candidates"] = val_candidates[:20]

    # Extract solver hints
    solver_hints = evidence.get("solver_hints", [])
    triage["solver_hints"] = solver_hints[:10]

    # Extract decompiler snippets if available
    decompiler_snippets = evidence.get("decompiler_snippets", [])
    triage["decompiler_snippets"] = decompiler_snippets[:10]

    # Extract input APIs
    input_apis = []
    api_patterns = ["scanf", "gets", "cin", "fgets", "read", "recv", "input", "getline"]
    for fn in function_names:
        name = fn.get("name", "").lower()
        for pat in api_patterns:
            if pat in name:
                input_apis.append(fn["name"])
                break
    triage["input_apis"] = list(dict.fromkeys(input_apis))[:20]

    # Build solver profile hypotheses
    hypotheses = []
    if compare_contexts:
        hypotheses.append("string_compare_password_checker")
    if input_apis:
        hypotheses.append("standard_input_based")
    if any("scanf" in fn.get("name", "").lower() for fn in function_names):
        hypotheses.append("scanf_input_validation")
    if any("strcmp" in fn.get("name", "").lower() for fn in function_names):
        hypotheses.append("strcmp_direct_compare")
    triage["solver_profile_hypotheses"] = hypotheses

    return triage


def run_static_triage(
    *,
    sample_id: str,
    queue_path: Path,
    inventory_path: Path,
    artifact_index_path: Path | None,
    out_path: Path,
    mainline: str = "",
) -> dict[str, Any]:
    """Main logic: locate sample, run IDA triage, produce artifact."""
    # Locate sample
    sample_info = _locate_sample(sample_id, queue_path, inventory_path)
    relative_path = sample_info["relative_path"]

    if not relative_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            relative_path="",
            sha256=sample_info["sha256"],
            size_bytes=sample_info["size_bytes"],
            file_type=sample_info["file_type"],
            category=sample_info["category"],
            tags=sample_info["tags"],
            blocked_reason="SAMPLE_NOT_FOUND_IN_QUEUE_OR_INVENTORY",
            mainline=mainline,
        )
        _save_json(out_path, result)
        return result

    # Resolve binary path
    binary_path = _resolve_binary_path(relative_path)
    if not binary_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            relative_path=relative_path,
            sha256=sample_info["sha256"],
            size_bytes=sample_info["size_bytes"],
            file_type=sample_info["file_type"],
            category=sample_info["category"],
            tags=sample_info["tags"],
            blocked_reason="BINARY_NOT_FOUND",
            detail=f"Could not resolve path: {relative_path}",
            mainline=mainline,
        )
        _save_json(out_path, result)
        return result

    # Run IDA static triage
    # Use system temp directory to avoid IDA GetDiskFreeSpaceEx issues
    # with long/unicode paths on NTFS (8.3 short name resolution failures
    # cause IDA to report 0 available disk space and refuse to write DB files).
    import tempfile as _tf
    output_dir = Path(_tf.gettempdir()) / f"reverse_agent_triage_{sample_id}"
    ida_result = _run_ida_static_triage(binary_path, output_dir)

    # Build artifact
    tool_status = ida_result.get("tool_status", "blocked")
    blocked_reason = ida_result.get("blocked_reason", "")

    if tool_status == "blocked":
        result = _blocked_artifact(
            sample_id=sample_id,
            relative_path=relative_path,
            sha256=sample_info["sha256"],
            size_bytes=sample_info["size_bytes"],
            file_type=sample_info["file_type"],
            category=sample_info["category"],
            tags=sample_info["tags"],
            blocked_reason=blocked_reason,
            source_tool=ida_result.get("source_tool", "IDA"),
            mainline=mainline,
        )
        _save_json(out_path, result)
        return result

    # Success - build triage artifact
    recommended_next = "Review triage evidence; consider targeted IDA extraction or solver if compare context found."
    if ida_result.get("compare_contexts"):
        recommended_next = "Compare context found; consider constraint recovery or targeted decompilation."
    elif ida_result.get("solver_profile_hypotheses"):
        recommended_next = f"Solver profile hypotheses: {', '.join(ida_result['solver_profile_hypotheses'][:3])}. Consider targeted extraction."

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": relative_path,
        "analysis_mode": "single_sample_static_triage",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "success",
        "blocked_reason": "",
        "source_tool": ida_result.get("source_tool", "IDA"),
        "sha256": sample_info["sha256"],
        "size_bytes": sample_info["size_bytes"],
        "file_type": sample_info["file_type"],
        "category": sample_info["category"],
        "tags": sample_info["tags"],
        "queue_rank": sample_info["queue_rank"],
        **({"mainline": mainline} if mainline else {}),
        "triage": {
            "input_apis": ida_result.get("input_apis", []),
            "interesting_strings": ida_result.get("interesting_strings", []),
            "functions": ida_result.get("functions", []),
            "compare_contexts": ida_result.get("compare_contexts", []),
            "validation_function_candidates": ida_result.get("validation_function_candidates", []),
            "solver_profile_hypotheses": ida_result.get("solver_profile_hypotheses", []),
            "decompiler_snippets": ida_result.get("decompiler_snippets", []),
            "solver_hints": ida_result.get("solver_hints", []),
        },
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended_next,
    }

    _save_json(out_path, result)
    print(f"static triage: status=success sample_id={sample_id}")
    print(f"  strings: {len(result['triage']['interesting_strings'])}")
    print(f"  functions: {len(result['triage']['functions'])}")
    print(f"  compare_contexts: {len(result['triage']['compare_contexts'])}")
    print(f"  hypotheses: {result['triage']['solver_profile_hypotheses']}")
    return result


def _blocked_artifact(
    *,
    sample_id: str,
    relative_path: str,
    sha256: str,
    size_bytes: int,
    file_type: str,
    category: str,
    tags: list[str],
    blocked_reason: str,
    detail: str = "",
    source_tool: str = "",
    mainline: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": relative_path,
        "analysis_mode": "single_sample_static_triage",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "blocked",
        "blocked_reason": blocked_reason,
        "blocked_detail": detail,
        "source_tool": source_tool,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "file_type": file_type,
        "category": category,
        "tags": tags,
        "triage": {
            "input_apis": [],
            "interesting_strings": [],
            "functions": [],
            "compare_contexts": [],
            "validation_function_candidates": [],
            "solver_profile_hypotheses": [],
        },
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": f"Resolve blocker: {blocked_reason}",
    }
    if mainline:
        result["mainline"] = mainline
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run single-sample static triage using IDA evidence collection.",
    )
    parser.add_argument("--sample-id", required=True, help="Sample ID to triage")
    parser.add_argument("--queue", default="project_state/local_reverse_evaluation_queue.json")
    parser.add_argument("--inventory", default="project_state/local_reverse_inventory.json")
    parser.add_argument("--artifact-index", default="project_state/artifact_index.json")
    parser.add_argument("--mainline", default="", help="Decision mainline to record in artifact (optional)")
    parser.add_argument("--out", default="project_state/local_reverse_cpp1_2f6fcb63_static_triage.json")
    args = parser.parse_args()

    try:
        run_static_triage(
            sample_id=args.sample_id,
            queue_path=Path(args.queue),
            inventory_path=Path(args.inventory),
            artifact_index_path=Path(args.artifact_index),
            out_path=Path(args.out),
            mainline=args.mainline,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
