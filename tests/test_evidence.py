"""Tests for the static evidence factory functions in reverse_agent.evidence."""

from __future__ import annotations

from reverse_agent.evidence import (
    EVIDENCE_KIND_BASE64_MATERIAL,
    EVIDENCE_KIND_CANDIDATE,
    EVIDENCE_KIND_RC4_MATERIAL,
    EVIDENCE_KIND_STATIC_ANTI_DEBUG,
    EVIDENCE_KIND_STATIC_COMPARE,
    EVIDENCE_KIND_STATIC_CONSTANT,
    EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE,
    EVIDENCE_KIND_STATIC_GUI_INPUT,
    EVIDENCE_KIND_STATIC_INPUT,
    EVIDENCE_KIND_STATIC_TRANSFORM_HINT,
    EVIDENCE_KIND_UTF16LE_MATERIAL,
    StructuredEvidence,
    base64_material_evidence,
    collect_derived_candidates,
    rc4_material_evidence,
    static_anti_debug_evidence,
    static_compare_evidence,
    static_constant_evidence,
    static_crypto_signature_evidence,
    static_gui_input_evidence,
    static_input_evidence,
    static_transform_hint_evidence,
    utf16le_material_evidence,
)


def test_structured_evidence_default_fields():
    ev = StructuredEvidence(kind="TestEvidence", source_tool="unit")
    assert ev.kind == "TestEvidence"
    assert ev.source_tool == "unit"
    assert ev.summary == ""
    assert ev.payload == {}
    assert ev.confidence is None
    assert ev.derived_candidates == []


def test_static_input_evidence_factory():
    ev = static_input_evidence(
        "IDA",
        input_apis=["scanf", "__input"],
        prompt_strings=["please input a string:"],
        input_buffer_address="0x401000",
        confidence=0.7,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_INPUT
    assert ev.source_tool == "IDA"
    assert ev.payload["input_apis"] == ["scanf", "__input"]
    assert ev.payload["prompt_strings"] == ["please input a string:"]
    assert ev.payload["input_buffer_address"] == "0x401000"
    assert ev.confidence == 0.7
    assert "input APIs" in ev.summary


def test_static_compare_evidence_factory():
    callsites = [{"callee": "_strncmp", "call_ea": "0x40620E"}]
    ev = static_compare_evidence(
        "IDA",
        compare_apis=["_strncmp"],
        compare_callsites=callsites,
        expected_value_location="__GLOBAL_HEAP_SELECTED",
        confidence=0.7,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_COMPARE
    assert ev.payload["compare_apis"] == ["_strncmp"]
    assert ev.payload["compare_callsites"] == callsites
    assert ev.payload["expected_value_location"] == "__GLOBAL_HEAP_SELECTED"
    assert "compare APIs" in ev.summary


def test_static_constant_evidence_factory():
    ev = static_constant_evidence(
        "IDA",
        constants=[0x0E329B23, 0x01, 0x02],
        constant_table_kind="DES_SBOX",
        table_address="0x405000",
        confidence=0.6,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_CONSTANT
    assert ev.payload["constants"] == [0x0E329B23, 0x01, 0x02]
    assert ev.payload["constant_table_kind"] == "DES_SBOX"
    assert ev.payload["table_address"] == "0x405000"


def test_static_transform_hint_evidence_factory():
    ev = static_transform_hint_evidence(
        "IDA",
        transform_kind="xor",
        loop_evidence=["sub_401000"],
        arithmetic_ops=["add"],
        bitwise_ops=["xor"],
        table_lookup=False,
        confidence=0.5,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_TRANSFORM_HINT
    assert ev.payload["transform_kind"] == "xor"
    assert ev.payload["loop_evidence"] == ["sub_401000"]
    assert ev.payload["bitwise_ops"] == ["xor"]
    assert ev.payload["table_lookup"] is False


def test_static_crypto_signature_evidence_factory():
    ev = static_crypto_signature_evidence(
        "IDA",
        algorithm="rc4",
        markers=["ksa", "prga"],
        marker_confidence="HIGH",
        confidence=0.6,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE
    assert ev.payload["algorithm"] == "rc4"
    assert ev.payload["markers"] == ["ksa", "prga"]
    assert ev.payload["marker_confidence"] == "HIGH"


def test_static_gui_input_evidence_factory():
    ev = static_gui_input_evidence(
        "IDA",
        gui_apis=["GetDlgItemTextA"],
        gui_strings=["dialog"],
        confidence=0.6,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_GUI_INPUT
    assert ev.payload["gui_apis"] == ["GetDlgItemTextA"]


def test_static_anti_debug_evidence_factory():
    ev = static_anti_debug_evidence(
        "IDA",
        anti_debug_apis=["IsDebuggerPresent"],
        anti_debug_strings=["DebugBreak"],
        confidence=0.5,
    )
    assert ev.kind == EVIDENCE_KIND_STATIC_ANTI_DEBUG
    assert ev.payload["anti_debug_apis"] == ["IsDebuggerPresent"]


def test_existing_material_factories_unchanged():
    """Backward compatibility: existing factory functions still work."""
    ev = base64_material_evidence("IDA", construction_point="KSA", input_bytes_hex="ab")
    assert ev.kind == EVIDENCE_KIND_BASE64_MATERIAL

    ev2 = rc4_material_evidence("IDA", ksa_point="0x401000")
    assert ev2.kind == EVIDENCE_KIND_RC4_MATERIAL

    ev3 = utf16le_material_evidence("IDA", expansion_point="0x401020")
    assert ev3.kind == EVIDENCE_KIND_UTF16LE_MATERIAL


def test_collect_derived_candidates_dedupes():
    items = [
        StructuredEvidence(
            kind=EVIDENCE_KIND_CANDIDATE,
            source_tool="unit",
            derived_candidates=["abc", "def"],
        ),
        StructuredEvidence(
            kind=EVIDENCE_KIND_CANDIDATE,
            source_tool="unit",
            derived_candidates=["def", "ghi"],
        ),
    ]
    result = collect_derived_candidates(items)
    assert result == ["abc", "def", "ghi"]


def test_new_kind_constants_distinct():
    """All new static evidence kind constants are distinct strings."""
    kinds = {
        EVIDENCE_KIND_STATIC_INPUT,
        EVIDENCE_KIND_STATIC_COMPARE,
        EVIDENCE_KIND_STATIC_CONSTANT,
        EVIDENCE_KIND_STATIC_TRANSFORM_HINT,
        EVIDENCE_KIND_STATIC_CRYPTO_SIGNATURE,
        EVIDENCE_KIND_STATIC_GUI_INPUT,
        EVIDENCE_KIND_STATIC_ANTI_DEBUG,
    }
    assert len(kinds) == 7
    # Ensure they don't collide with existing kinds.
    existing = {
        EVIDENCE_KIND_CANDIDATE,
        EVIDENCE_KIND_BASE64_MATERIAL,
        EVIDENCE_KIND_RC4_MATERIAL,
        EVIDENCE_KIND_UTF16LE_MATERIAL,
    }
    assert kinds.isdisjoint(existing)
