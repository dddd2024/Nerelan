"""Tests for local_reverse_direct_strcmp_handoff."""

from __future__ import annotations

import json
from pathlib import Path

from reverse_agent.local_reverse_direct_strcmp_handoff import (
    BLOCKED_AMBIGUOUS,
    BLOCKED_INTERNAL_CRT,
    BLOCKED_NO_CURRENT_TRIAGE,
    BLOCKED_NO_LITERAL,
    build_handoff,
)


def _context(
    *,
    callee: str = "_strcmp",
    caller_func: str = "_main_0",
    nearby: str = 'push    offset Str2; "ippio" || lea     ecx, [ebp+Str1] || push    ecx; Str1',
    call_ea: str = "0x40111C",
) -> dict[str, str]:
    return {
        "call_ea": call_ea,
        "caller_func": caller_func,
        "callee": callee,
        "call_disasm": f"call    {callee}",
        "nearby": nearby,
        "ref_strings": "",
    }


def _triage(compare_contexts: list[dict[str, str]] | None = None, **overrides: object) -> dict[str, object]:
    triage: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "relative_path": "逆向课程2025春03/CPP2.exe",
        "analysis_mode": "local_reverse_single_sample_static_triage",
        "source_artifact_freshness": "current",
        "mainline": "tool_integration",
        "status": "STATIC_TRIAGE_COMPLETE",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "solved": False,
        "tool_status": "success",
        "blocked_reason": "",
        "source_tool": "IDA",
        "sha256": "2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1",
        "size_bytes": 196689,
        "queue_rank": 1,
        "candidate": None,
        "known_candidate": "",
        "triage": {
            "compare_contexts": compare_contexts if compare_contexts is not None else [_context()],
            "solver_profile_hypotheses": ["string_compare_password_checker", "strcmp_direct_compare"],
        },
    }
    triage.update(overrides)
    return triage


def _run(tmp_path: Path, triage: dict[str, object]) -> dict[str, object]:
    triage_path = tmp_path / "triage.json"
    out_path = tmp_path / "handoff.json"
    triage_path.write_text(json.dumps(triage, ensure_ascii=False), encoding="utf-8")
    result = build_handoff(triage_path=triage_path, out_path=out_path)
    assert out_path.exists()
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert loaded == result
    return result


def test_extracts_direct_strcmp_literal_without_promoting_to_known_candidate(tmp_path: Path) -> None:
    result = _run(tmp_path, _triage())

    assert result["status"] == "READY_FOR_RUNTIME_VALIDATION"
    assert result["sample_id"] == "cpp2_2f64e68d"
    assert result["analysis_mode"] == "direct_strcmp_static_handoff"
    assert result["mainline"] == "reverse_solving"
    assert result["source_artifact_freshness"] == "current"
    assert result["executed_sample"] is False
    assert result["static_only"] is True
    assert result["runtime_validated"] is False
    assert result["compare_call_ea"] == "0x40111C"
    assert result["compare_caller_func"] == "_main_0"
    assert result["compare_callee"] == "_strcmp"
    assert result["static_candidate_text"] == "ippio"
    assert result["static_candidate_hex"] == "697070696f"
    assert result["static_candidate_printable"] is True
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["validation_status"] == "not_validated"
    assert result["solved"] is False


def test_rejects_crt_strncmp_global_heap_context(tmp_path: Path) -> None:
    crt_context = _context(
        callee="_strncmp",
        caller_func="sub_406220",
        nearby='push    16h; MaxCount || lea     ecx, [ebp+Buffer] || push    ecx; Str2 || push    offset Str1; "__GLOBAL_HEAP_SELECTED"',
        call_ea="0x4062DE",
    )
    result = _run(tmp_path, _triage([crt_context]))

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == BLOCKED_INTERNAL_CRT
    assert result["static_candidate_text"] == ""
    assert result["known_candidate"] == ""
    assert result["solved"] is False


def test_blocks_direct_strcmp_without_literal(tmp_path: Path) -> None:
    result = _run(tmp_path, _triage([_context(nearby="lea     ecx, [ebp+Str1] || push    ecx; Str1")]))

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == BLOCKED_NO_LITERAL


def test_blocks_ambiguous_same_priority_contexts(tmp_path: Path) -> None:
    contexts = [
        _context(nearby='push offset Str2; "alpha" || lea ecx, [ebp+Str1] || push ecx; Str1', call_ea="0x401000"),
        _context(nearby='push offset Str2; "bravo" || lea ecx, [ebp+Str1] || push ecx; Str1', call_ea="0x401010"),
    ]
    result = _run(tmp_path, _triage(contexts))

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == BLOCKED_AMBIGUOUS


def test_prefers_main_context_over_other_direct_strcmp(tmp_path: Path) -> None:
    contexts = [
        _context(caller_func="sub_401200", nearby='push offset Str2; "decoy" || lea ecx, [ebp+Str1] || push ecx; Str1'),
        _context(caller_func="_main_0", nearby='push offset Str2; "ippio" || lea ecx, [ebp+Str1] || push ecx; Str1'),
    ]
    result = _run(tmp_path, _triage(contexts))

    assert result["status"] == "READY_FOR_RUNTIME_VALIDATION"
    assert result["compare_caller_func"] == "_main_0"
    assert result["static_candidate_text"] == "ippio"


def test_blocks_non_current_or_blocked_source_triage(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        _triage(
            source_artifact_freshness="stale",
            status="BLOCKED",
            tool_status="blocked",
            source_tool="",
            solved=False,
        ),
    )

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == BLOCKED_NO_CURRENT_TRIAGE
    assert result["candidate"] is None
    assert result["known_candidate"] == ""
    assert result["solved"] is False
