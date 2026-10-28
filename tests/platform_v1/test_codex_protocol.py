"""Provider-free native CLI wire-contract and public-evidence regressions."""

import json

import pytest

from reverse_agent.platform_v1.codex_protocol import (
    CodexJsonl, CodexProtocolError, parse_reset_time,
)


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


def test_transport_model_provenance_is_never_inferred_from_message_text():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "item.completed", "item": {
        "type": "agent_message", "text": "model=gpt-fixture"}}, DONE))
    assert parser.finish().models == []
    observed = CodexJsonl()
    observed.feed(wire(START[0], {"type": "turn.started", "model": "provider/gpt-fixture"}, MESSAGE, DONE))
    assert observed.finish().models == ["provider/gpt-fixture"]


@pytest.mark.parametrize("model", [None, [], "", "bad model", "x\nsecret"])
def test_invalid_transport_model_identity_fails_closed(model):
    parser = CodexJsonl()
    with pytest.raises(CodexProtocolError, match="codex_model_identity_invalid"):
        parser.feed(wire(START[0], {"type": "turn.started", "model": model}))


# --- #1260: usage-limit classification from error/turn.failed messages ---


def test_turn_failed_usage_limit_is_classified_and_redacted():
    seen = []
    parser = CodexJsonl(seen.append)
    parser.feed(wire(*START, {"type": "turn.failed", "error": {
        "message": "You've hit your usage limit. Try again at 2026-10-20T00:00:00Z",
        "api_key": "opaque-key"}}))
    result = parser.finish()
    assert result.failed and not result.completed
    assert result.failure_classification == "codex_usage_limit"
    assert "usage limit" in result.failure_detail
    assert "opaque-key" not in result.failure_detail
    assert seen and seen[-1]["type"] == "turn.error"
    assert seen[-1]["failure_classification"] == "codex_usage_limit"


def test_error_event_then_usage_limit_turn_failed_classifies():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "error", "error": {"message": "rate limit reached"}},
                     {"type": "turn.failed", "error": {"message": "rate limit reached"}}))
    result = parser.finish()
    assert result.failure_classification == "codex_usage_limit"


def test_generic_error_stays_turn_failed_but_keeps_detail():
    seen = []
    parser = CodexJsonl(seen.append)
    parser.feed(wire(*START, {"type": "turn.failed", "error": {"message": "the model blew up"}}))
    result = parser.finish()
    assert result.failure_classification == "codex_turn_failed"
    assert result.failure_detail == "the model blew up"
    assert seen and seen[-1]["type"] == "turn.error"
    assert seen[-1]["failure_classification"] == "codex_turn_failed"


def test_error_event_only_at_eof_classifies_usage_limit():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "error", "error": {"message": "429 usage limit"}}))
    result = parser.finish()
    assert result.failed
    assert result.failure_classification == "codex_usage_limit"


def test_secret_in_usage_limit_message_is_redacted():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "turn.failed", "error": {
        "message": "usage limit hit; token: sk-verysecretvalue Authorization: Bearer abc123"}}))
    result = parser.finish()
    assert result.failure_classification == "codex_usage_limit"
    assert "sk-verysecretvalue" not in result.failure_detail
    assert "abc123" not in result.failure_detail
    assert "REDACTED" in result.failure_detail


def test_failure_detail_is_bounded_to_500_chars():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "turn.failed", "error": {"message": "usage limit " + "x" * 2000}}))
    result = parser.finish()
    assert len(result.failure_detail) <= 500


def test_parse_reset_time_from_message():
    from datetime import datetime, timezone
    assert parse_reset_time("try again at 2026-10-20T00:00:00Z") == "2026-10-20T00:00:00Z"
    assert parse_reset_time("no reset here") is None
    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    assert parse_reset_time("try again at 14:30", now) == "2026-10-19T14:30:00Z"


@pytest.mark.parametrize('message, expected', [
    ('context limit reached', False), ('output token limit reached', False),
    ('max limit reached for file size', False), ('failed at foo.py:429', False),
    ("you've hit your upper bound", False), ('/logs/429/error', False),
    ("You've hit your limit ? resets 5pm", True),
    ('HTTP 429', True), ('status 429', True), ('429 Too Many Requests', True),
    ("You've hit your usage limit. Upgrade to Pro", True),
    ("You've hit your rate limit. Please try again later", True),
    ('account quota exceeded', True), ('plan quota exceeded', True),
    ('You exceeded your current quota, please check your plan', True),
])
def test_precise_limit_wording(message, expected):
    from reverse_agent.platform_v1.codex_protocol import usage_limit_hit
    assert usage_limit_hit(message) is expected


@pytest.mark.parametrize('progress, terminal, expected', [
    (False, '', 'codex_usage_limit'),
    (True, '', 'codex_turn_failed'),
    (False, 'unrelated terminal failure', 'codex_turn_failed'),
])
def test_terminal_classification_uses_only_fresh_eligible_text(progress, terminal, expected):
    seen = []
    parser = CodexJsonl(seen.append)
    diagnostic = "usage limit; reset 2026-10-20T00:00:00Z owner@example.invalid"
    events = [*START, {'type': 'error', 'error': {'message': diagnostic}}]
    if progress:
        events.append(MESSAGE)
    events.append({'type': 'turn.failed', 'error': {'message': terminal}})
    parser.feed(wire(*events))
    turn = parser.finish()
    assert turn.failure_classification == expected
    assert 'Earlier diagnostic:' in turn.failure_detail
    assert 'owner@example.invalid' not in repr(turn) + repr(seen)
    assert turn.failure_reset_at == ('2026-10-20T00:00:00Z' if expected == 'codex_usage_limit' else '')


@pytest.mark.parametrize('latest', ['', 'connection failed', 'rate limit reached'])
def test_latest_diagnostic_including_empty_replaces_previous(latest):
    parser = CodexJsonl()
    parser.feed(wire(*START, {'type': 'error', 'error': {'message': 'usage limit'}},
                     {'type': 'error', 'error': {'message': latest}}, {'type': 'turn.failed'}))
    assert parser.finish().failure_classification == (
        'codex_usage_limit' if latest == 'rate limit reached' else 'codex_turn_failed')


def test_eof_after_progress_does_not_reuse_limit_or_reset():
    parser = CodexJsonl()
    parser.feed(wire(*START, {'type': 'error', 'error': {
        'message': 'usage limit 2026-10-20T00:00:00Z'}}, MESSAGE))
    turn = parser.finish()
    assert turn.failure_classification == 'codex_turn_failed'
    assert not turn.failure_reset_at
    assert 'Earlier diagnostic:' in turn.failure_detail


def test_recovered_completion_clears_diagnostic_failure():
    parser = CodexJsonl()
    parser.feed(wire(*START, {'type': 'error', 'error': {'message': 'usage limit'}}, MESSAGE, DONE))
    turn = parser.finish()
    assert turn.completed and not turn.failed
    assert not turn.failure_detail and not turn.failure_reset_at


@pytest.mark.parametrize('date, expected', [
    ('2026-01-31', '2026-02-01'), ('2026-12-31', '2027-01-01'),
    ('2024-02-28', '2024-02-29'), ('2024-02-29', '2024-03-01'),
])
def test_clock_reset_calendar_rollover(date, expected):
    from datetime import datetime
    now = datetime.fromisoformat(date + 'T23:00:00+00:00')
    assert parse_reset_time('try again at 01:30', now) == expected + 'T01:30:00Z'


def test_reset_timezone_and_ambiguity_contract():
    from datetime import datetime
    aware = datetime.fromisoformat('2026-10-19T12:00:00-04:00')
    assert parse_reset_time('try again at 14:30', aware) == '2026-10-19T18:30:00Z'
    assert parse_reset_time('2026-10-19T14:30', aware) == '2026-10-19T18:30:00Z'
    assert parse_reset_time('2026-10-19T14:30+02:00') == '2026-10-19T12:30:00Z'
    for now in (None, datetime(2026, 10, 19, 12)):
        assert parse_reset_time('try again at 14:30', now) is None
        assert parse_reset_time('2026-10-19T14:30', now) is None
    for text in ('try again at 25:99', '2026-02-30T12:00Z', 'garbage'):
        assert parse_reset_time(text, aware) is None


def test_clock_reset_am_pm_forms():
    from datetime import datetime
    aware = datetime.fromisoformat('2026-10-19T12:00:00+00:00')
    assert parse_reset_time('try again at 3:05 PM', aware) == '2026-10-19T15:05:00Z'
    assert parse_reset_time('try again at 12:30 a.m.', aware) == '2026-10-20T00:30:00Z'
    assert parse_reset_time('try again at 12:15pm', aware) == '2026-10-19T12:15:00Z'
    assert parse_reset_time('try again at 13:05 PM', aware) is None


def test_clock_reset_in_failure_uses_host_local_time(monkeypatch):
    from datetime import datetime
    from reverse_agent.platform_v1 import codex_protocol
    now = datetime.fromisoformat('2026-10-19T12:00:00+08:00')
    monkeypatch.setattr(codex_protocol, 'local_now', lambda: now)
    parser = CodexJsonl()
    parser.feed(wire(*START, {'type': 'turn.failed',
                              'error': {'message': "You've hit your usage limit. Try again at 3:05 PM."}}))
    turn = parser.finish()
    assert turn.failure_classification == 'codex_usage_limit'
    assert turn.failure_reset_at == '2026-10-19T07:05:00Z'
