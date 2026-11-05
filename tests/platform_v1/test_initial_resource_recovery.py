"""Initial resource waits recover through existing Goal/Coordinator admission."""
import json
import time
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1 import goal_service as module
from reverse_agent.platform_v1.goal_service import PlannedTask
from reverse_agent.platform_v1.model_router import ModelSelectionError
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from tests.platform_v1.test_agent_team import _team, _window_payload, BASE
from tests.platform_v1.test_unattended_coordinator import _ready_fixture


@pytest.fixture
def launch(monkeypatch, tmp_path):
    stores = []
    clock = [time.time()]
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    monkeypatch.setattr(module.time, "time", lambda: clock[0])
    def build(tasks=None):
        store, control, autonomy, goals = _team(monkeypatch, {})
        stores.append(store)
        state = {"available": False, "reason": "no_runnable_model", "independent": True}
        calls, executed = [], []
        def resolve(task, **kwargs):
            calls.append((task.id, kwargs))
            if not state["available"]:
                error = TaskStoreError(state["reason"])
                error.decision = ModelSelectionError(state["reason"], excluded=[{
                    "binding_id": "writer", "filter": "account_quarantined", "retry_at": clock[0] + 5}]).decision
                raise error
            if task.kind == "review" and not state["independent"]:
                error = TaskStoreError("review_not_independent")
                error.decision = {"reason": "review_not_independent", "excluded_candidates": [
                    {"binding_id": "writer", "filter": "reviewer_is_author"}]}
                raise error
            return dict(binding_ref="reviewer" if task.kind == "review" else "writer",
                executor_kind="opencode", model_id="beta" if task.kind == "review" else "alpha",
                tier=3, reason="cheapest_qualifying")
        goals.task_resolver = resolve
        goal = goals.create(dict(objective="resource recovery fixture", repository="dddd2024/Nerelan",
            idempotency_key="recovery", executor_kind="opencode", orchestration_mode="agent_team"))
        if tasks and any(raw.get("kind") == "review" for raw in tasks):
            tasks = [dict(raw, validation_checks=[{"profile_id": "python_pytest", "working_directory": "."}])
                     for raw in tasks]
        goals.plan(goal.id, expected_revision=1, tasks=tasks or [dict(id="T1", title="work", instruction="work", difficulty=2)])
        goals.approve(goal.id, expected_revision=1)
        window = autonomy.activate(_window_payload(goal.repository))
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
        def execute(task_id):
            executed.append(task_id)
            return _ready_fixture(store, task_id)
        coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
            router=ExecutorRouter(), workspace_root=tmp_path / "workspaces", task_executor=execute, goals=goals)
        links = {row["plan_task_id"]: row["task_id"] for row in control.list_goal_tasks(goal.id)}
        return SimpleNamespace(store=store, control=control, autonomy=autonomy, goals=goals, goal=goal,
            window=window, state=state, calls=calls, executed=executed, coordinator=coordinator,
            links=links, clock=clock, resolve=resolve)
    yield build
    for store in stores:
        store._conn.close()


def task(case, plan_id="T1"):
    return case.store.get_task(case.links[plan_id])


def test_recovered_initial_account_is_admitted_once_without_replacing_the_task(launch):
    case = launch()
    original = task(case)
    events = tuple(event.id for event in case.store.get_events(original.id))
    wait = json.loads(original.failure_detail)["initial_resource_wait"]
    assert original.branch == wait["base_commit"] == BASE
    case.state["available"] = True
    case.clock[0] = wait["retry_at"] + 1
    assert case.coordinator.tick() == 1
    assert case.coordinator.tick() == 0
    final = task(case)
    assert final.id == original.id and final.execution_id == original.execution_id
    assert final.status == "READY_FOR_REVIEW_FIXTURE"
    assert case.executed == [original.id]
    assert set(events) <= {event.id for event in case.store.get_events(original.id)}
    assert len([event for event in case.store.get_events(original.id) if event.type == "MODEL_SELECTED"]) == 1
    assert case.calls[-1][1]["probe_availability"] is False
    budget = case.control.get_window(case.window.id)
    assert (budget.tasks_started, budget.retries_used) == (1, 0)


def test_still_unavailable_rechecks_are_persistently_rate_limited(launch):
    case = launch()
    first = task(case)
    wait = json.loads(first.failure_detail)["initial_resource_wait"]
    assert case.coordinator.tick() == 0 and len(case.calls) == 1
    case.clock[0] = wait["retry_at"] + 1
    assert case.coordinator.tick() == 0 and len(case.calls) == 2
    updated = json.loads(task(case).failure_detail)["initial_resource_wait"]
    assert updated["retry_at"] > case.clock[0]
    assert case.coordinator.tick() == 0 and len(case.calls) == 2
    assert case.control.get_window(case.window.id).tasks_started == 0
    assert case.control.list_task_escalations(case.goal.id) == ()


def test_legacy_unmarked_failures_are_not_reactivated(launch):
    case = launch()
    initial = task(case)
    decision = {"reason": "no_runnable_model", "excluded_candidates": []}
    case.store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (json.dumps(decision), initial.id))
    case.state["available"] = True
    case.clock[0] += 1000
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and len(case.calls) == 1


def test_pending_review_recovers_after_its_initial_author_choice(launch):
    case = launch([dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"}),
                   dict(id="A", title="author", instruction="write", difficulty=2)])
    assert json.loads(task(case, "R").failure_detail)["initial_resource_wait"]["kind"] == "author"
    case.state["available"] = True
    case.clock[0] += 61
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert task(case, "A").status == task(case, "R").status == "QUEUED"
    assert task(case, "R").binding_ref == "reviewer"
    assert case.control.get_goal(case.goal.id).status == "RUNNING"
    review_args = [args for plan, args in case.calls if plan == "R"][-1]
    assert review_args["author_models"] == ("alpha",)
    assert review_args["author_executors"] == ("opencode",)
    assert case.control.get_window(case.window.id).tasks_started == 0


def test_genuine_review_independence_failure_parks_without_repeated_polling(launch):
    case = launch([dict(id="A", title="author", instruction="write"),
                   dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"})])
    case.state.update(available=True, independent=False)
    case.clock[0] += 61
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert task(case, "R").status == "BLOCKED"
    assert "initial_resource_wait" not in json.loads(task(case, "R").failure_detail)
    before = len(case.calls)
    case.clock[0] += 1000
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert len(case.calls) == before


@pytest.mark.parametrize("change", ["expired", "not_started", "stopped", "revision", "artifact", "branch", "policy", "manual_block"])
def test_stale_window_goal_or_initial_identity_never_resumes(launch, change):
    case = launch()
    old = task(case)
    now = datetime.now(timezone.utc)
    if change in {"expired", "not_started"}:
        column = "expires_at" if change == "expired" else "starts_at"
        stamp = (now + timedelta(hours=-1 if change == "expired" else 1)).isoformat()
        case.store._conn.execute(f"UPDATE platform_autonomous_windows SET {column}=? WHERE id=?", (stamp, case.window.id))
    elif change == "stopped":
        case.control.stop_window(case.window.id)
    elif change == "revision":
        case.store._conn.execute("UPDATE platform_goals SET revision=revision+1 WHERE id=?", (case.goal.id,))
    elif change == "artifact":
        case.store._conn.execute("UPDATE platform_goals SET artifact_digest=? WHERE id=?", ("b" * 64, case.goal.id))
    elif change == "branch":
        case.store._conn.execute("UPDATE tasks SET branch=? WHERE id=?", ("b" * 40, old.id))
    elif change == "policy":
        case.store._conn.execute("UPDATE tasks SET policy_ref='foreign' WHERE id=?", (old.id,))
    else:
        case.store._conn.execute("UPDATE tasks SET failure_classification='owner_stopped' WHERE id=?", (old.id,))
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert case.executed == []


@pytest.mark.parametrize("history", ["claim", "run", "reservation", "publication", "usage", "charge", "intent", "worker", "evidence", "diff", "admission"])
def test_any_prior_execution_or_unknown_evidence_prevents_reactivation(launch, history):
    from tests.platform_v1.test_lease_invariants import _queued_task, _acquire
    case = launch()
    target = task(case)
    db = case.store._conn
    if history == "claim":
        db.execute("INSERT INTO platform_coordinator_claims VALUES (?,?, 'previous',1,1,'COMPLETE','x','x')", (target.id, case.window.id))
    elif history == "run":
        db.execute("INSERT INTO durable_runs (run_id,task_id,execution_id,worktree_path,created_at,updated_at) VALUES ('old-run',?,?,'old','x','x')", (target.id, target.execution_id))
    elif history == "reservation":
        db.execute("INSERT INTO platform_budget_reservations (task_id,claim_epoch,window_id,reserved_token_units,"
                   "reserved_cost_micro_units,state,created_at,updated_at) VALUES (?,1,?,1,1,'UNKNOWN','x','x')", (target.id, case.window.id))
    elif history == "publication":
        db.execute("INSERT INTO platform_publications VALUES ('old-pub',?,'dddd2024/Nerelan','main','old','FAILED','','0','','digest','','x','x')", (target.id,))
    elif history in {"usage", "charge"}:
        source = target if history == "usage" else case.store.create_task(title="foreign usage", executor_kind="opencode")
        case.store.append_usage_observation(source.id, observation_id="u", execution_id=source.execution_id,
            role="executor", model_id="alpha", provider_id="", source_kind="fixture", source_id="u", status="UNKNOWN")
        if history == "charge":
            db.execute("INSERT INTO platform_usage_charges VALUES ('u',?,?,1,'x')", (case.window.id, target.id))
    elif history == "intent":
        other = _queued_task(case.store)
        lease = _acquire(case.store, other)
        db.execute("INSERT INTO durable_external_operations (operation_id,run_id,task_id,operation_key,idempotency_key,"
                   "request_digest,state,created_at,updated_at) VALUES ('pending',?,?,'review','key','digest','PENDING','x','x')", (lease.run_id, target.id))
    elif history == "worker":
        case.store.add_event(target.id, event_type="EXECUTOR_RUNNING", title="previous worker", description="fixture")
    elif history == "evidence":
        case.store.add_evidence(target.id, category="fixture", label="unknown", value="u", status="UNKNOWN")
    elif history == "diff":
        db.execute("INSERT INTO task_changed_files (task_id,path,status,additions,deletions,diff_digest) VALUES (?,'file','modified',1,0,'digest')", (target.id,))
    else:
        db.execute("INSERT INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,need_json,small_task,safety_buffer,verdict_json) "
                   "VALUES (?,'old','account','{}','{}',0,10,'{}')", (target.id,))
    events = tuple(event.id for event in case.store.get_events(target.id))
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).execution_id == target.execution_id
    assert len(case.calls) == 1
    assert tuple(event.id for event in case.store.get_events(target.id)) == events


def test_authorization_is_rechecked_after_selection_and_denial_does_not_enqueue(launch, monkeypatch):
    case = launch()
    old = task(case)
    case.state["available"] = True
    case.clock[0] += 61
    called = []
    def deny(**kwargs):
        called.append(kwargs)
        assert task(case).binding_ref == "writer"
        return False
    monkeypatch.setattr(case.autonomy, "authorize", deny)
    assert case.coordinator.tick() == 0
    assert called and task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert task(case).branch == old.branch
    assert not any(event.type == "MODEL_SELECTED" for event in case.store.get_events(old.id))
    case.clock[0] += 100
    assert case.coordinator.tick() == 0 and len(called) == 1


def test_goal_revision_drift_during_resolution_rejects_the_stale_choice(launch):
    case = launch()
    original = case.goals.task_resolver
    def change(task, **kwargs):
        result = original(task, **kwargs)
        case.store._conn.execute("UPDATE platform_goals SET revision=revision+1 WHERE id=?", (case.goal.id,))
        return result
    case.goals.task_resolver = change
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""


def test_automatic_host_selection_disables_probes_without_skipping_actual_quota(monkeypatch, tmp_path):
    from tests.platform_v1.test_model_router import fixture_host
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.setattr(host, "_routing_availability", CombinedTrustedHost._routing_availability.__get__(host))
    probed, checked = [], []
    host._availability_probe = lambda *args: probed.append(args) or {"ok": True}
    def quota(binding):
        checked.append(binding["binding_id"])
        return {"decision": "switch", "reason": "observed_exhausted"} if binding["binding_id"] == "cheap" else None
    monkeypatch.setattr(host, "_quota_check", quota)
    result = host._resolve_task_model(PlannedTask("T", "work", "work", difficulty=2), probe_availability=False)
    assert result["binding_ref"] != "cheap" and "cheap" in checked and probed == []


def test_resource_summary_is_not_lost_at_the_public_diagnostic_limit():
    exclusions = [{"binding_id": str(i), "filter": "owner_override"} for i in range(10)]
    exclusions.append({"binding_id": "last", "filter": "account_quarantined", "retry_at": 1234})
    error = ModelSelectionError("no_runnable_model", excluded=exclusions)
    assert len(error.decision["excluded_candidates"]) == 10
    assert error.decision["temporary_resource_blocked"] is True and error.decision["retry_at"] == 1234
    pinned = ModelSelectionError("pinned_model_unavailable", excluded=exclusions, pin="0")
    assert "temporary_resource_blocked" not in pinned.decision


def test_native_recovery_uses_frozen_launch_base_not_a_new_repository_head(launch, monkeypatch):
    case = launch()
    original = case.goals.task_resolver
    def native(plan, **kwargs):
        return dict(original(plan, **kwargs), executor_kind="codex", binding_ref="native")
    case.goals.task_resolver = native
    case.state["available"] = True
    case.clock[0] += 61
    monkeypatch.setattr(module, "repository_base", lambda repository: (_ for _ in ()).throw(AssertionError("live HEAD read")))
    [recovered] = case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert recovered == task(case).id
    assert task(case).executor_kind == "codex" and task(case).branch == BASE


def test_external_authority_revocation_is_evaluated_inside_the_write_transaction(launch, monkeypatch):
    case = launch()
    case.state["available"] = True
    case.clock[0] += 61
    original = case.goals.task_resolver
    def select_then_revoke(plan, **kwargs):
        result = original(plan, **kwargs)
        case.autonomy.require_trusted_policy = True
        return result
    case.goals.task_resolver = select_then_revoke
    checked = []
    def revoked():
        checked.append(case.store._conn.in_transaction)
        raise TaskStoreError("authority_revoked")
    monkeypatch.setattr(case.autonomy, "_authority", revoked)
    assert case.coordinator.tick() == 0
    assert checked == [True]
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert case.control.get_window(case.window.id).tasks_started == 0


def test_stop_during_resolver_io_prevents_committing_the_choice(launch):
    case = launch()
    original = case.goals.task_resolver
    def stopped(plan, **kwargs):
        result = original(plan, **kwargs)
        case.control.stop_window(case.window.id)
        return result
    case.goals.task_resolver = stopped
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""


def test_a_new_failure_event_during_resolution_invalidates_the_compare_and_set(launch):
    case = launch()
    original = case.goals.task_resolver
    def changed(plan, **kwargs):
        result = original(plan, **kwargs)
        current = task(case)
        case.store.add_event(current.id, event_type="MODEL_SELECTION_FAILED", title="newer wait",
            description=current.failure_classification, metadata=json.loads(current.failure_detail))
        return result
    case.goals.task_resolver = changed
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert not any(event.type == "MODEL_SELECTED" for event in case.store.get_events(task(case).id))


def test_changed_frozen_author_snapshot_cannot_choose_a_stale_reviewer(launch):
    case = launch([dict(id="A", title="author", instruction="write"),
                   dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"})])
    original = case.goals.task_resolver
    def changed(plan, **kwargs):
        result = original(plan, **kwargs)
        if plan.id == "R":
            case.store.add_event(task(case, "A").id, event_type="MODEL_SELECTED", title="new identity",
                description="fixture", metadata={"model_id": "gamma", "binding_ref": "writer"})
        return result
    case.goals.task_resolver = changed
    case.state["available"] = True
    case.clock[0] += 61
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert task(case, "R").status == "BLOCKED" and task(case, "R").binding_ref == ""
    assert case.control.get_goal(case.goal.id).status == "BLOCKED"


def test_unknown_author_usage_does_not_become_permission_to_activate_review(launch):
    case = launch([dict(id="A", title="author", instruction="write"),
                   dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"})])
    case.state["available"] = True
    case.clock[0] += 61
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy, limit=1)
    author = task(case, "A")
    case.store.append_usage_observation(author.id, observation_id="unknown-author", execution_id=author.execution_id,
        role="executor", model_id="alpha", provider_id="", source_kind="fixture", source_id="u", status="UNKNOWN")
    before = len(case.calls)
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert task(case, "R").status == "BLOCKED" and len(case.calls) == before
    assert case.store.list_usage_observations(author.id)[0].status == "UNKNOWN"


def test_delegated_admission_uses_the_hosts_existing_goal_service(launch, monkeypatch):
    case = launch()
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED")
    monkeypatch.setattr(type(case.autonomy), "delegated_mode", property(lambda self: True))
    case.store._conn.execute("UPDATE platform_autonomous_windows SET capabilities_json=? WHERE id=?",
        (json.dumps(["execute_task", "validate_task", "approve_goal"]), case.window.id))
    seen = []
    monkeypatch.setattr(case.autonomy, "admit_goals", lambda service, **kwargs: seen.append(service))
    case.coordinator.tick()
    assert seen == [case.goals]


def test_two_independent_store_connections_cannot_reactivate_twice(launch, tmp_path):
    import sqlite3
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    case = launch()
    path = tmp_path / "race.sqlite3"
    copy = sqlite3.connect(str(path))
    case.store._conn.backup(copy)
    copy.close()
    case.state["available"] = True
    case.clock[0] += 61
    barrier = threading.Barrier(2)
    actors = []
    for _ in range(2):
        store = TaskStore(str(path))
        control = PlatformControlStore(store)
        autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
        def resolve(plan, **kwargs):
            result = case.resolve(plan, **kwargs)
            barrier.wait(3)
            return result
        goals = module.GoalService(store=store, control_store=control, task_resolver=resolve)
        actors.append((store, goals, autonomy))
    try:
        def recover(actor):
            return actor[1].reconsider_initial_models(case.window.id, autonomy=actor[2])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(recover, actors))
        assert sum(len(result) for result in results) == 1
        current = actors[0][0].get_task(task(case).id)
        assert current.status == "QUEUED" and current.execution_id == task(case).execution_id
        assert len([event for event in actors[0][0].get_events(current.id) if event.type == "MODEL_SELECTED"]) == 1
    finally:
        for store, _, _ in actors:
            store._conn.close()


@pytest.mark.parametrize("field,value", [("workspace", "previous-worktree"), ("model_profile_ref", "previous-profile"),
    ("validation_command_id", "previous-check"), ("validation_exit_code", 0), ("validation_output_digest", "previous-output")])
def test_prior_preparation_or_validation_fields_are_not_reset(launch, field, value):
    case = launch()
    case.store._conn.execute(f"UPDATE tasks SET {field}=? WHERE id=?", (value, task(case).id))
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and getattr(task(case), field) == value
    assert len(case.calls) == 1


def test_disabling_the_feature_does_not_reactivate_marked_tasks(launch, monkeypatch):
    case = launch()
    case.state["available"] = True
    case.clock[0] += 61
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED")
    assert case.coordinator.tick() == 0 and len(case.calls) == 1
    assert task(case).status == "BLOCKED"


def test_a_raised_selection_error_cannot_smuggle_a_successful_binding(launch):
    case = launch()
    def failed(*args, **kwargs):
        error = TaskStoreError("no_willing_model")
        error.decision = {"reason": "no_willing_model", "binding_ref": "forbidden",
                          "executor_kind": "opencode", "model_id": "forbidden-model"}
        raise error
    case.goals.task_resolver = failed
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert task(case).failure_classification == "no_willing_model"
    assert not any(event.type == "MODEL_SELECTED" for event in case.store.get_events(task(case).id))


@pytest.mark.parametrize("error", [TaskStoreError("fixture-private-error"), RuntimeError("fixture-private-error")])
def test_unexpected_adapter_errors_park_with_a_finite_reason(launch, error):
    case = launch()
    def failed(*args, **kwargs):
        raise error
    case.goals.task_resolver = failed
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    current = task(case)
    assert current.failure_classification == "initial_selection_resolver_error"
    assert "fixture-private-error" not in current.failure_detail
    assert "initial_resource_wait" not in json.loads(current.failure_detail)


def test_contract_base_cannot_be_overridden_by_changing_only_the_wait_marker(launch):
    case = launch([dict(id="A", title="author", instruction="write"),
                   dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"})])
    current = task(case, "A")
    altered = json.loads(current.failure_detail)
    altered["initial_resource_wait"]["base_commit"] = "b" * 40
    case.store._conn.execute("UPDATE tasks SET branch=?,failure_detail=? WHERE id=?", ("b" * 40, json.dumps(altered), current.id))
    case.store._conn.execute("UPDATE task_events SET metadata=? WHERE task_id=? AND type='MODEL_SELECTION_FAILED'",
        (json.dumps(altered), current.id))
    case.state["available"] = True
    case.clock[0] += 61
    assert case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy) == ()
    assert task(case, "A").status == "BLOCKED" and task(case, "R").status == "BLOCKED"


def test_real_delegated_checker_admission_retains_configured_service_and_zero_probe_intent(tmp_path, monkeypatch):
    from tests.platform_v1.test_delegated_goal_admission import system
    store, control, goals, autonomy, authority, coordinator = system(tmp_path, monkeypatch, count=1)
    coordinator.goals = goals
    calls = []
    original = goals._launch
    def tracked(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)
    monkeypatch.setattr(goals, "_launch", tracked)
    try:
        assert coordinator.tick() == 1
        assert len(calls) == 1 and calls[0]["probe_availability"] is False
        assert control.get_window("admission-window").tasks_started == 1
        assert control.get_window("admission-window").unknown_observation_count == 0
    finally:
        store._conn.close()


@pytest.mark.parametrize("bad", [None, {}, {"version": True}, {"version": 2}, {"retry_at": float("nan")}, {"task_id": "other"}])
def test_invalid_marker_never_becomes_authority_to_queue_work(launch, bad):
    case = launch()
    current = task(case)
    decision = json.loads(current.failure_detail)
    decision["initial_resource_wait"] = bad if bad is None or not bad else {
        **decision["initial_resource_wait"], **bad}
    case.store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (json.dumps(decision), current.id))
    case.store._conn.execute("UPDATE task_events SET metadata=? WHERE task_id=? AND type='MODEL_SELECTION_FAILED'",
        (json.dumps(decision), current.id))
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert len(case.calls) == 1 and task(case).status == "BLOCKED"


def test_an_execution_identity_change_during_resolution_is_not_overwritten(launch):
    case = launch()
    original = case.goals.task_resolver
    def changed(plan, **kwargs):
        result = original(plan, **kwargs)
        case.store._conn.execute("UPDATE tasks SET execution_id='new-identity' WHERE id=?", (task(case).id,))
        return result
    case.goals.task_resolver = changed
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).execution_id == "new-identity"


def test_same_model_author_version_change_still_invalidates_the_snapshot(launch):
    case = launch([dict(id="A", title="author", instruction="write"),
                   dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"})])
    original = case.goals.task_resolver
    def changed(plan, **kwargs):
        result = original(plan, **kwargs)
        if plan.id == "R":
            assert "_initial_author_snapshot" not in kwargs
            case.store.add_event(task(case, "A").id, event_type="MODEL_SELECTED", title="same model new version",
                description="fixture", metadata={"model_id": "alpha", "binding_ref": "writer"})
        return result
    case.goals.task_resolver = changed
    case.state["available"] = True
    case.clock[0] += 61
    case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy)
    assert task(case, "R").status == "BLOCKED" and task(case, "R").binding_ref == ""


def test_selection_event_failure_rolls_back_task_goal_and_authorization_receipt(launch, monkeypatch):
    case = launch()
    original = case.store._append_event
    fail = [True]
    def persist(**kwargs):
        if kwargs["event_type"] == "MODEL_SELECTED" and fail[0]:
            raise TaskStoreError("fixture_event_failure")
        return original(**kwargs)
    monkeypatch.setattr(case.store, "_append_event", persist)
    case.state["available"] = True
    case.clock[0] += 61
    receipts = len(case.control.list_receipts(window_id=case.window.id))
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert case.control.get_goal(case.goal.id).status == "BLOCKED"
    assert len(case.control.list_receipts(window_id=case.window.id)) == receipts
    fail[0] = False
    assert case.coordinator.tick() == 1 and case.executed == [task(case).id]


@pytest.mark.parametrize("invalid", [None, {}, {"binding_ref": " "}, {"model_id": ""}, {"reason": None}, {"executor_kind": "unsupported"}])
def test_malformed_successful_routes_park_without_dispatch(launch, invalid):
    case = launch()
    original = case.goals.task_resolver
    def changed(plan, **kwargs):
        valid = original(plan, **kwargs)
        return invalid if invalid is None or not invalid else {**valid, **invalid}
    case.goals.task_resolver = changed
    case.state["available"] = True
    case.clock[0] += 61
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).failure_classification == "initial_selection_route_invalid"


def test_an_unmarked_idle_goal_does_not_load_policy_or_probe_routes(launch, monkeypatch):
    case = launch()
    case.store._conn.execute("UPDATE tasks SET failure_detail='{}' WHERE id=?", (task(case).id,))
    loaded = []
    monkeypatch.setattr(case.autonomy, "_check_window_authority", lambda window_id: loaded.append(window_id))
    case.clock[0] += 100
    assert case.coordinator.tick() == 0 and loaded == [] and len(case.calls) == 1


def test_recursive_author_recovery_obeys_the_same_resolver_limit(launch):
    case = launch([dict(id="R", title="review", instruction="review", kind="review", dependencies=["A"],
                        artifact_input={"plan_task_id": "A"}),
                   dict(id="A", title="author", instruction="write")])
    case.state["available"] = True
    case.clock[0] += 61
    before = len(case.calls)
    first = case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy, limit=1)
    assert first == (task(case, "A").id,) and len(case.calls) == before + 1
    assert task(case, "R").status == "BLOCKED"
    second = case.goals.reconsider_initial_models(case.window.id, autonomy=case.autonomy, limit=1)
    assert second == (task(case, "R").id,) and len(case.calls) == before + 2
    assert case.control.get_goal(case.goal.id).status == "RUNNING"


def test_expiry_after_authorization_still_rolls_back_the_candidate(launch, monkeypatch):
    import threading
    case = launch()
    case.state["available"] = True
    case.clock[0] += 61
    deadline = datetime.now(timezone.utc) + timedelta(seconds=1)
    case.store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?", (deadline.isoformat(), case.window.id))
    original = case.autonomy.authorize
    def delayed(**kwargs):
        allowed = original(**kwargs)
        assert allowed
        threading.Event().wait(1.1)
        return allowed
    monkeypatch.setattr(case.autonomy, "authorize", delayed)
    assert case.coordinator.tick() == 0
    assert task(case).status == "BLOCKED" and task(case).binding_ref == ""
    assert case.control.get_window(case.window.id).tasks_started == 0
