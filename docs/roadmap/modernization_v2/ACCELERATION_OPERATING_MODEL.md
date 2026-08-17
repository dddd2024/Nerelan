# Repository Modernization V2 — Acceleration Operating Model

```text
STATUS: PLANNING_REFERENCE_ONLY
PARENT: #148
ACCELERATION_ISSUE: #232
CURRENT_RUNTIME_EXECUTION: #230
CREATED: 2026-08-17
PRE_PUBLICATION_CANONICAL_BASE: owner/repository-modernization-v2-planning@b6473a74fa74c91394a015a39b3c0d57c6eb5cc2
EXECUTION_AUTHORITY: NONE
```

> This document changes operating cadence, not the security boundary. It does not itself authorize local execution, provider/model access, credentials, merge, branch promotion, or destructive repository operations.

## 1. Objective

Increase accepted product progress per governance round-trip by reducing micro-authority churn, duplicated validation, and repeated product-history reconstruction.

Primary throughput metric:

```text
accepted product delta / governance round-trip
```

Do not optimize for Issue count, Decision count, or Gate artifact count.

## 2. Owner audit corrections

### 2.1 Reuse coherent scope; do not version authority for cosmetic batching

Issue #230 R2 V1 already covered the complete provider-free single-task durability slice: server-owned durable run, request-lifetime decoupling, fencing, stale reconciliation, bounded recovery, duplicate execute prevention, deterministic validation, and sequential-team regression coverage.

A successor authority is not justified merely to rename that same scope as a Sprint or to permit more ceremony. Small in-scope implementation/test repairs should happen before the final product commit. A new authority version is required only when the permission/scope/security contract changes materially **or when its exact canonical base becomes stale**.

During publication of this acceleration plan, canonical planning advanced after V1 had been published. Therefore #230 V1 is now stale by exact-base rule and MUST NOT execute. Owner must publish one replacement V2 from the final post-planning exact head; this is a required drift repair, not a new implementation slice.

After V2 publication, canonical planning is frozen until Sprint A returns for Owner audit unless an emergency safety correction explicitly supersedes V2.

### 2.2 Parallel work does not imply parallel landing

Exact-base authorities bind to a canonical planning SHA. Independent lanes may perform planning or isolated development concurrently when mutation surfaces do not overlap, but canonical landings are serialized.

Before any lane lands, Owner re-observes canonical planning. Any landing that advances planning invalidates another lane's old exact-base landing assumption and requires revalidation/successor publication before that lane can land.

### 2.3 Clean-product-branch-by-construction is Sprint B governance work

The current transition contract authorizes a specific authority branch/worktree. Creating a second clean product branch ad hoc from a Sprint A local execution session would bypass that contract.

Therefore Sprint A keeps the existing authority-branch implementation pattern and Owner performs one final product-only reconstruction after acceptance. Sprint B will explicitly implement and validate clean-product publication so this reconstruction can later be removed.

## 3. Immediate accelerated sequence

### Sprint A — Runtime convergence (#230)

Execute one coherent provider-free batch covering:

- durable run identity before external dispatch;
- HTTP/request lifetime no longer acting as execution authority;
- duplicate/concurrent execute prevention;
- fenced accepted task truth;
- provider-free stale-run reconciliation;
- explicit bounded recovery with newer fencing epoch;
- no silent retry of ambiguous external operations;
- deterministic validation after an accepted executor result without second executor dispatch;
- no sequential-team durability regression.

Do not open intermediate recovery Issues for same-scope implementation defects that can be repaired before the final commit.

Validation remains provider-free. Sprint A does not authorize OpenCode/model/provider/credential access.

After local acceptance:

```text
one Owner audit
-> one product-only landing
-> close Sprint A implementation
-> one separate real Dogfood2 interruption authority
```

Do not insert additional auth/config/model readiness probes unless new evidence specifically reopens that boundary.

### Sprint B — Governance / CI convergence

Prepare and implement a separate non-overlapping batch for:

- product invariant / current governance / historical fixture isolation;
- removing current mutable Decision state as an implicit unrelated product-test fixture;
- a clean-product-branch-by-construction publication contract;
- focused per-change tests plus one broader per-batch suite;
- GitHub-native protection/ruleset requirements for the effective integration branch;
- eliminating routine manual product-only reconstruction after the new contract is proven.

Sprint B planning may proceed while Sprint A runs, but Sprint B must not move canonical planning underneath active Sprint A V2.

### Sprint C — Integration-trunk cutover readiness

After Sprint A and Sprint B evidence:

1. prove a normal product change can follow clean product branch -> deterministic CI -> Owner audit -> direct clean landing;
2. run long-running sequential-team interruption/recovery dogfood;
3. satisfy objective cutover checks;
4. promote one declared integration truth and retire the permanent shadow-planning pattern.

## 4. Three-tier validation

**Per change:** focused deterministic tests for touched behavior plus scope/diff checks.

**Per batch:** relevant provider-free integration/regression suite once after the coherent batch is complete.

**Per milestone/live:** one real provider/model dogfood only after provider-free product landing.

Historical round-specific fixtures are blockers only when they represent a current contract regression. Independent historical drift is classified for Sprint B rather than automatically creating a new runtime recovery round.

## 5. Hard-stop boundary

Continue to fail closed for:

- canonical or authority SHA drift;
- credential/secret-boundary uncertainty;
- destructive operations not explicitly authorized;
- required mutation outside accepted architecture/path scope;
- deterministic core invariant failure;
- inability to prove safe handling of an ambiguous external operation;
- evidence corruption.

Do not automatically create a new authority solely for:

- an in-scope implementation bug found before commit;
- a missing same-scope test case;
- stale documentation unrelated to execution truth;
- known independent historical fixture drift;
- a non-authoritative flaky test unrelated to the changed product invariant.

## 6. Owner / local-agent division

Owner/GitHub performs all remotely available work:

- issue and roadmap maintenance;
- authority publication/supersession bookkeeping;
- exact remote SHA observation;
- PR/branch metadata work;
- candidate audit;
- final landing and closure.

Local Agent is reserved for work that genuinely requires the local checkout/runtime:

- code edits;
- local deterministic tests;
- local worktree evidence;
- intentional process-interruption/runtime experiments.

## 7. Authority publication rule after this document

The pre-publication state was:

```text
old canonical planning:
owner/repository-modernization-v2-planning
@ b6473a74fa74c91394a015a39b3c0d57c6eb5cc2

stale Sprint A V1 authority:
owner/issue230-single-durable-execution-r2-v1
@ 4ff1949ec09e7e308576eb3120141f26804e76da

Decision:
decision_20260817_issue230_single_durable_execution_r2_v1
```

Because publishing this planning document advanced canonical planning, V1 remains HOLD/SUPERSEDED and must never execute. Owner publishes V2 only after all Owner-side planning mutations for this round are complete, binds V2 to that exact final planning head, reverse-audits the one-Decision-only delta, and then freezes planning while V2 is active.

## 8. Non-goals

Acceleration does not authorize:

- weakened credential boundaries;
- bypassed fencing/lease semantics;
- trusting model self-report instead of deterministic verification;
- force push, rebase, reset, clean, stash, amend, or destructive cleanup;
- automatic retry of ambiguous external operations;
- overlapping product writes from multiple lanes;
- concurrent canonical landings;
- broad #152/#177/Pack/adaptive-routing implementation before stabilization exit.
