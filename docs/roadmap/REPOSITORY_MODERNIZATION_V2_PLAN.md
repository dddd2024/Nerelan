# Repository Modernization V2 Plan

> **For agentic workers:** execute only a separately authorized phase. Do not interpret this roadmap as code-mutation authority.

**Umbrella:** #148  
**Strategy:** strangler migration  
**Planning branch:** `owner/repository-modernization-v2-planning`  
**Baseline main:** `dd4cb074ab5b9baacf300706878b29bd745f12c3`

## Goal

Reduce reverse-agent to one current, testable architecture while preserving the already-proven Task API / TaskStore / OpenCode / evidence / frontend vertical slice and retiring historical state, governance, CI and backlog residue.

## Global constraints

- Do not greenfield-rewrite the product core.
- Do not merge or mutate Draft PR #146 during Phase 0.
- Do not use old `project_state/current_*` files as global product truth.
- Each implementation phase gets its own bounded branch, tests and review.
- Each replacement must retire/archive the superseded path; compatibility layers are temporary, not permanent.
- No direct push to `main`, force push, rebase, release or deploy as part of modernization implementation.
- Multi-Agent support is not considered operational until an exact-head real vertical slice proves it.

---

## Phase 0 — Current Truth Freeze and Inventory

**Objective:** create a reliable map before any product mutation.

### Deliverables

- `docs/architecture/CURRENT_ARCHITECTURE_BASELINE.md`
- `docs/architecture/HISTORICAL_DEBT_MATRIX.md`
- this plan
- open Issue classification
- branch/PR classification where historical branches materially affect current assumptions

### Exit criteria

- [ ] landed-vs-branch-only-vs-planned capability states are explicit;
- [ ] every known governance/state/CI debt item has an owner phase;
- [ ] #146 is frozen as evidence, not used as modernization working branch;
- [ ] no product source file changed.

---

## Phase 1A — P0 Security Verification: OpenCode Evidence Redaction

**Goal:** prove or refute the suspected tuple-container redaction defect before broad refactoring.

**Candidate files:**

- `reverse_agent/platform_v1/opencode_executor.py`
- `tests/platform_v1/test_opencode_executor.py`

### Test-first acceptance

1. Add a nested evidence payload containing secret-like values in:
   - dict;
   - list;
   - tuple;
   - tuple nested inside dict/list.
2. Call the same production redaction entry point used before persistence.
3. Assert no original secret survives any container form.
4. If tuple regression fails, minimally change `_redact_recursively` so returned tuple-derived data uses the recursively redacted result.
5. Re-run focused executor tests.
6. Run the relevant Platform V1 suite and `git diff --check`.

### Exit criteria

- [ ] exploitability/path behavior is demonstrated by test, not assumed;
- [ ] regression is fixed if reproducible;
- [ ] no unrelated executor redesign.

---

## Phase 1B — State and Authority Lifecycle Reset

**Goal:** stop completed historical authority from masquerading as active current state.

### Required design

Replace ambiguous perpetual `active` semantics with an explicit lifecycle:

```text
DRAFT
-> ACTIVE
-> COMPLETED | SUPERSEDED | EXPIRED | ABORTED
-> ARCHIVE
```

### Required properties

- `active` means currently applicable authority only;
- completed PR landing authority cannot remain current merely because a tracked file was not cleaned up;
- state transition records bind exact Decision/PR/head identity;
- archive history remains auditable;
- legacy reverse-engineering state is separately classified from platform execution authority;
- no destructive cleanup of local runtime scratch is implied.

### Candidate paths to audit before implementation

- `project_state/decision_packet.md`
- `project_state/mainline_merge_intents/**`
- `project_state/current_state.json`
- `project_state/state_manifest.json`
- source-of-truth docs
- relevant state/gate tests

### Exit criteria

- [ ] one machine-readable lifecycle exists;
- [ ] completed #134-era authority cannot satisfy an active-current query;
- [ ] legacy reverse state is explicitly non-global;
- [ ] old state remains available in archive form where needed.

---

## Phase 1C — Runtime Scratch / Workspace Lifecycle

**Goal:** remove long-lived ambiguous `.frontend_stage/**` and `.platform_v1_runtime/**` carryover from normal governance semantics.

### Required properties

- runtime scratch location and ownership are explicit;
- startup can distinguish tracked repository state, managed runtime state and unrelated local dirt;
- preservation is default; no `clean`/`reset --hard` automation;
- lifecycle includes create, identify, reuse/recover when valid, quarantine when suspect, retire when safe;
- #147 baseline-vs-delta semantics feed Phase 2 rather than being solved by broad allowlists.

---

## Phase 2A — One Typed Decision Contract

**Goal:** make one schema/compiler path authoritative for Decision structure.

### Architecture

```text
Decision source
-> typed/schema validation
-> semantic compilation
-> command plan
-> preflight
-> execution evidence
```

Tests verify the contract; they do not secretly define additional required fields.

### Required fields/classes

At minimum model:

- identity / revision;
- risk tier;
- repository/base/branch binding;
- allowed mutation paths;
- read-only/reference paths;
- command-local mutation grants;
- capability/network policy;
- evidence-source types;
- publication/merge capability flags;
- baseline dirty-state identity;
- retry/repair budget;
- lifecycle state.

### Required regression inputs

Use historical failures as fixtures:

- #142 unsupported evidence-source token;
- #143 outer execution-surface command incompatibility;
- #147 pre-existing dirty carryover;
- #136/#146 landing contracts that passed some layers but exposed later implicit fields.

### Exit criteria

- [ ] Decision can be validated read-only before activation;
- [ ] schema and semantic compiler produce actionable machine-readable errors;
- [ ] no Platform V1 test can introduce an undocumented required Decision field;
- [ ] old contract parser has a documented retirement point.

---

## Phase 2B — Baseline vs Current-Round Delta

**Goal:** formalize the distinction tracked by #147.

### Model

```text
startup baseline
  + stable identity/digest of pre-existing dirty paths
  + current-round command receipts
  = post-round delta
```

A path dirty before the round is not automatically a mutation by the round. A new write after the baseline remains subject to exact command/path authority.

### Exit criteria

- [ ] unchanged pre-existing scratch does not cause false mutation attribution;
- [ ] a new write to the same path fails without grant;
- [ ] reference paths fail closed on actual delta;
- [ ] artifacts expose baseline and delta separately.

---

## Phase 2C — Execution-Surface Compatibility

**Goal:** prevent repository-authorized commands from being rejected only after reaching the outer local Agent/tool layer.

### Direction

- prefer short atomic commands;
- move complex behavior into reviewed repository-owned helpers;
- declare executor capability profiles;
- statically reject known-incompatible command shapes before activation;
- keep host safety stricter than repository policy when necessary.

#143 and #139 should be consolidated into this design if still applicable.

---

## Phase 3A — CI / Gate Simplification

**Goal:** retire permanent migration machinery from normal CI.

### Inventory targets

- `State Gate` transition path;
- legacy Gate path;
- Path-A compatibility;
- Decision Preflight duplication;
- PR-number-specific bootstrap/authority branches;
- duplicate pytest invocations across workflows.

### Target responsibility split

Prefer a small set such as:

```text
CI                -> build/unit/integration correctness
Agent Policy      -> typed Decision/policy validation when applicable
Evidence          -> required artifacts/provenance when applicable
Security          -> security/static checks
```

Do not preserve a legacy path solely because historical PRs once required it.

### Exit criteria

- [ ] no normal workflow contains special logic for old PR numbers such as #106/#112;
- [ ] one authority validation path exists;
- [ ] duplicate test execution is reduced;
- [ ] historical migration tests move to archival regression fixtures or are retired.

---

## Phase 3B — GitHub-Native Repository Protection

**Goal:** stop duplicating repository-host enforcement inside reverse-agent where GitHub can enforce it directly.

Audit and configure, where supported:

- require pull request before main changes;
- required status checks;
- allowed merge methods;
- force-push protection;
- deletion protection where desired.

Repository-owned policy should still decide Agent capabilities and evidence requirements; GitHub should enforce GitHub repository mechanics.

---

## Phase 4A — Runtime Contract Consolidation

**Goal:** make current runtime naming and interfaces match actual architecture.

### Required audit

- `run_store.py` vs `TaskStore` naming;
- obsolete coordinator/execution-adapter references;
- fixture-first comments and defaults;
- executor result/state contracts;
- publication-state separation.

Renames must be compatibility-audited; do not churn import paths merely for aesthetics.

---

## Phase 4B — Typed Frontend/Backend Task Contract

**Goal:** replace broad fallback-driven truth reconstruction with an explicit API contract.

### Required outcomes

- real validation state derives from authoritative backend truth;
- #145 is fixed;
- mock/fixture behavior is explicit and cannot leak into real tasks;
- `nextAction`, validation, workflow and authority states have declared semantics;
- frontend tests include real OpenCode-shaped payloads;
- Agent Canvas-derived presentation remains presentation, not a second runtime-state model.

---

## Phase 4C — Backlog and Documentation Migration

**Goal:** make GitHub planning and repository docs describe the current architecture.

### Classify every relevant open Issue

- `KEEP` — still accurate and applicable;
- `REWRITE` — problem remains, implementation assumptions stale;
- `SUPERSEDED` — replaced by landed/current architecture;
- `ARCHIVE` — historical evidence only.

Initial known examples:

- #145: KEEP, fold into Phase 4B;
- #142/#143/#147: KEEP/REWRITE into Phase 2;
- #139: likely REWRITE/merge into Phase 2C;
- #138: SUPERSEDED by #148 documentation alignment scope;
- #120: problem likely KEEP, implementation path REWRITE because referenced coordinator architecture is stale;
- #105: likely ARCHIVE/SUPERSEDED after current authority path is replaced;
- #126: KEEP as research reference, not product capability;
- #137: KEEP as post-modernization mother-platform direction.

Update README, AGENTS and source-of-truth docs only after the architecture states they describe are actually selected.

---

## Phase 5 — Multi-Agent Capability Vertical Slice

**Prerequisite:** Phases 1-4 produce one stable runtime/policy/evidence substrate.

**Goal:** prove one real multi-Agent collaboration path without building a custom scheduler from zero.

### Required spike before implementation

Evaluate a mature orchestration runtime or native runtime capability against the exact required contract:

```text
parent/manager
-> structured child task
-> isolated worker execution
-> artifact/evidence return
-> join/dependency resolution
-> independent verification
-> bounded replan/escalation
```

### Minimum acceptance slice

Use one real repository task decomposable into at least two independent workers and one verifier/join step.

Must prove:

- [ ] two or more workers actually execute;
- [ ] overlap/parallelism where requested is observable;
- [ ] each worker has bounded task/path/tool authority;
- [ ] parent passes structured constraints, not only prose chat;
- [ ] artifacts/results have stable identities;
- [ ] join waits for required dependencies;
- [ ] verifier can reject one worker result;
- [ ] failure/retry does not duplicate already accepted work;
- [ ] UI can represent the worker relationship/evidence without inventing task truth;
- [ ] exact-head regression evidence exists.

Only after this phase may README/AGENTS claim operational multi-Agent support.

---

## Landing strategy for frozen #146

Do not continue adding v25/v26 landing contracts to the old authority system.

After Phase 1/2 establishes the modernization bridge, choose one explicit disposition:

1. land #146 through a minimal compatibility bridge proven against the new lifecycle; or
2. transplant the already-accepted product commits into a fresh branch on the new baseline without rewriting product logic.

The selected option must preserve the accepted Stage B evidence and avoid a new frontend rewrite.

---

## Modernization completion definition

The repository is considered modernized when:

```text
one current architecture
one current source-of-truth hierarchy
one typed Decision/policy contract
one active-state lifecycle
one normal CI authority path
one durable Task API/store runtime
one explicit executor abstraction
one evidence/verifier boundary
one frontend task truth mapping
historical artifacts clearly archived
multi-Agent claims backed by real evidence
```

Every phase should leave the repository simpler than it found it.