"""Provider-free contract for third-party, read-only Codex reset observation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO

from reverse_agent.model_access.codex_reset_signals import (
    FEED_URL, MAX_FEED_BYTES, fetch_feed, parse_feed,
)

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=timezone.utc)


def item(identity: str, text: str, *, kind="candidate", explicit=False, **extra):
    return {
        "id": identity, "url": f"https://x.com/thsottiaux/status/{identity}",
        "at": "2026-10-19T08:40:00.000Z",
        "text": text, "kind": kind, "explicit_reset_claim": explicit, **extra,
    }


def feed(*items, at="2026-10-19T08:50:00.000Z", stale=False):
    return {"version": 1, "source": "x-api", "stale": stale,
            "fetched_at": at, "tweets": list(items)}


def test_announcement_remains_planning_only():
    event = parse_feed(feed(item("2112034063934742720",
                                 "Global reset landing within 2 hours",
                                 explicit=True)), now=NOW).events[0]
    assert event.kind == "RESET_ANNOUNCEMENT"
    assert event.action == "PLAN_ONLY"
    assert event.source_url == "https://x.com/thsottiaux/status/2112034063934742720"


def test_claimed_reset_only_triggers_vendor_refresh_not_dispatch():
    result = parse_feed(feed(item("2112034063934742721",
                                  "We have reset usage limits for Codex users",
                                  explicit=True)), now=NOW)
    assert result.status == "FRESH"
    assert result.events[0].action == "REFRESH_QUOTA"
    assert "DISPATCH" not in result.events[0].action


def test_banked_is_distinct_from_personal_quota():
    events = parse_feed(feed(item("2112034063934742722",
                                  "Loading a banked reset in paid accounts",
                                  kind="banked")), now=NOW).events
    assert len(events) == 1
    assert events[0].kind == "BANKED_ANNOUNCEMENT"
    assert events[0].action == "PLAN_ONLY"


def test_only_reply_context_can_attach_landing_to_reset():
    parent = item("2112034063934742723", "Day 13/ Le limit reset")
    child = item("2112034063934742724", "Landing sometime today",
                 kind="signal", reset_verification_candidate=True,
                 in_reply_to_tweet_id=parent["id"])
    unrelated = item("2112034063934742725", "Landing sometime today",
                     kind="signal", reset_verification_candidate=True,
                     in_reply_to_tweet_id="9999999999999999999")
    result = parse_feed(feed(parent, child, unrelated), now=NOW)
    assert [v.event_id for v in result.events] == [
        "tibo-x:2112034063934742724:RESET_ANNOUNCEMENT"
    ]


def test_hint_and_unrelated_resets_do_not_reactivate_account():
    teaser = item("2112034063934742726", "We'll see", kind="codex",
                  tease_classification={"teasing": True})
    unrelated = item("2112034063934742727", "How often do limits reset?",
                     kind="limits")
    events = parse_feed(feed(teaser, unrelated), now=NOW).events
    assert [e.kind for e in events] == ["POSSIBLE_HINT"]
    assert events[0].action == "PLAN_ONLY"


def test_bad_schema_stale_and_replayed_post_fail_closed():
    assert parse_feed(feed(at="2026-10-19T07:00:00.000Z"), now=NOW).status == "STALE"
    assert parse_feed(feed(stale=True), now=NOW).status == "UNKNOWN"
    assert parse_feed({"version": 2}, now=NOW).events == ()
    old = item("2112034063934742720", "We have reset limits", explicit=True)
    old["at"] = "2026-10-01T08:00:00.000Z"
    assert parse_feed(feed(old), now=NOW).events == ()


def test_fake_or_rewritten_original_link_and_duplicate_ids():
    a = item("2112034063934742720", "Global reset lands later", explicit=True)
    fake = {**a, "url": "https://evil.example.com/ref"}
    assert parse_feed(feed(fake), now=NOW).events == ()
    assert len(parse_feed(feed(a, a), now=NOW).events) == 1


class FakeResponse(BytesIO):
    def __init__(self, blob: bytes, content_type="application/json"):
        super().__init__(blob)
        self.headers = {"Content-Type": content_type}


def test_bounded_fetch_and_no_secrets_in_request():
    def opener(request, *, timeout):
        assert request.full_url == FEED_URL
        assert request.get_method() == "GET"
        assert timeout == 5
        assert "Authorization" not in request.headers
        assert "Cookie" not in request.headers
        return FakeResponse(json.dumps(feed()).encode())
    assert fetch_feed(opener=opener, now=NOW).status == "FRESH"
    assert fetch_feed(opener=lambda *a, **k: FakeResponse(b"x" * (MAX_FEED_BYTES + 1)),
                      now=NOW).reason == "response_too_large"
    assert fetch_feed(opener=lambda *a, **k: FakeResponse(b"{}","text/html"),
                      now=NOW).reason == "wrong_content_type"
    assert fetch_feed(opener=lambda *a, **k: (_ for _ in ()).throw(OSError("down")),
                      now=NOW).status == "UNKNOWN"
