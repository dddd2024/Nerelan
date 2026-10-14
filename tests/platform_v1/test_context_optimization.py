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
