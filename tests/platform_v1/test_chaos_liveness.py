"""Provider-free fault injection for goal retry, recovery and status.

Runs the real goal machinery (window, launch, ``runnable_tasks``, ``escalate_failed_tasks``,
``refresh_goal_status``) and fakes only the executor. Each attempt ends with an outcome from a
fault catalogue taken from live failure rows (2026-11-15 .. 11-19). Host events leave the rows
the host leaves: an orphaned durable run and a PENDING local call.

The oracle labels recorded faults independently of production classification. Transient
host faults must settle or retry. Model failures can exhaust the goal retry budget.
Host plumbing failures can exhaust a step's free retries and must leave an actionable
hold distinct from model budget exhaustion.

What it does not cover yet: workspace restore across bindings (#1689, needs git), the review
and repair loop (needs model-review evidence), real claims and coordinator ticks, and the
launcher (#1693). Mixed-fault cases age their attempts past backoff; a separate case checks
the retry deadline directly.

``NERELAN_CHAOS_SEEDS`` raises the number of random seeds for a longer local run.
"""
from __future__ import annotations

import os
import random
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Callable

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
import reverse_agent.platform_v1.goal_service as goal_service_module
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore

BASE = "c" * 40
MAX_RETRIES = 2  # the live continuous window's setting
FREE_RETRIES = 2  # per-step allowance in the current retry policy
BINDINGS = ("bind-a", "bind-b", "bind-c")
LONG_AGO = "2000-01-01T00:00:00Z"  # every backoff measured from updated_at has passed
STUCK_ROUNDS = 3
MAX_ROUNDS = 400


# --- fault catalogue: what an attempt can end with ----------------------------------------

def _finish(store, task, status, classification, detail=""):
    store._conn.execute(
        "UPDATE tasks SET status=?, failure_classification=?, failure_detail=?, updated_at=? WHERE id=?",
        (status, classification, detail, LONG_AGO, task.id))


def _orphaned_local_call(store, task):
    """What a host restart or redeploy leaves: a reconciled run and its local call still PENDING."""
    store._conn.execute(
        "INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_owner, lease_epoch, "
        "lease_expiry_ms, recovery_classification, created_at, updated_at) "
        "VALUES (?, ?, ?, '', 'old-host', 1, 1, 'orphan_stale_lease', ?, ?)",
        (f"run-{task.id}", task.id, task.execution_id, LONG_AGO, LONG_AGO))
    store._conn.execute(
        "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
        "idempotency_key, request_digest, state, external_operation_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'digest', 'PENDING', '', ?, ?)",
        (f"op-{task.id}", f"run-{task.id}", task.id, f"single-exec-{task.id}",
         f"single-exec-{task.id}-{task.execution_id}", LONG_AGO, LONG_AGO))


def _redeploy(store, task):
    _orphaned_local_call(store, task)
    _finish(store, task, "FAILED", "host_version_changed",
            "authority_sha_mismatch: the host was redeployed under the run")


def _restart_refused_dispatch(store, task):
    _orphaned_local_call(store, task)
    _finish(store, task, "FAILED", "ambiguous_external_operation", goal_service_module.REFUSED_SECOND_DISPATCH)


def _preparation_interrupted(store, task):
    _finish(store, task, "BLOCKED", "blocked", "worktree_preparation_failed:host_restarted")


@dataclass(frozen=True)
class Fault:
    name: str
    kind: str
    apply: Callable


def _plain(status, classification, detail=""):
    return lambda store, task: _finish(store, task, status, classification, detail)


FAULTS = (
    # Liveness and provider faults seen live 2026-11-15 .. 11-19.
    Fault("stall", "host", _plain("FAILED", "executor_stalled", "opencode_stalled:900")),
    Fault("rate_limit_429", "host", _plain(
        "FAILED", "api_error_429",
        "opencode_nonzero:exit=1:api_error_429 name=APIError status=429 message=inference exceeds tpm/rpm limit")),
    Fault("rate_limit_in_generic_exit", "host", _plain(
        "FAILED", "executor_nonzero",
        'opencode_nonzero:exit=1:executor_nonzero name=UnknownError message={"message":"x: rpm exhausted '
        '(429: you can retry your request)","type":"api_error"')),
    Fault("quota_limit_hit", "host", _plain("FAILED", "quota_exhausted:limit_hit", "quota_exhausted:limit_hit")),
    Fault("quota_credits", "host", _plain(
        "FAILED", "quota_exhausted",
        "opencode_nonzero:exit=1:quota_exhausted name=APIError status=429 message=Credits exhausted")),
    Fault("terminated", "host", _plain("FAILED", "executor_terminated", "exit=3221225786")),
    Fault("termination_in_generic_exit", "host", _plain(
        "FAILED", "executor_nonzero", "opencode_nonzero:exit=3221225786:executor_nonzero")),
    Fault("pool_misroute", "plumbing", _plain(
        "FAILED", "owner_window_binding_outside_confirmed_pool", "owner_window_binding_outside_confirmed_pool")),
    # Host events: a restart or redeploy while the attempt ran.
    Fault("redeploy", "host", _redeploy),
    Fault("restart_refused_dispatch", "host", _restart_refused_dispatch),
    Fault("preparation_interrupted", "host", _preparation_interrupted),
    # Real model failures: these may spend the window's max_retries.
    Fault("model_hygiene", "model", _plain("FAILED", "patch_hygiene_failed", "functional_patch_hygiene_failed")),
    Fault("model_nonzero", "model", _plain("FAILED", "executor_nonzero", "opencode_nonzero:exit=1:executor_nonzero")),
)
BY_NAME = {fault.name: fault for fault in FAULTS}
HOST_FAULTS = tuple(fault for fault in FAULTS if fault.kind == "host")
NON_MODEL_FAULTS = tuple(fault for fault in FAULTS if fault.kind != "model")
MODEL_FAULTS = tuple(fault for fault in FAULTS if fault.kind == "model")


# --- the bed --------------------------------------------------------------------------------

def _resolver(plan_task, *, goal, avoid_bindings=(), failed_binding="", **kwargs):
    """A pool of equal-tier bindings; honours avoidance like the live router."""
    choice = next((ref for ref in BINDINGS if ref not in avoid_bindings and ref != failed_binding), BINDINGS[0])
    return {"binding_ref": choice, "executor_kind": "opencode", "model_id": f"pool/{choice}", "tier": 3,
            "reason": "chaos_bed", "context_window": 128000}


class Bed:
    def __init__(self, monkeypatch):
        monkeypatch.setattr(goal_service_module, "resolve_repository_workspace", lambda repository: object())
        monkeypatch.setattr(goal_service_module, "repository_base", lambda repository: BASE)
        self.store = TaskStore(":memory:")
        self.control = PlatformControlStore(self.store)
        # Live goals carry the Owner's per-goal admission receipts; admission is not under test here.
        monkeypatch.setattr(self.control, "check_strict_task_admission", lambda window_id, task_id: None)
        self.autonomy = AutonomyService(control_store=self.control, capabilities=CapabilityRegistry())
        self.goals = GoalService(store=self.store, control_store=self.control, task_resolver=_resolver,
                                 roster_resolver=lambda role: ("opencode", BINDINGS[0]))
        now = datetime.now(timezone.utc)
        self.window = self.autonomy.activate({
            "policy_id": "owner-window-chaos", "policy_revision": 1, "owner_identity": "owner@example",
            "starts_at": (now - timedelta(seconds=5)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
            "max_concurrent_tasks": 3, "max_tasks": 100, "max_retries": MAX_RETRIES, "confirmation": "ACTIVATE"})
        self.scripts: dict[str, list[Fault]] = {}
        self.model_failures: dict[str, int] = {}
        self.free_faults: Counter[tuple[str, str]] = Counter()
        self.plumbing_block: dict[str, str] = {}
        self.trace: dict[str, list[str]] = {}

    def add_goal(self, key: str, script: list[Fault], *, steps: int = 2) -> str:
        goal = self.goals.create({"objective": f"Chaos {key}", "repository": "dddd2024/Nerelan",
                                  "idempotency_key": f"chaos-{key}", "executor_kind": "opencode",
                                  "orchestration_mode": "agent_team", "binding_ref": ""})
        plan = [{"id": "T001", "title": "Implement", "instruction": "Implement", "agent_role": "coder"}]
        for n in range(2, steps + 1):
            plan.append({"id": f"T{n:03d}", "title": f"Step {n}", "instruction": f"Step {n}",
                         "dependencies": [f"T{n - 1:03d}"], "agent_role": "coder"})
        self.goals.plan(goal.id, expected_revision=1, tasks=plan)
        self.goals.approve(goal.id, expected_revision=1)
        self.goals.launch(goal.id, expected_revision=1, window_id=self.window.id)
        self.scripts[goal.id] = list(script)
        self.model_failures[goal.id] = 0
        self.trace[goal.id] = [f"script={[fault.name for fault in script]}"]
        return goal.id

    def _attempt_count(self, goal_id: str) -> int:
        return len(self.control.list_task_escalations(goal_id)) + len(self.control.list_goal_tasks(goal_id))

    def _execute_runnable(self) -> set[str]:
        """The fake executor: every runnable QUEUED attempt ends with its goal's next scripted outcome."""
        touched = set()
        for task_id in self.control.runnable_tasks(self.window.id, limit=500):
            task = self.store.get_task(task_id)
            if task.status != "QUEUED":
                continue
            goal_id = self.control.goal_id_for_task(task_id)
            plan_task = next(link["plan_task_id"] for link in self.control.list_goal_tasks(goal_id)
                             if link["task_id"] == task_id)
            script = self.scripts[goal_id]
            if script:
                fault = script.pop(0)
                fault.apply(self.store, task)
                if fault.kind == "model":
                    self.model_failures[goal_id] += 1
                else:
                    key = (goal_id, plan_task)
                    if fault.kind == "plumbing" and self.free_faults[key] >= FREE_RETRIES:
                        self.plumbing_block[goal_id] = task.id
                    self.free_faults[key] += 1
                outcome = fault.name
            else:
                _finish(self.store, task, "READY_FOR_REVIEW", "")
                outcome = "success"
            self.store._conn.commit()
            self.trace[goal_id].append(f"{plan_task}:{task.binding_ref}:{outcome}")
            touched.add(goal_id)
        return touched

    def expected_status(self, goal_id: str) -> str:
        if goal_id in self.plumbing_block or self.model_failures[goal_id] > MAX_RETRIES:
            return "BLOCKED"
        return "COMPLETED"

    def make_continuous(self) -> None:
        # Goals are launched first; then the window becomes a continuous Owner run (#1538), as on
        # the live host (launching into it would need per-goal Owner confirmation, not under test).
        self.store._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode='OWNER_WINDOW', "
                                 "expires_at='', max_tasks=1000000 WHERE id=?", (self.window.id,))
        self.store._conn.commit()

    def run(self) -> list[str]:
        """Rounds of execute -> escalate -> refresh until every goal settles; returns violations."""
        self.make_continuous()
        stuck = {goal_id: 0 for goal_id in self.scripts}
        violations: list[str] = []
        for _ in range(MAX_ROUNDS):
            before = {goal_id: self._attempt_count(goal_id) for goal_id in self.scripts}
            touched = self._execute_runnable()
            for goal_id in self.scripts:
                self.goals.escalate_failed_tasks(goal_id)
                self.control.refresh_goal_status(goal_id)
            open_goals = 0
            for goal_id in self.scripts:
                status = self.control.get_goal(goal_id).status
                if status == self.expected_status(goal_id):
                    stuck[goal_id] = 0
                    continue
                open_goals += 1
                moved = goal_id in touched or self._attempt_count(goal_id) != before[goal_id]
                stuck[goal_id] = 0 if moved else stuck[goal_id] + 1
                if stuck[goal_id] == STUCK_ROUNDS:
                    violations.append(self.describe(goal_id, f"stuck {STUCK_ROUNDS} rounds, goal {status}"))
            if open_goals == 0:
                break
            if violations:
                return violations
        else:
            violations += [self.describe(goal_id, f"no settlement in {MAX_ROUNDS} rounds")
                           for goal_id in self.scripts
                           if self.control.get_goal(goal_id).status != self.expected_status(goal_id)]
        return violations

    def describe(self, goal_id: str, why: str) -> str:
        links = [f"{link['plan_task_id']}={link['status']}/{self.store.get_task(link['task_id']).failure_classification}"
                 for link in self.control.list_goal_tasks(goal_id)]
        holds = [f"{event.metadata.get('reason')}" for link in self.control.list_goal_tasks(goal_id)
                 for event in self.store.get_events(link["task_id"]) if event.type == "MODEL_SELECTION_FAILED"]
        reasons = [row["reason"] for row in self.control.list_task_escalations(goal_id)]
        return (f"{why}; model_failures={self.model_failures[goal_id]}/{MAX_RETRIES}; links={links}; "
                f"escalations={reasons}; holds={holds}; trace={self.trace[goal_id]}")


def _assert_live(bed: Bed) -> None:
    violations = bed.run()
    assert not violations, "liveness violations:\n" + "\n".join(violations)
    for goal_id, task_id in bed.plumbing_block.items():
        current = {link["task_id"] for link in bed.control.list_goal_tasks(goal_id)}
        assert task_id in current, bed.describe(goal_id, "plumbing attempt was replaced after its cap")
        events = [event for event in bed.store.get_events(task_id)
                  if event.type == "MODEL_SELECTION_FAILED"
                  and event.metadata.get("reason") == "host_retry_limit_reached"]
        assert len(events) == 1, bed.describe(goal_id, "expected one actionable plumbing hold")
        assert events[0].metadata["cause"] == "owner_window_binding_outside_confirmed_pool"


@pytest.fixture
def bed(monkeypatch):
    instance = Bed(monkeypatch)
    try:
        yield instance
    finally:
        instance.store._conn.close()


# --- deterministic cases: each host fault, alone and repeated --------------------------------

@pytest.mark.parametrize("fault", [fault.name for fault in HOST_FAULTS])
@pytest.mark.parametrize("repeat", [1, 3])
def test_a_goal_survives_repeated_host_faults(bed, fault, repeat):
    goal_id = bed.add_goal(f"{fault}-{repeat}", [BY_NAME[fault]] * repeat)
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "COMPLETED"


def test_model_failures_within_the_budget_still_complete(bed):
    goal_id = bed.add_goal("model-within", [BY_NAME["model_hygiene"]] * MAX_RETRIES)
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "COMPLETED"


def test_model_failures_past_the_budget_block_the_goal(bed):
    # The oracle's other side: the bed must not hide a real budget stop.
    goal_id = bed.add_goal("model-past", [BY_NAME["model_hygiene"]] * (MAX_RETRIES + 1))
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "BLOCKED"


@pytest.mark.parametrize("fault", ["rate_limit_in_generic_exit", "termination_in_generic_exit", "pool_misroute"])
def test_free_host_retry_after_model_budget_is_spent(bed, fault):
    script = [BY_NAME["model_hygiene"]] * MAX_RETRIES + [BY_NAME[fault]]
    goal_id = bed.add_goal(fault, script)
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "COMPLETED"
    assert bed.goals.retry_options(goal_id)["routing_retries_left"] == 0


def test_plumbing_uses_only_shared_free_retries(bed):
    script = [BY_NAME["rate_limit_429"]] + [BY_NAME["pool_misroute"]] * FREE_RETRIES
    goal_id = bed.add_goal("plumbing-cap", script)
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "BLOCKED"
    assert bed.goals.retry_options(goal_id)["routing_retries_left"] == MAX_RETRIES
    for _ in range(2):
        assert bed.goals.escalate_failed_tasks(goal_id) == ()
    _assert_live(bed)  # repeated ticks do not duplicate the hold event


def test_wrapped_rate_limit_after_free_cap_waits_then_retries(bed, monkeypatch):
    script = [BY_NAME["rate_limit_in_generic_exit"]] * (FREE_RETRIES + 1)
    goal_id = bed.add_goal("rate-limit-backoff", script)
    bed.make_continuous()
    # Use the real retry deadline with a fake clock, without changing database time.
    for _ in range(FREE_RETRIES):
        bed._execute_runnable()
        assert len(bed.goals.escalate_failed_tasks(goal_id)) == 1
    bed._execute_runnable()
    deadline = datetime.fromisoformat(LONG_AGO).timestamp() + 120 * 2**FREE_RETRIES
    clock = SimpleNamespace(time=lambda: deadline - 1)
    monkeypatch.setattr(goal_service_module, "time", clock)
    assert bed.goals.escalate_failed_tasks(goal_id) == ()
    clock.time = lambda: deadline
    assert len(bed.goals.escalate_failed_tasks(goal_id)) == 1
    _assert_live(bed)
    assert bed.control.get_goal(goal_id).status == "COMPLETED"


# --- random mixes: several goals at once, host and model faults interleaved -----------------

SEEDS = int(os.environ.get("NERELAN_CHAOS_SEEDS", "12"))


@pytest.mark.parametrize("seed", range(SEEDS))
def test_random_fault_mixes_never_strand_a_goal(bed, seed):
    rng = random.Random(seed)
    for n in range(6):
        script = [rng.choice(NON_MODEL_FAULTS) for _ in range(rng.randint(0, 6))]
        for _ in range(rng.randint(0, MAX_RETRIES)):
            script.insert(rng.randint(0, len(script)), rng.choice(MODEL_FAULTS))
        bed.add_goal(f"s{seed}-g{n}", script, steps=rng.randint(1, 3))
    _assert_live(bed)
