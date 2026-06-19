from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Material evidence kind constants for Base64/RC4/UTF-16LE material probes
EVIDENCE_KIND_CANDIDATE = "CandidateEvidence"
EVIDENCE_KIND_RUNTIME_COMPARE = "RuntimeCompareEvidence"
EVIDENCE_KIND_STATIC_STRING = "StaticStringEvidence"
EVIDENCE_KIND_CONSTRAINT = "ConstraintEvidence"
EVIDENCE_KIND_BASE64_MATERIAL = "Base64MaterialEvidence"
EVIDENCE_KIND_RC4_MATERIAL = "RC4MaterialEvidence"
EVIDENCE_KIND_UTF16LE_MATERIAL = "UTF16LEMaterialEvidence"


@dataclass
class StructuredEvidence:
    kind: str
    source_tool: str
    summary: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    derived_candidates: list[str] = field(default_factory=list)


def base64_material_evidence(
    source_tool: str,
    *,
    construction_point: str = "",
    input_bytes_hex: str = "",
    output_chars: str = "",
    chunk_boundary_info: dict[str, Any] | None = None,
    instruction_address: str = "",
    confidence: float | None = None,
    derived_candidates: list[str] | None = None,
) -> StructuredEvidence:
    """Create a Base64MaterialEvidence record from material probe data."""
    payload: dict[str, Any] = {
        "construction_point": construction_point,
        "input_bytes_hex": input_bytes_hex,
        "output_chars": output_chars,
        "instruction_address": instruction_address,
    }
    if chunk_boundary_info is not None:
        payload["chunk_boundary_info"] = chunk_boundary_info
    summary_parts: list[str] = []
    if construction_point:
        summary_parts.append(f"Base64 {construction_point}")
    if instruction_address:
        summary_parts.append(f"@ {instruction_address}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_BASE64_MATERIAL,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} Base64 material",
        confidence=confidence,
        payload=payload,
        derived_candidates=derived_candidates or [],
    )


def rc4_material_evidence(
    source_tool: str,
    *,
    ksa_point: str = "",
    prga_point: str = "",
    key_material_hex: str = "",
    input_bytes_hex: str = "",
    output_bytes_hex: str = "",
    instruction_address: str = "",
    confidence: float | None = None,
    derived_candidates: list[str] | None = None,
) -> StructuredEvidence:
    """Create a RC4MaterialEvidence record from material probe data."""
    payload: dict[str, Any] = {
        "ksa_point": ksa_point,
        "prga_point": prga_point,
        "key_material_hex": key_material_hex,
        "input_bytes_hex": input_bytes_hex,
        "output_bytes_hex": output_bytes_hex,
        "instruction_address": instruction_address,
    }
    summary_parts: list[str] = []
    if ksa_point:
        summary_parts.append(f"RC4 KSA {ksa_point}")
    if prga_point:
        summary_parts.append(f"PRGA {prga_point}")
    if instruction_address:
        summary_parts.append(f"@ {instruction_address}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_RC4_MATERIAL,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} RC4 material",
        confidence=confidence,
        payload=payload,
        derived_candidates=derived_candidates or [],
    )


def utf16le_material_evidence(
    source_tool: str,
    *,
    expansion_point: str = "",
    source_bytes_hex: str = "",
    wide_chars: str = "",
    instruction_address: str = "",
    confidence: float | None = None,
    derived_candidates: list[str] | None = None,
) -> StructuredEvidence:
    """Create a UTF16LEMaterialEvidence record from material probe data."""
    payload: dict[str, Any] = {
        "expansion_point": expansion_point,
        "source_bytes_hex": source_bytes_hex,
        "wide_chars": wide_chars,
        "instruction_address": instruction_address,
    }
    summary_parts: list[str] = []
    if expansion_point:
        summary_parts.append(f"UTF-16LE {expansion_point}")
    if instruction_address:
        summary_parts.append(f"@ {instruction_address}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_UTF16LE_MATERIAL,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} UTF-16LE material",
        confidence=confidence,
        payload=payload,
        derived_candidates=derived_candidates or [],
    )


# Static evidence kind constants for the generic static evidence bridge.
# These extend the material evidence kinds above and remain compatible with
# the existing StructuredEvidence dataclass fields.
EVIDENCE_KIND_STATIC_INPUT = "StaticInputEvidence"
EVIDENCE_KIND_STATIC_COMPARE = "StaticCompareEvidence"
EVIDENCE_KIND_STATIC_CONSTANT = "StaticConstantEvidence"
EVIDENCE_KIND_STATIC_TRANSFORM_HINT = "StaticTransformHintEvidence"
EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE = "StaticCryptoSignatureEvidence"
EVIDENCE_KIND_STATIC_GUI_INPUT = "StaticGuiInputEvidence"
EVIDENCE_KIND_STATIC_ANTI_DEBUG = "StaticAntiDebugEvidence"


def static_input_evidence(
    source_tool: str,
    *,
    input_apis: list[str] | None = None,
    prompt_strings: list[str] | None = None,
    input_buffer_address: str = "",
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticInputEvidence record from static triage data."""
    payload: dict[str, Any] = {
        "input_apis": list(input_apis or []),
        "prompt_strings": list(prompt_strings or []),
        "input_buffer_address": input_buffer_address,
    }
    summary_parts: list[str] = []
    if input_apis:
        summary_parts.append(f"input APIs: {', '.join(input_apis[:4])}")
    if prompt_strings:
        summary_parts.append(f"prompts: {', '.join(prompt_strings[:2])}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_INPUT,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static input evidence",
        confidence=confidence,
        payload=payload,
    )


def static_compare_evidence(
    source_tool: str,
    *,
    compare_apis: list[str] | None = None,
    compare_callsites: list[dict[str, Any]] | None = None,
    expected_value_location: str = "",
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticCompareEvidence record from static triage data."""
    payload: dict[str, Any] = {
        "compare_apis": list(compare_apis or []),
        "compare_callsites": list(compare_callsites or []),
        "expected_value_location": expected_value_location,
    }
    summary_parts: list[str] = []
    if compare_apis:
        summary_parts.append(f"compare APIs: {', '.join(compare_apis[:4])}")
    if compare_callsites:
        summary_parts.append(f"{len(compare_callsites)} callsite(s)")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_COMPARE,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static compare evidence",
        confidence=confidence,
        payload=payload,
    )


def static_constant_evidence(
    source_tool: str,
    *,
    constants: list[Any] | None = None,
    constant_table_kind: str = "",
    table_address: str = "",
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticConstantEvidence record from static triage data."""
    payload: dict[str, Any] = {
        "constants": list(constants or []),
        "constant_table_kind": constant_table_kind,
        "table_address": table_address,
    }
    summary_parts: list[str] = []
    if constant_table_kind:
        summary_parts.append(f"table: {constant_table_kind}")
    if constants:
        summary_parts.append(f"{len(constants)} constant(s)")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_CONSTANT,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static constant evidence",
        confidence=confidence,
        payload=payload,
    )


def static_transform_hint_evidence(
    source_tool: str,
    *,
    transform_kind: str = "",
    loop_evidence: list[str] | None = None,
    arithmetic_ops: list[str] | None = None,
    bitwise_ops: list[str] | None = None,
    table_lookup: bool = False,
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticTransformHintEvidence record from static triage data.

    Transform hints are conservative: they recommend a solver profile but do
    not make the plan solve-ready without sufficient constants and provenance.
    """
    payload: dict[str, Any] = {
        "transform_kind": transform_kind,
        "loop_evidence": list(loop_evidence or []),
        "arithmetic_ops": list(arithmetic_ops or []),
        "bitwise_ops": list(bitwise_ops or []),
        "table_lookup": table_lookup,
    }
    summary_parts: list[str] = []
    if transform_kind:
        summary_parts.append(f"transform: {transform_kind}")
    if table_lookup:
        summary_parts.append("table lookup")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_TRANSFORM_HINT,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static transform hint",
        confidence=confidence,
        payload=payload,
    )


def static_crypto_signature_evidence(
    source_tool: str,
    *,
    algorithm: str = "",
    markers: list[str] | None = None,
    marker_confidence: str = "",
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticCryptoSignatureEvidence record from static triage data.

    Crypto signatures are profile hints only unless enough structured material
    exists to confirm the algorithm and locate key material.
    """
    payload: dict[str, Any] = {
        "algorithm": algorithm,
        "markers": list(markers or []),
        "marker_confidence": marker_confidence,
    }
    summary_parts: list[str] = []
    if algorithm:
        summary_parts.append(f"algorithm: {algorithm}")
    if markers:
        summary_parts.append(f"{len(markers)} marker(s)")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static crypto signature",
        confidence=confidence,
        payload=payload,
    )


def static_gui_input_evidence(
    source_tool: str,
    *,
    gui_apis: list[str] | None = None,
    gui_strings: list[str] | None = None,
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticGuiInputEvidence record from static triage data."""
    payload: dict[str, Any] = {
        "gui_apis": list(gui_apis or []),
        "gui_strings": list(gui_strings or []),
    }
    summary_parts: list[str] = []
    if gui_apis:
        summary_parts.append(f"GUI APIs: {', '.join(gui_apis[:4])}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_GUI_INPUT,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static GUI input evidence",
        confidence=confidence,
        payload=payload,
    )


def static_anti_debug_evidence(
    source_tool: str,
    *,
    anti_debug_apis: list[str] | None = None,
    anti_debug_strings: list[str] | None = None,
    confidence: float | None = None,
) -> StructuredEvidence:
    """Create a StaticAntiDebugEvidence record from static triage data."""
    payload: dict[str, Any] = {
        "anti_debug_apis": list(anti_debug_apis or []),
        "anti_debug_strings": list(anti_debug_strings or []),
    }
    summary_parts: list[str] = []
    if anti_debug_apis:
        summary_parts.append(f"anti-debug APIs: {', '.join(anti_debug_apis[:4])}")
    return StructuredEvidence(
        kind=EVIDENCE_KIND_STATIC_ANTI_DEBUG,
        source_tool=source_tool,
        summary=" ".join(summary_parts) or f"{source_tool} static anti-debug evidence",
        confidence=confidence,
        payload=payload,
    )


def collect_derived_candidates(items: list[StructuredEvidence]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for item in items:
        for candidate in item.derived_candidates:
            text = str(candidate).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            values.append(text)
    return values
