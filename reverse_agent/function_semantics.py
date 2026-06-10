from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


FUNCTION_SEMANTIC_AUDIT_FILE_NAME = "function_semantic_audit.json"
FUNCTION_SEMANTIC_AUDIT_KIND = "function_semantic_audit"

ALLOWED_SEMANTIC_GUESSES = {
    "utf16le_constructor",
    "base64_transform",
    "rc4_ksa",
    "rc4_prga",
    "rc4_transform",
    "copy_or_handoff",
    "compare_preparer",
    "string_helper",
    "allocator_or_container_helper",
    "unrelated_helper",
    "unknown_but_bounded",
}

MATERIAL_SEMANTIC_GUESSES = {
    "utf16le_constructor",
    "base64_transform",
    "rc4_ksa",
    "rc4_prga",
    "rc4_transform",
}

ALLOWED_AUDIT_CLASSIFICATIONS = {
    "function_semantic_audit_complete",
    "material_function_identified",
    "material_hook_ready",
    "compare_side_only",
    "copy_handoff_only",
    "wrong_window",
    "manual_disassembly_required",
    "runtime_instrumentation_required",
    "evidence_insufficient",
}


def _strings(values: Iterable[Any] | Any) -> list[str]:
    if not isinstance(values, list | tuple | set):
        values = [] if values is None else [values]
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in out:
            out.append(text)
    return out


def _dicts(values: Iterable[Any] | Any) -> list[dict[str, Any]]:
    if not isinstance(values, list | tuple):
        return []
    return [dict(item) for item in values if isinstance(item, dict)]


@dataclass
class FunctionSemanticRecord:
    function: str
    call_sites: list[str] = field(default_factory=list)
    input_sources: list[str] = field(default_factory=list)
    output_sinks: list[str] = field(default_factory=list)
    stack_slots_read: list[str] = field(default_factory=list)
    stack_slots_written: list[str] = field(default_factory=list)
    registers_read: list[str] = field(default_factory=list)
    registers_written: list[str] = field(default_factory=list)
    memory_writes: list[dict[str, Any]] = field(default_factory=list)
    candidate_dependent: bool = False
    semantic_guess: str = "unknown_but_bounded"
    confidence: str = "low"
    positive_evidence: list[str] = field(default_factory=list)
    negative_evidence: list[str] = field(default_factory=list)
    next_required_evidence: list[str] = field(default_factory=list)
    instruction_confirmed: bool = False
    hookable: bool = False
    connects_to_compare_lhs: bool = False
    connects_to_transform_chain: bool = False
    material_hook_candidate_status: str = "not_ready"

    def to_dict(self) -> dict[str, Any]:
        semantic_guess = (
            self.semantic_guess
            if self.semantic_guess in ALLOWED_SEMANTIC_GUESSES
            else "unknown_but_bounded"
        )
        return {
            "function": str(self.function).strip(),
            "call_sites": _strings(self.call_sites),
            "input_sources": _strings(self.input_sources),
            "output_sinks": _strings(self.output_sinks),
            "stack_slots_read": _strings(self.stack_slots_read),
            "stack_slots_written": _strings(self.stack_slots_written),
            "registers_read": _strings(self.registers_read),
            "registers_written": _strings(self.registers_written),
            "memory_writes": _dicts(self.memory_writes),
            "candidate_dependent": bool(self.candidate_dependent),
            "semantic_guess": semantic_guess,
            "confidence": str(self.confidence or "low"),
            "positive_evidence": _strings(self.positive_evidence),
            "negative_evidence": _strings(self.negative_evidence),
            "next_required_evidence": _strings(self.next_required_evidence),
            "instruction_confirmed": bool(self.instruction_confirmed),
            "hookable": bool(self.hookable),
            "connects_to_compare_lhs": bool(self.connects_to_compare_lhs),
            "connects_to_transform_chain": bool(self.connects_to_transform_chain),
            "material_hook_candidate_status": str(self.material_hook_candidate_status or "not_ready"),
        }


def normalize_function_semantic_record(record: FunctionSemanticRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record, FunctionSemanticRecord):
        return record.to_dict()
    data = record if isinstance(record, dict) else {}
    normalized = FunctionSemanticRecord(
        function=str(data.get("function", "")).strip(),
        call_sites=_strings(data.get("call_sites", [])),
        input_sources=_strings(data.get("input_sources", [])),
        output_sinks=_strings(data.get("output_sinks", [])),
        stack_slots_read=_strings(data.get("stack_slots_read", [])),
        stack_slots_written=_strings(data.get("stack_slots_written", [])),
        registers_read=_strings(data.get("registers_read", [])),
        registers_written=_strings(data.get("registers_written", [])),
        memory_writes=_dicts(data.get("memory_writes", [])),
        candidate_dependent=bool(data.get("candidate_dependent")),
        semantic_guess=str(data.get("semantic_guess") or "unknown_but_bounded"),
        confidence=str(data.get("confidence") or "low"),
        positive_evidence=_strings(data.get("positive_evidence", [])),
        negative_evidence=_strings(data.get("negative_evidence", [])),
        next_required_evidence=_strings(data.get("next_required_evidence", [])),
        instruction_confirmed=bool(data.get("instruction_confirmed")),
        hookable=bool(data.get("hookable")),
        connects_to_compare_lhs=bool(data.get("connects_to_compare_lhs")),
        connects_to_transform_chain=bool(data.get("connects_to_transform_chain")),
        material_hook_candidate_status=str(data.get("material_hook_candidate_status") or "not_ready"),
    )
    return normalized.to_dict()


def is_material_hook_ready(record: dict[str, Any]) -> bool:
    semantic_guess = str(record.get("semantic_guess") or "")
    return (
        semantic_guess in MATERIAL_SEMANTIC_GUESSES
        and bool(record.get("instruction_confirmed"))
        and bool(record.get("hookable"))
        and bool(record.get("candidate_dependent"))
        and (
            bool(record.get("connects_to_compare_lhs"))
            or bool(record.get("connects_to_transform_chain"))
        )
    )


def compute_breakpoint_probe_allowed(records: Iterable[dict[str, Any]]) -> bool:
    return any(is_material_hook_ready(record) for record in records)


def normalize_function_semantic_audit(payload: dict[str, Any]) -> dict[str, Any]:
    functions = [
        normalize_function_semantic_record(item)
        for item in payload.get("functions", [])
        if isinstance(item, dict)
    ]
    material_hook_candidates = [
        item for item in functions if is_material_hook_ready(item)
    ]
    classification = str(payload.get("classification") or "").strip()
    if classification not in ALLOWED_AUDIT_CLASSIFICATIONS:
        classification = "material_hook_ready" if material_hook_candidates else "evidence_insufficient"
    return {
        "artifact_kind": FUNCTION_SEMANTIC_AUDIT_KIND,
        "classification": classification,
        "sample": str(payload.get("sample") or ""),
        "profile": str(payload.get("profile") or ""),
        "run_name": str(payload.get("run_name") or ""),
        "target_functions": _strings(payload.get("target_functions", [])),
        "functions": functions,
        "function_count": len(functions),
        "material_pipeline_hypothesis": _strings(payload.get("material_pipeline_hypothesis", [])),
        "material_hook_candidates": material_hook_candidates,
        "material_hook_candidate_count": len(material_hook_candidates),
        "breakpoint_probe_allowed": compute_breakpoint_probe_allowed(functions),
        "top_semantic_guesses": _top_semantic_guesses(functions),
        "dataflow_summary": dict(payload.get("dataflow_summary", {}))
        if isinstance(payload.get("dataflow_summary"), dict)
        else {},
        "negative_evidence": _strings(payload.get("negative_evidence", [])),
        "next_bounded_action": str(payload.get("next_bounded_action") or ""),
        "promotable_validations": [],
    }


def _top_semantic_guesses(functions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "function": item.get("function"),
            "semantic_guess": item.get("semantic_guess"),
            "confidence": item.get("confidence"),
            "candidate_dependent": item.get("candidate_dependent"),
            "material_hook_candidate_status": item.get("material_hook_candidate_status"),
        }
        for item in functions
    ]
    return rows[:8]
