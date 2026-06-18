"""Single-sample static triage adapter.

Reads a sample from the evaluation queue / inventory, runs IDA static
evidence collection (reusing existing tool_runners / collect_evidence.py),
and produces a compact triage artifact.

Does NOT execute the target binary. Does NOT generate candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TYPE_EVIDENCE_SCHEMA_VERSION = 1
TYPE_EVIDENCE_STATUSES = {
    "not_observed",
    "candidate_static_signal",
    "observed_static_signal",
    "blocked_missing_required_evidence",
}
TYPE_EVIDENCE_PROFILE_IDS = [
    "string_comparison",
    "xor",
    "shift_affine",
    "bit_operations",
    "lookup_table",
    "rc4",
    "des",
    "hash_md5_sha",
    "simple_antidebug",
    "mixed_unknown",
]

TYPE_EVIDENCE_REQUIRED: dict[str, list[str]] = {
    "string_comparison": [
        "compare callsite",
        "operand source",
        "compared value or producer",
    ],
    "xor": [
        "xor operation",
        "xor key or derivation",
        "loop bounds or operand width",
    ],
    "shift_affine": [
        "shift/rotate/affine operation",
        "transform constants",
        "loop structure",
    ],
    "bit_operations": [
        "bit operation sequence",
        "operand source",
        "input-to-compare chain",
    ],
    "lookup_table": [
        "table access",
        "table base",
        "table size",
        "table contents",
    ],
    "rc4": [
        "KSA or PRGA loop",
        "S-box state",
        "key material or derivation",
    ],
    "des": [
        "DES round or S-box pattern",
        "permutation tables or constants",
        "key schedule",
    ],
    "hash_md5_sha": [
        "hash constants or round structure",
        "hash comparison point",
        "bounded input domain",
    ],
    "simple_antidebug": [
        "anti-debug API or SEH/static technique",
        "check location",
        "branch condition",
    ],
    "mixed_unknown": [
        "static triage evidence",
        "observed transform family",
        "reason for remaining unknown",
    ],
}


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _summarize_text(value: str, *, limit: int = 2000) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def _read_tail(path: Path, *, limit: int = 2000) -> str:
    try:
        if not path.exists():
            return ""
        return _summarize_text(path.read_text(encoding="utf-8", errors="replace"), limit=limit)
    except OSError as exc:
        return f"<unable to read log: {exc}>"


def _short_text(value: Any, *, limit: int = 240) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def _flatten_evidence_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(_flatten_evidence_text(item))
        return parts
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.extend(_flatten_evidence_text(item))
        return parts
    return [str(value)]


def _evidence_text_blob(evidence: dict[str, Any], parsed_triage: dict[str, Any]) -> str:
    relevant_fields = [
        "strings",
        "functions",
        "compare_contexts",
        "local_check_contexts",
        "control_id_contexts",
        "string_xrefs",
        "validation_function_candidates",
        "decompiler_snippets",
        "forced_decompiler_snippets",
        "solver_hints",
    ]
    parts: list[str] = []
    for field in relevant_fields:
        parts.extend(_flatten_evidence_text(evidence.get(field)))
        parts.extend(_flatten_evidence_text(parsed_triage.get(field)))
    return "\n".join(parts).lower()


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _profile(status: str, *, observed: list[str] | None = None, missing: list[str] | None = None) -> dict[str, Any]:
    if status not in TYPE_EVIDENCE_STATUSES:
        raise ValueError(f"invalid type_evidence status: {status}")
    return {
        "status": status,
        "required_evidence": [],
        "observed_evidence": observed or [],
        "missing_evidence": missing or [],
        "promotion_blockers": [],
    }


def _profile_with_requirements(
    profile_id: str,
    status: str,
    *,
    observed: list[str] | None = None,
    missing: list[str] | None = None,
    blockers: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = _profile(status, observed=observed, missing=missing)
    profile["required_evidence"] = list(TYPE_EVIDENCE_REQUIRED[profile_id])
    profile["promotion_blockers"] = blockers or [
        "static_verified is not emitted by static triage schema normalization",
        "filename/sample_id/category/keyword/solver-module hits are not sufficient",
    ]
    if extra:
        profile.update(extra)
    return profile


def _default_type_evidence(*, source: str = "adapter_schema_default") -> dict[str, Any]:
    profiles = {
        profile_id: _profile_with_requirements(
            profile_id,
            "not_observed",
            missing=list(TYPE_EVIDENCE_REQUIRED[profile_id]),
        )
        for profile_id in TYPE_EVIDENCE_PROFILE_IDS
    }
    profiles["hash_md5_sha"]["bounded_domain_required"] = True
    profiles["hash_md5_sha"]["bounded_domain_evidence"] = {
        "length": {"observed": False, "evidence": ""},
        "charset": {"observed": False, "evidence": ""},
        "format": {"observed": False, "evidence": ""},
    }
    profiles["lookup_table"]["table_evidence"] = {
        "access": {"observed": False, "evidence": ""},
        "base": {"observed": False, "evidence": ""},
        "size": {"observed": False, "evidence": ""},
        "contents": {"observed": False, "evidence": ""},
    }
    return {
        "schema_version": TYPE_EVIDENCE_SCHEMA_VERSION,
        "source": source,
        "status_vocabulary": sorted(TYPE_EVIDENCE_STATUSES),
        "type_tag_observations": [],
        "profiles": profiles,
        "promotion_safety": {
            "emits_static_verified": False,
            "metadata_only_is_not_static_evidence": True,
            "keyword_hits_are_not_static_verification": True,
            "filename_sample_id_category_solver_module_are_not_sufficient": True,
            "runtime_validation_required_for_confirmed_candidate": True,
        },
    }


def _extract_type_evidence(evidence: dict[str, Any], parsed_triage: dict[str, Any]) -> dict[str, Any]:
    """Normalize static type evidence from already-collected IDA evidence.

    This is a pure schema helper. It does not run external tools and it never
    emits ``static_verified``.
    """
    result = _default_type_evidence(source="ida_evidence_adapter")
    profiles = result["profiles"]
    observations: list[dict[str, str]] = []
    text = _evidence_text_blob(evidence, parsed_triage)

    compare_contexts = parsed_triage.get("compare_contexts") or evidence.get("compare_contexts") or []
    if compare_contexts or _has_any(text, ["strcmp", "memcmp", "lstrcmp", "strncmp"]):
        observed = ["compare context or compare API name observed"]
        if compare_contexts:
            observed.append(f"compare_context_count={len(compare_contexts)}")
        profiles["string_comparison"] = _profile_with_requirements(
            "string_comparison",
            "candidate_static_signal",
            observed=observed,
            missing=["operand source", "compared value or producer"],
        )
        observations.append({"type_id": "string_comparison", "status": "candidate_static_signal"})

    if _has_any(text, [" xor ", "\txor", "^=", " xor(", "xor loop", "xor key"]):
        profiles["xor"] = _profile_with_requirements(
            "xor",
            "candidate_static_signal",
            observed=["xor operation keyword or instruction text observed"],
            missing=["xor key or derivation", "loop bounds or operand width"],
        )
        observations.append({"type_id": "xor", "status": "candidate_static_signal"})

    if _has_any(text, [" shl ", " shr ", " rol ", " ror ", "shift", "rotate", "affine", "mod "]) or (
        _has_any(text, ["imul", "mul"]) and _has_any(text, [" add ", "+"])
    ):
        profiles["shift_affine"] = _profile_with_requirements(
            "shift_affine",
            "candidate_static_signal",
            observed=["shift/rotate/affine transform text observed"],
            missing=["complete transform constants", "loop structure"],
        )
        observations.append({"type_id": "shift_affine", "status": "candidate_static_signal"})

    if _has_any(text, [" xor ", "\txor", " shl ", " shr ", " rol ", " ror ", " and ", " or ", " not "]):
        profiles["bit_operations"] = _profile_with_requirements(
            "bit_operations",
            "candidate_static_signal",
            observed=["bitwise operation text observed"],
            missing=["operand source", "input-to-compare chain"],
        )
        observations.append({"type_id": "bit_operations", "status": "candidate_static_signal"})

    table_access = _has_any(text, ["lookup", "table", "array[", "s-box", "sbox", "index"])
    table_base = _has_any(text, ["base address", "table base", "base=0x", "base 0x"])
    table_size = _has_any(text, ["table size", "size=256", "256-byte", "size 256"])
    table_contents = _has_any(text, ["table contents", "contents=", "dumped table", "s-box contents"])
    if table_access:
        missing = []
        if not table_base:
            missing.append("table base")
        if not table_size:
            missing.append("table size")
        if not table_contents:
            missing.append("table contents")
        profiles["lookup_table"] = _profile_with_requirements(
            "lookup_table",
            "observed_static_signal" if not missing else "blocked_missing_required_evidence",
            observed=["lookup table or indexed table access text observed"],
            missing=missing,
            extra={
                "table_evidence": {
                    "access": {"observed": True, "evidence": "lookup/table/index text observed"},
                    "base": {"observed": table_base, "evidence": "base text observed" if table_base else ""},
                    "size": {"observed": table_size, "evidence": "size text observed" if table_size else ""},
                    "contents": {"observed": table_contents, "evidence": "contents text observed" if table_contents else ""},
                }
            },
        )
        observations.append({"type_id": "lookup_table", "status": profiles["lookup_table"]["status"]})

    rc4_parts = {
        "ksa_or_prga": _has_any(text, ["ksa", "prga", "key scheduling", "pseudo-random generation"]),
        "sbox": _has_any(text, ["s-box", "sbox", "256-byte state", "state array"]),
        "key": _has_any(text, ["rc4 key", "key material", "key derivation"]),
    }
    if any(rc4_parts.values()) or _has_any(text, ["rc4"]):
        profiles["rc4"] = _profile_with_requirements(
            "rc4",
            "candidate_static_signal",
            observed=[name for name, ok in rc4_parts.items() if ok] or ["rc4 text observed"],
            missing=[name for name, ok in rc4_parts.items() if not ok],
        )
        observations.append({"type_id": "rc4", "status": "candidate_static_signal"})

    des_parts = {
        "round_or_sbox": _has_any(text, ["des round", "s-box", "sbox"]),
        "permutation": _has_any(text, ["permutation", "initial permutation", "pc1", "pc2", "ip table", "fp table"]),
        "key_schedule": _has_any(text, ["key schedule", "subkey", "subkeys"]),
    }
    if any(des_parts.values()) or _has_any(text, [" des "]):
        profiles["des"] = _profile_with_requirements(
            "des",
            "candidate_static_signal",
            observed=[name for name, ok in des_parts.items() if ok] or ["des text observed"],
            missing=[name for name, ok in des_parts.items() if not ok],
        )
        observations.append({"type_id": "des", "status": "candidate_static_signal"})

    hash_signal = _has_any(text, ["sha", "sha-256", "sha256", "md5", "67452301", "6a09e667", "hash"])
    domain = {
        "length": {"observed": _has_any(text, ["length", "len=", "input length"]), "evidence": ""},
        "charset": {"observed": _has_any(text, ["charset", "alphabet", "digits", "lowercase", "uppercase"]), "evidence": ""},
        "format": {"observed": _has_any(text, ["format", "prefix", "flag{", "regex"]), "evidence": ""},
    }
    for key, item in domain.items():
        if item["observed"]:
            item["evidence"] = f"{key} evidence text observed"
    if hash_signal:
        domain_present = any(item["observed"] for item in domain.values())
        profiles["hash_md5_sha"] = _profile_with_requirements(
            "hash_md5_sha",
            "candidate_static_signal" if domain_present else "blocked_missing_required_evidence",
            observed=["hash constants or hash text observed"] + [
                f"bounded_domain_{key}" for key, item in domain.items() if item["observed"]
            ],
            missing=[] if domain_present else ["bounded input domain"],
            extra={
                "bounded_domain_required": True,
                "bounded_domain_evidence": domain,
                "solver_ready": False,
            },
        )
        observations.append({"type_id": "hash_md5_sha", "status": profiles["hash_md5_sha"]["status"]})

    if _has_any(text, ["isdebuggerpresent", "ntqueryinformationprocess", "beingdebugged", "int 2d", "int 3", "seh", "anti-debug", "antidebug"]):
        profiles["simple_antidebug"] = _profile_with_requirements(
            "simple_antidebug",
            "candidate_static_signal",
            observed=["anti-debug API/SEH/static technique text observed"],
            missing=["check location", "branch condition"],
            blockers=[
                "debugger execution is outside this schema helper",
                "static signal is not a bypass or runtime validation",
            ],
        )
        observations.append({"type_id": "simple_antidebug", "status": "candidate_static_signal"})

    if text and not observations:
        profiles["mixed_unknown"] = _profile_with_requirements(
            "mixed_unknown",
            "candidate_static_signal",
            observed=["static triage text exists but no specific type profile matched"],
            missing=["observed transform family"],
        )
        observations.append({"type_id": "mixed_unknown", "status": "candidate_static_signal"})
    elif observations:
        profiles["mixed_unknown"] = _profile_with_requirements(
            "mixed_unknown",
            "not_observed",
            missing=["reason for remaining unknown"],
            blockers=["specific candidate signals were observed; do not keep mixed_unknown without a later triage reason"],
        )

    result["type_tag_observations"] = observations
    return result


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


def _tool_provenance(
    *,
    ida_exec: str = "",
    ida_script: str = "",
    evidence_out: Path | None = None,
    log_out: Path | None = None,
    db_out: Path | None = None,
    command_args: list[str] | None = None,
    exit_code: int | None = None,
    stdout: str = "",
    stderr: str = "",
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    log_tail = _read_tail(log_out) if log_out else ""
    return {
        "source_tool": "IDA",
        "ida_executable": ida_exec,
        "ida_script": ida_script,
        "resolver": {
            "ida_executable_user_path": "",
            "ida_script_user_path": "",
            "ida_executable_resolved": bool(ida_exec),
            "ida_script_resolved": bool(ida_script),
        },
        "command": " ".join(shlex.quote(part) for part in command_args) if command_args else "",
        "command_args": command_args or [],
        "timeout_seconds": timeout_seconds,
        "exit_code": exit_code,
        "expected_evidence_path": str(evidence_out) if evidence_out else "",
        "evidence_exists": bool(evidence_out and evidence_out.exists()),
        "log_path": str(log_out) if log_out else "",
        "log_exists": bool(log_out and log_out.exists()),
        "log_tail": log_tail,
        "database_path": str(db_out) if db_out else "",
        "stdout_summary": _summarize_text(stdout),
        "stderr_summary": _summarize_text(stderr),
    }


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
    provenance = _tool_provenance(ida_exec=ida_exec, ida_script=ida_script)

    if not ida_exec:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found",
            "source_tool": "IDA",
            "tool_provenance": provenance,
        }
    if not ida_script:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA script not found",
            "source_tool": "IDA",
            "tool_provenance": provenance,
        }

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
    provenance = _tool_provenance(
        ida_exec=ida_exec,
        ida_script=ida_script,
        evidence_out=evidence_out,
        log_out=log_out,
        db_out=db_out,
        command_args=cmd,
    )

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(evidence_out)
    env["REVERSE_AGENT_IDA_FORCE_FUNCS"] = ""  # No forced funcs for triage

    stdout = ""
    stderr = ""
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
        stdout = result.stdout or ""
        stderr = result.stderr or ""
    except subprocess.TimeoutExpired:
        provenance = _tool_provenance(
            ida_exec=ida_exec,
            ida_script=ida_script,
            evidence_out=evidence_out,
            log_out=log_out,
            db_out=db_out,
            command_args=cmd,
            exit_code=None,
        )
        provenance["timeout"] = True
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_TIMEOUT: IDA timed out after 300s",
            "source_tool": "IDA",
            "tool_provenance": provenance,
        }
    except Exception as exc:
        provenance["exception"] = repr(exc)
        return {
            "tool_status": "blocked",
            "blocked_reason": f"STATIC_TOOL_ERROR: {exc}",
            "source_tool": "IDA",
            "tool_provenance": provenance,
        }

    provenance = _tool_provenance(
        ida_exec=ida_exec,
        ida_script=ida_script,
        evidence_out=evidence_out,
        log_out=log_out,
        db_out=db_out,
        command_args=cmd,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )

    # Parse IDA output
    if evidence_out.exists():
        try:
            evidence = _load_json(evidence_out)
            parsed = _parse_ida_evidence(evidence, exit_code)
            parsed["tool_provenance"] = provenance
            return parsed
        except (json.JSONDecodeError, KeyError) as exc:
            return {
                "tool_status": "blocked",
                "blocked_reason": f"STATIC_TOOL_PARSE_ERROR: {exc}",
                "exit_code": exit_code,
                "source_tool": "IDA",
                "tool_provenance": provenance,
            }
    else:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
            "exit_code": exit_code,
            "source_tool": "IDA",
            "tool_provenance": provenance,
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
    triage["type_evidence"] = _extract_type_evidence(evidence, triage)

    return triage


def _infer_source_run(artifact_index_path: Path | None) -> str:
    decision_path = (
        artifact_index_path.parent / "decision_packet.md"
        if artifact_index_path is not None
        else Path("project_state/decision_packet.md")
    )
    if not decision_path.exists():
        return ""
    text = decision_path.read_text(encoding="utf-8", errors="replace")
    marker = "```json decision_meta"
    start = text.find(marker)
    if start < 0:
        return ""
    start = text.find("{", start)
    end = text.find("```", start)
    if start < 0 or end < 0:
        return ""
    try:
        meta = json.loads(text[start:end].strip())
    except json.JSONDecodeError:
        return ""
    return str(meta.get("round_id", "")).strip()


def _update_artifact_index(
    *,
    artifact_index_path: Path | None,
    sample_id: str,
    out_path: Path,
    artifact: dict[str, Any],
    source_run: str,
) -> None:
    if artifact_index_path is None:
        return
    index = _load_json(artifact_index_path) if artifact_index_path.exists() else {}
    latest = index.setdefault("latest_artifacts_v2", {})
    data = out_path.read_bytes()
    key = f"local_reverse_{sample_id}_static_triage"
    latest[key] = {
        "freshness": "current",
        "kind": "local_reverse_single_sample_static_triage",
        "modified_at": artifact.get("generated_at", _now_iso()),
        "path": str(out_path).replace("\\", "/"),
        "sample_id": sample_id,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "source_run": source_run,
        "tool_status": artifact.get("tool_status", ""),
    }
    _save_json(artifact_index_path, index)


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
    source_run = _infer_source_run(artifact_index_path)
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
            source_run=source_run,
        )
        _save_json(out_path, result)
        _update_artifact_index(
            artifact_index_path=artifact_index_path,
            sample_id=sample_id,
            out_path=out_path,
            artifact=result,
            source_run=source_run,
        )
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
            source_run=source_run,
        )
        _save_json(out_path, result)
        _update_artifact_index(
            artifact_index_path=artifact_index_path,
            sample_id=sample_id,
            out_path=out_path,
            artifact=result,
            source_run=source_run,
        )
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
            source_run=source_run,
            tool_provenance=ida_result.get("tool_provenance", {}),
            queue_rank=sample_info["queue_rank"],
            allowed_actions=sample_info["allowed_actions"],
            forbidden_actions=sample_info["forbidden_actions"],
        )
        _save_json(out_path, result)
        _update_artifact_index(
            artifact_index_path=artifact_index_path,
            sample_id=sample_id,
            out_path=out_path,
            artifact=result,
            source_run=source_run,
        )
        print(f"static triage: status=blocked sample_id={sample_id}")
        print(f"  blocked_reason: {blocked_reason}")
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
        "allowed_actions": sample_info["allowed_actions"],
        "forbidden_actions": sample_info["forbidden_actions"],
        "source_run": source_run,
        "tool_provenance": ida_result.get("tool_provenance", {}),
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
            "type_evidence": ida_result.get("type_evidence", _default_type_evidence()),
        },
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended_next,
    }

    _save_json(out_path, result)
    _update_artifact_index(
        artifact_index_path=artifact_index_path,
        sample_id=sample_id,
        out_path=out_path,
        artifact=result,
        source_run=source_run,
    )
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
    source_run: str = "",
    tool_provenance: dict[str, Any] | None = None,
    queue_rank: int | None = None,
    allowed_actions: list[str] | None = None,
    forbidden_actions: list[str] | None = None,
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
        "source_run": source_run,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "file_type": file_type,
        "category": category,
        "tags": tags,
        "queue_rank": queue_rank,
        "allowed_actions": allowed_actions or [],
        "forbidden_actions": forbidden_actions or [],
        "tool_provenance": tool_provenance or {},
        "triage": {
            "input_apis": [],
            "interesting_strings": [],
            "functions": [],
            "compare_contexts": [],
            "validation_function_candidates": [],
            "solver_profile_hypotheses": [],
            "decompiler_snippets": [],
            "solver_hints": [],
            "type_evidence": _default_type_evidence(source="blocked_artifact_default"),
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
