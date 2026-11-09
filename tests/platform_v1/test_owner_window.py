"""Owner-confirmed multi-Goal windows. Provider-free: no server, model or dispatch."""
from __future__ import annotations

import io
import json
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import goal_service, owner_window
from reverse_agent.platform_v1.binding_resolver import BindingResolver
from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
from reverse_agent.platform_v1.durable_execution import ExecutorRuntimeError, _require_owner_window_pool
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

ALL = ("execute_task", "resume_task", "reconcile_task", "validate_task")


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
        ({"capabilities": ("execute_task", "land_reviewed_pr")}, "owner_window_capabilities_invalid"),
        ({"max_tasks": 1}, "owner_window_max_tasks_below_planned_tasks"),
        ({"max_concurrent": 9}, "host_atomic_window_scope_invalid"),
        ({"max_retries": 6}, "host_atomic_window_scope_invalid"),
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

    def test_no_binding_is_refused(self, task):
        setup, stored = task
        with pytest.raises(ExecutorRuntimeError):
            _require_owner_window_pool(setup.db, stored, None, stored.policy_ref)

    def test_ordinary_windows_are_untouched(self, setup):
        stored = SimpleNamespace(id="t", policy_ref="no-such-window")
        _require_owner_window_pool(setup.db, stored, None, "no-such-window")


class TestCommandLine:
    def test_valid_arguments(self):
        args = owner_window.parse(["--goal", "g1", "--goal", "g2", "--hours", "24", "--max-tasks", "10",
                                   "--capability", "execute_task", "--capability", "open_draft_pr"])
        assert args.goal == ["g1", "g2"] and args.capability == ["execute_task", "open_draft_pr"]

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
                    return SimpleNamespace(fetchone=lambda: (3,))
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
        a = setup.planned("a", "codex", "pinned")
        report = setup.host._owner_window_admission.preflight([a.id], **{**REQUEST, "max_tasks": 0})
        assert report["ok"] is False
        assert self.by_check(report)["goals"]["reason"] == "owner_window_max_tasks_below_planned_tasks"

    def test_an_unknown_goal_is_reported_not_raised(self, setup):
        report = setup.host._owner_window_admission.preflight(["goal-missing"], **REQUEST)
        assert report["ok"] is False and self.by_check(report)["goals"]["reason"] == "goal_not_found:goal-missing"

    @pytest.mark.parametrize("change", [{"hours": 0}, {"capabilities": ["resume_task"]}])
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
