# LangGraph Parallel Worker Team Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real reverse-agent multi-worker execution path by reusing pinned `langgraph==1.0.5` for parallel fan-out/join and reusing the existing TaskStore + ExecutorRouter execution plane, with a structured verifier result that controls final workflow acceptance.

**Architecture:** `development_graph.py` keeps the #149 `execution_node` seam. A new internal LangGraph team subgraph uses native `Send` fan-out, reduces structured worker results, and runs a deterministic/injectable verifier. Because the internal team graph has a different state schema from `DevelopmentWorkflowState`, a thin execution-node adapter maps parent `team_assignments` into the internal team graph and maps only `team_execution_result` back into the parent graph. Actual worker execution goes through one shared programmatic Platform V1 execution service used by both the HTTP Task API and the LangGraph worker adapter. TaskStore remains the only durable product truth; LangGraph state carries only transient assignments/results and references to TaskStore records.

**Tech Stack:** Python 3.13, `langgraph==1.0.5`, SQLite TaskStore, existing `ExecutorRouter`, pytest.

## Global Constraints

- Base exactly on `owner/repository-modernization-v2-planning@d7cf40b13ab0997e747597976f3c0929ab80c8d6`.
- Do not add or upgrade runtime dependencies.
- Do not introduce AutoGen, OpenAI Agents SDK, CrewAI, a custom scheduler, or a custom thread pool for orchestration.
- Do not introduce `executor_kind="multi_agent"`; worker/team dispatch belongs to LangGraph, concrete execution belongs to `ExecutorRouter`.
- Do not create a second TaskStore/database or make LangGraph checkpoints canonical task/evidence truth.
- Do not modify `frontend/**`, `.github/**`, `project_state/**`, PR #146, model/provider config, credentials, publication/merge/release code.
- Existing `reverse_agent/orchestrator_*` and manual-mode orchestrator paths are legacy; inspect only to avoid reuse, do not extend them.
- No real model/provider call is required for acceptance; integration acceptance uses real TaskStore tasks with `deterministic_fixture` executors.
- Do not change the public meaning of `validation_command_id` in this task. Preserve the executor-owned approved validation command behavior.

---

### Task 1: Baseline and TaskStore concurrency proof

**Files:**
- Inspect: `reverse_agent/platform_v1/run_store.py`
- Test: `tests/platform_v1/test_task_contracts.py`

**Interfaces:**
- Consumes: current single `TaskStore` instance and its `create_task`, `add_event`, `add_evidence`, `get_task` APIs.
- Produces: evidence that one TaskStore instance can safely receive independent worker writes concurrently, or a minimal synchronization fix with regression coverage.

- [ ] **Step 1: Verify exact branch and baseline**

Run:

```powershell
git rev-parse HEAD
git status --short
python -m pytest tests/test_development_graph.py tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q
```

The starting HEAD after fetching/switching must match the canonical remote task-branch head supplied by Owner. Worktree must be clean and baseline tests must pass before production mutation.

- [ ] **Step 2: Write a deterministic concurrent-write test**

Add a focused test in `tests/platform_v1/test_task_contracts.py` that creates two independent tasks in the **same** `TaskStore`, starts two Python threads behind a `threading.Barrier(2)`, and has each thread append one valid event and one evidence record to its own task. Use an existing valid event type such as `EXECUTOR_RUNNING`; do not invent a new event type for the probe.

Capture exceptions from both threads and assert conceptually:

```python
assert exceptions == []
assert len(store.get_task(task_a.id).events) >= 2  # DISCOVERED + probe event
assert len(store.get_task(task_a.id).evidence_refs) == 1
assert len(store.get_task(task_b.id).events) >= 2
assert len(store.get_task(task_b.id).evidence_refs) == 1
```

Use finite barrier/join timeouts so a deadlock fails deterministically.

- [ ] **Step 3: Run the concurrency probe repeatedly**

Run the focused probe at least 20 times. On PowerShell an acceptable loop is:

```powershell
1..20 | ForEach-Object {
  python -m pytest tests/platform_v1/test_task_contracts.py -q
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

If all 20 runs pass, **do not add synchronization merely for style**. Record that the baseline shared-store probe passed.

If any run exposes SQLite connection races, transaction errors, locks, or nondeterministic reads/writes, continue to Step 4.

- [ ] **Step 4: Only if the probe fails, add the smallest safe TaskStore synchronization**

Use one `threading.RLock` owned by `TaskStore`. Because public methods call other TaskStore methods, synchronization must be re-entrant and must protect all connection-touching compound/public operations that can race, not only `add_event` in isolation. Do not introduce per-worker stores or a second DB.

Intended shape:

```python
from threading import RLock

class TaskStore:
    def __init__(...):
        ...
        self._lock = RLock()

    def get_task(...):
        with self._lock:
            ...

    def add_event(...):
        with self._lock:
            ...
```

Keep the change as small as correctness permits. Re-run the 20x probe and all TaskStore contract tests.

- [ ] **Step 5: Preserve evidence**

If a production lock was required, commit the synchronization + regression as a bounded checkpoint. If the baseline was already safe, leave only the regression test in the eventual combined task diff.

---

### Task 2: Extract one reusable trusted Task execution service

**Files:**
- Create: `reverse_agent/platform_v1/task_execution.py`
- Modify: `reverse_agent/platform_v1/task_service.py`
- Test: `tests/platform_v1/test_task_service.py`
- Test: `tests/platform_v1/test_task_runtime.py`

**Interfaces:**
- Consumes: `TaskStore`, `ExecutorRouter`, existing executor/event/evidence contracts, and the existing OpenCode executor-kwargs construction semantics.
- Produces a reusable programmatic execution path for an already-created TaskStore task.

Preferred surface after exact-code audit:

```python
@dataclass(frozen=True)
class TaskExecutionOutcome:
    task_id: str
    execution_id: str
    success: bool
    validation_command_id: str
    validation_exit_code: int
    changed_files: tuple[Mapping[str, Any], ...]
    evidence_ids: tuple[str, ...]
    failure_classification: str = ""
    failure_detail: str = ""

class TaskExecutionService:
    def __init__(self, store: TaskStore, router: ExecutorRouter) -> None: ...
    def execute(self, task_id: str, *, workspace_root: str) -> TaskExecutionOutcome: ...
```

Names may change only if exact repository conventions justify it; semantics may not.

- [ ] **Step 1: Write service tests before extraction**

Write focused tests that call the new programmatic service directly on a queued `deterministic_fixture` task and assert the same lifecycle currently produced by `POST /api/tasks/{id}/execute`:

```python
outcome = service.execute(task.id, workspace_root=str(tmp_path))
assert outcome.success is True
stored = store.get_task(task.id)
assert stored.status == "READY_FOR_REVIEW_FIXTURE"
assert stored.validation_exit_code == 0
assert stored.changed_files
assert any(e["category"] == "Validation" for e in stored.evidence_refs)
assert any(e["category"] == "Executor" for e in stored.evidence_refs)
```

Also test non-queued rejection and executor failure classification.

- [ ] **Step 2: Run new tests and verify RED**

Expected failure: programmatic execution service does not yet exist.

- [ ] **Step 3: Move, do not duplicate, the HTTP execution lifecycle**

Extract the existing status transitions, `ExecutorRouter.dispatch_execute`, changed-file persistence, validation persistence, executor/validation evidence, event callback persistence, and failure classification out of `_TaskHandler.do_POST` / `_run_executor` into the shared service.

Preserve existing statuses exactly:

```text
deterministic_fixture: QUEUED -> PREPARING_WORKSPACE -> RUNNING_FIXTURE -> VALIDATING -> READY_FOR_REVIEW_FIXTURE
other concrete executor: QUEUED -> PREPARING_WORKSPACE -> RUNNING -> VALIDATING -> READY_FOR_REVIEW
```

The service must use the task's existing `executor_kind`; it must never synthesize a team executor kind.

- [ ] **Step 4: Preserve OpenCode kwargs in the shared path**

Current `_build_executor_kwargs(task)` in `task_service.py` resolves OpenCode `model_id`, `repo_dir`, and `base_ref`. Move or reuse that logic so **both** HTTP and LangGraph worker execution use one exact implementation. Do not leave two copies with potentially different OpenCode behavior.

Do not add provider/model calls in the tests.

- [ ] **Step 5: Derive evidence ids from TaskStore records, not return values**

`TaskStore.add_evidence(...)` returns a `Task`, not the generated evidence id. Therefore `TaskExecutionOutcome.evidence_ids` must be derived from persisted TaskStore state, for example by taking the set/list difference of evidence IDs before vs. after execution, or by reading the final evidence set when the queued task is known fresh. Do not change `add_evidence` return type solely for Task 2 unless exact repository-wide audit proves it is safe and necessary.

- [ ] **Step 6: Make HTTP execute a thin adapter**

`POST /api/tasks/{id}/execute` should resolve workspace root and call the shared service, then serialize the current TaskStore task. Preserve current HTTP status/response tests.

Do not change the meaning of the optional HTTP `validation_command_id` parameter in this task; the concrete executor remains responsible for its approved validation command unless an existing tested path already consumes that parameter.

- [ ] **Step 7: Run Platform V1 regressions**

```powershell
python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_task_contracts.py tests/platform_v1/test_opencode_executor.py -q
```

Expected: PASS with zero model/provider calls.

---

### Task 3: Add structured worker/team contracts and parent workflow channels

**Files:**
- Modify: `reverse_agent/architecture/contracts.py`
- Test: create `tests/test_team_graph.py` if no existing team-graph test file exists.

**Interfaces:**
- Produces exact immutable team-domain contracts and two optional parent-state channels.

Preferred contracts:

```python
@dataclass(frozen=True)
class WorkerAssignment:
    worker_id: str
    role: str
    task_id: str
    workspace_root: str

@dataclass(frozen=True)
class WorkerExecutionResult:
    worker_id: str
    task_id: str
    execution_id: str
    success: bool
    validation_exit_code: int
    evidence_ids: tuple[str, ...] = ()
    failure_classification: str = ""
    reasons: tuple[str, ...] = ()

@dataclass(frozen=True)
class TeamExecutionResult:
    accepted: bool
    worker_results: tuple[WorkerExecutionResult, ...]
    reasons: tuple[str, ...] = ()
```

Add to `DevelopmentWorkflowState` only the transient orchestration channels needed by the parent graph:

```python
team_assignments: list[dict[str, Any]]
team_execution_result: dict[str, Any]
```

Do not add durable TaskStore copies to the parent state.

- [ ] **Step 1: Write validation/serialization tests**

Require non-empty `worker_id`, `role`, `task_id`, `workspace_root`. Reject duplicate worker ids at team-graph input validation rather than silently overwriting.

- [ ] **Step 2: Run and verify RED**

Expected: imports/classes/channels missing.

- [ ] **Step 3: Add minimal dataclasses and deterministic serialization**

Each contract must have deterministic `to_dict()`; add `from_mapping()` only where an actual graph boundary needs it.

Do not duplicate TaskStore task fields such as executor kind, model profile, permission profile, or policy into `WorkerAssignment`; `task_id` references the durable task row that already owns those facts.

- [ ] **Step 4: Run contract tests**

Expected: PASS.

---

### Task 4: Build the internal LangGraph-native parallel team subgraph

**Files:**
- Create: `reverse_agent/workflows/team_graph.py`
- Modify: `reverse_agent/workflows/__init__.py` only if a public export is justified.
- Test: `tests/test_team_graph.py`

**Interfaces:**
- Consumes: `list[WorkerAssignment]`, a worker callable/adapter, and a verifier callable.
- Produces: an **internal compiled LangGraph team graph** with its own team-state schema and output containing `team_execution_result`.

Preferred builder surface:

```python
def build_team_graph(
    *,
    worker: Callable[[WorkerAssignment], WorkerExecutionResult],
    verifier: Callable[[tuple[WorkerExecutionResult, ...]], TeamExecutionResult] | None = None,
): ...
```

- [ ] **Step 1: Verify pinned LangGraph primitives locally**

Use Python `inspect` against installed 1.0.5 and confirm `langgraph.types.Send`, state reducers, and compiled graph invocation behavior. Do not upgrade and do not assume latest-online API details.

- [ ] **Step 2: Write fan-out/join tests first**

Use a `threading.Barrier(2)` fake worker **only as a test instrument**. If LangGraph executes worker branches sequentially, the barrier test must timeout/fail; if LangGraph natively fans out concurrently, both workers pass and return results.

Assert both worker IDs are present and final result ordering is deterministic.

- [ ] **Step 3: Implement native `Send` fan-out**

Use a team-specific state with a reducer for parallel worker results, conceptually:

```python
class TeamWorkflowState(TypedDict, total=False):
    assignments: list[dict[str, Any]]
    assignment: dict[str, Any]
    worker_results: Annotated[list[dict[str, Any]], operator.add]
    team_execution_result: dict[str, Any]
```

A routing function returns one `Send("worker", {"assignment": assignment})` per assignment. The worker node emits exactly one `worker_results` element. Use the reducer to merge parallel results. Do not create a Python thread pool/scheduler yourself.

- [ ] **Step 4: Fan in to verifier**

Use LangGraph edges so all worker sends complete before verifier/join executes. Sort `WorkerExecutionResult` values by `worker_id` before building `TeamExecutionResult`, because parallel branch update order must not become a product contract.

Default verifier accepts only when every worker result reports success. An injected verifier may reject otherwise-successful worker results and return deterministic reasons.

- [ ] **Step 5: Validate duplicate and empty assignments**

Reject empty team input or duplicate worker IDs before fan-out with a deterministic error/blocked result. Do not silently collapse assignments.

- [ ] **Step 6: Run team graph tests repeatedly**

Run the concurrency/fan-out test at least 20 times to catch scheduler/reducer nondeterminism.

---

### Task 5: Connect team workers to the real TaskStore + ExecutorRouter path

**Files:**
- Modify: `reverse_agent/workflows/team_graph.py` or create one narrowly scoped `reverse_agent/workflows/worker_execution.py` only if keeping the adapter separate materially improves clarity.
- Test: `tests/test_team_graph.py`
- Test: relevant Platform V1 tests.

**Interfaces:**
- Consumes: `TaskExecutionService` and `WorkerAssignment`.
- Produces: a worker callable that executes the referenced durable TaskStore task and returns only structured references/result facts.

- [ ] **Step 1: Write the real integration test**

Create one `TaskStore`, one `ExecutorRouter`, one `TaskExecutionService`, and two queued `deterministic_fixture` tasks. Build two assignments with distinct task IDs and distinct workspace-root directories. Invoke the internal team graph.

Assert all of the following:

```python
assert team.accepted is True
assert len(team.worker_results) == 2
assert store.get_task(task_a.id).status == "READY_FOR_REVIEW_FIXTURE"
assert store.get_task(task_b.id).status == "READY_FOR_REVIEW_FIXTURE"
assert store.get_task(task_a.id).validation_exit_code == 0
assert store.get_task(task_b.id).validation_exit_code == 0
assert store.get_task(task_a.id).evidence_refs
assert store.get_task(task_b.id).evidence_refs
assert task_a.id != task_b.id
```

Also prove both results reference the correct durable task/execution IDs and that no task/router registry value uses `multi_agent` as executor kind.

- [ ] **Step 2: Run and verify RED**

Expected: no TaskExecutionService-backed worker adapter yet.

- [ ] **Step 3: Implement the thinnest worker adapter**

The adapter must call:

```python
TaskExecutionService.execute(
    assignment.task_id,
    workspace_root=assignment.workspace_root,
)
```

and transform `TaskExecutionOutcome` into `WorkerExecutionResult`. It must not reimplement TaskStore status/evidence persistence.

- [ ] **Step 4: Add verifier rejection integration**

Run the same two successful fixture tasks with an injected verifier that rejects `worker-b`. Durable worker tasks stay successful, while aggregate `TeamExecutionResult.accepted` is false and deterministic reasons identify the verifier rejection. This proves verifier semantics are distinct from executor success.

- [ ] **Step 5: Run focused regressions**

```powershell
python -m pytest tests/test_team_graph.py tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q
```

---

### Task 6: Add the explicit parent-state execution-node adapter and acceptance propagation

**Files:**
- Modify: `reverse_agent/workflows/team_graph.py` or create a tiny adapter next to it.
- Modify: `reverse_agent/workflows/nodes/acceptance_gate.py`
- Modify: `reverse_agent/architecture/contracts.py` only if Task 3 did not already add the parent channels.
- Test: `tests/test_development_graph.py`
- Test: `tests/test_team_graph.py`

**Interfaces:**
- Internal team graph state and `DevelopmentWorkflowState` remain separate.
- Produces a thin parent execution-node callable, preferred surface:

```python
def build_team_execution_node(*, team_graph) -> Callable[[DevelopmentWorkflowState], dict[str, Any]]:
    ...
```

The adapter reads `state["team_assignments"]`, invokes the internal team graph with only its expected team-state input, and returns to the parent only:

```python
{
    "team_execution_result": internal_result["team_execution_result"],
    "node_trace": [*(state.get("node_trace") or []), "team_execution"],
}
```

Do **not** pass a different-state-schema compiled team graph directly as the parent execution node and rely on implicit channel merging.

- [ ] **Step 1: Write parent adapter tests first**

Prove that the adapter:

- reads exactly parent `team_assignments`;
- does not copy TaskStore rows/events/evidence into parent state;
- invokes the internal team graph;
- returns only the normalized team result plus trace marker.

- [ ] **Step 2: Write acceptance regression tests first**

Add three cases:

```text
no team_execution_result -> existing #149 standard/trust-authorized behavior unchanged
accepted team_execution_result -> executable can remain true
rejected team_execution_result -> final acceptance BLOCKED/non-executable with verifier/execution reasons
```

- [ ] **Step 3: Run and verify RED for rejected result**

Expected current bug: `acceptance_gate_node` ignores team execution result and still accepts.

- [ ] **Step 4: Implement minimal acceptance precedence**

At the start of `acceptance_gate_node`, if `team_execution_result` exists and its `accepted` field is false, return a non-executable BLOCKED acceptance result using deterministic team reasons, e.g.:

```python
AcceptanceResult(
    AcceptanceStatus.BLOCKED,
    False,
    tuple(team_result.get("reasons") or ["team_execution_rejected"]),
)
```

Do not rewrite risk tier or authorization status to encode executor/verifier failure.

- [ ] **Step 5: Compose the internal team graph through the explicit adapter**

Build:

```python
team_graph = build_team_graph(...)
execution_node = build_team_execution_node(team_graph=team_graph)
development_graph = build_development_graph(
    port,
    provider=provider,
    execution_node=execution_node,
)
```

Add end-to-end tests proving:

```text
risk/authorization -> parent adapter -> internal LangGraph team fan-out -> verifier -> team result -> acceptance gate
```

for both accepted and verifier-rejected paths.

- [ ] **Step 6: Run development/team tests**

```powershell
python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q
```

---

### Task 7: Architecture documentation, legacy classification, and final verification

**Files:**
- Modify: `docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md`
- Create: `docs/architecture/LANGGRAPH_TEAM_RUNTIME.md`

**Interfaces:**
- Documents the proven multi-worker path and exact boundary for later real OpenCode dogfood.

- [ ] **Step 1: Document the proven runtime**

Include the exact flow:

```text
DevelopmentWorkflowState
  -> Policy / Trust Authorization
  -> thin team execution-node adapter
       -> internal LangGraph Team Subgraph
            -> Send(worker-a)
            -> Send(worker-b)
            -> reducer/join
            -> verifier
       -> TeamExecutionResult only
  -> Acceptance Gate

Each worker
  -> WorkerAssignment(task_id, workspace_root)
  -> TaskExecutionService
  -> ExecutorRouter
  -> concrete executor
  -> TaskStore events/evidence/validation
```

Explicitly state:

- team orchestration is not an executor kind;
- TaskStore is durable product truth;
- LangGraph team/development state is transient;
- internal team graph and parent graph have an explicit adapter rather than implicit cross-schema state merging;
- legacy `reverse_agent/orchestrator_*` is `RETIRE_LATER` and was not extended.

- [ ] **Step 2: Run full required verification**

```powershell
python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q
python -m pytest tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q
git diff --check
git status --short
git diff d7cf40b13ab0997e747597976f3c0929ab80c8d6 -- pyproject.toml
```

All tests must pass; `git diff --check` must be clean; `pyproject.toml` must have no dependency change.

- [ ] **Step 3: Verify forbidden scopes stayed untouched**

```powershell
git diff --name-only d7cf40b13ab0997e747597976f3c0929ab80c8d6...HEAD
```

Must contain no `frontend/`, `.github/`, `project_state/`, provider/credential config, or PR #146 artifacts.

- [ ] **Step 4: Final task commit and normal push**

After all verification passes, stage only exact Task 2 files and commit:

```text
feat: add LangGraph parallel worker team adapter
```

If Task 1 required an earlier bounded synchronization checkpoint commit, keep it; do not squash/amend solely to force one commit.

Then normal-push only:

```text
owner/issue151-langgraph-worker-team-v1
```

No force push, PR creation, Ready transition, merge, Issue close, main update, release, or deploy.

## Stop Conditions

Stop and return evidence instead of inventing a workaround if any of these becomes true:

- pinned LangGraph 1.0.5 cannot provide native parallel fan-out/join;
- safe parallel TaskStore execution would require one database/store per worker or a second durable truth;
- implementation would require `executor_kind="multi_agent"`;
- the only path requires extending legacy `reverse_agent/orchestrator_*`;
- a model/provider credential/configuration change is required;
- the change expands into frontend/governance/publication work;
- parent/team state integration cannot be expressed through the explicit thin adapter without duplicating durable task state.

## Required Final Report

Return:

1. initial exact task-branch HEAD;
2. final local and remote HEAD;
3. exact changed files;
4. pinned LangGraph 1.0.5 `Send`/subgraph/reducer API evidence;
5. TaskStore concurrency probe result over at least 20 runs and whether a lock was required;
6. team fan-out concurrency proof over at least 20 runs;
7. real two-worker TaskStore + ExecutorRouter deterministic-fixture result;
8. verifier-rejection result;
9. parent execution-node adapter + final acceptance propagation result;
10. focused test commands and exact pass/fail counts;
11. `git diff --check` result;
12. dependency changes: must be NONE;
13. external/model/provider calls: must be 0;
14. privileged GitHub operations: must be NONE.

Terminal verdict must be exactly one of:

```text
LANGGRAPH_PARALLEL_TEAM_ADAPTER_ACCEPTED
```

or

```text
LANGGRAPH_PARALLEL_TEAM_ADAPTER_BLOCKED_WITH_EVIDENCE
```
