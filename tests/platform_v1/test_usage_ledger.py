"""One token ledger across executors, Claude quota capture and subscription windows (provider-free)."""
from __future__ import annotations

import json
import os
import time

from reverse_agent.model_access.subscription_quota import claude_rate_limits, codex_rate_limits, read_codex_quota
from reverse_agent.platform_v1.claude_protocol import ClaudeStreamJson
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.usage_ledger import binding_token_totals, latest_rate_limits, task_token_records


def _task(store, binding, kind, status="READY_FOR_REVIEW", *, completed=None, observation=None):
    task = store.create_task(title="t", executor_kind=kind, binding_ref=binding, repository="o/r")
    store._conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task.id))
    if completed is not None:
        store._conn.execute("INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
                            "VALUES (?, ?, 'EXECUTOR_COMPLETED', ?, '', '', '', ?)",
                            (f"ev-{task.id}", task.id, completed.pop("_at", "2026-10-14T05:00:00Z"), json.dumps(completed)))
    if observation is not None:
        store._conn.execute(
            "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, role, model_id, "
            "provider_id, source_kind, source_id, status, input_units, output_units, reasoning_units, cache_read_units, "
            "cache_write_units, payload_digest, created_at) VALUES (?, ?, '', 0, 'e', 'executor', 'm', 'p', 's', ?, "
            "'OBSERVED', ?, ?, ?, ?, ?, '', '')", (f"u-{task.id}", task.id, f"src-{task.id}", *observation))
    store._conn.commit()
    return task


def test_each_executor_lands_in_the_same_counters():
    store = TaskStore(":memory:")
    # OpenCode: input, output, reasoning, cache read, cache write from its observation row.
    _task(store, "glm@opencode", "opencode", observation=(1000, 300, 50, 4000, 200))
    # Codex: input_tokens includes the cached part.
    _task(store, "gpt@codex", "codex", completed={"token_usage": {
        "input_tokens": 10_000, "cached_input_tokens": 8_000, "output_tokens": 500}})
    # Claude Code: cache reads and writes are separate from input; it names the model behind "sonnet".
    _task(store, "sonnet@claude", "claude_code", completed={
        "token_usage": {"input_tokens": 40, "cached_input_tokens": 7000, "cache_write_input_tokens": 900,
                        "output_tokens": 200},
        "models": ["claude-sonnet-5-5"], "cli_reported_cost_usd": 0.0123})
    # An older Claude record without cache writes, and a failed task that still spent tokens.
    _task(store, "sonnet@claude", "claude_code", "FAILED", completed={
        "token_usage": {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5}})
    _task(store, "glm@opencode", "opencode", "QUEUED", observation=(9, 9, 0, 0, 0))  # unfinished: ignored
    records = {r["binding_ref"] + ("" if r["ok"] else "!"): r for r in task_token_records(store)}
    assert records["glm@opencode"]["tokens"] == {"input": 1000, "cache_read": 4000, "cache_write": 200,
                                                 "output": 300, "reasoning": 50}
    assert records["gpt@codex"]["tokens"] == {"input": 2000, "cache_read": 8000, "cache_write": None,
                                              "output": 500, "reasoning": None}
    assert records["sonnet@claude"]["tokens"]["cache_write"] == 900
    assert records["sonnet@claude!"]["tokens"]["cache_write"] is None
    totals = binding_token_totals(task_token_records(store))
    claude = totals["sonnet@claude"]
    assert (claude["input"], claude["output"], claude["tasks"], claude["tasks_with_tokens"]) == (50, 205, 2, 2)
    assert claude["cache_write_unknown_tasks"] == 1
    assert claude["models"] == {"claude-sonnet-5-5": {"input": 40, "cache_read": 7000, "cache_write": 900,
                                                      "output": 200, "reasoning": 0},
                                "": {"input": 10, "cache_read": 0, "cache_write": 0, "output": 5, "reasoning": 0}}
    assert claude["cli_reported_cost_usd"] == 0.0123
    assert totals["glm@opencode"]["tasks"] == 1


def test_a_task_without_token_figures_counts_but_adds_nothing():
    store = TaskStore(":memory:")
    _task(store, "x", "codex", completed={"usage_status": "unknown", "token_usage": None})
    entry = binding_token_totals(task_token_records(store))["x"]
    assert (entry["tasks"], entry["tasks_with_tokens"], entry["input"]) == (1, 0, 0)


def test_claude_stream_keeps_rate_limits_cache_writes_models_and_cli_cost():
    parser = ClaudeStreamJson()
    parser.feed(b'{"type":"rate_limit_event","rate_limit_info":{"status":"allowed","resetsAt":1792000000,'
                b'"rateLimitType":"five_hour","utilization":0.4,"surpriseField":"dropped"},"session_id":"s"}\n'
                b'{"type":"system","subtype":"init","session_id":"s"}\n'
                b'{"type":"rate_limit_event","rate_limit_info":{"status":"allowed_warning","resetsAt":1792100000,'
                b'"rateLimitType":"five_hour","utilization":0.9}}\n'
                b'{"type":"rate_limit_event","rate_limit_info":{"status":"allowed","rateLimitType":"seven_day"}}\n'
                b'{"type":"rate_limit_event","rate_limit_info":"not an object"}\n'
                b'{"type":"result","subtype":"success","is_error":false,"result":"done","total_cost_usd":0.05,'
                b'"modelUsage":{"claude-sonnet-5-5":{"inputTokens":3}},"usage":{"input_tokens":3,'
                b'"cache_read_input_tokens":100,"cache_creation_input_tokens":20,"output_tokens":7}}\n')
    turn = parser.finish()
    assert turn.rate_limits == [
        {"status": "allowed_warning", "window": "five_hour", "resets_at": 1792100000, "utilization": 0.9},
        {"status": "allowed", "window": "seven_day"}]
    assert turn.usage == {"input_tokens": 3, "cached_input_tokens": 100, "output_tokens": 7,
                          "cache_write_input_tokens": 20}
    assert turn.models == ["claude-sonnet-5-5"] and turn.reported_cost_usd == 0.05


def test_latest_claude_notices_come_from_the_given_bindings_only():
    store = TaskStore(":memory:")
    _task(store, "claude-sonnet", "claude_code", completed={
        "_at": "2026-10-14T04:00:00Z", "rate_limits": [{"status": "allowed", "window": "five_hour"}]})
    _task(store, "relay-glm", "claude_code", completed={
        "_at": "2026-10-14T06:00:00Z", "rate_limits": [{"status": "rejected", "window": "five_hour"}]})
    assert latest_rate_limits(store, ["claude-sonnet"]) == (
        [{"status": "allowed", "window": "five_hour"}], "2026-10-14T04:00:00Z")
    assert latest_rate_limits(store, []) is None


def test_quota_windows_are_normalized_and_a_passed_reset_is_not_zero_use():
    now = 1_792_000_000
    codex = codex_rate_limits({"rate_limits": {
        "primary": {"used_percent": 49.0, "window_minutes": 300, "resets_at": now + 3600},
        "secondary": {"used_percent": 40.0, "window_minutes": 10080, "resets_at": now - 1},
        "plan_type": "plus", "credits": {"has_credits": False, "unlimited": False, "balance": "0"}}},
        "2026-10-14T04:44:18Z", now=now)
    assert [(w["window"], w["used_percent"], w["reset_passed"]) for w in codex["windows"]] == [
        ("five_hour", 49.0, False), ("weekly", 40.0, True)]
    assert codex["plan"] == "plus" and codex["provenance"] == "OFFICIAL_VIA_CLI"
    claude = claude_rate_limits([{"status": "allowed", "window": "seven_day", "utilization": 0.25,
                                  "resets_at": now + 10}], "t", now=now)
    assert claude["windows"][0] | {} == {"window": "weekly", "used_percent": 25.0, "status": "allowed",
                                         "resets_at": claude["windows"][0]["resets_at"], "window_minutes": None,
                                         "reset_passed": False}
    assert claude_rate_limits([], None)["state"] == "UNKNOWN"


def test_codex_session_logs_are_read_for_rate_limits_only(tmp_path):
    day = tmp_path / "sessions" / "2026" / "10" / "14"
    day.mkdir(parents=True)
    log = day / "rollout-1.jsonl"
    lines = [
        {"timestamp": "2026-10-14T04:00:00Z", "type": "event_msg",
         "payload": {"type": "token_count", "rate_limits": {"primary": {"used_percent": 10.0, "window_minutes": 300,
                                                                        "resets_at": 1792000000}}}},
        {"timestamp": "2026-10-14T04:10:00Z", "type": "response_item",
         "payload": {"type": "message", "content": "secret conversation text"}},
        {"timestamp": "2026-10-14T04:20:00Z", "type": "event_msg",
         "payload": {"type": "token_count", "rate_limits": {"primary": {"used_percent": 30.0, "window_minutes": 300,
                                                                        "resets_at": 1792000000}}}},
    ]
    log.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    now = time.time()
    os.utime(log, (now, now))
    quota = read_codex_quota(tmp_path, now=now)
    assert quota["observed_at"] == "2026-10-14T04:20:00Z" and quota["windows"][0]["used_percent"] == 30.0
    assert "secret" not in json.dumps(quota)
    assert read_codex_quota(tmp_path / "missing")["state"] == "UNKNOWN"
