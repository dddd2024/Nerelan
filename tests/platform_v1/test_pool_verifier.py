"""Background verification of unproven models (Owner decision 2026-11-11). All probes are fakes."""
import json
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.model_availability import AvailabilityCache
from reverse_agent.platform_v1.pool_verifier import PoolVerifier
from reverse_agent.platform_v1.routing_inputs import read_overrides


def _binding(binding_id, model, connection="gateway", executor="opencode", enabled=True):
    return {"binding_id": binding_id, "model_id": model, "connection_id": connection,
            "executor_id": executor, "enabled": enabled, "native_endpoint": "/chat/completions"}


class _Host:
    def __init__(self, tmp_path, bindings, *, window=True, window_allows=True, paid=False, overrides=None):
        state = tmp_path / "model_setup_state.json"
        state.write_text("{}", encoding="utf-8")
        if overrides is not None:
            (tmp_path / "model_routing_overrides.json").write_text(json.dumps(overrides), encoding="utf-8")
        connections = [
            {"connection_id": "gateway", "auth_method": "none", "enabled": True},
            {"connection_id": "paid", "auth_method": "api_key", "enabled": True},
            {"connection_id": "native", "auth_method": "external_cli_session", "enabled": True},
            {"connection_id": "off", "auth_method": "none", "enabled": False},
        ]
        self._store = SimpleNamespace(_state_path=state, list_bindings_public=lambda: bindings,
                                      list_connections_public=lambda: connections)
        self._control_store = SimpleNamespace(
            active_window=lambda: SimpleNamespace(id="owner-1") if window else None)
        self._availability_cache = AvailabilityCache()
        self.probed = []
        self.answers = {}
        self._window_allows, self._paid = window_allows, paid
        self._bindings = bindings

    def _availability_probe(self, binding):
        self.probed.append(binding["binding_id"])
        return self.answers.get(binding["binding_id"], {"ok": True})

    def _probe_routing_binding(self, binding):  # pragma: no cover - the fake seam always wins
        pytest.fail("a real probe must not run in tests")

    def _routing_probe_window_allowed(self, goal):
        return self._window_allows and goal.window_id == "owner-1"

    def _routing_paid_allowed(self, goal, owner):
        return self._paid

    def _runnable_bindings(self):
        return {b["binding_id"] for b in self._bindings if b["binding_id"] != "not-runnable"}

    def _usage_profiles(self):
        return {}

    def _routing_availability_history(self):
        return {}

    def _routing_availability(self, binding, connection, **kwargs):
        assert kwargs["probe_allowed"] is False
        return self._availability_cache.check(binding, connection)


_OVERRIDES = {"models": {"free/a": {"cost_class": "free"}, "free/b": {"cost_class": "free"},
                         "sub/c": {"cost_class": "subscription"}},
              "connections": {"paid": {"cost_class": "paid_api"}}}


def test_one_check_per_call_cheapest_first_and_results_are_remembered(tmp_path):
    bindings = [_binding("c-sub", "sub/c"), _binding("b-free", "free/b"), _binding("a-free", "free/a")]
    host = _Host(tmp_path, bindings, overrides=_OVERRIDES)
    host.answers["a-free"] = {"ok": False, "error": "not allowed for user type"}
    verifier = PoolVerifier(host)

    assert verifier.verify_once() == "a-free"
    # The shared one-per-minute limit holds the next check.
    assert verifier.verify_once() is None
    assert host.probed == ["a-free"]
    connection = {"connection_id": "gateway", "auth_method": "none", "enabled": True}
    assert host._availability_cache.check(bindings[2], connection)["state"] == "UNAVAILABLE"

    host._availability_cache.next_probe = 0
    assert verifier.verify_once() == "b-free"
    host._availability_cache.next_probe = 0
    assert verifier.verify_once() == "c-sub"
    host._availability_cache.next_probe = 0
    assert verifier.verify_once() is None  # everything is known now
    assert host.probed == ["a-free", "b-free", "c-sub"]


@pytest.mark.parametrize("kwargs", [{"window": False}, {"window_allows": False},
                                    {"overrides": {**_OVERRIDES, "availability_probes": False}}])
def test_no_check_without_a_permitting_window_or_when_switched_off(tmp_path, kwargs):
    host = _Host(tmp_path, [_binding("a-free", "free/a")], **{"overrides": _OVERRIDES, **kwargs})
    assert PoolVerifier(host).verify_once() is None
    assert host.probed == []


def test_environment_switch_and_broken_settings_turn_it_off(tmp_path, monkeypatch):
    host = _Host(tmp_path, [_binding("a-free", "free/a")], overrides=_OVERRIDES)
    monkeypatch.setenv("REVERSE_AGENT_ROUTING_PROBES", "0")
    assert PoolVerifier(host).verify_once() is None
    monkeypatch.delenv("REVERSE_AGENT_ROUTING_PROBES")
    (tmp_path / "model_routing_overrides.json").write_text("{not json", encoding="utf-8")
    assert PoolVerifier(host).verify_once() is None
    assert host.probed == []


def test_native_accounts_paid_apis_and_unusable_bindings_are_never_checked(tmp_path):
    bindings = [
        _binding("native", "gpt", connection="native", executor="codex"),
        _binding("gateway-claude", "claude/sonnet"),
        _binding("paid", "vendor/model", connection="paid"),
        _binding("disabled", "free/a", enabled=False),
        _binding("off-connection", "free/a", connection="off"),
        _binding("not-runnable", "free/a"),
        _binding("excluded", "free/b"),
    ]
    overrides = {**_OVERRIDES, "bindings": {"excluded": {"exclude": True}}}
    host = _Host(tmp_path, bindings, overrides=overrides)
    assert PoolVerifier(host).verify_once() is None
    assert host.probed == []
    # A window that allows paid use lets the paid API binding be checked.
    host._paid = True
    assert PoolVerifier(host).verify_once() == "paid"


def test_settings_reject_a_non_boolean_switch(tmp_path):
    state = tmp_path / "model_setup_state.json"
    (tmp_path / "model_routing_overrides.json").write_text('{"availability_probes": "yes"}', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
        read_overrides(state)


def test_the_thread_waits_one_interval_before_its_first_check(tmp_path):
    host = _Host(tmp_path, [_binding("a-free", "free/a")], overrides=_OVERRIDES)
    verifier = PoolVerifier(host, poll_seconds=3600)
    verifier.start()
    verifier.stop()
    assert host.probed == []


def test_a_binding_that_keeps_failing_is_tried_once_and_does_not_hold_up_the_rest(tmp_path):
    """Review of #1447: a 429 expires from the cache after five minutes and must not be re-probed."""
    bindings = [_binding(f"free-{i}", "free/a" if i < 3 else "free/b") for i in range(6)]
    host = _Host(tmp_path, bindings, overrides=_OVERRIDES)
    for i in range(3):
        host.answers[f"free-{i}"] = {"ok": False, "error": "429 rate limit"}
    # The real cache rule: the availability reading comes from the cache at the simulated time.
    clock = {"now": 1_000_000.0}
    host._routing_availability = lambda binding, connection, **kw: host._availability_cache.check(
        binding, connection, now=clock["now"])
    verifier = PoolVerifier(host)
    for _ in range(180):  # three hours of one-minute polls
        verifier.verify_once(now=clock["now"])
        clock["now"] += 60
    assert sorted(host.probed) == [f"free-{i}" for i in range(6)]
    # After a day a still-unknown binding may be tried again.
    clock["now"] += 86400
    assert verifier.verify_once(now=clock["now"]) in {"free-0", "free-1", "free-2"}


def test_an_unreadable_cache_entry_is_not_returned_forever(tmp_path):
    bindings = [_binding("a-free", "free/a"), _binding("b-free", "free/b")]
    host = _Host(tmp_path, bindings, overrides=_OVERRIDES)
    connection = {"connection_id": "gateway", "auth_method": "none", "enabled": True}
    # A reading dated in the future (clock stepped back) is reported as unknown and cannot be probed.
    host._availability_cache.remember(bindings[0], connection, {"state": "AVAILABLE", "reason": "verified_request",
                                                               "observed_at": 9e12, "expires_at": 9e12 + 1})
    verifier = PoolVerifier(host)
    assert verifier.verify_once() == "a-free" and host.probed == []
    host._availability_cache.next_probe = 0
    assert verifier.verify_once() == "b-free" and host.probed == ["b-free"]
