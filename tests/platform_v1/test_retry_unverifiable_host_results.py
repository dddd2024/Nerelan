"""2026-11-18: a step whose last attempt failed for a host reason must retry, never park silently.

- A validation the host could not carry out (functional_base_mismatch) left a result that can
  never verify; escalation skipped it with no event, so the step never retried.
- Attempts cut at the old 1 h wall limit counted as model failures and used up the budget.
"""
import subprocess

from reverse_agent.platform_v1 import functional_validation as validation
from reverse_agent.platform_v1 import goal_service as gs
from test_contract_miss_fixup import case  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)


def test_a_host_side_validation_failure_retries_the_step(case):
    root, base, store, control, service, goal, _, task = case
    subprocess.run(["git", "-C", str(root), "commit", "--allow-empty", "-qm", "moved"], check=True,
                   capture_output=True)
    moved = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                           capture_output=True, text=True).stdout.strip()
    command, code, reason, identity = validation.run_task_validation(
        store, task.id, worktree=root, base_commit=moved, execution_id=task.execution_id)
    assert code and reason == "functional_base_mismatch"
    store._conn.execute("UPDATE tasks SET status='FAILED', validation_command_id=?, validation_exit_code=?, "
                        "validation_output_digest=?, failure_classification='deterministic_validation_failure', "
                        "failure_detail=? WHERE id=?", (command, code, identity, reason, task.id))
    store._conn.commit()
    failed = store.get_task(task.id)
    assert not validation.functional_evidence(failed).get("verified")  # the result can never verify
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["from_task_id"] == task.id
    retry = store.get_task(step["to_task_id"])
    assert validation.frozen_base(retry) == base  # fresh attempt from the approved base, no reuse


def test_only_a_cut_at_the_old_wall_limit_is_a_wall_timeout():
    assert gs._wall_timeout("timeout", "opencode_timeout:3600") == "wall_timeout"
    assert gs._wall_timeout("timeout", "opencode_timeout:600") == "wall_timeout"
    assert gs._wall_timeout("timeout", "opencode_timeout:86400") == ""  # the runaway guard
    assert gs._wall_timeout("timeout", "opencode_timeout:cleanup_unconfirmed:3600") == ""
    assert gs._wall_timeout("timeout", "opencode_stalled:900") == ""
    assert gs._wall_timeout("executor_stalled", "opencode_timeout:3600") == ""


def test_wall_timeouts_share_the_free_cap_instead_of_spending_the_budget():
    rows = [{"plan_task_id": "a", "reason": "failed:timeout", "cause": "wall_timeout"}] * 2
    assert {gs._retry_kind(row) for row in rows} == {"plumbing"}
    assert gs._routing_retries_spent(rows, patient=True) == 0
    assert gs._routing_retries_spent(rows * 2, patient=True) == 2  # past the cap they spend again
