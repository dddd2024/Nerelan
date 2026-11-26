"""Local Git/SQLite feedback loop tests; no providers or network."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup, run_review, REJECT, Reviewer
from test_functional_execution import LocalImplementation, ordinary
from reverse_agent.platform_v1 import goal_service, artifact_handoff
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def rejected(setup):
    store, _, producer, review, _, options, _ = setup
    options['response'] = REJECT
    result = run_review(setup)
    assert result.failure_classification == 'model_review_rejected'
    control = PlatformControlStore(store)
    goal_id = control.goal_id_for_task(producer)
    store._conn.execute("UPDATE platform_goals SET orchestration_mode = 'agent_team' WHERE id = ?", (goal_id,))
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 10')
    return store, control, GoalService(store=store, control_store=control), goal_id


def repair_and_review(setup, service, goal_id, response, actual=None):
    store, router, _, _, _, _, root = setup
    outcome, = service.escalate_failed_tasks(goal_id)
    repair = outcome['to_task_id']
    assert service.escalate_failed_tasks(goal_id) == ()
    old = artifact_handoff._load_evidence(store.get_task(repair), 'ReviewRepair', store.get_task(repair).execution_id)
    source = artifact_handoff._producer_worktree(store, store.get_task(old['producer']['task_id']),
        goal_service.functional_evidence(store.get_task(old['producer']['task_id'])))
    # Use the fixture repository's shared object database, just as production does.
    implementation = LocalImplementation(source, old['producer']['commit'], f'value = 2\n# repaired {repair}\n')
    router.replace('opencode', lambda **kwargs: implementation)
    result = ordinary(store, router).execute(repair, workspace_root=str(root / 'repair'))
    assert result.success, result
    store.append_usage_observation(repair, observation_id=f'repair-author-{repair}', execution_id=store.get_task(repair).execution_id,
        role='executor', model_id='local/repair-author', provider_id='local', source_kind='assistant_message',
        source_id='repair-turn', status='UNKNOWN')
    reopened = TaskStore(store.db_path)
    try:
        resumed = GoalService(store=reopened, control_store=PlatformControlStore(reopened),
                              task_resolver=service.task_resolver)
        refreshed, = resumed.escalate_failed_tasks(goal_id)
        assert resumed.escalate_failed_tasks(goal_id) == ()
    finally:
        reopened._conn.close()
    review = refreshed['to_task_id']
    router.replace('opencode', lambda **kwargs: Reviewer(source, kwargs['base_ref'], response=response, actual=actual))
    from test_functional_execution import durable
    result = durable(store, router).execute_durable_single(review, workspace_root=str(root / 'fresh'))
    return repair, review, result


def test_reject_fix_fresh_accept(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    routed_authors = []
    def resolve(plan, *, goal, author_models=(), author_bindings=(), author_executors=()):
        if plan.kind != "review":
            return {"executor_kind": "opencode", "binding_ref": "local-test-binding",
                    "model_id": "local/repair-author", "reason": "repair route"}
        routed_authors.append(set(author_models))
        assert not author_bindings
        assert set(author_executors) == {"opencode"}
        return {'executor_kind': 'opencode', 'binding_ref': 'local-test-binding',
                'reason': 'fixture independent reviewer', 'model_id': 'local/test'}
    service.task_resolver = resolve
    repair, review, result = repair_and_review(review_setup, service, goal_id, '{"verdict":"ACCEPT","findings":[]}')
    assert result.success, result
    assert routed_authors == [{'local/author', 'local/repair-author'}]
    assert service.escalate_failed_tasks(goal_id) == ()
    authors = goal_service.GoalService(store=store, control_store=control)._review_authors(
        service._normalize_task(control.get_goal(goal_id).tasks[1], seq=1), control.get_goal(goal_id),
        {raw['id']: service._normalize_task(raw, seq=i) for i, raw in enumerate(control.get_goal(goal_id).tasks)})
    assert set(authors['author_models']) == {'local/author', 'local/repair-author'}
    assert artifact_handoff.load_input_binding(store.get_task(review))['producer']['task_id'] == repair
    assert store.get_task(review_setup[3]).status == 'FAILED'
    with pytest.raises(TaskStoreError, match='artifact_goal_link_changed'):
        artifact_handoff.bind_consumer_input(store, review_setup[3], allow_create=False)


def test_configured_second_reject_blocks_without_third_round(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    service.max_review_rounds = 2
    _, review, result = repair_and_review(review_setup, service, goal_id, REJECT)
    assert result.failure_classification == 'model_review_rejected', result
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count
    assert store.get_task(review).status == 'BLOCKED'
    assert any(e.metadata.get('reason') == 'model_review_round_limit' or
               e.metadata.get('decision', {}).get('reason') == 'model_review_round_limit'
               for e in store.get_events(review))


def test_concurrent_reopen_idempotent(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    def escalate(_):
        reopened = TaskStore(store.db_path)
        try:
            return GoalService(store=reopened, control_store=PlatformControlStore(reopened)).escalate_failed_tasks(goal_id)
        finally:
            reopened._conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(escalate, range(2)))
    assert sum(len(result) for result in results) == 1
    assert len(control.list_task_escalations(goal_id)) == 1
    assert escalate(0) == ()


def test_expired_window_no_repair(review_setup):
    store, _, service, goal_id = rejected(review_setup)
    store._conn.execute("UPDATE platform_autonomous_windows SET expires_at = '2000-01-01T00:00:00Z'")
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count


def test_link_failure_rolls_back_creation(review_setup, monkeypatch):
    store, control, service, goal_id = rejected(review_setup)
    count = store.count_tasks()
    original = goal_service.freeze_handoff_contract
    def crash(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('crash')
    monkeypatch.setattr(goal_service, 'freeze_handoff_contract', crash)
    with pytest.raises(RuntimeError, match='crash'):
        service.escalate_failed_tasks(goal_id)
    assert store.count_tasks() == count
    assert control.list_task_escalations(goal_id) == ()
    monkeypatch.setattr(goal_service, 'freeze_handoff_contract', original)
    assert len(service.escalate_failed_tasks(goal_id)) == 1


@pytest.mark.parametrize('response', ['invalid', REJECT])
def test_unverified_reject_never_repairs(review_setup, response):
    store, _, service, goal_id = rejected(review_setup)
    store._conn.execute("UPDATE task_evidence SET detail = ? WHERE category = 'ModelReview'", (response,))
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count


@pytest.mark.parametrize("author", ["alias/author:free", "alias/repair-author:free"])
def test_fresh_review_excludes_entire_author_history(review_setup, author):
    _, _, service, goal_id = rejected(review_setup)
    _, _, result = repair_and_review(review_setup, service, goal_id,
        '{"verdict":"ACCEPT","findings":[]}', actual=[author])
    assert result.failure_classification == 'review_not_independent'


def test_window_retry_budget_not_expanded(review_setup):
    store, _, service, goal_id = rejected(review_setup)
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 1')
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count


@pytest.mark.parametrize('failure', ['timeout', 'executor_failure', 'transport_error', 'model_review_invalid_output'])
def test_review_without_verdict_retries_without_repair(review_setup, failure):
    store, _, producer, review, _, options, _ = review_setup
    options['response'] = 'unparseable review'
    assert run_review(review_setup).failure_classification == 'model_review_invalid_output'
    assert not any(row['category'] == 'ModelReview' for row in store.get_task(review).evidence_refs)
    control = PlatformControlStore(store)
    goal_id = control.goal_id_for_task(producer)
    store._conn.execute("UPDATE platform_goals SET orchestration_mode = 'agent_team' WHERE id = ?", (goal_id,))
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 1')
    store._conn.execute('UPDATE tasks SET failure_classification = ? WHERE id = ?', (failure, review))
    selections = []
    def resolve(plan, *, goal, author_models, author_bindings, **kwargs):
        selections.append(set(author_models))
        assert not author_bindings
        return {'executor_kind': 'opencode', 'binding_ref': 'local-test-binding',
                'reason': 'sole independent reviewer', 'model_id': 'local/test'}
    service = GoalService(store=store, control_store=control, task_resolver=resolve)
    count = store.count_tasks()
    retry, = service.escalate_failed_tasks(goal_id)
    assert retry['from_task_id'] == review
    retried = store.get_task(retry['to_task_id'])
    assert retried.binding_ref == store.get_task(review).binding_ref
    assert selections == [{'local/author'}]
    assert store.count_tasks() == count + 1
    assert not any(row['reason'].startswith('model_review_repair:')
                   for row in control.list_task_escalations(goal_id))
    assert next(row for row in control.list_goal_tasks(goal_id) if row['plan_task_id'] == 'A')['task_id'] == producer
    store._conn.execute("UPDATE tasks SET status = 'FAILED', failure_classification = ? WHERE id = ?",
                        (failure, retried.id))
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count + 1
    assert len(control.list_task_escalations(goal_id)) == 1


def test_mutation_after_reject_is_not_feedback(review_setup):
    store, _, service, goal_id = rejected(review_setup)
    reviewer = review_setup[4][0]
    (reviewer.prepared.worktree / 'app.py').write_text('value = 9\n')
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count


def test_default_three_review_rounds_exhaustion(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    assert service.max_review_rounds == 3
    _, second, result = repair_and_review(review_setup, service, goal_id, REJECT)
    assert result.failure_classification == "model_review_rejected"
    _, third, result = repair_and_review(review_setup, service, goal_id, REJECT)
    assert second != third and result.failure_classification == "model_review_rejected"
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.get_task(third).status == "BLOCKED"
    assert store.count_tasks() == count
    repairs = [row for row in control.list_task_escalations(goal_id)
               if row["reason"].startswith("model_review_repair:")]
    assert len(repairs) == 2


def test_actual_same_author_model_refused(review_setup):
    review_setup[5]["actual"] = ["alias/author:free"]
    result = run_review(review_setup)
    assert result.failure_classification == "review_not_independent"
    assert not [row for row in review_setup[0].get_task(review_setup[3]).evidence_refs
                if row.get("category") == "ModelReview"]


def test_free_retries_do_not_block_a_review_repair_round(review_setup):
    # Decision B: a not-the-model's-fault retry elsewhere in the goal spends no max_retries.
    store, control, service, goal_id = rejected(review_setup)
    _, _, producer, review, *_ = review_setup
    goal = control.get_goal(goal_id)
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 2')
    store._conn.execute(
        "INSERT INTO platform_task_escalations (goal_id, goal_revision, plan_task_id, step, from_task_id, to_task_id, "
        "from_role, to_role, reason, created_at) VALUES (?, ?, 'T-other', 1, ?, ?, 'coder', 'coder', "
        "'host_retry:executor_stalled', '2026-01-01T00:00:00Z')", (goal_id, goal.revision, producer, review))
    store._conn.commit()
    outcome, = service.escalate_failed_tasks(goal_id)
    assert outcome['to_task_id'] not in {producer, review}


def test_rejected_review_repair_is_runnable_and_goal_stays_running(review_setup):
    # 2026-11-15: a rejected review left its link FAILED, so the goal turned BLOCKED
    # and the queued repair was never claimed (only RUNNING goals' tasks are).
    store, control, service, goal_id = rejected(review_setup)
    goal = control.get_goal(goal_id)
    outcome, = service.escalate_failed_tasks(goal_id)
    repair = outcome['to_task_id']
    assert store.get_task(repair).status == 'QUEUED'
    assert control.get_goal(goal_id).status == 'RUNNING'
    assert repair in control.runnable_tasks(goal.window_id)
    # The repaired artifact still needs its refreshed review: not COMPLETED yet.
    store._conn.execute("UPDATE tasks SET status = 'READY_FOR_REVIEW' WHERE id = ?", (repair,))
    assert control.refresh_goal_status(goal_id).status == 'RUNNING'
    # A failed repair blocks the goal again.
    store._conn.execute("UPDATE tasks SET status = 'FAILED' WHERE id = ?", (repair,))
    assert control.refresh_goal_status(goal_id).status == 'BLOCKED'


def test_repair_replaced_by_a_later_attempt_still_keeps_the_goal_running(review_setup):
    # 2026-11-15: an Owner retry or a 429 retry replaced the repair; the review then
    # waited on that later attempt, but the goal was BLOCKED again.
    store, control, service, goal_id = rejected(review_setup)
    goal = control.get_goal(goal_id)
    outcome, = service.escalate_failed_tasks(goal_id)
    repair = store.get_task(outcome['to_task_id'])
    store._conn.execute("UPDATE tasks SET status = 'FAILED', failure_classification = 'api_error_429' WHERE id = ?",
                        (repair.id,))
    assert control.refresh_goal_status(goal_id).status == 'BLOCKED'
    retry = store.create_task(title=repair.title, repository=repair.repository, executor_kind=repair.executor_kind,
                              binding_ref=repair.binding_ref)
    control.escalate_goal_task(goal_id, goal_revision=goal.revision, plan_task_id=outcome['plan_task_id'],
        from_task_id=repair.id, to_task_id=retry.id, from_role='coder', to_role='coder', reason='owner_retry')
    assert control.refresh_goal_status(goal_id).status == 'RUNNING'
    assert retry.id in control.runnable_tasks(goal.window_id)
    # A failed later attempt blocks the goal again.
    store._conn.execute("UPDATE tasks SET status = 'FAILED' WHERE id = ?", (retry.id,))
    assert control.refresh_goal_status(goal_id).status == 'BLOCKED'


def test_a_rejection_parked_for_budget_is_repaired_once_the_budget_is_free(review_setup):
    """2026-11-19 (#1551 goal): the first reviewed feature was parked as routing_retry_budget_exhausted
    because host-side history was counted as model failures. Once the budget is free (here: raised;
    live: the history reclassified), the same verified REJECT gets its repair and the goal runs again."""
    store, control, service, goal_id = rejected(review_setup)
    review = review_setup[3]
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 0')
    store._conn.commit()
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    parked = store.get_task(review)
    assert (parked.status, parked.failure_classification) == ('BLOCKED', 'routing_retry_budget_exhausted')
    # Later ticks while the budget is still spent neither raise nor record the block again.
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count
    assert sum(e.type == 'MODEL_SELECTION_FAILED' for e in store.get_events(review)) == 1
    assert control.get_goal(goal_id).status == 'BLOCKED'
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 10')
    store._conn.commit()
    outcome, = service.escalate_failed_tasks(goal_id)
    repair = store.get_task(outcome['to_task_id'])
    assert repair.status == 'QUEUED' and outcome['from_task_id'] == review_setup[2]
    assert artifact_handoff._load_evidence(repair, 'ReviewRepair', repair.execution_id)['review_task_id'] == review
    # The parked review no longer blocks the goal, so its QUEUED repair can be claimed.
    assert control.get_goal(goal_id).status == 'RUNNING'
    assert service.escalate_failed_tasks(goal_id) == ()


def test_a_parked_rejection_whose_repair_cannot_be_routed_stays_parked_without_raising(review_setup):
    """#1690 review nit: routing the repair of a budget-parked review may fail; the review must stay
    parked rather than be re-blocked (which raises and rolls back every tick for the goal)."""
    store, control, service, goal_id = rejected(review_setup)
    review = review_setup[3]
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 0')
    store._conn.commit()
    assert service.escalate_failed_tasks(goal_id) == ()
    store._conn.execute('UPDATE platform_autonomous_windows SET max_retries = 10')
    store._conn.commit()

    def no_model(plan, *, goal, **kwargs):
        raise TaskStoreError('no_runnable_model')
    service.task_resolver = no_model
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count
    parked = store.get_task(review)
    assert (parked.status, parked.failure_classification) == ('BLOCKED', 'routing_retry_budget_exhausted')


@pytest.mark.parametrize("expires, repaired", [("", True), ("2999-01-01T00:00:00Z", False)])
def test_continuous_run_repairs_a_rejection_after_the_retry_budget_is_spent(review_setup, expires, repaired):
    """P0-D2 r8: one failed coding attempt left 1 of 2 retries, and a repair asked for 2."""
    store, control, service, goal_id = rejected(review_setup)
    _, _, producer, review, *_ = review_setup
    goal = control.get_goal(goal_id)
    store._conn.execute("UPDATE platform_autonomous_windows SET max_retries = 2, expires_at = ?, "
                        "confirmation_mode = 'OWNER_WINDOW'", (expires,))
    store._conn.execute(
        "INSERT INTO platform_task_escalations (goal_id, goal_revision, plan_task_id, step, from_task_id, to_task_id, "
        "from_role, to_role, reason, created_at) VALUES (?, ?, 'T-other', 1, ?, ?, 'coder', 'coder', "
        "'failed:deterministic_validation_failure', '2026-01-01T00:00:00Z')", (goal_id, goal.revision, producer, review))
    store._conn.commit()
    assert bool(service._repair_rejected_reviews(goal_id)) is repaired


def test_continuous_run_still_stops_at_the_review_round_limit(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    service.max_review_rounds = 1
    store._conn.execute("UPDATE platform_autonomous_windows SET expires_at = '', confirmation_mode = 'OWNER_WINDOW'")
    store._conn.commit()
    assert service._repair_rejected_reviews(goal_id) == ()
    assert store.get_task(review_setup[3]).failure_classification == 'model_review_round_limit'


def test_review_loop_rows_spend_retries_only_outside_a_continuous_run():
    history = [{"plan_task_id": "T1", "reason": "model_review_repair:x", "cause": ""},
               {"plan_task_id": "T2", "reason": "model_review_refresh:x", "cause": ""},
               {"plan_task_id": "T1", "reason": "failed:deterministic_validation_failure", "cause": ""}]
    assert goal_service._routing_retries_spent(history) == 3
    assert goal_service._routing_retries_spent(history, patient=True) == 1


def test_review_authors_allows_truncated_failed_claude_attempt_with_usage_observation(review_setup):
    from reverse_agent.platform_v1 import model_review
    store, control, service, goal_id = rejected(review_setup)
    _, _, producer, review, *_ = review_setup
    goal = control.get_goal(goal_id)
    prior = store.create_task(title="truncated", repository=goal.repository,
                              executor_kind="claude_code", binding_ref="claude-opus")
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='claude_code_stream_limit_exceeded' WHERE id=?",
                        (prior.id,))
    store._conn.execute(
        "INSERT INTO platform_task_escalations (goal_id, goal_revision, plan_task_id, step, from_task_id, to_task_id, "
        "from_role, to_role, reason, created_at) VALUES (?, ?, 'A', 1, ?, ?, 'coder', 'coder', "
        "'failed:claude_code_stream_limit_exceeded', '2026-01-01T00:00:00Z')",
        (goal_id, goal.revision, prior.id, producer))
    store.append_usage_observation(prior.id, observation_id="obs-trunc-1", execution_id=prior.execution_id,
                                   role="executor", model_id="opus", provider_id="claude",
                                   source_kind="executor", source_id="turn-1", status="UNKNOWN")
    store._conn.commit()
    binding = artifact_handoff.bind_consumer_input(store, review, allow_create=False)
    _, _, actual = model_review.review_authors(store, store.get_task(review), binding)
    assert "opus" in actual
    # Ensure a FAILED attempt with an unexpected failure classification still enforces EXECUTOR_COMPLETED.
    store._conn.execute("UPDATE tasks SET failure_classification='deterministic_validation_failure' WHERE id=?", (prior.id,))
    store._conn.commit()
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        model_review.review_authors(store, store.get_task(review), binding)
    # Ensure a READY_FOR_REVIEW claude_code attempt still enforces EXECUTOR_COMPLETED models match.
    store._conn.execute("UPDATE tasks SET status='READY_FOR_REVIEW' WHERE id=?", (prior.id,))
    store._conn.commit()
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        model_review.review_authors(store, store.get_task(review), binding)


def test_advisory_only_reject_does_not_trigger_repair(review_setup):
    import json
    store, _, producer, _, _, options, _ = review_setup
    options["response"] = json.dumps({
        "verdict": "REJECT",
        "findings": [{"path": "app.py", "line": 1, "severity": "low", "message": "style note"}],
    })
    assert run_review(review_setup).success
    control = PlatformControlStore(store)
    goal_id = control.goal_id_for_task(producer)
    assert GoalService(store=store, control_store=control).escalate_failed_tasks(goal_id) == ()


def test_incremental_review_receives_previous_findings_and_repair_diff(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    _, router, _, _, _, _, root = review_setup
    outcome, = service.escalate_failed_tasks(goal_id)
    repair = outcome["to_task_id"]
    old = artifact_handoff._load_evidence(store.get_task(repair), "ReviewRepair", store.get_task(repair).execution_id)
    source = artifact_handoff._producer_worktree(
        store, store.get_task(old["producer"]["task_id"]),
        goal_service.functional_evidence(store.get_task(old["producer"]["task_id"])),
    )
    implementation = LocalImplementation(source, old["producer"]["commit"], f"value = 2\n# repaired {repair}\n")
    router.replace("opencode", lambda **kwargs: implementation)
    assert ordinary(store, router).execute(repair, workspace_root=str(root / "repair")).success
    store.append_usage_observation(
        repair, observation_id=f"repair-author-{repair}", execution_id=store.get_task(repair).execution_id,
        role="executor", model_id="local/repair-author", provider_id="local",
        source_kind="assistant_message", source_id="repair-turn", status="UNKNOWN",
    )
    refreshed, = service.escalate_failed_tasks(goal_id)
    seen = []
    router.replace(
        "opencode",
        lambda **kwargs: (seen.append(Reviewer(source, kwargs["base_ref"])), seen[-1])[1],
    )
    from test_functional_execution import durable
    result = durable(store, router).execute_durable_single(refreshed["to_task_id"], workspace_root=str(root / "fresh"))
    assert result.success, result
    assert "incremental_review" in seen[0].prompt
    assert "previous_findings" in seen[0].prompt and "Incorrect value" in seen[0].prompt
    assert "repair_diff" in seen[0].prompt and f"# repaired {repair}" in seen[0].prompt
