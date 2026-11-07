"""The real-account probe must fail *informatively*, not silently.

A probe that records only ``returncode:1`` cannot feed the cooldown registry or
the evolution loop: both need a failure *kind*. These tests pin the classifier,
the redaction of CLI diagnostics, and the retry rule that decides whether one
more real call is justified.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "multi_account_real_acceptance.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("real_acceptance_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("text, expected", [
    ("Error: invalid api key provided", "account_abnormal"),
    ("authentication_error: token revolved", "account_abnormal"),
    ("Your credit balance is too low to continue", "account_abnormal"),
    ("API Error: 401 unauthorized", "account_abnormal"),
    ("Rate limit reached for this account", "quota_exhausted"),
    ("usage limit exceeded, try again in 4h", "quota_exhausted"),
    ("HTTP 429 too many requests", "quota_exhausted"),
    ("read ECONNRESET", "transient"),
    ("503 Service Unavailable", "transient"),
    ("socket hang up", "transient"),
    ("Traceback (most recent call last): KeyError: 'x'", "task_failed"),
    ("", "task_failed"),
    (None, "task_failed"),
])
def test_classify_failure_matches_the_production_vocabulary(probe, text, expected):
    assert probe.classify_failure(text) == expected


def test_account_failure_outranks_a_quota_mention(probe):
    """Both signals present: the account itself is the problem, so isolate it."""
    text = "401 unauthorized: your key is invalid (quota check skipped)"
    assert probe.classify_failure(text) == "account_abnormal"


@pytest.mark.parametrize("result, retryable", [
    ({"ok": True, "error": None, "failure_kind": None}, False),
    ({"ok": False, "error": "timeout", "failure_kind": "transient"}, True),
    ({"ok": False, "error": "TimeoutExpired", "failure_kind": "transient"}, True),
    ({"ok": False, "error": "returncode:1", "failure_kind": "transient"}, True),
    ({"ok": False, "error": "returncode:1", "failure_kind": "account_abnormal"}, False),
    ({"ok": False, "error": "returncode:1", "failure_kind": "quota_exhausted"}, False),
    ({"ok": False, "error": "returncode:1", "failure_kind": "task_failed"}, False),
])
def test_only_transport_failures_earn_a_second_real_call(probe, result, retryable):
    assert probe.is_retryable(result) is retryable


def test_redaction_drops_tokens_keys_and_home_paths(probe):
    raw = ("failed with key sk-abcdefghijklmnopqrstuvwxyz0123456789 "
           "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456 "
           r"at C:\Users\wjc27\Temp\realprobe-claude-code-abc\run.log")
    cleaned = probe.redact(raw)
    assert "sk-abcdefghijklmnopqrstuvwxyz0123456789" not in cleaned
    assert "abcdefghijklmnopqrstuvwxyz123456" not in cleaned
    assert "wjc27" not in cleaned
    assert "<redacted>" in cleaned


def test_redaction_is_bounded_and_survives_empty_input(probe):
    assert probe.redact("") == ""
    assert probe.redact(None) == ""
    assert len(probe.redact("x" * 5000, limit=120)) <= 120


def test_redaction_keeps_the_part_of_the_message_that_explains_it(probe):
    """The tail is what carries the reason, so it must survive, just clipped."""
    cleaned = probe.redact("boilerplate " * 40 + "FATAL: rate limit reached", limit=60)
    assert "rate limit reached" in cleaned


@pytest.mark.parametrize("kind, expected_attempts", [
    ("transient", 2),
    ("account_abnormal", 1),
    ("quota_exhausted", 1),
    ("task_failed", 1),
])
def test_probe_cli_spends_at_most_one_extra_call(probe, monkeypatch, kind, expected_attempts):
    """A locked account is not retried: rerouting is the answer, not a second call."""
    calls = []

    def fake_probe(name, argv, *, timeout):
        calls.append(name)
        return {"account": name, "ok": False, "seconds": 0.1, "cost_units": None,
                "priced": False, "tokens": None, "error": "returncode:1",
                "failure_kind": kind, "diagnostic": "boom"}

    monkeypatch.setattr(probe, "_probe_once", fake_probe)
    result = probe.probe_cli("claude-code", ["claude"], timeout=1.0)
    assert result["attempts"] == expected_attempts
    assert len(calls) == expected_attempts
    assert result["failure_kind"] == kind


def test_probe_cli_stops_after_the_first_success(probe, monkeypatch):
    calls = []

    def fake_probe(name, argv, *, timeout):
        calls.append(name)
        return {"account": name, "ok": True, "seconds": 0.2, "cost_units": 0.001,
                "priced": True, "tokens": None, "error": None,
                "failure_kind": None, "diagnostic": ""}

    monkeypatch.setattr(probe, "_probe_once", fake_probe)
    result = probe.probe_cli("claude-code", ["claude"], timeout=1.0)
    assert result["ok"] is True
    assert result["attempts"] == 1
    assert len(calls) == 1


# --- the alert expectation must be proportional to the real pool -------------

def _statuses(probe, *healths):
    from reverse_agent.platform_v1.multi_account.status import AccountStatus
    return [AccountStatus(account_ref=f"acc{i}", provider=f"p{i}", health=health)
            for i, health in enumerate(healths)]


def test_healthy_pool_must_not_page(probe):
    """A fully healthy pool that alerts trains operators to ignore alerts."""
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, AccountHealth.HEALTHY, AccountHealth.HEALTHY, AccountHealth.HEALTHY)
    assert probe.expected_alert_codes(pool) == set()


def test_an_unobservable_share_of_the_pool_is_an_incident(probe):
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, AccountHealth.HEALTHY, AccountHealth.HEALTHY,
                     AccountHealth.UNKNOWN, AccountHealth.STALE)
    assert probe.expected_alert_codes(pool) == {"perception_partial"}


def test_a_small_minority_of_unobserved_accounts_is_not_an_incident(probe):
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, *([AccountHealth.HEALTHY] * 10 + [AccountHealth.UNKNOWN]))
    assert probe.expected_alert_codes(pool) == set()


def test_pool_wide_verdict_replaces_per_account_notices(probe):
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, AccountHealth.ABNORMAL, AccountHealth.ABNORMAL)
    assert probe.expected_alert_codes(pool) == {"all_accounts_abnormal"}


def test_exhausted_everywhere_is_reported_once_for_the_pool(probe):
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, AccountHealth.EXHAUSTED, AccountHealth.STALE)
    assert probe.expected_alert_codes(pool) == {"all_accounts_exhausted"}


def test_a_mixed_pool_reports_the_account_that_is_actually_broken(probe):
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    pool = _statuses(probe, AccountHealth.HEALTHY, AccountHealth.ABNORMAL,
                     AccountHealth.EXHAUSTED)
    assert probe.expected_alert_codes(pool) == {"account_abnormal", "account_exhausted"}


def test_an_empty_pool_is_an_error_not_silence(probe):
    assert probe.expected_alert_codes([]) == {"no_accounts_observed"}


def test_the_expectation_agrees_with_the_real_engine(probe):
    """The independent expectation and the shipped rules must not drift apart.

    This is the point of writing the oracle out by hand: if a rule changes
    without the contract changing, this test fails instead of the acceptance
    silently accepting the new behaviour.
    """
    from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator
    from reverse_agent.platform_v1.multi_account.status import AccountHealth
    cases = [
        (AccountHealth.HEALTHY, AccountHealth.HEALTHY),
        (AccountHealth.HEALTHY, AccountHealth.UNKNOWN),
        (AccountHealth.HEALTHY, AccountHealth.UNKNOWN, AccountHealth.STALE),
        (AccountHealth.HEALTHY, AccountHealth.ABNORMAL, AccountHealth.EXHAUSTED),
        (AccountHealth.ABNORMAL, AccountHealth.ABNORMAL),
        (AccountHealth.EXHAUSTED, AccountHealth.STALE),
        (AccountHealth.STALE, AccountHealth.STALE),
    ]
    for healths in cases:
        pool = _statuses(probe, *healths)
        bot = MultiAccountOrchestrator(MultiAccountConfig())
        actual = {a["code"] for a in bot.observe({"accounts": []})["alerts"]}
        assert actual, "an empty snapshot must not be silent"
        engine = {alert.code for alert in bot.alerts.evaluate(statuses=pool)}
        assert engine == probe.expected_alert_codes(pool), healths


# --- committed evidence must not carry host line endings ---------------------

def test_written_evidence_is_lf_only(probe, tmp_path):
    """CRLF evidence fails CI: every line then reads as trailing whitespace.

    The simulation script already pinned this; the real-account writer did not,
    and the first live evidence file failed the exact-range hygiene gate on
    Windows. Byte-for-byte reproducibility across hosts is the requirement, not
    a nicety.
    """
    payload = {"generated_at": "2026-11-07T00:00:00+00:00", "started_at": None,
               "live": False, "magpie": {"version": "x", "accounts": 1,
                                          "providers": ["claude"]},
               "real_30d": {key: None for key in ("period", "calls", "errors", "retried",
                                                  "cost", "unpriced", "credits", "ttft_ms",
                                                  "decode_out", "decode_n")},
               "checks": [{"key": "k", "title": "标题", "ok": True,
                           "detail": {"a": 1}, "note": ""}],
               "probes": [], "result": {"passed": 1, "total": 1, "ok": True},
               "total_probe_cost_usd": 0.0}

    class Args:
        out_dir = str(tmp_path)

    probe.write_reports(payload, Args)
    written = list(tmp_path.iterdir())
    assert written
    for path in written:
        raw = path.read_bytes()
        assert b"\r\n" not in raw, f"{path.name} was written with host line endings"
        if path.suffix == ".md":
            assert raw.endswith(b"\n")
