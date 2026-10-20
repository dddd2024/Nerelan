import json
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import artifact_handoff as handoff
from reverse_agent.platform_v1.agent_planner import extract_plan
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.review_contract import (
    validate_verdict, verdict_schema, ReviewContractError, MAX_RESPONSE_BYTES,
)


@pytest.mark.parametrize('verdict', ['ACCEPT', 'REJECT'])
def test_valid_verdict(verdict):
    value = {'verdict': verdict, 'findings': []}
    assert validate_verdict(json.dumps(value)) == value
    schema = verdict_schema()
    schema['required'].clear()
    assert verdict_schema()['required'] == ['verdict', 'findings']


@pytest.mark.parametrize('value', [None, [], {}, {'verdict': 'MAYBE', 'findings': []},
    {'verdict': 'ACCEPT', 'findings': {},}, '{"verdict":"ACCEPT","findings":[]} extra',
    '{"verdict":"REJECT","verdict":"ACCEPT","findings":[]}',
    '```json\n{"verdict":"ACCEPT","findings":[]}\n```'])
def test_invalid_response(value):
    with pytest.raises(ReviewContractError, match='model_review_invalid_response'):
        validate_verdict(value)


@pytest.mark.parametrize('patch', [{'file': '../secret'}, {'file': 'C:/file'}, {'file': '/abs'},
    {'file': 'a\\b'}, {'file': ''}, {'file': 'a\n'}, {'line': True}, {'line': 0},
    {'line': 1.5}, {'severity': 'warning'}, {'summary': ''}, {'summary': []}, {'extra': 1}])
def test_invalid_finding(patch):
    finding = {'file': 'src/file.py', 'line': 1, 'severity': 'blocking', 'summary': 'Fix this'}
    finding.update(patch)
    with pytest.raises(ReviewContractError):
        validate_verdict({'verdict': 'REJECT', 'findings': [finding]})


def test_bounds_and_accept_consistency():
    with pytest.raises(ReviewContractError, match='too_large'):
        validate_verdict(' ' * (MAX_RESPONSE_BYTES + 1))
    finding = {'file': 'a.py', 'line': 2, 'severity': 'blocking', 'summary': 'Problem'}
    with pytest.raises(ReviewContractError):
        validate_verdict({'verdict': 'ACCEPT', 'findings': [finding]})
    assert validate_verdict({'verdict': 'REJECT', 'findings': [finding]})['findings'] == [finding]
    with pytest.raises(ReviewContractError):
        validate_verdict({'verdict': 'REJECT', 'findings': [finding] * 101})


@pytest.mark.parametrize('traits', [{'kind': 'review'}, {'agent_role': 'reviewer'}])
def test_review_requires_explicit_input(traits):
    raw = dict(id='R', title='Review', instruction='Review', **traits)
    with pytest.raises(TaskStoreError, match='model_review_artifact_input_required'):
        extract_plan(json.dumps({'tasks': [raw]}))
    with pytest.raises(TaskStoreError, match='model_review_artifact_input_required'):
        GoalService._normalize_task(raw, seq=1)
    task = GoalService._normalize_task(dict(raw, artifact_input={'plan_task_id': 'A'}), seq=1)
    assert task.capability == 'validate_task'


@pytest.mark.parametrize('kind,role,mode', [('review', '', 'model_review'),
    ('code', 'reviewer', 'model_review'), ('code', '', 'host_validation')])
def test_frozen_traits_select_route(monkeypatch, kind, role, mode):
    documents = []
    store = SimpleNamespace(_bind_artifact_evidence=lambda *args, **kwargs: documents.append(kwargs['document']))
    task = SimpleNamespace(id='runtime', repository='owner/repo')
    planned = SimpleNamespace(id='R', kind=kind, agent_role=role, capability='validate_task',
                              artifact_input={'plan_task_id': 'A'})
    goal = SimpleNamespace(id='goal', revision=1, artifact_digest='a'*64, tasks=[])
    contract = handoff.freeze_handoff_contract(store, task, goal=goal, plan_task=planned, base_commit='b'*40)
    monkeypatch.setattr(handoff, '_load_evidence', lambda *args: contract)
    assert handoff.load_handoff_contract(task)['validation_mode'] == mode
    assert handoff.validation_only_input(task) == (mode == 'host_validation')
    assert handoff.model_review_input(task) == (mode == 'model_review')
    # Mutable runtime labels do not override frozen approval.
    task.kind = 'review' if kind == 'code' else 'code'
    assert handoff.validation_only_input(task) == (mode == 'host_validation')
    contract['validation_mode'] = 'execution'
    with pytest.raises(TaskStoreError, match='artifact_contract_invalid'):
        handoff.load_handoff_contract(task)


def test_legacy_unknown_validation_identity_fails_closed(monkeypatch):
    task = SimpleNamespace(id='runtime', repository='owner/repo')
    contract = dict(version=1, task_id=task.id, repository=task.repository, goal_id='goal',
                    goal_revision=1, goal_artifact_digest='a'*64, plan_task_id='R', base_commit='b'*40,
                    artifact_input={'plan_task_id': 'A'}, export_required=False, capability='validate_task')
    monkeypatch.setattr(handoff, '_load_evidence', lambda *args: contract)
    with pytest.raises(TaskStoreError, match='artifact_contract_invalid'):
        handoff.load_handoff_contract(task)
    contract['capability'] = 'execute_task'
    assert handoff.load_handoff_contract(task) == contract

def test_replay_rejects_changed_review_traits(monkeypatch):
    from reverse_agent.platform_v1 import control_store
    raw = dict(id='R', kind='code', agent_role='', capability='validate_task',
               artifact_input={'plan_task_id': 'A'}, dependencies=['A'])
    goal = SimpleNamespace(id='goal', repository='owner/repo', revision=1, artifact_digest='a'*64, tasks=[raw])
    control = SimpleNamespace(get_goal=lambda _: goal, list_goal_tasks=lambda _: [
        dict(task_id='runtime', plan_task_id='R', goal_revision=1)])
    monkeypatch.setattr(control_store, 'PlatformControlStore', lambda _: control)
    task = SimpleNamespace(id='runtime', repository='owner/repo')
    contract = dict(version=2, repository=task.repository, goal_id='goal', goal_revision=1,
                    goal_artifact_digest='a'*64, plan_task_id='R', capability='validate_task',
                    artifact_input={'plan_task_id': 'A'}, kind='review', agent_role='')
    with pytest.raises(TaskStoreError, match='artifact_approved_plan_changed'):
        handoff._current_goal(None, task, contract)
    raw['kind'] = 'review'
    assert handoff._current_goal(None, task, contract) is goal
