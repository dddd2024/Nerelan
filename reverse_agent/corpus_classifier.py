"""Corpus classifier for reverse engineering samples.

This module provides rule-based classification of reverse engineering samples
based on static features. Classifications are hints, not definitive conclusions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reverse_agent.static_feature_extractor import StaticFeatures, extract_static_features


# Classification categories
CATEGORIES = [
    "affine_lowercase",
    "caesar_or_shift",
    "xor_or_bytewise",
    "hash_check",
    "rc4_like",
    "des_like",
    "aes_like",
    "base64_or_encoding",
    "seh_or_exception",
    "string_compare",
    "unknown",
]


@dataclass
class ClassificationResult:
    """Classification result for a sample."""

    case_id: str
    predicted_category: str
    confidence: str  # high, medium, low
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommended_next_step: str = ""


def classify_from_filename(case_id: str) -> tuple[str, str, list[dict[str, Any]]]:
    """Extract weak hints from filename.

    Args:
        case_id: The case ID (often derived from filename)

    Returns:
        Tuple of (category, confidence, evidence)
    """
    case_lower = case_id.lower()
    evidence = []

    # Weak hints from filename
    if "rc4" in case_lower or "rc4enc" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'rc4'",
            "strength": "weak",
        })
        return "rc4_like", "low", evidence

    if "des" in case_lower or "desenc" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'des'",
            "strength": "weak",
        })
        return "des_like", "low", evidence

    if "aes" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'aes'",
            "strength": "weak",
        })
        return "aes_like", "low", evidence

    if "seh" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'seh'",
            "strength": "weak",
        })
        return "seh_or_exception", "low", evidence

    if "hash" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'hash'",
            "strength": "weak",
        })
        return "hash_check", "low", evidence

    if "base64" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'base64'",
            "strength": "weak",
        })
        return "base64_or_encoding", "low", evidence

    if "xor" in case_lower:
        evidence.append({
            "type": "filename",
            "detail": f"Case ID '{case_id}' contains 'xor'",
            "strength": "weak",
        })
        return "xor_or_bytewise", "low", evidence

    return "unknown", "low", []


def classify_from_features(features: StaticFeatures) -> tuple[str, str, list[dict[str, Any]]]:
    """Classify based on static features.

    Args:
        features: Extracted static features

    Returns:
        Tuple of (category, confidence, evidence)
    """
    evidence = []

    # Check for RC4 hints
    rc4_keywords = ["rc4", "ksa", "prga", "sbox", "state"]
    rc4_hits = [h for h in features.crypto_hints if any(k in h["keyword"] for k in rc4_keywords)]
    if rc4_hits:
        evidence.append({
            "type": "crypto_hint",
            "detail": f"Found RC4-related keywords: {[h['keyword'] for h in rc4_hits[:3]]}",
            "strength": "medium",
        })
        return "rc4_like", "medium", evidence

    # Check for DES hints
    des_keywords = ["des", "des_ecb", "des_cbc", "subkey", "permutation"]
    des_hits = [h for h in features.crypto_hints if any(k in h["keyword"] for k in des_keywords)]
    if des_hits:
        evidence.append({
            "type": "crypto_hint",
            "detail": f"Found DES-related keywords: {[h['keyword'] for h in des_hits[:3]]}",
            "strength": "medium",
        })
        return "des_like", "medium", evidence

    # Check for AES hints
    aes_keywords = ["aes", "rijndael", "sbox", "mixcolumns"]
    aes_hits = [h for h in features.crypto_hints if any(k in h["keyword"] for k in aes_keywords)]
    if aes_hits:
        evidence.append({
            "type": "crypto_hint",
            "detail": f"Found AES-related keywords: {[h['keyword'] for h in aes_hits[:3]]}",
            "strength": "medium",
        })
        return "aes_like", "medium", evidence

    # Check for hash hints
    hash_keywords = ["md5", "sha", "sha1", "sha256", "digest", "hash"]
    hash_hits = [h for h in features.crypto_hints if any(k in h["keyword"] for k in hash_keywords)]
    if hash_hits:
        evidence.append({
            "type": "crypto_hint",
            "detail": f"Found hash-related keywords: {[h['keyword'] for h in hash_hits[:3]]}",
            "strength": "medium",
        })
        return "hash_check", "medium", evidence

    # Check for Base64 hints
    base64_keywords = ["base64", "base32", "base16", "encode", "decode"]
    base64_hits = [h for h in features.crypto_hints if any(k in h["keyword"] for k in base64_keywords)]
    base64_constants = [c for c in features.interesting_constants if c.get("kind") == "base64_candidate"]
    if base64_hits or base64_constants:
        evidence.append({
            "type": "crypto_hint",
            "detail": f"Found encoding hints: {[h['keyword'] for h in base64_hits[:3]]}",
            "strength": "medium",
        })
        return "base64_or_encoding", "medium", evidence

    # Check for string comparison hints
    compare_keywords = ["strcmp", "strncmp", "memcmp", "compare", "password", "flag"]
    compare_hits = [h for h in features.compare_hints if any(k in h["keyword"] for k in compare_keywords)]
    if compare_hits:
        evidence.append({
            "type": "compare_hint",
            "detail": f"Found comparison keywords: {[h['keyword'] for h in compare_hits[:3]]}",
            "strength": "medium",
        })
        return "string_compare", "medium", evidence

    # Check for SEH hints (exception handling)
    seh_keywords = ["seh", "exception", "try", "catch", "handler"]
    seh_hits = [h for h in features.keyword_hits if any(k in h["keyword"] for k in seh_hits)]
    if seh_hits:
        evidence.append({
            "type": "keyword_hint",
            "detail": f"Found SEH-related keywords: {[h['keyword'] for h in seh_hits[:3]]}",
            "strength": "medium",
        })
        return "seh_or_exception", "medium", evidence

    # Check for XOR hints in strings
    xor_strings = [s for s in features.ascii_strings_sample if "xor" in s.lower()]
    if xor_strings:
        evidence.append({
            "type": "string_hint",
            "detail": f"Found XOR-related strings",
            "strength": "low",
        })
        return "xor_or_bytewise", "low", evidence

    return "unknown", "low", []


def classify_sample(
    case_id: str,
    features: StaticFeatures,
    notes: str = "",
    codex_task: str = "",
) -> ClassificationResult:
    """Classify a sample based on all available information.

    Classification priority:
    1. Static features (highest confidence if found)
    2. Filename hints (weak evidence, low confidence)
    3. Notes/task content (if available)

    Args:
        case_id: The case ID
        features: Extracted static features
        notes: Optional notes content
        codex_task: Optional codex_task content

    Returns:
        ClassificationResult with category, confidence, and evidence
    """
    all_evidence = []

    # First, try filename hints (for RC4, DES, SEH, etc.)
    filename_category, filename_confidence, filename_evidence = classify_from_filename(case_id)
    all_evidence.extend(filename_evidence)

    # If filename gives a strong hint, use it as base category
    if filename_category != "unknown":
        category = filename_category
        confidence = filename_confidence
    else:
        category = "unknown"
        confidence = "low"

    # Then, try classification from static features
    feature_category, feature_confidence, feature_evidence = classify_from_features(features)
    all_evidence.extend(feature_evidence)

    # If features strongly suggest a different category, consider it
    if feature_category != "unknown" and feature_confidence == "medium":
        if category == "unknown":
            category = feature_category
            confidence = feature_confidence
        elif category == feature_category:
            # Both agree - boost confidence
            confidence = "medium"

    # Check notes and codex_task for additional hints
    notes_lower = (notes or "").lower()
    task_lower = (codex_task or "").lower()

    # Look for explicit mentions in notes/task
    if "affine" in notes_lower or "affine" in task_lower:
        all_evidence.append({
            "type": "notes_hint",
            "detail": "Notes/task mention affine cipher",
            "strength": "medium",
        })
        if category == "unknown":
            category = "affine_lowercase"
            confidence = "medium"

    if "caesar" in notes_lower or "caesar" in task_lower or "rot" in task_lower:
        all_evidence.append({
            "type": "notes_hint",
            "detail": "Notes/task mention Caesar/ROT cipher",
            "strength": "medium",
        })
        if category == "unknown":
            category = "caesar_or_shift"
            confidence = "medium"

    # Final result
    if category == "unknown":
        confidence = "low"
        all_evidence.append({
            "type": "default",
            "detail": "No strong classification indicators found",
            "strength": "none",
        })

    return ClassificationResult(
        case_id=case_id,
        predicted_category=category,
        confidence=confidence,
        evidence=all_evidence,
        recommended_next_step=get_recommended_step(category),
    )


def get_recommended_step(category: str) -> str:
    """Get recommended next step for a category.

    Args:
        category: The predicted category

    Returns:
        Recommended next step description
    """
    recommendations = {
        "affine_lowercase": (
            "Use simple_static_patterns.solve_affine_lowercase() with brute-force "
            "parameter search if target string is known"
        ),
        "caesar_or_shift": (
            "Use simple_static_patterns.solve_caesar_lowercase() or try all 25 shifts"
        ),
        "xor_or_bytewise": (
            "Look for XOR keys in strings/constants; try common keys (0x00-0xFF)"
        ),
        "hash_check": (
            "Extract expected hash from binary; compute input hash and compare"
        ),
        "rc4_like": (
            "Static analysis: look for S-box initialization (KSA) and keystream generation (PRGA). "
            "Key may be in strings or hardcoded. DO NOT assume key is known."
        ),
        "des_like": (
            "Static analysis: look for DES key schedule, S-boxes, or permutation tables. "
            "Key and ciphertext may be in binary. DO NOT assume key is known."
        ),
        "aes_like": (
            "Static analysis: look for AES S-box, MixColumns, or key schedule. "
            "Key may be hardcoded or derived from input."
        ),
        "base64_or_encoding": (
            "Look for Base64 alphabet string in binary; decode any Base64 constants found"
        ),
        "seh_or_exception": (
            "Analyze exception handler structure; control flow may be obfuscated via SEH"
        ),
        "string_compare": (
            "Look for strcmp/memcmp calls; expected string may be nearby in binary"
        ),
        "unknown": (
            "Perform deeper static analysis: check imports, exports, and cross-references"
        ),
    }
    return recommendations.get(category, "Unknown category - manual analysis required")


def classification_to_dict(result: ClassificationResult) -> dict[str, Any]:
    """Convert ClassificationResult to dictionary for JSON serialization.

    Args:
        result: ClassificationResult object

    Returns:
        Dictionary representation
    """
    return {
        "case_id": result.case_id,
        "predicted_category": result.predicted_category,
        "confidence": result.confidence,
        "evidence": result.evidence,
        "recommended_next_step": result.recommended_next_step,
    }
