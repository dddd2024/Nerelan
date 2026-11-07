"""Blocking, provider-free safety tests for Tibo X reset observer (#1246)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from io import BytesIO

from reverse_agent.model_access.codex_reset_signals import (
    FEED_URL, MAX_FEED_BYTES, fetch_feed, parse_feed,
)

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=timezone.utc)
X_EPOCH_MS = 1288834974657
POST_TIME = NOW - timedelta(minutes=20)


def post_id(n=1, when=POST_TIME):
    return str(((int(when.timestamp() * 1000) - X_EPOCH_MS) << 22) | n)


def item(n, text, *, kind="candidate", explicit=False, when=POST_TIME, **extra):
    identity = post_id(n, when)
    return {
        "id": identity, "url": f"https://x.com/thsottiaux/status/{identity}",
        "at": when.isoformat().replace("+00:00", "Z"),
        "text": text, "kind": kind, "explicit_reset_claim": explicit, **extra,
    }


def feed(*items, at=NOW-timedelta(minutes=10), stale=False):
    return {"version": 1, "source": "x-api", "stale": stale,
            "fetched_at": at.isoformat().replace("+00:00", "Z"), "tweets": list(items)}


def test_announcement_is_advisory():
    event = parse_feed(feed(item(1, "Global Codex reset landing within 2 hours",
                                 explicit=True)), now=NOW).events[0]
    assert event.kind == "RESET_ANNOUNCEMENT"
    assert event.action == "PLAN_ONLY"
    assert event.source_url.endswith(post_id(1))


def test_completed_global_codex_reset_only_requests_real_quota_refresh():
    result = parse_feed(feed(item(2, "We have reset limits for all Codex users",
                                  explicit=True)), now=NOW)
    assert result.status == "FRESH"
    assert result.events[0].kind == "RESET_REPORTED_COMPLETE"
    assert result.events[0].action == "REFRESH_QUOTA"
    assert all(x.action != "DISPATCH" for x in result.events)


def test_allowlisted_global_reset_completion_forms_really_refresh():
    posts = (
        item(31, "Global Codex limits reset complete", explicit=True),
        item(32, "Global Codex quotas reset is completed", explicit=True),
    )
    result = parse_feed(feed(*posts), now=NOW)
    assert [x.kind for x in result.events] == [
        "RESET_REPORTED_COMPLETE", "RESET_REPORTED_COMPLETE"
    ]
    assert all(x.action == "REFRESH_QUOTA" for x in result.events)


def test_personal_banked_and_missing_codex_scope_are_not_global():
    posts = (
        item(3, "My personal Codex quota has been reset", explicit=True),
        item(4, "We have reset banked Codex credits for everyone", explicit=True),
        item(5, "We have reset usage limits for all users", explicit=True),
    )
    result = parse_feed(feed(*posts), now=NOW)
    assert len(result.events) == 3
    assert {x.kind for x in result.events} == {"RESET_SCOPE_UNVERIFIED"}
    assert all(x.action == "PLAN_ONLY" for x in result.events)


def test_negated_or_pending_reset_is_never_completed():
    posts = (
        item(33, "Not all Codex users have been reset yet", explicit=True),
        item(34, "We have not reset every Codex user", explicit=True),
        item(35, "Global Codex reset is still pending: it has been reset soon", explicit=True),
    )
    result = parse_feed(feed(*posts), now=NOW)
    assert len(result.events) == 3
    assert all(e.kind != "RESET_REPORTED_COMPLETE" for e in result.events)
    assert all(e.action == "PLAN_ONLY" for e in result.events)


def test_codex_exclusion_and_partial_scope_never_refresh():
    posts = (
        item(36, "We have reset all products except Codex", explicit=True),
        item(37, "Almost all Codex users have been reset", explicit=True),
        item(38, "We have reset limits for all Codex users except Pro", explicit=True),
        item(39, "We have reset limits for all Codex users, but it is incomplete", explicit=True),
    )
    result = parse_feed(feed(*posts), now=NOW)
    assert len(result.events) == 4
    assert all(x.kind != "RESET_REPORTED_COMPLETE" for x in result.events)
    assert all(x.action == "PLAN_ONLY" for x in result.events)


def test_banked_grant_remains_distinct_from_personal_limits():
    events = parse_feed(feed(item(6, "Loading a banked reset in paid accounts",
                                  kind="banked")), now=NOW).events
    assert len(events) == 1
    assert events[0].kind == "BANKED_ANNOUNCEMENT"
    assert events[0].action == "PLAN_ONLY"


def test_reply_requires_valid_original_parent():
    parent = item(7, "Day 13: Codex global reset")
    child = item(8, "Landing sometime today", kind="signal",
                 when=POST_TIME + timedelta(minutes=1),
                 reset_verification_candidate=True, in_reply_to_tweet_id=parent["id"])
    malformed_parent = {**parent, "url": "https://malicious.example/status/" + parent["id"]}
    assert len(parse_feed(feed(parent, child), now=NOW).events) == 2-1 # child only
    assert not parse_feed(feed(malformed_parent, child), now=NOW).events
    stale_parent = {**parent, "at": "2026-10-01T10:00:00Z"}
    assert not parse_feed(feed(stale_parent, child), now=NOW).events


def test_reply_parent_must_be_older_than_reply():
    younger_parent = item(40, "Codex global reset", when=POST_TIME + timedelta(minutes=2))
    older_reply = item(41, "Landing today", kind="signal",
                       reset_verification_candidate=True,
                       in_reply_to_tweet_id=younger_parent["id"])
    assert parse_feed(feed(younger_parent, older_reply), now=NOW).events == ()
    same_time_parent = item(42, "Codex global reset")
    same_time_reply = item(43, "Landing today", kind="signal",
                           reset_verification_candidate=True,
                           in_reply_to_tweet_id=same_time_parent["id"])
    assert parse_feed(feed(same_time_parent, same_time_reply), now=NOW).events == ()


def test_timestamp_skew_cannot_reverse_x_snowflake_reply_order():
    parent = item(50, "Global Codex reset", when=POST_TIME + timedelta(minutes=2))
    child = item(51, "Landing now", kind="signal",
                 reset_verification_candidate=True, in_reply_to_tweet_id=parent["id"])
    # Both claimed timestamps are within 5m of their Snowflakes, but the
    # mirror can make the truly newer parent *appear* earlier than the reply.
    parent["at"] = (POST_TIME - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
    child["at"] = (POST_TIME + timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    assert not parse_feed(feed(parent, child), now=NOW).events


def test_spoofed_original_url_and_unhashable_id_do_not_throw():
    a = item(9, "Global Codex reset landing", explicit=True)
    assert parse_feed(feed({**a, "url": "https://evil.example/status/x"}), now=NOW).events == ()
    out = parse_feed(feed({"id": [], "text": "global Codex reset", "url": "x"}), now=NOW)
    assert out.status == "FRESH" and out.events == ()
    assert parse_feed(feed({"id": {"bad": "key"}}), now=NOW).events == ()


def test_replayed_snowflake_cannot_receive_forged_new_timestamp():
    old = item(10, "We have reset Codex for all users", explicit=True,
               when=NOW - timedelta(days=30))
    old["at"] = POST_TIME.isoformat().replace("+00:00", "Z")
    assert parse_feed(feed(old), now=NOW).events == ()


def test_stale_future_and_bad_feed_fail_closed():
    assert parse_feed(feed(at=NOW-timedelta(hours=2)), now=NOW).status == "STALE"
    assert parse_feed(feed(stale=True), now=NOW).status == "UNKNOWN"
    assert parse_feed({"version": 2}, now=NOW).events == ()
    assert parse_feed(feed(at=NOW+timedelta(hours=1)), now=NOW).status == "STALE"


def test_event_id_deduped_by_original_post_even_on_reclassification():
    a = item(11, "We have reset for all Codex users", explicit=True)
    reclassified = {**a, "kind": "codex", "explicit_reset_claim": False,
                    "tease_classification": {"teasing": True}}
    result = parse_feed(feed(a, reclassified), now=NOW)
    assert len(result.events) == 1
    assert result.events[0].event_id == "tibo-x:" + post_id(11)
    second = parse_feed(feed(reclassified), now=NOW).events[0]
    assert second.event_id == result.events[0].event_id


def test_only_contextual_verified_reply_promoted():
    parent = item(12, "Day 13 / Codex reset")
    child = item(13, "Landing today", kind="signal",
                 when=POST_TIME + timedelta(minutes=1), reset_verification_candidate=True,
                 in_reply_to_tweet_id=parent["id"])
    stranger = item(14, "Landing today", kind="signal", reset_verification_candidate=True,
                    in_reply_to_tweet_id=post_id(666))
    events = parse_feed(feed(parent, child, stranger), now=NOW).events
    assert [x.event_id for x in events] == [
        "tibo-x:" + post_id(13, POST_TIME + timedelta(minutes=1))
    ]


class FakeResponse(BytesIO):
    def __init__(self, blob: bytes, content_type="application/json"):
        super().__init__(blob)
        self.headers = {"Content-Type": content_type}


def test_bounded_fetch_without_secrets_or_provider_calls():
    def opener(request, *, timeout):
        assert request.full_url == FEED_URL and request.get_method() == "GET"
        assert timeout == 5
        assert "Authorization" not in request.headers and "Cookie" not in request.headers
        return FakeResponse(json.dumps(feed()).encode())
    assert fetch_feed(opener=opener, now=NOW).status == "FRESH"
    assert fetch_feed(opener=lambda *a, **k: FakeResponse(b"x"*(MAX_FEED_BYTES+1)),
                      now=NOW).reason == "response_too_large"
    assert fetch_feed(opener=lambda *a, **k: FakeResponse(b"{}","text/html"),
                      now=NOW).reason == "wrong_content_type"
    assert fetch_feed(opener=lambda *a, **k: (_ for _ in ()).throw(OSError("down")),
                      now=NOW).status == "UNKNOWN"


def test_dns_like_open_stall_does_not_block_host_or_spawn_more_workers(monkeypatch):
    import threading
    import time
    from reverse_agent.model_access import codex_reset_signals as mod

    opened = threading.Event()
    release = threading.Event()

    def slow_open(request, *, timeout):
        opened.set()
        release.wait(1.0)
        return FakeResponse(json.dumps(feed()).encode())

    monkeypatch.setattr(mod, "MAX_FETCH_SECONDS", 0.025)
    started = time.perf_counter()
    first = fetch_feed(opener=slow_open, now=NOW)
    assert first.reason == "fetch_deadline_exceeded"
    assert time.perf_counter() - started < 0.25
    assert opened.is_set()
    second = fetch_feed(opener=slow_open, now=NOW)
    assert second.reason == "previous_fetch_still_running"
    release.set()
    # Clean up this finite fake worker to avoid making later tests observe a
    # deliberately in-flight fetch. Production DNS can remain blocked safely.
    mod._FETCH_WORKER.join(timeout=1.0)


def test_fetch_respects_deadline_even_when_chunks_are_dribbled(monkeypatch):
    t = [100.0]
    from reverse_agent.model_access import codex_reset_signals as mod

    def ticking():
        t[0] += 0.6
        return t[0]

    monkeypatch.setattr(mod.time, "monotonic", ticking)
    class InfiniteResponse(FakeResponse):
        def __init__(self):
            super().__init__(b"")
        def read1(self, n=-1):
            return b"a"

    result = fetch_feed(opener=lambda *a, **k: InfiniteResponse(), now=NOW)
    assert result.status == "UNKNOWN"
    assert result.reason == "fetch_deadline_exceeded"


# --- routing translation (Owner rule 2026-11-07: an announced reset lands within a day)

from datetime import datetime as _dt, timedelta as _td, timezone as _tz
import threading as _threading

import pytest

from reverse_agent.model_access.codex_reset_signals import (
    CodexResetSignalReader,
    ResetEvent,
    ResetObservation,
    routing_signal,
)
from reverse_agent.platform_v1.routing_inputs import reset_decision

_POSTED = _dt(2026, 11, 7, 12, tzinfo=_tz.utc)


def _event(kind, at=_POSTED, action="PLAN_ONLY", ident="1"):
    return ResetEvent(f"tibo-x:{ident}", kind, f"https://x.com/thsottiaux/status/{ident}",
                      at.isoformat().replace("+00:00", "Z"), "text", action)


def _fresh(*events):
    return ResetObservation("FRESH", "2026-11-07T12:00:00Z", tuple(events))


def test_an_announcement_is_read_as_a_reset_within_a_day():
    signal = routing_signal(_fresh(_event("RESET_ANNOUNCEMENT")), now=_POSTED + _td(hours=2))
    assert signal["state"] == "PLAN_ONLY" and signal["validated"] is True and signal["assumed"] is True
    assert signal["expected_reset_at"] == "2026-11-08T12:00:00Z"
    decision = reset_decision(signal, now=(_POSTED + _td(hours=2)).timestamp(), weekly_remaining=.26)
    assert decision["drain"] is True


def test_an_announcement_older_than_the_window_stops_draining():
    signal = routing_signal(_fresh(_event("RESET_ANNOUNCEMENT")), now=_POSTED + _td(hours=25))
    assert signal["state"] == "UNKNOWN"
    assert reset_decision(signal, now=(_POSTED + _td(hours=25)).timestamp(), weekly_remaining=.26)["drain"] is False


def test_the_window_is_an_owner_knob():
    signal = routing_signal(_fresh(_event("RESET_ANNOUNCEMENT")), now=_POSTED + _td(hours=30), within=_td(hours=48))
    assert signal["state"] == "PLAN_ONLY"


def test_a_reported_completion_asks_for_a_quota_reread():
    signal = routing_signal(_fresh(_event("RESET_ANNOUNCEMENT"),
                                   _event("RESET_REPORTED_COMPLETE", _POSTED + _td(hours=3), "REFRESH_QUOTA", "2")),
                            now=_POSTED + _td(hours=4))
    assert signal["state"] == "REFRESH_QUOTA"


def test_a_newer_announcement_after_a_completion_drains_again():
    signal = routing_signal(_fresh(_event("RESET_REPORTED_COMPLETE", _POSTED, "REFRESH_QUOTA", "2"),
                                   _event("RESET_ANNOUNCEMENT", _POSTED + _td(hours=2), ident="3")),
                            now=_POSTED + _td(hours=3))
    assert signal["state"] == "PLAN_ONLY"


@pytest.mark.parametrize("kind", ["POSSIBLE_HINT", "BANKED_ANNOUNCEMENT", "RESET_SCOPE_UNVERIFIED"])
def test_hints_banked_and_unverified_scope_never_drain(kind):
    assert routing_signal(_fresh(_event(kind)), now=_POSTED)["state"] == "UNKNOWN"


@pytest.mark.parametrize("status", ["STALE", "UNKNOWN"])
def test_an_unusable_feed_is_no_announcement(status):
    signal = routing_signal(ResetObservation(status, None, (_event("RESET_ANNOUNCEMENT"),), "x"), now=_POSTED)
    assert signal["state"] in {"STALE", "UNKNOWN"}
    assert reset_decision(signal, now=_POSTED.timestamp(), weekly_remaining=.26)["drain"] is False


def test_the_reader_never_blocks_routing_on_the_network():
    release = _threading.Event()

    def slow_fetch():
        release.wait(5)
        return _fresh(_event("RESET_ANNOUNCEMENT"))

    clock = {"now": _POSTED.timestamp() + 60}
    reader = CodexResetSignalReader(fetch=slow_fetch, clock=lambda: clock["now"])
    assert reader()["state"] == "UNKNOWN"  # returned at once while the fetch is pending
    release.set()
    for _ in range(100):
        if reader()["state"] == "PLAN_ONLY":
            break
        _threading.Event().wait(.02)
    assert reader()["state"] == "PLAN_ONLY"


def test_the_reader_polls_at_most_once_per_interval_and_survives_errors():
    calls = []

    def fetch():
        calls.append(1)
        raise OSError("down")

    clock = {"now": 1_000.0}
    reader = CodexResetSignalReader(fetch=fetch, clock=lambda: clock["now"], poll_seconds=900)
    reader()
    for _ in range(100):
        if calls:
            break
        _threading.Event().wait(.01)
    _threading.Event().wait(.05)
    reader()
    assert len(calls) == 1
    clock["now"] += 901
    reader()
    for _ in range(100):
        if len(calls) == 2:
            break
        _threading.Event().wait(.01)
    assert len(calls) == 2 and reader()["state"] == "UNKNOWN"


def test_a_real_response_without_a_reachable_socket_is_read(monkeypatch):
    """The Python 3.13 failure: the observer gave up whenever it could not reach the socket."""
    import io
    from reverse_agent.model_access import codex_reset_signals as module

    body = json.dumps({"version": 1, "source": "x-api", "stale": False,
                       "fetched_at": _POSTED.isoformat().replace("+00:00", "Z"), "tweets": []}).encode()

    class Response(io.BytesIO):
        headers = {"Content-Type": "application/json"}

        def read1(self, size=-1):
            return self.read(size)

    monkeypatch.setattr(module.urllib.request, "build_opener",
                        lambda *a: type("O", (), {"open": staticmethod(lambda req, timeout: Response(body))})())
    observation = module._fetch_feed_worker(now=_POSTED)
    assert observation.status == "FRESH"


# --- stated times and Tibo's real announcement shape (October 2026) -----------

from reverse_agent.model_access.codex_reset_signals import parse_feed, stated_time


def _snowflake(at):
    """A post id whose X Snowflake time is `at`, as the validator requires."""
    return str((int(at.timestamp() * 1000) - 1288834974657) << 22)


def _post(at, text, *, reply=False, **extra):
    ident = _snowflake(at)
    return {"id": ident, "url": f"https://x.com/thsottiaux/status/{ident}", "text": text,
            "at": at.isoformat().replace("+00:00", "Z"), "is_reply": reply, "kind": "other",
            "explicit_reset_claim": False, **extra}


def _feed(now, tweets, events=()):
    return {"version": 1, "source": "x-api", "stale": False,
            "fetched_at": now.isoformat().replace("+00:00", "Z"), "tweets": list(tweets), "events": list(events)}


_ANNOUNCED = _dt(2026, 10, 28, 2, 42, 53, tzinfo=_tz.utc)


@pytest.mark.parametrize("text,expected", [
    ("Lands by midnight PST.", _dt(2026, 10, 28, 7, tzinfo=_tz.utc)),   # PDT in October
    ("at 10am PT", _dt(2026, 10, 28, 17, tzinfo=_tz.utc)),
    ("by 18:00 UTC", _dt(2026, 10, 28, 18, tzinfo=_tz.utc)),
    ("in 2 hours", _ANNOUNCED + _td(hours=2)),
    ("in an hour", _ANNOUNCED + _td(hours=1)),
])
def test_stated_times_are_read_relative_to_the_post(text, expected):
    assert stated_time(text, _ANNOUNCED) == expected


@pytest.mark.parametrize("text", ["midnight", "reset at noon", "by 25:00 UTC", "at 13pm PT", "in 99 hours"])
def test_vague_or_impossible_times_are_not_guessed(text):
    assert stated_time(text, _ANNOUNCED) is None


def test_the_october_28_thread_drains_until_the_stated_midnight():
    tweets = [_post(_ANNOUNCED, "Day 23/ Much requested plugins. Just kidding, today is a reset."),
              _post(_ANNOUNCED + _td(seconds=45), "Lands by midnight PST.", reply=True)]
    now = _ANNOUNCED + _td(minutes=5)
    signal = routing_signal(parse_feed(_feed(now, tweets), now=now), now=now)
    assert signal["state"] == "PLAN_ONLY" and signal["assumed"] is False
    assert signal["expected_reset_at"] == "2026-10-28T07:00:00Z"
    later = _dt(2026, 10, 28, 7, 5, tzinfo=_tz.utc)
    assert routing_signal(parse_feed(_feed(later, tweets), now=later), now=later)["state"] == "UNKNOWN"


def test_today_without_a_time_ends_at_pacific_midnight_not_a_day_later():
    posted = _dt(2026, 10, 26, 5, 21, tzinfo=_tz.utc)
    tweets = [_post(posted, "Day 21/ Wonder what happens the remaining seven days. But today is a reset.")]
    now = posted + _td(minutes=10)
    signal = routing_signal(parse_feed(_feed(now, tweets), now=now), now=now)
    assert signal["expected_reset_at"] == "2026-10-26T07:00:00Z"


@pytest.mark.parametrize("text", ["Is today a reset?", "today is not a reset", "Tomorrow is a reset day maybe"])
def test_questions_and_negations_are_not_announcements(text):
    now = _ANNOUNCED + _td(minutes=1)
    assert routing_signal(parse_feed(_feed(now, [_post(_ANNOUNCED, text)]), now=now), now=now)["state"] == "UNKNOWN"


def test_the_feeds_own_reset_events_count_and_banked_ones_do_not():
    ident = _snowflake(_ANNOUNCED)
    event = {"type": "reset", "scope": "global", "reset_kind": None, "preview": False, "confidence": "medium",
             "announcement_state": "announced", "url": f"https://x.com/thsottiaux/status/{ident}",
             "announced_at": _ANNOUNCED.isoformat().replace("+00:00", "Z"), "summary": "By midnight PST"}
    now = _ANNOUNCED + _td(minutes=1)
    assert routing_signal(parse_feed(_feed(now, [], [event]), now=now), now=now)["state"] == "PLAN_ONLY"
    for change in ({"reset_kind": "banked"}, {"scope": "account"}, {"confidence": "low"},
                   {"announcement_state": "none"}, {"url": "https://example.com/x"}, {"preview": True}):
        observation = parse_feed(_feed(now, [], [{**event, **change}]), now=now)
        assert routing_signal(observation, now=now)["state"] == "UNKNOWN", change
