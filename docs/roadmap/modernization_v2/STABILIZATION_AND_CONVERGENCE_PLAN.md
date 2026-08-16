# Repository Modernization V2 — Stabilization and Convergence Plan

```text
STATUS: ACTIVE_SUBPLAN
PARENT: docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md
UMBRELLA: #148
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
CREATED: 2026-08-16
BASELINE: owner/repository-modernization-v2-planning@3b650e6239336c796593cecd3c137cf839cf1e95
```

> This document is a subordinate stabilization plan under Repository Modernization V2. It does not replace the parent roadmap, authorize repository mutation, create a new authority path, or become a second product source of truth.

## 1. Why this stabilization phase exists

The modernization has already produced substantial runtime capability: durable TaskStore state, real OpenCode execution, Connection / Executor / Binding separation, LangGraph orchestration, sequential multi-Agent roles, checkpointed durable execution, lease/heartbeat/fencing, process-crash recovery, persisted Product Setup metadata, deterministic verification, and persisted OpenCode provider-auth reuse.

The immediate risk is no longer lack of capability. It is that product runtime progress is being slowed by recurring governance/CI coupling, historical mutable fixtures, special landing/reconstruction paths, and an increasingly long-lived planning branch.

For the next bounded phase, success is measured by **convergence and repeatability**, not by the number of new platform features.

Target outcome:

```text
one normal product change
-> one clean product branch / PR
-> deterministic product CI
-> independent verification
-> clean landing
-> restart-safe unattended dogfood
```

without requiring a new governance workaround for each ordinary product change.

## 2. Stabilization scope freeze

Until the exit criteria in this document are met, do not start broad implementation of:

- #152 Freshness Automation Foundation;
- #177 natural-language goal intake / Spec Kit-first decomposition;
- broad Pack / Capability growth;
- adaptive or learned model routing;
- a second real executor solely for breadth;
- a second orchestration framework;
- swarm, voting, debate, or other multi-Agent topology expansion beyond the current bounded team path.

Planning and research may continue, but these tracks must not displace stabilization work or create a parallel runtime.

The current persisted OpenCode provider-auth reuse landing at `3b650e6239336c796593cecd3c137cf839cf1e95` is the stabilization baseline. Persisted/external OpenCode auth is the preferred first real dogfood credential path. API-key credential relay remains a supported secondary path and must not block the first end-to-end unattended proof.

## 3. Workstream A — CI and governance test isolation

### Problem

Product changes are still vulnerable to failures caused by historical governance state or tests that accidentally encode a previous repository snapshot as a permanent invariant. Examples include reading the current tracked `project_state/decision_packet.md` as an implicit global fixture or asserting an old exact dependency set when the actual architecture has intentionally moved forward.

### Required separation

Converge toward three explicit classes of tests:

```text
product invariants
  = runtime/security/behavior that must remain true across rounds

governance contract tests
  = current typed authority/policy semantics

historical governance fixtures
  = regression examples for earlier Decisions, merge intents and migrations
```

Directory names may differ from the conceptual names below, but the ownership boundary must be explicit:

```text
tests/product/
tests/governance_contract/
tests/governance_fixtures/
```

### Rules

1. The repository's current mutable `project_state/decision_packet.md` must not be the implicit fixture for unrelated product tests.
2. Historical Decisions, merge intents and transition states should be represented by explicit immutable fixtures when regression coverage is needed.
3. Dependency/version assertions are global blockers only when they represent an intentional compatibility contract. Historical exact pins must not silently become permanent schema.
4. Product CI should fail for product invariant violations, not because an unrelated historical authority snapshot changed.
5. Governance contract CI should validate the current typed contract against explicit inputs.
6. Historical fixtures must remain useful regression evidence without controlling current product truth.
7. Do not weaken fail-closed security properties merely to make the suite green.

### Acceptance

A normal product-only change can run the required product and governance-contract tests without depending on round-specific tracked authority state, while historical governance regressions remain testable through explicit fixtures.

## 4. Workstream B — long-running unattended dogfood

Run one real, bounded end-to-end dogfood using the capabilities that now exist instead of adding another platform layer first.

Required stack:

```text
persisted OpenCode external/session auth
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
-> Planner completes
-> Coder begins/completes
-> persist checkpoint + heartbeat
-> terminate the trusted execution process/host boundary intentionally
-> allow the old lease to become stale
-> restart the trusted host/process
-> reopen the same TaskStore/checkpointer
-> reconcile stale ownership
-> acquire a newer fenced epoch
-> resume the same task/run/worktree
-> do not re-run already accepted roles
-> Reviewer continues from verified persisted product state
-> deterministic verification completes
```

Required evidence:

- same task identity before and after restart;
- same durable run/worktree identity;
- monotonically valid lease/fencing transition;
- at least two persisted heartbeat observations while the original process is alive;
- completed roles are not replayed;
- persisted worktree digest/state is checked before trusting prior role output;
- no raw provider credential appears in TaskStore, workspace, evidence, logs or frontend state;
- final verifier result is derived from deterministic evidence, not Agent self-report;
- failure is classified explicitly if recovery cannot continue safely.

A failed dogfood is useful evidence. Do not hide a real incompatibility behind fixture-only success.

## 5. Workstream C — product history versus execution-authority history

Formalize this long-term invariant:

```text
Product Git history != transient execution-authority history
```

### Product Git should retain

- product/runtime code;
- stable schemas/contracts;
- deterministic tests and durable fixtures;
- active architecture/roadmap documentation;
- stable policy that genuinely belongs to the product.

### Runtime/artifact state should increasingly retain

- per-run Decisions that are not durable product design;
- execution receipts;
- transient Gate outputs;
- current-round command plans;
- heartbeat/lease/checkpoint evidence;
- other round-specific execution material.

The existing product-only reconstruction pattern has proved the value of separating these histories, but repeated manual reconstruction must not become the permanent normal workflow.

### Direction

Prefer an explicit runtime/artifact boundary so ordinary product commits are clean by construction. Do not create a new tracked artifact family merely to implement this separation.

## 6. Workstream D — planning branch cutover

`owner/repository-modernization-v2-planning` is currently the effective product integration trunk. It must not remain a permanent shadow `main` without an explicit lifecycle.

Define and execute a future promotion/cutover only after all of the following are true:

1. the active product/runtime test set passes on the integration baseline;
2. the CI/governance test isolation above is established;
3. at least one ordinary product change lands without a special authority-history reconstruction workaround;
4. the long-running unattended dogfood passes or reaches a well-understood bounded blocker with no evidence corruption;
5. current source-of-truth documentation points to Repository Modernization V2 rather than a superseded architecture;
6. historical/frozen PRs and branches needed only as evidence are clearly classified;
7. the exact promotion method and post-promotion rollback/verification checks are documented before mutation.

The cutover may promote the modernized architecture into `main` or establish another explicitly named current integration branch, but there must be exactly one declared current product integration truth after cutover.

## 7. Workstream E — collect capability data, do not route automatically yet

The project now has enough real execution surface to begin collecting empirical model/executor capability data. This is data collection only; it does not authorize adaptive routing.

Record, where available and sanitized:

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

### Rules

- No raw prompts, credentials or sensitive repository content are required merely to build capability statistics.
- Capability claims should eventually be based on observed task-family outcomes rather than static labels such as `supports_coding`.
- Do not introduce LiteLLM or another router solely to collect this data if the existing execution path can record it.
- Do not implement learned/adaptive routing until there is a meaningful sample of real executions and a deterministic evaluation target.

Later routing may combine:

```text
capability fit
+ availability
+ quota/rate-limit headroom
+ latency
+ cost/budget
+ user quality/economy/speed preference
+ observed failure history
```

but that is explicitly outside this stabilization phase.

## 8. Mature-component ownership invariants

Every generic capability should have one primary owner. Reverse-agent should add only the thin policy/evidence/integration layer that is specific to this product.

| Capability | Primary owner / direction |
|---|---|
| orchestration | LangGraph |
| durable product task truth | reverse-agent TaskStore |
| first real coding executor | OpenCode |
| presentation/workbench | Agent Canvas where retained |
| repository/PR/CI truth | GitHub |
| model gateway/accounting candidate | LiteLLM when justified by a later bounded phase |
| dependency/upstream update automation | Renovate under #152 when resumed |
| provider authentication | provider/executor-supported auth stores; reverse-agent stores sanitized references/status only |
| policy/evidence/verification | reverse-agent |

Additional invariants:

- LangGraph state must not become a second TaskStore.
- `multi_agent` must not become a fake executor kind; orchestration selects real executors through existing boundaries.
- Do not duplicate an executor's already persisted provider secret inside reverse-agent merely for convenience.
- A compatibility adapter must have a retirement condition.

## 9. Governance failure budget

After the stabilization corrections are established, allow at most **one bounded correction** for a newly discovered recurring governance/CI architecture defect on the ordinary product path.

If the same class of blocker recurs after that correction, the default response is:

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

Security-critical fail-closed behavior remains mandatory. The goal is to reduce duplicated authority mechanics, not to bypass required verification.

## 10. Stabilization exit criteria

This subplan is complete when all of the following are demonstrated:

1. persisted OpenCode external/session auth is usable after restart without duplicating the raw provider secret in reverse-agent;
2. product/governance/historical test responsibilities are explicitly isolated and ordinary product CI no longer depends on incidental round-specific authority state;
3. one real long-running `sequential_team` task survives an intentional process/host interruption and resumes the same durable run/worktree safely;
4. completed roles are not replayed and stale workers cannot commit new truth;
5. final acceptance comes from deterministic verification;
6. raw credentials do not enter product task/evidence state;
7. the product-history / execution-authority-history separation has an explicit implementation direction that does not rely on permanent manual reconstruction;
8. planning-branch cutover criteria are satisfied and a bounded promotion task can be authorized;
9. real execution telemetry is being recorded for future capability analysis;
10. no new orchestration framework, broad Pack layer, adaptive router or second executor has been introduced merely to expand scope during stabilization.

## 11. Resume after stabilization

After exit, return to the parent Repository Modernization V2 roadmap and re-evaluate sequencing using current evidence. The expected candidate tracks remain:

```text
#152 Freshness Automation
#177 Goal -> Spec -> Plan -> Tasks
real end-to-end dogfood expansion
Pack / Capability growth
later data-backed model/executor routing
broader historical debt retirement
```

Do not assume the old order is still correct merely because it was previously documented. Real dogfood evidence and current dependency relationships decide the next bounded phase.

## 12. Non-goals

This subplan does not authorize:

- product code changes;
- branch promotion or merge;
- removal of security gates without replacement evidence;
- automatic model routing;
- new provider credentials or secret migration;
- a second orchestration framework;
- broad Pack implementation;
- autonomous merge/release;
- destructive cleanup of historical branches, worktrees or evidence.

Each implementation workstream still requires the repository's applicable bounded authority and exact-head verification.