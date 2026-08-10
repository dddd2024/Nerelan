# LangGraph Team Runtime

Proven multi-worker runtime for Repository Modernization V2 Task 2 (#151).
Established on top of the #149 execution-seam boundary using pinned
`langgraph==1.0.5`.

## 1. Runtime contracts

```text
DevelopmentWorkflowState
  -> Policy / Trust Authorization
  -> build_team_execution_node(team_graph=...)      (thin parent adapter)
       -> internal LangGraph Team Subgraph
            -> dispatch_workers (no-op, validates assignments)
            -> Send("worker", {assignment: ...})     (parallel fan-out)
            -> Send("worker", {assignment: ...})
            -> worker node (reducer appends to worker_results)
            -> verifier node (aggregates into team_execution_result)
       -> parent receives only {team_execution_result, node_trace}
  -> Acceptance Gate
```

## 2. State schemas

### Parent: `DevelopmentWorkflowState` (TypedDict)

New transient channels added by #151:

- `team_assignments: list[dict[str, Any]]` — assignments fed to the adapter;
- `team_execution_result: dict[str, Any]` — normalized team aggregate result.

Durable TaskStore fields (task rows, events, evidence, changed_files) are
never duplicated into parent state.

### Internal: `TeamWorkflowState` (TypedDict)

- `assignments: list[dict[str, Any]]`
- `assignment: dict[str, Any]` (current Send-branch payload)
- `worker_results: Annotated[list[dict], operator.add]` (LangGraph reducer)
- `team_execution_result: dict[str, Any]`

`TeamWorkflowState` is distinct from `DevelopmentWorkflowState`.
`build_team_execution_node` is the explicit adapter between them.

## 3. Structured contracts (`architecture/contracts.py`)

- `WorkerAssignment(worker_id, role, task_id, workspace_root)` — references
  the durable task row; does NOT duplicate executor_kind / model_profile_ref /
  permission_profile / policy_ref.
- `WorkerExecutionResult(worker_id, task_id, execution_id, success,
  validation_exit_code, evidence_ids, failure_classification,
  failure_detail, reasons)` — per-worker structured result.
- `TeamExecutionResult(accepted, worker_results, reasons)` — aggregate
  acceptance. `worker_results` sorted by `worker_id` so parallel branch
  completion order is not a product contract.

All three have deterministic `to_dict()` / `from_mapping()` for graph
boundary serialization.

## 4. TaskExecutionService

`TaskExecutionService(store, router).execute(task_id, workspace_root=...)` is
the single programmatic execution path used by both:

- HTTP `POST /api/tasks/{id}/execute`;
- LangGraph worker adapter (`build_worker_adapter(service=...)`).

It owns the full lifecycle: `QUEUED -> PREPARING_WORKSPACE -> RUNNING[_FIXTURE]
-> VALIDATING -> READY_FOR_REVIEW[_FIXTURE]`, executor dispatch via
`ExecutorRouter`, changed-file / validation / evidence persistence, and
failure classification.

OpenCode executor kwargs are built in exactly one helper
(`task_execution._build_executor_kwargs`) on the shared execution path. The
HTTP adapter contains no separate executor lifecycle or kwargs implementation.

## 5. TaskStore concurrency

The shared `TaskStore` instance now owns a single `threading.RLock`. All
public methods that touch the SQLite connection are wrapped with
`with self._lock:`. RLock is used because public methods call other public
methods internally (e.g. `transition_to` calls `get_task`).

The earlier implementation reported a shared-connection
`sqlite3.InterfaceError`, but the Owner re-audit does not possess persisted,
independently verifiable evidence for that historical failure or its reported
20/20 follow-up. The single `RLock` is retained as the shared-connection
serialization invariant. Current support comes from the repeated TaskStore
regression evidence produced by this rework, including proof that the lock is
not held across an external executor callback.

## 6. Fan-out / join mechanics

- `add_conditional_edges("dispatch_workers", <send_factory>, ["worker"])`
  returns one `Send("worker", {"assignment": ...})` per validated assignment.
- Each Send branch runs the `worker` node with the assignment merged into
  state; the worker node appends exactly one entry to the
  `worker_results` reducer.
- After all Send branches complete, the edge `worker -> verifier` fires.
- The verifier sorts results by `worker_id`, invokes the injected (or
  default) verifier callable, and writes `team_execution_result`.

## 7. Verifier semantics

The default verifier accepts the team iff every worker reports success.
An injected verifier may reject even when all workers succeeded; this is
intentional — verifier rejection is a distinct semantic layer from executor
success. Durable task rows remain successful; the aggregate
`TeamExecutionResult.accepted` is false with deterministic reasons.

## 8. Acceptance gate propagation

`acceptance_gate_node` now checks `team_execution_result` before the
existing risk/authorization logic:

- `team_execution_result` absent → existing #149 behavior unchanged;
- `accepted == True` → existing path continues;
- `accepted == False` → `AcceptanceStatus.BLOCKED`, `executable = False`,
  reasons from `team_execution_result.reasons` (or
  `("team_execution_rejected",)` if empty).
- present but malformed result → `AcceptanceStatus.BLOCKED`,
  `executable = False`, reason `team_execution_result_invalid`.

Risk tier and authorization status are never repurposed to encode
execution/verifier failure.

## 9. End-to-end parent-graph composition

```python
team_graph = build_team_graph(worker=build_worker_adapter(service=service))
execution_node = build_team_execution_node(team_graph=team_graph)
development_graph = build_development_graph(
    port, provider=provider, execution_node=execution_node,
)
```

Proven paths:

- Standard (R1) with team execution: `classify_risk -> team_execution -> acceptance_gate`
- Trust-authorized (R2) with team execution: `classify_risk -> request_trust_authorization -> team_execution -> acceptance_gate`
- Blocked authorization: `team_execution` skipped, acceptance BLOCKED.
- Verifier rejection: `team_execution` runs, acceptance BLOCKED.

## 10. Legacy boundary

`reverse_agent/orchestrator_api.py`, `orchestrator_context.py`, and
`orchestrator_console_schema.py` are `RETIRE_LATER` and were not modified
by #151. No `multi_agent` executor kind was introduced. No
`frontend/**`, `.github/**`, `project_state/**`, or provider/credential
configuration was changed.
