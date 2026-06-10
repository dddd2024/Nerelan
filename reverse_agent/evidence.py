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
