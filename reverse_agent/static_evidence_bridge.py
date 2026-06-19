"""Generic static evidence bridge.

Converts dict-like static tool artifacts (IDA/Ghidra/strings/objdump/static
triage JSON) into :class:`~reverse_agent.evidence.StructuredEvidence` records
plus a :class:`~reverse_agent.solver_dispatch_plan.SolverDispatchPlan`.

Detection is rule-based on artifact *content*, never on ``sample_id``.  The
bridge does not run IDA, Ghidra, debuggers, solvers, samples, or any external
tool.  It only normalizes already-produced static artifacts.

The bridge is intentionally conservative: transform hints and crypto
signatures recommend solver profiles but do not make the dispatch plan
solve-ready without sufficient constants and provenance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .evidence import (
    StructuredEvidence,
    static_anti_debug_evidence,
    static_compare_evidence,
    static_constant_evidence,
    static_crypto_signature_evidence,
    static_gui_input_evidence,
    static_input_evidence,
    static_transform_hint_evidence,
)
from .solver_dispatch_plan import SolverDispatchPlan, build_solver_dispatch_plan


# --- Rule tables -----------------------------------------------------------

# Input APIs / names that indicate a user-input source.
_INPUT_API_PATTERNS = (
    "scanf",
    "gets",
    "fgets",
    "getchar",
    "readfile",
    "getdlgitemtexta",
    "getdlgitemtextw",
    "getwindowtexta",
    "getwindowtextw",
    "__input",
    "cin",
    "getline",
)

# Prompt-like strings that suggest the program asks for input.
_PROMPT_STRING_PATTERNS = (
    "please input",
    "enter",
    "input",
    "password",
    "passphrase",
    "prompt",
)

# Compare APIs / names that indicate a comparison sink.
_COMPARE_API_PATTERNS = (
    "strcmp",
    "strncmp",
    "memcmp",
    "comparestringa",
    "comparestringw",
    "lstrcmpa",
    "lstrcmpw",
    "lstrcmpia",
    "lstrcmpiw",
)

# GUI-related APIs.
_GUI_API_PATTERNS = (
    "getdlgitemtexta",
    "getdlgitemtextw",
    "getwindowtexta",
    "getwindowtextw",
    "dialogboxparam",
    "createdialogparam",
    "messageboxa",
    "messageboxw",
)

# Anti-debug APIs / strings.
_ANTI_DEBUG_API_PATTERNS = (
    "isdebuggerpresent",
    "checkremotedebuggerpresent",
    "ntsetinformationthread",
    "outputdebugstringa",
    "outputdebugstringw",
    "debugbreak",
)
_ANTI_DEBUG_STRING_PATTERNS = (
    "debugbreak",
    "debugger",
    "beingdebugged",
    "ntglobalflag",
)

# Crypto algorithm markers (lowercased substring match).
_CRYPTO_MARKERS = {
    "rc4": (
        "rc4",
        "ksa",
        "prga",
        "sbox",
    ),
    "des": (
        "des",
        "feistel",
        "sbox",
        "permutation",
    ),
    "aes": (
        "aes",
        "rijndael",
        "sbox",
        "mixcolumns",
    ),
    "md5": ("md5",),
    "sha1": ("sha1",),
    "sha256": ("sha256",),
}

# Transform hints detected from decompiler text / solver hints.
_TRANSFORM_KIND_PATTERNS = {
    "xor": ("xor", "^", "exclusive or"),
    "affine": ("affine", "linear", "ax+b", "a*x+b"),
    "shift": ("shift", "rol", "ror", "<<", ">>"),
    "lookup": ("lookup", "table", "sbox", "substitute"),
}


def _lower(value: Any) -> str:
    return str(value).lower() if value is not None else ""


def _match_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(p in text for p in patterns)


def _extract_strings(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Return interesting string entries from various artifact schemas."""
    # Static triage schema: triage.interesting_strings
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        strings = triage.get("interesting_strings")
        if isinstance(strings, list):
            return [s for s in strings if isinstance(s, dict)]
    # Flat schema: interesting_strings / strings
    for key in ("interesting_strings", "strings"):
        strings = artifact.get(key)
        if isinstance(strings, list):
            return [s for s in strings if isinstance(s, dict)]
    # Evidence summary schema: evidence_summary.key_strings
    evidence_summary = artifact.get("evidence_summary")
    if isinstance(evidence_summary, dict):
        key_strings = evidence_summary.get("key_strings")
        if isinstance(key_strings, list):
            return [{"value": s} for s in key_strings if isinstance(s, str)]
    return []


def _extract_functions(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Return function entries from various artifact schemas."""
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        functions = triage.get("functions")
        if isinstance(functions, list):
            return [f for f in functions if isinstance(f, dict)]
    for key in ("functions",):
        functions = artifact.get(key)
        if isinstance(functions, list):
            return [f for f in functions if isinstance(f, dict)]
    return []


def _extract_compare_contexts(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Return compare callsite entries from various artifact schemas."""
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        contexts = triage.get("compare_contexts")
        if isinstance(contexts, list):
            return [c for c in contexts if isinstance(c, dict)]
    evidence_summary = artifact.get("evidence_summary")
    if isinstance(evidence_summary, dict):
        contexts = evidence_summary.get("compare_contexts")
        if isinstance(contexts, list):
            return [c for c in contexts if isinstance(c, dict)]
    for key in ("compare_contexts",):
        contexts = artifact.get(key)
        if isinstance(contexts, list):
            return [c for c in contexts if isinstance(c, dict)]
    return []


def _extract_input_apis(artifact: dict[str, Any]) -> list[str]:
    """Return input API names from various artifact schemas."""
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        apis = triage.get("input_apis")
        if isinstance(apis, list):
            return [str(a) for a in apis if a]
    for key in ("input_apis",):
        apis = artifact.get(key)
        if isinstance(apis, list):
            return [str(a) for a in apis if a]
    return []


def _extract_solver_hints(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Return solver hint entries from various artifact schemas."""
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        hints = triage.get("solver_hints")
        if isinstance(hints, list):
            return [h for h in hints if isinstance(h, dict)]
    classification = artifact.get("classification")
    if isinstance(classification, dict):
        hints = classification.get("solver_hints")
        if isinstance(hints, list):
            return [h for h in hints if isinstance(h, dict)]
    for key in ("solver_hints",):
        hints = artifact.get(key)
        if isinstance(hints, list):
            return [h for h in hints if isinstance(h, dict)]
    return []


def _extract_decompiler_snippets(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    """Return decompiler snippet entries from various artifact schemas."""
    triage = artifact.get("triage")
    if isinstance(triage, dict):
        snippets = triage.get("decompiler_snippets")
        if isinstance(snippets, list):
            return [s for s in snippets if isinstance(s, dict)]
    for key in ("decompiler_snippets",):
        snippets = artifact.get(key)
        if isinstance(snippets, list):
            return [s for s in snippets if isinstance(s, dict)]
    return []


def _extract_constants(artifact: dict[str, Any]) -> list[Any]:
    """Return constant entries from various artifact schemas."""
    for key in ("constants", "constant_tables"):
        constants = artifact.get(key)
        if isinstance(constants, list):
            return constants
    return []


@dataclass
class BridgeResult:
    """Output of :meth:`StaticEvidenceBridge.convert`."""

    evidence: list[StructuredEvidence] = field(default_factory=list)
    plan: SolverDispatchPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": [
                {
                    "kind": e.kind,
                    "source_tool": e.source_tool,
                    "summary": e.summary,
                    "payload": e.payload,
                    "confidence": e.confidence,
                    "derived_candidates": list(e.derived_candidates),
                }
                for e in self.evidence
            ],
            "plan": self.plan.to_dict() if self.plan else None,
        }


class StaticEvidenceBridge:
    """Generic adapter converting static tool artifacts to evidence + plan.

    The bridge is stateless and reusable.  Detection is rule-based on
    artifact content; it never branches on ``sample_id``.
    """

    def convert(
        self,
        artifact: dict[str, Any],
        *,
        source_artifact_id: str = "",
        source_tool: str = "",
        has_current_provenance: bool = False,
    ) -> BridgeResult:
        """Convert a static artifact dict into evidence and a dispatch plan.

        Args:
            artifact: dict-like static tool output (triage JSON, evidence
                summary JSON, cipher profile JSON, etc.).
            source_artifact_id: identifier of the source artifact for
                provenance.
            source_tool: name of the tool that produced the artifact (e.g.
                ``IDA``).  Falls back to the artifact's ``source_tool`` field.
            has_current_provenance: whether the artifact has current (non-stale)
                provenance.  Defaults to False so plans stay conservative.
        """
        if not isinstance(artifact, dict):
            raise TypeError("artifact must be a dict")

        tool = source_tool or str(artifact.get("source_tool", "")) or "static"
        evidence: list[StructuredEvidence] = []
        provenance_notes: list[str] = []

        strings = _extract_strings(artifact)
        functions = _extract_functions(artifact)
        compare_contexts = _extract_compare_contexts(artifact)
        input_apis = _extract_input_apis(artifact)
        solver_hints = _extract_solver_hints(artifact)
        snippets = _extract_decompiler_snippets(artifact)
        constants = _extract_constants(artifact)

        # --- Input evidence -------------------------------------------------
        detected_input_apis: list[str] = []
        for api in input_apis:
            if _match_any(_lower(api), _INPUT_API_PATTERNS):
                detected_input_apis.append(api)
        # Also scan function names for input APIs.
        for func in functions:
            name = _lower(func.get("name", ""))
            if _match_any(name, _INPUT_API_PATTERNS):
                if func.get("name") not in detected_input_apis:
                    detected_input_apis.append(str(func.get("name")))

        prompt_strings: list[str] = []
        for s in strings:
            value = str(s.get("value", ""))
            if _match_any(_lower(value), _PROMPT_STRING_PATTERNS):
                prompt_strings.append(value)

        if detected_input_apis or prompt_strings:
            evidence.append(
                static_input_evidence(
                    source_tool=tool,
                    input_apis=detected_input_apis,
                    prompt_strings=prompt_strings,
                    confidence=0.7,
                )
            )

        # --- Compare evidence ----------------------------------------------
        detected_compare_apis: list[str] = []
        for ctx in compare_contexts:
            callee = str(ctx.get("callee", ""))
            if callee and callee not in detected_compare_apis:
                detected_compare_apis.append(callee)
        # Also scan function names for compare APIs.
        for func in functions:
            name = _lower(func.get("name", ""))
            if _match_any(name, _COMPARE_API_PATTERNS):
                fname = str(func.get("name"))
                if fname not in detected_compare_apis:
                    detected_compare_apis.append(fname)

        if detected_compare_apis or compare_contexts:
            evidence.append(
                static_compare_evidence(
                    source_tool=tool,
                    compare_apis=detected_compare_apis,
                    compare_callsites=compare_contexts,
                    confidence=0.7,
                )
            )

        # --- Constant evidence ---------------------------------------------
        if constants:
            evidence.append(
                static_constant_evidence(
                    source_tool=tool,
                    constants=constants,
                    constant_table_kind=str(artifact.get("constant_table_kind", "")),
                    confidence=0.6,
                )
            )

        # --- Transform hint evidence ---------------------------------------
        transform_kinds: list[str] = []
        loop_evidence: list[str] = []
        arithmetic_ops: list[str] = []
        bitwise_ops: list[str] = []
        table_lookup = False

        # From solver hints.
        for hint in solver_hints:
            kind = _lower(hint.get("kind", ""))
            reason = _lower(hint.get("reason", ""))
            for tkind, patterns in _TRANSFORM_KIND_PATTERNS.items():
                if _match_any(kind, patterns) or _match_any(reason, patterns):
                    if tkind not in transform_kinds:
                        transform_kinds.append(tkind)
                    if tkind == "lookup":
                        table_lookup = True

        # From decompiler snippets.
        for snippet in snippets:
            text = _lower(snippet.get("text", ""))
            if not text:
                continue
            if "for" in text or "while" in text or "loop" in text:
                loop_evidence.append(str(snippet.get("function", "")))
            if "xor" in text or "^" in text:
                if "xor" not in transform_kinds:
                    transform_kinds.append("xor")
                bitwise_ops.append("xor")
            if "+" in text or "-" in text:
                arithmetic_ops.extend(["add", "sub"])
            if "<<" in text or ">>" in text:
                if "shift" not in transform_kinds:
                    transform_kinds.append("shift")
                bitwise_ops.append("shift")
            if "sbox" in text or "table" in text:
                if "lookup" not in transform_kinds:
                    transform_kinds.append("lookup")
                table_lookup = True

        if transform_kinds or loop_evidence or arithmetic_ops or bitwise_ops:
            evidence.append(
                static_transform_hint_evidence(
                    source_tool=tool,
                    transform_kind=",".join(transform_kinds) if transform_kinds else "",
                    loop_evidence=loop_evidence,
                    arithmetic_ops=arithmetic_ops,
                    bitwise_ops=bitwise_ops,
                    table_lookup=table_lookup,
                    confidence=0.5,
                )
            )

        # --- Crypto signature evidence -------------------------------------
        crypto_found: dict[str, list[str]] = {}
        # Scan strings for crypto markers.
        all_text = " ".join(_lower(s.get("value", "")) for s in strings)
        # Scan function names.
        all_text += " " + " ".join(_lower(f.get("name", "")) for f in functions)
        # Scan solver hints.
        all_text += " " + " ".join(
            _lower(h.get("kind", "")) + " " + _lower(h.get("reason", ""))
            for h in solver_hints
        )

        for algorithm, markers in _CRYPTO_MARKERS.items():
            matched: list[str] = []
            for marker in markers:
                if marker in all_text:
                    matched.append(marker)
            if matched:
                crypto_found[algorithm] = matched

        for algorithm, markers in crypto_found.items():
            marker_confidence = "HIGH" if len(markers) >= 2 else "MEDIUM"
            evidence.append(
                static_crypto_signature_evidence(
                    source_tool=tool,
                    algorithm=algorithm,
                    markers=markers,
                    marker_confidence=marker_confidence,
                    confidence=0.6 if len(markers) >= 2 else 0.4,
                )
            )

        # --- GUI input evidence --------------------------------------------
        gui_apis: list[str] = []
        for func in functions:
            name = _lower(func.get("name", ""))
            if _match_any(name, _GUI_API_PATTERNS):
                gui_apis.append(str(func.get("name")))
        gui_strings: list[str] = []
        for s in strings:
            value = _lower(s.get("value", ""))
            if "dialog" in value or "window" in value or "button" in value:
                gui_strings.append(str(s.get("value")))

        if gui_apis or gui_strings:
            evidence.append(
                static_gui_input_evidence(
                    source_tool=tool,
                    gui_apis=gui_apis,
                    gui_strings=gui_strings,
                    confidence=0.6,
                )
            )

        # --- Anti-debug evidence -------------------------------------------
        anti_debug_apis: list[str] = []
        for func in functions:
            name = _lower(func.get("name", ""))
            if _match_any(name, _ANTI_DEBUG_API_PATTERNS):
                anti_debug_apis.append(str(func.get("name")))
        anti_debug_strings: list[str] = []
        for s in strings:
            value = _lower(s.get("value", ""))
            if _match_any(value, _ANTI_DEBUG_STRING_PATTERNS):
                anti_debug_strings.append(str(s.get("value")))

        if anti_debug_apis or anti_debug_strings:
            evidence.append(
                static_anti_debug_evidence(
                    source_tool=tool,
                    anti_debug_apis=anti_debug_apis,
                    anti_debug_strings=anti_debug_strings,
                    confidence=0.5,
                )
            )

        # --- Provenance notes ----------------------------------------------
        if source_artifact_id:
            provenance_notes.append(f"source_artifact: {source_artifact_id}")
        if not has_current_provenance:
            provenance_notes.append(
                "provenance: static-only; not current reverse-solving evidence "
                "unless rebuilt with current provenance this round"
            )
        if artifact.get("runtime_validated") is False:
            provenance_notes.append("runtime_validated=false; static-only artifact")

        # --- Build dispatch plan -------------------------------------------
        source_artifacts = [source_artifact_id] if source_artifact_id else []
        plan = build_solver_dispatch_plan(
            evidence,
            source_artifacts=source_artifacts,
            provenance_notes=provenance_notes,
            has_current_provenance=has_current_provenance,
        )

        return BridgeResult(evidence=evidence, plan=plan)
