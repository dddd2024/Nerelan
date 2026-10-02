"""Provider-free native CLI wire-contract and public-evidence regressions."""

import json
import time

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


def test_critical_error_then_failed_turn_preserves_diagnostics_until_real_terminal():
    seen = []
    parser = CodexJsonl(seen.append)
    parser.feed(wire(*START,
        {"type": "error", "message": "Request failed"},
        {"type": "error", "message": "Additional diagnostic"},
        {"type": "turn.failed", "error": {"message": "Turn request failed"}}))
    result = parser.finish()
    assert result.failed and not result.completed
    assert result.failure_classification == "codex_turn_failed"
    assert [item["text"] for item in seen] == ["Request failed", "Additional diagnostic", "Turn request failed"]
    with pytest.raises(CodexProtocolError, match="codex_event_after_terminal"):
        parser.feed(wire(MESSAGE))


@pytest.mark.parametrize("finish_events", [[], [MESSAGE, DONE]])
def test_error_only_eof_and_completion_after_critical_error_never_become_success(finish_events):
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "error", "message": "Critical diagnostic"}, *finish_events))
    result = parser.finish()
    assert result.failed and not result.completed
    assert result.failure_classification == "codex_turn_failed"


def test_pre_thread_warning_is_visible_without_relaxing_agent_item_identity():
    seen = []
    warning = {"type": "item.completed", "item": {"type": "error", "message": "Configuration warning"}}
    parser = CodexJsonl(seen.append)
    parser.feed(wire(warning, *START, MESSAGE, DONE))
    assert parser.finish().completed
    assert seen[0]["text"] == "Configuration warning"
    with pytest.raises(CodexProtocolError, match="codex_turn_identity_invalid"):
        CodexJsonl().feed(wire(MESSAGE))


def test_error_diagnostics_redact_secrets_and_credential_urls_before_publication():
    seen = []
    parser = CodexJsonl(seen.append)
    parser.feed(wire(*START,
        {"type": "error", "message": "Authorization: Bearer " + "s" * 9000, "token": "opaque-secret"},
        {"type": "turn.failed", "error": {"message": "https://user:private-password@host.invalid/request", "token": "opaque-secret"}}))
    result = parser.finish()
    public = json.dumps(seen) + repr(result)
    assert "private-password" not in public and "opaque-secret" not in public
    assert "s" * 64 not in public and "REDACTED" in public
    assert result.failed


@pytest.mark.parametrize("diagnostic,private", [
    ("wss://fixture-user:fixture-password@host.invalid/request", "fixture-password"),
    ("Authorization=Basic Zml4dHVyZTo=", "Zml4dHVyZTo="),
    ("token=fixture", "fixture"),
    ('{"token": "short value"}', "short value"),
    ("access_token='tiny'", "tiny"),
    (json.dumps({"token": 'first" private remainder'}), "private remainder"),
    ("password='first\\' private remainder'", "private remainder"),
])
@pytest.mark.parametrize("surface", ["error", "turn.failed", "warning"])
def test_all_public_diagnostic_surfaces_redact_credentials_regardless_of_length(diagnostic, private, surface):
    seen = []
    parser = CodexJsonl(seen.append)
    if surface == "warning":
        events = [{"type": "item.completed", "item": {"type": "error", "message": diagnostic}},
                  *START, MESSAGE, DONE]
    elif surface == "turn.failed":
        events = [*START, {"type": "turn.failed", "error": {"message": diagnostic}}]
    else:
        events = [*START, {"type": "error", "message": diagnostic},
                  {"type": "turn.failed", "error": {"message": "failed"}}]
    parser.feed(wire(*events))
    result = parser.finish()
    public = json.dumps(seen) + repr(result)
    assert private not in public and "REDACTED" in public
    assert result.completed is (surface == "warning")


def test_large_scheme_free_diagnostic_does_not_block_executor_deadline_checks():
    # A legal frame's long letter run has no URL. Redaction must not repeatedly
    # scan it as a new candidate scheme at each character inside the same run.
    parser = CodexJsonl()
    started = time.monotonic()
    parser.feed(wire(*START, {"type": "error", "message": "a" * 240_000},
                     {"type": "turn.failed", "error": {"message": "failed"}}))
    assert time.monotonic() - started < 2
    assert parser.finish().failed
