from dataclasses import replace
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.cost_quality_benchmark import (
    BenchmarkContract, BenchmarkError, compare_arms, summarize_arm,
)


CONTRACT = BenchmarkContract('a'*40, 'b'*64, 'c'*64, 'd'*64, 'e'*64)


class Observations:
    def __init__(self, rows=()):
        self.rows = rows

    def get_task(self, task_id, event_limit=0):
        return SimpleNamespace(id=task_id, execution_id='exec-'+task_id, branch='a'*40,
                               status='READY_FOR_REVIEW', failure_classification='',validation_exit_code=0)

    def list_usage_observations(self, task_id):
        return self.rows

    def get_events(self, task_id):
        return ()


def summary(arm='A', **kw):
    return summarize_arm(Observations(), contract=CONTRACT, arm=arm, task_ids=['task'],delivery_task_id='task',
                         wall_seconds=10, verification_seconds=2, coordination_seconds=1, **kw)


def accepted():
    return {'contract_identity':CONTRACT.identity, 'artifact_digest':'f'*64,
            'evaluator_ref':'independent-hidden-v1', 'independent':True, 'verdict':'ACCEPT'}


def test_unknown_usage_and_subscription_cost_never_become_zero():
    a, b = summary(), summary('B')
    assert a['usage']['cost_micro_units']['total'] is None
    assert a['cash_cost'] is None and a['quota_units'] is None
    assert not a['independently_accepted']
    result = compare_arms(a, b)
    assert result['cash_savings_fraction'] is None
    assert set(result['blockers']) == {'independent_acceptance_missing', 'cash_cost_unknown', 'tool_equivalence_unverified'}


def test_quality_and_same_contract_gate_cash_comparison():
    a = summary(cash_cost=10, currency='USD', acceptance=accepted(),observed_tools_digest='d'*64)
    b = summary('B', cash_cost=4, currency='USD', acceptance=accepted(),observed_tools_digest='d'*64)
    assert compare_arms(a,b)['cash_savings_fraction'] == .6
    assert compare_arms(a,b)['general_savings_claim'] is False
    b['contract_identity'] = replace(CONTRACT, base_commit='f'*40).identity
    with pytest.raises(BenchmarkError, match='comparison_mismatch'):
        compare_arms(a,b)


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), True])
def test_measurements_reject_nonphysical_values(value):
    with pytest.raises(BenchmarkError, match='measurement_invalid'):
        summary(cash_cost=value, currency='USD')


def test_retry_role_usage_retains_unknown_fields():
    row = SimpleNamespace(execution_id='exec-task', input_units=5, output_units=3,
                          reasoning_units=None, cache_read_units=0, cache_write_units=None, cost_micro_units=8)
    other = SimpleNamespace(**{**row.__dict__, 'cost_micro_units':None})
    s = summarize_arm(Observations((row,other)), contract=CONTRACT, arm='B', task_ids=['task'],delivery_task_id='task',
                      wall_seconds=2, verification_seconds=0, coordination_seconds=0)
    assert s['usage']['input_units']['total'] == 10
    assert s['usage']['cost_micro_units'] == {'known_total':8, 'unknown_observations':1, 'total':None}
    other.execution_id = 'old-execution'
    with pytest.raises(BenchmarkError, match='execution_mismatch'):
        summarize_arm(Observations((other,)), contract=CONTRACT, arm='B', task_ids=['task'],delivery_task_id='task',
                      wall_seconds=2, verification_seconds=0, coordination_seconds=0)


def test_untrusted_or_stale_acceptance_cannot_pass():
    claim = accepted()
    claim['independent'] = False
    assert not summary(acceptance=claim)['independently_accepted']
    claim['contract_identity'] = 'stale'
    with pytest.raises(BenchmarkError, match='acceptance_binding_invalid'):
        summary(acceptance=claim)


def test_duplicate_tasks_and_zero_baseline_do_not_make_savings():
    with pytest.raises(BenchmarkError, match='tasks_invalid'):
        summarize_arm(Observations(),contract=CONTRACT,arm='A',task_ids=['task','task'],delivery_task_id='task',
                      wall_seconds=1,verification_seconds=0,coordination_seconds=0)
    a = summary(cash_cost=0,currency='USD',acceptance=accepted())
    assert 'zero_baseline_cash_cost' in compare_arms(a,summary('B',cash_cost=0,currency='USD',acceptance=accepted()))['blockers']


def test_role_without_observations_keeps_total_unknown():
    row = SimpleNamespace(execution_id='exec-task', input_units=5, output_units=3,
                          reasoning_units=0, cache_read_units=0, cache_write_units=0, cost_micro_units=8)
    class Partial(Observations):
        def list_usage_observations(self, task_id):
            return (row,) if task_id == 'task' else ()
    s = summarize_arm(Partial(),contract=CONTRACT,arm='B',task_ids=['task','review'],delivery_task_id='task',
                      wall_seconds=2,verification_seconds=0,coordination_seconds=0)
    assert s['missing_usage_tasks'] == 1
    assert s['usage']['cost_micro_units']['known_total'] == 8
    assert s['usage']['cost_micro_units']['total'] is None


def test_quality_pass_after_timeout_cannot_become_completed_workflow():
    class TimedOut(Observations):
        def get_task(self,task_id,event_limit=0):
            task=super().get_task(task_id,event_limit=event_limit)
            task.status='FAILED'
            task.validation_exit_code=-1
            return task
    s=summarize_arm(TimedOut(),contract=CONTRACT,arm='B',task_ids=['task'],delivery_task_id='task',wall_seconds=600,
                    verification_seconds=2,coordination_seconds=1,acceptance=accepted())
    assert s['artifact_independently_accepted']
    assert not s['workflow_completed'] and not s['independently_accepted']
