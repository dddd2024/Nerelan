"""Phase C: evidence source normalization.

Normalizes legacy ``required_evidence_source`` values to the three explicit
Phase C sources so that local commands are not falsely represented as CI
evidence (F5).

Legacy values are accepted at parse time and normalized to the canonical
Phase C tokens. Unknown values are rejected.
"""

from __future__ import annotations

NORMALIZED_EVIDENCE_SOURCES = frozenset({
    "local_command_evidence",
    "repository_state_attestation",
    "ci_check_attestation",
})

_LEGACY_TO_NORMALIZED: dict[str, str] = {
    "local_provenance": "local_command_evidence",
    "repository_truth": "repository_state_attestation",
    "exact_head_ci": "ci_check_attestation",
    # Idempotent mappings for already-normalized values.
    "local_command_evidence": "local_command_evidence",
    "repository_state_attestation": "repository_state_attestation",
    "ci_check_attestation": "ci_check_attestation",
}


def normalize_evidence_source(source: str | None) -> str:
    """Normalize a legacy or already-normalized evidence source token.

    Empty/missing sources default to ``local_command_evidence`` (fail-safe
    for commands that predate the structured contract). Unknown values
    raise :class:`ValueError` so callers cannot silently introduce new
    evidence source semantics.
    """

    if not source or not source.strip():
        return "local_command_evidence"
    normalized = _LEGACY_TO_NORMALIZED.get(source)
    if normalized is None:
        raise ValueError(f"invalid_evidence_source:{source}")
    return normalized
