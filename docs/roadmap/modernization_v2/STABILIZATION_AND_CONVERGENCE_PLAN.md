# Repository Modernization V2 — Stabilization and Convergence Plan

```text
STATUS: ACTIVE_SUBPLAN
PARENT: docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md
UMBRELLA: #148
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
CREATED: 2026-08-16
REFRESHED: 2026-08-17
BASELINE: owner/repository-modernization-v2-planning@b6473a74fa74c91394a015a39b3c0d57c6eb5cc2
```

> This document is a subordinate stabilization plan under Repository Modernization V2. It does not replace the parent roadmap, authorize repository mutation, create a new authority path, or become a second product source of truth.

## 1. Why this stabilization phase exists

Repository Modernization V2 now has enough runtime capability that broad feature expansion is no longer the highest-value next move. The current platform already contains:

- durable TaskStore state;
- a real OpenCode executor path;
- Connection / Executor / Binding separation;
- executor-managed external-session authentication without duplicating raw provider secrets;
- persisted sanitized Product Setup metadata;
- LangGraph sequential-team orchestration;
- durable checkpoints, lease/heartbeat/fencing and stale-run reconciliation for the durable team path;
- deterministic validation and evidence persistence;
- real SenseNova execution through the ordinary Binding path.

The immediate risk is **convergence debt**: capability exists, but normal product execution and normal product landing are still less deterministic than they should be. Runtime progress has also repeatedly exposed governance-state coupling and special reconstruction paths.

For this phase, success is measured by repeatability:

```text
one normal product change
-> one clean product branch / PR
-> deterministic product CI
-> independent verification
-> clean landing
-> restart-safe unattended execution
```

without inventing another recovery subsystem or another governance workaround for each change.

## 2. Current evidence as of 2026-08-17

The previous stabilization draft was based on `3b650e6239336c796593cecd3c137cf839cf1e95`. That baseline is now stale and MUST NOT be treated as the current integration head.

Canonical planning is now:

```text
owner/repository-modernization-v2-planning
@ b6473a74fa74c91394a015a39b3c0d57c6eb5cc2
```

Material progress since the old draft baseline:

1. **#224** replaced terminal-UI auth scraping as normal authority with `executor_managed` opaque external-session semantics. Reverse-agent owns exact provider/base/model routing; the executor owns opaque credential material.
2. **#226** installed/reloaded the canonical sanitized SenseNova Connection/Binding Product Setup without persisting raw credentials.
3. **#227** removed a stale OpenCode constructor gate so `executor_managed` and `available` external/account sessions reach the real executor path while missing/unknown states remain fail-closed.
4. **#228** proved the real product route `Task API -> Binding -> OpenCode -> SenseNova` and exact marker mutation, but exposed a lifecycle/harness timeout problem before terminal TaskStore completion.
5. **#229** completed a fresh one-shot single-task lifecycle with one create, one execute and one product-path OpenCode launch, reaching persisted `READY_FOR_REVIEW` with `git_diff_check=0` and exact expected changed-file bytes.

Therefore these questions are no longer open:

- whether the installed OpenCode/SenseNova external session can be used through the product Binding path;
- whether the single-agent product path can reach deterministic terminal success;
- whether raw credential duplication is required for that path.

The main runtime gap exposed by this proof is now ordinary **single-task durability across request/process interruption**. That work is tracked as #230 and must reuse existing durable primitives.

## 3. Stabilization scope freeze

Until the exit criteria in this document are met, do not start broad implementation of:

- #152 Freshness Automation Foundation;
- #177 natural-language goal intake / Spec Kit-first decomposition;
- broad Pack / Capability growth;
- adaptive or learned model routing;
- a second real executor solely for breadth;
- a second orchestration framework;
- swarm, voting, debate or other multi-Agent topology expansion beyond the current bounded team path.

Planning and research may continue, but those tracks must not displace stabilization work or create a parallel runtime.

The preferred real credential path for current dogfood is the already-proven executor-managed OpenCode external session. API-key credential relay remains a supported secondary path and the independent #207 Windows socket/test-lifecycle debt must not be conflated with the external-session path.

## 4. Workstream A — CI and governance test isolation

### Problem

Product changes have repeatedly encountered failures caused by historical governance state or tests that accidentally encode a previous repository snapshot as a permanent invariant. Examples include using current tracked `project_state/decision_packet.md` as an implicit global fixture or treating a historical exact dependency/authority snapshot as current product truth.

### Required separation

Converge toward three explicit classes:

```text
product invariants
  = runtime/security/behavior that must remain true across rounds

governance contract tests
  = current typed authority/policy semantics

historical governance fixtures
  = explicit regression examples for earlier Decisions, merge intents and migrations
```

Directory names may differ, but ownership must be explicit.

Rules:

1. Current mutable `project_state/decision_packet.md` must not be an implicit fixture for unrelated product tests.
2. Historical Decisions/merge intents/transition states should be explicit immutable fixtures when regression coverage is required.
3. Dependency/version assertions are global blockers only when they represent an intentional current compatibility contract.
4. Product CI should fail for product invariant violations, not incidental historical authority drift.
5. Governance-contract CI should validate current typed contracts against explicit inputs.
6. Historical fixtures remain regression evidence, not current product authority.
7. Fail-closed security properties must not be weakened merely to make CI green.

Acceptance: a normal product-only change can run required product and current-governance tests without depending on round-specific tracked authority state.

## 5. Workstream B — make ordinary single execution durable

The functional single-agent E2E is now proven by #229. The next runtime task is #230.

Current code has a material split:

```text
sequential_team /execute
-> DurableExecutionService
-> durable run + lease/fencing/reconciliation

single /execute
-> TaskExecutionService.execute()
-> synchronous HTTP handler execution
```

The target is not a second implementation. The target is to reuse the durable run, ownership, fencing, reconciliation, worktree identity, validation and external-operation concepts for normal single execution.

Required properties:

- server-owned durable run identity before external dispatch;
- duplicate/concurrent execute cannot launch a second executor;
- HTTP request lifetime is not execution authority;
- accepted execution mutations are owner+epoch fenced;
- startup reconciliation remains provider-free and never launches a model;
- recovery receives a strictly newer fencing epoch;
- `/execute` does not silently become `/resume`;
- ambiguous in-flight external operations fail closed rather than being silently reissued;
- accepted executor result can continue deterministic validation without replaying the executor;
- sequential-team durable behavior does not regress.

Implementation and provider-free proof are tracked in #230. A later real interruption smoke must use a separate authority after product-only landing.

## 6. Workstream C — long-running unattended sequential-team dogfood

After the ordinary single path is no longer request/process-fragile, perform the originally intended bounded durable team dogfood instead of adding another platform layer.

Required stack:

```text
persisted executor-managed OpenCode auth
+ persisted Connection / Binding metadata
+ real OpenCode executor
+ sequential_team orchestration
+ durable TaskStore state
+ LangGraph checkpointing
+ lease / heartbeat / fencing
+ deterministic verifier
```

Required scenario:

```text
start one bounded real task
-> Planner accepted
-> Coder begins/completes
-> persist checkpoint + heartbeat
-> intentionally terminate trusted execution process/host
-> allow old lease to become stale
-> restart trusted host/process
-> reconcile stale ownership without model execution at startup
-> acquire a strictly newer fenced epoch
-> resume same task/run/worktree
-> do not replay accepted roles
-> Reviewer continues from verified persisted product state
-> deterministic verification completes
```

Required evidence includes same task/run/worktree identity, monotonic fencing, at least two pre-kill heartbeat observations, no replay of accepted roles, persisted worktree truth validation, no raw credential in product/evidence state and deterministic final acceptance.

A failed dogfood is valid evidence. Do not hide incompatibility behind fixture-only success.

## 7. Workstream D — product history versus execution-authority history

Formalize this long-term invariant:

```text
Product Git history != transient execution-authority history
```

Product Git should retain product/runtime code, stable schemas/contracts, deterministic tests/fixtures, active architecture/roadmap docs and genuinely durable policy.

Runtime/artifact state should increasingly retain per-run Decisions that are not durable product design, execution receipts, transient Gate outputs, current-round command plans, heartbeat/lease/checkpoint evidence and other round-specific execution material.

The existing product-only reconstruction pattern has proved the value of separation, but repeated manual reconstruction must not become the permanent normal workflow.

Prefer a clean-by-construction product-history boundary. Do not create another tracked artifact family merely to move transient artifacts around.

## 8. Workstream E — planning branch cutover

`owner/repository-modernization-v2-planning` is the effective product integration trunk today. It must not remain a permanent shadow `main` without an explicit lifecycle.

Authorize promotion/cutover only after:

1. active product/runtime tests pass on the integration baseline;
2. CI/governance test isolation is established;
3. at least one ordinary product change lands without a special authority-history reconstruction workaround;
4. the required interruption/recovery dogfood passes or reaches a bounded, well-understood blocker without evidence corruption;
5. current source-of-truth docs point to Modernization V2 rather than superseded architecture;
6. frozen/historical PRs and branches are clearly classified;
7. exact promotion and rollback/verification steps are documented before mutation.

After cutover, there must be exactly one declared current product integration truth.

## 9. Workstream F — collect capability data; do not route automatically yet

Begin collecting sanitized real execution facts where available:

```text
task_family
role
executor
provider
model
model_version
attempt
duration
token_usage
cost
failure_category
verifier_result
rework_count
final_acceptance
```

Rules:

- raw prompts, credentials and sensitive repository content are not required for capability statistics;
- capability claims should eventually derive from observed task-family outcomes;
- do not introduce LiteLLM or another router solely to collect data if the existing execution path can record it;
- do not implement learned/adaptive routing until a meaningful real sample and deterministic evaluation target exist.

Future routing may combine capability fit, availability, quota/rate-limit headroom, latency, cost/budget, user quality/economy/speed preference and observed failure history, but that remains outside this stabilization phase.

## 10. Mature-component ownership invariants

| Capability | Primary owner / direction |
|---|---|
| orchestration | LangGraph |
| durable product task truth | reverse-agent TaskStore |
| first real coding executor | OpenCode |
| presentation/workbench | Agent Canvas where retained |
| repository/PR/CI truth | GitHub |
| model gateway/accounting candidate | LiteLLM only when justified later |
| dependency/upstream automation | Renovate under #152 when resumed |
| provider authentication | provider/executor auth stores; reverse-agent keeps sanitized references/status only |
| policy/evidence/verification | reverse-agent |

Additional invariants:

- LangGraph state must not become a second TaskStore.
- `multi_agent` must not become a fake executor kind.
- Do not duplicate an executor's persisted provider secret inside reverse-agent.
- A compatibility adapter must have a retirement condition.
- Single-task durability must reuse the existing durable-runtime ownership model instead of introducing a second run store.

## 11. Governance failure budget

After stabilization corrections are established, allow at most **one bounded correction** for a newly discovered recurring governance/CI architecture defect on the ordinary product path.

If the same blocker class recurs after that correction, default to:

```text
simplify / remove / isolate the offending governance mechanism
```

not:

```text
add another Decision field
+ another Gate artifact
+ another sidecar path
+ another permanent compatibility branch
```

Security-critical fail-closed behavior remains mandatory. The goal is fewer duplicated authority mechanics, not weaker verification.

## 12. Stabilization exit criteria

This subplan is complete when all are demonstrated:

1. executor-managed OpenCode authentication is usable after restart without duplicating raw provider secret in reverse-agent — **functional route already proven by #228/#229; retain as regression invariant**;
2. product/governance/historical test responsibilities are explicitly isolated and normal product CI no longer depends on incidental round-specific authority state;
3. ordinary single-task execution is durable across request/process interruption with explicit fenced recovery semantics and no silent duplicate external execution;
4. one real long-running `sequential_team` task survives an intentional process/host interruption and resumes the same durable run/worktree safely;
5. completed accepted phases/roles are not replayed and stale workers cannot commit new truth;
6. final acceptance comes from deterministic verification;
7. raw credentials do not enter product task/evidence state;
8. product-history / execution-authority-history separation has an implementation direction that does not rely on permanent manual reconstruction;
9. planning-branch cutover criteria are satisfied and a bounded promotion task can be authorized;
10. real execution telemetry is being recorded for future capability analysis;
11. no new orchestration framework, broad Pack layer, adaptive router or second executor has been introduced merely to expand scope during stabilization.

## 13. Resume after stabilization

After exit, return to the parent Modernization V2 roadmap and re-evaluate sequencing from current evidence. Candidate tracks remain:

```text
#152 Freshness Automation
#177 Goal -> Spec -> Plan -> Tasks
real end-to-end dogfood expansion
Pack / Capability growth
later data-backed model/executor routing
broader historical debt retirement
```

Do not assume the old order is still correct merely because it was once documented.

## 14. Non-goals

This subplan does not authorize:

- product code changes;
- branch promotion or merge;
- security-gate removal without replacement evidence;
- automatic model routing;
- new provider credentials or secret migration;
- a second orchestration framework;
- broad Pack implementation;
- autonomous merge/release;
- destructive cleanup of historical branches, worktrees or evidence.

Each implementation workstream still requires applicable bounded authority and exact-head verification.