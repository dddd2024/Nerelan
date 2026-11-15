"""Correct the observed Codex quota window selection across session logs.

Tests use synthetic account events only; do not use a live subscription.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time

from reverse_agent.model_access.subscription_quota import read_codex_quota, codex_quota


def create_session(home, name, events, *, mtime=None):
    folder = home / "sessions" / "2026" / "10" / "16"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name + ".jsonl")
    path.write_text("\n".join(json.dumps(v) for v in events) + "\n", encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def evt(at, percent=None, *, weekly=47.0):
    limits = {"plan_type": "plus"}
    if percent is not None:
        limits["primary"] = {
            "window_minutes": 300, "used_percent": percent,
            "resets_at": int(at.timestamp()) + 3600,
        }
        limits["secondary"] = {
            "window_minutes": 10080, "used_percent": weekly,
            "resets_at": int(at.timestamp()) + 5 * 86400,
        }
    return {"type": "event_msg", "timestamp": at.isoformat().replace("+00:00", "Z"),
            "payload": {"type": "token_count", "rate_limits": limits}}


def test_last_plan_only_event_cannot_erase_latest_real_windows(tmp_path):
    now = datetime.now(timezone.utc)
    before = now - timedelta(minutes=12)
    create_session(tmp_path, "this-account", [evt(before, 100.0), evt(now - timedelta(minutes=1))])
    for fn in (read_codex_quota, codex_quota):
        quota = fn(tmp_path, now=now.timestamp())
        assert quota["state"] == "OBSERVED"
        assert quota["observed_at"] == before.isoformat().replace("+00:00", "Z")
        assert [v["used_percent"] for v in quota["windows"]][:2] == [100.0, 47.0]


def test_last_log_modified_is_not_same_as_newest_account_observation(tmp_path):
    now = datetime.now(timezone.utc)
    old, recent = now - timedelta(hours=2), now - timedelta(minutes=3)
    create_session(tmp_path, "old-but-updated-file", [evt(old, 20.0)], mtime=now.timestamp())
    create_session(tmp_path, "latest-event-but-older-file", [evt(recent, 99.0)],
                   mtime=now.timestamp()-100)
    quota = read_codex_quota(tmp_path, now=now.timestamp())
    assert quota["observed_at"] == recent.isoformat().replace("+00:00", "Z")
    assert quota["windows"][0]["used_percent"] == 99.0


def test_more_than_twelve_files_do_not_hide_recent_window(tmp_path):
    now = datetime.now(timezone.utc)
    for n in range(17):
        create_session(tmp_path, f"older-{n}", [evt(now-timedelta(hours=4), 30.0)],
                       mtime=now.timestamp()-n)
    recent = now - timedelta(minutes=2)
    create_session(tmp_path, "best-valid-window",
                   [evt(recent, 97.0)], mtime=now.timestamp()-50)
    quota = read_codex_quota(tmp_path, now=now.timestamp())
    assert quota["windows"][0]["used_percent"] == 97.0


def test_missing_or_plan_only_windows_cannot_be_called_confirmed_quota(tmp_path):
    now = datetime.now(timezone.utc)
    create_session(tmp_path, "account", [evt(now-timedelta(minutes=3))])
    for fn in (read_codex_quota, codex_quota):
        result = fn(tmp_path, now=now.timestamp())
        assert result["state"] == "UNKNOWN" or not result.get("windows")
        assert not result.get("windows")


def test_future_account_event_is_not_current_read_only_snapshot(tmp_path):
    now = datetime.now(timezone.utc)
    actual = now - timedelta(minutes=1)
    create_session(tmp_path, "account", [evt(actual, 85.0), evt(now+timedelta(hours=2), 0.0)])
    quota = read_codex_quota(tmp_path, now=now.timestamp())
    assert quota["windows"][0]["used_percent"] == 85.0