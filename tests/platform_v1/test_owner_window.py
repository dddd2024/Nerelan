"""Owner-confirmed multi-Goal windows. Provider-free: no server, model or dispatch."""
from __future__ import annotations

import io
import json
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import durable_execution, goal_service, owner_window
from reverse_agent.platform_v1.binding_resolver import BindingResolver
from reverse_agent.platform_v1.control_store import OWNER_LANDING_CAPABILITY, OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
from reverse_agent.platform_v1.durable_execution import ExecutorRuntimeError, _require_owner_window_pool
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

ALL = ("execute_task", "resume_task", "reconcile_task", "validate_task")
WITH_LANDING = (*ALL, "open_draft_pr", OWNER_LANDING_CAPABILITY)


class TestContinuousRun:
    def start(self, setup, *goals):
        return admit(setup.host, tuple(g.id for g in goals), continuous=True,
                     hours=0, max_tasks=0, max_token_units=0, max_concurrent=3)[0]

    def test_no_expiry_or_task_token_stop_and_usage_remains_recorded(self, setup):
        goal = setup.planned("long", "codex", "pinned", tasks=13)
        window = self.start(setup, goal)
        control = setup.host._control_store
        assert window.continuous and window.expires_at == "" and window.max_tasks == 0
        assert control.active_window(now="2099-01-01T00:00:00Z").id == window.id
        setup.db._conn.execute("UPDATE platform_autonomous_windows SET tasks_started=12, observed_token_units=90000000 WHERE id=?", (window.id,))
        last = control.list_goal_tasks(goal.id)[-1]["task_id"]
        epoch, claimed = control.claim_task(window_id=window.id, task_id=last, owner="test", lease_ms=1000)
        assert epoch == 1 and claimed.tasks_started == 13 and claimed.observed_token_units == 90000000

    def test_append_goal_preserves_running_claim_and_window_counters(self, setup):
        first = setup.planned("first", "codex", "pinned")
        window = self.start(setup, first)
        control = setup.host._control_store
        task = control.list_goal_tasks(first.id)[0]["task_id"]
        control.claim_task(window_id=window.id, task_id=task, owner="test", lease_ms=10000)
        second = setup.planned("second", "codex", "pinned")
        admission = setup.host._owner_window_admission
        request = dict(hours=0, max_tasks=0, max_concurrent=3, max_retries=2, capabilities=ALL, continuous=True)
        report = admission.preflight([second.id], **request)
        assert report["ok"], report
        appended = admission.admit_from_card([second.id], card_digest=report["card_digest"], **request)
        assert appended.id == window.id and appended.tasks_started == 1
        assert control.get_goal(second.id).window_id == window.id
        assert setup.db._conn.execute("SELECT status FROM platform_coordinator_claims WHERE task_id=?", (task,)).fetchone()[0] == "ACTIVE"

    def test_stop_is_final_for_this_run(self, setup):
        first = setup.planned("stop", "codex", "pinned")
        window = self.start(setup, first)
        control = setup.host._control_store
        control.stop_window(window.id)
        assert control.active_window() is None
        task = control.list_goal_tasks(first.id)[0]["task_id"]
        with pytest.raises(TaskStoreError, match="window_not_active"):
            control.claim_task(window_id=window.id, task_id=task, owner="test", lease_ms=1000)

    def test_stale_append_card_cannot_restart_a_stopped_run(self, setup):
        first = setup.planned("first", "codex", "pinned")
        window = self.start(setup, first)
        second = setup.planned("second", "codex", "pinned")
        admission = setup.host._owner_window_admission
        request = dict(hours=0, max_tasks=0, max_concurrent=3, max_retries=2, capabilities=ALL, continuous=True)
        report = admission.preflight([second.id], **request)
        setup.host._control_store.stop_window(window.id)
        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            admission.admit_from_card([second.id], card_digest=report["card_digest"], **request)
        assert setup.host._control_store.active_window() is None

    def test_continuous_run_still_enforces_account_quota_and_concurrency(self, setup):
        goal = setup.planned("quota", "codex", "pinned", tasks=4)
        window = self.start(setup, goal)
        control = setup.host._control_store
        tasks = control.list_goal_tasks(goal.id)
        now = datetime.now(timezone.utc).timestamp()
        evidence = {"account_ref": "account", "source": "official", "observed_at": now, "state": "OBSERVED",
                    "windows": [{"window": name, "used_percent": 100, "resets_at": now + 3600}
                                for name in ("five_hour", "weekly")]}
        control.prepare_quota_admission(task_id=tasks[0]["task_id"], binding_ref="pinned", account_ref="account",
            evidence=evidence, need={"windows": {name: {"p80": 1} for name in ("five_hour", "weekly")}})
        with pytest.raises(TaskStoreError, match="QUOTA_WAIT"):
            control.claim_task(window_id=window.id, task_id=tasks[0]["task_id"], owner="test", lease_ms=10000)
        assert control.get_window(window.id).tasks_started == 0
        for task in tasks[1:]:
            control.claim_task(window_id=window.id, task_id=task["task_id"], owner="test", lease_ms=10000)
        extra = setup.planned("extra", "codex", "pinned")
        self.start(setup, extra)
        with pytest.raises(TaskStoreError, match="window_wip_limit_reached"):
            control.claim_task(window_id=window.id, task_id=control.list_goal_tasks(extra.id)[0]["task_id"], owner="test", lease_ms=10000)

    def test_continuous_run_survives_read_only_restart_preflight_without_granting_dispatch(self, setup):
        from reverse_agent.platform_v1.startup_preflight import WindowState, assess_boot_readiness
        goal = setup.planned("reboot", "codex", "pinned")
        window = self.start(setup, goal)
        report = assess_boot_readiness(windows=[WindowState(window.id, "ACTIVE", window.starts_at, "", OWNER_WINDOW_MODE)],
                                      claims=[], task_counts={"QUEUED": 1}, now=datetime.now(timezone.utc))
        assert report["state"] == "READY_FOR_HOST_RECONCILIATION" and not report["dispatch_permitted"]

    @pytest.mark.parametrize("stopped", [False, True])
    def test_adoption_keeps_tasks_but_respects_owner_stop(self, setup, stopped):
        first = setup.planned("stranded", "codex", "pinned")
        old, _ = admit(setup.host, (first.id,))
        control = setup.host._control_store
        links = control.list_goal_tasks(first.id)
        control.stop_window(old.id, reason="owner_stopped" if stopped else "window_task_budget_exhausted")
        second = setup.planned("new", "codex", "pinned")
        window = self.start(setup, second)
        outcomes = control.adopt_standing_goals(window.id)
        if stopped:
            assert outcomes == () and control.get_goal(first.id).window_id == old.id
        else:
            assert outcomes[0]["status"] == "REBOUND"
            assert control.get_goal(first.id).window_id == window.id
            assert control.list_goal_tasks(first.id) == links
            task = setup.db.get_task(links[0]["task_id"])
            _require_owner_window_pool(setup.db, task, RESOLVED["pinned"], task.policy_ref)
            control.check_strict_task_admission(window.id, task.id)

    def test_untrusted_activation_cannot_request_continuous(self, setup):
        with pytest.raises(TaskStoreError, match="continuous_run_requires_owner_admission"):
            setup.host._control_store.activate_window({"continuous": True}, confirmation="ACTIVATE")

    @pytest.mark.parametrize("observed", [95, 100])
    def test_token_exhaustion_allows_continuous_start_but_keeps_live_claims(self, setup, observed):
        first = setup.planned("tokens", "codex", "pinned")
        old, _ = admit(setup.host, (first.id,), max_token_units=100)
        control = setup.host._control_store
        task = control.list_goal_tasks(first.id)[0]["task_id"]
        control.claim_task(window_id=old.id, task_id=task, owner="test", lease_ms=10000)
        setup.db._conn.execute("UPDATE platform_autonomous_windows SET observed_token_units=? WHERE id=?", (observed, old.id))
        assert control.active_window().id == old.id
        # A settled claim has no unknown remote outcome left to isolate.
        setup.db._conn.execute("UPDATE platform_coordinator_claims SET status='COMPLETE' WHERE task_id=?", (task,))
        assert control.active_window() is None
        assert control.get_window(old.id).stop_reason == "window_token_budget_exhausted"
        second = setup.planned("continuous", "codex", "pinned")
        assert self.start(setup, second).continuous

    def test_adopted_task_rejects_a_binding_only_in_the_source_pool(self, setup):
        first = setup.planned("source", "codex", "pinned")
        old, _ = admit(setup.host, (first.id,))
        control = setup.host._control_store
        control.stop_window(old.id, reason="window_task_budget_exhausted")
        setup.host._store.upsert_binding({"binding_id": "free", "name": "Free", "connection_id": "gateway",
            "executor_id": "opencode", "model_id": "token-sensenova/glm-test", "enabled": False})
        second = setup.planned("target", "codex", "pinned")
        target = self.start(setup, second)
        assert control.adopt_standing_goals(target.id)[0]["status"] == "REBOUND"
        task = setup.db.get_task(control.list_goal_tasks(first.id)[0]["task_id"])
        assert task.policy_ref == old.policy_id
        with pytest.raises(ExecutorRuntimeError, match="outside_confirmed_pool"):
            _require_owner_window_pool(setup.db, task, RESOLVED["free"], task.policy_ref)

    @pytest.mark.parametrize("escape", ["commit", "rollback", "executescript"])
    def test_append_cannot_escape_its_transaction(self, setup, monkeypatch, escape):
        first = setup.planned("first", "codex", "pinned")
        window = self.start(setup, first)
        second = setup.planned("second", "codex", "pinned")
        original = setup.host._goal_service._launch
        def escape_after_launch(goal_id, **kwargs):
            original(goal_id, **kwargs)
            if escape == "executescript":
                setup.db._conn.executescript("SELECT 1;")
            else:
                getattr(setup.db._conn, escape)()
            raise RuntimeError("injected")
        monkeypatch.setattr(setup.host._goal_service, "_launch", escape_after_launch)
        with pytest.raises(TaskStoreError):
            self.start(setup, second)
        control = setup.host._control_store
        assert control.get_goal(second.id).status == "PLANNED"
        assert control.list_goal_tasks(second.id) == ()
        assert [g.id for g in control.list_window_goals(window.id)] == [first.id]
        assert not setup.db._conn.in_transaction


# Filled per test from the real resolver over the fixture store, so the pool the
# Owner approves and the resolution dispatch checks come from the same code.
RESOLVED: dict = {}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    models = ModelProfileStore()
    models.upsert_connection({"connection_id": "native", "name": "Codex", "provider": "codex",
                              "base_url": "https://chatgpt.com", "auth_method": "external_cli_session",
                              "enabled": True})
    models.upsert_connection({"connection_id": "gateway", "name": "Gateway", "provider": "magpie",
                              "base_url": "http://127.0.0.1:3425/v1", "auth_method": "api_key", "enabled": True})
    models.upsert_binding({"binding_id": "pinned", "name": "Pinned", "connection_id": "native",
                           "executor_id": "codex", "model_id": "gpt-test", "enabled": True})
    models.upsert_binding({"binding_id": "free", "name": "Free", "connection_id": "gateway",
                           "executor_id": "opencode", "model_id": "token-sensenova/glm-test", "enabled": True})
    db = TaskStore(str(tmp_path / "owner.sqlite"))
    host = CombinedTrustedHost(task_store=db, store=models, vault=None,
                               codex_readiness_probe=lambda: "managed_login_ready")

    def no_http(_url):
        raise AssertionError("the Owner pool must not call the model-control server")
    monkeypatch.setattr(host, "_binding_resolver_factory", no_http)
    resolver = BindingResolver(transport=owner_window._store_transport(models))
    RESOLVED.clear()
    RESOLVED.update({ref: resolver.resolve(ref, task_executor=executor)
                     for ref, executor in (("pinned", "codex"), ("free", "opencode"))})
    monkeypatch.setattr(host, "_routing_bind_discovered", lambda: None)
    workspace = SimpleNamespace(repository="owner/repo", repo_dir=tmp_path.resolve())
    for module in (owner_window, goal_service):
        monkeypatch.setattr(module, "resolve_repository_workspace", lambda _: workspace)
        monkeypatch.setattr(module, "repository_base", lambda _: "a" * 40)
    goals = host._goal_service

    def planned(key, executor, binding, tasks=1):
        goal = goals.create({"objective": f"Objective {key}\nsecond line", "repository": "owner/repo",
                             "idempotency_key": key, "executor_kind": executor, "binding_ref": binding,
                             "orchestration_mode": "single"})
        return goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": f"T{i}", "title": f"Task {i} of {key}", "instruction": "Do the bounded work"}
            for i in range(tasks)]).goal

    yield SimpleNamespace(host=host, db=db, planned=planned)
    db._conn.close()


def admit(host, goal_ids, *, confirm=None, **overrides):
    shown = []

    def accept(text, code):
        shown.append((text, code))
        return True

    request = dict(hours=24, max_tasks=10, max_concurrent=1, max_retries=2, capabilities=ALL,
                   confirm=confirm or accept)
    request.update(overrides)
    return host._owner_admit_window(goal_ids=goal_ids, **request), shown


def untouched(s, *goals):
    control = s.host._control_store
    assert control.list_windows() == ()
    for goal in goals:
        assert control.get_goal(goal.id) == goal
    for table in ("tasks", "platform_operation_receipts", "platform_goal_task_links"):
        assert s.db._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert not s.db._conn.in_transaction


class TestAdmission:
    @pytest.mark.parametrize("scenario", ["success", "unknown_receipt", "head_changed", "behind", "revoked"])
    def test_resume_binds_the_parked_pr_without_rebinding_its_goal(self, setup, tmp_path, request, monkeypatch, scenario):
        from reverse_agent.platform_v1 import control_store
        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        from reverse_agent.platform_v1.landing_loop import LandingLoopController
        from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
        from test_landing_loop import ProgressGitHub

        goal = setup.planned("parked", "codex", "pinned")
        old, _ = admit(setup.host, (goal.id,), capabilities=(*ALL, "open_draft_pr"))
        control = setup.host._control_store
        github = ProgressGitHub()
        state = control.ensure_landing(repository=goal.repository, goal_id=goal.id,
            pr_number=42, head_sha=github.head, review_round=1)
        identity = state["identity"]
        claim = control.claim_landing_operation(identity, "review_comment", window_id=old.id)
        assert claim
        setup.db._conn.execute("UPDATE platform_goals SET status='COMPLETED' WHERE id=?", (goal.id,))
        control.finish_landing_tick(identity, "BLOCKED", "landing_denied_by_window", 0)
        control.stop_window(old.id)
        before = control.get_goal(goal.id)
        links = control.list_goal_tasks(goal.id)

        window, shown = admit(setup.host, (goal.id,), capabilities=(OWNER_LANDING_CAPABILITY,),
                              resume_parked_landing=True)
        assert f"{goal.repository} PR #42" in shown[0][0] and github.head in shown[0][0]
        assert control.get_goal(goal.id) == before
        assert control.list_goal_tasks(goal.id) == links
        assert control.list_window_goals(window.id) == ()
        assert control.landing_operation(identity, "review_comment")["claim_id"] == claim
        assert control.landing_operation(identity, "review_comment")["window_id"] == old.id

        reopened = TaskStore(str(tmp_path / "owner.sqlite"))
        request.addfinalizer(reopened._conn.close)
        control = control_store.PlatformControlStore(reopened)
        if scenario == "revoked":
            control.stop_window(window.id)
        if scenario == "head_changed":
            github.head = "b" * 40
        github.behind = scenario == "behind"
        def readback(_state, claim_id):
            assert claim_id == claim
            return dict(identity=identity, claim_id=claim, operation="review_comment",
                        outcome="UNKNOWN" if scenario == "unknown_receipt" else "SUCCEEDED")
        github.reconcile_review_comment = readback
        loop = LandingLoopController(control_store=control, github=github,
            autonomy=AutonomyService(control_store=control, capabilities=CapabilityRegistry()))
        coordinator = UnattendedCoordinator(store=reopened, control_store=control, autonomy=loop.autonomy,
            router=None, workspace_root="", landing_loop=loop)
        now = [control_store._utc_now_ms()]
        monkeypatch.setattr(control_store, "_utc_now_ms", lambda: now[0])
        for _ in range(3):
            now[0] += 60_001
            coordinator.tick()
        if scenario == "success":
            assert control.get_landing(identity)["phase"] == "COMPLETE"
            assert [name for name, _ in github.calls].count("merge") == 1
        else:
            assert control.get_landing(identity)["parking_reason"] == {
                "unknown_receipt": "landing_recovery_prior_receipt_unresolved",
                "head_changed": "landing_head_race", "behind": "landing_recovery_branch_behind",
                "revoked": "landing_denied_by_window",
            }[scenario]
            assert github.calls == [] and github.draft and not github.merged
        assert control.get_goal(goal.id) == before

    def test_terminal_landing_grant_is_bound_to_one_confirmed_goal(self, setup, monkeypatch):
        from reverse_agent.platform_v1 import control_store
        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        from reverse_agent.platform_v1.landing_loop import LandingLoopController
        from test_landing_loop import ProgressGitHub, step

        goal = setup.planned("landing", "codex", "pinned")
        other = setup.planned("other", "codex", "pinned")
        window, shown = admit(setup.host, (goal.id,), capabilities=WITH_LANDING)
        assert "GitHub Ready and merge after independent review" in shown[0][0]
        control = setup.host._control_store
        now = [control_store._utc_now_ms()]
        monkeypatch.setattr(control_store, "_utc_now_ms", lambda: now[0])
        github = ProgressGitHub()
        loop = LandingLoopController(control_store=control, github=github,
            autonomy=AutonomyService(control_store=control, capabilities=CapabilityRegistry()))

        other_state = control.ensure_landing(repository=other.repository, goal_id=other.id,
            pr_number=40, head_sha=github.head, review_round=1)
        with pytest.raises(TaskStoreError, match="landing_owner_scope_not_confirmed"):
            control.claim_landing_operation(other_state["identity"], "merge", window_id=window.id)
        assert step(loop, other_state, window, now)["parking_reason"] == "landing_owner_scope_not_confirmed"
        assert github.calls == []

        state = control.ensure_landing(repository=goal.repository, goal_id=goal.id,
            pr_number=41, head_sha=github.head, review_round=1)
        step(loop, state, window, now)
        assert not github.draft and not github.merged
        step(loop, state, window, now)
        assert github.merged
        assert step(loop, state, window, now)["phase"] == "COMPLETE"
        assert [name for name, _ in github.calls].count("merge") == 1

    @pytest.mark.parametrize("surface,continuous,goal_count,reason", [
        ("ui", False, 1, "owner_window_capabilities_invalid"),
        ("supervisor", False, 1, "owner_window_capabilities_invalid"),
        ("terminal", True, 1, "owner_window_landing_scope_invalid"),
        ("terminal", False, 2, "owner_window_landing_scope_invalid"),
    ])
    def test_landing_rejects_implicit_or_wider_consent(self, setup, surface, continuous, goal_count, reason):
        goals = [setup.planned(f"landing-{i}", "codex", "pinned") for i in range(goal_count)]
        with pytest.raises(TaskStoreError, match=reason):
            setup.host._owner_window_admission.admit([goal.id for goal in goals], surface=surface,
                capabilities=WITH_LANDING, continuous=continuous, hours=0 if continuous else 1,
                max_tasks=0 if continuous else 5, max_concurrent=1, max_retries=0,
                confirm=lambda *_args, **_kw: pytest.fail("invalid landing request reached confirmation"))
        untouched(setup, *goals)

    def test_activates_exactly_the_confirmed_goals_with_one_receipt_each(self, setup):
        a, b = setup.planned("a", "codex", "pinned"), setup.planned("b", "opencode", "free", tasks=2)
        window, shown = admit(setup.host, (a.id, b.id))
        control = setup.host._control_store
        assert window.confirmation_mode == OWNER_WINDOW_MODE
        assert (window.max_tasks, window.max_concurrent_tasks, window.max_retries) == (10, 1, 2)
        expires = datetime.fromisoformat(window.expires_at.replace("Z", "+00:00"))
        assert 23.9 < (expires - datetime.now(timezone.utc)).total_seconds() / 3600 <= 24
        assert {g.id: g.status for g in control.list_window_goals(window.id)} == {a.id: "RUNNING", b.id: "RUNNING"}
        rows = setup.db._conn.execute(
            "SELECT subject_id, evidence_json FROM platform_operation_receipts WHERE operation_type = ?",
            (OWNER_WINDOW_RECEIPT,)).fetchall()
        assert sorted(r["subject_id"] for r in rows) == sorted([a.id, b.id])
        evidence = json.loads(rows[0]["evidence_json"])
        assert {entry["binding_ref"] for entry in evidence["approved_pool"]} == {"pinned", "free"}
        assert evidence["goals"] == [a.id, b.id]

    def test_each_task_reserves_an_even_share_of_the_caps(self, setup):
        # 2026-11-09: a capped window reserved 0 per task, so any use stopped it as an overrun.
        a = setup.planned("a", "codex", "pinned")
        window, _ = admit(setup.host, (a.id,), max_token_units=2_000_000, max_cost_micro_units=900)
        assert (window.per_task_token_reservation, window.per_task_cost_reservation) == (200_000, 90)

    def test_the_prompt_shows_the_whole_scope_and_the_code(self, setup):
        a = setup.planned("a", "codex", "pinned")
        _, shown = admit(setup.host, (a.id,))
        text, code = shown[0]
        for expected in (a.id, a.artifact_digest, "Objective a", "second line", "Task 0 of a",
                         "pinned: codex gpt-test", "weekly paced", "Paid API:       excluded",
                         f"Type {code} to activate"):
            assert expected in text

    def test_the_pool_is_read_from_the_store_under_the_lock_without_http(self, setup):
        # The fixture's resolver factory raises if called; reaching the model-control
        # server from inside the store lock would wait on that same lock (#1401 B1).
        b = setup.planned("b", "opencode", "free")
        window, shown = admit(setup.host, (b.id,))
        assert window.confirmation_mode == OWNER_WINDOW_MODE
        assert "free: opencode magpie/token-sensenova/glm-test" in shown[0][0]

    def test_a_binding_the_resolver_rejects_is_not_offered(self, setup):
        setup.host._store.set_codex_readiness("managed_login_unavailable")
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_pinned_binding_outside_pool"):
            admit(setup.host, (a.id,))
        untouched(setup, a)

    def test_a_refusal_changes_nothing(self, setup):
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_confirmation_refused"):
            admit(setup.host, (a.id,), confirm=lambda text, code: False)
        untouched(setup, a)

    def test_a_goal_edited_while_the_owner_reads_rolls_back(self, setup):
        a = setup.planned("a", "codex", "pinned")
        goals = setup.host._goal_service

        def edit_then_accept(text, code):
            goals.plan(a.id, expected_revision=a.revision, tasks=[
                {"id": "X", "title": "Swapped", "instruction": "Something else"}])
            return True

        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            admit(setup.host, (a.id,), confirm=edit_then_accept)
        assert setup.host._control_store.list_windows() == ()

    def test_a_failure_inside_the_transaction_leaves_nothing_behind(self, setup, monkeypatch):
        a, b = setup.planned("a", "codex", "pinned"), setup.planned("b", "opencode", "free")
        real = setup.host._goal_service._launch

        def fail_second(goal_id, **kwargs):
            if goal_id == b.id:
                raise TaskStoreError("injected")
            return real(goal_id, **kwargs)

        monkeypatch.setattr(setup.host._goal_service, "_launch", fail_second)
        with pytest.raises(TaskStoreError, match="injected"):
            admit(setup.host, (a.id, b.id))
        untouched(setup, a, b)

    @pytest.mark.parametrize("overrides,error", [
        ({"hours": 169}, "owner_window_duration_invalid"),
        ({"hours": 0}, "owner_window_duration_invalid"),
        ({"capabilities": ("resume_task",)}, "owner_window_capabilities_invalid"),
        ({"capabilities": ("execute_task", "land_reviewed_pr")}, "owner_window_landing_scope_invalid"),
        ({"max_tasks": 1}, "owner_window_max_tasks_below_planned_tasks"),
        ({"max_concurrent": 9}, "owner_window_limits_invalid"),
        ({"max_retries": 6}, "owner_window_limits_invalid"),
    ])
    def test_envelope_limits(self, setup, overrides, error):
        a = setup.planned("a", "opencode", "free", tasks=2)
        with pytest.raises(TaskStoreError, match=error):
            admit(setup.host, (a.id,), **overrides)
        untouched(setup, a)

    def test_goals_must_share_one_repository(self, setup):
        a = setup.planned("a", "codex", "pinned")
        other = setup.host._goal_service.create({"objective": "Elsewhere", "repository": "owner/other",
                                                 "idempotency_key": "o", "executor_kind": "codex",
                                                 "binding_ref": "pinned", "orchestration_mode": "single"})
        other = setup.host._goal_service.plan(other.id, expected_revision=other.revision, tasks=[
            {"id": "T", "title": "T", "instruction": "x"}]).goal
        with pytest.raises(TaskStoreError, match="owner_window_requires_one_repository"):
            admit(setup.host, (a.id, other.id))

    def test_only_planned_unbound_goals_are_admissible(self, setup):
        a = setup.planned("a", "codex", "pinned")
        draft = setup.host._goal_service.create({"objective": "Draft only", "repository": "owner/repo",
                                                 "idempotency_key": "d", "executor_kind": "codex",
                                                 "binding_ref": "pinned", "orchestration_mode": "single"})
        with pytest.raises(TaskStoreError, match="owner_window_goal_not_admissible"):
            admit(setup.host, (a.id, draft.id))

    def test_a_pinned_binding_must_be_in_the_pool(self, setup, monkeypatch):
        a = setup.planned("a", "codex", "pinned")
        monkeypatch.setattr(setup.host._store, "list_bindings_public",
                            lambda: [b for b in ModelProfileStore.list_bindings_public(setup.host._store)
                                     if b["binding_id"] != "pinned"])
        with pytest.raises(TaskStoreError, match="owner_window_pinned_binding_outside_pool"):
            admit(setup.host, (a.id,))

    def test_paid_bindings_are_never_offered(self, setup, monkeypatch):
        from reverse_agent.platform_v1 import routing_inputs
        monkeypatch.setattr(routing_inputs, "binding_cost_class",
                            lambda binding, connection, owner: "paid_api" if binding["binding_id"] == "free" else "free")
        a = setup.planned("a", "codex", "pinned")
        window, shown = admit(setup.host, (a.id,))
        assert "free (paid API)" in shown[0][0]
        pool = json.loads(setup.db._conn.execute(
            "SELECT evidence_json FROM platform_operation_receipts WHERE operation_type = ?",
            (OWNER_WINDOW_RECEIPT,)).fetchone()[0])["approved_pool"]
        assert [entry["binding_ref"] for entry in pool] == ["pinned"]

    def stale_claim(self, setup, *, task_status="INTERRUPTED", stop=True, expired=True, recorded=True):
        """An attempt claimed by a window that was then stopped, as on the run host 2026-11-14."""
        a = setup.planned("old", "codex", "pinned")
        old, _ = admit(setup.host, (a.id,))
        if stop:
            setup.host._control_store.stop_window(old.id, reason="owner_stopped")
        task = setup.db.create_task(title="abandoned attempt", repository="owner/repo",
                                    executor_kind="deterministic_fixture")
        setup.db._conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (task_status, task.id))
        setup.db._conn.execute(
            "INSERT INTO platform_coordinator_claims (task_id, window_id, epoch, status, expires_at_ms, owner, "
            "created_at, updated_at) VALUES (?, ?, 1, 'ACTIVE', ?, 'coordinator-old', '', '')",
            (task.id, old.id, 0 if expired else 10 ** 15))
        if recorded:
            # A durable checkpoint with a recorded external operation: effects are known.
            setup.db._conn.execute(
                "INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_epoch, lease_expiry_ms, "
                "created_at, updated_at) VALUES (?, ?, 'exec-old', 'fixture', 1, 1, 'x', 'x')",
                (f"run-{task.id}", task.id))
            setup.db._conn.execute(
                "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                "idempotency_key, request_digest, state, created_at, updated_at) "
                "VALUES (?, ?, ?, 'k', 'i', 'd', 'SUCCEEDED', 'x', 'x')", (f"op-{task.id}", f"run-{task.id}", task.id))
        setup.db._conn.commit()
        return old, task

    def test_an_unknown_effects_claim_stops_blocking_but_keeps_its_hold(self, setup):
        """#1206/#1277: the ACTIVE claim is the hold; admission must not retire it."""
        old, task = self.stale_claim(setup, recorded=False)
        b = setup.planned("b", "codex", "pinned")
        window, _ = admit(setup.host, (b.id,))
        assert window.status == "ACTIVE"
        claim = setup.db._conn.execute("SELECT status FROM platform_coordinator_claims WHERE task_id = ?",
                                       (task.id,)).fetchone()
        assert claim["status"] == "ACTIVE"
        control = setup.host._control_store
        with control._lock:
            assert control._stale_claim_unknown_locked(task.id, old.id, 10 ** 15)

    def test_a_stale_claim_of_a_closed_window_is_retired_by_the_next_window(self, setup):
        old, task = self.stale_claim(setup)
        b = setup.planned("b", "codex", "pinned")
        report = setup.host._owner_window_admission.preflight([b.id], **REQUEST)
        assert report["ok"] is True, report["checks"]
        assert [w["warning"] for w in report["warnings"]] == ["stale_claims_retired"]
        window, _ = admit(setup.host, (b.id,))
        assert window.status == "ACTIVE"
        claim = setup.db._conn.execute("SELECT status FROM platform_coordinator_claims WHERE task_id = ?",
                                       (task.id,)).fetchone()
        assert claim["status"] == "RETIRED"
        receipt = setup.db._conn.execute(
            "SELECT reason, result FROM platform_operation_receipts WHERE operation_type = 'claim_retirement' "
            "AND subject_id = ?", (task.id,)).fetchone()
        assert (receipt["reason"], receipt["result"]) == ("window_closed_claim_expired", f"retired_for:{window.id}")

    @pytest.mark.parametrize("variant", ["lease_live", "window_active", "task_running"])
    def test_a_claim_that_may_be_live_still_holds(self, setup, variant):
        self.stale_claim(setup, expired=variant != "lease_live", stop=variant != "window_active",
                         task_status="RUNNING" if variant == "task_running" else "INTERRUPTED")
        b = setup.planned("b", "codex", "pinned")
        with pytest.raises(TaskStoreError):
            admit(setup.host, (b.id,))
        assert setup.db._conn.execute(
            "SELECT COUNT(*) FROM platform_coordinator_claims WHERE status = 'ACTIVE'").fetchone()[0] == 1

    def test_old_active_claims_hold_admission(self, setup):
        a = setup.planned("a", "codex", "pinned")
        setup.db._conn.execute(
            "INSERT INTO platform_coordinator_claims (task_id, window_id, epoch, status, expires_at_ms, owner, "
            "created_at, updated_at) VALUES ('t', 'w', 1, 'ACTIVE', 0, 'o', '', '')")
        with pytest.raises(TaskStoreError, match="owner_window_old_active_claims_hold"):
            admit(setup.host, (a.id,))


class TestOnlyConfirmedGoalsRun:
    @pytest.fixture
    def active(self, setup):
        a = setup.planned("a", "codex", "pinned")
        window, _ = admit(setup.host, (a.id,))
        extra = setup.planned("extra", "codex", "pinned")
        extra = setup.host._goal_service.approve(extra.id, expected_revision=extra.revision)
        return setup, window, a, extra

    def test_no_other_goal_launches_into_the_window(self, active):
        setup, window, _, extra = active
        with pytest.raises(TaskStoreError, match="owner_window_goal_not_confirmed"):
            setup.host._goal_service._launch(extra.id, expected_revision=extra.revision, window_id=window.id)

    def test_claim_admission_refuses_a_foreign_goal_task(self, active):
        setup, window, a, extra = active
        control = setup.host._control_store
        own = control.list_goal_tasks(a.id)[0]["task_id"]
        control.check_strict_task_admission(window.id, own)
        # Smuggle a task link in behind the launch check: the claim path still refuses it.
        setup.db._conn.execute(
            "INSERT INTO platform_goal_task_links (goal_id, task_id, plan_task_id, seq, goal_revision, "
            "dependencies_json) VALUES (?, 'smuggled', 'X', 9, ?, '[]')", (extra.id, extra.revision))
        with pytest.raises(TaskStoreError, match="owner_window_goal_not_confirmed"):
            control.check_strict_task_admission(window.id, "smuggled")

    def test_activate_window_rejects_mixing_the_two_admission_shapes(self, setup):
        control = setup.host._control_store
        payload = {"policy_id": "p", "policy_revision": 1, "owner_identity": "o",
                   "starts_at": "2026-01-01T00:00:00Z", "expires_at": "2026-01-01T01:00:00Z",
                   "repositories": ["owner/repo"], "capabilities": ["execute_task"],
                   "max_tasks": 1, "max_concurrent_tasks": 1, "max_retries": 0}
        for kwargs in ({"_host_expected_goal_ids": ("g",)},
                       {"_host_sql_admit": lambda _w: None, "_host_expected_goal_ids": ("g",),
                        "_host_expected_goal_id": "g"},
                       {"_host_sql_admit": lambda _w: None, "_host_expected_goal_ids": ()}):
            with pytest.raises(TaskStoreError, match="host_atomic_admission_invalid"):
                control.activate_window(payload, confirmation="ACTIVATE", **kwargs)


class TestDispatchPoolGuard:
    @pytest.fixture
    def task(self, setup):
        a = setup.planned("a", "opencode", "free")
        window, _ = admit(setup.host, (a.id,))
        task_id = setup.host._control_store.list_goal_tasks(a.id)[0]["task_id"]
        return setup, setup.db.get_task(task_id)

    def test_a_pool_binding_passes(self, task):
        setup, stored = task
        _require_owner_window_pool(setup.db, stored, RESOLVED["free"], stored.policy_ref)

    def test_a_binding_outside_the_pool_is_refused(self, task):
        setup, stored = task
        swapped = replace(RESOLVED["free"], model_id="something-else")
        with pytest.raises(ExecutorRuntimeError, match="owner_window_binding_outside_confirmed_pool"):
            _require_owner_window_pool(setup.db, stored, swapped, stored.policy_ref)

    def test_durable_dispatch_preserves_a_pool_misroute(self, task, monkeypatch, tmp_path):
        setup, stored = task
        swapped = replace(RESOLVED["free"], model_id="something-else")
        monkeypatch.setattr(durable_execution, "resolve_repository_workspace", lambda _repository: object())
        service = durable_execution.DurableExecutionService(
            store=setup.db,
            router=SimpleNamespace(create_executor=lambda **_: pytest.fail("Executor must not be created")),
            binding_resolver=SimpleNamespace(resolve=lambda *_, **__: swapped),
            execution_authority_sha="a" * 40,
            planning_sha="a" * 40,
        )
        outcome = service.execute_durable_single(stored.id, workspace_root=str(tmp_path))
        final = setup.db.get_task(stored.id)
        assert not outcome.success
        assert outcome.failure_classification == final.failure_classification == "owner_window_binding_outside_confirmed_pool"
        assert final.status == "FAILED"
        assert setup.db._conn.execute("SELECT COUNT(*) FROM durable_external_operations").fetchone()[0] == 0
        assert setup.db._conn.execute("SELECT lease_owner FROM durable_runs WHERE task_id=?", (stored.id,)).fetchone()[0] == ""

    def test_no_binding_is_refused(self, task):
        setup, stored = task
        with pytest.raises(ExecutorRuntimeError):
            _require_owner_window_pool(setup.db, stored, None, stored.policy_ref)

    def test_ordinary_windows_are_untouched(self, setup):
        stored = SimpleNamespace(id="t", policy_ref="no-such-window")
        _require_owner_window_pool(setup.db, stored, None, "no-such-window")


class TestLivePool:
    """Owner decision 2026-11-17 (#1667): a continuous window uses the live binding pool."""

    def admitted(self, setup, monkeypatch, *, continuous):
        # A routed goal, so the real router (not a pin) chooses its model afterwards.
        monkeypatch.setattr(setup.host._goal_service, "task_resolver", lambda item, *, goal=None, **kw: {
            "executor_kind": "codex", "binding_ref": "pinned", "model_id": "gpt-test", "reason": "fixture_route"})
        goals = setup.host._goal_service
        goal = goals.create({"objective": "Live pool", "repository": "owner/repo", "idempotency_key": "live",
                             "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": "agent_team"})
        goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": "T", "title": "Task", "instruction": "Do it", "difficulty": 1}]).goal
        bounds = (dict(continuous=True, hours=0, max_tasks=0, max_token_units=0) if continuous else {})
        window, _ = admit(setup.host, (goal.id,), **bounds)
        # Bound after admission, as the Magpie group bindings were on 2026-11-17.
        setup.host._store.upsert_binding({"binding_id": "late", "name": "Late", "connection_id": "gateway",
            "executor_id": "opencode", "model_id": "token-sensenova/glm-late", "enabled": True})
        late = BindingResolver(transport=owner_window._store_transport(setup.host._store)).resolve(
            "late", task_executor="opencode")
        control = setup.host._control_store
        goal = control.get_goal(goal.id)
        task = setup.db.get_task(control.list_goal_tasks(goal.id)[0]["task_id"])
        return goal, window, task, late

    def route(self, setup, goal):
        from reverse_agent.platform_v1.goal_service import PlannedTask
        return setup.host._resolve_task_model(PlannedTask("T", "Task", "Do it", difficulty=1), goal=goal,
                                              forecast=True, probe_availability=False)

    def test_a_binding_added_after_admission_runs_in_a_continuous_window(self, setup, monkeypatch):
        from reverse_agent.platform_v1.window_pool import goal_window_pool
        goal, window, task, late = self.admitted(setup, monkeypatch, continuous=True)
        _require_owner_window_pool(setup.db, task, late, task.policy_ref)
        assert goal_window_pool(setup.db, goal.id, window.id)["pool_source"] == "live"
        assert "late" in {e["binding_ref"] for e in setup.host._goal_service._owner_window_pool(goal, window.id)}
        decision = self.route(setup, goal)
        assert decision["pool_source"] == "live" and decision["pool_size"] == 3
        assert "outside_window_pool" not in decision["excluded_summary"]
        # The admission receipt keeps the pool confirmed then, as audit evidence.
        evidence = json.loads(setup.db._conn.execute(
            "SELECT evidence_json FROM platform_operation_receipts WHERE subject_id=? AND operation_type=?",
            (goal.id, OWNER_WINDOW_RECEIPT)).fetchone()[0])
        assert "late" not in {e["binding_ref"] for e in evidence["approved_pool"]}

    def test_an_expiring_window_keeps_its_admission_pool(self, setup, monkeypatch):
        from reverse_agent.platform_v1.window_pool import goal_window_pool
        goal, window, task, late = self.admitted(setup, monkeypatch, continuous=False)
        with pytest.raises(ExecutorRuntimeError, match="owner_window_binding_outside_confirmed_pool"):
            _require_owner_window_pool(setup.db, task, late, task.policy_ref)
        assert goal_window_pool(setup.db, goal.id, window.id)["pool_source"] == "admission"
        assert "late" not in {e["binding_ref"] for e in setup.host._goal_service._owner_window_pool(goal, window.id)}
        decision = self.route(setup, goal)
        assert decision["pool_source"] == "admission" and decision["pool_size"] == 2
        assert decision["binding_ref"] != "late"
        assert {"binding_id": "late", "model_id": "token-sensenova/glm-late",
                "filter": "outside_window_pool"} in decision["excluded_candidates"]

    def test_an_owner_exclude_removes_a_binding_from_the_live_pool(self, setup, monkeypatch):
        from reverse_agent.platform_v1 import routing_inputs
        goal, window, task, late = self.admitted(setup, monkeypatch, continuous=True)
        monkeypatch.setattr(routing_inputs, "read_overrides",
                            lambda _path: {"bindings": {"late": {"exclude": True}}})
        with pytest.raises(ExecutorRuntimeError, match="owner_window_binding_outside_confirmed_pool"):
            _require_owner_window_pool(setup.db, task, late, task.policy_ref)
        assert "late" not in {e["binding_ref"] for e in setup.host._goal_service._owner_window_pool(goal, window.id)}
        decision = self.route(setup, goal)
        assert decision["pool_source"] == "live" and decision["pool_size"] == 2
        assert any(row["binding_id"] == "late" and row["filter"] == "outside_window_pool"
                   for row in decision["excluded_candidates"])

    def test_continuous_adoption_uses_the_live_pool(self, setup, monkeypatch):
        goal, old, task, late = self.admitted(setup, monkeypatch, continuous=False)
        control = setup.host._control_store
        control.stop_window(old.id, reason="window_task_budget_exhausted")
        target = TestContinuousRun().start(setup, setup.planned("target", "codex", "pinned"))
        assert control.adopt_standing_goals(target.id)[0]["status"] == "REBOUND"
        evidence = json.loads(setup.db._conn.execute(
            "SELECT evidence_json FROM platform_operation_receipts WHERE subject_id=? AND window_id=? "
            "AND operation_type=?", (goal.id, target.id, OWNER_WINDOW_RECEIPT)).fetchone()[0])
        assert evidence["pool_source"] == "live" and "late" in {e["binding_ref"] for e in evidence["approved_pool"]}
        _require_owner_window_pool(setup.db, task, late, task.policy_ref)

    def test_a_disabled_binding_leaves_the_live_pool(self, setup, monkeypatch):
        goal, window, task, late = self.admitted(setup, monkeypatch, continuous=True)
        setup.host._store.upsert_binding({"binding_id": "late", "name": "Late", "connection_id": "gateway",
            "executor_id": "opencode", "model_id": "token-sensenova/glm-late", "enabled": False})
        with pytest.raises(ExecutorRuntimeError, match="owner_window_binding_outside_confirmed_pool"):
            _require_owner_window_pool(setup.db, task, late, task.policy_ref)


class TestCommandLine:
    def test_valid_arguments(self):
        args = owner_window.parse(["--goal", "g1", "--goal", "g2", "--hours", "24", "--max-tasks", "10",
                                   "--capability", "execute_task", "--capability", "open_draft_pr"])
        assert args.goal == ["g1", "g2"] and args.capability == ["execute_task", "open_draft_pr"]

    def test_landing_is_an_explicit_terminal_flag(self):
        args = owner_window.parse(["--goal", "g1", "--hours", "1", "--max-tasks", "5",
                                   "--capability", "execute_task", "--capability", "validate_task",
                                   "--capability", "open_draft_pr", "--land-reviewed-pr"])
        assert OWNER_LANDING_CAPABILITY in args.capability

    def test_landing_recovery_only_requests_landing_capability(self):
        args = owner_window.parse(["--goal", "g1", "--hours", "1", "--resume-parked-landing"])
        assert args.capability == [OWNER_LANDING_CAPABILITY]

    @pytest.mark.parametrize("argv", [
        ["--goal", "g", "--hours", "200", "--max-tasks", "1", "--capability", "execute_task"],
        ["--goal", "g", "--hours", "1", "--max-tasks", "1", "--capability", "resume_task"],
        ["--goal", "g", "--goal", "g", "--hours", "1", "--max-tasks", "1", "--capability", "execute_task"],
        ["--goal", "a/b", "--hours", "1", "--max-tasks", "1", "--capability", "execute_task"],
        ["--goal", "g", "--hours", "1", "--max-tasks", "1", "--capability", "land_reviewed_pr"],
        ["--goal", "g", "--hours", "1", "--max-tasks", "1", "--max-concurrent", "9", "--capability", "execute_task"],
        ["--goal", "g", "--hours", "1", "--max-tasks", "1", "--capability", "execute_task", "--yes"],
    ])
    def test_invalid_arguments_stop_before_the_host(self, argv, monkeypatch):
        from reverse_agent.platform_v1 import trusted_host
        monkeypatch.setattr(trusted_host, "run_combined_trusted_host", lambda **kw: pytest.fail("host started"))
        with pytest.raises(SystemExit):
            owner_window.main(argv)

    def test_the_code_must_be_typed_at_an_interactive_terminal(self):
        out = io.StringIO()
        piped = io.StringIO("ABC123\n")
        assert owner_window.terminal_confirm("scope", "ABC123", stdin=piped, stdout=out) is False
        assert "interactive terminal" in out.getvalue()

    @pytest.mark.parametrize("typed,expected", [("abc123\n", True), ("ABC124\n", False), ("\n", False)])
    def test_only_the_shown_code_activates(self, typed, expected):
        class Tty(io.StringIO):
            def isatty(self):
                return True
        assert owner_window.terminal_confirm("scope", "ABC123", stdin=Tty(typed), stdout=io.StringIO()) is expected


class TestRoutePreview:
    """Every task must launch on a pool binding; the Owner sees which, before confirming."""

    def routed(self, setup, mode="agent_team", key="r"):
        goals = setup.host._goal_service
        goal = goals.create({"objective": "Routed work", "repository": "owner/repo", "idempotency_key": key,
                             "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": mode})
        return goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": "T", "title": "Routed task", "instruction": "Do it"}]).goal

    def route_to(self, monkeypatch, setup, *answers):
        calls = []

        def route(item, *, goal=None, **kwargs):
            answer = answers[min(len(calls), len(answers) - 1)]
            calls.append(kwargs)
            if isinstance(answer, Exception):
                raise answer
            return answer
        monkeypatch.setattr(setup.host._goal_service, "task_resolver", route)
        return calls

    FREE = {"executor_kind": "opencode", "binding_ref": "free", "model_id": "token-sensenova/glm-test",
            "reason": "fixture_route"}

    def test_the_prompt_shows_each_tasks_expected_model(self, setup, monkeypatch):
        calls = self.route_to(monkeypatch, setup, self.FREE)
        a, pinned = self.routed(setup), setup.planned("p", "codex", "pinned")
        _, shown = admit(setup.host, (a.id, pinned.id))
        text = shown[0][0]
        assert f"- {a.id} T: free (token-sensenova/glm-test, fixture_route)" in text
        assert f"- {pinned.id} T0: pinned (gpt-test, pinned)" in text
        assert calls and all(call.get("probe_availability") is False for call in calls)

    def test_a_routed_single_goal_is_refused_before_the_owner_is_asked(self, setup):
        # 2026-11-08: such a Goal launched with no binding, its task was refused at
        # dispatch and the window went BLOCKED.
        single = self.routed(setup, mode="single")
        asked = []
        with pytest.raises(TaskStoreError, match="routed_single_goal_gets_no_binding"):
            admit(setup.host, (single.id,), confirm=lambda text, code: asked.append(code) or True)
        assert asked == []
        untouched(setup, single)

    def test_a_task_routing_cannot_place_is_refused_before_the_owner_is_asked(self, setup, monkeypatch):
        self.route_to(monkeypatch, setup, TaskStoreError("no_runnable_model"))
        goal = self.routed(setup)
        with pytest.raises(TaskStoreError, match="owner_window_task_unroutable:.*no_runnable_model"):
            admit(setup.host, (goal.id,))
        untouched(setup, goal)

    def test_a_binding_outside_the_shown_pool_is_refused(self, setup, monkeypatch):
        self.route_to(monkeypatch, setup, {**self.FREE, "binding_ref": "not-in-pool"})
        goal = self.routed(setup)
        with pytest.raises(TaskStoreError, match="not-in-pool_outside_pool"):
            admit(setup.host, (goal.id,))
        untouched(setup, goal)

    def test_a_task_left_unbound_inside_the_transaction_rolls_everything_back(self, setup, monkeypatch):
        # The preview routed fine, then quota moved: launch records no binding.
        self.route_to(monkeypatch, setup, self.FREE, TaskStoreError("no_runnable_model"))
        goal = self.routed(setup)
        with pytest.raises(TaskStoreError, match=f"owner_window_task_unbound:{goal.id}:T"):
            admit(setup.host, (goal.id,))
        untouched(setup, goal)


    def test_a_review_task_is_routed_with_its_authors_identity(self, setup, monkeypatch):
        # A review needs its author's model; the real resolver refuses one routed without it.
        seen = []

        def route(item, *, goal=None, author_models=(), author_bindings=(), **kwargs):
            if (item.kind == "review" or item.agent_role == "reviewer") and item.artifact_input:
                if not author_models and not author_bindings:
                    raise TaskStoreError("review_not_independent")
            seen.append((item.id, tuple(author_models), kwargs.get("probe_availability")))
            return dict(self.FREE)
        monkeypatch.setattr(setup.host._goal_service, "task_resolver", route)
        goals = setup.host._goal_service
        checks = [{"profile_id": "python_pytest", "working_directory": "."}]
        goal = goals.create({"objective": "Reviewed work", "repository": "owner/repo", "idempotency_key": "rv",
                             "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": "agent_team"})
        goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": "T001", "title": "Code", "instruction": "Do it", "validation_checks": checks},
            {"id": "T002", "title": "Review", "instruction": "Review it", "kind": "review", "agent_role": "reviewer",
             "dependencies": ["T001"], "artifact_input": {"plan_task_id": "T001"}, "validation_checks": checks},
        ]).goal
        _, shown = admit(setup.host, (goal.id,))
        assert f"- {goal.id} T002: free (token-sensenova/glm-test, fixture_route)" in shown[0][0]
        preview = seen[:2]  # the preview routes before the transaction launch routes again
        assert preview == [("T001", (), False), ("T002", ("token-sensenova/glm-test",), False)]

class TestRoutedGoals:
    def test_an_agent_team_goal_is_routed_inside_the_transaction(self, setup, monkeypatch):
        seen = []

        def route(item, *, goal=None, **kwargs):
            seen.append(kwargs)
            return {"executor_kind": "opencode", "binding_ref": "free", "model_id": "token-sensenova/glm-test",
                    "reason": "fixture_route"}

        monkeypatch.setattr(setup.host._goal_service, "task_resolver", route)
        goals = setup.host._goal_service
        goal = goals.create({"objective": "Routed work", "repository": "owner/repo", "idempotency_key": "r",
                             "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": "agent_team"})
        goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": "T", "title": "Routed task", "instruction": "Do it"}]).goal
        window, shown = admit(setup.host, (goal.id,))
        assert "routed" in shown[0][0]
        # Availability probes are model calls; none may run inside the activation transaction.
        assert seen and all(call.get("probe_availability") is False for call in seen)
        task = setup.db.get_task(setup.host._control_store.list_goal_tasks(goal.id)[0]["task_id"])
        assert task.binding_ref == "free"
        _require_owner_window_pool(setup.db, task, RESOLVED["free"], task.policy_ref)


REQUEST = dict(hours=24, max_tasks=10, max_concurrent=1, max_retries=2, capabilities=list(ALL))


class TestPreflight:
    """What would refuse activation, reported before anyone is asked; it authorizes nothing."""

    def by_check(self, report):
        return {check["check"]: check for check in report["checks"]}

    def test_a_clean_scope_reports_ok_with_the_expected_models_and_changes_nothing(self, setup):
        a, b = setup.planned("a", "codex", "pinned"), setup.planned("b", "opencode", "free", tasks=2)
        report = setup.host._owner_window_admission.preflight([a.id, b.id], **REQUEST)
        assert report["ok"] is True
        assert [check["check"] for check in report["checks"]] == [
            "leftover_claims", "goals", "model_pool", "routing"]
        assert f"- {a.id} T0: pinned (gpt-test, pinned)" in report["preview"]
        assert f"- {b.id} T1: free ({RESOLVED['free'].model_id}, pinned)" in report["preview"]
        scope = report["scope"]
        assert scope["repository"] == "owner/repo" and scope["paid_api"] == "excluded"
        assert [goal["id"] for goal in scope["goals"]] == [a.id, b.id]
        # The card enables Start only when the plan on screen is this revision.
        assert [goal["revision"] for goal in scope["goals"]] == [
            setup.host._control_store.get_goal(a.id).revision, setup.host._control_store.get_goal(b.id).revision]
        assert scope["goals"][1]["tasks"] == [{"id": "T0", "title": "Task 0 of b"}, {"id": "T1", "title": "Task 1 of b"}]
        assert (scope["envelope"]["max_tasks"], scope["envelope"]["max_retries"]) == (10, 2)
        assert {entry["binding"] for entry in scope["pool"]} == {"pinned", "free"}
        json.dumps(report)  # the HTTP route sends it as is
        untouched(setup, a, b)

    def test_leftover_claims_are_named_and_the_goal_check_waits_for_them(self, setup, monkeypatch):
        a = setup.planned("a", "codex", "pinned")
        real = setup.db._conn

        class Claims:
            def execute(self, sql, *args):
                if "platform_coordinator_claims" in sql:
                    return SimpleNamespace(fetchone=lambda: (3,), fetchall=lambda: [])
                return real.execute(sql, *args)
        monkeypatch.setattr(setup.host._control_store, "_conn", Claims())
        checks = self.by_check(setup.host._owner_window_admission.preflight([a.id], **REQUEST))
        assert (checks["leftover_claims"]["ok"], checks["leftover_claims"]["reason"]) == (
            False, "owner_window_old_active_claims_hold")
        assert "3 active coordinator claims" in checks["leftover_claims"]["detail"]
        assert checks["goals"]["reason"] == "skipped_while_claims_hold"
        assert "routing" not in checks

    def test_a_routed_single_goal_fails_routing_with_its_reason(self, setup):
        goals = setup.host._goal_service
        goal = goals.create({"objective": "Routed", "repository": "owner/repo", "idempotency_key": "s",
                             "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": "single"})
        goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[
            {"id": "T", "title": "Routed task", "instruction": "Do it"}]).goal
        report = setup.host._owner_window_admission.preflight([goal.id], **REQUEST)
        routing = self.by_check(report)["routing"]
        assert report["ok"] is False and routing["ok"] is False
        assert "routed_single_goal_gets_no_binding" in routing["reason"]
        untouched(setup, goal)

    def test_a_goal_that_is_not_admissible_is_reported(self, setup):
        a = setup.planned("a", "codex", "pinned", tasks=2)
        report = setup.host._owner_window_admission.preflight([a.id], **{**REQUEST, "max_tasks": 1})
        assert report["ok"] is False
        assert self.by_check(report)["goals"]["reason"] == "owner_window_max_tasks_below_planned_tasks"

    def test_an_unknown_goal_is_reported_not_raised(self, setup):
        report = setup.host._owner_window_admission.preflight(["goal-missing"], **REQUEST)
        assert report["ok"] is False and self.by_check(report)["goals"]["reason"] == "goal_not_found:goal-missing"

    @pytest.mark.parametrize("change", [{"hours": 0}, {"capabilities": ["resume_task"]}, {"max_concurrent": 50},
                                        {"max_retries": 6}, {"max_tasks": 101}, {"max_token_units": -1}])
    def test_an_invalid_request_is_reported_first(self, setup, change):
        a = setup.planned("a", "codex", "pinned")
        report = setup.host._owner_window_admission.preflight([a.id], **{**REQUEST, **change})
        assert [check["check"] for check in report["checks"]] == ["request"]
        assert report["ok"] is False and report["scope"] is None


class TestOwnerWindowRequest:
    def test_a_well_formed_body_is_normalized(self):
        from reverse_agent.platform_v1.task_service import owner_window_request
        body = {"goal_ids": ["g1"], "hours": 2, "max_tasks": 3, "max_concurrent": 1, "max_retries": 1,
                "capabilities": ["execute_task"], "max_token_units": 300000}
        assert owner_window_request(body) == {
            "goal_ids": ["g1"], "hours": 2.0, "capabilities": ["execute_task"], "max_tasks": 3,
            "max_concurrent": 1, "max_retries": 1, "max_token_units": 300000, "max_cost_micro_units": 0}

    @pytest.mark.parametrize("body", [
        [], {"goal_ids": "g1", "hours": 2, "max_tasks": 3, "max_concurrent": 1, "max_retries": 1,
             "capabilities": ["execute_task"]},
        {"goal_ids": ["g1"], "hours": True, "max_tasks": 3, "max_concurrent": 1, "max_retries": 1,
         "capabilities": ["execute_task"]},
        {"goal_ids": ["g1"], "hours": 2, "max_concurrent": 1, "max_retries": 1, "capabilities": ["execute_task"]},
        {"goal_ids": ["g1"], "hours": 2, "max_tasks": 3, "max_concurrent": 1, "max_retries": -1,
         "capabilities": ["execute_task"]},
        {"goal_ids": ["g1"], "hours": 2, "max_tasks": "3", "max_concurrent": 1, "max_retries": 1,
         "capabilities": ["execute_task"]},
        {"goal_ids": ["g1"], "hours": 10 ** 400, "max_tasks": 3, "max_concurrent": 1, "max_retries": 1,
         "capabilities": ["execute_task"]},
    ])
    def test_a_malformed_body_is_refused(self, body):
        from reverse_agent.platform_v1.task_service import owner_window_request
        with pytest.raises(TaskStoreError, match="owner_window_request_invalid"):
            owner_window_request(body)

    def test_the_host_wires_the_preflight_into_the_task_api_and_nothing_that_activates(self):
        import inspect
        from reverse_agent.platform_v1 import task_service, trusted_host
        assert "owner_window_preflight=self._owner_window_admission.preflight" in inspect.getsource(trusted_host)
        handler = inspect.getsource(task_service._TaskHandler)
        route = handler[handler.index('["api", "owner-window", "preflight"]'):]
        route = route[:route.index('if segments == ["api", "windows", "activate"]')]
        assert "admit" not in route and "activate" not in route


class TestCardActivation:
    """Owner decision 2026-11-09: Start on the confirmation card activates the window."""

    REQ = dict(hours=24, max_tasks=10, max_concurrent=1, max_retries=2, capabilities=list(ALL))

    def card(self, setup, *goals):
        report = setup.host._owner_window_admission.preflight([g.id for g in goals], **self.REQ)
        assert report["ok"] is True and report["confirmation"] == "ui"
        return report["card_digest"]

    def test_start_on_the_card_activates_with_one_receipt_per_goal(self, setup):
        a, b = setup.planned("a", "codex", "pinned"), setup.planned("b", "opencode", "free")
        digest = self.card(setup, a, b)
        window = setup.host._owner_window_admission.admit_from_card([a.id, b.id], card_digest=digest, **self.REQ)
        assert window.confirmation_mode == OWNER_WINDOW_MODE and window.status == "ACTIVE"
        rows = setup.db._conn.execute("SELECT evidence_json FROM platform_operation_receipts WHERE operation_type = ?",
                                      (OWNER_WINDOW_RECEIPT,)).fetchall()
        assert len(rows) == 2
        assert {json.loads(r["evidence_json"])["mechanism"] for r in rows} == {
            "owner pressed Start on the Nerelan confirmation card"}

    def test_the_card_digest_is_stable_across_requests(self, setup):
        a = setup.planned("a", "codex", "pinned")
        assert self.card(setup, a) == self.card(setup, a)

    @pytest.mark.parametrize("change", [{"max_retries": 1}, {"hours": 12}, {"max_tasks": 9}])
    def test_a_request_unlike_the_card_is_refused(self, setup, change):
        a = setup.planned("a", "codex", "pinned")
        digest = self.card(setup, a)
        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            setup.host._owner_window_admission.admit_from_card([a.id], card_digest=digest, **{**self.REQ, **change})
        untouched(setup, a)

    def test_a_goal_replanned_after_the_card_is_refused(self, setup):
        a = setup.planned("a", "codex", "pinned")
        digest = self.card(setup, a)
        goals = setup.host._goal_service
        replanned = goals.plan(a.id, expected_revision=a.revision, tasks=[
            {"id": "T0", "title": "Different", "instruction": "Other work"}]).goal
        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            setup.host._owner_window_admission.admit_from_card([a.id], card_digest=digest, **self.REQ)
        untouched(setup, replanned)

    @pytest.mark.parametrize("digest", ["", "x" * 64, None, "A" * 64])
    def test_a_malformed_digest_is_refused(self, setup, digest):
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_card_digest_invalid"):
            setup.host._owner_window_admission.admit_from_card([a.id], card_digest=digest, **self.REQ)
        untouched(setup, a)

    def test_strict_terminal_mode_refuses_the_card(self, setup, tmp_path, monkeypatch):
        state = tmp_path / "model_setup_state.json"
        (tmp_path / "owner_window_settings.json").write_text(json.dumps({"confirmation": "terminal"}), encoding="utf-8")
        monkeypatch.setattr(setup.host._store, "_state_path", state, raising=False)
        a = setup.planned("a", "codex", "pinned")
        report = setup.host._owner_window_admission.preflight([a.id], **self.REQ)
        assert report["confirmation"] == "terminal"
        with pytest.raises(TaskStoreError, match="owner_window_terminal_confirmation_required"):
            setup.host._owner_window_admission.admit_from_card([a.id], card_digest=report["card_digest"], **self.REQ)
        untouched(setup, a)

    @pytest.mark.parametrize("content", ['{"confirmation": "anything"}', "not json", "[]"])
    def test_bad_settings_are_refused(self, setup, tmp_path, monkeypatch, content):
        (tmp_path / "owner_window_settings.json").write_text(content, encoding="utf-8")
        monkeypatch.setattr(setup.host._store, "_state_path", tmp_path / "model_setup_state.json", raising=False)
        with pytest.raises(TaskStoreError, match="owner_window_settings_invalid"):
            setup.host._owner_window_admission.confirmation_mode()

    def test_the_task_api_route_passes_the_card_digest(self):
        import inspect
        from reverse_agent.platform_v1 import task_service, trusted_host
        assert "owner_window_activate=self._owner_window_admission.admit_from_card" in inspect.getsource(trusted_host)
        handler = inspect.getsource(task_service._TaskHandler)
        route = handler[handler.index('["api", "owner-window", "activate"]'):]
        route = route[:route.index('["api", "owner-window", "preflight"]')]
        assert 'payload.pop("card_digest"' in route and "card_digest=card_digest" in route


class TestCardRequest:
    """The card starts from a preset: the host turns it into the request it will check."""

    def test_the_default_preset_gives_a_request_preflight_accepts(self, setup):
        a = setup.planned("a", "codex", "pinned", tasks=2)
        admission = setup.host._owner_window_admission
        card = admission.card_request([a.id])
        assert card["preset"] == "continuous" and set(card["presets"]) >= {"trial", "day", "week"}
        assert card["confirmation"] == "ui"
        request = dict(card["request"])
        assert request.pop("goal_ids") == [a.id]
        assert request["continuous"] is True and request["max_tasks"] == 0 and request["max_token_units"] == 0
        report = admission.preflight([a.id], **request)
        assert report["ok"] is True
        window = admission.admit_from_card([a.id], card_digest=report["card_digest"], **request)
        assert window.status == "ACTIVE" and window.continuous

    def test_a_named_preset_changes_the_bounds(self, setup):
        a = setup.planned("a", "codex", "pinned")
        trial = setup.host._owner_window_admission.card_request([a.id], "trial")["request"]
        assert trial["hours"] == 2.0 and trial["max_retries"] == 1

    @pytest.mark.parametrize("preset", ["forever", 3])
    def test_an_unknown_preset_is_refused(self, setup, preset):
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_preset_invalid"):
            setup.host._owner_window_admission.card_request([a.id], preset)

    def test_the_route_is_read_only(self):
        import inspect
        from reverse_agent.platform_v1 import task_service, trusted_host
        assert "owner_window_card_request=self._owner_window_admission.card_request" in inspect.getsource(trusted_host)
        handler = inspect.getsource(task_service._TaskHandler)
        route = handler[handler.index('["api", "owner-window", "request"]'):]
        route = route[:route.index('["api", "owner-window", "preflight"]')]
        assert "admit" not in route and "activate" not in route
