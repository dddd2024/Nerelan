"""Provider-free native CLI wire-contract and public-evidence regressions."""

import json

import pytest

from reverse_agent.platform_v1.codex_protocol import CodexJsonl, CodexProtocolError


def wire(*events):
    return b"\n".join(json.dumps(x, ensure_ascii=False).encode() for x in events) + b"\n"


START = [{"type": "thread.started", "thread_id": "thread-1"}, {"type": "turn.started"}]
MESSAGE = {"type": "item.completed", "item": {"type": "agent_message", "text": "已完成"}}
DONE = {"type": "turn.completed"}


def test_arbitrary_utf8_chunk_boundaries_and_final_frame_without_newline():
    stream = wire(*START, MESSAGE, DONE).rstrip(b"\n")
    seen = []
    parser = CodexJsonl(seen.append)
    for byte in stream:
        parser.feed(bytes([byte]))
    result = parser.finish()
    assert result.completed and result.final_text == "已完成"
    assert result.thread_id == "thread-1"
    assert result.usage is None
    assert seen == result.items


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": -1}, {
    "input_tokens": True, "cached_input_tokens": 0, "output_tokens": 0,
}])
def test_unknown_or_invalid_usage_does_not_become_zero(usage):
    parser = CodexJsonl()
    parser.feed(wire(*START, MESSAGE, {"type": "turn.completed", "usage": usage}))
    assert parser.finish().usage is None


def test_actual_token_usage_is_not_a_cost_estimate():
    usage = {"input_tokens": 45, "cached_input_tokens": 20, "output_tokens": 4}
    parser = CodexJsonl()
    parser.feed(wire(*START, MESSAGE, {"type": "turn.completed", "usage": usage}))
    assert parser.finish().usage == usage
    assert "cost" not in parser.turn.__dict__


@pytest.mark.parametrize("status,exit_code,expected", [
    ("failed", -1, True),   # Windows sandbox helper never launched the child.
    ("failed", 1, False),   # Ordinary command failure may be exploratory.
    ("completed", 0, False),
    ("failed", None, False),  # Do not invent an unavailable exit code.
])
def test_failed_command_helper_is_preserved_after_completed_turn(status, exit_code, expected):
    item = {"type": "command_execution", "status": status, "command": "git status"}
    if exit_code is not None:
        item["exit_code"] = exit_code
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "item.completed", "item": item}, MESSAGE, DONE))
    result = parser.finish()
    assert result.completed
    assert result.tool_launch_failed is expected


def test_transient_command_updates_do_not_fabricate_launch_failure():
    parser = CodexJsonl()
    item = {"type": "command_execution", "status": "failed", "exit_code": -1}
    parser.feed(wire(*START, {"type": "item.updated", "item": item}, MESSAGE, DONE))
    assert parser.finish().tool_launch_failed is False


@pytest.mark.parametrize("fields", [{}, {"exit_code": None}, {"status": "completed"}, {"status": "failed", "exit_code": -1}])
def test_helper_setup_diagnostic_without_launch_exit_code_is_sanitized(fields):
    seen = []
    parser = CodexJsonl(seen.append)
    item = {"type": "command_execution", "command": "C:\\private-workspace\\tool.exe",
            "aggregated_output": "helper_unknown_error: setup refresh had errors "
                                 "C:\\private-workspace Authorization: Bearer fixture-private-token",
            **fields}
    stream = wire(*START, {"type": "item.completed", "item": item}, MESSAGE, DONE)
    for byte in stream:
        parser.feed(bytes([byte]))
    turn = parser.finish()
    assert turn.completed and turn.tool_launch_failed
    assert seen[0]["failure_classification"] == "codex_tool_launch_failed"
    assert seen[0]["diagnostic"] == "helper_unknown_error: setup refresh had errors"
    assert "private-workspace" not in repr(turn) + repr(seen)
    assert "fixture-private-token" not in repr(turn) + repr(seen)


@pytest.mark.parametrize("exit_code", [0, 1, 2])
def test_successfully_launched_command_may_print_helper_error_words(exit_code):
    # Grep/search output can quote documentation about the helper itself.
    seen = []
    parser = CodexJsonl(seen.append)
    status = "completed" if exit_code == 0 else "failed"
    item = {"type": "command_execution", "command": "rg -n helper_unknown_error .",
            "status": status, "exit_code": exit_code,
            "aggregated_output": "docs/notes: helper_unknown_error: setup refresh had errors"}
    parser.feed(wire(*START, {"type": "item.completed", "item": item}, MESSAGE, DONE))
    turn = parser.finish()
    assert turn.completed and not turn.tool_launch_failed
    assert seen[0]["status"] == status
    assert "failure_classification" not in seen[0]


@pytest.mark.parametrize("kind,item_type,output", [
    ("item.updated", "command_execution", "helper_unknown_error: setup refresh had errors"),
    ("item.completed", "agent_message", "helper_unknown_error: setup refresh had errors"),
    ("item.completed", "command_execution", "helper_unknown_error"),
    ("item.completed", "command_execution", "setup refresh had errors"),
])
def test_setup_failure_requires_specific_completed_command_diagnostic(kind, item_type, output):
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": kind, "item": {
        "type": item_type, "text": output, "aggregated_output": output,
    }}, MESSAGE, DONE))
    assert not parser.finish().tool_launch_failed


@pytest.mark.parametrize("stream,classification", [
    (b"not-json\n", "codex_invalid_jsonl"),
    (b"\xff\n", "codex_invalid_jsonl"),
    (b"[]\n", "codex_invalid_event"),
    (wire({"type": "turn.started"}), "codex_turn_identity_invalid"),
    (wire(*START, {"type": "turn.started"}), "codex_turn_identity_invalid"),
    (wire(*START, START[0]), "codex_duplicate_thread"),
    (wire(*START, {"type": "item.completed", "item": []}), "codex_invalid_item"),
    (wire(*START, MESSAGE, DONE, MESSAGE), "codex_event_after_terminal"),
])
def test_invalid_or_cross_turn_stream_fails_closed(stream, classification):
    with pytest.raises(CodexProtocolError, match=f"^{classification}$"):
        CodexJsonl().feed(stream)


@pytest.mark.parametrize("events,classification", [
    (START, "codex_turn_incomplete"),
    ([*START, DONE], "codex_final_message_missing"),
])
def test_exit_without_complete_readable_final_is_not_success(events, classification):
    parser = CodexJsonl()
    parser.feed(wire(*events))
    with pytest.raises(CodexProtocolError, match=f"^{classification}$"):
        parser.finish()


def test_failed_turn_never_echoes_secret_bearing_error_object():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "turn.failed", "error": {"token": "private-value"}}))
    result = parser.finish()
    assert result.failed and not result.completed
    assert result.failure_classification == "codex_turn_failed"
    assert "private-value" not in repr(result)


def test_public_allowlist_redacts_before_truncation_and_discards_opaque_payloads():
    seen = []
    parser = CodexJsonl(seen.append)
    message = {"type": "item.completed", "item": {
        "type": "agent_message", "text": "Authorization: Bearer " + "x" * 9000,
        "api_key": "opaque-key",
    }}
    opaque = {"type": "item.updated", "item": {
        "type": "mcp_tool_call", "arguments": {"password": "opaque-password"},
        "result": "private tool result",
    }}
    parser.feed(wire(*START, opaque, message, DONE))
    result = parser.finish()
    public = json.dumps(seen) + repr(result)
    assert "opaque-key" not in public and "opaque-password" not in public
    assert "private tool result" not in public and "x" * 64 not in public
    assert "REDACTED" in result.final_text


@pytest.mark.parametrize("newline", [b"", b"\n"])
def test_line_size_bound_applies_with_and_without_delimiter(newline):
    parser = CodexJsonl(max_frame_bytes=100, max_stream_bytes=1000)
    with pytest.raises(CodexProtocolError, match="codex_frame_limit_exceeded"):
        parser.feed(b"x" * 101 + newline)


def test_total_stream_and_event_counts_are_independently_bounded():
    parser = CodexJsonl(max_frame_bytes=10, max_stream_bytes=20)
    with pytest.raises(CodexProtocolError, match="codex_stream_limit_exceeded"):
        parser.feed(b"\n" * 21)
    parser = CodexJsonl(max_events=1)
    with pytest.raises(CodexProtocolError, match="codex_event_limit_exceeded"):
        parser.feed(wire(*START))
