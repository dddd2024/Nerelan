"""Multi-agent team: role roster and per-task agent routing (provider-free)."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
import reverse_agent.platform_v1.goal_service as goal_service_module
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

BASE = "a" * 40


def _models(tmp_path):
    store = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    store.upsert_connection({"connection_id": "free-api", "name": "Free", "provider": "openai-compatible",
                             "base_url": "https://example.invalid/v1", "auth_method": "none", "enabled": True})
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session", "enabled": True})
    for binding_id, executor, connection, model in (
        ("cheap", "opencode", "free-api", "flash-lite"),
        ("mid", "opencode", "free-api", "glm-5.2"),
        ("strong", "claude_code", "claude-account", "opus"),
    ):
        store.upsert_binding({"binding_id": binding_id, "name": binding_id, "executor_id": executor,
                              "connection_id": connection, "model_id": model, "enabled": True})
    return store


def test_roster_maps_roles_to_bindings_and_persists(tmp_path):
    store = _models(tmp_path)
    roster = store.put_agent_roster({"roles": {"planner": "strong", "complex": "strong", "coder": "mid",
                                               "simple": "cheap", "reviewer": "cheap"}})
    assert roster["roles"]["coder"] == {"binding_id": "mid", "available": True,
                                        "executor_id": "opencode", "model_id": "glm-5.2"}
    assert roster["roles"]["planner"]["executor_id"] == "claude_code"
    saved = json.loads((tmp_path / "agent_roster.json").read_text(encoding="utf-8"))
    assert saved == {"schema_version": 1, "roles": {"planner": "strong", "complex": "strong", "coder": "mid",
                                                    "simple": "cheap", "reviewer": "cheap"}}
    reloaded = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    assert reloaded.get_agent_roster_public()["roles"]["simple"]["binding_id"] == "cheap"


@pytest.mark.parametrize("roles,error", [
    ({"wizard": "mid"}, "unknown_agent_role:wizard"),
    ({"coder": "missing"}, "agent_role_binding_unknown:coder"),
    ({"coder": "mid", "reviewer": "mid"}, "agent_reviewer_must_differ_from_coder"),
])
def test_roster_rejects_invalid_assignments(tmp_path, roles, error):
    store = _models(tmp_path)
    with pytest.raises(ValueError, match=error):
        store.put_agent_roster({"roles": roles})
    assert not (tmp_path / "agent_roster.json").exists()


def test_owner_stand_ins_persist_survive_role_edits_and_validate(tmp_path):
    store = _models(tmp_path)
    store.put_agent_roster({"roles": {"complex": "strong"}, "standins": {"complex": ["mid", "mid", ""]}})
    assert store.get_agent_roster_public()["standins"] == {"complex": ["mid"]}
    store.put_agent_roster({"roles": {"complex": "strong", "coder": "mid"}})  # a role edit keeps them
    reloaded = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    assert reloaded.get_agent_roster_public()["standins"] == {"complex": ["mid"]}
    with pytest.raises(ValueError, match="agent_standin_role_invalid:planner"):
        store.put_agent_roster({"roles": {}, "standins": {"planner": ["mid"]}})
    with pytest.raises(ValueError, match="agent_standin_binding_unknown:complex"):
        store.put_agent_roster({"roles": {}, "standins": {"complex": ["missing"]}})
    store.delete_binding("mid")  # a removed stand-in is not offered
    assert store.get_agent_roster_public()["standins"] == {}
    store.put_agent_roster({"roles": {"complex": "strong"}, "standins": {}})
    assert "standins" not in json.loads((tmp_path / "agent_roster.json").read_text(encoding="utf-8"))


def test_deleted_binding_leaves_role_unfilled_not_remapped(tmp_path):
    store = _models(tmp_path)
    store.put_agent_roster({"roles": {"coder": "mid"}})
    store.delete_binding("mid")
    assert store.get_agent_roster_public()["roles"]["coder"]["available"] is False


@pytest.mark.parametrize("content", ["{not json", "[]", '"text"', '{"schema_version": 1, "roles": []}'])
def test_damaged_roster_file_never_blocks_the_store(tmp_path, content):
    _models(tmp_path)
    (tmp_path / "agent_roster.json").write_text(content, encoding="utf-8")
    store = ModelProfileStore(state_path=tmp_path / "model_setup_state.json")
    assert store.get_agent_roster_public()["roles"]["coder"]["binding_id"] == ""
    assert store.get_binding_public("mid")["model_id"] == "glm-5.2"


def _window_payload(repository):
    now = datetime.now(timezone.utc)
    return {"policy_id": "owner-window-team", "policy_revision": 1, "owner_identity": "owner@example",
            "starts_at": (now - timedelta(seconds=5)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": [repository], "capabilities": ["execute_task", "validate_task"],
            "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE"}


def _team(monkeypatch, roster):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    monkeypatch.setattr(goal_service_module, "resolve_repository_workspace", lambda repository: object())
    monkeypatch.setattr(goal_service_module, "repository_base", lambda repository: BASE)

    def resolve(role):
        if role not in roster:
            raise TaskStoreError(f"agent_role_unfilled:{role}")
        return roster[role]
    return store, control, autonomy, GoalService(store=store, control_store=control, roster_resolver=resolve)


PLAN = [
    {"id": "T001", "title": "Design the change", "instruction": "Design", "agent_role": "complex"},
    {"id": "T002", "title": "Implement it", "instruction": "Implement", "dependencies": ["T001"]},
    {"id": "T003", "title": "Update docs", "instruction": "Docs", "dependencies": ["T002"], "agent_role": "simple"},
]


def test_agent_team_goal_routes_each_task_to_its_role_agent(monkeypatch):
    roster = {"complex": ("claude_code", "strong"), "coder": ("opencode", "mid"), "simple": ("opencode", "cheap")}
    store, control, autonomy, goals = _team(monkeypatch, roster)
    goal = goals.create({"objective": "Ship a feature with a team", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "team-goal-1", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    planned = goals.plan(goal.id, expected_revision=1, tasks=PLAN).goal
    assert "agent_role" not in planned.tasks[1] and planned.tasks[0]["agent_role"] == "complex"
    goals.approve(goal.id, expected_revision=1)
    window = autonomy.activate(_window_payload("dddd2024/Nerelan"))
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    routed = {link["plan_task_id"]: store.get_task(link["task_id"]) for link in control.list_goal_tasks(goal.id)}
    assert (routed["T001"].executor_kind, routed["T001"].binding_ref, routed["T001"].branch) == ("claude_code", "strong", BASE)
    assert (routed["T002"].executor_kind, routed["T002"].binding_ref) == ("opencode", "mid")  # default role: coder
    assert (routed["T003"].executor_kind, routed["T003"].binding_ref) == ("opencode", "cheap")
    assert {task.orchestration_mode for task in routed.values()} == {"single"}


def test_unfilled_role_fails_before_any_task_is_created(monkeypatch):
    store, control, autonomy, goals = _team(monkeypatch, {"coder": ("opencode", "mid")})
    goal = goals.create({"objective": "Needs a complex agent", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "team-goal-2", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    goals.plan(goal.id, expected_revision=1, tasks=PLAN)
    goals.approve(goal.id, expected_revision=1)
    window = autonomy.activate(_window_payload("dddd2024/Nerelan"))
    with pytest.raises(TaskStoreError, match="agent_role_unfilled:complex"):
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert len(control.list_goal_tasks(goal.id)) == 0


def test_agent_team_without_roster_and_bad_roles_fail_closed(monkeypatch):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "No roster available", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "team-goal-3", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    with pytest.raises(TaskStoreError, match="unsupported_agent_role:wizard"):
        goals.plan(goal.id, expected_revision=1,
                   tasks=[{"id": "T001", "title": "x", "instruction": "y", "agent_role": "wizard"}])
    goals.plan(goal.id, expected_revision=1, tasks=PLAN[:1])
    goals.approve(goal.id, expected_revision=1)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = autonomy.activate(_window_payload("dddd2024/Nerelan"))
    with pytest.raises(TaskStoreError, match="agent_roster_unavailable"):
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
    with pytest.raises(TaskStoreError, match="agent_team_requires_model_executor"):
        goals.create({"objective": "Fixture team", "repository": "dddd2024/Nerelan", "idempotency_key": "team-goal-4",
                      "executor_kind": "deterministic_fixture", "orchestration_mode": "agent_team"})


def test_mixed_executor_team_tasks_keep_functional_evidence(monkeypatch):
    roster = {"complex": ("claude_code", "strong"), "coder": ("opencode", "mid"), "simple": ("opencode", "cheap")}
    store, control, autonomy, goals = _team(monkeypatch, roster)
    goal = goals.create({"objective": "Mixed team evidence", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "team-goal-evidence", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    goals.plan(goal.id, expected_revision=1, tasks=PLAN)
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate(_window_payload("dddd2024/Nerelan")).id)
    current = control.get_goal(goal.id)
    for link in control.list_goal_tasks(goal.id):
        evidence = goals._task_link_evidence(current, link)["functional_validation"]
        assert evidence.get("reason") != "goal_functional_contract_mismatch", (link["plan_task_id"], evidence)
