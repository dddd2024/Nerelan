"""Issue 1248 later Owner requirements, entirely fake transports and observations."""
import json
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import model_router, model_availability, routing_capabilities
from reverse_agent.platform_v1.model_availability import AvailabilityCache, observation
from reverse_agent.platform_v1.run_read_model import _event_projection
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1 import claude_executor, binding_resolver, opencode_executor
from tests.platform_v1.test_model_router import candidate, fixture_host


def select(pool, **kwargs):
    return model_router.select_model(pool, difficulty=kwargs.pop('difficulty', 2), kind='code', **kwargs)


def test_catalog_is_not_verified_and_paid_default_off():
    row = candidate('a', 'new-model', 'paid_api')
    with pytest.raises(model_router.ModelSelectionError) as caught:
        select([row])
    assert caught.value.decision['excluded_candidates'][0]['filter'] == 'paid_spend_disabled'
    row.pop('availability')
    with pytest.raises(model_router.ModelSelectionError) as caught:
        select([row], allow_paid=True)
    assert caught.value.decision['excluded_candidates'][0]['filter'] == 'availability:unverified'


def test_calibration_required_and_measured_first_over_owner_table():
    row = candidate('flash', 'deepseek-v4.1-flash')
    with pytest.raises(ValueError):
        select([row], difficulty=3)
    rows = [{'suite_version': 1, 'binding_id': 'flash', 'kind': 'code', 'difficulty': 4,
             'success': True, 'seconds': 12} for _ in range(3)]
    profiles = routing_capabilities.calibration_profiles(rows)
    profiles['flash']['task_buckets']['code:4']['timeouts'] = 0
    table = {'deepseek-v4.1-flash': {'tiers': {'code': 1}}, 'famous-name': {'tiers': {'code': 5}}}
    result = select([candidate('other', 'famous-name'), row], difficulty=4,
                    profiles=profiles, capability_table=table)
    assert result['binding_ref'] == 'flash' and result['tier_source'] == 'measured'
    assert profiles['flash']['task_buckets']['code:4']['attempts'] == 3
    assert model_router.prior_tier('new-gpt-6-super-opus') == (2, True)
    with pytest.raises(ValueError):
        select([row], difficulty=3, capability_table={'deepseek-v4.1-flash': {'tiers': {'code': 4}}})
    assert select([row], difficulty=2, capability_table={'deepseek-v4.1-flash': {'tiers': {'code': 4}}})['tier_source'] == 'owner_table'


@pytest.mark.parametrize('mutation', [{'suite_version': 2}, {'success': 'yes'}, {'difficulty': True}, {'kind': 'unknown'}])
def test_invalid_calibration_rejected(mutation):
    row = {'suite_version': 1, 'binding_id': 'a', 'kind': 'code', 'difficulty': 2, 'success': True}
    with pytest.raises(ValueError):
        routing_capabilities.calibration_profiles([row | mutation])


def test_cached_probe_daily_persistent_and_globally_rate_limited(tmp_path):
    cache = AvailabilityCache(tmp_path / 'availability.json')
    connection = {'connection_id': 'api', 'auth_method': 'api_key'}
    a, b = candidate('a', 'a'), candidate('b', 'b')
    calls = []
    def probe(row):
        calls.append(row['binding_id'])
        return {'ok': True}
    assert cache.check(a, connection, probe=probe, allow_probe=True, now=100)['state'] == 'AVAILABLE'
    assert cache.check(a, connection, probe=probe, allow_probe=True, now=1000)['state'] == 'AVAILABLE'
    assert cache.check(b, connection, probe=probe, allow_probe=True, now=120)['state'] == 'UNKNOWN'
    assert calls == ['a']
    reloaded = AvailabilityCache(cache.path)
    assert reloaded.check(a, connection, now=1000)['state'] == 'AVAILABLE'
    assert reloaded.check(a, connection, probe=probe, allow_probe=True, now=86501)['state'] == 'AVAILABLE'
    assert calls == ['a', 'a']


def test_unavailable_ttl_transient_and_success_evidence():
    cache = AvailabilityCache()
    connection = {'connection_id': 'api', 'auth_method': 'api_key'}
    row = candidate('a', 'a')
    bad = lambda _: {'ok': False, 'error': 'not allowed for user type [personal_free_user]'}
    result = cache.check(row, connection, probe=bad, allow_probe=True, now=100)
    assert result['state'] == 'UNAVAILABLE' and result['expires_at'] == 86500
    assert result['reason'] == 'not_allowed_for_user_type'
    result = cache.check(row, connection, now=200, recent_success=150)
    assert result['state'] == 'AVAILABLE'
    cache.remember(row, connection, observation(now=201, error='429 timeout'))
    assert cache.check(row, connection, now=210)['penalty'] == .5
    assert model_availability.availability_error('model_not_supported: private details') == 'model_not_supported'


@pytest.mark.parametrize('auth,model', [('external_cli_session', 'gpt'), ('api_key', 'codex/gpt'), ('api_key', 'claude/sonnet'), ('none', 'codex')])
def test_owner_accounts_never_probed(auth, model):
    cache = AvailabilityCache()
    def forbidden(_):
        pytest.fail('Owner quota probe')
    assert cache.check(candidate('a', model), {'auth_method': auth}, probe=forbidden,
                       allow_probe=True, now=10)['state'] == 'UNKNOWN'


def test_host_paid_allowance_scoped_to_window(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    host._control_store = SimpleNamespace(get_window=lambda _: SimpleNamespace(status='ACTIVE'),
        window_policy_binding=lambda _: {'authority': {}})
    goal = SimpleNamespace(window_id='window-1')
    assert not host._routing_paid_allowed(goal)
    assert not host._routing_paid_allowed(goal, {'paid_api_windows': ['other']})
    assert host._routing_paid_allowed(goal, {'paid_api_windows': ['window-1']})
    assert not host._routing_paid_allowed(None, {'paid_api_windows': ['window-1']})


def test_no_paid_probe_without_window_and_enabled_connections_only(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    # Use the real availability gate in this test; all observations are fakes.
    monkeypatch.delattr(host, '_routing_availability')
    calls = []
    host._availability_probe = lambda row: calls.append(row['binding_id']) or {'ok': True}
    row = candidate('a', 'paid')
    connection = {'connection_id': 'api', 'auth_method': 'api_key'}
    assert host._routing_availability(row, connection, allow_paid=False, cost_class='paid_api')['state'] == 'UNKNOWN'
    assert not calls
    assert host._routing_availability(row, connection, allow_paid=True, cost_class='paid_api')['state'] == 'AVAILABLE'


def test_model_selection_failed_is_blocked_and_selected_shows_exclusions():
    task = SimpleNamespace(id='t', execution_id='e')
    projected = _event_projection({'type': 'MODEL_SELECTION_FAILED', 'metadata': {'reason': 'no_willing_model'}}, task=task)
    assert projected['category'] == projected['status'] == 'BLOCKED'
    assert projected['description'] == 'no_willing_model'
    projected = _event_projection({'type': 'MODEL_SELECTED', 'metadata': {'model_id': 'chosen', 'binding_ref': 'b',
        'reason': 'cheapest_qualifying', 'excluded_candidates': [{'model_id': 'large', 'filter': 'quota_exhausted'}]}}, task=task)
    assert 'chosen' in projected['description'] and 'large: quota_exhausted' in projected['description']


def test_namespaced_claude_ids_only_in_relay():
    assert claude_executor.validate_claude_model('copilot/gpt-6-sol', relay_mode=True) == 'copilot/gpt-6-sol'
    with pytest.raises(Exception, match='claude_code_model_id_invalid'):
        claude_executor.validate_claude_model('copilot/gpt-6-sol')
    with pytest.raises(Exception):
        claude_executor.validate_claude_model('provider/model --escape', relay_mode=True)


def test_responses_catalog_selects_native_adapter():
    resolution = binding_resolver.OpenCodeBindingResolution('b', 'c', 'opencode', 'magpie', 'copilot/gpt',
        'http://localhost:1234', 'none', 'unavailable', native_endpoint='/responses')
    config = json.loads(opencode_executor.build_binding_config_content(resolution))
    assert config['provider']['magpie']['npm'] == '@ai-sdk/openai'


def test_initial_no_willing_model_creates_blocked_task(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.setattr(host, '_runnable_bindings', lambda: set())
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({'objective': 'Local research', 'repository': 'dddd2024/Nerelan',
        'idempotency_key': 'all-filtered', 'executor_kind': 'opencode', 'orchestration_mode': 'agent_team'})
    goals.plan(goal.id, expected_revision=1, tasks=[{'id': 'T1', 'title': 'Research', 'instruction': 'local only',
        'difficulty': 2, 'needs': ['security_simulation']}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate(_window_payload(goal.repository)).id)
    task = store.get_task(control.list_goal_tasks(goal.id)[0]['task_id'])
    assert task.status == 'BLOCKED' and task.failure_classification == 'no_willing_model'
    [event] = [event for event in store.get_events(task.id) if event.type == 'MODEL_SELECTION_FAILED']
    assert event.metadata['excluded_candidates']


def test_discovery_observations_survive_restart_and_bind_enabled_models(monkeypatch, tmp_path):
    from reverse_agent.model_access import service as model_service
    from reverse_agent.model_access.store import ModelProfileStore
    host = fixture_host(monkeypatch, tmp_path)
    connection = host._store.upsert_connection({'connection_id': 'fixture-catalog', 'name': 'Catalog',
        'provider': 'openai-compatible', 'base_url': 'https://catalog.example.invalid/v1', 'auth_method': 'none'})
    payload = {'object': 'list', 'data': [{'id': 'copilot/gpt-6-sol', 'context_window': 512000,
        'max_output_tokens': 8000, 'input_modalities': ['text', 'image'], 'native_endpoints': ['/v1/responses']}]}
    def listing(url, headers, timeout):
        assert url.endswith('/models')
        return 200, json.dumps(payload).encode()
    discovered = model_service.discover_connection_models(store=host._store, connection_id=connection['connection_id'],
        live_enabled=True, transport=listing)
    assert discovered['models'] == ['copilot/gpt-6-sol']
    host._routing_bind_discovered()
    [binding] = [row for row in host._store.list_bindings_public() if row['connection_id'] == 'fixture-catalog']
    assert binding['native_endpoint'] == '/responses'
    assert host._routing_model_metadata()['copilot/gpt-6-sol']['context_window'] == 512000
    reopened = ModelProfileStore(state_path=tmp_path / 'model_setup_state.json')
    assert reopened.get_binding_public(binding['binding_id'])['native_endpoint'] == '/responses'
    host._store.upsert_binding({**binding, 'enabled': False})
    host._routing_bind_discovered()
    assert not host._store.get_binding_public(binding['binding_id'])['enabled']


def test_native_endpoint_lease_is_bound_and_keyless_probe_is_confined(monkeypatch):
    from reverse_agent.model_access import credential_relay as relay
    from tests.platform_v1.test_credential_relay import _make_snapshot
    manager = relay.CredentialRelayManager()
    snapshot = _make_snapshot(native_endpoint='/responses')
    lease = manager.create_lease(snapshot, relay_url='http://127.0.0.1:1')
    with pytest.raises(relay.CredentialRelayError, match='lease_path_mismatch'):
        manager._validate_lease_for_request(lease.lease_id, method='POST', path='/chat/completions', model='gpt-4o')
    active = manager._validate_lease_for_request(lease.lease_id, method='POST', path='/responses', model='gpt-4o')
    calls = []
    monkeypatch.setattr(relay, '_http_roundtrip', lambda url, *args: calls.append((url, args)) or (200, b'{}', {}))
    relay.forward_to_upstream(active, body=b'{}')
    assert calls[-1][0].endswith('/responses')
    keyless = _make_snapshot(auth_method='none', resolved_api_key=None)
    body = {'model': 'gpt-4o', 'messages': [{'role': 'user', 'content': 'Reply OK'}], 'max_tokens': 4}
    relay.forward_keyless_probe(keyless, body=json.dumps(body).encode())
    assert 'Authorization' not in calls[-1][1][2]
    with pytest.raises(relay.CredentialRelayError):
        relay.forward_keyless_probe(snapshot, body=json.dumps(body).encode())
    with pytest.raises(relay.CredentialRelayError):
        relay.forward_keyless_probe(keyless, body=json.dumps(body | {'max_tokens': 500}).encode())


def test_large_decision_json_is_projected_without_dropping_exclusions():
    metadata = {'model_id': 'chosen', 'binding_ref': 'b', 'reason': 'cheapest_qualifying',
        'candidates': [{'binding_id': str(i), 'score_breakdown': {'padding': 'x' * 1500}} for i in range(5)],
        'excluded_candidates': [{'model_id': 'too-small', 'filter': 'context_window'}]}
    raw = json.dumps(metadata)
    assert len(raw) > 4096
    projected = _event_projection({'type': 'MODEL_SELECTED', 'metadata': raw}, task=SimpleNamespace(id='t'))
    assert 'chosen' in projected['description'] and 'too-small: context_window' in projected['description']


def test_gateway_cost_classes_and_no_demand_record():
    from reverse_agent.platform_v1.routing_inputs import binding_cost_class
    conn = {'auth_method': 'api_key'}
    def binding(model):
        return {'binding_id': 'b', 'connection_id': 'c', 'model_id': model}
    assert binding_cost_class(binding('workbuddy/glm-5.3'), conn, {}) == 'free'
    assert binding_cost_class(binding('copilot/gpt-4.1'), conn, {}) == 'subscription'
    assert binding_cost_class(binding('copilot/gpt-4.1'), {'auth_method': 'none'}, {}) == 'subscription'
    assert binding_cost_class(binding('anthropic/sonnet'), conn, {}) == 'paid_api'
    assert binding_cost_class(binding('anthropic/sonnet:free'), conn, {}) == 'free'
    with pytest.raises(model_router.ModelSelectionError) as caught:
        select([], reset_signal={'state': 'PLAN_ONLY', 'validated': True, 'expected_reset_at': 200}, now=100)
    assert caught.value.decision['reset']['demand'] == 'NO_DEMAND'


@pytest.mark.parametrize('classification,text,changes,expected', [
    ('', 'I cannot help with that request.', [], 'MODEL_REFUSED'),
    ('', 'I cannot help with that request.', [{'path': 'fixed.py'}], ''),
    ('MODEL_UNAVAILABLE:model_not_supported', '', [], 'MODEL_UNAVAILABLE'),
    ('policy_refusal', '', [], 'MODEL_REFUSED'),
])
def test_ordinary_dispatch_classifies_willingness_and_entitlement(tmp_path, classification, text, changes, expected):
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorResult
    store = TaskStore(':memory:')
    task = store.create_task(title='Classify', executor_kind='opencode', binding_ref='fixture-binding')
    def dispatch(**kwargs):
        kwargs['event_callback'](task.id, {'type': 'EXECUTOR_COMPLETED', 'title': 'Response',
                                         'metadata': {'final_text': text}})
        return ExecutorResult(success=True, validation_command_id='git_diff_check', validation_exit_code=0,
            validation_output_digest='', validation_output_summary='', changed_files=changes,
            failure_classification=classification)
    service = TaskExecutionService(store=store, router=SimpleNamespace(dispatch_execute=dispatch))
    result = service._dispatch_executor(task=task, workspace_root=str(tmp_path), validation_command_id='', executor_kwargs={})
    assert result['failure_classification'] == expected
    assert result['success'] == (not expected)


def test_dispatch_entitlement_failure_reroutes_without_capability_failure(monkeypatch, tmp_path):
    from datetime import datetime, timezone
    import time
    from tests.platform_v1.test_agent_team import _team, _window_payload
    from reverse_agent.platform_v1.model_profiles import compute_agent_profiles
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.delattr(host, '_routing_availability')
    store, control, autonomy, goals = _team(monkeypatch, {})
    host._task_store = store
    host._availability_cache = AvailabilityCache()
    for row in host._store.list_bindings_public():
        connection = host._store.get_connection_public(row['connection_id'])
        host._availability_cache.remember(row, connection, observation(now=time.time() - 10, success=True))
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({'objective': 'Authorized work', 'repository': 'dddd2024/Nerelan',
        'idempotency_key': 'unavailable-reroute', 'executor_kind': 'opencode', 'orchestration_mode': 'agent_team'})
    goals.plan(goal.id, expected_revision=1, tasks=[{'id': 'T1', 'title': 'Edit', 'instruction': 'Edit', 'difficulty': 2}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate(_window_payload(goal.repository)).id)
    task = store.get_task(control.list_goal_tasks(goal.id)[0]['task_id'])
    assert task.binding_ref == 'cheap'
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='MODEL_UNAVAILABLE', failure_detail='model_not_supported', updated_at=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), task.id))
    store._conn.commit()
    [retry] = goals.escalate_failed_tasks(goal.id)
    replacement = store.get_task(retry['to_task_id'])
    assert replacement.binding_ref != 'cheap'
    event = next(e for e in store.get_events(replacement.id) if e.type == 'MODEL_SELECTED')
    assert event.metadata['difficulty'] == 2 and event.metadata['reason'] == 'cheapest_qualifying'
    assert event.metadata['excluded_candidates'][0]['filter'] == 'availability:model_not_supported'
    assert compute_agent_profiles(store)['cheap']['attempts'] == 0


def test_refusal_never_bypasses_window_retry_budget(monkeypatch, tmp_path):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    from reverse_agent.platform_v1.model_profiles import compute_agent_profiles
    host = fixture_host(monkeypatch, tmp_path)
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({'objective': 'Local research', 'repository': 'dddd2024/Nerelan',
        'idempotency_key': 'refusal-budget', 'executor_kind': 'opencode', 'orchestration_mode': 'agent_team'})
    goals.plan(goal.id, expected_revision=1, tasks=[{'id': 'T1', 'title': 'Research', 'instruction': 'local only',
        'difficulty': 2, 'needs': ['security_simulation']}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate({**_window_payload(goal.repository), 'max_retries': 0}).id)
    task = store.get_task(control.list_goal_tasks(goal.id)[0]['task_id'])
    store.add_event(task.id, event_type='MODEL_REFUSED', title='Refused')
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='MODEL_REFUSED' WHERE id=?", (task.id,))
    store._conn.commit()
    assert not goals.escalate_failed_tasks(goal.id)
    assert store.get_task(task.id).failure_classification == 'routing_retry_budget_exhausted'
    assert store.get_task(task.id).status == 'BLOCKED'
    profile = compute_agent_profiles(store)[task.binding_ref]
    assert profile['attempts'] == 0 and profile['refusal_rates']['security_simulation'] == 1


def test_personal_grants_and_banked_resets_are_neutral():
    from reverse_agent.platform_v1.routing_inputs import reset_decision
    signal = {'state': 'PLAN_ONLY', 'validated': True, 'expected_reset_at': 200}
    for extra in ({'scope': 'personal'}, {'kind': 'banked_grant'}, {'expected_reset_at': 'soon'}):
        decision = reset_decision(signal | extra, now=100, weekly_remaining=.1)
        assert not decision['drain'] and decision['cost_adjustment'] == 0


def test_measured_low_refusal_beats_unknown_and_owner_traits_override_measurements():
    pool = [candidate('a-unknown', 'unknown'), candidate('b-proven', 'proven')]
    profiles = {'b-proven': {'refusal_rates': {'security_simulation': .05}, 'tool_reliability': .1}}
    assert select(pool, needs=['security_simulation'], profiles=profiles)['binding_ref'] == 'b-proven'
    result = select(pool, needs=['tool_use'], profiles=profiles, overrides={'b-proven': {'tool_reliability': 1.,
        'refusal_rates': {'code': 0.}}})
    assert result['binding_ref'] == 'b-proven'
    assert result['characteristics']['tool_reliability'] == 1.


def test_reset_estimated_task_preserves_buffer_and_short_capacity():
    from reverse_agent.platform_v1.routing_inputs import reset_decision
    signal = {'state': 'PLAN_ONLY', 'expected_reset_at': 20000, 'validated': True}
    pool = [candidate('codex', 'known', 'subscription', 'codex', weekly_headroom=.05,
        quota_headroom=.05, short_headroom=.1, task_weekly_fraction=.03, task_short_fraction=.02),
        candidate('other', 'known', 'subscription', 'claude_code', quota_headroom=.8)]
    result = select(pool, reset_signal=signal, now=10000)
    assert result['binding_ref'] == 'other'
    assert result['excluded_candidates'][0]['filter'] == 'reset_buffer'
    pool[0]['task_weekly_fraction'] = .01
    pool[0]['task_short_fraction'] = .2
    result = select(pool, reset_signal=signal, now=10000)
    assert result['excluded_candidates'][0]['filter'] == 'short_window_capacity'
    plan = reset_decision(signal, now=10000, weekly_remaining=.2, short_resets_at=11000)
    assert plan['remaining_short_windows'] == 2 and plan['remaining_buffer'] == .03
    assert plan['target_per_short_window'] == pytest.approx(.085)
    neutral = reset_decision(signal | {'expected_reset_at': float('nan')}, now=10000)
    json.dumps(neutral, allow_nan=False)
    assert not neutral['drain']


def test_transient_penalty_expires_without_another_probe():
    cache = AvailabilityCache()
    binding, connection = candidate('a', 'a'), {'connection_id': 'c'}
    cache.remember(binding, connection, observation(now=100, success=True))
    cache.remember(binding, connection, observation(now=200, error='timeout'))
    assert cache.check(binding, connection, now=201)['penalty'] == .5
    result = cache.check(binding, connection, now=501)
    assert result['state'] == 'AVAILABLE' and result['penalty'] == 0
