"""Paid subscriptions never go through a gateway (Owner decision 2026-11-23, #1743). Provider-free."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import model_review_transport, owner_window, subscription_gateway as gate
from reverse_agent.platform_v1.binding_resolver import BindingResolutionError, BindingResolver
from reverse_agent.platform_v1.goal_service import PlannedTask
from reverse_agent.platform_v1.model_profiles import neutral_failure
from reverse_agent.platform_v1.model_router import ModelSelectionError, select_model
from reverse_agent.platform_v1.pool_verifier import PoolVerifier  # noqa: F401 - import proves no cycle
from reverse_agent.platform_v1.routing_inputs import read_overrides
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

MAGPIE = {"auth_method": "none", "base_url": "http://127.0.0.1:3425/v1", "executor_provider_id": "openai-compatible"}
PUBLIC_KEY = {"auth_method": "api_key", "base_url": "https://api.openai.com/v1", "executor_provider_id": "openai"}
CODEX = {"auth_method": "external_cli_session", "base_url": "https://chatgpt.com", "executor_provider_id": "codex"}
CLAUDE = {"auth_method": "external_cli_session", "base_url": "https://claude.ai", "executor_provider_id": "claude-code"}
MIXED = ["codex/gpt-6-sol", "workbuddy-ai/gpt-6-sol"]
CLEAN = ["workbuddy-ai/gpt-6-sol", "copilot/gpt-6-sol"]


def cause(model, connection=MAGPIE, executor="opencode", **owner):
    return gate.block_cause(model, connection, executor, owner)


# --- the rule ------------------------------------------------------------------

@pytest.mark.parametrize("model", [
    "claude/claude-opus-5-5", "codex/gpt-6-sol", "antigravity-bridge/gemini-4", "antigravity/gemini-4",
    "CODEX/gpt-6", " codex/gpt-6", "magpie/codex/gpt-6", "openai-compatible/magpie/claude/opus", "codex-2/gpt-6",
    "codex2/gpt-6", "claude_code/opus", "openai-codex/gpt-6", "chatgpt/gpt-6", "claudecode/opus", "codexcli/x", "relay/codex/gpt-6"])
@pytest.mark.parametrize("connection", [
    MAGPIE, {**MAGPIE, "auth_method": "api_key"}, {**PUBLIC_KEY, "base_url": "https://relay.example.com/v1"},
    {**MAGPIE, "auth_method": "external_cli_session"}])
def test_a_paid_provider_namespace_is_refused_on_every_route(model, connection):
    assert cause(model, connection).startswith("provider:")


@pytest.mark.parametrize("model", [
    "copilot/claude-opus-5.5", "copilot/gpt-6-sol", "copilot/auto", "workbuddy/auto", "workbuddy-ai/gpt-6-sol",
    "trae-cn/glm-5.3", "opencode-zen-free/big-pickle", "groq/openai/gpt-oss-120b", "openrouter/openai/gpt-6.1-terra",
    "openrouter/google/gemini-omni", "raccoon/sn-glm-5-3", "minimax-code/MiniMax-M3", "zcode/GLM-5.2", "glm-5.2",
    "qwen3:8b", "gpt-oss:20b", "openai/gpt-oss-20b", "openai/text-embedding-3", "auto/glm-5.3", "auto/kimi-k3"])
def test_other_sources_are_untouched(model):
    assert cause(model) == ""


def test_native_agents_and_vendor_api_keys_are_untouched():
    assert cause("gpt-6.1-sol", CODEX, "codex") == ""
    assert cause("opus", CLAUDE, "claude_code") == ""
    assert cause("gpt-6", PUBLIC_KEY) == ""
    assert cause("claude-opus-5-5", {"auth_method": "api_key", "base_url": "https://api.anthropic.com",
                                     "executor_provider_id": "anthropic-compatible"}, "claude_code") == ""


def test_a_session_on_a_vendor_host_is_untouched_but_a_gateway_named_after_an_account_is_not():
    zen = {"auth_method": "external_cli_session", "base_url": "https://opencode.ai/zen/v1", "executor_provider_id": "ai"}
    assert cause("gpt-6", zen) == cause("glm-5.2", zen) == ""
    assert cause("antigravity/swe-1", {**MAGPIE, "executor_provider_id": "antigravity"}) == "provider:antigravity"


@pytest.mark.parametrize("auth", ["external_cli_session", "account_login"])
@pytest.mark.parametrize("model", ["gpt-6-sol", "auto"])
def test_a_session_connection_to_the_gateway_is_refused_at_dispatch(host, auth, model):
    host._store.upsert_connection({"connection_id": "session", "name": "S", "provider": "openai-compatible",
        "base_url": "http://127.0.0.1:3425/v1", "auth_method": auth, "enabled": True})
    bind(host, "s", model, connection_id="session")
    with pytest.raises(gate.PaidSubscriptionGatewayError):
        host._store.resolve_execution_snapshot("s")
    with pytest.raises(BindingResolutionError, match="^paid_subscription_gateway$"):
        BindingResolver(transport=owner_window._store_transport(host._store)).resolve("s", task_executor="opencode")


def test_a_native_executor_does_not_launder_a_gateway():
    # Claude Code pointed at the gateway's Anthropic endpoint, and a login that is not its own.
    relay = {"auth_method": "api_key", "base_url": "https://token.example.com/v1",
             "anthropic_base_url": "http://127.0.0.1:3425", "executor_provider_id": "litellm-proxy"}
    assert cause("claude-opus-5-5", relay, "claude_code") == "model_family:claude"
    assert cause("claude/opus", {**CLAUDE, "auth_method": "none"}, "claude_code") == "provider:claude"
    assert cause("codex/gpt-6", CLAUDE, "codex") == "provider:codex"


@pytest.mark.parametrize("base_url", [
    "http://127.0.0.1:3425/v1", "http://localhost:3425", "http://[::1]:3425", "http://192.168.64.1:3425/v1",
    "http://10.0.0.2", "http://127.1:3425", "http://0x7f.0.0.1:3425", "http://gateway:8080", "http://host.docker.internal:3425", "http://pc.lan", "::bad[", ""])
@pytest.mark.parametrize("auth", ["api_key", "external_cli_session", "account_login"])
def test_a_bare_name_on_a_local_gateway_is_refused_whatever_it_signs_in_with(base_url, auth):
    connection = {"auth_method": auth, "base_url": base_url}
    assert gate.block_cause("workbuddy/glm-5.3", connection, "opencode", None) == "settings_unreadable"
    for model in ("claude-opus-5-5", "gpt4o", "openai/gpt-6", "anthropic/claude-opus-5-5", "google/gemini-4", "sonnet", "gpt-6-sol", "gpt5", "o3-mini", "gemini-3.8-flash", "openai-compatible/gpt-6"):
        assert cause(model, connection).startswith("model_family:"), model
    assert cause("auto", connection) == cause("", connection) == cause(None, connection) == "model_unknown"
    assert cause("glm-5.2", connection) == ""


# --- groups and auto -----------------------------------------------------------

@pytest.mark.parametrize("model", ["group/nerelan-gpt-6-sol", "magpie/group/nerelan-gpt-6-sol", "Group/Nerelan-GPT-6-Sol"])
def test_group_membership_decides(model):
    key = "group/nerelan-gpt-6-sol"
    assert cause(model) == "group_membership_unknown"
    assert cause(model, groups={key: {"identity": "gpt-6-sol"}}) == "group_membership_unknown"
    assert cause(model, groups={key: {"identity": "gpt-6-sol", "members": MIXED}}) == "group_member:codex"
    assert cause(model, groups={key: {"identity": "gpt-6-sol", "members": CLEAN}}) == ""


def test_group_names_and_identities_hide_nothing():
    assert cause("group/coding") == "group_membership_unknown"  # undeclared: anything may serve it
    # A harmless name or identity does not hide a paid member, or a paid identity.
    assert cause("group/coding", groups={"group/coding": {"identity": "glm-5.3", "members": MIXED}}) == "group_member:codex"
    assert cause("group/coding", groups={"group/coding": {"identity": "claude-opus-5-5"}}) == "group_membership_unknown"
    assert cause("group/nerelan-gpt-6", groups={"group/nerelan-gpt-6": {"identity": "glm-5.3"}}) == "group_membership_unknown"
    assert cause("group/nerelan-glm-5-3", groups={"group/nerelan-glm-5-3": {"identity": "glm-5.3"}}) == ""


def test_dropped_members_are_unknown_membership(tmp_path):
    path = tmp_path / "model_routing_overrides.json"
    path.write_text(json.dumps({"groups": {"Group/GLM": {"identity": "glm-5.3", "members": ["codex/gpt-6", "bad"]}}}),
                    encoding="utf-8")
    assert gate.block_cause("group/glm", MAGPIE, "opencode", read_overrides(tmp_path / "model_setup_state.json")) \
        == "group_membership_unknown"


@pytest.mark.parametrize("model", ["auto/gpt-6-sol", "auto/claude-opus-5-5", "auto/gemini-3.8-flash", "auto/auto",
                                   "magpie/auto/gpt-6-sol", "auto/group/x"])
def test_auto_routes_of_a_subscription_family_stay_closed_even_when_declared(model):
    key = model.removeprefix("magpie/")
    assert cause(model) == "auto_membership_unknown"
    assert cause(model, groups={key: {"identity": "glm-5.3", "members": CLEAN}}) == "auto_membership_unknown"


def test_a_declared_auto_route_with_a_paid_member_is_refused():
    assert cause("auto/glm-5.3", groups={"auto/glm-5.3": {"identity": "glm-5.3", "members": MIXED}}) == "group_member:codex"


# --- the setting ---------------------------------------------------------------

def test_the_provider_list_is_a_setting_with_safe_defaults(tmp_path):
    state, path = tmp_path / "model_setup_state.json", tmp_path / "model_routing_overrides.json"
    assert gate.owner_settings(None) == {} and gate.owner_settings(state) == {}
    path.write_text(json.dumps({"paid_subscriptions": {"providers": {"codex": ["gpt"], "grok": ["grok"]}}}), encoding="utf-8")
    owner = gate.owner_settings(state)
    assert gate.block_cause("grok/grok-5", MAGPIE, "opencode", owner) == "provider:grok"
    assert gate.block_cause("grok-5", MAGPIE, "opencode", owner) == "model_family:grok"
    assert gate.block_cause("claude/opus", MAGPIE, "opencode", owner) == ""


@pytest.mark.parametrize("setting", [None, {}, [], {"providers": {}}, {"providers": []}, {"providers": {"codex": "gpt"}},
                                     {"providers": {"": ["gpt"]}}, {"providers": {"codex": [1]}},
                                     {"providers": {"codex": ["gpt"]}, "enabled": False}])
def test_a_malformed_setting_fails_closed(tmp_path, setting):
    (tmp_path / "model_routing_overrides.json").write_text(json.dumps({"paid_subscriptions": setting}), encoding="utf-8")
    state = tmp_path / "model_setup_state.json"
    with pytest.raises(ValueError, match="invalid_model_routing_overrides"):
        read_overrides(state)
    owner = gate.owner_settings(state)
    assert owner is None
    assert gate.block_cause("workbuddy/glm-5.3", MAGPIE, "opencode", owner) == "settings_unreadable"
    assert gate.block_cause("codex/gpt-6", MAGPIE, "opencode", owner) == "provider:codex"
    assert gate.block_cause("gpt-6.1-sol", CODEX, "codex", owner) == ""  # native agents keep working


# --- every way to a dispatch ---------------------------------------------------

@pytest.fixture
def host(tmp_path, monkeypatch):
    """The real store, routing and resolver paths; no server, account or model access."""
    monkeypatch.setenv("REVERSE_AGENT_SUBSCRIPTION_QUOTA", "0")
    monkeypatch.delenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", raising=False)
    from reverse_agent.platform_v1.model_availability import AvailabilityCache
    host = object.__new__(CombinedTrustedHost)
    host._store = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    host._task_store = TaskStore(":memory:")
    host._availability_cache = AvailabilityCache()
    host._availability_probe = None
    host._relay_manager, host.relay_url = None, "http://127.0.0.1:1"
    host._store.upsert_connection({"connection_id": "magpie", "name": "Magpie", "provider": "openai-compatible",
        "base_url": "http://127.0.0.1:3425/v1", "auth_method": "none", "enabled": True})
    host.overrides = tmp_path / "model_routing_overrides.json"
    return host


def bind(host, binding_id, model, **over):
    host._store.upsert_binding({"binding_id": binding_id, "name": binding_id, "executor_id": "opencode",
                                "connection_id": "magpie", "model_id": model, "enabled": True, **over})


def declare(host, **data):
    host.overrides.write_text(json.dumps({"models": {"copilot/gpt-6-sol": "free"}, **data}), encoding="utf-8")


def task(difficulty=2):
    return PlannedTask("T", "Edit", "Edit", difficulty=difficulty)


BLOCKED_MODELS = ["codex/gpt-6-sol", "claude/claude-opus-5-5", "antigravity-bridge/gemini-4", "auto/gpt-6-sol",
                  "group/nerelan-gpt-6-sol", "gpt-6-sol"]


@pytest.mark.parametrize("model", BLOCKED_MODELS)
def test_selection_never_picks_it_and_says_why(host, model):
    bind(host, "paid", model)
    declare(host, bindings={"paid": {"cost_class": "free", "tiers": {"code": 5}}},
            groups={"group/nerelan-gpt-6-sol": {"identity": "gpt-6-sol", "members": MIXED}})
    with pytest.raises(TaskStoreError) as caught:
        host._resolve_task_model(task())
    row = caught.value.decision["excluded_candidates"][0]
    assert row["binding_id"] == "paid" and row["filter"] == "paid_subscription_gateway" and row["cause"]
    bind(host, "ok", "copilot/gpt-6-sol")
    assert host._resolve_task_model(task())["binding_ref"] == "ok"


@pytest.mark.parametrize("model", BLOCKED_MODELS)
def test_an_owner_pin_or_retry_choice_does_not_override_it(host, model):
    bind(host, "paid", model)
    bind(host, "ok", "copilot/gpt-6-sol")
    declare(host, bindings={"paid": {"cost_class": "free"}})
    goal = SimpleNamespace(binding_ref="paid", window_id="", id="g")  # owner retry pins the chosen binding
    with pytest.raises(TaskStoreError, match="pinned_model_unavailable") as caught:
        host._resolve_task_model(task(), goal=goal)
    assert caught.value.decision["pin_filter"] == "paid_subscription_gateway"
    # Nor do failure fallbacks: escalation from a failed model, a stall, a refusal.
    for fallback in ({"failed_binding": "ok"}, {"avoid_bindings": ("ok",)}, {"refused_models": ("glm-5.2",)}):
        assert host._resolve_task_model(task(), **fallback)["binding_ref"] == "ok"


def test_review_selection_excludes_it_too():
    row = {"binding_id": "paid", "model_id": "claude/opus", "executor_id": "opencode", "dispatch_block": "provider:claude"}
    with pytest.raises(ModelSelectionError) as caught:
        select_model([row], difficulty=1, kind="review", role="reviewer", author_models=["glm-5.2"], pin="paid")
    assert caught.value.decision["pin_filter"] == "paid_subscription_gateway"


def test_newly_discovered_models_are_bound_but_never_dispatched(host):
    host._store.record_model_catalog("magpie", ["codex/gpt-9", "auto/gpt-9", "copilot/gpt-6-sol"], {})
    declare(host)
    decision = host._resolve_task_model(task())
    assert decision["model_id"] == "copilot/gpt-6-sol"
    assert decision["excluded_summary"]["paid_subscription_gateway"] == 2
    blocked = {b["model_id"] for b in host._store.list_bindings_public() if b["dispatch_block"]}
    assert blocked == {"codex/gpt-9", "auto/gpt-9"}


@pytest.mark.parametrize("model", BLOCKED_MODELS)
def test_dispatch_refuses_a_binding_chosen_earlier(host, model):
    """A queued task keeps its binding_ref; the resolver, leases and probes all refuse it."""
    bind(host, "paid", model)
    resolver = host._binding_resolver_factory("http://127.0.0.1:1")
    with pytest.raises(BindingResolutionError, match="^paid_subscription_gateway$"):
        resolver.resolve("paid", task_executor="opencode")
    with pytest.raises(gate.PaidSubscriptionGatewayError):
        host._store.resolve_execution_snapshot("paid")
    with pytest.raises(gate.PaidSubscriptionGatewayError):
        host._lease_provider_factory()(SimpleNamespace(binding_ref="paid"))
    with pytest.raises(gate.PaidSubscriptionGatewayError):
        host._probe_routing_binding(host._store.get_binding_public("paid"))
    with pytest.raises(BindingResolutionError, match="paid_subscription_gateway"):
        BindingResolver(transport=owner_window._store_transport(host._store)).resolve("paid", task_executor="opencode")
    assert "paid" not in host._runnable_bindings()


def test_a_group_change_takes_effect_at_the_next_dispatch(host):
    bind(host, "group", "group/nerelan-gpt-6-sol")
    resolver = BindingResolver(transport=owner_window._store_transport(host._store))
    declare(host, groups={"group/nerelan-gpt-6-sol": {"identity": "gpt-6-sol", "members": CLEAN}})
    assert resolver.resolve("group", task_executor="opencode").model_id == "openai-compatible/group/nerelan-gpt-6-sol" \
        or resolver.resolve("group", task_executor="opencode").model_id == "group/nerelan-gpt-6-sol"
    declare(host, groups={"group/nerelan-gpt-6-sol": {"identity": "gpt-6-sol", "members": MIXED}})
    with pytest.raises(BindingResolutionError, match="paid_subscription_gateway"):
        resolver.resolve("group", task_executor="opencode")


def test_a_rebound_binding_is_judged_again(host):
    bind(host, "b", "copilot/gpt-6-sol")
    assert host._store.get_binding_public("b")["dispatch_block"] == ""
    bind(host, "b", "codex/gpt-6-sol")
    assert host._store.get_binding_public("b")["dispatch_block"] == "provider:codex"
    with pytest.raises(gate.PaidSubscriptionGatewayError):
        host._store.resolve_execution_snapshot("b")


def test_window_pools_do_not_offer_it(host):
    bind(host, "paid", "codex/gpt-6-sol")
    bind(host, "ok", "copilot/gpt-6-sol")
    declare(host)
    pool, _shown, skipped = owner_window.resolve_pool(host._store, {})
    assert [entry["binding_ref"] for entry in pool] == ["ok"]
    assert skipped == ["paid (paid_subscription_gateway)"]
    assert [entry["binding_ref"] for entry in owner_window.live_pool(host._store)] == ["ok"]


def test_legacy_role_routing_refuses_it(host):
    bind(host, "paid", "codex/gpt-6-sol")
    host._store.put_agent_roster({"roles": {"coder": "paid"}})
    with pytest.raises(TaskStoreError, match="paid_subscription_gateway"):
        host._resolve_agent_role("coder")


def test_a_reviewer_call_cannot_be_built_for_it(host):
    """The tool-less reviewer dispatches only a resolution, which the resolver refuses first."""
    bind(host, "paid", "claude/claude-opus-5-5")
    with pytest.raises(BindingResolutionError):
        host._binding_resolver_factory("http://127.0.0.1:1").resolve("paid", task_executor="opencode")
    assert callable(model_review_transport.review)


def test_a_server_that_reports_no_verdict_is_judged_by_the_defaults():
    rows = {"bindings": {"binding_id": "x", "enabled": True, "executor_id": "opencode", "connection_id": "magpie",
                         "model_id": "codex/gpt-6"},
            "connections": {"connection_id": "magpie", "enabled": True, "provider": "openai-compatible", **MAGPIE}}
    resolver = BindingResolver(transport=lambda url, *_: (200, rows[url.split("/api/")[1].split("/")[0]]))
    with pytest.raises(BindingResolutionError, match="paid_subscription_gateway"):
        resolver.resolve("x", task_executor="opencode")


@pytest.mark.parametrize("model", ["magpie/claude/opus", "codex/gpt-6", "magpie/auto/gpt-6", "magpie/group/any"])
@pytest.mark.parametrize("durable", [False, True])
def test_a_task_without_a_binding_cannot_name_it(monkeypatch, model, durable):
    from reverse_agent.platform_v1 import task_execution
    from reverse_agent.platform_v1.durable_execution import DurableExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_MODEL", model)
    store = TaskStore(":memory:")
    row = store.create_task(title="unbound", executor_kind="opencode")
    with pytest.raises(BindingResolutionError, match="paid_subscription_gateway"):
        if durable:
            DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="a",
                                    planning_sha="p")._build_executor_kwargs(store.get_task(row.id))
        else:
            task_execution._build_executor_kwargs(store.get_task(row.id))


def test_the_refusal_is_no_evidence_against_the_model():
    assert neutral_failure(gate.BLOCKED_CLASS, gate.BLOCKED_CLASS) == gate.BLOCKED_CLASS


def test_native_codex_still_routes(host):
    host._store.upsert_connection({"connection_id": "native", "name": "Native", "provider": "codex",
        "base_url": "https://chatgpt.com", "auth_method": "external_cli_session", "enabled": True})
    bind(host, "native", "gpt-6.1-sol", executor_id="codex", connection_id="native")
    host._store.set_native_readiness("codex", "managed_login_ready")
    assert host._store.get_binding_public("native")["dispatch_block"] == ""
    assert host._resolve_task_model(task())["binding_ref"] == "native"
    assert host._store.resolve_execution_snapshot("native").raw_model_id == "gpt-6.1-sol"
