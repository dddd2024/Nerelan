"""Provider-free comparison of frozen tasks using existing usage observations.

These records are evidence, never execution authority. Missing cash/quota facts
remain unknown; provider-reported cost is not a subscription cash invoice.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence


class BenchmarkError(ValueError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _sha(value: str, length: int) -> str:
    if not isinstance(value, str) or not re.fullmatch(f"[0-9a-f]{{{length}}}", value):
        raise BenchmarkError("benchmark_identity_invalid")
    return value


@dataclass(frozen=True)
class BenchmarkContract:
    base_commit: str
    requirements_digest: str
    acceptance_digest: str
    tools_digest: str
    resource_budget_digest: str

    def __post_init__(self) -> None:
        _sha(self.base_commit, 40)
        for value in (self.requirements_digest, self.acceptance_digest,
                      self.tools_digest, self.resource_budget_digest):
            _sha(value, 64)

    @property
    def identity(self) -> str:
        return digest(self.__dict__)


def _nonnegative(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        raise BenchmarkError("benchmark_measurement_invalid")
    return float(value)


def summarize_arm(store: Any, *, contract: BenchmarkContract, arm: str,
                  task_ids: Sequence[str], delivery_task_id: str, wall_seconds: float,
                  verification_seconds: float, coordination_seconds: float,
                  cash_cost: float | None = None, currency: str | None = None,
                  quota_units: float | None = None, human_seconds: float | None = None,
                  observed_tools_digest: str | None = None,
                  acceptance: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Read actual TaskStore usage, counting every admitted role and retry.

    Acceptance must come from a trusted caller's independent evaluator. This
    function checks its binding; it does not certify reviewer independence.
    """
    if not isinstance(arm, str) or not arm or len(arm) > 80 or any(ord(c) < 32 for c in arm):
        raise BenchmarkError("benchmark_arm_invalid")
    if not task_ids or len(set(task_ids)) != len(task_ids):
        raise BenchmarkError("benchmark_tasks_invalid")
    if delivery_task_id not in task_ids:
        raise BenchmarkError("benchmark_delivery_task_invalid")
    wall, verification, coordination = map(_nonnegative, (wall_seconds, verification_seconds, coordination_seconds))
    if any(x is None for x in (wall, verification, coordination)):
        raise BenchmarkError("benchmark_measurement_required")
    cash, quota, human = map(_nonnegative, (cash_cost, quota_units, human_seconds))
    if observed_tools_digest is not None:
        _sha(observed_tools_digest, 64)
    if (cash is None) != (currency is None) or (currency is not None and not re.fullmatch('[A-Z]{3}', currency)):
        raise BenchmarkError("benchmark_currency_invalid")
    rows = []
    tasks = []
    native_usage = []
    missing_usage_tasks = 0
    for task_id in task_ids:
        task = store.get_task(task_id, event_limit=0)
        if task.branch != contract.base_commit:
            raise BenchmarkError("benchmark_base_mismatch")
        tasks.append({"task_id":task.id, "execution_id":task.execution_id,
                      "status":task.status, "failure_classification":task.failure_classification,
                      "validation_exit_code":task.validation_exit_code})
        # Native account CLIs expose token counters separately from dollar cost.
        # Preserve provider definitions; do not silently combine unlike counters.
        for event in store.get_events(task_id):
            usage = event.metadata.get('token_usage')
            if event.type != 'EXECUTOR_COMPLETED' or not isinstance(usage, dict):
                continue
            keys = ('input_tokens', 'output_tokens', 'cached_input_tokens')
            if not all(type(usage.get(key)) is int and usage[key] >= 0 for key in keys):
                continue
            native_usage.append({'task_id':task_id, 'event_id':event.id,
                                 'executor':event.metadata.get('executor_kind'),
                                 'counters':{key:usage[key] for key in keys}})
        observations = store.list_usage_observations(task_id)
        if not observations:
            missing_usage_tasks += 1
        for row in observations:
            if row.execution_id != task.execution_id:
                raise BenchmarkError("benchmark_execution_mismatch")
            rows.append(row)
    # No observations is unknown, and an incomplete set never becomes zero.
    metrics = {}
    for field in ('input_units', 'output_units', 'reasoning_units', 'cache_read_units',
                  'cache_write_units', 'cost_micro_units'):
        values = [getattr(row, field) for row in rows]
        metrics[field] = {"known_total":sum(x for x in values if x is not None),
                          "unknown_observations":sum(x is None for x in values),
                          "total":sum(values) if values and not missing_usage_tasks and all(x is not None for x in values) else None}
    accepted = False
    artifact_accepted = False
    delivery = next(task for task in tasks if task['task_id'] == delivery_task_id)
    workflow_completed = delivery['status'] in {'READY_FOR_REVIEW', 'COMPLETED'} and delivery['validation_exit_code'] == 0
    receipt = None
    if acceptance is not None:
        required = {'contract_identity', 'artifact_digest', 'evaluator_ref', 'independent', 'verdict'}
        if set(acceptance) != required or acceptance['contract_identity'] != contract.identity:
            raise BenchmarkError("benchmark_acceptance_binding_invalid")
        _sha(acceptance['artifact_digest'], 64)
        if (type(acceptance['independent']) is not bool or acceptance['verdict'] not in {'ACCEPT', 'REJECT'}
                or not isinstance(acceptance['evaluator_ref'], str) or not acceptance['evaluator_ref']
                or len(acceptance['evaluator_ref']) > 200):
            raise BenchmarkError("benchmark_acceptance_invalid")
        receipt = dict(acceptance)
        artifact_accepted = receipt['independent'] and receipt['verdict'] == 'ACCEPT'
        accepted = artifact_accepted and workflow_completed
    return {'schema_version':1, 'authority':'NONE', 'contract_identity':contract.identity,
            'arm':arm, 'tasks':tasks, 'usage':metrics, 'usage_observation_count':len(rows),
            'delivery_task_id':delivery_task_id,
            'missing_usage_tasks':missing_usage_tasks,
            'native_usage':native_usage,
            'observed_tools_digest':observed_tools_digest,
            'wall_seconds':wall, 'verification_seconds':verification, 'coordination_seconds':coordination,
            'cash_cost':cash, 'currency':currency, 'quota_units':quota, 'human_seconds':human,
            'independently_accepted':accepted, 'artifact_independently_accepted':artifact_accepted,
            'workflow_completed':workflow_completed, 'acceptance':receipt}


def compare_arms(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    if left['contract_identity'] != right['contract_identity'] or left['arm'] == right['arm']:
        raise BenchmarkError("benchmark_comparison_mismatch")
    reasons = []
    if any(x['observed_tools_digest'] is None for x in (left, right)):
        reasons.append('tool_equivalence_unverified')
    elif left['observed_tools_digest'] != right['observed_tools_digest']:
        reasons.append('tool_mismatch')
    if not all(x['independently_accepted'] for x in (left, right)):
        reasons.append('independent_acceptance_missing')
    if any(x['cash_cost'] is None for x in (left, right)):
        reasons.append('cash_cost_unknown')
    elif left['currency'] != right['currency']:
        reasons.append('currency_mismatch')
    elif left['cash_cost'] == 0:
        reasons.append('zero_baseline_cash_cost')
    return {'schema_version':1, 'scope':'SINGLE_FROZEN_TASK', 'general_savings_claim':False,
            'contract_identity':left['contract_identity'], 'comparable_cash_cost':not reasons,
            'cash_savings_fraction':((left['cash_cost']-right['cash_cost']) / left['cash_cost']) if not reasons else None,
            'blockers':reasons}
