"""Solver dispatch plan produced by the static evidence bridge.

A :class:`SolverDispatchPlan` records the readiness state, recommended solver
profiles, missing evidence, source artifacts, and provenance notes for a set
of :class:`~reverse_agent.evidence.StructuredEvidence` records.  The plan is
intentionally conservative: it recommends solver profiles but never claims to
be solve-ready unless sufficient current evidence with provenance exists.

This module does not run solvers, samples, or external reverse-engineering
tools.  It only normalizes evidence into a dispatch hint for downstream
``reverse_solving`` rounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evidence import (
    EVIDENCE_KIND_STATIC_ANTI_DEBUG,
    EVIDENCE_KIND_STATIC_COMPARE,
    EVIDENCE_KIND_STATIC_CONSTANT,
    EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE,
    EVIDENCE_KIND_STATIC_GUI_INPUT,
    EVIDENCE_KIND_STATIC_INPUT,
    EVIDENCE_KIND_STATIC_TRANSFORM_HINT,
    StructuredEvidence,
)


# Readiness states.  ``solver_profile_hint_only`` is the most conservative and
# is the default for static-only evidence without current provenance.
READINESS_NOT_SOLVE_READY = "not_solve_ready"
READINESS_NEEDS_CURRENT_STATIC_PROVENANCE = "needs_current_static_provenance"
READINESS_SOLVER_PROFILE_HINT_ONLY = "solver_profile_hint_only"

_VALID_READINESS = {
    READINESS_NOT_SOLVE_READY,
    READINESS_NEEDS_CURRENT_STATIC_PROVENANCE,
    READINESS_SOLVER_PROFILE_HINT_ONLY,
}

# Solver profile names that the bridge can recommend.  These are generic
# profile hints, not solver implementations.
PROFILE_STRING_COMPARE = "string_compare"
PROFILE_XOR = "xor"
PROFILE_AFFINE_SHIFT = "affine_shift"
PROFILE_LOOKUP_TABLE = "lookup_table"
PROFILE_RC4 = "rc4"
PROFILE_DES = "des"
PROFILE_AES = "aes"
PROFILE_HASH = "hash"
PROFILE_GUI_CHECK = "gui_check"
PROFILE_ANTI_DEBUG_PRECONDITION = "anti_debug_precondition"


# Mapping from crypto algorithm strings (lowercased) to solver profiles.
_CRYPTO_PROFILE_MAP = {
    "rc4": PROFILE_RC4,
    "des": PROFILE_DES,
    "aes": PROFILE_AES,
    "md5": PROFILE_HASH,
    "sha1": PROFILE_HASH,
    "sha256": PROFILE_HASH,
    "sha": PROFILE_HASH,
}

# Mapping from transform_kind strings (lowercased) to solver profiles.
_TRANSFORM_PROFILE_MAP = {
    "xor": PROFILE_XOR,
    "affine": PROFILE_AFFINE_SHIFT,
    "shift": PROFILE_AFFINE_SHIFT,
    "lookup": PROFILE_LOOKUP_TABLE,
    "table": PROFILE_LOOKUP_TABLE,
}


@dataclass
class SolverDispatchPlan:
    """Conservative solver dispatch plan derived from structured evidence.

    Attributes:
        readiness: one of ``not_solve_ready``, ``needs_current_static_provenance``,
            ``solver_profile_hint_only``.
        recommended_solver_profiles: generic solver profile hints.
        required_missing_evidence: evidence families still needed before
            solving.
        source_artifacts: identifiers of the source artifacts used.
        provenance_notes: human-readable provenance and freshness notes.
    """

    readiness: str = READINESS_SOLVER_PROFILE_HINT_ONLY
    recommended_solver_profiles: list[str] = field(default_factory=list)
    required_missing_evidence: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    provenance_notes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        """Raise ValueError if the plan is internally inconsistent."""
        if self.readiness not in _VALID_READINESS:
            raise ValueError(
                f"invalid readiness state: {self.readiness!r}; "
                f"expected one of {sorted(_VALID_READINESS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        self.validate()
        return {
            "readiness": self.readiness,
            "recommended_solver_profiles": list(self.recommended_solver_profiles),
            "required_missing_evidence": list(self.required_missing_evidence),
            "source_artifacts": list(self.source_artifacts),
            "provenance_notes": list(self.provenance_notes),
        }


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_solver_dispatch_plan(
    evidence: list[StructuredEvidence],
    *,
    source_artifacts: list[str] | None = None,
    provenance_notes: list[str] | None = None,
    has_current_provenance: bool = False,
) -> SolverDispatchPlan:
    """Build a conservative :class:`SolverDispatchPlan` from evidence.

    The plan never claims solve-readiness for static-only evidence.  When
    ``has_current_provenance`` is False (the default), readiness is at most
    ``needs_current_static_provenance``.
    """
    profiles: list[str] = []
    missing: list[str] = []
    has_input = False
    has_compare = False
    has_constant = False
    has_transform = False
    has_crypto = False
    has_gui = False
    has_anti_debug = False

    for ev in evidence:
        kind = ev.kind
        if kind == EVIDENCE_KIND_STATIC_INPUT:
            has_input = True
        elif kind == EVIDENCE_KIND_STATIC_COMPARE:
            has_compare = True
            profiles.append(PROFILE_STRING_COMPARE)
        elif kind == EVIDENCE_KIND_STATIC_CONSTANT:
            has_constant = True
        elif kind == EVIDENCE_KIND_STATIC_TRANSFORM_HINT:
            has_transform = True
            transform_kind = str(ev.payload.get("transform_kind", "")).lower()
            profile = _TRANSFORM_PROFILE_MAP.get(transform_kind)
            if profile:
                profiles.append(profile)
            if ev.payload.get("table_lookup"):
                profiles.append(PROFILE_LOOKUP_TABLE)
        elif kind == EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE:
            has_crypto = True
            algorithm = str(ev.payload.get("algorithm", "")).lower()
            profile = _CRYPTO_PROFILE_MAP.get(algorithm)
            if profile:
                profiles.append(profile)
        elif kind == EVIDENCE_KIND_STATIC_GUI_INPUT:
            has_gui = True
            profiles.append(PROFILE_GUI_CHECK)
        elif kind == EVIDENCE_KIND_STATIC_ANTI_DEBUG:
            has_anti_debug = True
            profiles.append(PROFILE_ANTI_DEBUG_PRECONDITION)

    # Determine missing evidence required before solving.
    if not has_input and not has_gui:
        missing.append("input_source_evidence")
    if not has_compare:
        missing.append("comparison_sink_evidence")
    if has_crypto and not has_constant:
        missing.append("key_or_constant_evidence")
    if has_transform and not has_constant:
        missing.append("transform_constant_evidence")

    profiles = _dedupe_preserve_order(profiles)

    if has_current_provenance and not missing:
        readiness = READINESS_SOLVER_PROFILE_HINT_ONLY
    elif has_current_provenance:
        readiness = READINESS_NEEDS_CURRENT_STATIC_PROVENANCE
    else:
        readiness = READINESS_NEEDS_CURRENT_STATIC_PROVENANCE

    plan = SolverDispatchPlan(
        readiness=readiness,
        recommended_solver_profiles=profiles,
        required_missing_evidence=missing,
        source_artifacts=list(source_artifacts or []),
        provenance_notes=list(provenance_notes or []),
    )
    plan.validate()
    return plan
