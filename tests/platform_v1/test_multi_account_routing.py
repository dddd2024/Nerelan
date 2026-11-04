"""Who owns account routing, and what changes when Magpie owns it.

The Owner decision of 2026-11-04 keeps Nerelan's account selection as the
default and lets Magpie take over only with an explicit acknowledgement that its
switching behaviour was verified. These tests pin that boundary so a reachable
port alone can never silently move the decision upstream.
"""
from __future__ import annotations

import pytest

from reverse_agent.platform_v1.multi_account import dispatch
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.routing import (
    resolve_account_routing, routing_view,
)
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus


def test_explicit_local_and_magpie_are_honoured():
    assert resolve_account_routing("local", env={}) == "local"
    assert resolve_account_routing("MAGPIE", env={}) == "magpie"


def test_auto_needs_both_enablement_and_an_acknowledgement():
    assert resolve_account_routing("auto", env={}) == "local"
    assert resolve_account_routing("auto", env={"REVERSE_AGENT_MAGPIE": "1"}) == "local"
    assert resolve_account_routing(
        "auto", env={"REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING": "1"}) == "local"
    assert resolve_account_routing("auto", env={
        "REVERSE_AGENT_MAGPIE": "1",
        "REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING": "1",
    }) == "magpie"


def test_unknown_value_falls_back_to_local():
    for value in ("", None, "magpie-please", 42):
        assert resolve_account_routing(value, env={}) == "local"


def test_view_explains_why_auto_did_not_delegate():
    view = routing_view("auto", env={"REVERSE_AGENT_MAGPIE": "1"})
    assert view == {"requested": "auto", "owner": "local",
                    "reason": "auto_requires_verified_switching",
                    "magpie_enabled": True, "switching_acknowledged": False}


def test_config_reads_the_switch_from_the_environment(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_ACCOUNT_ROUTING", raising=False)
    assert MultiAccountConfig().account_routing == "local"
    monkeypatch.setenv("REVERSE_AGENT_ACCOUNT_ROUTING", "magpie")
    assert MultiAccountConfig.from_env().account_routing == "magpie"
    with pytest.raises(ValueError):
        MultiAccountConfig(account_routing="both")


def _account(ref: str, health: AccountHealth) -> AccountStatus:
    return AccountStatus(account_ref=ref, provider="codex", health=health)


@pytest.fixture
def brain_at(monkeypatch):
    def build(routing: str) -> None:
        dispatch.reset_orchestrator()
        monkeypatch.setenv("REVERSE_AGENT_ACCOUNT_ROUTING", routing)
        monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
        dispatch.get_orchestrator(store_path=None)
    yield build
    dispatch.reset_orchestrator()


def test_local_routing_still_blocks_an_exhausted_candidate(brain_at):
    brain_at("local")
    assert dispatch.account_routing()["owner"] == "local"
    verdict = dispatch.reroute_guard([_account("a", AccountHealth.EXHAUSTED)], "a")
    assert verdict == {"skip": True, "health": "EXHAUSTED", "reason": "account_unfit"}


def test_magpie_routing_stops_duplicating_the_account_verdict(brain_at):
    brain_at("magpie")
    assert dispatch.account_routing()["owner"] == "magpie"
    verdict = dispatch.reroute_guard([_account("a", AccountHealth.EXHAUSTED)], "a")
    # Magpie owns switching, so a local EXHAUSTED verdict must not veto a reroute.
    assert verdict == {"skip": False, "health": None, "reason": "routing_delegated_to_magpie"}


def test_magpie_routing_disables_the_local_idle_hint(brain_at):
    brain_at("magpie")
    assert dispatch.idle_wait_seconds() is None
    dispatch.reset_orchestrator()

    brain_at("local")
    brain = dispatch.get_orchestrator(store_path=None)
    brain.cooldowns.record_failure("a", "task_failed", now=brain._clock())
    assert dispatch.idle_wait_seconds() is not None


def test_guard_without_a_brain_stays_permissive():
    dispatch.reset_orchestrator()
    verdict = dispatch.reroute_guard([_account("a", AccountHealth.EXHAUSTED)], "a")
    assert verdict["skip"] is True  # default owner is local, so behaviour is unchanged
    dispatch.reset_orchestrator()
