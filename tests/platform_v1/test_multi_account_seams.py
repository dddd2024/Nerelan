"""Regression tests for the production dispatch seams (flag-gated, zero-risk-off).

These verify that the multi-account brain is wired into the dispatch path
(goal_service orchestration-mode decision and functional_validation outcome
recording) WITHOUT changing behaviour when ``REVERSE_AGENT_MULTI_ACCOUNT_ENABLED``
is off, and only overriding the legacy default with *measured* evidence.
"""
import os
from unittest import mock

import pytest

import reverse_agent.platform_v1.functional_validation as functional_validation_module
import reverse_agent.platform_v1.goal_service as goal_service_module
from reverse_agent.platform_v1.goal_service import _resolve_orchestration_mode
from reverse_agent.platform_v1.multi_account import dispatch as ma_dispatch
from reverse_agent.platform_v1.multi_account.status import (
    AccountHealth, AccountStatus, WindowStatus,
)

_FLAG = "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED"


def _status(account_ref, health, *, windows=None):
    return AccountStatus(
        account_ref=account_ref, health=health, windows=windows or [],
        raw={"account_ref": account_ref})


# --- Seam C: goal_service guard integration (extracted helper) ----------------
class _FakeGS:
    def __init__(self, provider=None, resolver=None):
        self.account_status_provider = provider
        self.binding_account_resolver = resolver


def _exhausted_provider():
    return [_status("acc-bad", AccountHealth.EXHAUSTED)]


def _healthy_provider():
    return [_status("acc-ok", AccountHealth.HEALTHY)]


def _resolver(binding_ref):
    return "acc-bad" if binding_ref == "b-bad" else ("acc-ok" if binding_ref == "b-ok" else None)


def test_reroute_guard_skip_off_when_flag_unset(monkeypatch):
    monkeypatch.delenv(_FLAG, raising=False)
    gs = _FakeGS(provider=_exhausted_provider, resolver=_resolver)
    assert _resolve_orchestration_mode  # noqa: B018 - import sanity
    assert goal_service_module._reroute_guard_skip(gs, {"binding_ref": "b-bad"}) == (False, None)


def test_reroute_guard_skip_requires_providers(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    assert goal_service_module._reroute_guard_skip(_FakeGS(provider=None, resolver=_resolver),
                                                  {"binding_ref": "b-bad"}) == (False, None)
    assert goal_service_module._reroute_guard_skip(_FakeGS(provider=_exhausted_provider, resolver=None),
                                                  {"binding_ref": "b-bad"}) == (False, None)


def test_reroute_guard_skip_exhausted_candidate(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    gs = _FakeGS(provider=_exhausted_provider, resolver=_resolver)
    assert goal_service_module._reroute_guard_skip(gs, {"binding_ref": "b-bad"}) == (True, "acc-bad")


def test_reroute_guard_skip_healthy_candidate(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    gs = _FakeGS(provider=_healthy_provider, resolver=_resolver)
    assert goal_service_module._reroute_guard_skip(gs, {"binding_ref": "b-ok"}) == (False, "acc-ok")


def test_reroute_guard_skip_unmappable_binding(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    gs = _FakeGS(provider=_exhausted_provider, resolver=_resolver)
    # "b-unknown" resolves to None -> must not skip (legacy reroute proceeds).
    assert goal_service_module._reroute_guard_skip(gs, {"binding_ref": "b-unknown"}) == (False, None)


def test_reroute_guard_skip_provider_failure_is_safe(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")

    def boom():
        raise RuntimeError("perception down")

    gs = _FakeGS(provider=boom, resolver=_resolver)
    assert goal_service_module._reroute_guard_skip(gs, {"binding_ref": "b-bad"}) == (False, None)


# --- Seam C: account-aware reroute guard -------------------------------------
def test_reroute_guard_skips_exhausted_and_abnormal():
    statuses = [_status("acc-a", AccountHealth.EXHAUSTED), _status("acc-b", AccountHealth.ABNORMAL)]
    assert ma_dispatch.reroute_guard(statuses, "acc-a")["skip"] is True
    assert ma_dispatch.reroute_guard(statuses, "acc-b")["skip"] is True


def test_reroute_guard_allows_healthy_degraded_stale_unknown():
    statuses = [
        _status("h", AccountHealth.HEALTHY),
        _status("d", AccountHealth.DEGRADED),
        _status("s", AccountHealth.STALE),
        _status("u", AccountHealth.UNKNOWN),
    ]
    for ref in ("h", "d", "s", "u"):
        assert ma_dispatch.reroute_guard(statuses, ref)["skip"] is False


def test_reroute_guard_allows_unknown_account():
    assert ma_dispatch.reroute_guard([_status("x", AccountHealth.HEALTHY)], "other")["skip"] is False
    assert ma_dispatch.reroute_guard([], "x")["skip"] is False


def test_reroute_guard_never_raises():
    # A non-iterable / malformed input must degrade to "do not block reroute".
    assert ma_dispatch.reroute_guard(None, "x")["skip"] is False
    assert ma_dispatch.reroute_guard("not-a-list", "x")["skip"] is False



# --- Seam A: goal-level orchestration mode ------------------------------------
def test_resolve_mode_default_without_flag(monkeypatch):
    monkeypatch.delenv(_FLAG, raising=False)
    assert _resolve_orchestration_mode({}) == "sequential_team"


def test_resolve_mode_explicit_pin_always_wins(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    assert _resolve_orchestration_mode({"orchestration_mode": "agent_team"}) == "agent_team"
    assert _resolve_orchestration_mode({"orchestration_mode": "single"}) == "single"


def test_resolve_mode_flag_on_ignores_default_ladder(monkeypatch):
    # No measured evidence -> selector returns the default ladder branch, which
    # we deliberately ignore so the legacy "sequential_team" default is kept.
    monkeypatch.setenv(_FLAG, "1")
    with mock.patch.object(ma_dispatch, "recommend_orchestration_mode",
                           return_value={"mode": "agent_team",
                                         "reason": "default_multi_task_no_evidence"}):
        assert _resolve_orchestration_mode({}) == "sequential_team"


def test_resolve_mode_flag_on_applies_measured_evidence(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    with mock.patch.object(ma_dispatch, "recommend_orchestration_mode",
                           return_value={"mode": "single", "reason": "measured_break_even"}):
        assert _resolve_orchestration_mode({}) == "single"
    with mock.patch.object(ma_dispatch, "recommend_orchestration_mode",
                           return_value={"mode": "agent_team", "reason": "measured_break_even"}):
        assert _resolve_orchestration_mode({}) == "agent_team"


def test_resolve_mode_brain_failure_keeps_legacy(monkeypatch):
    monkeypatch.setenv(_FLAG, "1")
    with mock.patch.object(ma_dispatch, "recommend_orchestration_mode",
                           side_effect=RuntimeError("brain down")):
        assert _resolve_orchestration_mode({}) == "sequential_team"


# --- Seam B: functional-validation outcome recording -------------------------
def _write_passing_junit(path):
    path.write_text(
        '<?xml version="1.0"?><testsuite name="x" tests="1" failures="0">'
        '<testcase classname="C" name="t"/></testsuite>', encoding="utf-8")


def test_test_report_records_outcome_when_flag_on(monkeypatch, tmp_path):
    monkeypatch.setenv(_FLAG, "1")
    captured = {}

    def fake_record(outcome, *, store_path=None):
        captured.update(outcome)
        return {}

    with mock.patch.object(ma_dispatch, "record_goal_outcome", side_effect=fake_record):
        report = tmp_path / "r.xml"
        _write_passing_junit(report)
        result = functional_validation_module._test_report("junit", report, b"")
    assert result["accepted"] is True
    assert captured.get("accepted") is True
    assert captured.get("mode") is None


def test_test_report_no_record_when_flag_off(monkeypatch, tmp_path):
    monkeypatch.delenv(_FLAG, raising=False)
    called = {"n": 0}

    def fake_record(outcome, *, store_path=None):
        called["n"] += 1
        return {}

    with mock.patch.object(ma_dispatch, "record_goal_outcome", side_effect=fake_record):
        report = tmp_path / "r.xml"
        _write_passing_junit(report)
        functional_validation_module._test_report("junit", report, b"")
    assert called["n"] == 0
