# LangGraph Parallel Worker Team Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real reverse-agent multi-worker execution path by reusing pinned `langgraph==1.0.5` for parallel fan-out/join and reusing the existing TaskStore + ExecutorRouter execution plane, with a structured verifier result that controls final workflow acceptance.

**Architecture:** `development_graph.py` keeps the #149 `execution_node` seam. A new LangGraph team subgraph uses native `Send` fan-out, reduces structured worker results, and runs a deterministic/injectable verifier. Actual worker execution goes through one shared programmatic Platform V1 execution service used by both the HTTP Task API and the LangGraph worker adapter. TaskStore remains the only durable product truth; LangGraph state carries only transient assignments/results and references to TaskStore records.

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

Expected starting HEAD after pulling the task-plan commit must match the remote task branch exactly; worktree must be clean; baseline tests must pass before production mutation.

- [ ] **Step 2: Write a deterministic concurrent-write test**

Add a test in `tests/platform_v1/test_task_contracts.py` that creates two independent tasks in the **same** `TaskStore`, starts two Python threads behind a `threading.Barrier(2)`, and has each thread append one event and one evidence record to its own task. Capture exceptions from each thread and assert:

```python
assert exceptions == []
assert len(store.get_task(task_a.id).events) >= 2
assert len(store.get_task(task_a.id).evidence_refs) == 1
assert len(store.get_task(task_b.id).events) >= 2
assert len(store.get_task(task_b.id).evidence_refs) == 1
```

Use finite timeouts so a deadlock fails deterministically.

- [ ] **Step 3: Run the single concurrency test repeatedly**

Run at least:

```powershell
1..20 | ForEach-Object { python -m pytest tests/platform_v1/test_task_contracts.py -q; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
```

If all 20 runs pass, **do not add a lock** merely for style. Record the result in the final report.

If any run exposes SQLite/connection concurrency errors, proceed to Step 4.

- [ ] **Step 4: Only if Step 3 fails, add the smallest store synchronization**

Use a single re-entrant lock owned by `TaskStore` around connection mutations/compound reads that must be atomic. The intended shape is:

```python
from threading import RLock

class TaskStore:
    def __init__(...):
        ...
        self._lock = RLock()

    def add_event(...):
        with self._lock:
            ...
```

Do not introduce per-worker stores or a new DB. Re-run the 20x concurrency test and the full `test_task_contracts.py` file.

- [ ] **Step 5: Checkpoint commit**

Commit only if production synchronization was required. If the baseline was already safe, keep only the concurrency regression test for the later combined task commit.

---

### Task 2: Extract one reusable trusted Task execution service

**Files:**
- Create: `reverse_agent/platform_v1/task_execution.py`
- Modify: `reverse_agent/platform_v1/task_service.py`
- Test: `tests/platform_v1/test_task_service.py`
- Test: `tests/platform_v1/test_task_runtime.py`

**Interfaces:**
- Consumes: `TaskStore`, `ExecutorRouter`, existing executor/event/evidence contracts.
- Produces:

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

Expected failure: `TaskExecutionService` / `task_execution` does not exist.

- [ ] **Step 3: Move, do not duplicate, execution lifecycle logic**

Extract the existing status transitions, `ExecutorRouter.dispatch_execute`, changed-file persistence, validation persistence, executor/validation evidence, and failure classification out of `_TaskHandler.do_POST` / `_run_executor` into `TaskExecutionService.execute`.

Preserve existing statuses exactly:

```text
deterministic_fixture: QUEUED -> PREPARING_WORKSPACE -> RUNNING_FIXTURE -> VALIDATING -> READY_FOR_REVIEW_FIXTURE
other concrete executor: QUEUED -> PREPARING_WORKSPACE -> RUNNING -> VALIDATING -> READY_FOR_REVIEW
```

The service must use the task's existing `executor_kind`; it must never synthesize a team executor kind.

- [ ] **Step 4: Make HTTP execute a thin adapter**

`POST /api/tasks/{id}/execute` should resolve workspace root and call the shared service. HTTP status/response behavior must remain compatible with existing tests.

- [ ] **Step 5: Run Platform V1 regressions**

```powershell
python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_task_contracts.py tests/platform_v1/test_opencode_executor.py -q
```

Expected: PASS with no model/provider call.

---

### Task 3: Add structured worker/team contracts

**Files:**
- Modify: `reverse_agent/architecture/contracts.py`
- Test: create `tests/test_team_graph.py` if no existing team-graph test file exists.

**Interfaces:**
- Produces exact immutable contracts:

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

Each contract must have deterministic `to_dict()`; add `from_mapping()` only where the graph boundary actually needs it.

- [ ] **Step 1: Write validation/serialization tests**

Require non-empty `worker_id`, `role`, `task_id`, `workspace_root`; reject duplicate worker ids at team-graph input validation rather than silently overwriting.

- [ ] **Step 2: Run and verify RED**

Expected: imports/classes missing.

- [ ] **Step 3: Add minimal dataclasses and validation**

Do not add model conversation/messages or duplicate TaskStore task fields such as executor kind/policy/model profile into `WorkerAssignment`; the task id points to the durable task record that already owns those facts.

- [ ] **Step 4: Run contract tests**

Expected: PASS.

---

### Task 4: Build LangGraph-native parallel team subgraph

**Files:**
- Create: `reverse_agent/workflows/team_graph.py`
- Modify: `reverse_agent/workflows/__init__.py` only if a public export is required.
- Test: `tests/test_team_graph.py`

**Interfaces:**
- Consumes: `list[WorkerAssignment]`, a worker callable/adapter, and a verifier callable.
- Produces: compiled LangGraph subgraph whose output includes `team_execution_result`.

Expected builder surface:

```python
def build_team_graph(
    *,
    worker: Callable[[WorkerAssignment], WorkerExecutionResult],
    verifier: Callable[[tuple[WorkerExecutionResult, ...]], TeamExecutionResult] | None = None,
): ...
```

- [ ] **Step 1: Verify pinned LangGraph primitives locally**

Use Python `inspect` against installed 1.0.5 and confirm `langgraph.types.Send` plus reducer semantics exist. Do not upgrade.

- [ ] **Step 2: Write fan-out/join tests first**

Use a `threading.Barrier(2)` fake worker. If LangGraph executes branches sequentially, the test must timeout/fail; if it fans out concurrently, both workers pass the barrier and return results.

Assert:

```python
assert {r["worker_id"] for r in result["team_execution_result"]["worker_results"]} == {"worker-a", "worker-b"}
```

Add tests for duplicate worker id rejection and deterministic result ordering (sort final results by `worker_id` before emitting the team contract).

- [ ] **Step 3: Implement native `Send` fan-out**

Use LangGraph state with a reducer for worker results, conceptually:

```python
class TeamWorkflowState(TypedDict, total=False):
    assignments: list[dict[str, Any]]
    worker_results: Annotated[list[dict[str, Any]], operator.add]
    team_execution_result: dict[str, Any]
```

A routing function returns one `Send("worker", assignment_dict)` per assignment. Do not create Python threads yourself for orchestration.

- [ ] **Step 4: Add verifier/join**

Default verifier accepts only when every worker result reports success. A supplied verifier may reject an otherwise-successful worker result; its structured reasons must appear in `TeamExecutionResult`.

- [ ] **Step 5: Run team graph tests repeatedly**

Run the concurrency test at least 20 times to catch scheduling/reducer nondeterminism.

---

### Task 5: Connect team workers to the real TaskStore + ExecutorRouter path

**Files:**
- Create or modify: `reverse_agent/workflows/team_graph.py` (keep adapter small) or a narrowly justified `reverse_agent/workflows/worker_execution.py`
- Test: `tests/test_team_graph.py`
- Test: relevant Platform V1 tests

**Interfaces:**
- Consumes: `TaskExecutionService` and `WorkerAssignment`.
- Produces: a worker callable that loads/executes the durable TaskStore task and returns only structured references/result facts.

- [ ] **Step 1: Write the real integration test**

Create one `TaskStore`, one `ExecutorRouter`, and two queued `deterministic_fixture` tasks. Build two assignments with distinct task ids and distinct `workspace_root` directories. Invoke the team graph.

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

Also assert no registry/task value contains `multi_agent` as executor kind.

- [ ] **Step 2: Run and verify RED**

Expected: no TaskExecutionService-backed worker adapter yet.

- [ ] **Step 3: Implement the thinnest adapter**

The adapter must call `TaskExecutionService.execute(assignment.task_id, workspace_root=assignment.workspace_root)` and transform `TaskExecutionOutcome` into `WorkerExecutionResult`. Do not replicate TaskStore persistence in the worker node.

- [ ] **Step 4: Add verifier rejection integration**

Run the same two successful fixture tasks with an injected verifier that rejects `worker-b`. Durable worker tasks stay successful, but aggregate `TeamExecutionResult.accepted` is false and reasons identify the verifier rejection. This proves verifier semantics are distinct from executor success.

- [ ] **Step 5: Run focused regressions**

```powershell
python -m pytest tests/test_team_graph.py tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q
```

---

### Task 6: Make execution/team rejection control final development-workflow acceptance

**Files:**
- Modify: `reverse_agent/architecture/contracts.py`
- Modify: `reverse_agent/workflows/nodes/acceptance_gate.py`
- Test: `tests/test_development_graph.py`
- Test: `tests/test_team_graph.py`

**Interfaces:**
- `DevelopmentWorkflowState` gains optional `team_execution_result: dict[str, Any]`.
- Existing invocations with no team result preserve #149 behavior.

- [ ] **Step 1: Write acceptance regression tests first**

Add three cases:

```text
no team result -> existing standard/trust-authorized acceptance unchanged
accepted team result -> executable remains true
rejected team result -> acceptance BLOCKED/non-executable with verifier/execution reasons
```

- [ ] **Step 2: Run and verify RED for rejected result**

Expected current bug: acceptance ignores team execution result and still accepts.

- [ ] **Step 3: Implement minimal precedence in acceptance gate**

At the start of `acceptance_gate_node`, if `team_execution_result` exists and `accepted` is false, return:

```python
AcceptanceResult(
    AcceptanceStatus.BLOCKED,
    False,
    tuple(team_result.get("reasons") or ["team_execution_rejected"]),
)
```

Do not rewrite risk/authorization statuses and do not treat executor rejection as a risk-tier decision.

- [ ] **Step 4: Compose the real compiled team graph through #149 seam**

Add one end-to-end development-graph test that passes `execution_node=build_team_graph(...)` and proves:

```text
risk/authorization -> team subgraph -> verifier -> acceptance gate
```

with both accepted and verifier-rejected paths.

- [ ] **Step 5: Run development/team tests**

```powershell
python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q
```

---

### Task 7: Architecture documentation, legacy classification, and final verification

**Files:**
- Modify: `docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md`
- Create: `docs/architecture/LANGGRAPH_TEAM_RUNTIME.md`

**Interfaces:**
- Documents the now-proven path and exact boundary for Task 3 / real OpenCode dogfood.

- [ ] **Step 1: Document the proven runtime**

Include the exact flow:

```text
DevelopmentWorkflow
  -> Policy / Trust Authorization
  -> LangGraph Team Subgraph
       -> Send(worker-a)
       -> Send(worker-b)
       -> join/reduce
       -> verifier
  -> TeamExecutionResult
  -> Acceptance Gate

Each worker
  -> TaskExecutionService
  -> ExecutorRouter
  -> concrete executor
  -> TaskStore events/evidence/validation
```

Explicitly state: team orchestration is not an executor kind; TaskStore is durable truth; LangGraph state is transient; legacy `reverse_agent/orchestrator_*` is `RETIRE_LATER` and was not extended.

- [ ] **Step 2: Run full required verification**

```powershell
python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q
python -m pytest tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q
git diff --check
git status --short
git diff -- pyproject.toml
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

Then normal-push only:

```text
owner/issue151-langgraph-worker-team-v1
```

No force push, PR creation, Ready transition, merge, Issue close, main update, release, or deploy.

## Required Final Report

Return:

1. initial exact head;
2. final local and remote head;
3. exact changed files;
4. LangGraph 1.0.5 `Send`/subgraph API evidence;
5. TaskStore concurrency probe result (20 runs, and whether a lock was required);
6. team concurrency proof result (20 runs);
7. real two-worker TaskStore + ExecutorRouter deterministic-fixture result;
8. verifier-rejection result;
9. final development-graph acceptance propagation result;
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
