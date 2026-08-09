# LangGraph Spine Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate reverse-agent orchestration on the already-pinned LangGraph runtime and expose one bounded insertion seam for later worker/team execution without creating a second task, policy, workspace, or evidence truth.

**Architecture:** Keep `TaskStore` and Platform V1 as durable product truth. Keep `AuthorizedRiskPolicyProvider` as the current policy source. Keep LangGraph as workflow mechanics only. The first change establishes and tests a single execution-subgraph/node seam between authorization/risk routing and acceptance; no multi-Agent worker is implemented in this task.

**Tech Stack:** Python 3.13+, `langgraph==1.0.5`, pytest 8.x, existing reverse-agent contracts.

## Global Constraints

- Work only on `owner/issue149-langgraph-spine-v1` in a fresh isolated worktree; do not modify the existing `F:\reverse-agent` worktree containing the preserved v24 candidate.
- Do not add or upgrade orchestrator dependencies.
- Do not modify PR #146 or its branch.
- Do not change Task API, TaskStore persistence semantics, OpenCode execution semantics, model/provider configuration, credentials, frontend, publication, merge/release/deploy behavior.
- Prefer reuse of existing `reverse_agent.architecture.contracts` and `reverse_agent.workflows` over creating new namespaces.
- If the pinned LangGraph API cannot support a clean bounded node/subgraph seam without duplicating state, stop and report `LANGGRAPH_SPINE_REJECTED_WITH_EVIDENCE` rather than adding another framework.

---

### Task 1: Baseline and pinned-LangGraph capability inspection

**Files:**
- Read: `pyproject.toml`
- Read: `reverse_agent/workflows/development_graph.py`
- Read: `reverse_agent/architecture/contracts.py`
- Read: `reverse_agent/architecture/policy_provider.py`
- Read: `tests/test_development_graph.py`

**Interfaces:**
- Consumes: existing `build_development_graph`, `DevelopmentWorkflowState`, `AuthorizedRiskPolicyProvider`, `TrustAuthorizationPort`.
- Produces: a recorded decision whether the pinned LangGraph API can accept a callable/runnable/subgraph node at a bounded execution seam.

- [ ] **Step 1:** From the isolated worktree, record `git rev-parse HEAD`, `git status --short`, and `python -c "import langgraph; print(langgraph.__file__)"`.
- [ ] **Step 2:** Run `python -m pytest tests/test_development_graph.py -q` and require the existing suite to pass before edits.
- [ ] **Step 3:** Inspect the installed `langgraph.graph.StateGraph.add_node` signature and the concrete compiled-graph/runnable types using Python `inspect`; do not use online API assumptions.
- [ ] **Step 4:** Record whether a compiled graph/runnable/callable can be inserted as a node while preserving one `DevelopmentWorkflowState`. If not, stop without product mutation.

### Task 2: Write the execution-seam regression first

**Files:**
- Modify: `tests/test_development_graph.py`

**Interfaces:**
- Consumes: existing graph builder.
- Produces: regression coverage proving the graph can optionally pass through exactly one bounded execution seam while default behavior remains unchanged.

- [ ] **Step 1:** Add a deterministic test node/subgraph that appends exactly one marker such as `"execution_seam"` to `node_trace` and changes no policy/task/evidence state.
- [ ] **Step 2:** Add a test proving the default `build_development_graph(...)` path remains byte-for-byte equivalent for the existing acceptance/risk assertions and does not include `execution_seam`.
- [ ] **Step 3:** Add a test proving the opt-in seam runs after risk/authorization and before `acceptance_gate`.
- [ ] **Step 4:** Add a test proving an R2/R3 blocked authorization cannot reach the seam.
- [ ] **Step 5:** Run only the new tests and confirm they fail before implementation for the expected missing seam support.

### Task 3: Implement the smallest LangGraph-native seam

**Files:**
- Modify: `reverse_agent/workflows/development_graph.py`
- Modify: `reverse_agent/workflows/__init__.py` only if the existing public export must expose the new seam type.
- Modify: `reverse_agent/architecture/contracts.py` only if the pinned LangGraph API requires one explicit state key for the seam; otherwise leave it untouched.

**Interfaces:**
- Consumes: pinned LangGraph node/subgraph interface discovered in Task 1.
- Produces: one optional `execution_node` or semantically equivalent parameter on `build_development_graph`; default is no execution node and preserves current behavior.

- [ ] **Step 1:** Add the optional seam using the smallest API shape supported by the pinned LangGraph runtime. Do not introduce a scheduler, worker pool, new persistence layer, or duplicate state model.
- [ ] **Step 2:** Route accepted/authorized flows through the seam only when supplied; blocked flows remain blocked before the seam.
- [ ] **Step 3:** Keep `InMemorySaver` behavior and existing provider binding unchanged.
- [ ] **Step 4:** Run the focused seam tests and require PASS.
- [ ] **Step 5:** Run the full `tests/test_development_graph.py` suite and require PASS.

### Task 4: Prove Platform V1 remains the durable product truth

**Files:**
- Test/read only unless a focused regression is required: `reverse_agent/platform_v1/task_service.py`
- Test/read only unless a focused regression is required: `reverse_agent/platform_v1/run_store.py`
- Test/read only unless a focused regression is required: `reverse_agent/platform_v1/task_runtime.py`
- Test/read only unless a focused regression is required: existing matching tests under `tests/platform_v1/`

**Interfaces:**
- Consumes: existing TaskService/TaskStore/ExecutorRouter.
- Produces: evidence that LangGraph seam addition does not replace or duplicate durable task/event/evidence truth.

- [ ] **Step 1:** Identify the exact existing Platform V1 tests covering task create/readback, persisted events/evidence, and ExecutorRouter dispatch.
- [ ] **Step 2:** Run those existing tests unchanged.
- [ ] **Step 3:** If any production mutation outside `reverse_agent/workflows/**` is required merely to make the seam work, stop and report why before making that mutation.

### Task 5: Document the mature-component boundary

**Files:**
- Create: `docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md`

**Interfaces:**
- Consumes: verified implementation and test evidence.
- Produces: authoritative modernization guidance for the next multi-Agent task.

- [ ] **Step 1:** Document exactly four reverse-agent-owned contracts: Task, Workspace, Policy, Evidence/Artifact.
- [ ] **Step 2:** Document LangGraph-owned responsibilities: graph routing, conditional edges, checkpoint mechanics, future worker/team orchestration mechanics.
- [ ] **Step 3:** Include a `KEEP / ADAPT / RETIRE_LATER / OUT_OF_SCOPE` matrix for current orchestration-related modules.
- [ ] **Step 4:** Name the exact verified insertion seam for the next multi-Agent task.
- [ ] **Step 5:** State explicitly that TaskStore remains durable product truth and LangGraph state is workflow state, not a second product database.

### Task 6: Final verification and publication boundary

**Files:**
- All changed files from Tasks 2–5 only.

**Interfaces:**
- Produces: exact implementation commit and local evidence for Owner review.

- [ ] **Step 1:** Run `python -m pytest tests/test_development_graph.py -q`.
- [ ] **Step 2:** Run the focused existing Platform V1 tests identified in Task 4.
- [ ] **Step 3:** Run `git diff --check`.
- [ ] **Step 4:** Verify `pyproject.toml` has no dependency change.
- [ ] **Step 5:** Verify no files under `frontend/`, `.github/`, `project_state/`, or PR #146 branch were changed.
- [ ] **Step 6:** Commit with message `refactor: establish LangGraph orchestration seam` and normal-push only `owner/issue149-langgraph-spine-v1`.
- [ ] **Step 7:** Do not create/update/Ready/merge a PR. Return the exact pushed SHA, changed-file list, test results, module classification matrix, and exactly one terminal recommendation: `LANGGRAPH_SPINE_ACCEPTED_FOR_MULTI_AGENT_ADAPTER` or `LANGGRAPH_SPINE_REJECTED_WITH_EVIDENCE`.
