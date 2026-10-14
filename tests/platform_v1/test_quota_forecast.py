"""Tiered subscription quota: official percent > status > estimate > unknown, and the dispatch guard."""
from __future__ import annotations

import json
import os
import time

import pytest

from reverse_agent.model_access.quota_forecast import (
    PercentSample, UsageEvent, capacity_from_hits, capacity_from_percent, capacity_range, estimated_window, guard,
    rolling_blocks,
)
from reverse_agent.model_access.quota_history import read_claude_history, read_codex_history
from reverse_agent.model_access.subscription_quota import claude_quota, codex_quota
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.quota_guard import alternatives, check, typical_task_units

H = 3600


# ---- estimation -------------------------------------------------------------------------

def test_capacity_from_official_percent_steps_with_rounding_range():
    samples = [PercentSample(0, "five_hour", 99, 10.0, 0.5), PercentSample(60, "five_hour", 99, 15.0, 1.0),
               PercentSample(120, "five_hour", 99, 20.0, 1.0)]
    cap = capacity_from_percent(samples)["five_hour"]
    # 2.0 units moved the official figure 10 points: 20 units per window, +/- one point each end.
    assert cap["mid"] == 20.0 and cap["low"] == pytest.approx(200 / 11, abs=1e-3) and cap["high"] == pytest.approx(200 / 9, abs=1e-3)
    assert capacity_from_percent([PercentSample(0, "weekly", 1, 10.0, 5), PercentSample(1, "weekly", 1, 11.0, 5)]) == {}


def test_capacity_range_is_robust_to_one_window_with_unseen_usage():
    cap = capacity_range([8.0, 8.5, 7.9, 8.2, 0.1])
    assert cap["low"] > 7 and cap["min"] == 0.1 and cap["samples"] == 5


def test_rolling_blocks_and_capacity_from_limit_hits():
    events = [UsageEvent(0, 4.0), UsageEvent(H, 6.0), UsageEvent(2 * H, 9.0),       # block 1 hits at 2.5h
              UsageEvent(6 * H, 3.0), UsageEvent(7 * H, 8.0)]                       # block 2 hits at 7.5h
    blocks = rolling_blocks(events)
    assert [(b["start"], b["end"]) for b in blocks] == [(0, 5 * H), (6 * H, 11 * H)]
    # Windows open at the top of the hour of their first request.
    assert [(b["start"], b["end"]) for b in rolling_blocks([UsageEvent(4 * H + 419, 1.0)])] == [(4 * H, 9 * H)]
    cap = capacity_from_hits(events, [2.5 * H, 7.5 * H, 7.5 * H, 99 * H])
    assert (cap["low"], cap["mid"], cap["high"], cap["samples"]) == (11.0, 15.0, 19.0, 2)


def test_estimated_window_reports_a_range_and_remaining_units():
    window = estimated_window("five_hour", used_units=10.0, capacity={"low": 10.0, "mid": 20.0, "high": 40.0},
                              resets_at=None, now=0)
    assert window["basis"] == "estimated" and window["used_percent"] == 50.0
    assert window["used_percent_range"] == [25.0, 100.0] and window["remaining_units_range"] == [0.0, 30.0]


@pytest.mark.parametrize("window,need,decision", [
    ({"status": "rejected"}, None, "switch"),
    ({"availability": "limit_reached"}, None, "switch"),
    ({"remaining_units_range": [1.0, 2.0]}, 3.0, "switch"),
    ({"remaining_units_range": [1.0, 5.0]}, 3.0, "warn"),
    ({"remaining_units_range": [4.0, 5.0]}, 3.0, "ok"),
    ({"basis": "official_percent", "used_percent": 99.0}, None, "switch"),
    ({"basis": "official_percent", "used_percent": 92.0}, None, "warn"),
    ({"status": "allowed_warning"}, None, "warn"),
    ({"status": "rejected", "reset_passed": True}, None, "ok"),
    ({"basis": "estimated", "used_percent": 99.4, "used_percent_range": [72.5, 100.0]}, None, "warn"),
    ({"basis": "estimated", "used_percent": 99.9, "used_percent_range": [98.5, 100.0]}, None, "switch"),
])
def test_guard_decisions(window, need, decision):
    assert guard(window, need)["decision"] == decision


# ---- local CLI logs ---------------------------------------------------------------------

def _write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    now = time.time()
    os.utime(path, (now, now))


def _codex_event(ts, used, resets, *, inp=1_000_000, cached=0, out=0, reached=None):
    return {"timestamp": ts, "type": "event_msg", "payload": {
        "type": "token_count",
        "info": {"last_token_usage": {"input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out}},
        "rate_limits": {"primary": {"used_percent": used, "window_minutes": 300, "resets_at": resets},
                        "plan_type": "plus", "rate_limit_reached_type": reached}}}


def test_codex_history_prices_usage_learns_capacity_and_lists_hits(tmp_path):
    resets = int(time.time()) + 3 * H
    _write(tmp_path / "sessions" / "2026" / "10" / "14" / "rollout-a.jsonl", [
        {"timestamp": "2026-10-14T01:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6.1-sol"}},
        {"timestamp": "2026-10-14T01:00:01Z", "type": "response_item", "payload": {"type": "message",
                                                                                     "content": "do not read"}},
        _codex_event("2026-10-14T01:00:02Z", 10.0, resets),
        _codex_event("2026-10-14T01:30:00Z", 30.0, resets),           # +2 units (1M input at $2) -> +20 points
        _codex_event("2026-10-14T02:00:00Z", 50.0, resets, reached="primary"),
    ])
    history = read_codex_history(tmp_path)
    assert len(history.usage) == 3 and history.usage[0].units == 2.0
    assert [h["window"] for h in history.hits] == ["primary"]
    quota = codex_quota(tmp_path)
    window = quota["windows"][0]
    assert window["basis"] == "official_percent" and window["used_percent"] == 50.0
    assert window["capacity_units"]["mid"] == 10.0  # 4 units moved 40 points
    assert window["remaining_units_range"][0] <= 5.0 <= window["remaining_units_range"][1]
    assert quota["limit_hits"][0]["source"] == "codex_session_log"
    assert "do not read" not in json.dumps(quota)


def _claude_assistant(ts, msg_id, *, inp=0, out=0, model="claude-sonnet-5-5"):
    return {"type": "assistant", "timestamp": ts, "requestId": "r-" + msg_id,
            "message": {"id": msg_id, "model": model, "content": [{"type": "text", "text": "private reply"}],
                        "usage": {"input_tokens": inp, "cache_read_input_tokens": 0,
                                  "cache_creation_input_tokens": 0, "output_tokens": out}}}


def _iso(epoch):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def test_claude_history_dedupes_messages_and_finds_limit_hits(tmp_path):
    t0 = time.time() - 20 * H
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(t0), "m1", out=1_000_000),            # $10 at sonnet-5-5 output price
        _claude_assistant(_iso(t0), "m1", out=1_000_000),            # same message, second content block
        {"type": "user", "timestamp": _iso(t0 + 1), "message": {"content": "private prompt", "usage": "x"}},
        {"type": "assistant", "timestamp": _iso(t0 + 60), "isApiErrorMessage": True, "error": "rate_limit",
         "apiError": "usage_limit_reached", "message": {"model": "<synthetic>", "usage": {}}},
    ])
    history = read_claude_history(tmp_path)
    assert [round(e.units, 2) for e in history.usage] == [10.0]
    assert len(history.hits) == 1


def test_claude_quota_estimates_from_past_hits_when_no_official_number(tmp_path):
    now = time.time()
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(now - 30 * H), "a", out=2_000_000),   # $20 then hit -> capacity 20
        {"type": "assistant", "timestamp": _iso(now - 30 * H + 60), "isApiErrorMessage": True,
         "error": "rate_limit", "apiError": "usage_limit_reached", "message": {}},
        _claude_assistant(_iso(now - H), "b", out=1_000_000),        # $10 in the current window
    ])
    quota = claude_quota(None, tmp_path, now=now)
    window = quota["windows"][0]
    assert quota["provenance"] == "ESTIMATED_FROM_HISTORY"
    assert window["basis"] == "estimated" and window["used_percent"] == 50.0 and window["resets_at_estimated"]
    assert quota["limit_hits"][0]["source"] == "claude_session_log"
    assert "private" not in json.dumps(quota)


def test_claude_quota_limit_reached_in_current_window_and_official_status(tmp_path):
    now = time.time()
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(now - H), "a", out=1_000_000),
        {"type": "assistant", "timestamp": _iso(now - H + 60), "isApiErrorMessage": True,
         "error": "rate_limit", "apiError": "usage_limit_reached", "message": {}},
    ])
    reached = claude_quota(None, tmp_path, now=now)["windows"][0]
    assert reached["availability"] == "limit_reached" and reached["remaining_units_range"] == [0.0, 0.0]
    status_only = claude_quota(([{"status": "allowed_warning", "window": "seven_day"}], "t"), tmp_path / "none", now=now)
    weekly = status_only["windows"][0]
    assert (weekly["basis"], weekly["availability"]) == ("official_status", "near_limit")
    assert status_only["provenance"] == "OFFICIAL_VIA_CLI"


def test_claude_quota_without_any_signal_is_unknown(tmp_path):
    assert claude_quota(None, tmp_path)["state"] == "UNKNOWN"


# ---- dispatch guard ---------------------------------------------------------------------

def test_typical_need_falls_back_from_binding_to_connection_to_all_tasks():
    from reverse_agent.platform_v1.quota_guard import typical_need
    bindings = [{"binding_id": "sonnet", "connection_id": "claude", "model_id": "sonnet"},
                {"binding_id": "opus", "connection_id": "claude", "model_id": "claude-opus-5-5"},
                {"binding_id": "glm", "connection_id": "sense", "model_id": "glm-5.2"}]
    records = [{"binding_ref": "sonnet", "ok": True, "models": [], "tokens": {"input": 10}},  # alias: unpriced
               {"binding_ref": "glm", "ok": True, "models": [], "tokens": {"input": 1_000_000}}]
    assert typical_need(records, bindings[0], bindings) == (1.4, "all_tasks")
    records.append({"binding_ref": "opus", "ok": True, "models": [], "tokens": {"input": 1_000_000}})
    assert typical_need(records, bindings[0], bindings) == (4.0, "connection")
    assert typical_need([], bindings[0], bindings) == (None, "none")
    assert guard({"remaining_units_range": [0.0, 2.0]}, None)["reason"] == "no_task_estimate"


def test_typical_task_units_and_check_skip_api_keys():
    records = [{"binding_ref": "b", "ok": True, "models": [], "tokens": {"input": 1_000_000, "output": 0}},
               {"binding_ref": "b", "ok": True, "models": [], "tokens": {"input": 3_000_000, "output": 0}},
               {"binding_ref": "b", "ok": False, "models": [], "tokens": {"input": 9_000_000, "output": 0}}]
    assert typical_task_units(records, "b", "glm-5.2") == 2.8  # median of $1.4 and $4.2
    quotas = {"claude-code": {"windows": [{"status": "rejected"}]}}
    assert check({"executor_provider_id": "claude-code", "auth_method": "external_cli_session"}, quotas, None)[
        "decision"] == "switch"
    assert check({"executor_provider_id": "openai-compatible", "auth_method": "api_key"}, quotas, None) is None


def test_alternatives_never_step_down_in_strength():
    bindings = [
        {"binding_id": "opus", "connection_id": "claude", "model_id": "opus", "executor_id": "claude_code", "enabled": True},
        {"binding_id": "glm-simple", "connection_id": "sense", "model_id": "glm", "executor_id": "opencode", "enabled": True},
        {"binding_id": "gpt-complex", "connection_id": "chatgpt", "model_id": "gpt", "executor_id": "codex", "enabled": True},
        {"binding_id": "opus-relay", "connection_id": "api", "model_id": "opus", "executor_id": "claude_code", "enabled": True},
    ]
    roster = {"simple": {"binding_id": "glm-simple"}, "coder": {"binding_id": "opus"}, "complex": {"binding_id": "gpt-complex"}}
    usable = {"opencode", "codex", "claude_code"}
    picked = alternatives("coder", bindings[0], bindings=bindings, roster=roster, usable_executors=usable)
    assert [b["binding_id"] for b in picked] == ["opus-relay", "gpt-complex"]  # never the weaker simple agent
    assert [b["binding_id"] for b in alternatives("planner", bindings[0], bindings=bindings, roster=roster,
                                                  usable_executors=usable)] == ["opus-relay"]


def test_host_switches_a_role_off_an_exhausted_account_and_logs_it(monkeypatch):
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session", "enabled": True})
    store.upsert_connection({"connection_id": "chatgpt-account", "name": "ChatGPT", "provider": "codex",
                             "base_url": "https://chatgpt.com", "auth_method": "external_cli_session", "enabled": True})
    for binding_id, connection, executor, model in (("claude-opus", "claude-account", "claude_code", "opus"),
                                                    ("chatgpt-gpt", "chatgpt-account", "codex", "gpt-6.1-sol")):
        store.upsert_binding({"binding_id": binding_id, "name": binding_id, "connection_id": connection,
                              "executor_id": executor, "model_id": model, "enabled": True})
    store.set_native_readiness("claude_code", "managed_login_ready")
    store.set_native_readiness("codex", "managed_login_ready")
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    verdicts = {"claude-account": {"decision": "switch", "reason": "limit_reached", "window": "five_hour"},
                "chatgpt-account": {"decision": "ok", "reason": "fits"}}
    monkeypatch.setattr(host, "_quota_check", lambda binding: verdicts[binding["connection_id"]], raising=False)
    roster = {"coder": {"binding_id": "claude-opus"}, "complex": {"binding_id": "chatgpt-gpt"}}
    assert host._quota_guarded("coder", "claude_code", "claude-opus", roster) == ("codex", "chatgpt-gpt")
    entry = host._quota_guard_entries()[0]
    assert (entry["decision"], entry["reason"], entry["switched_to"]) == ("switch", "limit_reached", "chatgpt-gpt")
    # With no acceptable stand-in the role keeps its agent and the warning is recorded.
    verdicts["chatgpt-account"] = {"decision": "switch", "reason": "limit_reached"}
    assert host._quota_guarded("coder", "claude_code", "claude-opus", roster) == ("claude_code", "claude-opus")
    assert host._quota_guard_entries()[0]["reason"] == "limit_reached:no_alternative"


def _guard_host(monkeypatch, verdicts):
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session", "enabled": True})
    store.upsert_binding({"binding_id": "claude-opus", "name": "opus", "connection_id": "claude-account",
                          "executor_id": "claude_code", "model_id": "opus", "enabled": True})
    store.set_native_readiness("claude_code", "managed_login_ready")
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    monkeypatch.setattr(host, "_quota_check", lambda binding: verdicts.get(binding["connection_id"]), raising=False)
    return host, store


def test_guard_never_switches_to_a_binding_that_cannot_run(monkeypatch):
    # The reviewer's repro: the only stand-in sits on a disabled API-key connection without a key.
    verdicts = {"claude-account": {"decision": "switch", "reason": "limit_reached"}}
    host, store = _guard_host(monkeypatch, verdicts)
    store.upsert_connection({"connection_id": "api", "name": "API", "provider": "anthropic-compatible",
                             "base_url": "https://api.example.test", "auth_method": "api_key", "enabled": False})
    store.upsert_binding({"binding_id": "opus-relay", "name": "opus relay", "connection_id": "api",
                          "executor_id": "claude_code", "model_id": "opus", "enabled": True})
    assert host._quota_guarded("coder", "claude_code", "claude-opus", {}) == ("claude_code", "claude-opus")
    assert host._quota_guard_entries()[0]["reason"] == "limit_reached:no_alternative"
    # Enabled but still without a key: also not a stand-in.
    store.upsert_connection({"connection_id": "api", "name": "API", "provider": "anthropic-compatible",
                             "base_url": "https://api.example.test", "auth_method": "api_key", "enabled": True})
    assert host._quota_guarded("coder", "claude_code", "claude-opus", {}) == ("claude_code", "claude-opus")
    # With a usable key it is taken.
    store.upsert_connection({"connection_id": "api", "name": "API", "provider": "anthropic-compatible",
                             "base_url": "https://api.example.test", "auth_method": "api_key", "enabled": True,
                             "api_key": "test-key-not-real"})
    assert host._quota_guarded("coder", "claude_code", "claude-opus", {}) == ("claude_code", "opus-relay")
    assert "_logged" not in host._quota_guard_entries()[0]


def test_failed_quota_checks_never_move_or_admit_a_role(monkeypatch):
    error = {"decision": "error", "reason": "quota_check_failed"}
    host, store = _guard_host(monkeypatch, {"claude-account": error})
    assert host._quota_guarded("coder", "claude_code", "claude-opus", {}) == ("claude_code", "claude-opus")
    assert host._quota_guard_entries() == []
    # A stand-in whose own check failed is not treated as fitting.
    store.upsert_connection({"connection_id": "chatgpt-account", "name": "ChatGPT", "provider": "codex",
                             "base_url": "https://chatgpt.com", "auth_method": "external_cli_session", "enabled": True})
    store.upsert_binding({"binding_id": "gpt", "name": "gpt", "connection_id": "chatgpt-account",
                          "executor_id": "codex", "model_id": "opus", "enabled": True})
    store.set_native_readiness("codex", "managed_login_ready")
    host2, _ = _guard_host(monkeypatch, {"claude-account": {"decision": "switch", "reason": "limit_reached"},
                                         "chatgpt-account": error})
    host2._store = store
    assert host2._quota_guarded("coder", "claude_code", "claude-opus", {}) == ("claude_code", "claude-opus")


def test_repeated_identical_warnings_are_logged_once(monkeypatch):
    host, _ = _guard_host(monkeypatch, {})
    for _ in range(3):
        host._record_quota_decision({"role": None, "binding_id": "b", "decision": "warn", "reason": "near_limit"})
    assert len(host._quota_guard_entries()) == 1


def test_a_stale_official_availability_does_not_contradict_the_estimate(tmp_path):
    now = time.time()
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(now - H), "a", out=1_000_000),
        {"type": "assistant", "timestamp": _iso(now - H + 60), "isApiErrorMessage": True,
         "error": "rate_limit", "apiError": "usage_limit_reached", "message": {}},
    ])
    old = ([{"status": "allowed", "window": "five_hour", "resets_at": int(now - 10 * H)}], "t")
    window = claude_quota(old, tmp_path, now=now)["windows"][0]
    assert window["availability"] == "limit_reached"


def test_oversized_log_lines_are_skipped_without_losing_later_lines(tmp_path, monkeypatch):
    import reverse_agent.model_access.quota_history as qh
    monkeypatch.setattr(qh, "MAX_LINE_BYTES", 1024)
    now = time.time()
    path = tmp_path / "projects" / "p" / "s.jsonl"
    path.parent.mkdir(parents=True)
    huge = json.dumps({"type": "user", "message": {"content": "x" * 5000, "usage": {}}})
    good = json.dumps(_claude_assistant(_iso(now - H), "a", out=1_000_000))
    path.write_text(huge + "\n" + good + "\n", encoding="utf-8")
    os.utime(path, (now, now))
    assert len(qh.read_claude_history(tmp_path).usage) == 1


# ---- official Claude readings: status line, calibration, weekly ---------------------------

def test_statusline_records_only_official_windows_and_never_fails(tmp_path, monkeypatch, capsys):
    import io
    from reverse_agent.model_access import claude_statusline as sl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    payload = {"model": {"display_name": "Opus"}, "transcript_path": "C:/private/transcript.jsonl",
               "rate_limits": {"five_hour": {"used_percentage": 88, "resets_at": 1792000000},
                               "seven_day": {"used_percentage": 75, "resets_at": "2026-10-19T05:00:00Z"},
                               "spend_limit": {"used_percentage": 5}}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert sl.run_statusline() == 0
    assert "5h 88% · 7d 75%" in capsys.readouterr().out
    lines = [json.loads(x) for x in sl.log_path().read_text(encoding="utf-8").splitlines()]
    assert [(r["window"], r["used_percent"]) for r in lines] == [("five_hour", 88.0), ("weekly", 75.0)]
    assert lines[1]["resets_at"] == 1792386000 and "private" not in sl.log_path().read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert sl.run_statusline() == 0


def test_statusline_install_keeps_other_settings_and_refuses_a_foreign_status_line(tmp_path, monkeypatch):
    from reverse_agent.model_access import claude_statusline as sl
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "state"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    settings = tmp_path / "claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"model": "opus", "statusLine": {"type": "command", "command": "mine"}}),
                        encoding="utf-8")
    assert sl.install() == 1  # someone else's status line is not replaced
    settings.write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    assert sl.install() == 0
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["model"] == "opus" and "claude_statusline.py" in data["statusLine"]["command"]
    assert sl.uninstall() == 0 and json.loads(settings.read_text(encoding="utf-8")) == {"model": "opus"}


def test_calibration_divides_window_usage_by_the_official_percent():
    from reverse_agent.model_access.quota_forecast import calibrate
    reset = 10 * H
    usage = [UsageEvent(6 * H, 5.0), UsageEvent(7 * H, 6.0), UsageEvent(1 * H, 99.0)]  # last one: earlier window
    samples = [{"at": 7.5 * H, "used_percent": 40.0, "resets_at": reset},
               {"at": 8 * H, "used_percent": 55.0, "resets_at": reset}]   # latest reading of the window wins
    cap = calibrate(samples, usage, length=5 * H)
    assert cap["mid"] == pytest.approx(11.0 * 100 / 55) and cap["samples"] == 1
    assert calibrate([{"at": 8 * H, "used_percent": 5.0, "resets_at": reset}], usage, length=5 * H) is None


def test_hit_capacity_counts_one_hit_per_window_and_drops_probable_weekly_hits():
    events = [UsageEvent(0, 20.0), UsageEvent(6 * H, 22.0), UsageEvent(12 * H, 21.0), UsageEvent(18 * H, 3.0)]
    hits = [0.5 * H, 0.6 * H, 6.5 * H, 12.5 * H, 18.5 * H]  # a retry in window 1; window 4 hit the weekly cap
    cap = capacity_from_hits(events, hits)
    assert (cap["samples"], cap["low"]) == (3, 20.0)


def _statusline_file(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_claude_quota_shows_a_fresh_official_reading_as_is(tmp_path):
    now = time.time()
    log = tmp_path / "sl.jsonl"
    _statusline_file(log, [{"at": int(now - 60), "window": "five_hour", "used_percent": 88, "resets_at": int(now + 2 * H)},
                           {"at": int(now - 60), "window": "weekly", "used_percent": 75, "resets_at": int(now + 4 * 24 * H)}])
    quota = claude_quota(None, tmp_path / "none", now=now, statusline_path=log)
    five, weekly = quota["windows"]
    assert (five["basis"], five["used_percent"], five["official_source"]) == ("official_percent", 88, "claude_statusline")
    assert (weekly["window"], weekly["used_percent"], weekly["resets_at_estimated"]) == ("weekly", 75, False)
    assert quota["provenance"] == "OFFICIAL_VIA_CLI"


def test_claude_quota_carries_an_older_reading_forward_with_calibrated_capacity(tmp_path):
    now = time.time()
    reset = int(now + H)
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(now - 3 * H), "a", out=1_000_000),      # $10 before the reading
        _claude_assistant(_iso(now - 10 * 60), "b", out=500_000),      # $5 after it
    ])
    log = tmp_path / "sl.jsonl"
    _statusline_file(log, [{"at": int(now - 2 * H), "window": "five_hour", "used_percent": 50, "resets_at": reset}])
    window = claude_quota(None, tmp_path, now=now, statusline_path=log)["windows"][0]
    # $10 was 50% -> about $20 per window; $5 more is about 25 points.
    assert window["basis"] == "estimated" and window["anchor"]["used_percent"] == 50
    assert window["used_percent"] == pytest.approx(75, abs=0.5) and window["capacity_source"] == "official_calibration"
    assert window["resets_at_estimated"] is False


def test_weekly_window_rolls_the_official_reset_forward_and_counts_usage_since(tmp_path):
    now = time.time()
    week = 7 * 24 * H
    old_reset = int(now - 2 * 24 * H)  # last week's reset passed two days ago
    _write(tmp_path / "projects" / "p" / "s.jsonl", [
        _claude_assistant(_iso(old_reset - 3 * 24 * H), "a", out=4_000_000),   # $40 in the previous week
        _claude_assistant(_iso(now - 24 * H), "b", out=1_000_000),             # $10 this week
    ])
    log = tmp_path / "sl.jsonl"
    _statusline_file(log, [{"at": int(old_reset - 24 * H), "window": "weekly", "used_percent": 40,
                            "resets_at": old_reset}])
    weekly = next(w for w in claude_quota(None, tmp_path, now=now, statusline_path=log)["windows"]
                  if w["window"] == "weekly")
    assert weekly["basis"] == "estimated" and weekly["used_percent"] == pytest.approx(10, abs=0.5)
    assert weekly["resets_at"] == _iso(old_reset + week).replace("+00:00", "Z")
