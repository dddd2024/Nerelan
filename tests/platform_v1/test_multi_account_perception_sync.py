"""Perception sync: Magpie snapshot to quota observation rows.

Pure-function tests: no network, no filesystem, deterministic clock.
"""
from __future__ import annotations

from typing import Any

from reverse_agent.platform_v1.multi_account.perception_sync import (
    EVIDENCE_KEYS,
    observations_from_snapshot,
    sync_snapshot,
)

NOW = 1_700_000_000.0  # 2023-11-14T22:13:20Z


def account(ref: str = "c38efd6a74a2", **overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "provider": "codex",
        "kind": "subscription",
        "plan": None,
        "account_ref": ref,
        "windows": [{"name": "5 hours", "used_percent": 0.0, "remaining_percent": 100.0,
                     "resets_at": "2026-11-05T18:50:01+00:00", "unlimited": False}],
        "cached_windows": [],
        "state": "FRESH",
        "reason": None,
        "observed_at": "2026-11-05T13:50:39+00:00",
        "provenance": "EXTERNAL_MAGPIE",
        "source_version": "0.1.2945",
    }
    entry.update(overrides)
    return entry


def snapshot(*accounts: Any) -> dict[str, Any]:
    return {"status": "available", "version": "0.1.2945", "models": [],
            "accounts": list(accounts), "reason": None}


class Recorder:
    """Collects writes; raises for any account_ref listed in ``fail_on``."""

    def __init__(self, fail_on: tuple[str, ...] = ()) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.fail_on = set(fail_on)

    def __call__(self, account_ref: str, observed_at: str, payload: str) -> None:
        if account_ref in self.fail_on:
            raise RuntimeError("disk full at /secret/path")
        self.calls.append((account_ref, observed_at, payload))


def test_fresh_account_keeps_allowed_keys_and_drops_personal_fields() -> None:
    entry = account(user="a@b.c")
    rows = observations_from_snapshot(snapshot(entry), now=NOW)

    assert len(rows) == 1
    row = rows[0]
    assert row["account_ref"] == "c38efd6a74a2"
    assert row["state"] == "FRESH"
    assert row["observed_at"] == "2026-11-05T13:50:39+00:00"
    assert row["evidence"] == {key: entry[key] for key in EVIDENCE_KEYS}
    assert "user" not in row["evidence"]

    recorder = Recorder()
    summary = sync_snapshot(snapshot(entry), write=recorder, now=NOW)
    assert summary["written"] == 1
    assert "a@b.c" not in recorder.calls[0][2]


def test_evidence_is_a_deep_copy() -> None:
    entry = account()
    row = observations_from_snapshot(snapshot(entry), now=NOW)[0]
    entry["windows"][0]["used_percent"] = 99.0
    assert row["evidence"]["windows"][0]["used_percent"] == 0.0


def test_unknown_account_is_kept_and_counted_in_states() -> None:
    rows = observations_from_snapshot(
        snapshot(account("aaaa", state="UNKNOWN"), account("bbbb", state="FRESH"),
                 account("cccc", state=None)),
        now=NOW,
    )
    assert [row["state"] for row in rows] == ["UNKNOWN", "FRESH", "UNKNOWN"]

    recorder = Recorder()
    summary = sync_snapshot(snapshot(account("aaaa", state="UNKNOWN"),
                                     account("bbbb", state="FRESH")),
                            write=recorder, now=NOW)
    assert summary["states"] == {"FRESH": 1, "UNKNOWN": 1}
    assert summary["written"] == 2


def test_entry_without_account_ref_is_skipped_and_never_written() -> None:
    missing = account()
    del missing["account_ref"]
    empty = account(account_ref="")
    snap = snapshot(missing, empty, account("keep01"))

    assert [row["account_ref"] for row in observations_from_snapshot(snap, now=NOW)] == ["keep01"]

    recorder = Recorder()
    summary = sync_snapshot(snap, write=recorder, now=NOW)
    assert summary["skipped"] == 2
    assert summary["written"] == 1
    assert [call[0] for call in recorder.calls] == ["keep01"]


def test_malformed_inputs_return_no_rows_and_raise_nothing() -> None:
    bad_snapshots: list[Any] = [
        None,
        "not a mapping",
        42,
        ["accounts"],
        {"accounts": "nope"},
        {"accounts": None},
        {},
        {"accounts": [None, 42, "text", ["list"]]},
    ]
    for bad in bad_snapshots:
        assert observations_from_snapshot(bad, now=NOW) == []

    recorder = Recorder()
    summary = sync_snapshot({"accounts": [None, 42]}, write=recorder, now=NOW)
    assert summary["skipped"] == 2
    assert summary["written"] == 0
    assert recorder.calls == []

    summary = sync_snapshot("garbage", write=recorder, now=NOW)  # type: ignore[arg-type]
    assert summary["written"] == 0
    assert summary["skipped"] == 0


def test_failing_write_is_counted_and_later_rows_still_written() -> None:
    recorder = Recorder(fail_on=("aaaa",))
    summary = sync_snapshot(snapshot(account("aaaa"), account("bbbb"), account("cccc")),
                            write=recorder, now=NOW)

    assert summary["failed"] == 1
    assert summary["failures"] == ["RuntimeError"]
    assert summary["written"] == 2
    assert [call[0] for call in recorder.calls] == ["bbbb", "cccc"]
    # Only the exception type name is reported, never its message.
    assert "secret" not in repr(summary)


def test_missing_observed_at_falls_back_to_iso_utc_from_now() -> None:
    entry = account("nots01")
    del entry["observed_at"]

    row = observations_from_snapshot(snapshot(entry), now=NOW)[0]
    assert row["observed_at"] == "2023-11-14T22:13:20Z"
    assert row["observed_at"].endswith("Z")
    assert "observed_at" not in row["evidence"]

    recorder = Recorder()
    sync_snapshot(snapshot(entry), write=recorder, now=0.0)
    assert recorder.calls[0][1] == "1970-01-01T00:00:00Z"


def test_rows_are_sorted_by_account_ref() -> None:
    rows = observations_from_snapshot(
        snapshot(account("mmmm"), account("aaaa"), account("zzzz"), account("bbbb")),
        now=NOW,
    )
    assert [row["account_ref"] for row in rows] == ["aaaa", "bbbb", "mmmm", "zzzz"]


def test_oldest_and_newest_are_min_and_max_of_rows() -> None:
    recorder = Recorder()
    summary = sync_snapshot(
        snapshot(account("aaaa", observed_at="2026-11-05T13:50:39Z"),
                 account("bbbb", observed_at="2026-11-04T09:00:00Z"),
                 account("cccc", observed_at="2026-11-05T20:00:00Z")),
        write=recorder, now=NOW,
    )
    assert summary["oldest_observed_at"] == "2026-11-04T09:00:00Z"
    assert summary["newest_observed_at"] == "2026-11-05T20:00:00Z"


def test_oldest_and_newest_are_none_without_rows() -> None:
    recorder = Recorder()
    summary = sync_snapshot(snapshot(), write=recorder, now=NOW)
    assert summary["oldest_observed_at"] is None
    assert summary["newest_observed_at"] is None
    assert summary["written"] == 0
    assert summary["failures"] == []
