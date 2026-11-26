from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from test_context_builder import repo, _isolated_git, _setup, _head
from _local_client_fixture import client_session, client_headers
from reverse_agent.platform_v1.agent_planner import PlannerOutput
from reverse_agent.platform_v1.context_builder import ContextBuilderError, build_context_packet, render_context_packet
from reverse_agent.platform_v1.context_recovery import ContextRecoveryService
from reverse_agent.platform_v1.context_optimization import snapshot_digest
from reverse_agent.platform_v1.context_builder import _canonical_digest
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_service import _handler_factory
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


def setup_service(tmp_path, repo, runner=None, **scope):
    db = tmp_path / 's.db'
    store, goal, first, second, other = _setup(db)
    service = ContextRecoveryService(store=store, workspace_for=lambda _: (str(repo), _head(repo)),
        summary_binding=lambda: ('codex', 'configured-model'), summary_runner=runner, **scope)
    return service, store, first, db


def pressure(store, task):
    for index in range(80):
        store.add_event(task.id, event_type='VALIDATED',
            title=f'DECISION-{index}' if index == 1 else f'event-{index}', description=f'record-{index} 中文恢复' * 150,
            raw_log='PRIVATE-RAW', metadata={'secret': 'PRIVATE-META'})


def test_pressure_budget_deterministic_browse_and_original_retrieval(tmp_path, repo):
    service, store, task, _ = setup_service(tmp_path, repo)
    pressure(store, task)
    full = service._full(task.id)
    packet = service.packet(task.id, budget_bytes=8192)
    text = render_context_packet(packet)
    assert len(text.encode()) <= 8192
    assert packet['task'] == full['task']
    assert packet['summary_trigger']['needed']
    assert packet['compression']['history_omitted'] > 0
    assert text == render_context_packet(service.packet(task.id, budget_bytes=8192))
    assert 'PRIVATE-RAW' not in text and 'PRIVATE-META' not in text
    snapshot = packet['retrieval']['snapshot_digest']
    browse = service.retrieve(task.id, expected_snapshot=snapshot, budget_bytes=512)
    assert browse['matches'] and len(render_context_packet(browse).encode()) <= 512
    last = full['history'][-1]
    found = service.retrieve(task.id, expected_snapshot=snapshot, refs=(last['id'],), budget_bytes=16384)
    assert found['matches'][0]['content'] == last
    bounded = service.retrieve(task.id, expected_snapshot=snapshot, refs=(last['id'],), budget_bytes=512)
    assert bounded['matches'][0]['truncated']
    store.add_event(task.id, event_type='VALIDATED', title='new', description='change')
    with pytest.raises(ContextBuilderError, match='context_snapshot_stale'):
        service.retrieve(task.id, expected_snapshot=snapshot)


def test_summary_explicit_once_cache_and_cross_agent_restart(tmp_path, repo):
    calls = []
    def runner(**kwargs):
        calls.append(kwargs)
        return PlannerOutput('Decision: preserve the original references.\n'
                             'Uncertain: current status.\napi_key=synthetic-secret-value', {'input_tokens': 12})
    service, store, task, db = setup_service(tmp_path, repo, runner)
    pressure(store, task)
    packet = service.packet(task.id)
    assert not calls
    snapshot = packet['retrieval']['snapshot_digest']
    summary = service.summarize(task.id, expected_snapshot=snapshot)
    assert summary['status'] == 'COMPLETED' and len(calls) == 1
    assert 'synthetic-secret-value' not in render_context_packet(summary)
    assert service.summarize(task.id, expected_snapshot=snapshot) == summary and len(calls) == 1
    handoff = service.handoff(task.id, expected_snapshot=snapshot, from_agent='planner', to_agent='reviewer')
    store._conn.close()
    reopened = TaskStore(str(db))
    resumed = ContextRecoveryService(store=reopened, workspace_for=service.workspace_for)
    recovered = resumed.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='reviewer')
    assert recovered['packet']['advisory_summary']['summary'] == summary['summary']
    assert recovered['packet']['task']['id'] == task.id
    assert recovered['authority'] == 'NONE'
    assert len(render_context_packet(recovered['packet']).encode()) <= 16384
    # The successor sees fresh state; the old prose never becomes state truth.
    reopened._conn.execute("UPDATE tasks SET status='READY_FOR_REVIEW' WHERE id=?", (task.id,))
    updated = resumed.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='reviewer')
    assert updated['packet']['task']['status'] == 'READY_FOR_REVIEW'
    with pytest.raises(ContextBuilderError, match='context_handoff_stale'):
        resumed.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='other')
    reopened._conn.execute("UPDATE tasks SET execution_id='next-execution' WHERE id=?", (task.id,))
    with pytest.raises(ContextBuilderError, match='context_handoff_stale'):
        resumed.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='reviewer')


def test_summary_completion_race_and_restricted_view(tmp_path, repo):
    service, store, task, _ = setup_service(tmp_path, repo)
    pressure(store, task)
    def runner(**kwargs):
        store.add_event(task.id, event_type='VALIDATED', title='racing event', description='new')
        return PlannerOutput('stale model prose')
    service.summary_runner = runner
    snapshot = snapshot_digest(service._full(task.id))
    result = service.summarize(task.id, expected_snapshot=snapshot)
    assert result['status'] == 'FAILED' and result['error'] == 'context_snapshot_stale'
    assert 'advisory_summary' not in service.packet(task.id)
    service.visible_task_ids = (task.id,)
    restricted = service.packet(task.id)
    assert restricted['retrieval']['snapshot_digest'] != snapshot
    with pytest.raises(ContextBuilderError, match='context_summary_scope_restricted'):
        service.summarize(task.id, expected_snapshot=restricted['retrieval']['snapshot_digest'])
    with pytest.raises(ContextBuilderError, match='context_reference_unavailable'):
        service.retrieve(task.id, expected_snapshot=restricted['retrieval']['snapshot_digest'], refs=('hidden-ref',))


def test_authenticated_http_context_routes_do_not_grant_browser_paths(tmp_path, repo):
    service, store, task, _ = setup_service(tmp_path, repo)
    session = client_session()
    handler = _handler_factory(store, ExecutorRouter(), allowed_origin='http://localhost:5173',
        local_client_session=session, context_recovery=service)
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(action, payload, authorized=True):
        conn = http.client.HTTPConnection(*server.server_address, timeout=10)
        headers = client_headers() if authorized else {}
        headers['Content-Type'] = 'application/json'
        conn.request('POST', f'/api/tasks/{task.id}/context/{action}', json.dumps(payload), headers)
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result
    try:
        assert request('packet', {}, False)[0] == 401
        status, packet = request('packet', {'workspace': 'C:/malicious-path', 'visible_task_ids': []})
        assert status == 200 and packet['task']['id'] == task.id
        snapshot = packet['retrieval']['snapshot_digest']
        status, handoff = request('handoff', dict(expected_snapshot=snapshot, from_agent='a', to_agent='b'))
        assert status == 200
        status, recovered = request('recover', dict(handoff_id=handoff['handoff_id'], agent_id='b'))
        assert status == 200 and recovered['packet']['task']['id'] == task.id
        assert request('retrieve', {'expected_snapshot': 'stale'})[0] == 409
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def test_pending_summary_restart_never_repeats_unknown_paid_call(tmp_path, repo):
    service, store, task, db = setup_service(tmp_path, repo)
    pressure(store, task)
    snapshot = snapshot_digest(service._full(task.id))
    def crash(**kwargs):
        raise KeyboardInterrupt('simulated process loss after paid call reservation')
    service.summary_runner = crash
    with pytest.raises(KeyboardInterrupt):
        service.summarize(task.id, expected_snapshot=snapshot)
    store._conn.close()
    reopened = TaskStore(str(db))
    def unexpected(**kwargs):
        pytest.fail('must not retry an unknown paid call on restart')
    resumed = ContextRecoveryService(store=reopened, workspace_for=service.workspace_for,
        summary_binding=service.summary_binding, summary_runner=unexpected)
    result = resumed.summarize(task.id, expected_snapshot=snapshot)
    assert result['status'] == 'RUNNING'
    assert 'advisory_summary' not in resumed.packet(task.id)


def test_handoff_rejects_visibility_and_scoped_git_drift(tmp_path, repo):
    service, store, task, _ = setup_service(tmp_path, repo, visible_paths=('a.txt',))
    snapshot = snapshot_digest(service._full(task.id))
    handoff = service.handoff(task.id, expected_snapshot=snapshot, from_agent='a', to_agent='b')
    service.visible_task_ids = (task.id,)
    with pytest.raises(ContextBuilderError, match='context_handoff_stale'):
        service.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='b')
    service.visible_task_ids = None
    (repo / 'a.txt').write_text('changed\n', encoding='utf-8')
    with pytest.raises(ContextBuilderError, match='context_handoff_stale'):
        service.recover(task.id, handoff_id=handoff['handoff_id'], agent_id='b')


def test_malformed_derived_cache_is_ignored_without_losing_current_truth(tmp_path, repo):
    service, store, task, _ = setup_service(tmp_path, repo)
    packet = service.packet(task.id)
    malformed = {'authority': 'NONE', 'status': 'COMPLETED', 'summary': 'bad cache',
        'scope_digest': packet['retrieval']['scope_digest'],
        'input_snapshot_digest': packet['retrieval']['snapshot_digest'], 'sources': [None]}
    store.add_evidence(task.id, category='ContextSummary', label='bad',
        value=render_context_packet(malformed), status='COMPLETED', raw_json_digest=_canonical_digest(malformed))
    fresh = service.packet(task.id)
    assert fresh['task'] == packet['task'] and 'advisory_summary' not in fresh
    missing_usage = {**malformed, 'sources': [], 'summary': 'advisory with unknown usage'}
    store.add_evidence(task.id, category='ContextSummary', label='unknown-usage',
        value=render_context_packet(missing_usage), status='COMPLETED', raw_json_digest=_canonical_digest(missing_usage))
    assert service.packet(task.id)['advisory_summary']['usage'] is None


def _make_local_repo(tmp_path):
    from tests.platform_v1.test_context_builder import _git
    path = tmp_path / 'repo'
    path.mkdir()
    _git(path, 'init', '-q')
    _git(path, 'remote', 'add', 'origin', 'https://github.com/octo/demo.git')
    (path / 'a.txt').write_text('alpha\n', encoding='utf-8')
    _git(path, 'add', 'a.txt')
    _git(path, 'commit', '-q', '-m', 'init')
    return path


def test_compact_context_preserves_objective_over_markdown_at_p0b_budget(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's1.db')
    objective = 'P0B_OBJECTIVE_MARKER ' + ('fix goal objective clipping ' * 70)
    spec_md = '# Spec\n' + ('detailed spec section\n' * 450)
    plan_md = '# Plan\n' + ('detailed plan section\n' * 450)
    store._conn.execute(
        'UPDATE platform_goals SET objective = ?, spec_markdown = ?, plan_markdown = ? WHERE id = ?',
        (objective, spec_md, plan_md, goal.id),
    )
    store._conn.commit()
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    assert len(render_context_packet(full).encode()) > 16384
    compact = compact_context(full, budget_bytes=16384)
    assert compact['goal']['objective'] == objective
    assert compact['goal']['spec_markdown'] == ''
    assert compact['goal']['plan_markdown'] == ''
    assert compact['compression']['goal_text_omitted'] is True
    assert len(render_context_packet(compact).encode()) <= 16384


def test_compact_context_clips_oversized_objective_while_reserving_critical_history(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's2.db')
    objective = 'OBJ_START ' + ('x' * 6000)
    for i in range(10):
        store.add_event(first.id, event_type='EXECUTOR_PROGRESS', title=f'step-{i}',
                        description='progress ' * 10)
    store.add_event(first.id, event_type='VALIDATED', title='DECISION keep critical hint',
                    description='Critical decision rationale')
    store._conn.execute(
        'UPDATE platform_goals SET objective = ?, spec_markdown = "", plan_markdown = "" WHERE id = ?',
        (objective, goal.id),
    )
    store._conn.commit()
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    compact = compact_context(full, budget_bytes=3072)
    assert compact['goal']['objective'].startswith('OBJ_START ')
    assert len(compact['goal']['objective']) < len(objective)
    assert compact['compression']['goal_text_omitted'] is True
    assert any('DECISION' in event['title'] for event in compact['history'])
    assert len(render_context_packet(compact).encode()) <= 3072


def test_compact_context_empty_restricted_objective_keeps_goal_text_omitted_false(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's3.db')
    store._conn.execute(
        'UPDATE platform_goals SET objective = "", spec_markdown = "", plan_markdown = "" WHERE id = ?',
        (goal.id,),
    )
    store._conn.commit()
    for i in range(30):
        store.add_event(first.id, event_type='EXECUTOR_PROGRESS', title=f'ev-{i}', description='event body ' * 15)
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    assert len(render_context_packet(full).encode()) > 3072
    compact = compact_context(full, budget_bytes=3072)
    assert compact['goal']['objective'] == ''
    assert compact['goal']['spec_markdown'] == ''
    assert compact['goal']['plan_markdown'] == ''
    assert compact['compression']['goal_text_omitted'] is False
    assert compact['compression']['history_omitted'] > 0
    assert len(render_context_packet(compact).encode()) <= 3072


def test_compact_context_clips_multibyte_utf8_objective_by_byte_budget(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's4.db')
    objective = '中文目标' * 500
    assert len(objective) == 2000 and len(objective.encode('utf-8')) == 6000
    store._conn.execute(
        'UPDATE platform_goals SET objective = ?, spec_markdown = "", plan_markdown = "" WHERE id = ?',
        (objective, goal.id),
    )
    store._conn.commit()
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    compact = compact_context(full, budget_bytes=5120)
    assert len(compact['goal']['objective'].encode('utf-8')) > len(objective)
    assert compact['goal']['objective'].startswith('中文目标')
    assert len(compact['goal']['objective']) < len(objective)
    assert compact['compression']['goal_text_omitted'] is True
    assert len(render_context_packet(compact).encode()) <= 5120


def test_compact_context_one_byte_overflow_keeps_goal_text_omitted_honest(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's5.db')
    objective = 'ONE_BYTE_OVERFLOW_CHECK ' + ('x' * 600)
    store._conn.execute(
        'UPDATE platform_goals SET objective = ?, spec_markdown = "", plan_markdown = "" WHERE id = ?',
        (objective, goal.id),
    )
    store._conn.commit()
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    exact_bytes = len(render_context_packet(compact_context(full, budget_bytes=65536)).encode())
    assert exact_bytes - 1 >= 1024
    compact = compact_context(full, budget_bytes=exact_bytes - 1)
    assert len(render_context_packet(compact).encode()) <= exact_bytes - 1
    if compact['compression']['goal_text_omitted']:
        assert compact['goal']['objective'] != full['goal']['objective']


def test_compact_context_recovers_objective_after_blanking_many_task_titles(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's6.db')
    objective = 'RECOVER_ME_OBJECTIVE'
    store._conn.execute(
        'UPDATE platform_goals SET objective = ?, spec_markdown = "", plan_markdown = "" WHERE id = ?',
        (objective, goal.id),
    )
    for i in range(25):
        t = store.create_task(
            title=f'long-task-title-{i:02d}-' + ('t' * 42),
            repository='octo/demo',
            executor_kind='deterministic_fixture',
        )
        store._conn.execute(
            'INSERT INTO platform_goal_task_links (goal_id, goal_revision, plan_task_id, task_id, '
            'dependencies_json, seq) VALUES (?, ?, ?, ?, "[]", ?)',
            (goal.id, goal.revision, f'extra-{i}', t.id, i + 10),
        )
    store._conn.commit()
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=65536)
    empty_obj_packet = compact_context(full, budget_bytes=65536)
    for task in [empty_obj_packet['task'], *empty_obj_packet['tasks']]:
        task['title'] = task['title'][:64]
    empty_obj_packet['goal']['objective'] = ''
    empty_obj_packet['compression']['goal_text_omitted'] = True
    clipped_titles_empty_obj_bytes = len(render_context_packet(empty_obj_packet).encode())
    blanked_titles_with_obj_packet = compact_context(full, budget_bytes=65536)
    for task in [blanked_titles_with_obj_packet['task'], *blanked_titles_with_obj_packet['tasks']]:
        task['title'] = ''
    blanked_titles_with_obj_bytes = len(render_context_packet(blanked_titles_with_obj_packet).encode())
    assert blanked_titles_with_obj_bytes < clipped_titles_empty_obj_bytes
    tight_budget = max(1024, (blanked_titles_with_obj_bytes + clipped_titles_empty_obj_bytes) // 2)
    assert blanked_titles_with_obj_bytes <= tight_budget < clipped_titles_empty_obj_bytes
    compact = compact_context(full, budget_bytes=tight_budget)
    assert compact['goal']['objective'] == 'RECOVER_ME_OBJECTIVE'
    assert compact['compression']['goal_text_omitted'] is False
    assert len(render_context_packet(compact).encode()) <= tight_budget


def test_compact_context_sheds_activity_history_before_goal_spec_and_plan(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's-order.db')
    spec_md = '# Spec\n' + ('requirement line\n' * 150)
    plan_md = '# Plan\n' + ('plan step line\n' * 150)
    store._conn.execute('UPDATE platform_goals SET spec_markdown = ?, plan_markdown = ? WHERE id = ?',
                        (spec_md, plan_md, goal.id))
    store._conn.commit()
    for i in range(120):
        store.add_event(first.id, event_type='MODEL_SELECTED', title=f'tool-{i}', description='noise ' * 40)
    store.add_event(first.id, event_type='VALIDATED', title='DECISION keep this', description='why')
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=262144)
    assert len(render_context_packet(full).encode()) > 16384
    compact = compact_context(full, budget_bytes=16384)
    assert compact['goal']['spec_markdown'] == spec_md
    assert compact['goal']['plan_markdown'] == plan_md
    assert compact['compression']['goal_text_omitted'] is False
    assert compact['compression']['history_omitted'] > 0
    assert any('DECISION' in event['title'] for event in compact['history'])
    assert len(render_context_packet(compact).encode()) <= 16384


def test_compact_context_empty_history_fit_counts_omissions_within_budget(tmp_path):
    from reverse_agent.platform_v1.context_optimization import compact_context
    r = _make_local_repo(tmp_path)
    store, goal, first, _, _ = _setup(tmp_path / 's-edge.db')
    for i in range(100):
        store.add_event(first.id, event_type='MODEL_SELECTED', title=f'e-{i}', description='x' * 200)
    full = build_context_packet(store, task_id=first.id, workspace=r, expected_head=_head(r), budget_bytes=262144)
    probe = compact_context(full, budget_bytes=262144)
    probe['history'] = []
    probe['sources'] = [s for s in probe['sources'] if s['kind'] in {'goal', 'checkpoint', 'git'}
                        or (s['kind'] == 'task' and s['ref'] == probe['task']['id'])]
    for budget in range(len(render_context_packet(probe).encode()) - 8,
                        len(render_context_packet(probe).encode()) + 8):
        try:
            compact = compact_context(full, budget_bytes=budget)
        except ContextBuilderError:
            continue
        assert len(render_context_packet(compact).encode()) <= budget
