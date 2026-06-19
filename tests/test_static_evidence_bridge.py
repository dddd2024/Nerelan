"""Tests for reverse_agent.static_evidence_bridge.

Acceptance cases follow decision_packet.md section 6 (Implementation Scope):
1. Synthetic triage with __input + _strncmp + compare context.
2. Synthetic xor/arithmetic loop artifact.
3. Synthetic RC4-like artifact.
4. Historical affine_8cfebe03 fixture (acceptance only; no production hardcode).
5. No test executes a binary or launches IDA/Ghidra/debugger.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.evidence import (
    EVIDENCE_KIND_STATIC_ANTI_DEBUG,
    EVIDENCE_KIND_STATIC_COMPARE,
    EVIDENCE_KIND_STATIC_CONSTANT,
    EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE,
    EVIDENCE_KIND_STATIC_GUI_INPUT,
    EVIDENCE_KIND_STATIC_INPUT,
    EVIDENCE_KIND_STATIC_TRANSFORM_HINT,
)
from reverse_agent.solver_dispatch_plan import (
    PROFILE_RC4,
    PROFILE_STRING_COMPARE,
    PROFILE_XOR,
    READINESS_NEEDS_CURRENT_STATIC_PROVENANCE,
    READINESS_SOLVER_PROFILE_HINT_ONLY,
)
from reverse_agent.static_evidence_bridge import BridgeResult, StaticEvidenceBridge

REPO_ROOT = Path(__file__).resolve().parents[1]
AFFINE_FIXTURE = REPO_ROOT / "project_state" / "local_reverse_affine_8cfebe03_static_triage.json"


def _bridge():
    return StaticEvidenceBridge()


# --- Acceptance case 1: input + compare -> string_compare ------------------

def test_synthetic_input_and_compare_yields_string_compare():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "input_apis": ["__input"],
            "interesting_strings": [
                {"value": "please input a string:"},
            ],
            "functions": [
                {"name": "__input"},
                {"name": "_strncmp"},
            ],
            "compare_contexts": [
                {
                    "call_ea": "0x40620E",
                    "caller_func": "sub_406150",
                    "callee": "_strncmp",
                    "ref_strings": "__GLOBAL_HEAP_SELECTED",
                }
            ],
        },
    }
    result = _bridge().convert(artifact, source_artifact_id="synthetic_triage.json")
    assert isinstance(result, BridgeResult)
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_INPUT in kinds
    assert EVIDENCE_KIND_STATIC_COMPARE in kinds
    assert result.plan is not None
    assert PROFILE_STRING_COMPARE in result.plan.recommended_solver_profiles


# --- Acceptance case 2: xor/arithmetic loop -> transform hint -------------

def test_synthetic_xor_loop_yields_transform_hint():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "input_apis": ["scanf"],
            "interesting_strings": [],
            "functions": [{"name": "sub_401000"}],
            "compare_contexts": [{"callee": "memcmp"}],
            "decompiler_snippets": [
                {
                    "function": "sub_401000",
                    "text": "for (int i = 0; i < len; i++) { out[i] = in[i] ^ key[i]; }",
                }
            ],
        },
    }
    result = _bridge().convert(artifact, source_artifact_id="xor_loop.json")
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_TRANSFORM_HINT in kinds
    assert PROFILE_XOR in result.plan.recommended_solver_profiles
    # Without constants, plan is not solve-ready.
    assert result.plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE
    assert "transform_constant_evidence" in result.plan.required_missing_evidence


def test_synthetic_xor_with_constants_still_hint_only():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "input_apis": ["scanf"],
            "functions": [{"name": "sub_401000"}],
            "compare_contexts": [{"callee": "memcmp"}],
            "decompiler_snippets": [
                {
                    "function": "sub_401000",
                    "text": "v = a ^ 0x5A;",
                }
            ],
        },
        "constants": [0x5A],
    }
    result = _bridge().convert(artifact, has_current_provenance=True)
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_CONSTANT in kinds
    assert EVIDENCE_KIND_STATIC_TRANSFORM_HINT in kinds
    # Even with constants + provenance, static-only evidence stays hint-only.
    assert result.plan.readiness == READINESS_SOLVER_PROFILE_HINT_ONLY


# --- Acceptance case 3: RC4-like -> crypto signature hint -----------------

def test_synthetic_rc4_yields_crypto_signature_hint():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "input_apis": ["scanf"],
            "interesting_strings": [
                {"value": "rc4"},
                {"value": "RC4 KSA initialization"},
            ],
            "functions": [{"name": "_strncmp"}],
            "compare_contexts": [{"callee": "_strncmp"}],
            "decompiler_snippets": [
                {
                    "function": "sub_402000",
                    "text": "for (i = 0; i < 256; i++) S[i] = i; // KSA",
                }
            ],
        },
    }
    result = _bridge().convert(artifact, source_artifact_id="rc4_like.json")
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE in kinds
    assert PROFILE_RC4 in result.plan.recommended_solver_profiles
    # RC4 without key/constant evidence -> missing key_or_constant_evidence.
    assert "key_or_constant_evidence" in result.plan.required_missing_evidence
    # Static-only -> not solve-ready.
    assert result.plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE


# --- Acceptance case 4: historical affine fixture -------------------------

@pytest.mark.skipif(
    not AFFINE_FIXTURE.exists(),
    reason="affine_8cfebe03 fixture not present; skipping historical acceptance",
)
def test_historical_affine_fixture_parses_but_not_solve_ready():
    """Historical affine fixture parses into evidence + plan, but readiness
    must be no stronger than needs_current_static_provenance unless rebuilt
    in this round."""
    artifact = json.loads(AFFINE_FIXTURE.read_text(encoding="utf-8"))
    result = _bridge().convert(
        artifact,
        source_artifact_id=str(AFFINE_FIXTURE.relative_to(REPO_ROOT)).replace("\\", "/"),
        has_current_provenance=False,
    )
    kinds = {e.kind for e in result.evidence}
    # The fixture has __input and _strncmp.
    assert EVIDENCE_KIND_STATIC_INPUT in kinds
    assert EVIDENCE_KIND_STATIC_COMPARE in kinds
    assert PROFILE_STRING_COMPARE in result.plan.recommended_solver_profiles
    # Historical artifact without current provenance -> not solve-ready.
    assert result.plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE
    # Provenance note records static-only status.
    assert any("static-only" in note for note in result.plan.provenance_notes)


# --- Acceptance case 5: no binary/tool execution --------------------------

def test_bridge_does_not_require_external_tools():
    """The bridge is pure-Python and never launches external tools."""
    artifact = {"source_tool": "static", "triage": {"input_apis": ["scanf"]}}
    result = _bridge().convert(artifact)
    assert result.evidence
    assert result.plan is not None


# --- Additional coverage ---------------------------------------------------

def test_bridge_rejects_non_dict():
    with pytest.raises(TypeError):
        _bridge().convert("not a dict")  # type: ignore[arg-type]


def test_bridge_handles_empty_artifact():
    result = _bridge().convert({})
    assert result.evidence == []
    assert result.plan is not None
    assert result.plan.readiness == READINESS_NEEDS_CURRENT_STATIC_PROVENANCE


def test_bridge_detects_gui_input():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "functions": [{"name": "GetDlgItemTextA"}],
            "interesting_strings": [{"value": "dialog window"}],
        },
    }
    result = _bridge().convert(artifact)
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_GUI_INPUT in kinds


def test_bridge_detects_anti_debug():
    artifact = {
        "source_tool": "IDA",
        "triage": {
            "functions": [{"name": "IsDebuggerPresent"}],
            "interesting_strings": [{"value": "DebugBreak"}],
        },
    }
    result = _bridge().convert(artifact)
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_ANTI_DEBUG in kinds


def test_bridge_evidence_summary_schema():
    """Bridge handles the static_evidence_summary schema."""
    artifact = {
        "source_tool": "IDA",
        "evidence_summary": {
            "key_strings": ["please input a string:", "flag"],
            "compare_contexts": [{"callee": "_strncmp"}],
        },
    }
    result = _bridge().convert(artifact)
    kinds = {e.kind for e in result.evidence}
    assert EVIDENCE_KIND_STATIC_INPUT in kinds
    assert EVIDENCE_KIND_STATIC_COMPARE in kinds


def test_bridge_result_to_dict():
    artifact = {"source_tool": "IDA", "triage": {"input_apis": ["scanf"]}}
    result = _bridge().convert(artifact)
    d = result.to_dict()
    assert "evidence" in d
    assert "plan" in d
    assert isinstance(d["evidence"], list)
    assert d["plan"] is not None


def test_bridge_provenance_notes_include_source():
    artifact = {"source_tool": "IDA", "triage": {"input_apis": ["scanf"]}}
    result = _bridge().convert(artifact, source_artifact_id="triage.json")
    assert any("triage.json" in note for note in result.plan.provenance_notes)


def test_bridge_runtime_validated_false_note():
    artifact = {
        "source_tool": "IDA",
        "runtime_validated": False,
        "triage": {"input_apis": ["scanf"]},
    }
    result = _bridge().convert(artifact)
    assert any("runtime_validated=false" in note for note in result.plan.provenance_notes)
