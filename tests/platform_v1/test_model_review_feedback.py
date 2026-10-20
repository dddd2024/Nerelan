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
    implementation = LocalImplementation(source, old['producer']['commit'], 'value = 2\n# repaired\n')
    router.replace('opencode', lambda **kwargs: implementation)
    result = ordinary(store, router).execute(repair, workspace_root=str(root / 'repair'))
    assert result.success, result
    store.append_usage_observation(repair, observation_id='repair-author', execution_id=store.get_task(repair).execution_id,
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
    def resolve(plan, *, goal, author_models, author_bindings):
        routed_authors.append(set(author_models))
        assert not author_bindings
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


def test_second_reject_blocks_without_third_round(review_setup):
    store, control, service, goal_id = rejected(review_setup)
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


def test_mutation_after_reject_is_not_feedback(review_setup):
    store, _, service, goal_id = rejected(review_setup)
    reviewer = review_setup[4][0]
    (reviewer.prepared.worktree / 'app.py').write_text('value = 9\n')
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal_id) == ()
    assert store.count_tasks() == count
