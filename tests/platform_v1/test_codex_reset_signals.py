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


def test_banked_grant_remains_distinct_from_personal_limits():
    events = parse_feed(feed(item(6, "Loading a banked reset in paid accounts",
                                  kind="banked")), now=NOW).events
    assert len(events) == 1
    assert events[0].kind == "BANKED_ANNOUNCEMENT"
    assert events[0].action == "PLAN_ONLY"


def test_reply_requires_valid_original_parent():
    parent = item(7, "Day 13: Codex global reset")
    child = item(8, "Landing sometime today", kind="signal",
                 reset_verification_candidate=True, in_reply_to_tweet_id=parent["id"])
    malformed_parent = {**parent, "url": "https://malicious.example/status/" + parent["id"]}
    assert len(parse_feed(feed(parent, child), now=NOW).events) == 2-1 # child only
    assert not parse_feed(feed(malformed_parent, child), now=NOW).events
    stale_parent = {**parent, "at": "2026-10-01T10:00:00Z"}
    assert not parse_feed(feed(stale_parent, child), now=NOW).events


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
    child = item(13, "Landing today", kind="signal", reset_verification_candidate=True,
                 in_reply_to_tweet_id=parent["id"])
    stranger = item(14, "Landing today", kind="signal", reset_verification_candidate=True,
                    in_reply_to_tweet_id=post_id(666))
    events = parse_feed(feed(parent, child, stranger), now=NOW).events
    assert [x.event_id for x in events] == ["tibo-x:" + post_id(13)]


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
