# Conditional operating reference

Companion to [AGENTS.md](../../AGENTS.md), not new execution authority. Read the section for the current action; do not preload the whole document for a small edit. The existing approval, risk, validation and landing predicates are unchanged.

## Product boundaries

Nerelan's thin adapter layer is `reverse_agent/platform_v1/`. Reuse GitHub Spec Kit-compatible planning, LangGraph topology/checkpoints, OpenCode repository execution/model bindings and OpenHands presentation patterns; do not copy their runtimes or replicate GitHub Issue/PR state.

The trusted host owns one TaskStore database for task, goal, window, receipt, claim, run and publication truth. The unattended coordinator requires `REVERSE_AGENT_AUTONOMOUS=1` and an owner-activated bounded window before doing work. Live model/API probes require separate explicit R3 authority. Provider-free startup and CI make zero model calls. The runtime/module/environment names above remain compatibility identifiers, not a request for a broader rename.

## Path A

Use only for ordinary R0/R1. A template-created Issue is CANDIDATE until a repository owner/maintainer reviews it and applies `r1-approved`. Verify who applied the label, not just its presence. Normalize the approved Issue body and compute its SHA-256; record repository, Issue, approval state/approver/event, digest, immutable observation reference, Work Item identity, exact branch/base and current head in the Draft PR body.

The approved body, exact digest, allowed paths, forbidden operations, acceptance criteria, target branch, `integration_base_ref` and `base_sha` jointly define the snapshot. The immutable observation reference is the body digest unless a stronger GitHub immutable revision exists. A planning branch is valid only when explicitly approved; never silently substitute main. Comments do not override the snapshot. Material Issue-body edits invalidate it and require owner/maintainer reapproval plus a new snapshot.

Activation is a fresh exact-base branch, one tree-identical empty activation commit, then exact-branch push and a Draft with the complete snapshot before any product/source/test change. Arbitrary seed-file changes are not bootstrap. Rebind `exact_head_sha` after each implementation push; a transient synchronization check against the old head is not final evidence. Verify the live PR base ref, base SHA and merge-base against the snapshot. If the base differs, stop; obtain a revised/reapproved Work Item and a fresh branch. No Path-A history rewrite.

Do not load the legacy Decision/state stack for this path. Ordinary R1 authorization does not permit workflow, dependency, authority-surface, provider, credential, binary, destructive or unbounded publication changes merely because their diff is small.

## Path B

Use only when the task's risk or transition contract requires it. Resolve the bounded APPROVED Decision, its exact base/branch/path/operation grants, required surfaces and active skill profiles. The activated Decision is immutable; never repair an active contract in place or treat an Issue/comment as a replacement.

The existing transition sequence is:

```text
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre
```

Follow the actual bounded contract and generated plan, including bootstrap exceptions and evidence provenance. Require `PRE_EXECUTION_AUTHORIZED` before implementation; do not execute omitted or unauthorized commands. Generated artifacts are evidence, not an independent grant. Failed validation, inconsistent authority or unavailable required capability blocks the affected action. A different execution surface must itself be authorized; a local failure cannot be renamed CI success.

Do not universally substitute the older `preflight`/`command-plan` legacy sequence for the transition kernel. Legacy report/closeout requirements apply only when the active task selects that contract; see [legacy project-state reference](../prompts/legacy-project-state-reference.md).

## Delegated controller authority

An explicit Owner-to-controller handoff can include authority to select and approve the next Work Item. An ordinary request to implement a feature, an Issue comment, a roadmap or an Agent's own plan does not establish that delegation. Preserve the original Owner instruction and its identity in existing execution evidence. Record the repository/goal/capability envelope, expiry or renewal rules, aggregate operation/retry/cost allowances and revocation conditions before using it. An absent capability or budget is not permission to infer a privileged side effect.

The controller acts as a delegated approver, not as the human Owner or the independent auditor. Use the existing `approved_by`, `approval_basis` and `approval_event_or_time` fields to make that distinction explicit. Do not add a new authority store, approval Gate or self-issued independent acceptance receipt. Path A's reviewed Issue/label/digest rules are unchanged; use Path B for a delegated transition authorization.

For each selected slice:

1. Observe live ownership, repository, integration ref and exact base. Reuse existing work without taking another active owner's task. Base drift requires a separately scoped recovery; it never silently changes an old snapshot or licenses history rewriting.
2. Bind exact allowed paths, operation/surface capabilities, required checks, branch/base/head, expiry and cumulative retry/spending limits in a new Decision. Cite the recorded delegation as the approval basis and identify the actual controller approver. A successor of failed work retains that failure and consumes the applicable correction allowance.
3. Commit only the permitted Decision bootstrap, generate the existing command plan and obtain `PRE_EXECUTION_AUTHORIZED` before implementation. A compiler rejection is a real failure. Preserve its immutable Decision and evidence; a corrected successor is permitted only within the recorded delegation and allowances. Never modify the compiler or judge merely to admit a rejected request.
4. Charge operations before executing them. Carry forward the original absolute expiry and aggregate spending when renewing the same grant. If the standing delegation permits a new allocation, append its distinct authorization and allowance without resetting or relabeling prior consumption. Otherwise park the affected slice.
5. Execute and verify through the real platform where the needed capability is available. If unavailable, retain observed capability/runtime evidence and use the authorized alternate executor. Keep Task/Goal data, model use, actual runtime provenance and functional acceptance separate.
6. Publish only through the exact permitted path. Delegated authorization does not supply an independent review, turn a Draft into Ready, or invoke the personal human R1 merge carve-out. Agent landing still needs separately applicable Path-B capabilities, exact-head checks, independent acceptance and immediate external-state observations.

Failure or exhaustion of one operation does not automatically exhaust unrelated Work Items inside the delegation. Select the next eligible slice, checkpoint a blocked one, and resume only after its relevant condition changes. If no authorized useful action remains, record the exact blocker without repeated confirmation requests, unchanged polling or claims of background execution. Owner revocation and window-wide hard stops take precedence over successor selection.

This workflow removes repeated interactive approval for covered authorization decisions. It does not assert that a durable unattended scheduler, arbitrary coding executor, GitHub merge/release adapter or deployment adapter has been implemented or accepted. Those product capabilities remain separately testable Work Items under #118.

## Worktree guards

Observe the startup baseline before edits. Do not delete, restore, hide or stage anything while classifying it.

| Class | Meaning and action |
| --- | --- |
| AUTHORIZED_TRACKED_DELTA | Tracked change inside the exact approved allowlist; only normally stageable class. |
| KNOWN_RUNTIME_SCRATCH | Untracked `task_workspaces/` or `.platform_v1_runtime/` content; non-blocking and non-stageable. |
| GENERATED_GOVERNANCE_ARTIFACT | Generated `project_state/gates/` content; non-stageable without an explicit separate grant. |
| UNKNOWN_UNTRACKED | Preserve it; read-only bootstrap is allowed, publication waits for owner/authority resolution. |
| UNAUTHORIZED_TRACKED_OR_SENSITIVE | Stop immediately; never stage it. |

Classification grants no reset, clean, stash, restore, deletion or broad staging. `startup-snapshot` machine-enforces bootstrap classification.

For ordinary R1 local readiness:

```text
python -m reverse_agent.project_gate worktree-r1-publication-readiness --issue-body-file <approved-issue-body-file> --pr-body-file <draft-pr-body-file>
```

Store these frozen inputs outside the repository. The guard derives allowed paths from the approved Issue body and checks its digest, branch/base/head/merge-base and worktree classes. It does not replace live label provenance, owner permission, Issue/PR state, auto-merge or authority-revision checks; GitHub State Gate remains the final live verification.

For applicable Path-B product staging/publication:

```text
python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state
```

Require `PUBLICATION_READY`. An authorized remote/CI checkout and its real evidence must be distinguished from user-local work and from a partial materialization.

## Landing

The personal owner/maintainer R1 carve-out in AGENTS requires every snapshot/digest/approval, fresh-base, allowed-path, local exact-head check, successful exact-head Actions, independent audit and resolved-thread predicate. Immediately reobserve remote integration ref and `baseRefOid` against `base_sha`, `headRefOid` against the audited head, MERGEABLE, CLEAN, CI SUCCESS and no concurrent publication/mutation.

Then personally mark-ready and immediately merge with merge method `merge` and expected-head protection; verify merged state, recorded merge commit and new remote integration ref before closing the source Issue. GitHub UI use has no universal local clean-tree requirement; an owner-controlled CLI must prevent accidental commit, push, branch mutation or unrelated changes. Personal `gh pr merge` can qualify, but an Agent invoking the same account/CLI does not.

Agent-, automation-, workflow-, scheduled-, delegated- and service-initiated landing remains Path B, as do auto-merge and every R2/R3 landing. Any failed personal R1 predicate excludes the carve-out. A self-audit or a Draft with passing tests is not independent acceptance.
