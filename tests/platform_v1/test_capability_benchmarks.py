"""Issue 1264: benchmark-seeded priors. Recorded fixtures only; no network."""
import json
import socket
from pathlib import Path

import pytest

from reverse_agent.platform_v1 import capability_benchmarks as cb
from reverse_agent.platform_v1 import model_router, routing_capabilities
from tests.platform_v1.test_model_router import candidate


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError('network access in a provider-free test')
    monkeypatch.setattr(socket, 'create_connection', refuse)


def row(benchmark, score, source, day='2026-10-19', variant=''):
    return {'benchmark': benchmark, 'score': score, 'source': source,
            'url': f'https://{source}.example/leaderboard', 'retrieved_at': day, 'variant': variant}


def snapshot(**families):
    return {'version': 1, 'snapshot_id': 'fixture@2026-10-19',
            'families': {name: {'aliases': aliases, 'scores': scores} for name, (aliases, scores) in families.items()}}


def five_models(second_source=True, conflict=False):
    scores = {'m1': 10, 'm2': 20, 'm3': 30, 'm4': 40, 'm5': 50}
    families = {}
    for name, value in scores.items():
        rows = [row('swe_bench_verified', value, 'alpha')]
        if second_source:
            other = 60 - value if conflict else value + 1
            rows.append(row('aider_polyglot', other, 'beta'))
        families[name] = ([name], rows)
    return snapshot(**families)


def test_percentile_and_tier_mapping():
    priors = cb.compute_priors(five_models())
    assert [priors[f'm{i}']['code']['percentile'] for i in range(1, 6)] == [0, .25, .5, .75, 1]
    assert [priors[f'm{i}']['code']['tier'] for i in range(1, 6)] == [1, 2, 3, 4, 5]
    assert cb.tier_for(0) == 1 and cb.tier_for(.199) == 1 and cb.tier_for(.2) == 2 and cb.tier_for(1) == 5
    # Code benchmarks also inform review; nothing informs writing here.
    assert 'review' in priors['m5'] and 'writing' not in priors['m5']


def test_multi_source_median_and_confidence():
    agreeing = cb.compute_priors(five_models())
    assert agreeing['m5']['code']['confidence'] == 'high'
    assert {s['source'] for s in agreeing['m5']['code']['sources']} == {'alpha', 'beta'}
    evidence = agreeing['m5']['code']['sources'][0]['evidence'][0]
    assert evidence['url'].startswith('https://') and evidence['retrieved_at'] == '2026-10-19'
    conflicting = cb.compute_priors(five_models(conflict=True))
    assert conflicting['m5']['code']['confidence'] == 'low'
    assert conflicting['m5']['code']['percentile'] == .5  # median of 1.0 and 0.0
    single = cb.compute_priors(five_models(second_source=False))
    assert single['m5']['code']['confidence'] == 'low'


def test_three_sources_take_the_median():
    families = {}
    for name, (a, b, c) in {'x': (1, 1, 3), 'y': (2, 2, 2), 'z': (3, 3, 1)}.items():
        families[name] = ([name], [row('gpqa_diamond', a, 's1'), row('gpqa_diamond', b, 's2'), row('gpqa_diamond', c, 's3')])
    priors = cb.compute_priors(snapshot(**families))
    assert priors['z']['analysis']['percentile'] == 1 and priors['z']['analysis']['confidence'] == 'low'
    assert priors['y']['analysis']['percentile'] == .5 and priors['y']['analysis']['confidence'] == 'high'


def test_single_family_column_is_not_evidence():
    priors = cb.compute_priors(snapshot(only=(['only'], [row('hle', 99, 'alpha')])))
    assert priors == {}


def test_alias_mapping_across_providers():
    data = cb.seed_snapshot()
    index = cb.alias_index(data)
    for model in ('workbuddy/deepseek-v4-pro', 'trae-cn/DeepSeek-V4-Pro-Official', 'deepseek-v4-pro',
                  'other-gateway/deepseek-v4-pro'):
        assert cb.resolve_family(model, index) == 'deepseek-v4-pro'
    # Exact ids only: a name fragment never resolves.
    assert cb.resolve_family('deepseek-v4-pro-max', index) is None
    assert cb.resolve_family('deepseek', index) is None
    clash = snapshot(a=(['shared'], []), b=(['shared'], []))
    with pytest.raises(ValueError, match='invalid_capability_benchmarks'):
        cb.validate_snapshot(clash)


@pytest.mark.parametrize('mutation', [
    {'url': 'http://insecure.example/x'}, {'retrieved_at': '2026-13-01'}, {'retrieved_at': 'yesterday'},
    {'benchmark': 'vibes'}, {'score': float('nan')}, {'score': '90'}, {'source': ''},
])
def test_invalid_score_rows_rejected(mutation):
    data = snapshot(a=(['a'], [row('hle', 1, 'alpha') | mutation]))
    with pytest.raises(ValueError, match='invalid_capability_benchmarks'):
        cb.validate_snapshot(data)


def test_pseudo_count_blending_converges_to_measured():
    prior = cb.expected_success(5, 3)
    assert prior == .85
    rates = [cb.blend(prior, cb.PSEUDO_COUNT, 0, n) for n in (0, 3, 10, 100)]
    assert rates[0] == prior and rates == sorted(rates, reverse=True)
    assert rates[-1] < .03  # measured failures dominate
    assert cb.blend(cb.expected_success(1, 4), cb.PSEUDO_COUNT, 100, 100) > .97
    # Low confidence weighs less than high.
    assert cb.blend(prior, cb.LOW_CONFIDENCE_PSEUDO_COUNT, 0, 3) < cb.blend(prior, cb.PSEUDO_COUNT, 0, 3)


def profile(level, ok, attempts, kind='code'):
    return {'task_buckets': {f'{kind}:{level}': {'attempts': attempts, 'ok': ok, 'timeouts': 0,
                                                    'success_rate': ok / attempts}}}


def priors_for(model='m5', **kwargs):
    data = five_models(**kwargs)
    data['families'][model]['aliases'].append(f'gateway/{model}')
    return cb.BenchmarkPriors(data)


def test_precedence_order():
    bench = priors_for()
    table = routing_capabilities.CapabilityTable({'m5': {'tiers': {'code': 2}}})
    table.benchmarks = bench
    detail = routing_capabilities.tier_detail
    assert detail('m5', {}, 'code', 3, table, {'tiers': {'code': 1}})['source'] == 'owner_override'
    assert detail('m5', profile(3, 3, 3), 'code', 3, table)['source'] == 'measured_with_prior'
    assert detail('m5', profile(3, 10, 10), 'code', 3, table)['source'] == 'measured'
    assert detail('m5', {}, 'code', 3, table)['source'] == 'owner_table'
    benchmark = detail('gateway/m5', {}, 'code', 3, None, benchmarks=bench)
    assert benchmark['source'] == 'benchmark' and benchmark['tier'] == 5 and benchmark['unproven'] is False
    assert benchmark['benchmark']['confidence'] == 'high' and benchmark['benchmark']['family'] == 'm5'
    assert detail('m5', {}, 'writing', 3, None, benchmarks=bench) == {'tier': 2, 'unproven': True, 'source': 'prior'}
    # The legacy three-tuple view is unchanged.
    assert routing_capabilities.tier_evidence('m5', {}, 'code', 3, table) == (2, False, 'owner_table')


def test_unknown_model_is_unproven_and_low_confidence_needs_calibration():
    bench = priors_for(second_source=False)
    unknown = routing_capabilities.tier_detail('brand-new-model', {}, 'code', 3, None, benchmarks=bench)
    assert unknown == {'tier': 2, 'unproven': True, 'source': 'prior'}
    low = routing_capabilities.tier_detail('m5', {}, 'code', 3, None, benchmarks=bench)
    assert low['tier'] == 5 and low['unproven'] is True
    row_ = candidate('low', 'm5')
    table = routing_capabilities.CapabilityTable()
    table.benchmarks = bench
    decision = model_router.select_model([row_], difficulty=3, kind='code', capability_table=table)
    assert decision['reason'] == 'prior_only_unproven'
    assert decision['tier_basis']['benchmark']['confidence'] == 'low'


def test_prior_weighs_on_few_runs_and_large_gap_is_flagged():
    strong = priors_for()
    # Tier-1 model (m1, high confidence) with 3/3 successes at difficulty 3: not yet demonstrated.
    weak = routing_capabilities.tier_detail('m1', profile(3, 3, 3), 'code', 3, None, benchmarks=strong)
    assert weak['tier'] == 2 and weak['source'] == 'measured_with_prior'
    plain = routing_capabilities.tier_detail('unknown', profile(3, 3, 3), 'code', 3, None, benchmarks=strong)
    assert plain['tier'] == 3 and plain['source'] == 'measured'
    converged = routing_capabilities.tier_detail('m1', profile(3, 12, 12), 'code', 3, None, benchmarks=strong)
    assert converged['tier'] == 3 and converged['source'] == 'measured'
    # Boundary: a tier-1 prior at difficulty 5 needs 11 straight successes, not 10.
    assert routing_capabilities.tier_detail('m1', profile(5, 10, 10), 'code', 5, None, benchmarks=strong)['tier'] == 4
    assert routing_capabilities.tier_detail('m1', profile(5, 11, 11), 'code', 5, None, benchmarks=strong)['tier'] == 5
    gap = routing_capabilities.tier_detail('m5', profile(3, 0, 6), 'code', 3, None, benchmarks=strong)
    assert gap['prior_gap'] == ['code:3'] and gap['tier'] == 2


def test_router_records_sources_and_confidence(tmp_path):
    state = tmp_path / 'state.json'
    (tmp_path / cb.SNAPSHOT_FILE).write_text(json.dumps(five_models()), encoding='utf-8')
    table = routing_capabilities.read_capability_table(state)
    decision = model_router.select_model([candidate('strong', 'm5'), candidate('weak', 'm1')],
                                         difficulty=4, kind='code', capability_table=table)
    assert decision['binding_ref'] == 'strong' and decision['tier_source'] == 'benchmark'
    basis = decision['tier_basis']['benchmark']
    assert basis['confidence'] == 'high' and basis['snapshot_id'] == 'fixture@2026-10-19'
    assert all(s['evidence'] for s in basis['sources'])
    json.dumps(decision)
    # Without an adopted snapshot routing is unchanged.
    (tmp_path / cb.SNAPSHOT_FILE).unlink()
    assert routing_capabilities.read_capability_table(state) == {}
    (tmp_path / cb.SNAPSHOT_FILE).write_text('{"version": 2}', encoding='utf-8')
    with pytest.raises(ValueError, match='invalid_capability_benchmarks'):
        routing_capabilities.read_capability_table(state)


def test_needs_benchmark_lists_uncovered_catalog_models():
    data = cb.seed_snapshot()
    data['families']['glm-5.3']['scores'] = [row('hle', 1, 'alpha')]
    listed = cb.needs_benchmark(['workbuddy/glm-5.3', 'workbuddy/glm-5.2', 'mystery-9'], data)
    assert [x['model_id'] for x in listed] == ['mystery-9', 'workbuddy/glm-5.2']
    assert all(x['status'] == 'needs_benchmark' and x['unproven'] for x in listed)
    assert set(cb.SEED_FAMILIES) >= {'deepseek-v4.1-flash', 'glm-5.3', 'kimi-k3', 'minimax-m3', 'doubao-seed-code',
                                     'gpt-6.1-sol', 'claude-opus', 'codestral', 'agnes-3.0'}


SPEC = {'source': 'fixture-board', 'url': 'https://board.example/api/rows.json', 'format': 'json_rows',
        'model_field': 'model', 'variant_field': 'variant',
        'score_fields': {'swe': 'swe_bench_verified', 'gpqa': 'gpqa_diamond'}}
PAYLOAD = json.dumps({'rows': [
    {'model': 'workbuddy/glm-5.3', 'variant': 'GLM-5.3', 'swe': 70.1, 'gpqa': '80.5'},
    {'model': 'deepseek-v4-pro', 'swe': 65, 'gpqa': None},
    {'model': 'never-seen-model', 'swe': 50},
    {'model': 'glm-5.2', 'swe': '62.0%'},
]}).encode()


def test_importer_parses_recorded_fixture_and_stages_diff(tmp_path):
    rows = cb.parse_source(PAYLOAD, SPEC)
    assert {(r['model'], r['benchmark']) for r in rows} == {
        ('workbuddy/glm-5.3', 'swe_bench_verified'), ('workbuddy/glm-5.3', 'gpqa_diamond'),
        ('deepseek-v4-pro', 'swe_bench_verified'), ('never-seen-model', 'swe_bench_verified')}
    new, unmatched = cb.build_candidate(cb.seed_snapshot(), SPEC, rows, retrieved_at='2026-10-20',
                                        snapshot_id='fixture-board@2026-10-20')
    assert unmatched == ['never-seen-model']
    assert new['families']['glm-5.3']['scores'][0]['url'] == SPEC['url']
    staged = cb.stage_candidate(tmp_path, new)
    assert len([c for c in staged['changes'] if 'added' in c]) == 3
    assert not (tmp_path / cb.SNAPSHOT_FILE).exists()  # nothing used before confirmation
    with pytest.raises(ValueError, match='candidate_digest_mismatch'):
        cb.adopt_candidate(tmp_path, '0' * 64)
    assert cb.adopt_candidate(tmp_path, staged['digest'])['snapshot_id'] == 'fixture-board@2026-10-20'
    assert cb.read_snapshot(tmp_path / cb.SNAPSHOT_FILE) == new
    # Re-import replaces this source's rows instead of duplicating them.
    again, _ = cb.build_candidate(new, SPEC, rows, retrieved_at='2026-10-27', snapshot_id='x')
    assert len(again['families']['glm-5.3']['scores']) == 2
    # A model the source no longer lists loses that source's rows.
    dropped, _ = cb.build_candidate(new, SPEC, [r for r in rows if r['model'] != 'deepseek-v4-pro'],
                                    retrieved_at='2026-10-27', snapshot_id='y')
    assert dropped['families']['deepseek-v4-pro']['scores'] == []
    assert any(c.get('family') == 'deepseek-v4-pro' and 'removed' in c for c in cb.diff_snapshots(new, dropped))


def test_diff_shows_every_digest_change():
    base = five_models()
    moved = json.loads(json.dumps(base))
    moved['families']['m1']['scores'][0]['url'] = 'https://alpha.example/moved'
    moved['snapshot_id'] = 'fixture@2026-10-20'
    del moved['families']['m2']
    changes = cb.diff_snapshots(base, moved)
    assert cb.digest(base) != cb.digest(moved)
    assert {'snapshot_id_old': 'fixture@2026-10-19', 'snapshot_id_new': 'fixture@2026-10-20'} in changes
    assert any(c.get('family') == 'm1' and c.get('added', {}).get('url') == 'https://alpha.example/moved' for c in changes)
    assert any(c.get('family') == 'm2' and c.get('family_change') == 'removed' for c in changes)
    assert cb.diff_snapshots(base, base) == []


@pytest.mark.parametrize('alias', [['nested'], {'k': 'v'}, 3, None])
def test_non_string_alias_is_invalid_not_a_crash(alias):
    with pytest.raises(ValueError, match='invalid_capability_benchmarks'):
        cb.validate_snapshot(snapshot(a=(['a', alias], [])))


def test_importer_csv_and_cli_with_fixture(tmp_path, capsys):
    spec = SPEC | {'format': 'csv'}
    (tmp_path / 'spec.json').write_text(json.dumps(spec), encoding='utf-8')
    (tmp_path / 'board.csv').write_text('model,variant,swe,gpqa\nglm-5.3,,71,81\n', encoding='utf-8')
    assert cb.main(['import', '--state-dir', str(tmp_path), '--spec', str(tmp_path / 'spec.json'),
                    '--fixture', str(tmp_path / 'board.csv'), '--retrieved-at', '2026-10-20']) == 0
    out = json.loads(capsys.readouterr().out)
    assert out['unmatched_models'] == []
    assert len([c for c in out['changes'] if 'added' in c]) == 2
    # A first import also shows every family the seed adds.
    assert {c['family'] for c in out['changes'] if c.get('family_change') == 'added'} == set(cb.SEED_FAMILIES)
    assert cb.main(['adopt', '--state-dir', str(tmp_path), '--confirm', out['digest']]) == 0


@pytest.mark.parametrize('mutation', [
    {'url': 'http://board.example/x'}, {'url': 'https://user:pw@board.example/x'},
    {'headers': {'Authorization': 'Bearer x'}}, {'format': 'html'}, {'score_fields': {'x': 'vibes'}},
    {'rows_field': ['rows']},
])
def test_source_spec_must_be_https_and_credential_free(mutation):
    with pytest.raises(ValueError, match='invalid_benchmark_source'):
        cb.parse_source(PAYLOAD, SPEC | mutation)


class FakeResponse:
    def __init__(self, body, status=200):
        self.body, self.status = body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def read(self, limit=-1):
        return self.body[:limit] if limit >= 0 else self.body


def test_fetch_is_bounded_and_uses_injected_opener():
    seen = []

    def opener(request, timeout):
        seen.append((request.full_url, dict(request.header_items()), timeout))
        return FakeResponse(PAYLOAD)
    assert cb.fetch_source(SPEC, opener=opener) == PAYLOAD
    assert seen[0][0] == SPEC['url'] and not any(k.lower() == 'authorization' for k in seen[0][1])
    with pytest.raises(ValueError, match='too_large'):
        cb.fetch_source(SPEC, opener=lambda r, timeout: FakeResponse(b'x' * (cb.MAX_FETCH_BYTES + 5)))
    with pytest.raises(ValueError, match='http_error'):
        cb.fetch_source(SPEC, opener=lambda r, timeout: FakeResponse(b'', 500))


SNAPSHOT = Path(cb.__file__).with_name('capability_benchmarks_snapshot.json')


def test_reviewed_initial_snapshot_is_valid_and_cited():
    data = cb.read_snapshot(SNAPSHOT)
    assert data['snapshot_id'] == 'public-leaderboards@2026-10-20'
    seed = cb.seed_snapshot()
    assert {f: e['aliases'] for f, e in data['families'].items()} == {f: e['aliases'] for f, e in seed['families'].items()}
    rows = [r for e in data['families'].values() for r in e['scores']]
    assert rows and all(r['url'].startswith('https://') and r['variant'] and r['retrieved_at'] == '2026-10-20' for r in rows)
    # Families without verified numbers stay needs_benchmark.
    assert {x['family'] for x in cb.needs_benchmark(list(cb.SEED_FAMILIES), data)} == {
        'claude-opus', 'claude-sonnet', 'codestral', 'agnes-3.0'}
    priors = cb.compute_priors(data)
    assert priors['kimi-k3']['code']['confidence'] == 'high'
    assert priors['doubao-seed-code']['code']['confidence'] == 'low'  # one source only


@pytest.mark.parametrize('model, family', [
    # Live Magpie ids seen 2026-10-21 (#1313): exact same models under provider prefixes.
    ('opencode-zen-free/deepseek-v4.1-flash-free', 'deepseek-v4.1-flash'),
    ('workbuddy-ai/deepseek-v4.1-flash-sg', 'deepseek-v4.1-flash'),
    ('group/auto-deepseek-v4-1-flash', 'deepseek-v4.1-flash'),
    ('raccoon/sn-glm-5-3', 'glm-5.3'), ('trae-cn/glm-5.3-max', 'glm-5.3'),
    ('group/auto-kimi-k3', 'kimi-k3'), ('raccoon/sn-kimi-k3', 'kimi-k3'),
    ('group/auto-gpt-6-1-sol', 'gpt-6.1-sol'), ('workbuddy/deepseek-v4-pro', 'deepseek-v4-pro'),
    ('trae-cn/Doubao-Seed-Code', 'doubao-seed-code'), ('minimax-code/MiniMax-M3', 'minimax-m3'),
    # Different (smaller or unverified) models must not inherit a family's prior.
    ('trae-cn/glm-5.3-flash', None), ('workbuddy/glm-5.3-flash', None), ('workbuddy/kimi-k3-1', None),
    ('workbuddy/minimax-m3.1-flash', None), ('trae-cn/DeepSeek-V4-Flash', None),
])
def test_live_magpie_ids_resolve_only_to_their_own_family(model, family):
    priors = cb.BenchmarkPriors(cb.read_snapshot(SNAPSHOT))
    assert priors.family(model) == family
