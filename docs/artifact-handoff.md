# Accepted artifact inputs

An ordinary dependency orders tasks. To consume another task's code, select that
dependency explicitly as `artifact_input: {"plan_task_id": "A"}` in the reviewed
Goal plan. Selection or removal changes the plan revision and approval digest.
Both tasks must have approved executable functional checks. No input is selected
automatically, and saving does not approve or launch a Goal.

The producer must have a current host-verified result. The host snapshots accepted
uncommitted edits through the existing private Git index and retains that exact
tree in a deterministic commit under the bounded local ref
`refs/nerelan/accepted-artifacts/<task-id>/<execution-id>`. It never stages the
producer's real index. Existing different bindings fail closed; identical retries
are idempotent. This local retention does not publish a branch or PR.

The existing TaskStore evidence holds the frozen contract, accepted producer and
consumed input identities. Durable changes use the existing owner/epoch fence.
Consumers prepare a detached worktree from the retained commit using the existing
OpenCode preparation path. The original approved repository base remains separate
from the prepared input HEAD. A later producer change cannot silently replace an
accepted input. Missing objects, mismatched Goal/repository/execution and stale
ownership reject admission or recovery.

An input-consuming `validate_task` runs the trusted functional checks against the
exact accepted tree, with no model roles dispatched. Ordinary single/team entry
points share this validation path. Durable single/team execution retains the
existing ordered checkpoint format; input-bound milestones and explicit skipped
role events record that planner, coder and reviewer did not run. Recovery uses
the persisted worktree and input binding without preparing or dispatching twice.
An `execute_task` consumer still must produce a new diff from its input, including
when the original approved base differs from the prepared input commit.

Task and Run functional evidence expose the selected producer task/execution,
commit/tree and result/binding digests. Raw output, environment and arbitrary paths
are excluded. Fixture, failed and zero-test results cannot qualify as accepted
inputs. Multiple outputs are never combined implicitly.

Backend acceptance uses real temporary Git repositories, disk SQLite reopen,
installed pytest and the loopback Task API. Model execution and binding metadata
are explicit doubles; these tests do not claim live provider or desktop acceptance.
