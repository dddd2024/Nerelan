# Sprint B — Governance / CI Convergence Plan

```text
STATUS: PLANNING_REFERENCE_ONLY
PARENT: #232
RUNTIME_PREDECESSOR: #230
EXECUTION_AUTHORITY: NONE
CREATED: 2026-08-17
```

Sprint B exists to remove governance/CI overhead that currently slows ordinary product delivery. It is intentionally separate from Sprint A runtime durability so that runtime semantics and governance mechanics do not mutate the same files in one authority.

## Goals

1. Separate product invariant tests, current governance contract tests, and historical governance fixtures.
2. Stop using mutable `project_state/decision_packet.md` as an implicit fixture for unrelated product tests.
3. Define a clean-product-branch-by-construction publication contract so accepted product commits do not require routine post-hoc blob reconstruction.
4. Define focused per-change validation and one broader per-batch suite.
5. Define GitHub-native protection/ruleset requirements for the effective integration branch and later `main` cutover.
6. Preserve fail-closed security and exact-authority semantics while reducing repeated round-specific mechanics.

## Non-overlap with Sprint A

Sprint B must not mutate the Sprint A product paths while #230 V2 is active:

- `reverse_agent/platform_v1/task_service.py`
- `reverse_agent/platform_v1/task_execution.py`
- `reverse_agent/platform_v1/durable_execution.py`
- `reverse_agent/platform_v1/run_store.py`
- `reverse_agent/platform_v1/trusted_host.py`
- corresponding #230 focused test files.

Planning/research can proceed while Sprint A runs. Canonical landing cannot advance the planning branch underneath active #230 V2.

## Workstream B1 — test responsibility isolation

Target conceptual classes:

```text
product invariants
current governance contract
historical governance fixtures
```

Acceptance:

- normal product tests do not depend on the current tracked Decision packet merely because it exists;
- historical authority examples are explicit immutable fixtures when needed;
- current governance tests use explicit typed inputs;
- stale historical exact-SHA/version fixtures do not become unrelated product blockers;
- security-critical fail-closed assertions remain global where they truly are current invariants.

## Workstream B2 — clean product publication

Target flow:

```text
exact canonical base
-> immutable execution authority
-> explicitly authorized clean product branch/worktree
-> product/test commits only
-> authority records/verifies exact product candidate SHA
-> Owner audit
-> direct clean landing
```

The transition contract must explicitly authorize this topology before it is used. Do not create an ad-hoc second branch from an existing authority.

Acceptance:

- Decision/gate artifacts are not copied into the clean product candidate;
- candidate SHA is exact and immutable for Owner audit;
- authority branch can remain audit evidence without contaminating product history;
- no force push/rebase is required;
- one ordinary change lands without post-hoc blob-by-blob reconstruction.

## Workstream B3 — validation tiers

Define commands for:

- focused touched-surface checks per change;
- provider-free integration/regression checks per coherent batch;
- separate milestone/live dogfood.

Avoid rerunning unrelated historical governance suites on every product delta.

## Workstream B4 — GitHub-native integration protection

Current effective planning branch is not protected. Before cutover, define and apply where supported:

- no direct ordinary writes to integration truth;
- required deterministic checks;
- force-push protection;
- PR/review/ruleset policy appropriate to a single-owner repository;
- explicit emergency/Owner exception path with audit evidence.

This should reduce custom repository-host governance rather than duplicate GitHub.

## Workstream B5 — cutover readiness contribution

Sprint B is complete when one ordinary product change can prove:

```text
clean candidate
-> deterministic CI
-> Owner audit
-> clean landing
```

without transient Decision/gate history entering product Git and without historical fixtures causing incidental failure.

## Hard stops

Stop and seek a successor authority if implementation would:

- weaken secret/credential boundaries;
- permit destructive/force operations not explicitly approved;
- change runtime product behavior owned by active Sprint A;
- silently reinterpret current Decision authority;
- make historical failures disappear by deleting evidence rather than classifying/migrating it.

No execution is authorized by this document.
