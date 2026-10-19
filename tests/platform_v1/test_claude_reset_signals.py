"""Provider-free, blocking CI tests for Claude reset awareness (#1255)."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO

from reverse_agent.model_access import claude_reset_signals as signals

NOW = datetime(2026, 10, 19, 10, 45, tzinfo=timezone.utc)
EARLIER = NOW - timedelta(hours=2)
_X_EPOCH = 1288834974657


def iso(when):
    return when.isoformat().replace("+00:00", "Z")


def source(when=EARLIER, *, handle="ClaudeDevs", url=None):
    snowflake = str(((int(when.timestamp() * 1000) - _X_EPOCH) << 22) | 4)
    return {"kind": "x_post", "role": "original",
            "url": url or f"https://x.com/{handle}/status/{snowflake}",
            "handle": handle, "posted_at": iso(when)}


def event(name="2026-10-19-all-claude", *, kind="usage_reset", status="confirmed",
          when=EARLIER, revision=1, plans=None, scope="broad", windows=None,
          expires=None):
    return {
        "id": name, "kind": kind, "event_status": status, "revision": revision,
        "time_precision": "exact", "announced_at": iso(when),
        "allocation": "subscription_usage",
        "audience": {"scope": scope, "plans": plans or [], "statement": "sample"},
        "windows": windows or ["five_hour", "weekly"], "sources": [source(when)],
        "url": f"https://clauderesets.com/resets/{name}",
        "reset_offer": {"expires_on": expires} if expires else None,
    }


def status(*, latest=None, offers=None, announced=None, generated=None):
    return {
        "meta": {"api_version": "v1", "generated_at": iso(generated or NOW - timedelta(minutes=2)),
                 "editorial_reviewed_at": iso(NOW - timedelta(hours=3))},
        "data": {"latest_reset": latest, "reset_offers": offers if offers is not None else [],
                 "announced_reset": announced, "latest_ambiguous": None},
    }


def parse(payload):
    return signals.parse_status(payload, now=NOW)


def test_confirmed_applied_reset_requests_quota_refresh_only():
    v = parse(status(latest=event()))
    assert v.status == "FRESH"
    assert len(v.events) == 1
    e, = v.events
    assert e.kind == "RESET_REPORTED_COMPLETE" and e.action == "REFRESH_QUOTA"
    assert e.windows == ("five_hour", "weekly")
    assert e.plans == ()
    assert e.event_id == "claude-reset:2026-10-19-all-claude"


def test_banked_reset_with_plan_scope_and_expiry_cannot_refresh():
    e = event("2026-09-22-bank", kind="credit", when=NOW-timedelta(days=27),
              plans=["pro", "max", "team"], scope="limited", windows=["unspecified"],
              expires="2026-10-22")
    v = parse(status(offers=[e]))
    assert [x.action for x in v.events] == ["CLAIM_MANUALLY"]
    assert v.events[0].plans == ("pro", "max", "team")
    assert v.events[0].expires_on == "2026-10-22"
    assert not parse(status(offers=[{**e, "reset_offer": {"expires_on": "2026-10-18"}}])).events


def test_unconfirmed_banked_offer_is_not_yet_claimable():
    draft = event("future-claude-grant", kind="credit", status="announced",
                  when=EARLIER, plans=["pro", "max"], scope="limited",
                  windows=["unspecified"], expires="2026-10-22")
    v = parse(status(offers=[draft]))
    assert [x.kind for x in v.events] == ["BANKED_ANNOUNCEMENT"]
    assert [x.action for x in v.events] == ["PLAN_ONLY"]


def test_old_applied_reset_must_not_reopen_quota():
    e = event(when=NOW-timedelta(days=35))
    assert parse(status(latest=e)).events == ()


def test_an_announced_reset_remains_plan_only():
    e = event("claude-announced-19", status="announced")
    v = parse(status(announced=e))
    assert [x.action for x in v.events] == ["PLAN_ONLY"]


def test_revision_and_retraction_invalidate_existing_event():
    e = event(revision=4, status="retracted")
    v = parse(status(latest=e))
    assert [x.kind for x in v.events] == ["RETRACTED"]
    assert [x.action for x in v.events] == ["INVALIDATE_HINT"]
    assert v.events[0].revision == 4


def test_stale_future_unknown_api_versions_fail_closed():
    assert parse(status(generated=NOW-timedelta(hours=5))).status == "STALE"
    assert parse(status(generated=NOW+timedelta(hours=1))).status == "STALE"
    assert parse({"meta": {"api_version": "v2"}, "data": {}}).status == "UNKNOWN"
    v = status()
    v["data"]["reset_offers"] = "not list"
    assert parse(v).events == () and parse(v).status == "UNKNOWN"


def test_wrong_x_link_and_forged_snowflake_are_rejected():
    a = event()
    a["sources"][0]["url"] = "https://evil.example/collector"
    assert parse(status(latest=a)).events == ()
    b = event()
    b["sources"][0] = source(NOW-timedelta(days=30))
    assert parse(status(latest=b)).events == ()


def test_wrong_tracker_permalink_bogus_plans_and_api_credits_rejected():
    a = event()
    a["url"] = "https://clauderesets.com@evil.example/resets/"+a["id"]
    assert not parse(status(latest=a)).events
    b = event(plans=["paid-undocumented"], scope="limited")
    assert not parse(status(latest=b)).events
    c = event()
    c["allocation"] = "api_credits"
    assert not parse(status(latest=c)).events


def test_no_unsupported_or_partial_provider_evidence():
    a = event(scope="limited")
    assert not parse(status(latest=a)).events
    a = event()
    a["event_status"] = "speculated"
    assert not parse(status(latest=a)).events


def test_duplicate_event_id_prefers_highest_revision():
    a = event("same-claude-reset", revision=1)
    b = event("same-claude-reset", revision=2, kind="credit", expires="2026-10-22",
              windows=["unspecified"])
    v = parse(status(latest=a, offers=[b]))
    assert len(v.events) == 1 and v.events[0].revision == 2
    assert v.events[0].action == "CLAIM_MANUALLY"


class FakeResponse(BytesIO):
    def __init__(self, body, typ="application/json"):
        super().__init__(body)
        self.headers = {"Content-Type": typ}


def test_http_fetch_bounded_no_credentials_and_readonly():
    def opener(request, *, timeout):
        assert request.full_url == signals.STATUS_URL
        assert request.get_method() == "GET"
        assert "Authorization" not in request.headers and "Cookie" not in request.headers
        return FakeResponse(json.dumps(status()).encode())
    v = signals.fetch_status(opener=opener, now=NOW)
    assert v.status == "FRESH"
    assert signals.fetch_status(
        opener=lambda *a, **kw: FakeResponse(b"Z"*(signals.MAX_BODY+1)), now=NOW).status == "UNKNOWN"
    assert signals.fetch_status(
        opener=lambda *a, **kw: FakeResponse(b"<html>", "text/html"), now=NOW).status == "UNKNOWN"
    assert signals.fetch_status(
        opener=lambda *a, **kw: (_ for _ in ()).throw(OSError("network")), now=NOW).status == "UNKNOWN"


def test_dns_open_stall_deadline_and_bounded_one_worker(monkeypatch):
    entered = threading.Event()
    done = threading.Event()
    def hung(request, *, timeout):
        entered.set()
        done.wait(2)
        return FakeResponse(json.dumps(status()).encode())
    monkeypatch.setattr(signals, "MAX_FETCH_SECONDS", 0.025)
    start = time.monotonic()
    first = signals.fetch_status(opener=hung, now=NOW)
    assert first.reason == "fetch_timeout"
    assert time.monotonic() - start < 0.2 and entered.is_set()
    second = signals.fetch_status(opener=hung, now=NOW)
    assert second.reason == "previous_fetch_still_running"
    done.set()
    signals._NETWORK_WORKER.join(timeout=1)


def test_watcher_persists_dedupe_and_new_revision(tmp_path):
    current = [signals.ClaudeResetObservation("FRESH", iso(NOW), iso(NOW), parse(status(latest=event())).events)]
    watcher = signals.ClaudeResetWatcher(tmp_path, fetcher=lambda: current[0])
    state = watcher.poll_once()
    assert len(state["new_events"]) == 1
    assert watcher.poll_once()["new_events"] == []
    restart = signals.ClaudeResetWatcher(tmp_path, fetcher=lambda: current[0])
    assert restart.poll_once()["new_events"] == []
    current[0] = signals.ClaudeResetObservation(
        "FRESH", iso(NOW), iso(NOW), parse(status(latest=event(revision=2,status="retracted"))).events)
    state = restart.poll_once()
    assert len(state["new_events"]) == 1
    assert state["new_events"][0]["action"] == "INVALIDATE_HINT"
    assert restart.poll_once()["new_events"] == []


def test_unknown_poll_keeps_receipts_no_duplicate(tmp_path):
    outcomes = [
        parse(status(latest=event())),
        signals.ClaudeResetObservation("UNKNOWN", None, None, (), "service_down"),
    ]
    watcher = signals.ClaudeResetWatcher(tmp_path, fetcher=lambda: outcomes.pop(0))
    watcher.poll_once()
    x = watcher.poll_once()
    assert x["status"] == "UNKNOWN" and x["new_events"] == []
    assert len(x["events"]) == 1


def test_watcher_interval_minimum_and_clean_stop(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        signals.ClaudeResetWatcher(tmp_path, poll_seconds=5)
    called = threading.Event()
    def fake_fetch():
        called.set()
        return signals.ClaudeResetObservation("FRESH", iso(NOW), iso(NOW), ())
    watcher = signals.ClaudeResetWatcher(tmp_path, fetcher=fake_fetch,
                                        poll_seconds=signals.MIN_POLL_SECONDS)
    watcher.start()
    assert called.wait(1.5)
    watcher.stop()
    assert watcher._thread is None


def test_real_host_opt_in_and_model_control_read_only_status(tmp_path, monkeypatch):
    from urllib.request import urlopen
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    monkeypatch.setenv("REVERSE_AGENT_CLAUDE_RESET_WATCH", "1")
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    called = []
    def no_live_network(self):
        called.append("watch_started")
    monkeypatch.setattr(signals.ClaudeResetWatcher, "start", no_live_network)
    host = CombinedTrustedHost(
        task_db_path=str(tmp_path / "tasks.sqlite3"),
        model_control_port=0, task_api_port=0,
        execution_authority_sha="", planning_sha="",
        auth_list_probe=None,
    )
    try:
        host.start(coordinator_paused=True)
        assert called == ["watch_started"]
        with urlopen(host.model_control_url + "/api/reset-announcements", timeout=3) as response:
            assert response.status == 200
            view = json.load(response)
        assert view["enabled"] is True
        assert view["provider"] == "claude-code"
        assert view["status"] == "UNKNOWN"
        assert view["reason"] == "not_checked"
        assert host._coordinator._thread is None
    finally:
        host.stop()
    assert host._claude_reset_watcher is None


def test_real_host_default_disabled_without_network(tmp_path, monkeypatch):
    from urllib.request import urlopen
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    monkeypatch.delenv("REVERSE_AGENT_CLAUDE_RESET_WATCH", raising=False)
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    host = CombinedTrustedHost(
        task_db_path=str(tmp_path / "tasks.sqlite3"),
        model_control_port=0, task_api_port=0,
        execution_authority_sha="", planning_sha="",
        auth_list_probe=None,
    )
    try:
        host.start(coordinator_paused=True)
        with urlopen(host.model_control_url + "/api/reset-announcements", timeout=3) as response:
            view = json.load(response)
        assert view["enabled"] is False
        assert view["status"] == "UNKNOWN"
        assert host._claude_reset_watcher is None
    finally:
        host.stop()


def test_banked_offer_expiry_is_invalidated_even_if_source_offline(tmp_path):
    now = [datetime(2026, 10, 21, 23, 0, tzinfo=timezone.utc)]
    offer = event("2026-09-22-bank", kind="credit", when=NOW-timedelta(days=27),
                  plans=["pro", "max", "team"], scope="limited",
                  windows=["unspecified"], expires="2026-10-22")
    observations = [parse(status(offers=[offer])),
                    signals.ClaudeResetObservation("UNKNOWN", None, None, (), "no_network")]
    watcher = signals.ClaudeResetWatcher(
        tmp_path, fetcher=lambda: observations.pop(0), clock=lambda: now[0])
    first = watcher.poll_once()
    assert first["new_events"][0]["action"] == "CLAIM_MANUALLY"
    now[0] = datetime(2026, 10, 23, 0, 1, tzinfo=timezone.utc)
    expired = watcher.poll_once()
    assert expired["status"] == "UNKNOWN"
    assert expired["new_events"][0]["action"] == "INVALIDATE_HINT"
    assert expired["new_events"][0]["kind"] == "BANKED_OFFER_EXPIRED"
    assert len(expired["events"]) == 1


def test_applied_reset_refreshes_readonly_quota_once_across_restart(tmp_path):
    calls = []
    observed = parse(status(latest=event()))
    watcher = signals.ClaudeResetWatcher(
        tmp_path, fetcher=lambda: observed,
        on_quota_refresh=lambda: calls.append("official_cli_cache_reload"))
    watcher.poll_once()
    watcher.poll_once()
    again = signals.ClaudeResetWatcher(
        tmp_path, fetcher=lambda: observed,
        on_quota_refresh=lambda: calls.append("duplicate"))
    again.poll_once()
    assert calls == ["official_cli_cache_reload"]


def test_banked_and_retracted_not_trigger_quota_refresh(tmp_path):
    calls = []
    offer = event("manual-grant", kind="credit", when=NOW-timedelta(days=5),
                  plans=["pro", "max"], scope="limited",
                  windows=["unspecified"], expires="2026-10-22")
    inputs = [parse(status(offers=[offer])),
              parse(status(latest=event(status="retracted")))]
    watcher = signals.ClaudeResetWatcher(
        tmp_path, fetcher=lambda: inputs.pop(0),
        on_quota_refresh=lambda: calls.append("unexpected"))
    watcher.poll_once()
    watcher.poll_once()
    assert calls == []
