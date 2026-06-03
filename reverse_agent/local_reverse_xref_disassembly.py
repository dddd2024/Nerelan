from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_compare_site import TARGET_SAMPLE_IDS, extract_strings_with_offsets
from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe
from reverse_agent.local_reverse_string_solver import (
    FAILURE_MARKERS,
    SUCCESS_MARKERS,
    is_candidate_input,
    validation_succeeded,
)

STAGE = "bounded_xref_disassembly_extraction"
PREVIOUS_MISSING_EVIDENCE = "new_candidates_failed_runtime_validation"
DEFAULT_MAX_STRINGS_PER_SAMPLE = 12
DEFAULT_MAX_XREFS_PER_STRING = 20
DEFAULT_MAX_INSTRUCTIONS_PER_XREF = 64
DEFAULT_MAX_BYTES_PER_XREF = 512
DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE = 20
DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE = 20
EXECUTE_CHARACTERISTIC = 0x20000000
INTERESTING_MNEMONICS = {
    "call",
    "cmp",
    "je",
    "jne",
    "jg",
    "jge",
    "jl",
    "jle",
    "ja",
    "jae",
    "jb",
    "jbe",
    "jmp",
    "jz",
    "jnz",
    "lea",
    "mov",
    "push",
    "test",
}
SUCCESS_HINTS = tuple(dict.fromkeys((*SUCCESS_MARKERS, "well done", "you are right")))
FAILURE_HINTS = tuple(dict.fromkeys((*FAILURE_MARKERS, "try again", "hang on")))


@dataclass(frozen=True)
class Section:
    name: str
    rva: int
    virtual_size: int
    raw_offset: int
    raw_size: int
    executable: bool

    @property
    def raw_end(self) -> int:
        return self.raw_offset + self.raw_size

    @property
    def rva_end(self) -> int:
        return self.rva + max(self.virtual_size, self.raw_size)


@dataclass(frozen=True)
class PEMapping:
    image_base: int
    sections: list[Section]

    def raw_to_rva(self, raw_offset: int) -> int | None:
        for section in self.sections:
            if section.raw_offset <= raw_offset < section.raw_end:
                return section.rva + (raw_offset - section.raw_offset)
        return None

    def rva_to_raw(self, rva: int) -> int | None:
        for section in self.sections:
            if section.rva <= rva < section.rva_end:
                raw = section.raw_offset + (rva - section.rva)
                if raw < section.raw_end:
                    return raw
        return None

    def raw_to_va(self, raw_offset: int) -> int | None:
        rva = self.raw_to_rva(raw_offset)
        return None if rva is None else self.image_base + rva

    def va_to_raw(self, va: int) -> int | None:
        return self.rva_to_raw(va - self.image_base)

    def executable_sections(self) -> list[Section]:
        return [section for section in self.sections if section.executable]

    def section_for_raw(self, raw_offset: int) -> Section | None:
        for section in self.sections:
            if section.raw_offset <= raw_offset < section.raw_end:
                return section
        return None


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    result = run_xref_disassembly(
        corpus_index=_read_json(Path(args.corpus_index)),
        benchmark=_read_json(Path(args.benchmark)),
        string_result=_read_json(Path(args.string_result)),
        compare_site_result=_read_json(Path(args.compare_site_result)),
        policy=_read_json(Path(args.policy)),
        max_strings_per_sample=args.max_strings_per_sample,
        max_xrefs_per_string=args.max_xrefs_per_string,
        max_instructions_per_xref=args.max_instructions_per_xref,
        max_bytes_per_xref=args.max_bytes_per_xref,
        max_new_candidates_per_sample=args.max_new_candidates_per_sample,
        max_runtime_validations_per_sample=args.max_runtime_validations_per_sample,
        preview_limit=args.preview_limit,
    )
    _write_json(Path(args.out), result)

    print(
        "local reverse xref/disassembly extraction: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"solved={result['solved_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_xref_disassembly(
    *,
    corpus_index: dict[str, Any],
    benchmark: dict[str, Any],
    string_result: dict[str, Any],
    compare_site_result: dict[str, Any],
    policy: dict[str, Any],
    max_strings_per_sample: int = DEFAULT_MAX_STRINGS_PER_SAMPLE,
    max_xrefs_per_string: int = DEFAULT_MAX_XREFS_PER_STRING,
    max_instructions_per_xref: int = DEFAULT_MAX_INSTRUCTIONS_PER_XREF,
    max_bytes_per_xref: int = DEFAULT_MAX_BYTES_PER_XREF,
    max_new_candidates_per_sample: int = DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE,
    max_runtime_validations_per_sample: int = DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    timeout = _policy_timeout(policy)
    runtime_allowed = bool(policy.get("runtime_allowed"))
    corpus_by_id = {str(item.get("sample_id", "")): item for item in corpus_index.get("samples", [])}
    benchmark_by_id = {str(item.get("sample_id", "")): item for item in benchmark.get("samples", [])}
    previous_failed = collect_previous_failed_candidates(string_result, compare_site_result)
    selected = select_compare_site_targets(compare_site_result)
    blocked_reasons: list[str] = []

    if not root.exists():
        blocked_reasons.append("ROOT_UNAVAILABLE")
    if not runtime_allowed:
        blocked_reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if not capstone_available():
        blocked_reasons.append("BLOCKED_BY_MISSING_DISASSEMBLY_BACKEND")

    targets = []
    for previous in selected:
        target = extract_target(
            compare_target=previous,
            corpus_sample=corpus_by_id.get(str(previous.get("sample_id", ""))),
            benchmark_sample=benchmark_by_id.get(str(previous.get("sample_id", ""))),
            previous_failed_candidates=previous_failed.get(str(previous.get("sample_id", "")), set()),
            root=root,
            runtime_allowed=runtime_allowed,
            timeout=timeout,
            preview_limit=preview_limit,
            max_strings_per_sample=max_strings_per_sample,
            max_xrefs_per_string=max_xrefs_per_string,
            max_instructions_per_xref=max_instructions_per_xref,
            max_bytes_per_xref=max_bytes_per_xref,
            max_new_candidates_per_sample=max_new_candidates_per_sample,
            max_runtime_validations_per_sample=max_runtime_validations_per_sample,
            global_blocked=bool(blocked_reasons),
        )
        targets.append(target)
        blocked_reasons.extend(target.get("blocked_reasons", []))

    solved_count = sum(1 for target in targets if target.get("solved"))
    if not targets or any(target.get("status") == "BLOCKED" for target in targets):
        status = "BLOCKED"
    elif solved_count == len(targets):
        status = "SUCCESS"
    else:
        status = "PARTIAL"

    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "stage": STAGE,
        "status": status,
        "target_count": len(targets),
        "solved_count": solved_count,
        "bounds": {
            "max_strings_per_sample": max_strings_per_sample,
            "max_xrefs_per_string": max_xrefs_per_string,
            "max_instructions_per_xref": max_instructions_per_xref,
            "max_bytes_per_xref": max_bytes_per_xref,
            "max_new_candidates_per_sample": max_new_candidates_per_sample,
            "max_runtime_validations_per_sample": max_runtime_validations_per_sample,
        },
        "timeout_seconds": timeout,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "targets": targets,
    }


def select_compare_site_targets(compare_site_result: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for target in compare_site_result.get("targets", []):
        sample_id = str(target.get("sample_id", ""))
        if sample_id not in TARGET_SAMPLE_IDS:
            continue
        if target.get("solved") is True:
            continue
        if target.get("missing_evidence") != PREVIOUS_MISSING_EVIDENCE:
            continue
        selected.append(target)
    selected.sort(key=lambda item: str(item.get("sample_id", "")))
    return selected


def extract_target(
    *,
    compare_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    benchmark_sample: dict[str, Any] | None,
    previous_failed_candidates: set[str],
    root: Path,
    runtime_allowed: bool,
    timeout: int,
    preview_limit: int,
    max_strings_per_sample: int,
    max_xrefs_per_string: int,
    max_instructions_per_xref: int,
    max_bytes_per_xref: int,
    max_new_candidates_per_sample: int,
    max_runtime_validations_per_sample: int,
    global_blocked: bool,
) -> dict[str, Any]:
    sample_id = str(compare_target.get("sample_id", ""))
    relative_path = str(compare_target.get("relative_path", ""))
    blocked_reasons = validate_target(
        compare_target=compare_target,
        corpus_sample=corpus_sample,
        benchmark_sample=benchmark_sample,
        root=root,
        runtime_allowed=runtime_allowed,
        global_blocked=global_blocked,
    )
    base = {
        "sample_id": sample_id,
        "relative_path": relative_path,
        "sha256": str((corpus_sample or compare_target).get("sha256", "")),
        "previous_missing_evidence": compare_target.get("missing_evidence"),
        "pe_mapping_status": "blocked" if blocked_reasons else "failed",
        "capstone_status": "missing" if not capstone_available() else "available_not_used",
        "xref_summary": [],
        "disassembly_windows": [],
        "new_candidate_count": 0,
        "validated_candidate_count": 0,
        "solved": False,
        "solution": None,
        "runtime_evidence": None,
        "missing_evidence": "blocked_precondition" if blocked_reasons else "pe_mapping_failed",
        "next_action": "fix blocked precondition before xref extraction"
        if blocked_reasons
        else "bounded IDA string xref extraction",
        "status": "BLOCKED" if blocked_reasons else "NO_CANDIDATE_VALIDATED",
        "blocked_reasons": blocked_reasons,
    }
    if blocked_reasons or corpus_sample is None:
        return base

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    data = path.read_bytes()
    mapping = parse_pe_mapping(data)
    if mapping is None:
        return base

    key_strings = collect_key_strings(compare_target, mapping, max_strings=max_strings_per_sample)
    all_strings = extract_strings_with_offsets(data, max_count=3000)
    strings_by_offset = {item.offset: item.value for item in all_strings}
    xref_summary = []
    windows = []
    for key in key_strings:
        xrefs = find_xrefs(data, mapping, key, max_xrefs=max_xrefs_per_string)
        xref_entry = dict(key)
        xref_entry["xref_candidates"] = xrefs
        xref_summary.append(xref_entry)
        for xref in xrefs:
            window = disassemble_xref_window(
                data=data,
                mapping=mapping,
                xref=xref,
                max_instructions=max_instructions_per_xref,
                max_bytes=max_bytes_per_xref,
            )
            if window:
                windows.append(window)

    candidates = build_xref_candidates(
        windows=windows,
        mapping=mapping,
        strings_by_offset=strings_by_offset,
        previous_failed_candidates=previous_failed_candidates,
        max_candidates=max_new_candidates_per_sample,
    )

    validations = []
    solved_probe: dict[str, Any] | None = None
    for candidate in candidates[:max_runtime_validations_per_sample]:
        probe = run_probe(
            path=path,
            probe_name=f"xref_candidate_{len(validations) + 1}",
            stdin_text=f"{candidate['candidate']}\n",
            timeout=timeout,
            preview_limit=preview_limit,
        )
        success = validation_succeeded(probe)
        validation = {
            "candidate": candidate["candidate"],
            "source": candidate["source"],
            "probe_name": probe["probe_name"],
            "exit_code": probe["exit_code"],
            "timeout": probe["timeout"],
            "classification": probe["classification"],
            "success": success,
            "stdout_preview": probe["stdout_preview"],
            "stderr_preview": probe["stderr_preview"],
            "duration_ms": probe["duration_ms"],
        }
        validations.append(validation)
        if success:
            solved_probe = validation
            break

    solved = solved_probe is not None
    missing_evidence = None if solved else classify_missing_evidence(xref_summary, windows, candidates)
    base.update({
        "pe_mapping_status": "ok",
        "image_base": hex(mapping.image_base),
        "section_count": len(mapping.sections),
        "capstone_status": "available_used" if windows else "available_not_used",
        "xref_summary": xref_summary,
        "disassembly_windows": windows,
        "new_candidate_count": len(candidates),
        "validated_candidate_count": len(validations),
        "new_candidate_sources": summarize_candidate_sources(candidates),
        "validation_results_preview": validations[:10],
        "solved": solved,
        "solution": solved_probe["candidate"] if solved_probe else None,
        "runtime_evidence": solved_probe,
        "missing_evidence": missing_evidence,
        "next_action": next_action_for_missing(missing_evidence),
        "status": "SOLVED" if solved else "NO_CANDIDATE_VALIDATED",
    })
    return base


def validate_target(
    *,
    compare_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    benchmark_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    global_blocked: bool,
) -> list[str]:
    reasons: list[str] = []
    if global_blocked:
        reasons.append("GLOBAL_RUNTIME_PRECONDITION_FAILED")
    if not runtime_allowed:
        reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if not capstone_available():
        reasons.append("BLOCKED_BY_MISSING_DISASSEMBLY_BACKEND")
    if corpus_sample is None:
        reasons.append("MISSING_CORPUS_SAMPLE")
        return reasons
    if benchmark_sample is None:
        reasons.append("MISSING_BENCHMARK_SAMPLE")
    elif str(benchmark_sample.get("solve_readiness")) != "ready_static_string_compare":
        reasons.append("BENCHMARK_SAMPLE_NOT_READY_STATIC_STRING_COMPARE")

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    if not _is_under_root(path, root):
        reasons.append("PATH_OUTSIDE_ROOT")
    if not path.exists():
        reasons.append("SAMPLE_MISSING")
    elif _sha256_file(path) != str(corpus_sample.get("sha256", "")):
        reasons.append("SHA256_MISMATCH")
    return reasons


def parse_pe_mapping(data: bytes) -> PEMapping | None:
    try:
        import pefile  # type: ignore

        pe = pefile.PE(data=data, fast_load=True)
        image_base = int(pe.OPTIONAL_HEADER.ImageBase)
        sections = []
        for raw_section in pe.sections:
            name = raw_section.Name.rstrip(b"\x00").decode("ascii", errors="replace")
            sections.append(Section(
                name=name,
                rva=int(raw_section.VirtualAddress),
                virtual_size=int(raw_section.Misc_VirtualSize),
                raw_offset=int(raw_section.PointerToRawData),
                raw_size=int(raw_section.SizeOfRawData),
                executable=bool(int(raw_section.Characteristics) & EXECUTE_CHARACTERISTIC),
            ))
        return PEMapping(image_base=image_base, sections=sections)
    except Exception:
        return None


def collect_key_strings(compare_target: dict[str, Any], mapping: PEMapping, *, max_strings: int) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    role_sources = [
        ("success", compare_target.get("strings_summary", {}).get("success_strings", [])),
        ("failure", compare_target.get("strings_summary", {}).get("failure_strings", [])),
        ("prompt", compare_target.get("strings_summary", {}).get("prompt_strings", [])),
        ("compare_keyword", compare_target.get("compare_site_evidence", {}).get("compare_keyword_strings", [])),
    ]
    for role, entries in role_sources:
        for entry in entries:
            raw_offset = int(entry.get("offset", -1))
            rva = mapping.raw_to_rva(raw_offset)
            va = mapping.raw_to_va(raw_offset)
            if rva is None or va is None:
                continue
            candidate = {
                "string_value": str(entry.get("value", ""))[:160],
                "string_role": role,
                "raw_offset": raw_offset,
                "rva": rva,
                "va": va,
                "encoding": str(entry.get("encoding", "")),
            }
            if not any(existing["raw_offset"] == raw_offset and existing["string_role"] == role for existing in values):
                values.append(candidate)
            if len(values) >= max_strings:
                return values
    return values


def find_xrefs(data: bytes, mapping: PEMapping, key: dict[str, Any], *, max_xrefs: int) -> list[dict[str, Any]]:
    needles = [
        ("va32", _pack_u32(int(key["va"]))),
        ("rva32", _pack_u32(int(key["rva"]))),
        ("raw32", _pack_u32(int(key["raw_offset"]))),
    ]
    seen_offsets: set[int] = set()
    xrefs = []
    for section in mapping.executable_sections():
        section_data = data[section.raw_offset:section.raw_end]
        for reference_kind, needle in needles:
            if not needle:
                continue
            start = 0
            while True:
                relative = section_data.find(needle, start)
                if relative < 0:
                    break
                raw_offset = section.raw_offset + relative
                start = relative + 1
                if raw_offset in seen_offsets:
                    continue
                seen_offsets.add(raw_offset)
                rva = mapping.raw_to_rva(raw_offset)
                va = mapping.raw_to_va(raw_offset)
                xrefs.append({
                    "reference_kind": reference_kind,
                    "raw_offset": raw_offset,
                    "rva": rva,
                    "va": va,
                    "section": section.name,
                })
                if len(xrefs) >= max_xrefs:
                    return xrefs
    return xrefs


def disassemble_xref_window(
    *,
    data: bytes,
    mapping: PEMapping,
    xref: dict[str, Any],
    max_instructions: int,
    max_bytes: int,
) -> dict[str, Any] | None:
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32  # type: ignore
    except Exception:
        return None

    raw_offset = int(xref["raw_offset"])
    section = mapping.section_for_raw(raw_offset)
    if section is None or not section.executable:
        return None
    window_start = max(section.raw_offset, raw_offset - (max_bytes // 2))
    window_end = min(section.raw_end, window_start + max_bytes)
    code = data[window_start:window_end]
    rva = mapping.raw_to_rva(window_start)
    if rva is None:
        return None
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    instructions = []
    interesting = []
    for insn in md.disasm(code, mapping.image_base + rva):
        raw = window_start + (int(insn.address) - (mapping.image_base + rva))
        entry = {
            "address": hex(int(insn.address)),
            "rva": hex(int(insn.address) - mapping.image_base),
            "raw_offset": raw,
            "mnemonic": insn.mnemonic,
            "op_str": insn.op_str,
        }
        instructions.append(entry)
        if insn.mnemonic.lower() in INTERESTING_MNEMONICS:
            interesting.append(entry)
        if len(instructions) >= max_instructions:
            break
    if not instructions:
        return None
    return {
        "xref": xref,
        "window_raw_start": window_start,
        "window_raw_end": window_end,
        "instruction_count": len(instructions),
        "interesting_instruction_count": len(interesting),
        "instructions": instructions,
        "interesting_instructions": interesting[:24],
        "branch_hints": summarize_branch_hints(interesting),
    }


def build_xref_candidates(
    *,
    windows: list[dict[str, Any]],
    mapping: PEMapping,
    strings_by_offset: dict[int, str],
    previous_failed_candidates: set[str],
    max_candidates: int,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for window in windows:
        for instruction in window.get("interesting_instructions", []):
            for immediate in extract_immediates(str(instruction.get("op_str", ""))):
                raw_offset = resolve_immediate_to_raw(immediate, mapping)
                if raw_offset is None:
                    continue
                value = strings_by_offset.get(raw_offset) or read_printable_at_raw(raw_offset, strings_by_offset)
                if not value:
                    continue
                add_candidate(
                    candidates,
                    value=value,
                    source=f"xref_{instruction.get('mnemonic', 'operand')}",
                    previous_failed_candidates=previous_failed_candidates,
                    max_candidates=max_candidates,
                )
                if len(candidates) >= max_candidates:
                    return candidates
    return candidates


def add_candidate(
    candidates: list[dict[str, str]],
    *,
    value: str,
    source: str,
    previous_failed_candidates: set[str],
    max_candidates: int,
) -> None:
    candidate = value.strip().strip("\"'")
    if candidate in previous_failed_candidates:
        return
    if not is_candidate_input(candidate):
        return
    if any(existing["candidate"] == candidate for existing in candidates):
        return
    candidates.append({"candidate": candidate, "source": source})
    if len(candidates) > max_candidates:
        del candidates[max_candidates:]


def classify_missing_evidence(
    xref_summary: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    candidates: list[dict[str, str]],
) -> str:
    xref_count = sum(len(item.get("xref_candidates", [])) for item in xref_summary)
    if xref_count == 0:
        return "xref_not_found"
    if not windows:
        return "compare_branch_not_identified"
    if not candidates:
        if any(window.get("branch_hints", {}).get("has_branch_or_compare") for window in windows):
            return "target_constant_not_recovered"
        return "compare_branch_not_identified"
    return "new_xref_candidates_failed_runtime_validation"


def next_action_for_missing(missing_evidence: str | None) -> str | None:
    if missing_evidence is None:
        return None
    actions = {
        "xref_not_found": "bounded IDA string xref extraction",
        "compare_branch_not_identified": "add stronger xref backend or manual address seed",
        "target_constant_not_recovered": "inspect compare operand source near xref windows",
        "new_xref_candidates_failed_runtime_validation": "inspect xref-derived candidate source before widening",
        "needs_ida_script": "run bounded IDA string xref extraction",
        "blocked_precondition": "fix blocked precondition before xref extraction",
        "pe_mapping_failed": "repair PE mapping or use IDA-assisted xrefs",
    }
    return actions.get(missing_evidence, "bounded xref/disassembly follow-up")


def collect_previous_failed_candidates(
    string_result: dict[str, Any],
    compare_site_result: dict[str, Any],
) -> dict[str, set[str]]:
    failed: dict[str, set[str]] = {}
    for result in (string_result, compare_site_result):
        for target in result.get("targets", []):
            sample_id = str(target.get("sample_id", ""))
            bucket = failed.setdefault(sample_id, set())
            for validation in target.get("validation_results_preview", []):
                candidate = str(validation.get("candidate", ""))
                if candidate:
                    bucket.add(candidate)
    return failed


def summarize_branch_hints(instructions: list[dict[str, Any]]) -> dict[str, Any]:
    mnemonics = {str(item.get("mnemonic", "")).lower() for item in instructions}
    has_branch = any(mnemonic.startswith("j") for mnemonic in mnemonics)
    return {
        "has_call": "call" in mnemonics,
        "has_compare": bool({"cmp", "test"} & mnemonics),
        "has_branch": has_branch,
        "has_branch_or_compare": bool({"cmp", "test"} & mnemonics) or has_branch,
    }


def summarize_candidate_sources(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate["source"]] = counts.get(candidate["source"], 0) + 1
    return [{"source": source, "count": count} for source, count in sorted(counts.items())]


def extract_immediates(op_str: str) -> list[int]:
    values = []
    for match in re.finditer(r"0x[0-9a-fA-F]+|\b\d{5,}\b", op_str):
        text = match.group(0)
        try:
            values.append(int(text, 16 if text.lower().startswith("0x") else 10))
        except ValueError:
            pass
    return values


def resolve_immediate_to_raw(value: int, mapping: PEMapping) -> int | None:
    for resolver in (mapping.va_to_raw, mapping.rva_to_raw):
        raw = resolver(value)
        if raw is not None:
            return raw
    return value if mapping.section_for_raw(value) is not None else None


def read_printable_at_raw(raw_offset: int, strings_by_offset: dict[int, str]) -> str:
    for offset, value in strings_by_offset.items():
        if offset <= raw_offset < offset + len(value):
            return value
    return ""


def capstone_available() -> bool:
    try:
        import capstone  # noqa: F401  # type: ignore

        return True
    except Exception:
        return False


def _pack_u32(value: int) -> bytes:
    if value < 0 or value > 0xFFFFFFFF:
        return b""
    return struct.pack("<I", value)


def _policy_timeout(policy: dict[str, Any]) -> int:
    default_timeout = int(policy.get("default_timeout_seconds") or 5)
    max_timeout = int(policy.get("max_timeout_seconds") or 15)
    return max(1, min(default_timeout, max_timeout))


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded local reverse xref/disassembly extraction.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--benchmark", default="project_state/local_reverse_solve_benchmark.json")
    parser.add_argument("--string-result", default="project_state/local_reverse_string_solver_result.json")
    parser.add_argument("--compare-site-result", default="project_state/local_reverse_compare_site_result.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_xref_disassembly_result.json")
    parser.add_argument("--max-strings-per-sample", type=int, default=DEFAULT_MAX_STRINGS_PER_SAMPLE)
    parser.add_argument("--max-xrefs-per-string", type=int, default=DEFAULT_MAX_XREFS_PER_STRING)
    parser.add_argument("--max-instructions-per-xref", type=int, default=DEFAULT_MAX_INSTRUCTIONS_PER_XREF)
    parser.add_argument("--max-bytes-per-xref", type=int, default=DEFAULT_MAX_BYTES_PER_XREF)
    parser.add_argument("--max-new-candidates-per-sample", type=int, default=DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE)
    parser.add_argument("--max-runtime-validations-per-sample", type=int, default=DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE)
    parser.add_argument("--preview-limit", type=int, default=PREVIEW_LIMIT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
