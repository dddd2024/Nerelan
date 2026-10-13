"""Natural-language Agent team configuration (zero model calls)."""
import json

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.agent_planner import PlannerOutput
from reverse_agent.platform_v1.policy_configurator import (
    PolicyConfigurator, binding_health, build_policy_prompt, extract_policy,
)
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

KNOWN = {
    "claude-opus": {"binding_id": "claude-opus", "executor_id": "claude_code", "model_id": "opus", "connection_id": "claude-account"},
    "claude-sonnet": {"binding_id": "claude-sonnet", "executor_id": "claude_code", "model_id": "sonnet", "connection_id": "claude-account"},
    "coding-glm": {"binding_id": "coding-glm", "executor_id": "opencode", "model_id": "glm-5.2", "connection_id": "deepseek-flash"},
    "coding-kimi": {"binding_id": "coding-kimi", "executor_id": "opencode", "model_id": "kimi-k3", "connection_id": "deepseek-flash"},
    "chatgpt-gpt": {"binding_id": "chatgpt-gpt", "executor_id": "codex", "model_id": "gpt-6.1-sol", "connection_id": "chatgpt-account"},
}
PROPOSAL = {"roles": {"planner": "claude-opus", "complex": "claude-sonnet", "coder": "coding-glm",
                      "simple": "coding-glm", "reviewer": "chatgpt-gpt"},
            "excluded": ["coding-kimi"], "explanation": "规划用 Opus，日常编码用免费的 GLM，审查交给 GPT，Kimi 近期限流故排除。"}


def test_prompt_carries_preference_bindings_and_health():
    prompt = build_policy_prompt(text="Kimi 别用，尽量省钱", bindings=list(KNOWN.values()),
                                 health={"coding-kimi": {"ok": 0, "failed": 3, "rate_limited": 3}})
    for token in ("Kimi 别用", "coding-kimi", "rate_limited=3", "claude-opus", "different"):
        assert token in prompt


def test_extract_policy_validates_against_real_bindings():
    proposal = extract_policy("```json\n" + json.dumps(PROPOSAL) + "\n```", known=KNOWN)
    assert proposal["roles"]["coder"] == "coding-glm" and proposal["excluded"] == ["coding-kimi"]
    assert "GLM" in proposal["explanation"]


@pytest.mark.parametrize("change,error", [
    ({"roles": {"coder": "made-up"}}, "agent_policy_unknown_binding:coder"),
    ({"roles": {"coder": "coding-kimi"}, "excluded": ["coding-kimi"]}, "agent_policy_role_uses_excluded_binding:coder"),
    ({"roles": {"planner": "coding-glm"}}, "agent_policy_planner_requires_native_executor"),
    ({"roles": "everything"}, "agent_policy_roles_required"),
])
def test_extract_policy_rejects_invented_or_inconsistent_proposals(change, error):
    with pytest.raises(TaskStoreError, match=error):
        extract_policy(json.dumps({**PROPOSAL, **change}), known=KNOWN)


def _store(tmp_path):
    store = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    store.upsert_connection({"connection_id": "free", "name": "Free", "provider": "openai-compatible",
                             "base_url": "https://example.invalid/v1", "auth_method": "none", "enabled": True})
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session", "enabled": True})
    for binding_id, executor, connection, model in (("claude-opus", "claude_code", "claude-account", "opus"),
                                                     ("coding-glm", "opencode", "free", "glm-5.2"),
                                                     ("coding-flash", "opencode", "free", "flash-lite")):
        store.upsert_binding({"binding_id": binding_id, "name": binding_id, "executor_id": executor,
                              "connection_id": connection, "model_id": model, "enabled": True})
    return store


def _configurator(store, runner):
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        return runner(**kwargs)
    return PolicyConfigurator(bindings=store.list_bindings_public, health=lambda: {},
                              interpreter=lambda: ("claude_code", "claude-opus", "opus"),
                              apply_roster=store.put_agent_roster, runner=run), calls


def test_interpret_proposes_without_applying_then_apply_saves_roster_and_policy(tmp_path):
    store = _store(tmp_path)
    answer = {"roles": {"planner": "claude-opus", "complex": "claude-opus", "coder": "coding-glm",
                        "simple": "coding-flash", "reviewer": "claude-opus"},
              "excluded": [], "explanation": "规划和审查用 Opus，编码用免费模型。"}
    configurator, calls = _configurator(store, lambda **_: PlannerOutput(json.dumps(answer), {"input_tokens": 9,
                                                                                            "cached_input_tokens": 0,
                                                                                            "output_tokens": 4}))
    job = configurator.interpret("规划和审查用最强的，编码用免费的", background=False)
    assert job["status"] == "PROPOSED" and job["proposal"]["roles"]["simple"] == "coding-flash"
    assert job["usage_status"] == "observed_tokens"
    assert calls[0]["executor_kind"] == "claude_code" and "规划和审查用最强的" in calls[0]["prompt"]
    assert store.get_agent_roster_public()["roles"]["coder"]["binding_id"] == ""  # nothing applied yet
    applied = configurator.apply(job["id"])
    roster = applied["roster"]
    assert roster["roles"]["coder"]["binding_id"] == "coding-glm"
    assert roster["policy"]["text"] == "规划和审查用最强的，编码用免费的"
    assert configurator.get(job["id"])["status"] == "APPLIED"
    reloaded = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    assert reloaded.get_agent_roster_public()["policy"]["explanation"] == "规划和审查用 Opus，编码用免费模型。"
    with pytest.raises(TaskStoreError, match="agent_policy_not_proposed"):
        configurator.apply(job["id"])


def test_apply_surfaces_roster_validation_and_manual_edit_clears_policy(tmp_path):
    store = _store(tmp_path)
    same_model = {"roles": {"coder": "coding-glm", "reviewer": "coding-glm"}, "excluded": [], "explanation": "x"}
    configurator, _ = _configurator(store, lambda **_: json.dumps(same_model))
    job = configurator.interpret("随便", background=False)
    with pytest.raises(TaskStoreError, match="agent_reviewer_must_differ_from_coder"):
        configurator.apply(job["id"])
    store.put_agent_roster({"roles": {"coder": "coding-glm"}, "policy": {"text": "旧偏好"}})
    store.put_agent_roster({"roles": {"coder": "coding-flash"}})
    assert store.get_agent_roster_public()["policy"] == {}


def test_interpret_failures_are_finite(tmp_path):
    store = _store(tmp_path)
    configurator, _ = _configurator(store, lambda **_: "我不确定")
    assert configurator.interpret("x", background=False)["error"] == "agent_policy_not_json"
    with pytest.raises(TaskStoreError, match="agent_policy_text_invalid"):
        configurator.interpret("   ", background=False)
    opencode_only = PolicyConfigurator(bindings=store.list_bindings_public, health=lambda: {},
                                       interpreter=lambda: ("opencode", "coding-glm", "glm-5.2"),
                                       apply_roster=store.put_agent_roster, runner=lambda **_: "")
    with pytest.raises(TaskStoreError, match="agent_policy_requires_native_interpreter"):
        opencode_only.interpret("x", background=False)


def test_binding_health_counts_outcomes_and_rate_limits():
    store = TaskStore(":memory:")
    for status, classification, binding in (("READY_FOR_REVIEW", "", "coding-glm"), ("FAILED", "provider_rate_limited", "coding-kimi"),
                                            ("FAILED", "patch_hygiene_failed", "coding-kimi")):
        task = store.create_task(title="t", executor_kind="opencode", binding_ref=binding, repository="o/r")
        store._conn.execute("UPDATE tasks SET status = ?, failure_classification = ? WHERE id = ?", (status, classification, task.id))
    store._conn.commit()
    health = binding_health(store)
    pick = lambda stats: {key: stats[key] for key in ("ok", "failed", "rate_limited")}
    assert pick(health["coding-glm"]) == {"ok": 1, "failed": 0, "rate_limited": 0}
    assert pick(health["coding-kimi"]) == {"ok": 0, "failed": 2, "rate_limited": 1}
