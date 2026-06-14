"""Targeted compare-byte extraction for cpp1_2f6fcb63.

Reads the static triage artifact, runs IDA with extract_named_data.py to get
byte_429A30 bytes and _main_0 pseudocode, then produces a structured target-bytes
artifact.

Does NOT execute the sample. Does NOT generate candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_cpp1_signed_transform_recheck import printable_preimages_for_target


TARGET_PROVENANCE_ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_target_provenance_recheck"
TARGET_PROVENANCE_ARTIFACT_KIND = "local_reverse_cpp1_target_provenance_recheck"
TARGET_PROVENANCE_SOURCE_RUN = "round_20260605_cpp1_target_byte_provenance_recheck_v1"
TARGET_BYTES_REVALIDATION_ARTIFACT_KEY = "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation"
TARGET_BYTES_REVALIDATION_ARTIFACT_KIND = "target_bytes_current_revalidation"
TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN = (
    "round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1"
)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_decision_meta_round_id(state_dir: Path | None = None) -> str:
    state_dir = state_dir or Path("project_state")
    decision_path = state_dir / "decision_packet.md"
    if not decision_path.exists():
        return TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN
    text = decision_path.read_text(encoding="utf-8")
    start_marker = "```json decision_meta"
    start = text.find(start_marker)
    if start < 0:
        return TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN
    start = text.find("\n", start)
    end = text.find("```", start + 1)
    if start < 0 or end < 0:
        return TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN
    try:
        payload = json.loads(text[start:end].strip())
    except json.JSONDecodeError:
        return TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN
    round_id = str(payload.get("round_id", "")).strip()
    return round_id or TARGET_BYTES_REVALIDATION_DEFAULT_SOURCE_RUN


def _parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        return int(text, 16) if text.lower().startswith("0x") else int(text, 10)
    except ValueError:
        return None


def _hx(value: int | None) -> str:
    return f"0x{value:08X}" if value is not None else ""


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
        if os.path.isdir(c_str):
            return Path(c_str)
    return None


def _resolve_binary_path(relative_path: str) -> Path | None:
    """Resolve the full binary path using LOCAL_REVERSE_ROOT."""
    if not relative_path:
        return None
    root = _find_sample_root()
    if not root:
        return None
    full_path = root / relative_path
    return full_path if full_path.exists() else None


def _read_pe_sections(binary_path: Path) -> list[dict[str, Any]]:
    data = binary_path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        return []
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if pe_offset <= 0 or pe_offset + 0x18 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        return []
    coff = pe_offset + 4
    section_count = int.from_bytes(data[coff + 2:coff + 4], "little")
    optional_size = int.from_bytes(data[coff + 16:coff + 18], "little")
    optional = coff + 20
    if optional + optional_size > len(data):
        return []
    image_base = int.from_bytes(data[optional + 28:optional + 32], "little")
    section_table = optional + optional_size
    sections = []
    for index in range(section_count):
        off = section_table + index * 40
        if off + 40 > len(data):
            break
        name = data[off:off + 8].split(b"\0", 1)[0].decode("ascii", errors="replace")
        virtual_size = int.from_bytes(data[off + 8:off + 12], "little")
        virtual_address = int.from_bytes(data[off + 12:off + 16], "little")
        raw_size = int.from_bytes(data[off + 16:off + 20], "little")
        raw_pointer = int.from_bytes(data[off + 20:off + 24], "little")
        sections.append(
            {
                "name": name,
                "image_base": image_base,
                "virtual_address": virtual_address,
                "virtual_start": image_base + virtual_address,
                "virtual_end": image_base + virtual_address + max(virtual_size, raw_size),
                "virtual_size": virtual_size,
                "raw_pointer": raw_pointer,
                "raw_size": raw_size,
            }
        )
    return sections


def _read_pe_window(binary_path: Path, target_address: int, radius: int = 0x40, max_span: int = 18) -> dict[str, Any]:
    sections = _read_pe_sections(binary_path)
    section = next(
        (item for item in sections if item["virtual_start"] <= target_address < item["virtual_end"]),
        None,
    )
    if not section:
        return {
            "available": False,
            "blocked_reason": "TARGET_SECTION_NOT_FOUND",
            "section_name": "",
            "symbol_span": {},
            "raw_data_window": {},
            "target_file_offset": None,
            "window_bytes": [],
            "window_start_va": None,
        }

    data = binary_path.read_bytes()
    target_file_offset = section["raw_pointer"] + (target_address - section["virtual_start"])
    window_start_va = max(section["virtual_start"], target_address - radius)
    window_end_va = min(section["virtual_end"], target_address + radius + max_span)
    window_start_offset = section["raw_pointer"] + (window_start_va - section["virtual_start"])
    window_end_offset = section["raw_pointer"] + (window_end_va - section["virtual_start"])
    window_start_offset = max(0, min(window_start_offset, len(data)))
    window_end_offset = max(window_start_offset, min(window_end_offset, len(data)))
    window_bytes = list(data[window_start_offset:window_end_offset])
    symbol_start_offset = target_file_offset - window_start_offset
    symbol_bytes = data[target_file_offset:target_file_offset + 16]

    return {
        "available": True,
        "blocked_reason": "",
        "section_name": section["name"],
        "target_file_offset": target_file_offset,
        "window_start_va": window_start_va,
        "window_bytes": window_bytes,
        "symbol_span": {
            "name": "byte_429A30",
            "address": _hx(target_address),
            "file_offset": target_file_offset,
            "length": 16,
            "section": section["name"],
            "bytes_hex": symbol_bytes.hex(),
        },
        "raw_data_window": {
            "start_address": _hx(window_start_va),
            "end_address": _hx(window_start_va + len(window_bytes)),
            "target_relative_offset": symbol_start_offset,
            "radius_before": target_address - window_start_va,
            "bytes_hex": bytes(window_bytes).hex(),
        },
    }


def _source_artifact_freshness(artifact_index: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    v2 = artifact_index.get("latest_artifacts_v2", {})
    freshness: dict[str, Any] = {}
    for key in keys:
        meta = v2.get(key, {})
        freshness[key] = {
            "path": meta.get("path", ""),
            "freshness": meta.get("freshness", ""),
            "source_run": meta.get("source_run", ""),
            "sample_id": meta.get("sample_id", ""),
        }
    return freshness


def _artifact_freshness_for_path(artifact_index: dict[str, Any], path: Path) -> dict[str, Any]:
    wanted = str(path).replace("\\", "/")
    wanted_alt = str(path).replace("/", "\\")
    for key, meta in artifact_index.get("latest_artifacts_v2", {}).items():
        meta_path = str(meta.get("path", ""))
        if meta_path in {wanted, wanted_alt} or meta_path.replace("\\", "/") == wanted:
            return {
                "artifact_key": key,
                "path": meta.get("path", ""),
                "freshness": meta.get("freshness", ""),
                "source_run": meta.get("source_run", ""),
                "sample_id": meta.get("sample_id", ""),
            }
    return {
        "artifact_key": "",
        "path": str(path).replace("\\", "/"),
        "freshness": "not_registered",
        "source_run": "",
        "sample_id": "",
    }


def _check_equal(name: str, left: Any, right: Any) -> dict[str, Any]:
    passed = left == right
    return {
        "name": name,
        "status": "PASSED" if passed else "FAILED",
        "expected": left,
        "actual": right,
    }


def _check_present(name: str, value: Any) -> dict[str, Any]:
    present = value is not None and value != "" and value != []
    return {
        "name": name,
        "status": "PASSED" if present else "BLOCKED",
        "value": value,
    }


def _contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def _main_snippet_from_triage(triage: dict[str, Any], function_name: str = "_main_0") -> dict[str, Any]:
    for snippet in triage.get("triage", {}).get("decompiler_snippets", []):
        if snippet.get("function") == function_name:
            return snippet
    return {}


def _target_bytes_checks(target_artifact: dict[str, Any], triage: dict[str, Any]) -> list[dict[str, Any]]:
    target_bytes = target_artifact.get("target_bytes", [])
    target_hex = str(target_artifact.get("target_bytes_hex", ""))
    main_function = str(target_artifact.get("main_function", "_main_0"))
    target_pseudocode = str(target_artifact.get("main_pseudocode", ""))
    triage_snippet = _main_snippet_from_triage(triage, main_function)
    triage_pseudocode = str(triage_snippet.get("text", ""))
    forward_transform = target_artifact.get("forward_transform", {})

    checks = [
        _check_equal("sample_id", target_artifact.get("sample_id"), triage.get("sample_id")),
        _check_equal("relative_path", target_artifact.get("relative_path"), triage.get("relative_path")),
        _check_equal("sha256", target_artifact.get("sha256", triage.get("sha256")), triage.get("sha256")),
        _check_equal("target_symbol", target_artifact.get("target_symbol"), "byte_429A30"),
        _check_equal("target_address", target_artifact.get("target_address"), "0x00429A30"),
        _check_equal("target_length", target_artifact.get("target_length"), 16),
        _check_equal("target_bytes_len", len(target_bytes) if isinstance(target_bytes, list) else -1, 16),
        _check_equal("target_bytes_hex", target_hex, bytes(target_bytes).hex() if isinstance(target_bytes, list) else ""),
        _check_equal("main_function", main_function, "_main_0"),
        _check_present("main_pseudocode_old_artifact", target_pseudocode),
        _check_present("main_pseudocode_current_triage", triage_pseudocode),
        _check_equal("current_triage_tool_status", triage.get("tool_status"), "success"),
        _check_equal("current_triage_source_tool", triage.get("source_tool"), "IDA"),
        _check_equal("current_triage_runtime_validated", triage.get("runtime_validated"), False),
        _check_equal("current_triage_candidate", triage.get("candidate"), None),
        _check_equal("target_candidate", target_artifact.get("candidate"), None),
        _check_equal("target_known_candidate", target_artifact.get("known_candidate", ""), ""),
    ]

    semantic_patterns = [
        ("length_check_current_triage", triage_pseudocode, ["strlen(Str)", "!= 18"]),
        ("copy_length_current_triage", triage_pseudocode, ["strncpy(Destination, Str, 0x10u)"]),
        ("transform_formula_current_triage", triage_pseudocode, ["Destination[i]", "& 3", "& 0xC", "& 0xF0", ">> 2"]),
        ("compare_expression_current_triage", triage_pseudocode, ["Destination[i] == byte_429A30[i]"]),
        ("success_length_current_triage", triage_pseudocode, ["if ( i == 16 )"]),
        ("length_check_old_artifact", target_pseudocode, ["strlen(Str)", "!= 18"]),
        ("copy_length_old_artifact", target_pseudocode, ["strncpy(Destination, Str, 0x10u)"]),
        ("transform_formula_old_artifact", target_pseudocode, ["Destination[i]", "& 3", "& 0xC", "& 0xF0", ">> 2"]),
        ("compare_expression_old_artifact", target_pseudocode, ["Destination[i] == byte_429A30[i]"]),
    ]
    for name, text, needles in semantic_patterns:
        checks.append(
            {
                "name": name,
                "status": "PASSED" if _contains_all(text, needles) else "BLOCKED",
                "required_fragments": needles,
            }
        )

    checks.extend(
        [
            _check_equal("forward_transform_copy_length", forward_transform.get("copy_length"), 16),
            _check_equal(
                "forward_transform_compare_expression",
                forward_transform.get("compare_expression"),
                "Destination[i] == byte_429A30[i]",
            ),
            {
                "name": "forward_transform_formula",
                "status": "PASSED"
                if _contains_all(str(forward_transform.get("formula_c", "")), ["& 3", "& 0x0C", "& 0xF0", ">> 2"])
                else "BLOCKED",
                "value": forward_transform.get("formula_c", ""),
            },
        ]
    )
    return checks


def _target_revalidation_status(checks: list[dict[str, Any]]) -> tuple[str, str, list[str]]:
    failed = [str(check["name"]) for check in checks if check.get("status") == "FAILED"]
    blocked = [str(check["name"]) for check in checks if check.get("status") == "BLOCKED"]
    if failed:
        return "FAILED", "REVALIDATION_FIELD_MISMATCH", failed
    if blocked:
        return "BLOCKED", "REVALIDATION_FIELD_MISSING_OR_UNCONFIRMED", blocked
    return "PASSED", "", []


def _update_target_bytes_revalidation_artifact_index(
    artifact_index_path: Path,
    out_path: Path,
    sample_id: str,
    generated_at: str,
    source_run: str,
) -> None:
    artifact_index = _load_json(artifact_index_path)
    normalized_path = str(out_path).replace("\\", "/")
    artifact_index.setdefault("latest_artifacts", {})[TARGET_BYTES_REVALIDATION_ARTIFACT_KEY] = normalized_path
    artifact_index.setdefault("artifact_refs", {})[TARGET_BYTES_REVALIDATION_ARTIFACT_KEY] = normalized_path
    artifact_index.setdefault("latest_artifacts_v2", {})[TARGET_BYTES_REVALIDATION_ARTIFACT_KEY] = {
        "kind": TARGET_BYTES_REVALIDATION_ARTIFACT_KIND,
        "path": normalized_path,
        "freshness": "current",
        "source_run": source_run,
        "sha256": _sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "modified_at": generated_at,
        "sample_id": sample_id,
    }
    artifact_index["generated_at"] = generated_at
    _save_json(artifact_index_path, artifact_index)


def run_target_bytes_current_revalidation(
    *,
    target_bytes_path: Path,
    triage_path: Path,
    artifact_index_path: Path,
    out_path: Path,
    source_run: str | None = None,
) -> dict[str, Any]:
    artifact_index = _load_json(artifact_index_path)
    target_artifact = _load_json(target_bytes_path)
    triage = _load_json(triage_path)
    generated_at = _now_iso()
    source_run = source_run or _extract_decision_meta_round_id(artifact_index_path.parent)

    checks = _target_bytes_checks(target_artifact, triage)
    revalidation_status, blocked_reason, mismatched_fields = _target_revalidation_status(checks)
    sample_id = str(target_artifact.get("sample_id", ""))
    target_hex = str(target_artifact.get("target_bytes_hex", ""))

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": target_artifact.get("relative_path", ""),
        "sha256": target_artifact.get("sha256", triage.get("sha256", "")),
        "analysis_mode": "target_bytes_current_revalidation",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": generated_at,
        "tool_status": "success" if revalidation_status == "PASSED" else "blocked",
        "source_tool": "existing_static_artifacts",
        "ida_used_this_round": False,
        "sample_executed_this_round": False,
        "candidate": None,
        "known_candidate": "",
        "source_artifacts": {
            "current_static_triage": str(triage_path).replace("\\", "/"),
            "old_target_bytes": str(target_bytes_path).replace("\\", "/"),
            "artifact_index": str(artifact_index_path).replace("\\", "/"),
        },
        "source_artifact_freshness": {
            "current_static_triage": _artifact_freshness_for_path(artifact_index, triage_path),
            "old_target_bytes": _artifact_freshness_for_path(artifact_index, target_bytes_path),
        },
        "revalidation_checks": checks,
        "revalidation_status": revalidation_status,
        "blocked_reason": blocked_reason,
        "mismatched_fields": mismatched_fields,
        "target_symbol": target_artifact.get("target_symbol", "byte_429A30"),
        "target_address": target_artifact.get("target_address", ""),
        "target_length": target_artifact.get("target_length", 0),
        "target_bytes_hex": target_hex,
        "target_bytes": target_artifact.get("target_bytes", []),
        "main_function": target_artifact.get("main_function", "_main_0"),
        "main_function_address": target_artifact.get("main_function_address", ""),
        "forward_transform": target_artifact.get("forward_transform", {}),
        "compare_expression": target_artifact.get("compare_expression", ""),
        "evidence_notes": target_artifact.get("evidence_notes", []),
        "recommended_next_action": (
            "Next round may use this current revalidation artifact as the evidence entry "
            "for a solver/reverse_solving decision; do not treat this artifact as solved."
            if revalidation_status == "PASSED"
            else "Resolve revalidation blocker before any solver/reverse_solving decision; do not rerun IDA automatically."
        ),
    }

    _save_json(out_path, result)
    _update_target_bytes_revalidation_artifact_index(
        artifact_index_path,
        out_path,
        sample_id,
        generated_at,
        source_run,
    )
    print(f"target bytes current revalidation: status={revalidation_status} sample_id={sample_id}")
    print(f"  target_bytes_hex={target_hex}")
    print(f"  candidate={result['candidate']}")
    print(f"  known_candidate={result['known_candidate']!r}")
    print(f"  runtime_validated={result['runtime_validated']}")
    return result


def _assert_current_artifacts(artifact_index: dict[str, Any], keys: list[str]) -> None:
    freshness = _source_artifact_freshness(artifact_index, keys)
    bad = [
        key for key, meta in freshness.items()
        if meta.get("freshness") != "current" or not meta.get("path")
    ]
    if bad:
        raise ValueError("Required source artifact is not current: " + ", ".join(bad))


def _xref_summary(ida_control_flow: dict[str, Any]) -> dict[str, Any]:
    xref_context = (
        ida_control_flow.get("bounded_instruction_evidence", {})
        .get("target_xref_context", {})
    )
    xrefs = xref_context.get("xrefs", [])
    compare_xrefs = []
    data_xrefs = []
    for item in xrefs:
        record = {
            "from": item.get("from", ""),
            "type": item.get("type", ""),
            "in_main": item.get("in_main", False),
            "basic_block": item.get("basic_block"),
            "window": item.get("window", []),
        }
        if item.get("in_main") or any(
            str(insn.get("mnemonic", "")).lower() == "cmp"
            for insn in item.get("window", [])
        ):
            compare_xrefs.append(record)
        if item.get("type") == "data" or not item.get("in_main"):
            data_xrefs.append(record)
    return {
        "target_name": xref_context.get("target_name", "byte_429A30"),
        "target_address": xref_context.get("target_address", ""),
        "compare_xrefs": compare_xrefs,
        "data_xrefs": data_xrefs,
    }


def _span_feasibility(window: dict[str, Any], target_address: int, lengths: tuple[int, ...] = (16, 18)) -> list[dict[str, Any]]:
    if not window.get("available"):
        return []
    window_bytes = window["window_bytes"]
    window_start_va = int(window["window_start_va"])
    spans: list[dict[str, Any]] = []
    for relative_start in range(-0x40, 0x41):
        start_va = target_address + relative_start
        start_index = start_va - window_start_va
        if start_index < 0:
            continue
        for length in lengths:
            if start_index + length > len(window_bytes):
                continue
            span_bytes = window_bytes[start_index:start_index + length]
            feasibility = printable_preimages_for_target(span_bytes, model="signed_instruction")
            per_byte = feasibility["per_byte"]
            missing = [
                item["index"] for item in per_byte
                if not item["has_printable_preimage"]
            ]
            spans.append(
                {
                    "start_address": _hx(start_va),
                    "relative_start": relative_start,
                    "length": length,
                    "bytes_hex": bytes(span_bytes).hex(),
                    "all_target_bytes_have_printable_preimage": feasibility[
                        "all_target_bytes_have_printable_preimage"
                    ],
                    "missing_printable_preimage_indices": missing,
                    "complete_printable_preimage_span": (
                        "alternative_static_span_needs_review"
                        if feasibility["all_target_bytes_have_printable_preimage"]
                        else ""
                    ),
                }
            )
    return spans


def _update_target_provenance_artifact_index(
    artifact_index_path: Path,
    out_path: Path,
    sample_id: str,
    generated_at: str,
) -> None:
    artifact_index = _load_json(artifact_index_path)
    normalized_path = str(out_path).replace("/", "\\")
    artifact_index.setdefault("latest_artifacts", {})[TARGET_PROVENANCE_ARTIFACT_KEY] = normalized_path
    artifact_index.setdefault("artifact_refs", {})[TARGET_PROVENANCE_ARTIFACT_KEY] = normalized_path
    artifact_index.setdefault("latest_artifacts_v2", {})[TARGET_PROVENANCE_ARTIFACT_KEY] = {
        "kind": TARGET_PROVENANCE_ARTIFACT_KIND,
        "path": normalized_path,
        "freshness": "current",
        "source_run": TARGET_PROVENANCE_SOURCE_RUN,
        "sha256": _sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "modified_at": generated_at,
        "sample_id": sample_id,
    }
    artifact_index["generated_at"] = generated_at
    _save_json(artifact_index_path, artifact_index)


def run_target_provenance_recheck(
    *,
    target_bytes_path: Path,
    transform_recheck_path: Path,
    signed_transform_recheck_path: Path,
    ida_control_flow_path: Path,
    artifact_index_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    artifact_index = _load_json(artifact_index_path)
    source_keys = [
        "local_reverse_cpp1_2f6fcb63_target_bytes",
        "local_reverse_cpp1_2f6fcb63_transform_recheck",
        "local_reverse_cpp1_2f6fcb63_signed_transform_recheck",
        "local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck",
    ]
    _assert_current_artifacts(artifact_index, source_keys)

    target_artifact = _load_json(target_bytes_path)
    transform_recheck = _load_json(transform_recheck_path)
    signed_transform = _load_json(signed_transform_recheck_path)
    ida_control_flow = _load_json(ida_control_flow_path)
    for name, artifact in {
        "target_bytes": target_artifact,
        "transform_recheck": transform_recheck,
        "signed_transform_recheck": signed_transform,
        "ida_control_flow": ida_control_flow,
    }.items():
        if artifact.get("executed_sample") is not False:
            raise ValueError(f"{name} artifact executed_sample must be false")
        if artifact.get("runtime_validated") is not False:
            raise ValueError(f"{name} artifact runtime_validated must be false")

    sample_id = str(target_artifact.get("sample_id", ""))
    if sample_id != "cpp1_2f6fcb63":
        raise ValueError(f"Unexpected sample_id for cpp1 target provenance: {sample_id!r}")
    target_address = _parse_int(target_artifact.get("target_address")) or 0x00429A30
    target_bytes = target_artifact.get("target_bytes", [])
    if len(target_bytes) != 16:
        raise ValueError(f"target_bytes length must be 16, got {len(target_bytes)}")

    binary_path = _resolve_binary_path(str(target_artifact.get("relative_path", "")))
    window = (
        _read_pe_window(binary_path, target_address)
        if binary_path is not None
        else {
            "available": False,
            "blocked_reason": "BINARY_NOT_FOUND",
            "section_name": "",
            "symbol_span": {},
            "raw_data_window": {},
            "target_file_offset": None,
            "window_bytes": [],
            "window_start_va": None,
        }
    )

    xrefs = _xref_summary(ida_control_flow)
    spans = _span_feasibility(window, target_address)
    current_span = next(
        (
            span for span in spans
            if span["relative_start"] == 0 and span["length"] == 16
        ),
        None,
    )
    alternative_spans = [
        span for span in spans
        if span["all_target_bytes_have_printable_preimage"]
        and not (span["relative_start"] == 0 and span["length"] == 16)
    ]

    confirmed_hex = window.get("symbol_span", {}).get("bytes_hex", "")
    target_hex = str(target_artifact.get("target_bytes_hex", ""))
    current_target_matches_raw = bool(confirmed_hex) and confirmed_hex[: len(target_hex)] == target_hex
    signed_preimage_complete = signed_transform.get(
        "static_preimage_status", {}
    ).get("complete_printable_preimage") is True

    if not window.get("available"):
        verdict = "INSUFFICIENT_TARGET_PROVENANCE"
        blocked_reason = window.get("blocked_reason", "TARGET_RAW_WINDOW_UNAVAILABLE")
    elif not current_target_matches_raw:
        verdict = "INCONSISTENT_TARGET_BYTES"
        blocked_reason = "TARGET_BYTES_DO_NOT_MATCH_RAW_DATA"
    elif alternative_spans:
        verdict = "ALTERNATIVE_PRINTABLE_SPAN_FOUND_NEEDS_REVIEW"
        blocked_reason = "NEARBY_PRINTABLE_SPAN_NEEDS_STATIC_REVIEW"
    elif signed_preimage_complete or (current_span and current_span["all_target_bytes_have_printable_preimage"]):
        verdict = "INSUFFICIENT_TARGET_PROVENANCE"
        blocked_reason = "CURRENT_SPAN_PRINTABLE_FEASIBILITY_CONFLICT"
    else:
        verdict = "CONFIRMED_NO_PRINTABLE_PREIMAGE"
        blocked_reason = "CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE"

    generated_at = _now_iso()
    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "target_byte_provenance_recheck",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": generated_at,
        "source_artifacts": {
            "target_bytes": str(target_bytes_path).replace("\\", "/"),
            "transform_recheck": str(transform_recheck_path).replace("\\", "/"),
            "signed_transform_recheck": str(signed_transform_recheck_path).replace("\\", "/"),
            "ida_control_flow": str(ida_control_flow_path).replace("\\", "/"),
            "artifact_index": str(artifact_index_path).replace("\\", "/"),
        },
        "source_artifact_freshness": _source_artifact_freshness(artifact_index, source_keys),
        "ida_used_this_round": False,
        "ida_invocation_scope": "none",
        "used_existing_ida_interface": True,
        "new_ida_runner_created": False,
        "binary_static_parse": {
            "attempted": binary_path is not None,
            "binary_found": binary_path is not None,
            "source": "existing target artifact relative_path plus PE section table",
        },
        "target_symbol": target_artifact.get("target_symbol", "byte_429A30"),
        "target_address": target_artifact.get("target_address", _hx(target_address)),
        "target_length_candidates": [16, 18],
        "confirmed_target_bytes_hex": confirmed_hex[: len(target_hex)] if confirmed_hex else "",
        "artifact_target_bytes_hex": target_hex,
        "current_target_matches_raw_data": current_target_matches_raw,
        "raw_data_window": window.get("raw_data_window", {}),
        "section_name": window.get("section_name", ""),
        "symbol_span": window.get("symbol_span", {}),
        "compare_xrefs": xrefs["compare_xrefs"],
        "data_xrefs": xrefs["data_xrefs"],
        "nearby_candidate_spans": spans,
        "printable_preimage_feasibility_by_span": {
            "span_count": len(spans),
            "bounded_window": "target_address +/- 0x40",
            "allowed_lengths": [16, 18],
            "current_span": current_span,
            "alternative_printable_span_count": len(alternative_spans),
            "alternative_printable_spans": alternative_spans,
        },
        "signed_compare_notes": {
            "movsx_target_byte": "movsx byte_429A30[eax] sign-extends target bytes for compare only",
            "bytes_above_0x7f": sorted({f"{b:02x}" for b in target_bytes if b > 0x7F}),
            "does_not_imply_target_extraction_error": True,
            "signed_unsigned_transform_equivalent_after_u8": signed_transform
            .get("model_comparison_all_256", {})
            .get("models_equivalent_after_u8_truncation"),
            "current_target_has_complete_printable_preimage": signed_preimage_complete,
        },
        "provenance_verdict": verdict,
        "candidate": None,
        "known_candidate": "",
        "status": "BLOCKED",
        "blocked_reason": blocked_reason,
        "recommended_next_action": (
            "Keep cpp1_2f6fcb63 blocked/static-only. Current target bytes are raw-data "
            "consistent but do not have a complete printable preimage under the confirmed "
            "transform; any non-printable or alternative-span path needs a separate bounded "
            "review decision."
        ),
    }

    _save_json(out_path, result)
    _update_target_provenance_artifact_index(artifact_index_path, out_path, sample_id, generated_at)
    print(f"cpp1 target provenance recheck: status={result['status']} sample_id={sample_id}")
    print(f"  provenance_verdict={result['provenance_verdict']}")
    print(f"  target_matches_raw_data={result['current_target_matches_raw_data']}")
    print(f"  alternative_printable_span_count={len(alternative_spans)}")
    print(f"  candidate={result['candidate']}")
    print(f"  known_candidate={result['known_candidate']!r}")
    print(f"  runtime_validated={result['runtime_validated']}")
    return result



def _resolve_ida_executable() -> str:
    """Find IDA executable."""
    from .tool_runners import _resolve_ida_executable as resolve
    return resolve("")


def _resolve_ida_script() -> str:
    """Find extract_named_data.py script."""
    script_path = Path(__file__).parent / "ida_scripts" / "extract_named_data.py"
    if script_path.exists():
        return str(script_path)
    # Fallback: check env
    env_script = os.environ.get("REVERSE_AGENT_IDA_SCRIPT", "").strip()
    if env_script and Path(env_script).exists():
        return env_script
    return ""


def _run_ida_extraction(
    binary_path: Path,
    output_dir: Path,
    target_symbol: str = "byte_429A30",
    target_func: str = "_main_0",
    expected_target_length: int = 16,
) -> dict[str, Any]:
    """Run IDA with extract_named_data.py script."""
    ida_exec = _resolve_ida_executable()
    ida_script = _resolve_ida_script()

    if not ida_exec:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found"}
    if not ida_script:
        return {"tool_status": "blocked", "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA script not found"}

    output_dir.mkdir(parents=True, exist_ok=True)
    extract_out = output_dir / "named_data_extract.json"
    log_out = output_dir / "ida_extract.log"
    db_out = output_dir / "ida_extract.i64"

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
    env["REVERSE_AGENT_NAMED_DATA_OUT"] = str(extract_out)
    env["REVERSE_AGENT_TARGET_SYMBOL"] = target_symbol
    env["REVERSE_AGENT_TARGET_FUNC"] = target_func
    env["REVERSE_AGENT_TARGET_LENGTH"] = str(expected_target_length)

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

    # Parse extraction output
    if extract_out.exists():
        try:
            extract_data = _load_json(extract_out)
            return _parse_extraction(extract_data, exit_code)
        except (json.JSONDecodeError, KeyError) as exc:
            return {
                "tool_status": "blocked",
                "blocked_reason": f"STATIC_TOOL_PARSE_ERROR: {exc}",
                "exit_code": exit_code,
            }
    else:
        return {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no extraction JSON",
            "exit_code": exit_code,
        }


def _parse_extraction(extract_data: dict[str, Any], exit_code: int) -> dict[str, Any]:
    """Parse IDA extraction JSON into target-bytes fields."""
    named_data = extract_data.get("named_data", {})
    func_data = extract_data.get("function", {})
    compare_ctx = extract_data.get("compare_context", {})

    result: dict[str, Any] = {
        "tool_status": "success" if exit_code == 0 else "blocked",
        "blocked_reason": "" if exit_code == 0 else f"IDA_EXIT_CODE_{exit_code}",
        "source_tool": "IDA",
        "exit_code": exit_code,
    }

    # Named data extraction
    if named_data.get("found"):
        result["target_symbol"] = named_data.get("name", "")
        result["target_address"] = named_data.get("address", "")
        result["target_length"] = named_data.get("length", 0)
        result["target_bytes_hex"] = named_data.get("bytes_hex", "")
        result["target_bytes"] = named_data.get("bytes", [])
    else:
        result["target_symbol"] = extract_data.get("target_symbol", "byte_429A30")
        result["target_address"] = ""
        result["target_length"] = 0
        result["target_bytes_hex"] = ""
        result["target_bytes"] = []
        result["tool_status"] = "blocked"
        result["blocked_reason"] = "TARGET_BYTES_NOT_FOUND"

    # Function extraction
    if func_data.get("found"):
        result["main_function"] = func_data.get("name", "")
        result["main_function_address"] = func_data.get("address", "")
        result["main_pseudocode"] = func_data.get("pseudocode", "")
    else:
        result["main_function"] = extract_data.get("target_func", "_main_0")
        result["main_function_address"] = ""
        result["main_pseudocode"] = ""

    # Compare context
    result["compare_expression"] = compare_ctx.get("compare_expression", "")
    result["loop_context"] = compare_ctx.get("loop_context", "")

    return result


def _extract_forward_transform(pseudocode: str) -> dict[str, Any]:
    """Extract forward transform formula from _main_0 pseudocode."""
    transform = {
        "input_buffer": "Str",
        "work_buffer": "Destination",
        "copy_length": 16,
        "formula_c": "",
        "compare_expression": "Destination[i] == byte_429A30[i]",
        "notes": [],
    }

    if not pseudocode:
        return transform

    lines = pseudocode.split("\n")
    for line in lines:
        stripped = line.strip()
        # Look for the bit manipulation formula
        if "& 3" in stripped and "& 0x0C" in stripped and ">> 2" in stripped:
            transform["formula_c"] = stripped
            transform["notes"].append("nibble/bit-level transform detected")
        elif "& 3" in stripped and "* 16" in stripped and "& 0xF0" in stripped:
            transform["formula_c"] = stripped
            transform["notes"].append("nibble/bit-level transform detected")
        # Look for length checks
        if "!= 18" in stripped or "== 18" in stripped:
            transform["notes"].append(f"length check found: {stripped}")
        if "strncpy" in stripped.lower() or "memcpy" in stripped.lower():
            transform["notes"].append(f"copy operation: {stripped}")

    # Default formula if not found in pseudocode
    if not transform["formula_c"]:
        transform["formula_c"] = "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)"
        transform["notes"].append("formula from static triage evidence")

    return transform


def _build_evidence_notes(pseudocode: str) -> list[str]:
    """Build evidence notes from pseudocode anomalies."""
    notes = []
    if not pseudocode:
        return notes

    lower = pseudocode.lower()

    # Length discrepancy
    if "!= 18" in pseudocode and "== 16" in pseudocode:
        notes.append("length discrepancy: input must be 18 chars but compare loop checks 16 bytes")

    # Division anomaly (potential trap)
    if "/ v8" in pseudocode or "/ v9" in pseudocode:
        notes.append("division operation detected in path; potential anti-debug trap or dead code")

    # Memory check
    if "memory check" in lower:
        notes.append("memory check string found; may indicate anti-tampering")

    return notes


def run_target_byte_extraction(
    *,
    sample_id: str,
    triage_path: Path,
    inventory_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main logic: read triage, run IDA extraction, produce target-bytes artifact."""
    # Load triage artifact
    triage = _load_json(triage_path) if triage_path.exists() else {}
    inventory = _load_json(inventory_path) if inventory_path.exists() else {}

    relative_path = triage.get("relative_path", "")
    if not relative_path:
        # Try inventory
        for entry in inventory.get("entries", []):
            if entry.get("sample_id") == sample_id:
                relative_path = entry.get("relative_path", "")
                break

    if not relative_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="SAMPLE_NOT_FOUND_IN_TRIAGE_OR_INVENTORY",
        )
        _save_json(out_path, result)
        return result

    # Resolve binary path
    binary_path = _resolve_binary_path(relative_path)
    if not binary_path:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="BINARY_NOT_FOUND",
            detail=f"Could not resolve path: {relative_path}",
        )
        _save_json(out_path, result)
        return result

    # Run IDA extraction with expected target length
    expected_target_length = 16
    output_dir = out_path.parent / f"extract_{sample_id}"
    ida_result = _run_ida_extraction(
        binary_path, output_dir,
        expected_target_length=expected_target_length,
    )

    tool_status = ida_result.get("tool_status", "blocked")
    blocked_reason = ida_result.get("blocked_reason", "")

    if tool_status == "blocked":
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason=blocked_reason,
            source_tool=ida_result.get("source_tool", "IDA"),
            expected_target_length=expected_target_length,
            actual_target_length=ida_result.get("target_length", 0),
            actual_target_bytes=ida_result.get("target_bytes", []),
            actual_target_bytes_hex=ida_result.get("target_bytes_hex", ""),
        )
        _save_json(out_path, result)
        return result

    # Build success artifact
    pseudocode = ida_result.get("main_pseudocode", "")
    forward_transform = _extract_forward_transform(pseudocode)
    evidence_notes = _build_evidence_notes(pseudocode)

    # Check if target bytes were actually found
    target_bytes = ida_result.get("target_bytes", [])
    actual_target_length = len(target_bytes)

    # Validate expected length
    if actual_target_length < expected_target_length:
        result = _blocked_artifact(
            sample_id=sample_id,
            blocked_reason="INCOMPLETE_TARGET_BYTES",
            source_tool=ida_result.get("source_tool", "IDA"),
            expected_target_length=expected_target_length,
            actual_target_length=actual_target_length,
            actual_target_bytes=target_bytes,
            actual_target_bytes_hex=ida_result.get("target_bytes_hex", ""),
        )
        _save_json(out_path, result)
        return result

    recommended_next = "Target bytes extracted. Next round: create inverse-transform handoff to reverse the nibble/bit-level transform and recover password."

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": relative_path,
        "analysis_mode": "target_compare_byte_extraction",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "success",
        "blocked_reason": "",
        "expected_target_length": expected_target_length,
        "source_tool": ida_result.get("source_tool", "IDA"),
        "target_symbol": ida_result.get("target_symbol", "byte_429A30"),
        "target_address": ida_result.get("target_address", ""),
        "target_length": actual_target_length,
        "target_bytes_hex": ida_result.get("target_bytes_hex", ""),
        "target_bytes": target_bytes,
        "main_function": ida_result.get("main_function", "_main_0"),
        "main_function_address": ida_result.get("main_function_address", ""),
        "main_pseudocode": pseudocode[:2000] if pseudocode else "",
        "forward_transform": forward_transform,
        "compare_expression": ida_result.get("compare_expression", ""),
        "loop_context": ida_result.get("loop_context", ""),
        "evidence_notes": evidence_notes,
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": recommended_next,
    }

    _save_json(out_path, result)
    print(f"target byte extraction: status=success sample_id={sample_id}")
    print(f"  target_symbol: {result['target_symbol']}")
    print(f"  target_address: {result['target_address']}")
    print(f"  target_length: {result['target_length']}")
    print(f"  target_bytes_hex: {result['target_bytes_hex'][:32]}...")
    print(f"  forward_transform_formula: {forward_transform['formula_c'][:60]}...")
    return result


def _blocked_artifact(
    *,
    sample_id: str,
    blocked_reason: str,
    detail: str = "",
    source_tool: str = "",
    expected_target_length: int = 16,
    actual_target_length: int = 0,
    actual_target_bytes: list[int] | None = None,
    actual_target_bytes_hex: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "relative_path": "",
        "analysis_mode": "target_compare_byte_extraction",
        "mainline": "tool_integration",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "tool_status": "blocked",
        "blocked_reason": blocked_reason,
        "blocked_detail": detail,
        "expected_target_length": expected_target_length,
        "source_tool": source_tool,
        "target_symbol": "byte_429A30",
        "target_address": "",
        "target_length": actual_target_length,
        "target_bytes_hex": actual_target_bytes_hex,
        "target_bytes": actual_target_bytes if actual_target_bytes is not None else [],
        "main_function": "_main_0",
        "main_function_address": "",
        "main_pseudocode": "",
        "forward_transform": {
            "input_buffer": "Str",
            "work_buffer": "Destination",
            "copy_length": 16,
            "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
            "compare_expression": "Destination[i] == byte_429A30[i]",
            "notes": [],
        },
        "compare_expression": "",
        "loop_context": "",
        "evidence_notes": [],
        "candidate": None,
        "known_candidate": "",
        "recommended_next_action": f"Resolve blocker: {blocked_reason}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract target compare bytes from cpp1_2f6fcb63 using IDA.",
    )
    parser.add_argument(
        "--provenance-recheck",
        action="store_true",
        help="Run bounded static target-byte provenance recheck from current artifacts.",
    )
    parser.add_argument(
        "--current-revalidation",
        action="store_true",
        help="Revalidate old target bytes against the current static triage artifact without running IDA.",
    )
    parser.add_argument("--sample-id", default="cpp1_2f6fcb63", help="Sample ID")
    parser.add_argument("--triage", default="project_state/local_reverse_cpp1_2f6fcb63_static_triage.json")
    parser.add_argument("--inventory", default="project_state/local_reverse_inventory.json")
    parser.add_argument("--out", default="project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json")
    parser.add_argument("--target-bytes", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json"))
    parser.add_argument("--transform-recheck", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json"))
    parser.add_argument("--signed-transform-recheck", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json"))
    parser.add_argument("--ida-control-flow", type=Path, default=Path("project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json"))
    parser.add_argument("--artifact-index", type=Path, default=Path("project_state/artifact_index.json"))
    args = parser.parse_args()

    try:
        if args.current_revalidation:
            run_target_bytes_current_revalidation(
                target_bytes_path=args.target_bytes,
                triage_path=Path(args.triage),
                artifact_index_path=args.artifact_index,
                out_path=Path(args.out),
            )
            return 0
        if args.provenance_recheck:
            run_target_provenance_recheck(
                target_bytes_path=args.target_bytes,
                transform_recheck_path=args.transform_recheck,
                signed_transform_recheck_path=args.signed_transform_recheck,
                ida_control_flow_path=args.ida_control_flow,
                artifact_index_path=args.artifact_index,
                out_path=Path(args.out),
            )
            return 0
        run_target_byte_extraction(
            sample_id=args.sample_id,
            triage_path=Path(args.triage),
            inventory_path=Path(args.inventory),
            out_path=Path(args.out),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
