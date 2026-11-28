"""A quota-held task can move to another dispatchable binding at its task floor."""
import json

import pytest

from test_agent_escalation import _launched, _link
from reverse_agent.platform_v1.run_store import TaskStoreError


def _hold(store, control, task_id, *, binding="codex-bind", tier=4):
    store._conn.execute("UPDATE tasks SET binding_ref=?, executor_kind='codex' WHERE id=?", (binding, task_id))
    store._conn.execute(
        "INSERT OR REPLACE INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,need_json,"
        "small_task,safety_buffer,verdict_json) VALUES (?,?,?,?,?,?,?,?)",
        (task_id, binding, "acct", "{}", "{}", 0, 10,
         json.dumps({"decision": "quota_wait", "reason": "quota_capacity", "until": "2026-10-21T09:16:37Z"})))
    store._conn.commit()
    store.add_event(task_id, event_type="MODEL_SELECTED", title="Model selected", description=binding,
                    metadata={"binding_ref": binding, "tier": tier, "model_id": "gpt-6.1-sol", "reason": "cheapest"})


def _resolver(choice, calls):
    def resolve(plan_task, *, goal, quota_held_binding="", **kwargs):
        calls.append((plan_task.id, quota_held_binding, plan_task.difficulty, kwargs))
        if isinstance(choice, Exception):
            raise choice
        return dict(choice)
    return resolve


ALTERNATIVE = {"binding_ref": "kimi-bind", "executor_kind": "opencode", "model_id": "kimi-k3", "tier": 4,
               "reason": "retry_different_model", "context_window": 256000}


def test_held_task_moves_once_to_a_model_meeting_the_task_floor(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch, role="coder")
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id, tier=5)
    calls = []
    goals.task_resolver = _resolver(ALTERNATIVE, calls)
    [moved] = goals.escalate_failed_tasks(goal.id)
    assert moved["reason"] == "quota_hold_reroute" and moved["to_binding"] == "kimi-bind"
    assert calls == [("T001", "codex-bind", 3, {"probe_availability": False, "quota_preferred_tier": 5})]
    task = store.get_task(task_id)
    assert (task.binding_ref, task.executor_kind, task.status) == ("kimi-bind", "opencode", "QUEUED")
    assert control.quota_hold(task_id) is None  # stale admission for the old binding is gone
    latest = [e for e in store.get_events(task_id) if e.type == "MODEL_SELECTED"][-1]
    assert latest.metadata["binding_ref"] == "kimi-bind" and latest.metadata["reroute_reason"] == "quota_hold"
    assert (latest.metadata["held_tier"], latest.metadata["required_tier"]) == (5, 3)
    assert control.list_task_escalations(goal.id) == ()  # not a retry: no budget spent
    # A second hold on the new model never flips the task back.
    _hold(store, control, task_id, binding="kimi-bind", tier=4)
    assert goals.escalate_failed_tasks(goal.id) == ()


@pytest.mark.parametrize("choice", [
    dict(ALTERNATIVE, binding_ref="codex-bind"),                                 # only the held model
    dict(ALTERNATIVE, tier=2),                                                    # below the task floor
    dict(ALTERNATIVE, liveness={"fallback": True}),
    TaskStoreError("no_runnable_model"),
])
def test_held_task_waits_without_a_qualifying_alternative(monkeypatch, choice):
    store, control, goals, goal = _launched(monkeypatch, role="coder")
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(choice, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"
    assert control.quota_hold(task_id) is not None


def test_replay_1805_aligns_task_traits_claim_and_quota_reroute(monkeypatch, tmp_path):
    from test_model_router import fixture_host

    checks = [{"profile_id": "python_pytest", "working_directory": ".", "targets": ["tests/test_x.py"]}]
    store, control, goals, created = _launched(monkeypatch, role="coder", checks=checks,
        roster={"coder": ("claude_code", "strong"), "simple": ("opencode", "cheap")})
    goal = control.get_goal(created.id)
    host = fixture_host(monkeypatch, tmp_path)
    host._task_store, host._control_store = store, control
    goals.task_resolver = host._resolve_task_model
    task = store.get_task(_link(control, goal.id, "T001")["task_id"])
    planned = goals._normalize_task(goal.tasks[0], seq=0)

    # #1805 used a tier-5 native route for a tier-3 task, then reached claim
    # with both quota windows unknown. Rebuild that state without provider calls.
    first = host._resolve_task_model(planned, goal=goal, probe_availability=False)
    assert first["binding_ref"] == task.binding_ref == "strong"
    assert (first["difficulty"], first["tier"]) == (3, 5)
    goals._record_model_selection(task, first)
    host._prepare_task_quota(task)
    estimate = store._conn.execute("SELECT need_json FROM platform_quota_admissions WHERE task_id=?", (task.id,)).fetchone()
    assert json.loads(estimate[0])["estimate"]["difficulty"] == "3"
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:unknown_reset"):
        control.claim_task(window_id=goal.window_id, task_id=task.id, owner="fixture", lease_ms=60_000)
    hold = control.quota_hold(task.id)
    assert hold == first["quota_admission"]
    assert hold["state"] == "UNKNOWN" and hold["blocking_windows"] == ["five_hour", "weekly"]
    assert not goals.reroute_quota_held(goal.id)  # existing weaker routes cannot satisfy the task

    host._store.upsert_binding({"binding_id": "mid", "name": "Alternative", "executor_id": "opencode",
        "connection_id": "free-api", "model_id": "kimi-k3", "enabled": True})
    assert host._resolve_task_model(planned, goal=goal, probe_availability=False)["binding_ref"] == "mid"
    [moved] = goals.reroute_quota_held(goal.id)
    assert moved["task_id"] == task.id and moved["to_binding"] == "mid"
    assert store.get_task(task.id).status == "QUEUED"
    assert control.quota_hold(task.id) is None
    with pytest.raises(TaskStoreError, match="quota_reservation_identity_changed"):
        control.claim_task(window_id=goal.window_id, task_id=task.id, owner="fixture", lease_ms=60_000,
                           expected_binding=task.binding_ref)  # delayed claim of the previous binding
    with pytest.raises(TaskStoreError, match="quota_reservation_identity_changed"):
        host._prepare_task_quota(task)  # delayed preparation of the previous binding
    assert not control.quota_reservations()
    assert store._conn.execute("SELECT COUNT(*) FROM platform_coordinator_claims WHERE task_id=?", (task.id,)).fetchone()[0] == 0


def test_started_or_unheld_or_unselected_tasks_are_never_moved(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    calls = []
    goals.task_resolver = _resolver(ALTERNATIVE, calls)
    assert goals.escalate_failed_tasks(goal.id) == () and calls == []  # no hold
    _hold(store, control, task_id)
    store._conn.execute("DELETE FROM task_events WHERE task_id=? AND type='MODEL_SELECTED'", (task_id,))
    store._conn.commit()
    assert goals.escalate_failed_tasks(goal.id) == () and calls == []  # no recorded selection
    _hold(store, control, task_id)
    store._conn.execute("INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_epoch, "
                        "lease_expiry_ms, created_at, updated_at) VALUES ('run-x', ?, 'e', 'w', 1, 1, 'x', 'x')",
                        (task_id,))
    store._conn.commit()
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"


def test_another_binding_of_the_held_model_is_not_a_move(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    same = dict(ALTERNATIVE, binding_ref="codex-via-magpie", model_id="codex/gpt-6.1-sol", tier=4)
    goals.task_resolver = _resolver(same, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    # Not marked as rerouted: a genuinely different model can still be chosen later.
    goals.task_resolver = _resolver(ALTERNATIVE, [])
    [moved] = goals.escalate_failed_tasks(goal.id)
    assert moved["to_binding"] == "kimi-bind"


def test_native_target_needs_an_exact_launch_base(monkeypatch):
    native = dict(ALTERNATIVE, binding_ref="claude-bind", executor_kind="claude_code", model_id="claude-opus", tier=5)
    store, control, goals, goal = _launched(monkeypatch)  # no checks: launch froze no base
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(native, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"
    checks = [{"profile_id": "python_pytest", "working_directory": ".", "targets": ["tests/test_x.py"]}]
    store, control, goals, goal = _launched(monkeypatch, checks=checks)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(native, [])
    [moved] = goals.escalate_failed_tasks(goal.id)
    task = store.get_task(task_id)
    assert moved["to_binding"] == "claude-bind" and task.executor_kind == "claude_code" and len(task.branch) == 40


def test_coordinator_offers_fully_held_goals_to_the_rerouter(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    store, control, goals, goal = _launched(monkeypatch)
    rerouted = []
    def held(task):
        raise TaskStoreError("QUOTA_WAIT:2026-10-21T09:16:37Z")
    coordinator = UnattendedCoordinator(store=store, control_store=control,
        autonomy=SimpleNamespace(authorize=lambda **kwargs: True), router=SimpleNamespace(),
        workspace_root=tmp_path, quota_preparer=held, quota_rerouter=rerouted.append)
    assert coordinator.tick() == 0
    assert rerouted == [goal.id]


# --- #1596: liveness cool-down on a stalled binding, derived from its attempt rows -------

from datetime import datetime, timezone  # noqa: E402

from reverse_agent.platform_v1 import quota_guard  # noqa: E402

NOW = 1_800_000_000.0
MIN = 60


def _stall(at):
    return {"status": "FAILED", "failure_classification": "executor_stalled", "at": at}


def _ok(at):
    return {"status": "READY_FOR_REVIEW", "failure_classification": "", "at": at}


def test_one_stall_cools_the_binding_down_for_the_base_time_then_expires():
    hold = quota_guard.liveness_cooldown([_stall(NOW - 5 * MIN)], now=NOW)
    assert hold["reason"] == "liveness_cooldown" and hold["stalls"] == 1
    assert hold["seconds"] == quota_guard.LIVENESS_COOLDOWN_SECONDS == 15 * MIN
    assert hold["until"] == NOW + 10 * MIN
    assert quota_guard.liveness_cooldown([_stall(NOW - 5 * MIN)], now=NOW + 10 * MIN) is None  # expired


def test_repeated_stalls_lengthen_the_cooldown_up_to_the_cap():
    seconds = [quota_guard.liveness_cooldown([_stall(NOW - i) for i in range(n)], now=NOW)["seconds"]
               for n in range(1, 7)]
    assert seconds == [15 * MIN, 30 * MIN, 60 * MIN, 120 * MIN, 120 * MIN, 120 * MIN]
    assert quota_guard.LIVENESS_COOLDOWN_MAX_SECONDS == 120 * MIN


def test_a_success_clears_earlier_stalls_and_other_failures_do_not_count():
    assert quota_guard.liveness_cooldown([_ok(NOW - MIN), _stall(NOW - 2 * MIN)], now=NOW) is None
    # A stall after the success counts alone; the stalls before it are cleared.
    hold = quota_guard.liveness_cooldown([_stall(NOW - MIN), _ok(NOW - 2 * MIN), _stall(NOW - 3 * MIN)], now=NOW)
    assert hold["stalls"] == 1
    other = {"status": "FAILED", "failure_classification": "deterministic_validation_failure", "at": NOW - MIN}
    assert quota_guard.liveness_cooldown([other], now=NOW) is None
    assert quota_guard.liveness_cooldown([other, _stall(NOW - 2 * MIN)], now=NOW)["stalls"] == 1
    # Stalls older than the look-back are history, not a reason to grow the cool-down.
    old = NOW - quota_guard.LIVENESS_LOOKBACK_SECONDS - 1
    assert quota_guard.liveness_cooldown([_stall(NOW - MIN), _stall(old)], now=NOW)["stalls"] == 1


def _iso(at):
    return datetime.fromtimestamp(at, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_host_hold_comes_from_task_rows_and_routes_other_goals_away(monkeypatch, tmp_path):
    """No second ledger: the hold is read from the binding's attempts, like a limit-hit hold."""
    from test_model_router import fixture_host
    from reverse_agent.platform_v1 import trusted_host
    from reverse_agent.platform_v1.goal_service import PlannedTask
    from reverse_agent.platform_v1.run_store import TaskStore
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.delattr(host, "_quota_check")  # the real check, with the real hold
    monkeypatch.setattr(host, "_limit_hit_until", lambda connection, binding=None: None)
    host._task_store = TaskStore(":memory:")
    clock = {"now": NOW}
    monkeypatch.setattr(trusted_host.time, "time", lambda: clock["now"])

    def attempt(binding, status, classification, at):
        task = host._task_store.create_task(title="attempt", binding_ref=binding, executor_kind="opencode")
        host._task_store._conn.execute(
            "UPDATE tasks SET status=?, failure_classification=?, updated_at=? WHERE id=?",
            (status, classification, _iso(at), task.id))
        host._task_store._conn.commit()

    task = PlannedTask("T009", "another goal", "i", difficulty=2)
    assert host._resolve_task_model(task)["binding_ref"] == "cheap"
    attempt("cheap", "FAILED", "executor_stalled", NOW - MIN)
    verdict = host._quota_check(host._store.get_binding_public("cheap"))
    assert verdict["decision"] == "switch" and verdict["reason"] == "liveness_cooldown"
    assert verdict["until"] == _iso(NOW - MIN + 15 * MIN) and verdict["stalls"] == 1
    # Another goal now avoids the cooling binding and the decision records why.
    result = host._resolve_task_model(task)
    assert result["binding_ref"] != "cheap"
    assert any(row["binding_id"] == "cheap" and row["filter"] == "liveness_cooldown"
               for row in result["excluded_candidates"])
    # It expires on the fake clock ...
    clock["now"] = NOW + 15 * MIN
    assert host._quota_check(host._store.get_binding_public("cheap")) is None
    assert host._resolve_task_model(task)["binding_ref"] == "cheap"
    # ... and a successful attempt on the binding clears a fresh one at once.
    attempt("cheap", "FAILED", "executor_stalled", NOW + 15 * MIN)
    assert host._quota_check(host._store.get_binding_public("cheap"))["reason"] == "liveness_cooldown"
    attempt("cheap", "READY_FOR_REVIEW", "", NOW + 15 * MIN + 1)
    clock["now"] = NOW + 15 * MIN + 2
    assert host._quota_check(host._store.get_binding_public("cheap")) is None


def _stall_host(monkeypatch, tmp_path):
    from test_model_router import fixture_host
    from reverse_agent.platform_v1 import trusted_host
    from reverse_agent.platform_v1.run_store import TaskStore
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.delattr(host, "_quota_check")
    monkeypatch.setattr(host, "_limit_hit_until", lambda connection, binding=None: None)
    host._task_store = TaskStore(":memory:")
    monkeypatch.setattr(trusted_host.time, "time", lambda: NOW)

    def attempt(binding, status="FAILED", classification="executor_stalled", at=NOW - MIN):
        task = host._task_store.create_task(title="attempt", binding_ref=binding, executor_kind="opencode")
        host._task_store._conn.execute("UPDATE tasks SET status=?, failure_classification=?, updated_at=? WHERE id=?",
                                       (status, classification, _iso(at), task.id))
        host._task_store._conn.commit()
    return host, attempt


def test_a_cooldown_never_masks_real_quota_exhaustion(monkeypatch, tmp_path):
    from reverse_agent.platform_v1.goal_service import PlannedTask
    host, attempt = _stall_host(monkeypatch, tmp_path)
    verdicts = {"cheap": {"decision": "switch", "reason": "observed_exhausted", "provider": "fixture", "window": "5h"}}
    monkeypatch.setattr(quota_guard, "check", lambda connection, quotas, need: verdicts.get("current"))
    binding = host._store.get_binding_public("cheap")
    attempt("cheap")
    verdicts["current"] = verdicts["cheap"]
    exhausted = host._quota_check(binding)
    assert exhausted["reason"] == "observed_exhausted"  # exactly the verdict main returns, stall or not
    # Router: excluded as exhausted, never offered as a cooling fallback.
    monkeypatch.setattr(host, "_quota_check", lambda b: exhausted if b["binding_id"] == "cheap" else None)
    result = host._resolve_task_model(PlannedTask("T001", "t", "i", difficulty=2))
    assert result["binding_ref"] != "cheap"
    assert any(row["binding_id"] == "cheap" and row["filter"] == "quota_exhausted"
               for row in result["excluded_candidates"])
    # Role guard: still refuses with no alternative instead of warning and running.
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap"})
    with pytest.raises(TaskStoreError, match="quota_exhausted:observed_exhausted:no_alternative"):
        host._quota_guarded("simple", "opencode", "cheap", {})
    monkeypatch.undo()
    # Only an ok/warn account verdict is replaced by the cool-down, which keeps it.
    host, attempt = _stall_host(monkeypatch, tmp_path)
    attempt("cheap")
    warn = {"decision": "warn", "reason": "pessimistic_insufficient", "window": "weekly"}
    monkeypatch.setattr(quota_guard, "check", lambda connection, quotas, need: warn)
    cooling = host._quota_check(host._store.get_binding_public("cheap"))
    assert cooling["reason"] == "liveness_cooldown" and cooling["quota_verdict"]["reason"] == "pessimistic_insufficient"


def test_a_stall_cools_its_whole_upstream_like_a_limit_hit_hold(monkeypatch, tmp_path):
    host, attempt = _stall_host(monkeypatch, tmp_path)
    gateway = {"connection_id": "magpie", "base_url": "http://127.0.0.1:3425/v1"}
    account = {"connection_id": "acct-a", "base_url": "https://a.invalid", "account_ref": "team"}
    account_b = {"connection_id": "acct-b", "base_url": "https://b.invalid", "account_ref": "team"}
    bindings = [{"binding_id": "m3", "connection_id": "magpie", "model_id": "minimax/m3"},
                {"binding_id": "m3-fast", "connection_id": "magpie", "model_id": "minimax/m3-fast"},
                {"binding_id": "glm", "connection_id": "magpie", "model_id": "zai/glm-5.3"},
                {"binding_id": "a1", "connection_id": "acct-a", "model_id": "x"},
                {"binding_id": "b1", "connection_id": "acct-b", "model_id": "y"}]
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE_URL", raising=False)
    monkeypatch.setattr(host._store, "list_connections_public", lambda: [gateway, account, account_b])
    monkeypatch.setattr(host._store, "list_bindings_public", lambda: bindings)
    attempt("m3")
    attempt("a1")
    cooled = {b["binding_id"] for b in bindings if host._liveness_cooldown(b)}
    # Siblings on the stalled gateway upstream and on the stalled account cool too; other upstreams do not.
    assert cooled == {"m3", "m3-fast", "a1", "b1"}
    assert host._liveness_cooldown(bindings[1])["upstream"] == "gateway:magpie:minimax"
    # A success on any binding of that upstream clears it.
    attempt("m3-fast", status="READY_FOR_REVIEW", classification="", at=NOW - 1)
    assert host._liveness_cooldown(bindings[0]) is None


def test_a_stall_on_one_magpie_group_cools_no_other_group_or_binding(monkeypatch, tmp_path):
    """Owner decision 2026-11-17: each group/* id is its own upstream on the gateway."""
    host, attempt = _stall_host(monkeypatch, tmp_path)
    gateway = {"connection_id": "magpie", "base_url": "http://127.0.0.1:3425/v1", "auth_method": "none"}
    bindings = [{"binding_id": "g-glm", "connection_id": "magpie", "model_id": "group/nerelan-glm-5-3"},
                {"binding_id": "g-kimi", "connection_id": "magpie", "model_id": "group/nerelan-kimi"},
                {"binding_id": "glm", "connection_id": "magpie", "model_id": "trae-cn/glm-5.3"}]
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE_URL", raising=False)
    monkeypatch.setattr(host._store, "list_connections_public", lambda: [gateway])
    monkeypatch.setattr(host._store, "list_bindings_public", lambda: bindings)
    attempt("g-glm")
    assert {b["binding_id"] for b in bindings if host._liveness_cooldown(b)} == {"g-glm"}
    assert host._liveness_cooldown(bindings[0])["upstream"] == "gateway:magpie:group:nerelan-glm-5-3"


def test_cooldown_reads_the_task_table_once_per_routing_pass(monkeypatch, tmp_path):
    """~170 bindings and ~20k task rows: one indexed query, well under 250 ms."""
    import time as real_time
    host, _ = _stall_host(monkeypatch, tmp_path)
    connections = [{"connection_id": f"c{i}", "base_url": f"https://{i}.invalid"} for i in range(17)]
    bindings = [{"binding_id": f"b{i}", "connection_id": f"c{i % 17}", "model_id": f"m{i}"} for i in range(170)]
    monkeypatch.setattr(host._store, "list_connections_public", lambda: connections)
    monkeypatch.setattr(host._store, "list_bindings_public", lambda: bindings)
    conn = host._task_store._conn
    template = conn.execute("SELECT * FROM tasks LIMIT 0").description
    columns = [d[0] for d in template]
    seed = host._task_store.create_task(title="seed", binding_ref="b0", executor_kind="opencode")
    row = dict(zip(columns, conn.execute("SELECT * FROM tasks WHERE id=?", (seed.id,)).fetchone()))
    rows = []
    for i in range(20_000):
        recent = i % 10 == 0  # most history is older than the look-back
        rows.append(tuple({**row, "id": f"t{i}", "execution_id": f"e{i}", "idempotency_key": f"k{i}",
                           "binding_ref": f"b{i % 170}", "status": "FAILED" if i % 50 else "READY_FOR_REVIEW",
                           "failure_classification": "executor_stalled" if i % 50 else "",
                           "updated_at": _iso(NOW - (i % 600) * 60 - (0 if i % 50 else 43200) if recent
                                             else NOW - 3 * 86400 - i)}[c]
                          for c in columns))
    conn.executemany(f"INSERT INTO tasks ({','.join(columns)}) VALUES ({','.join('?' * len(columns))})", rows)
    conn.commit()
    assert {r[1] for r in conn.execute("PRAGMA index_list(tasks)")} >= {"idx_tasks_binding_updated", "idx_tasks_updated"}
    queries = []
    conn.set_trace_callback(lambda sql: queries.append(sql) if "FROM tasks" in sql else None)
    try:
        started = real_time.perf_counter()
        holds = [host._liveness_cooldown(b) for b in bindings]
        elapsed = real_time.perf_counter() - started
    finally:
        conn.set_trace_callback(None)
    assert len(queries) == 1
    assert elapsed < .25, elapsed  # generous for shared CI; the one-query assertion is the guard
    assert len(holds) == 170 and any(holds)
    plan = " ".join(str(r[-1]) for r in conn.execute(
        "EXPLAIN QUERY PLAN SELECT binding_ref FROM tasks WHERE updated_at >= 'x' "
        "AND status IN ('FAILED', 'READY_FOR_REVIEW') AND binding_ref != ''"))
    assert "idx_tasks_updated" in plan


@pytest.mark.parametrize("classification", ["model_review_abandoned_no_reply", "api_error_429",
                                            "server_session_error", "network_provider_failure"])
def test_a_route_fault_cools_the_pool_down_like_a_stall(classification):
    # #1533: a pool that did not serve the attempt is avoided for a while, so
    # routing stops choosing a free pool that keeps failing.
    fault = {"status": "FAILED", "failure_classification": classification, "at": NOW - MIN}
    hold = quota_guard.liveness_cooldown([fault], now=NOW)
    assert hold is not None and hold["stalls"] == 1
    assert quota_guard.liveness_cooldown([_ok(NOW), fault], now=NOW) is None
    # Stall-specific retry rules keep their own, narrower set.
    assert classification not in quota_guard.LIVENESS_STALL_CLASSES
