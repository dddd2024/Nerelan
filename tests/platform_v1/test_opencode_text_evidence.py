"""Provider-free regression coverage for OpenCode assistant answer evidence."""

import json

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    MAX_EVIDENCE_STRING_LEN,
    OpenCodeExecutor,
    _bounded_value,
    _build_executor_evidence,
    _persist_executor_evidence,
)
from reverse_agent.platform_v1.run_store import TaskStore


def text_event(text):
    return {"type": "text", "part": {"type": "text", "text": text}}


@pytest.mark.parametrize("exit_code,expected_status", [(0, "pass"), (1, "info")])
def test_cli_answer_survives_existing_task_evidence_roundtrip(exit_code, expected_status):
    event = text_event("NERELAN_FIRST_USE_OK result=391")
    event["part"].update(id="part-fixture", messageID="message-fixture")
    events, malformed = OpenCodeExecutor._parse_json_lines(None, json.dumps(event))
    assert not malformed
    evidence = _build_executor_evidence(events, exit_code=exit_code, model_id="test/model")
    store = TaskStore(":memory:")
    task = store.create_task(title="answer evidence", executor_kind="opencode")
    unrelated = store.create_task(title="other task", executor_kind="opencode")
    _persist_executor_evidence(store, task.id, evidence)
    saved = store.get_task(task.id)
    assert saved.status == task.status
    assert len(saved.evidence_refs) == 1
    item = saved.evidence_refs[0]
    assert item["value"] == "NERELAN_FIRST_USE_OK result=391"
    assert item["category"] == "ExecutorAction" and item["label"] == "text"
    assert item["status"] == expected_status
    assert "fixture" not in item["value"]
    assert not store.get_task(unrelated.id).evidence_refs


@pytest.mark.parametrize("part", [None, [], "secret", 1, {},
    {"type": "reasoning", "text": "hidden reasoning"},
    {"type": "text", "text": {"secret": "never serialize"}},
    {"type": "text", "text": ["never serialize"]},
    {"type": "text", "text": None},
    {"type": "text", "text": 7},
])
def test_malformed_or_non_text_parts_are_not_serialized(part):
    assert _bounded_value({"type": "text", "part": part}, 250) == ""


@pytest.mark.parametrize("event_type", [None, "reasoning", "tool_use", "step_finish"])
def test_text_part_requires_text_event(event_type):
    event = text_event("not an assistant answer event")
    event["type"] = event_type
    assert _bounded_value(event, 250) == ""


@pytest.mark.parametrize("key", ["path", "file", "command", "result", "message"])
def test_existing_top_level_field_precedes_nested_answer(key):
    event = text_event("nested answer")
    event[key] = "existing value"
    assert _bounded_value(event, 250) == "existing value"


def test_known_secret_crossing_output_boundary_is_redacted_before_truncation():
    prefix = "x" * (MAX_EVIDENCE_STRING_LEN - 8)
    secret = "ghp_" + "A" * 40
    value = _bounded_value(text_event(prefix + secret), MAX_EVIDENCE_STRING_LEN)
    assert value == (prefix + "[REDACTED]")[:MAX_EVIDENCE_STRING_LEN]
    assert "ghp_" not in value
    assert len(value) == MAX_EVIDENCE_STRING_LEN


def test_nul_removal_precedes_redaction_and_unicode_answer_remains_bounded():
    event = text_event("token=abc\x00def12345678901234567890\n" + "回答" * 200)
    value = _bounded_value(event, MAX_EVIDENCE_STRING_LEN)
    assert value.startswith("token: [REDACTED]\n")
    assert "abcdef" not in value and "\x00" not in value
    assert len(value) == MAX_EVIDENCE_STRING_LEN


def test_empty_text_does_not_serialize_other_part_fields():
    event = text_event("")
    event["part"]["metadata"] = {"credential": "private fixture"}
    assert _bounded_value(event, 250) == ""
