# Platform V1 Codex End-to-End Coordinator Design

Date: 2026-08-05
Source Work Item: #114
Parent Product Issue: #90
Live Canary: #115
Starting Base: `1142dd324fdd4c4bf2a1353d9d5e93bc04b33507`
Implementation Branch: `agent/platform-v1-codex-e2e-v1`

## 1. Problem

The repository already contains the reusable pieces needed to validate tasks and evidence, but it does not contain a production coordination loop. `reverse_agent.platform_v1` can validate Work Items, load authority, collect Git/GitHub evidence, evaluate acceptance and normalize OpenHands events. The OpenHands lifecycle remains fake-only, and no component currently owns persistent run state, worktree creation, real Codex invocation, commit/push publication, Draft PR creation or process-restart recovery.

The first version must connect those existing pieces into one usable loop rather than rebuild mature tools.

## 2. Selected Approach

Implement a thin trusted-host coordinator around:

- existing Platform V1 contracts, policy, authority, evidence and acceptance modules;
- installed `codex` for code execution;
- installed `git` for isolated worktrees and commits;
- installed `gh` for Issue/PR publication and workflow observation;
- SQLite from the Python standard library for persistent run state.

The coordinator is the product-specific middle layer. Codex, Git and GitHub remain replaceable adapters.

OpenHands live transport, Temporal, a custom Web UI, multi-executor routing and production deployment are deferred. Their future adoption must not require changing the core task, executor, publication or evidence interfaces.

## 3. Components

### 3.1 IssueTaskLoader

Reads one GitHub Issue using structured `gh` output and extracts exactly one machine-readable task block. It validates repository identity, base, branch, risk, paths, required checks, retry bounds and forbidden operations.

It rejects closed Issues, wrong repositories, main-target branches, root-wide path globs, unrestricted shell text, merge or deployment authority, and credential publication.

### 3.2 SQLiteRunStore

Persists one row per execution and an append-only transition/event table. The execution identity is derived from repository, Issue number, normalized task digest and exact base.

The store owns idempotency, attempt count, state, branch, worktree, Codex session/process reference, commit SHA, PR number, workflow observations and terminal classification.

Every external side effect is preceded by a persisted intent transition and followed by reconciliation against Git or GitHub truth.

### 3.3 GitWorktreeManager

Creates a deterministic worktree and task branch from the approved base. It can reconcile an existing matching worktree, but fails closed on unrelated dirt, branch mismatch, base drift or another active execution.

It never rebases, amends, resets another task, force-pushes or pushes main. Failed worktrees are retained by default for audit.

### 3.4 CodexExecutorAdapter

Discovers the installed Codex interface from `codex --version` and `codex exec --help`. It selects the highest supported non-interactive workspace permission compatible with the task safety boundary.

The adapter supplies a complete task prompt containing goal, exact allowed paths, required checks, forbidden operations, publication boundary and stop conditions. It captures exit status, elapsed time and bounded sanitized output metadata.

A fake adapter provides deterministic success, failure, timeout and malformed-output tests without model use.

### 3.5 LocalValidationRunner

Runs only approved task checks plus the relevant Platform V1 scoped suites. It records command, exit code, timeout and bounded output hashes. It never accepts caller-supplied pass/fail booleans.

The legacy repository-wide suite is diagnostic for this slice. A timeout is `INFRASTRUCTURE_TIMEOUT`, not semantic rejection.

### 3.6 GitHubPublicationAdapter

Reconciles branch and PR state before each write. It performs normal push, creates or converts exactly one Draft PR, records exact head identity and refuses mark-ready, merge, auto-merge, direct-main push, force-push, release and deployment.

### 3.7 WorkflowObserver and FailureClassifier

Reuses the existing exact-head GitHub workflow adapter. It records strict workflow truth and classifies success, product failures, policy failures, known external gate blockers, stale heads, infrastructure timeouts and transient GitHub errors.

The current B3 State Gate copy-heuristic defect is classified as a known external blocker. Product code must not be repeatedly modified to chase that external failure.

### 3.8 PlatformV1Coordinator

Owns the durable state machine:

```text
DISCOVERED
→ VALIDATED
→ WORKSPACE_READY
→ EXECUTOR_RUNNING
→ EXECUTOR_FINISHED
→ LOCAL_VALIDATED
→ COMMITTED
→ PUSHED
→ DRAFT_PR_OPEN
→ WORKFLOWS_OBSERVED
→ READY_FOR_HUMAN
```

Alternative terminal or recoverable states are:

```text
REWORK_REQUIRED
BLOCKED_EXTERNAL
FAILED_TERMINAL
CANCELLED
```

`resume` is safe from every boundary. Unchanged reruns return the existing execution, branch and PR.

## 4. Recovery Policy

The default implementation/rework limit is two Codex attempts. One additional retry is allowed for a classified infrastructure timeout or transient GitHub failure.

No retry is permitted for credential-policy violations, forbidden operations, base drift, branch identity mismatch, unbounded path authority or attempts to publish to main.

A product test failure may return to `REWORK_REQUIRED`, invoke Codex with structured failure evidence, rerun failed scoped checks and add normal fix-forward commits. The coordinator must not use zero-repair governance for ordinary product integration.

## 5. CLI

Extend the existing machine-readable Platform V1 CLI with cohesive commands equivalent to:

```text
run-e2e
resume
status
cancel
```

Inputs identify repository, Issue number and workspace root. Authority, checks and branch details are loaded from GitHub/repository state. Output is canonical JSON with stable exit codes.

## 6. Data and Secret Handling

Runtime SQLite and event data live under an untracked configurable runtime directory. Evidence stores bounded structured facts and hashes, not full environment dumps or credentials.

The live Codex and `gh` processes may use the trusted host's existing authenticated sessions. Repository code must not locate, read, print, copy, persist or upload the underlying credential material.

## 7. Testing

Provider-free tests cover:

- Issue task parsing and rejection cases;
- stable task/execution identity;
- state transitions and restart recovery;
- duplicate branch and PR prevention;
- worktree reconciliation;
- fake Codex success, failure, timeout and malformed output;
- secret redaction;
- scoped check outcomes and timeout classification;
- publication dry-run and fake GitHub behavior;
- resume from every side-effect boundary;
- CLI JSON and exit codes;
- one fake end-to-end run reaching `READY_FOR_HUMAN`.

Blocking local suites are the focused Platform V1, Supervisor/repository-hygiene and baseline-document suites plus `git diff --check`. The full repository suite remains visible as a diagnostic.

## 8. Live Canary

After provider-free validation, run the coordinator against Issue #115. The coordinator must create the exact approved file in an isolated branch, run the two required checks, commit, push, create one Draft PR, observe exact-head workflows and prove a second identical invocation creates no duplicate PR.

The canary may end in `BLOCKED_EXTERNAL` if the known B3 State Gate defect appears, but it must reach `DRAFT_PR_OPEN` and `WORKFLOWS_OBSERVED` with complete evidence.

## 9. Acceptance

The implementation is accepted for Owner review when:

1. scoped deterministic suites pass;
2. restart recovery and idempotency are demonstrated;
3. a fake end-to-end run reaches `READY_FOR_HUMAN`;
4. the live #115 canary creates one tested Draft PR;
5. a second run reuses the same execution and PR;
6. exact-head workflows are recorded and classified;
7. no secrets or environment dump appear in code, logs or GitHub evidence;
8. the implementation PR remains Draft and unmerged.

Terminal status:

```text
PLATFORM_V1_CODEX_E2E_DRAFT_PR_LOOP_COMPLETE
```

## 10. Safety Boundary

Always forbidden:

- direct push to main;
- merge, mark-ready or auto-merge;
- force-push or history rewrite;
- release, deployment, tag or package publication;
- credential extraction, printing or persistence;
- mutation of PR #106;
- rerun of historical State Gate run `30917109303`;
- closure of unrelated Issues or PRs.

Within this boundary, Codex may inspect the repository, choose implementation details, add normal commits, use the installed toolchain, create worktrees, push task branches, create Draft PRs, inspect CI and continue through bounded recovery until acceptance or a genuine terminal blocker.
