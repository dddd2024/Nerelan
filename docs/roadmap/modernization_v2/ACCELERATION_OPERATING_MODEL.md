# Repository Modernization V2 — Acceleration Operating Model

```text
STATUS: PLANNING_REFERENCE_ONLY
PARENT: #148
ACCELERATION_ISSUE: #232
CURRENT_RUNTIME_EXECUTION: #230
CREATED: 2026-08-17
CANONICAL_BASE_AT_PUBLICATION: owner/repository-modernization-v2-planning@b6473a74fa74c91394a015a39b3c0d57c6eb5cc2
EXECUTION_AUTHORITY: NONE
```

> This document changes the operating cadence, not the security boundary. It does not authorize local execution, provider/model access, credentials, merge, branch promotion, or destructive repository operations.

## 1. Objective

Increase accepted product progress per governance round-trip by reducing micro-authority churn, duplicated validation, and repeated product-history reconstruction.

Primary throughput metric:

```text
accepted product delta / governance round-trip
```

Do not optimize for Issue count, Decision count, or Gate artifact count.

## 2. Owner audit corrections to the first acceleration proposal

Three corrections are mandatory before using the accelerated model.

### 2.1 Reuse an already-coherent authority instead of creating a replacement merely for batching

Issue #230 R2 V1 already covers the whole provider-free single-task durability slice: server-owned durable run, request-lifetime decoupling, fencing, stale reconciliation, bounded recovery, duplicate execute prevention, deterministic validation, and sequential-team regression coverage.

Therefore a new Sprint-A authority must not be created merely to rename the same scope or permit more governance ceremony. #230 V1 remains the correct authority unless its local transition rejects it or implementation proves that the allowed architecture/path/security boundary is materially insufficient.

Small in-scope implementation/test repairs should happen before the single final product commit. A new authority version is required only when the permission or scope boundary changes materially.

### 2.2 Parallel work does not imply parallel landing

Exact-base authorities bind to a canonical planning SHA. Independent lanes may perform planning or isolated development concurrently when their mutation surfaces do not overlap, but canonical landings must be serialized.

Before any lane lands, Owner must re-observe canonical planning. A landing that advances canonical planning invalidates any other still-active exact-base landing assumption and requires revalidation before publication/landing.

### 2.3 Clean-product-branch-by-construction is a governance change, not an ad-hoc #230 exception

The current #230 Decision authorizes only its authority branch/worktree. Creating a second clean product branch from the local execution session without explicit governance support would bypass the current transition contract.

Therefore clean-product publication is Sprint B work. Until that mechanism is implemented and validated, #230 follows the existing authority-branch pattern and Owner performs one final product-only landing reconstruction after acceptance.

## 3. Immediate accelerated sequence

### Sprint A — Runtime convergence (#230)

Use the already-published #230 R2 V1 authority without creating a successor merely for acceleration.

One local implementation batch must cover the full accepted scope:

- durable run identity before external dispatch;
- request lifetime no longer acts as execution authority;
- duplicate/concurrent execute prevention;
- fenced accepted task truth;
- provider-free stale-run reconciliation;
- explicit bounded recovery with newer fencing epoch;
- no silent retry of ambiguous external operations;
- deterministic validation after accepted executor result without second executor dispatch;
- no sequential-team durability regression.

Validation remains provider-free. No OpenCode/model/provider/credential access is allowed in Sprint A.

After local acceptance, Owner performs one independent audit and one clean product-only landing. Do not open intermediate recovery Issues for same-scope implementation defects that can be repaired before the final commit.

After landing, run one separate real Dogfood2 interruption authority. Do not insert additional auth/config/model readiness probes unless new evidence specifically reopens that boundary.

### Sprint B — Governance / CI convergence

Prepare and then implement a separate non-overlapping governance batch:

- isolate product invariants, current governance contract tests, and historical governance fixtures;
- remove current mutable Decision state as an implicit unrelated product-test fixture;
- establish a clean-product-branch-by-construction publication contract;
- define focused per-change tests and one broader per-batch suite;
- design GitHub-native protection/ruleset requirements for the effective integration branch;
- reduce or eliminate manual product-only reconstruction after the new publication contract is proven.

Sprint B may be planned while Sprint A runs, but its canonical landing must not move the planning branch underneath an active Sprint A authority.

### Sprint C — Integration-trunk cutover readiness

After Sprint A and Sprint B evidence:

1. prove one normal product change can follow clean product branch -> deterministic CI -> Owner audit -> direct clean landing;
2. run the long-running sequential-team interruption/recovery dogfood;
3. satisfy objective cutover checks;
4. promote one declared integration truth and retire the permanent shadow-planning pattern.

## 4. Three-tier validation

### Per-change

Run only focused deterministic tests for the touched behavior plus scope/diff checks.

### Per-batch

Run the relevant provider-free integration/regression suite once after the coherent batch is complete.

### Per-milestone/live

Run one real provider/model dogfood after the provider-free product batch lands.

Historical round-specific fixtures are blockers only when they represent a current contract regression; otherwise classify them separately and repair them in Sprint B.

## 5. Hard-stop boundary

Continue to fail closed for:

- canonical or authority SHA drift;
- credential/secret-boundary uncertainty;
- destructive operations not explicitly authorized;
- required product mutation outside the accepted architecture/path family;
- deterministic core invariant failure;
- inability to prove safe handling of an ambiguous external operation;
- evidence corruption.

Do not automatically create a new recovery round solely for:

- an in-scope implementation bug found before commit;
- a missing same-scope test case;
- stale documentation;
- known independent historical fixture drift;
- a non-authoritative flaky test unrelated to the changed product invariant.

## 6. Owner / local-agent division

Owner/GitHub performs all remotely available work:

- issue and roadmap maintenance;
- authority publication and supersession bookkeeping;
- exact remote SHA observation;
- PR/branch metadata work;
- independent candidate audit;
- final landing and closure.

Local Agent is used only for work that genuinely requires the local checkout/runtime:

- code edits;
- local deterministic tests;
- local worktree evidence;
- intentional process-interruption/runtime experiments.

## 7. Current authority state at publication

At this document's publication baseline:

```text
canonical planning:
owner/repository-modernization-v2-planning
@ b6473a74fa74c91394a015a39b3c0d57c6eb5cc2

Sprint A authority:
owner/issue230-single-durable-execution-r2-v1
@ 4ff1949ec09e7e308576eb3120141f26804e76da

Decision:
decision_20260817_issue230_single_durable_execution_r2_v1
```

The prior temporary Owner HOLD on #230 was introduced only to allow acceleration replanning. Once the Owner audit confirms the exact SHAs remain unchanged, the HOLD may be lifted without creating a replacement Decision because the existing #230 authority already spans the coherent Sprint A implementation slice.

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
