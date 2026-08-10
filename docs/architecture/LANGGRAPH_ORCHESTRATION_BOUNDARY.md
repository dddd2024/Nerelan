# LangGraph Orchestration Boundary

Authoritative boundary for the Modernization V2 consolidation task (#149).
Introduced against baseline commit
`d8ad86e35910ec289032579655d49a95176605cb` on branch
`owner/issue149-langgraph-spine-v1` with pinned `langgraph==1.0.5`.

## A. Reverse-agent owns (four platform-domain boundaries)

1. **Task** -- task identity, bounded request, task lifecycle reference.
2. **Workspace** -- linked worktree identity, isolation scope, mutation
   boundary.
3. **Policy** -- server-owned capability / risk / approval input. Agent
   and model text must never expand authority beyond what the policy
   surface exposes.
4. **Evidence / Artifact** -- structured executor and verifier output.
   Free-form agent dialogue is not the handoff truth.

## B. LangGraph owns (workflow mechanics only)

- graph routing (direct edges and conditional edges);
- graph execution / node dispatch;
- checkpoint mechanics (`InMemorySaver`, `get_state`, resume/replay);
- future worker / team orchestration mechanics, when that work is
  explicitly scoped.

LangGraph does not own policy, tasks, workspace, or evidence.

## C. TaskStore

TaskStore is the **durable product truth**. It is the canonical store of
task rows, events, and evidence emitted by executor runs.

## D. LangGraph state

`DevelopmentWorkflowState` is **workflow state only**. It is a transient,
in-process shape used to thread a single workflow invocation through
risk classification, authorization, an optional execution seam, and the
acceptance gate. It is not persisted to a second database and never
duplicates the TaskStore row / event / evidence / changed_files shape.

If a later task adopts a durable LangGraph checkpointer, that checkpoint may
persist workflow mechanics only. It must not become a second canonical store
for reverse-agent task, event, evidence, or changed-file truth.

## E. Module classification matrix

| Module                          | Class             | Reason                                                                                      | Future multi-Agent seam                                                                                          |
|---------------------------------|-------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `workflows/development_graph.py`| **ADAPT**         | Hosts the single bounded `execution_node` seam (Phase F). Kept minimal; no scheduler/pool. | Multi-agent worker graph plugs in via the existing `execution_node` kwarg.                                        |
| `architecture/contracts.py`     | **KEEP**          | State schema already carries `node_trace`; no new durable key required for the seam.        | New agent/worker contracts (e.g. `WorkerHandoff`) added later without touching TaskStore schema.                  |
| `architecture/policy_provider.py` | **KEEP**        | Remains the single authoritative source of `RiskPolicySnapshot` / `WorkflowIdentity`.        | Multi-agent workers still receive a provider-issued snapshot; no provider duplication.                            |
| `architecture/risk.py`          | **KEEP**          | Risk tiers / routes / authorization statuses unchanged.                                     | New agent-tier tags (e.g. `TEAM_ROUTED`) added later if required.                                                 |
| `platform_v1/task_service.py`   | **KEEP**          | HTTP surface over TaskStore. LangGraph has no HTTP surface role.                            | May be the ingress that binds a worker's durable task row; behavior unchanged in #149.                            |
| `platform_v1/run_store.py`      | **KEEP**          | Durable SQLite TaskStore (task / event / evidence rows). LangGraph must not duplicate it.   | Workflow checkpoints remain separate from canonical TaskStore truth.                                             |
| `platform_v1/task_runtime.py`   | **KEEP**          | ExecutorRouter + LocalValidationRunner. LangGraph is not an executor.                      | Multi-agent workers invoke ExecutorRouter per task row; runtime ownership stays here.                            |
| `platform_v1/opencode_executor.py` | **KEEP**        | Deterministic executor semantics unchanged; no LangGraph substitution.                     | OpenCode remains an executor kind; multi-agent dispatch stays in LangGraph orchestration, and each worker selects an executor through `ExecutorRouter`. |
| `workflows/nodes/*.py`          | **KEEP**          | Node callables already return `DevelopmentWorkflowState` deltas; no shape change needed.    | Multi-agent worker node will be another `state -> dict` callable, structurally identical to existing nodes.       |
| `workflows/__init__.py`         | **KEEP**          | Public export of `build_development_graph`. New seam is a kwarg, no new export required.    | If a worker graph type is later exposed, it can be added here.                                                    |

### Retired later (not in this task)

- Historical non-LangGraph orchestrator shells (e.g. `tests/test_orchestrator_*`,
  `tests/test_project_*`) are not modified and not a target of #149. They are
  `RETIRE_LATER` candidates for a later cleanup task, kept untouched to preserve
  failure evidence for independent audit.

### Out of scope

- AutoGen / OpenAI Agents SDK / CrewAI / any new scheduler, workflow engine,
  agent framework, or worker pool.
- Frontend, `.github/`, `project_state/`, governance, publication, merge,
  release, deploy, credentials, model configuration.

## F. Verified insertion seam for the next multi-Agent task

The next multi-Agent task plugs into `build_development_graph(...,
execution_node=<worker_graph>)`. The pinned LangGraph 1.0.5 API accepts:

- a plain `Callable[[DevelopmentWorkflowState], dict]`;
- a `functools.partial`-bound callable;
- a compiled LangGraph subgraph (`StateGraph(...).compile(...)`).

Any of these may be passed as `execution_node`. When supplied, the graph routes

```
classify_risk
  -> request_trust_authorization   (only when risk requires trust authorization)
       -> execution_seam           (only when authorization status is AUTHORIZED)
            -> acceptance_gate
```

and on the standard (non-trust) path

```
classify_risk -> execution_seam -> acceptance_gate
```

A `BLOCKED` authorization result is guaranteed never to reach the seam.
Default `build_development_graph` behavior (no `execution_node`) remains
observably compatible with the covered pre-#149 Phase E behavior and does not
traverse the seam.

## G. Multi-worker team orchestration boundary (proven in #151)

The next multi-worker task (#151) plugs a compiled LangGraph team subgraph
into the existing `execution_node` seam via a **thin parent adapter**. The
proven flow is:

```text
DevelopmentWorkflowState
  -> Policy / Trust Authorization
  -> build_team_execution_node(team_graph=...)
       -> internal LangGraph Team Subgraph (own state schema)
            -> Send(worker-a)
            -> Send(worker-b)
            -> reducer (worker_results join)
            -> verifier
       -> TeamExecutionResult only
  -> Acceptance Gate

Each worker
  -> WorkerAssignment(task_id, workspace_root)
  -> TaskExecutionService.execute()
  -> ExecutorRouter
  -> concrete executor (deterministic_fixture / opencode)
  -> TaskStore events / evidence / validation
```

Explicit boundary statements:

- **Team orchestration is not an executor kind.** No `executor_kind =
  "multi_agent"` is ever synthesized; each worker selects its concrete
  executor through the existing `ExecutorRouter` registry.
- **TaskStore is durable product truth.** LangGraph team/development state
  is transient. The internal team graph carries only `assignments`,
  `worker_results`, and `team_execution_result`; the parent graph carries
  only `team_assignments` and `team_execution_result`. No TaskStore
  row / event / evidence / changed_files is duplicated into either.
- **Internal team graph and parent graph have different state schemas.**
  `build_team_execution_node` is an explicit adapter, not a reliance on
  implicit cross-schema channel merging.
- **Native LangGraph `Send` is the fan-out primitive.** No custom
  thread pool, scheduler, or message bus is introduced. Parallelism is
  proven with a `threading.Barrier(2)` instrument in tests (barrier is
  a test instrument only, not a production scheduler).
- **TaskStore concurrency is protected by `threading.RLock`.** The shared
  TaskStore holds a single re-entrant lock as its shared-connection
  serialization invariant. An earlier implementation reported a
  `sqlite3.InterfaceError`, but the Owner re-audit has no persisted,
  independently verifiable evidence for that historical failure or the
  reported 20/20 follow-up. Current repeated regressions support the invariant
  and verify that the lock does not span an external executor callback.
- **Acceptance gate reads `team_execution_result`.** When present and
  `accepted == False`, the gate returns `AcceptanceStatus.BLOCKED`,
  `executable = False`, using the team reasons. Without `team_execution_result`
  the gate behaves exactly as before #151.
- **Legacy `reverse_agent/orchestrator_*` is `RETIRE_LATER`** and was
  not extended.

See also :doc:`LANGGRAPH_TEAM_RUNTIME` for the proven runtime contracts.
