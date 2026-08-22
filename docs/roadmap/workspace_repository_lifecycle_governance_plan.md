# Workspace & Repository Lifecycle Governance Roadmap

```text
STATUS: LONG_TERM_CAPABILITY_PLAN
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
OWNER: reverse-agent mother platform
```

## 1. Goal

`reverse-agent` must not depend on each Agent remembering to clean up after itself.

Long-running unattended engineering naturally creates temporary and historical state:

```text
Git worktrees
local task workspaces
runtime scratch directories
build/test caches
local branches
remote branches
failed or interrupted execution directories
logs and intermediate artifacts
superseded plans and compatibility files
tracked source that has become unreachable or obsolete
```

Without explicit lifecycle governance, these accumulate until local storage, repository history, and the developer mental model become polluted. Cleanup must therefore be a platform capability with durable state, evidence-backed eligibility, retention policy, reconciliation after crashes, and fail-closed deletion rules.

The platform capability is named:

**Workspace & Repository Lifecycle Governance / 工作区与仓库生命周期治理**.

Its objective is not aggressive deletion. Its objective is to make every temporary execution asset explainably live, retained, cleanup-eligible, blocked, historical, or removed, and to make repository dead-asset findings evidence-backed rather than guesswork.

## 2. Existing starting point

This plan extends existing repository behavior instead of replacing it.

### 2.1 Existing worktree classification

`reverse_agent/control_plane/worktree_state.py` already classifies observed paths into bounded categories such as:

```text
AUTHORIZED_TRACKED_DELTA
KNOWN_RUNTIME_SCRATCH
GENERATED_GOVERNANCE_ARTIFACT
UNKNOWN_UNTRACKED
UNAUTHORIZED_TRACKED_OR_SENSITIVE
```

That module intentionally performs classification only. It does not delete, restore, stage, stash, reset or otherwise mutate a worktree. This remains a good boundary: classification is evidence; cleanup authority is a separate concern.

### 2.2 Historical repository hygiene

The repository has already required dedicated hygiene work to inventory and remove many clean obsolete worktrees while preserving dirty or uncertain ones. The stable lessons from that work remain permanent:

- a worktree is not deletable merely because it looks old;
- a branch is not deletable merely because a PR closed;
- dirty or locked worktrees are never force-removed by default;
- remote branch deletion requires per-branch evidence;
- unpreserved unique history blocks automatic deletion;
- unknown provenance is a blocker, not permission to clean.

The future platform turns these one-off manual principles into a durable lifecycle model.

### 2.3 Existing durable execution truth

TaskStore/control-store already owns task, run, claim, lease, budget, goal, window, evidence and publication truth. Lifecycle governance must consume these facts rather than create a second execution state machine.

## 3. Governing principles

The permanent rules are:

1. **Creation implies registration.** Every platform-created worktree or durable task workspace receives a lifecycle record at creation time.
2. **Terminal is not deletable.** Task completion, PR closure, elapsed time or lease expiry alone never proves cleanup safety.
3. **Evidence before mutation.** Cleanup requires an explainable eligibility record produced from current facts.
4. **Unknown fails closed.** Dirty state, unknown provenance, ambiguous ownership, unexpected files or unverified history blocks automatic deletion.
5. **Evidence outlives workspace.** Audit artifacts are preserved independently so temporary execution state can eventually die.
6. **Reconciliation does not depend on graceful Agent exit.** Crash recovery must find abandoned workspaces after the process that created them is gone.
7. **Automatic deletion is narrow.** Only explicitly disposable or gate-proven assets may be auto-removed.
8. **Tracked product retirement is proposal-driven.** Dead-source analysis may propose deletion but does not silently edit the repository.
9. **No wildcard destructive cleanup.** Bulk cleanup operates over individually classified records and records a receipt for each mutation.
10. **Reuse mature Git/filesystem primitives.** The repository should own policy and evidence, not reinvent Git worktree mechanics or generic disk cleanup.

## 4. Architectural placement

Target direction:

```text
Task / Goal / Run
      |
      v
Workspace Lifecycle Manager
      |
      +--> Workspace Registry -----------+
      |                                  |
      +--> Git worktree observation      |
      +--> TaskStore / RunStore truth    |
      +--> claim / lease / publication   |
      +--> GitHub PR / branch truth      |
      |                                  |
      v                                  |
Cleanup Eligibility Gate                |
      |                                  |
      +--> RETAIN / BLOCKED / ELIGIBLE --+
      |
      v
Bounded Cleanup Executor
      |
      +--> per-asset cleanup receipt
      +--> evidence preserved separately

Repository tree
      |
      v
Dead Asset Analyzer
      |
      v
Evidence-backed RETIRE_CANDIDATE
      |
      v
ordinary governed Work Item / review
```

The Workspace Registry is lifecycle metadata associated with existing execution truth. It must not become another scheduler or another task source of truth.

## 5. Workspace Registry contract

Every workspace created by the platform should eventually have a durable record conceptually equivalent to:

```yaml
workspace_id: ws-...
workspace_kind: git_worktree | task_workspace | runtime_scratch
path: F:/...
repository: dddd2024/reverse-agent

owner:
  goal_id: goal-...
  task_id: task-...
  run_id: run-...
  execution_id: exec-...
  agent_or_role: coder

git:
  branch: owner/example
  base_sha: ...
  observed_head_sha: ...
  remote_ref: origin/owner/example

publication:
  pr_number: 123
  pr_state: OPEN | CLOSED | MERGED | UNKNOWN

lifecycle:
  state: ACTIVE
  created_at: ...
  last_active_at: ...
  retention_until: ...
  cleanup_class: GATE_REQUIRED

observations:
  clean: false
  locked: false
  unknown_untracked_count: 0
  unique_unpreserved_commits: 0
  active_claim: false
  active_lease: false
  active_process_known: false

cleanup:
  eligibility: BLOCKED
  reason_codes:
    - WORKTREE_DIRTY
  last_evaluated_at: ...
  removed_at: null
```

Exact schema may change during implementation. The following properties are non-negotiable:

- identity and path;
- owning task/run/goal when known;
- Git branch/base/head when applicable;
- creation and last-activity time;
- lifecycle state;
- current dirty/lock/unknown state;
- retention deadline or explicit indefinite retention;
- cleanup eligibility and bounded reason codes;
- cleanup receipts after mutation.

Secrets, raw prompts, credentials and unrestricted logs do not belong in the registry.

## 6. Workspace lifecycle

Target finite lifecycle:

```text
CREATING
   |
   v
ACTIVE
   |
   +--> BLOCKED_DIRTY
   +--> BLOCKED_UNKNOWN
   +--> ORPHANED
   |
   v
IDLE
   |
   v
RETENTION
   |
   +--> KEEP_EVIDENCE
   +--> BLOCKED_DIRTY
   +--> BLOCKED_UNKNOWN
   |
   v
CLEANUP_ELIGIBLE
   |
   v
REMOVING
   |
   v
REMOVED
```

Interpretation:

- `CREATING`: workspace creation started but registration/setup is not complete.
- `ACTIVE`: current durable execution owns the workspace.
- `IDLE`: no current execution activity, but retention/verification has not completed.
- `RETENTION`: intentionally preserved for a bounded debugging/audit period.
- `CLEANUP_ELIGIBLE`: current evidence proves bounded removal is permitted.
- `REMOVING`: one cleanup attempt owns the mutation.
- `REMOVED`: physical workspace is absent and a durable receipt exists.
- `ORPHANED`: local workspace exists but no live execution owner can be confirmed.
- `BLOCKED_DIRTY`: tracked or unknown local content prevents automated cleanup.
- `BLOCKED_UNKNOWN`: provenance, Git history, ownership or external state is insufficiently known.
- `KEEP_EVIDENCE`: workspace is retained because required evidence has not yet been externalized or retention policy explicitly requires it.

`ORPHANED` is not synonymous with deletable. It must pass the same Cleanup Eligibility Gate.

## 7. Cleanup Eligibility Gate

Automatic worktree/workspace cleanup is permitted only when all applicable requirements are proven at mutation time.

Conceptual gate:

```text
no active Task/Run execution ownership
AND no active coordinator claim
AND no active durable lease
AND no known active executor/process ownership
AND no pending publication mutation
AND retention deadline satisfied
AND required artifacts/evidence externalized
AND path identity still matches registry
AND worktree not locked
AND tracked tree is clean
AND no unknown untracked/sensitive content
AND no unpushed or otherwise unpreserved unique commits
AND branch/PR state is compatible with retention policy
AND no authority record still requires the workspace
```

The gate returns a finite decision:

```text
ELIGIBLE
RETAIN_ACTIVE
RETAIN_POLICY
BLOCKED_DIRTY
BLOCKED_LOCKED
BLOCKED_UNKNOWN_CONTENT
BLOCKED_ACTIVE_CLAIM
BLOCKED_ACTIVE_LEASE
BLOCKED_PUBLICATION
BLOCKED_UNPRESERVED_HISTORY
BLOCKED_EVIDENCE_NOT_EXTERNALIZED
BLOCKED_PROVENANCE
BLOCKED_AUTHORITY_REFERENCE
```

The mutation path must repeat safety observations immediately before deletion. A stale dashboard result is advisory only.

### 7.1 Facts that are explicitly insufficient

None of the following proves deletion safety by itself:

```text
task status is terminal
Goal is completed
PR is closed
PR is merged
branch name contains old / v1 / tmp
workspace has not changed recently
claim or lease expired
Agent process disappeared
CI passed
```

These may be inputs, never sole authorization.

## 8. Three cleanup classes

### Level 1 — automatically disposable

Examples:

```text
explicit platform cache entries
bounded temporary downloads
known generated scratch with no evidence role
expired build/test cache under an owned cache root
```

Requirements:

- location is inside an explicitly owned disposable root;
- the asset has no authority/evidence role;
- deletion cannot remove tracked repository data;
- size/path observation is bounded;
- cleanup receipt is emitted.

### Level 2 — gate-proven workspace cleanup

Examples:

```text
platform-created Git worktree
platform-created task workspace
.platform_v1_runtime task/run directory
```

These require the full Cleanup Eligibility Gate. `--force` is not the normal path.

### Level 3 — proposal-only retirement

Examples:

```text
tracked source files
compatibility modules
roadmap/history documents
remote branches with unique history
persistent evidence
schema/database history
```

The hygiene subsystem may classify these as candidates and produce evidence, but actual removal requires a separately governed repository Work Item or explicit authority appropriate to the risk.

## 9. Retention policy

Retention should be configurable through named profiles rather than hidden constants.

Conceptual profiles:

```text
CONSERVATIVE
BALANCED
AGGRESSIVE
CUSTOM
```

A possible `BALANCED` policy target is:

```text
successful + safely published/merged clean workspace: 24 hours
failed clean workspace: 3 days
blocked workspace: retain until blocker resolution, then policy clock starts
interrupted/recoverable workspace: retain while recovery remains possible
known disposable cache: short bounded TTL
dirty / locked / unknown provenance: manual or separately governed resolution
required evidence: preserve independently according to evidence policy
```

The exact durations are product configuration, not authority. A short TTL cannot bypass the Cleanup Eligibility Gate.

## 10. Crash-independent Workspace Reconciler

A cleanup hook in `finally:` is insufficient because the process can crash before it runs.

The platform therefore needs a reconciler that periodically and on startup compares:

```text
Git worktree list / filesystem observations
        +
Workspace Registry
        +
TaskStore / RunStore / durable checkpoints
        +
claims / leases / budget reservations
        +
publication records
        +
GitHub PR / branch truth when authorized and available
```

The reconciler classifies each observed workspace into states such as:

```text
REGISTERED_ACTIVE
REGISTERED_IDLE
REGISTERED_RETENTION
ORPHANED_LOCAL
STALE_REGISTERED
DIRTY_ORPHAN
CLEANUP_ELIGIBLE
UNKNOWN
```

Examples:

```text
local worktree exists
registry exists
run active + lease fresh
=> REGISTERED_ACTIVE
```

```text
local worktree exists
registry owner absent
PR merged
clean
no unique commits
required evidence preserved
=> ORPHANED_LOCAL -> Cleanup Gate -> possible CLEANUP_ELIGIBLE
```

```text
local worktree exists
PR closed
working tree dirty
=> DIRTY_ORPHAN -> BLOCKED_DIRTY
```

Reconciliation is observational first. It must not convert discovery of an orphan into immediate deletion without the cleanup gate.

## 11. Artifact and evidence preservation

Workspace retention and evidence retention must be separate.

Target flow:

```text
workspace
  |
  +--> changed-file evidence
  +--> validation result
  +--> bounded command/log evidence
  +--> screenshots / reports / generated artifacts
  +--> publication references
          |
          v
Artifact / Evidence Store
          |
          v
Evidence manifest / durable references

workspace retention may then expire independently
```

A workspace cannot become `CLEANUP_ELIGIBLE` when it is the only known copy of required audit evidence.

Conversely, keeping every completed worktree forever must not be the platform's evidence strategy.

## 12. Repository Hygiene and Dead Asset Analyzer

Temporary workspace cleanup solves disk growth; tracked repository hygiene solves long-term architectural decay.

The platform should eventually classify tracked assets as:

```text
ACTIVE
COMPATIBILITY
GENERATED
HISTORICAL
DEPRECATED
RETIRE_CANDIDATE
UNKNOWN
```

### 12.1 Evidence sources

A dead-asset candidate should be supported by multiple available signals such as:

```text
static imports and references
call/symbol/reference graph
package exports
CLI / application entry points
HTTP/API route registration
workflow/runtime registration
configuration references
Pack / Skill / plugin references
tests and fixtures
documentation references
dynamic-loading declarations
replacement/supersession metadata
Git history and merged PRs
current architecture source-of-truth documents
```

File age alone is never proof of deadness.

### 12.2 Candidate record

Conceptual output:

```yaml
path: reverse_agent/legacy_component.py
classification: RETIRE_CANDIDATE
confidence: high
reasons:
  - no static imports
  - no runtime registration
  - no tests
  - architecture marks replacement as authoritative
replacement_refs:
  - reverse_agent/platform_v1/...
risk: MEDIUM
recommended_action: PROPOSE_REMOVAL
```

The analyzer must distinguish:

- provably unreferenced code;
- compatibility code intentionally retained;
- historical documentation intentionally retained;
- generated files governed by generation policy;
- uncertain dynamic references.

`UNKNOWN` is preferable to a false deletion claim.

### 12.3 Removal remains governed

A `RETIRE_CANDIDATE` does not grant mutation authority.

Expected flow:

```text
hygiene scan
-> evidence-backed candidate
-> Human Inbox / Autonomous Improvement candidate
-> ordinary specification / Work Item
-> bounded deletion/change
-> deterministic tests and repository checks
-> independent review
```

This makes repository hygiene auditable rather than destructive background behavior.

## 13. Branch lifecycle

Branch cleanup is related to workspace cleanup but is not identical.

A local/remote branch may remain useful after a worktree is removed. Remote-branch deletion requires its own evidence, including at minimum:

```text
not protected / not integration base
no open PR requires it
no active authority references it
current remote head matches the audited head
no linked dirty/locked workspace
head contained in accepted history OR unique history is otherwise preserved
```

The platform must not use wildcard branch deletion or delete branches based on naming convention or age.

Local branch removal and remote branch removal should emit distinct receipts.

## 14. User-facing storage and hygiene observability

The future frontend/System Doctor should make lifecycle state visible rather than silently deleting data.

Target summary:

```text
Storage & Hygiene

Worktrees                    17
Active                        3
Retention                     4
Cleanup eligible              6
Blocked dirty                 2
Orphan / unknown              2

Task/runtime workspaces    11.4 GB
Caches                       3.1 GB
Preserved artifacts         18.2 GB
Safe reclaimable             9.7 GB
```

For each cleanup-eligible workspace, the UI should be able to explain why:

```text
PR merged
no active task/run/claim/lease
worktree clean
no unknown files
no unpreserved unique commits
required evidence preserved
retention elapsed
```

Blocked entries should expose bounded explanations without leaking secrets or raw environment data.

User actions may eventually include:

```text
Clean safe items
Re-evaluate blocked item
Keep longer
Open evidence
Open associated Run / Goal / PR
```

A user-facing action must still invoke the server-side cleanup gate; the browser cannot fabricate eligibility.

## 15. Autonomous Improvement Loop integration

Long-term autonomous improvement may consume hygiene findings as candidate work.

Allowed direction:

```text
periodic hygiene observation
-> candidate dead assets / structural debt
-> evidence + expected benefit
-> candidate Goal / Inbox item
-> normal governed planning and approval
```

Forbidden direction:

```text
hygiene scanner decides a tracked file is old
-> silently deletes it
-> pushes/merges cleanup
```

Autonomy may improve discovery frequency, not bypass authority.

## 16. Phased implementation plan

### Phase L0 — lifecycle inventory and contract audit

Inventory all current creators/consumers of:

```text
Git worktrees
workspace_root / task_workspaces
.platform_v1_runtime
OpenCode workspaces
local branches
runtime caches
artifact/evidence paths
```

Map which system currently owns creation, activity, termination and retention. No deletion behavior changes.

Acceptance:

- every current workspace-producing path is identified;
- ownership gaps and duplicate roots are recorded;
- current hygiene rules are mapped rather than reimplemented blindly.

### Phase L1 — Workspace Registry and lifecycle contracts

Add the minimum durable lifecycle metadata using the existing trusted store where appropriate.

Acceptance:

- every newly platform-created durable workspace is registered;
- registry identity is idempotent;
- no secrets/raw prompts are persisted;
- lifecycle state does not duplicate task execution state.

### Phase L2 — read-only Reconciler and Cleanup Eligibility evaluation

Implement observation/classification without deletion.

Acceptance:

- registered active, idle, orphaned, stale, dirty and unknown cases are deterministic;
- cleanup eligibility returns finite reason codes;
- dirty/unknown/unique-history cases fail closed;
- repeated reconciliation is zero-destructive.

### Phase L3 — bounded cleanup executor for Level 1 and Level 2 assets

Enable narrow deletion only after proven eligibility.

Acceptance:

- path is revalidated immediately before mutation;
- no wildcard or force-default cleanup;
- each removed asset has a cleanup receipt;
- concurrent/repeated cleanup is idempotent;
- failures cannot partially rewrite unrelated workspace state;
- required evidence survives workspace removal.

### Phase L4 — retention profiles and storage accounting

Add configurable retention plus size/reclaimability observations.

Acceptance:

- TTL never bypasses safety gates;
- user policy can keep eligible assets longer;
- reclaimable size is clearly distinguished from total size;
- unknown size/state is explicit.

### Phase L5 — Repository Hygiene / Dead Asset read-only analyzer

Add evidence-backed candidate discovery with no source deletion.

Acceptance:

- age alone cannot produce `RETIRE_CANDIDATE`;
- static/dynamic uncertainty is represented;
- compatibility/historical assets can be intentionally retained;
- findings include evidence and replacement references where known.

### Phase L6 — Hygiene UI and manual safe cleanup

Expose lifecycle/storage truth in the existing product surfaces.

Acceptance:

- browser receives sanitized server-owned eligibility;
- safe cleanup requires confirmation and re-evaluation at mutation time;
- blocked items explain why;
- no frontend-owned cleanup state machine exists.

### Phase L7 — recurring hygiene observation and autonomous candidate generation

Run bounded reconciliation/hygiene checks periodically and feed tracked-asset findings into the normal candidate-work pipeline.

Acceptance:

- recurring checks do not silently mutate tracked repository content;
- cleanup of Level 1/2 assets remains policy/gate bounded;
- tracked/remote-history changes still require normal authority.

## 17. Measurable complete-capability criteria

The capability is complete only when the platform can demonstrate all of the following:

1. every platform-created worktree/workspace has a durable owner/lifecycle identity;
2. a crash cannot permanently hide an orphan from later reconciliation;
3. task/PR terminality alone never authorizes deletion;
4. dirty, locked, unknown-provenance and unpreserved-history workspaces fail closed;
5. evidence needed for audit survives removal of temporary workspaces;
6. cleanup decisions expose bounded reason codes and current evidence;
7. repeated cleanup is idempotent and cannot delete outside owned roots;
8. wildcard/force-default destructive cleanup is absent;
9. storage accounting distinguishes active, retained, blocked and safely reclaimable state;
10. repository dead-asset findings use reference/runtime/test/config/history evidence rather than age alone;
11. tracked-source and remote-history removal are proposal-driven and separately governed;
12. frontend visibility is derived from server truth and cannot widen cleanup scope;
13. cleanup/reconciliation reuse existing TaskStore/worktree/governance truth instead of creating another execution authority;
14. automatic cleanup materially bounds long-term worktree/workspace accumulation during sustained unattended operation.

## 18. Permanent boundaries

Do not:

- use `git clean`, `reset --hard`, stash, restore or filesystem recursion as a generic way to manufacture a clean repository;
- force-remove dirty/locked worktrees merely because a task ended;
- infer process death from an expired claim/lease alone;
- delete local or remote branches because of name or age;
- delete unpreserved unique history automatically;
- delete tracked source because it has not changed recently;
- treat closed/merged PR state alone as cleanup permission;
- make the browser a cleanup authority;
- put secrets/raw prompts into lifecycle records;
- preserve every worktree forever merely to retain evidence;
- create a second scheduler or second Task/Run source of truth;
- let an autonomous hygiene scanner directly push/merge tracked-source deletion.

## 19. Architectural decision summary

Fixed direction:

```text
Turn cleanup from Agent etiquette into platform lifecycle governance.
Register every platform-created workspace.
Reconcile after crashes and during normal operation.
Separate observation, eligibility and mutation.
Fail closed on dirty/locked/unknown/unpreserved state.
Preserve evidence independently from temporary workspaces.
Automatically clean only narrow disposable or gate-proven assets.
Treat tracked repository cleanup as evidence-backed candidate work.
Expose lifecycle and reclaimable storage to the user.
Integrate hygiene discovery with autonomous improvement without granting destructive authority.
```

This capability is infrastructure required for a mother platform expected to run unattended for long periods. Without it, successful automation eventually creates its own operational debt.