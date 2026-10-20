"""Issue 1248 later Owner requirements, entirely fake transports and observations."""
import json
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import model_router, model_availability, routing_capabilities
from reverse_agent.platform_v1.model_availability import AvailabilityCache, observation
from reverse_agent.platform_v1.run_read_model import _event_projection
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
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
    assert select([row], allow_paid=True)["binding_ref"] == "a"


def test_prior_fallback_and_measured_precedence_over_owner_table():
    row = candidate('flash', 'deepseek-v4.1-flash')
    fallback = select([row], difficulty=3)
    assert fallback["reason"] == "prior_only_unproven" and fallback["underpowered"]
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
    assert not select([row], difficulty=3, capability_table={'deepseek-v4.1-flash': {'tiers': {'code': 4}}})['underpowered']
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


def binding(model, connection_id='c'):
    return {'binding_id': 'b', 'connection_id': connection_id, 'model_id': model}


@pytest.mark.parametrize('model,connection,expected', [
    ('workbuddy/glm-5.3', {'auth_method': 'api_key'}, 'subscription'),
    ('workbuddy-ai/glm-5.2', {'auth_method': 'api_key'}, 'subscription'),
    ('trae-cn/credit-model', {'auth_method': 'api_key'}, 'subscription'),
    ('opencode-zen-free/some-model', {'auth_method': 'api_key'}, 'free'),
    ('vendor/model-free', {'auth_method': 'api_key'}, 'free'),
    ('vendor/model:free', {'auth_method': 'api_key'}, 'free'),
    ('vendor/Model-Free', {'auth_method': 'api_key'}, 'free'),
    ('copilot/gpt-4.1', {'auth_method': 'api_key'}, 'subscription'),
    ('copilot/gpt-4.1', {'auth_method': 'none'}, 'subscription'),
    ('anthropic/sonnet', {'auth_method': 'api_key'}, 'paid_api'),
    ('openrouter/non-free-model', {'auth_method': 'api_key'}, 'paid_api'),
    ('openrouter/non-free-model:free', {'auth_method': 'api_key'}, 'free'),
    ('sensetime/sensenova-6.7-flash-lite', {'auth_method': 'api_key'}, 'free'),
    ('glm-5.2', {'base_url': 'https://token.sensenova.cn/v1', 'auth_method': 'api_key'}, 'free'),
    ('glm-5.2', {'executor_provider_id': 'sensetime', 'auth_method': 'api_key'}, 'free'),
    ('plain-model', {'auth_method': 'external_cli_session'}, 'subscription'),
    ('local-model', {'auth_method': 'none'}, 'free'),
    ('api-key-model', {'auth_method': 'api_key'}, 'paid_api'),
])
def test_gateway_cost_class_mapping(model, connection, expected):
    from reverse_agent.platform_v1.routing_inputs import binding_cost_class
    assert binding_cost_class(binding(model), connection, {}) == expected


def test_cost_class_missing_fields_are_paid_not_a_crash():
    from reverse_agent.platform_v1.routing_inputs import binding_cost_class
    assert binding_cost_class({}, {}, {}) == 'paid_api'
    assert binding_cost_class({'model_id': None}, None, None) == 'paid_api'


def test_cost_override_round_trip_and_owner_precedence(tmp_path):
    from reverse_agent.platform_v1 import routing_inputs
    config = {
        'bindings': {'pinned': {'cost_class': 'paid_api'}},
        'models': {'provider/shared': {'cost_class': 'free'}},
        'connections': {'busy': {'cost_class': 'subscription'}},
    }
    (tmp_path / 'model_routing_overrides.json').write_text(json.dumps(config), encoding='utf-8')
    owner = routing_inputs.read_overrides(tmp_path / 'model_setup_state.json')
    assert owner['models']['provider/shared']['cost_class'] == 'free'
    conn = {'auth_method': 'api_key'}
    assert routing_inputs.binding_cost_class(binding('provider/shared', 'busy') | {'binding_id': 'pinned'}, conn, owner) == 'paid_api'
    assert routing_inputs.binding_cost_class(binding('provider/shared', 'busy'), conn, owner) == 'free'
    assert routing_inputs.binding_cost_class(binding('provider/other', 'busy'), conn, owner) == 'subscription'
    assert routing_inputs.binding_cost_class(binding('provider/other', 'idle'), conn, owner) == 'paid_api'


def test_shipped_default_overrides_template_is_empty_and_copyable():
    from reverse_agent.platform_v1.routing_inputs import DEFAULT_MODEL_ROUTING_OVERRIDES, default_overrides
    template = default_overrides()
    assert template == DEFAULT_MODEL_ROUTING_OVERRIDES
    assert template == {'bindings': {}, 'models': {}, 'connections': {},
                        'paid_api_windows': [], 'reset_buffer': .03}
    template['connections']['runtime-only'] = {'cost_class': 'free'}
    assert DEFAULT_MODEL_ROUTING_OVERRIDES['connections'] == {}


def test_no_demand_reset_record():
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


@pytest.fixture
def readiness_host(monkeypatch, tmp_path):
    """Real host routing, capability, readiness and quota paths; no account access."""
    from reverse_agent.model_access.store import ModelProfileStore
    from reverse_agent.model_access import subscription_quota, http_safe, credential_relay
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    host = object.__new__(CombinedTrustedHost)
    host._store = ModelProfileStore(state_path=tmp_path / 'model_setup_state.json')
    host._task_store = TaskStore(':memory:')
    host._availability_cache = AvailabilityCache()
    monkeypatch.delenv('REVERSE_AGENT_MODEL_CONTROL_LIVE', raising=False)
    monkeypatch.delenv('REVERSE_AGENT_ROUTING_PROBES', raising=False)
    monkeypatch.delenv('REVERSE_AGENT_SUBSCRIPTION_QUOTA', raising=False)
    host.test_quotas = {}
    monkeypatch.setattr(subscription_quota, 'codex_quota', lambda: host.test_quotas.get('codex', {}))
    monkeypatch.setattr(subscription_quota, 'claude_quota', lambda *_: host.test_quotas.get('claude-code', {}))
    def forbidden(*args, **kwargs):
        pytest.fail('unexpected probe/network call')
    monkeypatch.setattr(http_safe, 'urlopen', forbidden)
    monkeypatch.setattr(credential_relay, 'forward_keyless_probe', forbidden)
    host._availability_probe = forbidden
    return host


def add_ready_account(host, executor='codex', model=None):
    provider = 'codex' if executor == 'codex' else 'claude-code'
    model = model or ('gpt-6-sol' if executor == 'codex' else 'sonnet')
    host._store.upsert_connection({'connection_id': 'native', 'name': 'Native', 'provider': provider,
        'base_url': 'https://example.invalid', 'auth_method': 'external_cli_session', 'enabled': True})
    host._store.upsert_binding({'binding_id': 'native', 'name': 'Native', 'executor_id': executor,
        'connection_id': 'native', 'model_id': model, 'enabled': True})
    host._store.set_native_readiness(executor, 'managed_login_ready')


def routing_task(difficulty=2):
    from reverse_agent.platform_v1.goal_service import PlannedTask
    return PlannedTask('T', 'Edit', 'Edit locally', difficulty=difficulty)


@pytest.mark.parametrize('difficulty', [2, 4])
@pytest.mark.parametrize('executor,model', [('codex', 'gpt-6-sol'), ('claude_code', 'sonnet')])
def test_native_routes_from_real_readiness_without_history_or_probes(readiness_host, difficulty, executor, model):
    host = readiness_host
    add_ready_account(host, executor, model)
    host._availability_probe = None
    assert 'native' in host._runnable_bindings()
    result = host._resolve_task_model(routing_task(difficulty))
    assert result['binding_ref'] == 'native'
    assert result['tier_source'] == 'prior'  # readiness never fabricates capability
    assert not host._availability_cache.entries  # nor a successful request
    row = host._store.get_binding_public('native')
    connection = host._store.get_connection_public('native')
    assert host._routing_availability(row, connection, allow_paid=False, cost_class='subscription') == {
        'state': 'READY', 'reason': 'managed_login_ready'}


@pytest.mark.parametrize('executor', ['codex', 'claude_code'])
def test_native_login_unavailable_is_not_runnable(readiness_host, executor):
    host = readiness_host
    add_ready_account(host, executor)
    host._store.set_native_readiness(executor, 'managed_login_unavailable')
    assert 'native' not in host._runnable_bindings()
    with pytest.raises(TaskStoreError, match='no_runnable_model') as caught:
        host._resolve_task_model(routing_task(4))
    assert caught.value.decision['excluded_candidates'][0]['filter'] == 'executor_fitness'


@pytest.mark.parametrize('executor,provider', [('codex', 'codex'), ('claude_code', 'claude-code')])
def test_native_real_quota_guard_excludes_confirmed_exhaustion_even_pin(readiness_host, executor, provider):
    host = readiness_host
    add_ready_account(host, executor)
    host.test_quotas[provider] = {'windows': [{'window': 'weekly', 'basis': 'official_percent', 'used_percent': 100}]}
    assert host._quota_check(host._store.get_binding_public('native'))['reason'] == 'observed_exhausted'
    with pytest.raises(TaskStoreError) as caught:
        host._resolve_task_model(routing_task(), goal=SimpleNamespace(binding_ref='native'))
    assert caught.value.decision['excluded_candidates'][0]['filter'] == 'quota_exhausted'


def add_magpie(host):
    host._store.upsert_connection({'connection_id': 'magpie', 'name': 'Magpie', 'provider': 'openai-compatible',
        'base_url': 'https://example.invalid/v1', 'auth_method': 'none', 'enabled': True})
    host._store.upsert_binding({'binding_id': 'magpie', 'name': 'Magpie', 'executor_id': 'opencode',
        'connection_id': 'magpie', 'model_id': 'copilot/gpt-4.1', 'enabled': True})
    return host._store.get_binding_public('magpie'), host._store.get_connection_public('magpie')


def test_unknown_magpie_eligible_available_preferred_and_refusal_preserved(readiness_host):
    import time
    host = readiness_host
    row, connection = add_magpie(host)
    # Remove injected opt-in too: both environment opt-ins and callback absent.
    host._availability_probe = None
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    host._availability_cache.remember(row, connection, observation(now=time.time(), error='network timeout'))
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    add_ready_account(host)
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'native'
    host._availability_cache.remember(row, connection, observation(now=time.time(), success=True))
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    result = host._resolve_task_model(routing_task(), refused_models=[row['model_id']])
    assert result['binding_ref'] == 'native'
    assert result['excluded_candidates'][0]['filter'] == 'model_refused'


@pytest.mark.parametrize('native', [False, True])
@pytest.mark.parametrize('error', ['model_not_supported', 'not-allowed', 'not allowed for user type'])
def test_real_entitlement_cache_excludes_even_pins(readiness_host, native, error):
    import time
    host = readiness_host
    if native:
        add_ready_account(host)
        row, connection = host._store.get_binding_public('native'), host._store.get_connection_public('native')
    else:
        row, connection = add_magpie(host)
    host._availability_cache.remember(row, connection, observation(now=time.time(), error=error))
    with pytest.raises(TaskStoreError) as caught:
        host._resolve_task_model(routing_task(4), goal=SimpleNamespace(binding_ref=row['binding_id']))
    assert caught.value.decision['excluded_candidates'][0]['filter'].startswith('availability:')


def test_native_executor_never_probed_even_without_native_model_prefix():
    cache = AvailabilityCache()
    def forbidden(_):
        pytest.fail('native executor probe')
    for executor in ('codex', 'claude_code'):
        assert cache.check(candidate('b', 'plain-model', executor=executor), {'auth_method': 'none'},
            probe=forbidden, allow_probe=True)['state'] == 'UNKNOWN'


@pytest.mark.parametrize('model', ['codex/gpt-6-sol', 'claude/sonnet'])
@pytest.mark.parametrize('difficulty', [2, 4])
def test_namespaced_external_session_uses_real_runnable_path(readiness_host, model, difficulty):
    host = readiness_host
    host._store.upsert_connection({'connection_id': 'external', 'name': 'External',
        'provider': 'magpie', 'base_url': 'https://example.invalid/v1',
        'auth_method': 'external_cli_session', 'enabled': True})
    host._store.upsert_binding({'binding_id': 'external', 'name': 'External', 'executor_id': 'opencode',
        'connection_id': 'external', 'model_id': model, 'enabled': True})
    host._store.refresh_external_session_status({'magpie': 'oauth'})
    assert host._resolve_task_model(routing_task(difficulty))['binding_ref'] == 'external'
    assert not host._availability_cache.entries
    host._store.refresh_external_session_status({})
    with pytest.raises(TaskStoreError, match='no_runnable_model'):
        host._resolve_task_model(routing_task(difficulty))


def test_selection_history_is_bounded_batched_and_latest_wins(readiness_host):
    from datetime import datetime, timezone
    import time
    host = readiness_host
    row, connection = add_magpie(host)
    host._availability_probe = None
    now = time.time()
    def record(offset, status, classification='', detail=''):
        task = host._task_store.create_task(title='Observation', executor_kind='opencode', binding_ref='magpie')
        host._task_store._conn.execute(
            'UPDATE tasks SET status=?, failure_classification=?, failure_detail=?, updated_at=? WHERE id=?',
            (status, classification, detail, datetime.fromtimestamp(now + offset, timezone.utc).isoformat(), task.id))
        host._task_store._conn.commit()
    record(-100, 'FAILED', 'MODEL_UNAVAILABLE', 'model_not_supported')
    for offset in range(-40, -20):
        record(offset, 'QUEUED')
    # Old entitlement observation is outside the latest 20, not replayed.
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    assert not host._availability_cache.entries
    record(-10, 'COMPLETED')
    record(-9, 'FAILED', 'MODEL_UNAVAILABLE', 'model_not_supported')
    with pytest.raises(TaskStoreError):
        host._resolve_task_model(routing_task())
    assert host._availability_cache.check(row, connection)['state'] == 'UNAVAILABLE'
    record(-8, 'COMPLETED')
    statements = []
    host._task_store._conn.set_trace_callback(statements.append)
    try:
        assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    finally:
        host._task_store._conn.set_trace_callback(None)
    assert host._availability_cache.check(row, connection)['state'] == 'AVAILABLE'
    assert len([sql for sql in statements if 'ROW_NUMBER()' in sql]) == 1
    record(-7, 'FAILED', 'network_provider_timeout')
    assert host._resolve_task_model(routing_task())['binding_ref'] == 'magpie'
    assert host._availability_cache.check(row, connection)['penalty'] == .5
    # A newer cached rejection cannot be replaced by older successful tasks.
    host._availability_cache.remember(row, connection, observation(now=now - 1, error='not-allowed'))
    with pytest.raises(TaskStoreError):
        host._resolve_task_model(routing_task())


def test_available_preference_includes_exploration_and_unknown_pin_is_eligible():
    unknown = candidate('unknown', 'unknown')
    unknown['availability'] = {'state': 'UNKNOWN'}
    available = candidate('available', 'available', cost='subscription')
    assert select([unknown, available], exploration_draw=0)['binding_ref'] == 'available'
    assert select([unknown, available], pin='unknown')['binding_ref'] == 'unknown'


@pytest.mark.parametrize("independent", [False, True])
def test_chain_review_real_availability_and_blocked_evidence(monkeypatch, tmp_path, independent):
    from tests.platform_v1.test_agent_team import _team, _window_payload
    host = fixture_host(monkeypatch, tmp_path)
    # Keep the real availability cache and capability/evidence selection gates.
    monkeypatch.delattr(host, '_routing_availability')
    host._availability_probe = lambda row: pytest.fail('routing must not call a provider')
    mid = host._store.get_binding_public('mid')
    host._store.upsert_binding({**mid, 'model_id': 'glm-5.3'})
    if independent:
        host._store.upsert_binding({**mid, 'binding_id': 'independent', 'name': 'Independent',
                                   'model_id': 'gemini-flash-lite'})
    refs = {row['binding_id'] for row in host._store.list_bindings_public()}
    monkeypatch.setattr(host, '_runnable_bindings', lambda: refs)
    connections = {row['connection_id']: row for row in host._store.list_connections_public()}
    import time
    cache = host._availability_cache = AvailabilityCache()
    for row in host._store.list_bindings_public():
        cache.remember(row, connections[row['connection_id']], observation(now=time.time(), success=True))
    store, control, autonomy, goals = _team(monkeypatch, {})
    goals.task_resolver = host._resolve_task_model
    goal = goals.create({'objective': 'Review cumulative artifact', 'repository': 'dddd2024/Nerelan',
        'idempotency_key': 'chain', 'executor_kind': 'opencode', 'orchestration_mode': 'agent_team'})
    checks = [{'profile_id': 'python_pytest', 'working_directory': '.'}]
    def task(name, difficulty, deps=(), source=None):
        row = {'id': name, 'title': name, 'instruction': name, 'difficulty': difficulty,
               'dependencies': list(deps), 'validation_checks': checks}
        if source:
            row.update(kind='review', artifact_input={'plan_task_id': source})
        return row
    # Reverse order, diamond graph, and two distinct upstream model identities.
    goals.plan(goal.id, expected_revision=1, tasks=[task('R', 2, ('D',), 'D'),
        task('D', 4, ('B', 'C')), task('C', 4, ('A',)), task('B', 3, ('A',)), task('A', 2)])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=autonomy.activate({**_window_payload(goal.repository), 'max_retries': 3}).id)
    tasks = {row['plan_task_id']: store.get_task(row['task_id']) for row in control.list_goal_tasks(goal.id)}
    assert tasks['A'].binding_ref == 'cheap'
    assert tasks['B'].binding_ref == 'mid'
    assert tasks['C'].binding_ref == tasks['D'].binding_ref == 'strong'
    review = tasks['R']
    if not independent:
        assert review.status == 'BLOCKED'
        assert review.failure_classification == 'review_not_independent'
        [event] = [e for e in store.get_events(review.id) if e.type == 'MODEL_SELECTION_FAILED']
        assert event.metadata['reason'] == 'review_not_independent'
        assert {e['model_id'] for e in event.metadata['excluded_candidates']} >= {'flash-lite', 'glm-5.3', 'opus'}
        projected = _event_projection({'type': event.type, 'metadata': event.metadata}, task=review)
        assert projected['status'] == 'BLOCKED'
        return
    assert review.binding_ref == 'independent'
    [event] = [e for e in store.get_events(review.id) if e.type == 'MODEL_SELECTED']
    assert event.metadata['candidates'][0]['availability']['state'] == 'AVAILABLE'
    # A review retry can reuse the sole independent qualifying reviewer.
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='timeout' WHERE id=?", (review.id,))
    store._conn.commit()
    [retry] = goals.escalate_failed_tasks(goal.id)
    review = store.get_task(retry['to_task_id'])
    assert review.binding_ref == 'independent'
    # Recorded author survives a binding change, and retry cannot reuse it under an alias.
    cheap = host._store.get_binding_public('cheap')
    host._store.upsert_binding({**cheap, 'model_id': 'glm-5.3'})
    host._store.upsert_binding({**cheap, 'binding_id': 'old-author-alias',
                               'model_id': 'gateway/flash-lite-free:free'})
    refs.add('old-author-alias')
    for index, model in enumerate(('glm-5.3', 'gemini-flash-lite')):
        store.append_usage_observation(tasks['B'].id, observation_id=f'author-{index}',
            execution_id=tasks['B'].execution_id, role='coder', model_id=model, provider_id='fixture',
            source_kind='executor', source_id=f'chunk-{index}', status='UNKNOWN')
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='timeout' WHERE id=?", (review.id,))
    store._conn.commit()
    assert goals.escalate_failed_tasks(goal.id) == ()
    blocked = store.get_task(review.id)
    assert blocked.status == 'BLOCKED' and blocked.failure_classification == 'review_not_independent'
    assert any(e.type == 'MODEL_SELECTION_FAILED' and e.metadata['reason'] == 'review_not_independent'
               for e in store.get_events(review.id))


def test_retry_ancestry_keeps_previous_attempt_authors_and_fails_on_missing_evidence():
    from reverse_agent.platform_v1.goal_service import GoalService, PlannedTask
    service = object.__new__(GoalService)
    attempts = {'old': SimpleNamespace(binding_ref='changed', status='FAILED'),
                'current': SimpleNamespace(binding_ref='current', status='READY_FOR_REVIEW')}
    events = {name: [SimpleNamespace(type='MODEL_SELECTED', metadata={'model_id': model})]
              for name, model in [('old', 'first-author'), ('current', 'second-author')]}
    service.store = SimpleNamespace(get_task=attempts.__getitem__, get_events=events.__getitem__,
                                    list_usage_observations=lambda _: ())
    service.control_store = SimpleNamespace(
        list_goal_tasks=lambda _: [{'plan_task_id': 'A', 'task_id': 'current', 'goal_revision': 1}],
        list_task_escalations=lambda _: [{'plan_task_id': 'A', 'from_task_id': 'old', 'goal_revision': 1}])
    review = PlannedTask('R', 'R', 'R', kind='review', artifact_input={'plan_task_id': 'A'})
    planned = {'A': PlannedTask('A', 'A', 'A')}
    goal = SimpleNamespace(id='goal', revision=1)
    assert service._review_authors(review, goal, planned)['author_models'] == ('first-author', 'second-author')
    events['old'] = []
    with pytest.raises(TaskStoreError, match='review_not_independent'):
        service._review_authors(review, goal, planned)
