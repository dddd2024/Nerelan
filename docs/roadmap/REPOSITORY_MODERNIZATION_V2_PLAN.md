# Repository Modernization V2 Plan

> **For agentic workers:** execute only a separately authorized phase. Do not interpret this roadmap as code-mutation authority.

**Umbrella:** #148  
**Strategy:** strangler migration + mature-component-first  
**Planning branch:** `owner/repository-modernization-v2-planning`  
**Baseline main:** `dd4cb074ab5b9baacf300706878b29bd745f12c3`

## Goal

Reduce reverse-agent to one current, testable architecture while preserving the already-proven Task API / TaskStore / OpenCode / evidence / frontend vertical slice and retiring historical state, governance, CI and backlog residue.

The modernization is not a greenfield rewrite. Prefer:

```text
REUSE mature component
-> ADAPT through a thin reverse-agent boundary
-> RETIRE duplicated historical implementation
```

rather than rebuilding generic orchestration, provider/auth, repository-host or observability infrastructure.

## Global constraints

- Do not greenfield-rewrite the product core.
- Do not merge or mutate Draft PR #146 until an explicit modernization bridge is selected.
- Do not use old `project_state/current_*` files as global product truth.
- Each implementation phase gets its own bounded branch, tests and review.
- Each replacement must retire/archive the superseded path; compatibility layers are temporary, not permanent.
- No direct push to `main`, force push, rebase, release or deploy as part of modernization implementation.
- Multi-Agent support is not considered operational until exact-head integration evidence exists.
- Model/provider authentication must be separated from executor identity.
- A user should not need to enter the same provider credential separately into reverse-agent and every executor.

---

## Phase 0 — Current Truth Freeze and Inventory

**Objective:** create a reliable map before broad product mutation.

### Deliverables

- `docs/architecture/CURRENT_ARCHITECTURE_BASELINE.md`
- `docs/architecture/HISTORICAL_DEBT_MATRIX.md`
- `docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md`
- this plan
- open Issue classification
- branch/PR classification where historical branches materially affect current assumptions

### Current status

Phase 0 baseline work is substantially established. PR #146 remains frozen as accepted branch evidence rather than current main truth.

---

## Phase 1A — P0 Security Verification: OpenCode Evidence Redaction

**Goal:** prove or refute the suspected tuple-container redaction defect before broader executor refactoring.

**Candidate files:**

- `reverse_agent/platform_v1/opencode_executor.py`
- `tests/platform_v1/test_opencode_executor.py`

### Test-first acceptance

1. Add nested evidence payloads containing secret-like values in dict/list/tuple shapes.
2. Call the same production redaction entry point used before persistence.
3. Assert no original secret survives any container form.
4. If tuple regression fails, minimally fix `_redact_recursively`.
5. Re-run focused executor and relevant Platform V1 tests.

---

## Phase 1B — State and Authority Lifecycle Reset

**Goal:** stop completed historical authority from masquerading as active current state.

Target lifecycle:

```text
DRAFT
-> ACTIVE
-> COMPLETED | SUPERSEDED | EXPIRED | ABORTED
-> ARCHIVE
```

Completed PR landing authority must not remain current merely because a tracked file was never retired.

---

## Phase 1C — Runtime Scratch / Workspace Lifecycle

**Goal:** distinguish tracked repository state, managed runtime state and unrelated pre-existing local dirt.

Preservation is default; do not normalize by destructive `clean`/`reset --hard` behavior.

---

## Phase 2A — One Typed Decision Contract

**Goal:** one schema/compiler path for Decision structure and semantics.

Direction:

```text
Decision source
-> typed/schema validation
-> semantic compilation
-> command plan
-> preflight
-> execution evidence
```

Historical #142/#143/#147 failures become regression fixtures rather than reasons to add more implicit fields and compatibility branches.

---

## Phase 2B — Baseline vs Current-Round Delta

Formalize the difference between pre-existing dirty state and mutations attributable to the current execution round.

---

## Phase 2C — Execution-Surface Compatibility

Prefer short atomic commands and reviewed repository-owned helpers; statically reject command shapes incompatible with the actual local execution surface before activation.

---

## Phase 3 — CI / GitHub-Native Governance Cutover

### CI simplification

Retire permanent legacy/transition dual paths, historical PR-number exceptions and duplicate normal-path validation.

Prefer explicit responsibility boundaries:

```text
CI
Agent Policy
Evidence
Security
```

### GitHub-native protection

Use GitHub Rulesets/required checks/PR requirements/force-push protection for repository-host mechanics where available. Reverse-agent keeps Agent-specific capability/evidence policy, not duplicate GitHub merge authority.

---

## Phase 4 — Runtime / Frontend Contract Consolidation

### 4A Runtime naming and contract cleanup

- TaskStore naming/ownership;
- fixture vs real executor semantics;
- task execution service boundaries;
- workspace and evidence contracts.

### 4B Typed frontend/backend task truth

- fix #145;
- remove real-task dependence on mock-era fallbacks;
- keep Agent Canvas as presentation rather than a second task truth model.

### 4C Backlog/docs migration

Classify stale Issues and docs as `KEEP / REWRITE / SUPERSEDED / ARCHIVE` and retire superseded architecture references.

---

## Multi-Agent track — moved forward, not deferred to the end

The earlier plan placed Multi-Agent at the end of modernization. That is superseded.

The repository already pins `langgraph==1.0.5`, and #149 / PR #150 proved a bounded LangGraph execution seam on the isolated modernization planning branch. Therefore reverse-agent should reuse that mature orchestration spine rather than evaluate or introduce another framework first.

### #149 — completed foundation

Established:

```text
Development Graph
-> optional bounded execution seam
-> acceptance gate
```

with TaskStore remaining durable product truth.

### #151 — completed parallel-team foundation

Build the first real LangGraph-native parallel worker team adapter:

```text
manager/router
-> Send(worker A)
-> Send(worker B)
-> reducer/join
-> verifier
-> TeamExecutionResult
-> parent acceptance
```

Required integration:

- one shared TaskStore;
- existing ExecutorRouter;
- shared trusted TaskExecutionService path;
- at least two real deterministic-fixture tasks;
- genuine parallelism proof;
- structured worker/team results;
- verifier rejection propagates to final acceptance;
- no `executor_kind="multi_agent"`.

This proves the reverse-agent integration boundary, not LangGraph itself.

---

## Product Setup & Connections — active phase after #151

**Purpose:** remove the current mismatch where provider/API configuration, executor selection and executor-owned login state are mixed together.

Canonical design:

`docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md`

### Task 3A / #165 — contract foundation

Task 3A adds distinct process-local Connection, ExecutorDescriptor and Binding
contracts to the trusted Model Control store and loopback API. Public structures
are sanitized, references fail closed, and the legacy ModelProfile path remains
available for compatibility. The operational executor registry currently
contains only `opencode`; Codex and OpenHands are not claimed as operational by
this foundation.

### Task 3B / #170 — secret-free OpenCode consumption proof

Task 3B adds durable `Task.binding_ref`, resolves sanitized Binding data through
the trusted-loopback Task 3A API, and passes only provider/`baseURL` metadata to
OpenCode through transient config plus an explicit child-environment allowlist.
It supports `none` and available executor-owned session authentication.
Model-Control-owned `api_key` connections fail closed before subprocess launch;
credential bridging remains a separate design task.

### Required domain split

```text
Connection
  = provider/service access + authentication

Executor
  = OpenCode / Codex / OpenHands / other concrete runtime

Binding
  = Executor + Connection + Model
```

Authentication methods are Connection properties, for example:

```text
api_key
account_login / oauth
external_cli_session
none
```

API and account login are not different Agents.

### Single-configuration rule

A user configures/authenticates a provider once. Executor adapters reuse that Connection through supported transient env/config/session mechanisms.

Do not silently copy credentials into executor config stores. Do not expose raw secrets to TaskStore, frontend task state, evidence or logs.

### OpenCode target behavior

Task 3B bounded truth:

```text
Binding + none or available executor-owned session
-> secret-free OpenCode adapter

Model Control api_key
-> fail closed before OpenCode launch
```

Implemented secret-free path:

```text
Binding
-> Connection
-> OpenCode adapter
-> supported OpenCode env/config/session integration
-> OpenCode execution
```

If safe inheritance is unsupported for a provider/auth method, surface an explicit unsupported-binding/setup requirement rather than pretending it worked.

### GitHub/repository connection

GitHub is a separate repository-domain connection, not a model provider.

Prefer mature GitHub App/OAuth/`gh`/existing git credential mechanisms. Reverse-agent should expose sanitized connection/repository status and selection without creating a new credential protocol.

### Startup productization

Current `dev-up.ps1` / `dev-down.ps1` provide a **one-command** development lifecycle, not true one-click startup.

Add a thin Windows double-click/launcher entry that reuses existing prerequisite checks, PID ownership, health checks and browser launch. Do not build a large custom desktop runtime first.

### Live probe UX

Current connection testing requires explicit `REVERSE_AGENT_MODEL_CONTROL_LIVE=1`, while standard `dev-up.ps1` does not enable it. Product setup must make live probing explicit and coherent without silently enabling network access.

### Exit criteria

- one provider/API Connection can be configured once and consumed by a supported executor adapter without second manual credential entry;
- API-key and account-login connections are represented distinctly;
- Executor selection is distinct from Provider/Auth selection;
- Binding identifies Executor + Connection + Model;
- GitHub repository connection is separate from model connections;
- true thin launcher exists;
- no raw credentials leak into product task/evidence state;
- old `ModelProfile.executor` coupling has a retirement path.

---

## Real OpenCode Multi-Agent dogfood

Only after #151 plus Product Setup & Connections should the multi-Agent team be given real OpenCode/model work against reverse-agent itself.

Target dogfood:

```text
Owner goal
-> LangGraph manager/team
-> multiple bounded workers
-> concrete OpenCode executor via Binding/Connection
-> TaskStore/evidence
-> verifier
-> final review result
```

Use this dogfood to drive the remaining modernization rather than completing every historical cleanup before exercising the new architecture.

---

## Frozen #146 landing strategy

Do not continue v25/v26-style landing-contract patching under the old authority system.

After the modernization bridge is stable, explicitly choose either:

1. land #146 through the new lifecycle/authority bridge; or
2. transplant already-accepted product commits onto a fresh modernized baseline without rewriting the accepted frontend product logic.

Preserve accepted Stage B evidence.

---

## Current execution order

The fixed near-term sequence is:

```text
#149 LangGraph orchestration seam          DONE
        |
        v
#151 parallel worker team + verifier       DONE
        |
        v
Product Setup & Connections
  Task 3A Connection / Executor / Binding foundation (#165, done)
  Task 3B secret-free OpenCode Binding consumption (#170, implemented)
  provider/API/account status adapters
  GitHub repository connection + coherent live probe UX
  thin one-click launcher
        |
        v
#152 Freshness Automation Foundation
        |
        v
real OpenCode Multi-Agent dogfood
        |
        v
Pack / Capability growth
        |
        v
later data-based routing and broader debt burn-down
```

This sequence intentionally allows mature Multi-Agent infrastructure to participate in later modernization instead of deferring it until all cleanup is complete.

---

## Modernization completion definition

The repository is considered modernized when it has:

```text
one current architecture
one current source-of-truth hierarchy
one typed Decision/policy contract
one active-state lifecycle
one normal CI authority path
one durable Task API/store runtime
one explicit concrete executor abstraction
one Connection / Executor / Binding model
one evidence/verifier boundary
one frontend task truth mapping
one thin product startup path
historical artifacts clearly archived
multi-Agent claims backed by real evidence
```

Every phase should leave the repository simpler than it found it.
