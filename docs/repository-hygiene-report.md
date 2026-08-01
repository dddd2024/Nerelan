# Repository Hygiene Report

Generated under Issue #92 (Repository hygiene + thin Codex Supervisor composition v0).

- Repository: `dddd2024/reverse-agent`
- Starting main: `16526801bda2a816fc707342f903c1ad037de9bd`
- Implementation branch: `agent/codex-supervisor-foundation-v0`
- Risk tier: R2 metadata cleanup + bounded R1 implementation
- Real Codex/model invocation: forbidden (quota-free)

## Disposition legend

Each remote branch, PR, worktree, and Issue is classified into exactly one
disposition. A branch is never deleted solely because its name, creation
time, or PR-closed status suggests so; deletion requires every condition in
Section V of Issue #92 to hold.

| Code | Meaning |
|------|---------|
| `KEEP_ACTIVE` | Branch/Issue is the current execution authority or has an open authority-binding PR. Do not close or delete. |
| `CLOSE_PR_KEEP_BRANCH` | Open Draft PR is superseded by the current project direction. Close the PR without merge. The branch is retained because it carries unique commits not in main. |
| `DELETE_REMOTE_SAFE` | Branch HEAD is fully contained in main (or unique history is preserved by a merged PR) and every deletion condition holds. Remote branch may be deleted after re-verification. |
| `KEEP_HISTORICAL_UNIQUE` | Branch has unique commits not in main and no merged PR preserves them. The remote branch is retained as historical reference. |
| `BLOCKED_DIRTY_WORKTREE` | A local worktree linked to this branch is dirty or locked. Cleanup is blocked until the worktree is resolved. |
| `BLOCKED_UNKNOWN_PROVENANCE` | Branch origin cannot be verified (no PR, no Issue reference, HEAD drifted since audit). Do not delete. |

## Before / after summary

| Metric | Before | After (recommended) |
|--------|--------|---------------------|
| Remote branches (excl. main) | 28 | 17 retained, 11 delete-safe |
| Open Draft PRs | 9 | 0 (all 9 superseded — close without merge) |
| Closed unmerged Draft PRs | 1 (#78) | 1 (already closed) |
| Open Issues | 36 | 4 retained, 32 close-completed or close-not-planned-superseded |
| Local worktrees (excl. main) | 9 | 8 removable, 1 blocked (dirty) |

Note: the "after" column records recommended dispositions. Actual R2
cleanup execution (closing PRs, deleting remote branches, closing Issues)
requires a bounded Path-B Decision per AGENTS.md. This report is the
evidence base for that Decision.

## Section II — net-zero main commit protection

Two commits form a corrected append-only pair:

| Commit | Action |
|--------|--------|
| `eeade58b87536c7a09ec9b972cae1f5535e385ba` | created an empty probe file |
| `16526801bda2a816fc707342f903c1ad037de9bd` | deleted the empty probe file |

Verified net file diff between `2aacf42dbab7f283454908da861b6ef44990f1d5`
and `16526801bda2a816fc707342f903c1ad037de9bd` is **empty** (no file
additions, modifications, or deletions).

These commits are recorded as corrected append-only history. They must NOT
be reverted, reset, force-pushed, or rewritten. No third "cleanup commit"
is created.

## Section III — remote branch inventory

Origin/main SHA: `16526801bda2a816fc707342f903c1ad037de9bd`

### Fully merged branches (head contained in main, 0 unique commits)

These branches have `head_in_main = true` and `unique_commit_count = 0`.
After confirming no open PR and no authority Issue references them, each is
`DELETE_REMOTE_SAFE`.

| Branch | HEAD | PR | PR state | Worktree | Disposition |
|--------|------|----|----------|----------|-------------|
| `agent/decision-closeout-final-seal-publication-truth-rework-v2` | `9a37f743` | #4 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/add-codex-skills` | `1be2bd05` | #1 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/architecture-spine-v1` | `43418818` | #9 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/control-plane-transition-kernel-v1` | `0dbdc3cb` | #8 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/executor-neutral-vertical-slice-v1` | `0ab750cf` | #60 | MERGED | `F:/reverse-agent-executor-neutral-vertical-slice-v1` (clean) | `DELETE_REMOTE_SAFE` |
| `codex/governance-migration-owner-manual-merge-v1` | `7c19e741` | #44 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/p0-minimal-integration-baseline-v1` | `e8074fa8` | #27 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/pr60-mainline-landing-repair-v2` | `4d28cbfb` | #67 | MERGED | `F:/reverse-agent-pr60-mainline-landing-repair-v2` (clean) | `DELETE_REMOTE_SAFE` |
| `codex/readme-minimal-integration-pilot-v1` | `4ce3c19b` | #38 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `codex/run-closeout-legacy-doc-pilot-v1` | `16a32acc` | #41 | MERGED | — | `DELETE_REMOTE_SAFE` |
| `feature/training-materials-corpus` | `4808ca5e` | #3 | MERGED | — | `DELETE_REMOTE_SAFE` |

### Branches with unique commits and open Draft PRs

These branches carry code not in main. Their open Draft PRs are superseded
by the current project direction (Codex Supervisor v0, Issue #92). The
recommended action is: close the PR without merge, then retain the branch
as `KEEP_HISTORICAL_UNIQUE` because the unique commits are not preserved by
any merged PR.

| Branch | HEAD | Unique commits | PR | PR title | Worktree | Disposition |
|--------|------|----------------|----|----------|----------|-------------|
| `agent/architecture-constitution-plan-v1` | `d500c145` | 15 | #11 | Replace blocked P0 authority with gate-compatible Decision | `F:/reverse-agent-p0` (clean) | `CLOSE_PR_KEEP_BRANCH` |
| `agent/terminal-status-propagation-seal-restart-rework-v3` | `6a286746` | 44 | #5 | engineering: consumed-decision CI preflight parity rework | — | `CLOSE_PR_KEEP_BRANCH` |
| `codex/base-platform-m1-spec-policy-core-v1` | `6e096b11` | 2 | #47 | M1: implement versioned SpecPackage and Policy Resolver core | `F:/reverse-agent-issue46` (clean) | `CLOSE_PR_KEEP_BRANCH` |
| `codex/legacy-control-plane-transition-disposition-v1` | `7cd75fca` | 2 | #7 | governance: disposition legacy control plane transition | — | `CLOSE_PR_KEEP_BRANCH` |
| `codex/path-a-r1-state-gate-cutover-v1` | `40400440` | 8 | #49 | R2: add Path-A R1 State Gate and task-scoped exact-head CI | `F:/reverse-agent-path-a-r1-state-gate-cutover-v1` (clean) | `CLOSE_PR_KEEP_BRANCH` |
| `codex/p1a-current-merge-validation-v2` | `976fb860` | 3 | #21 | P1A: bind mainline checks to current merge | — | `CLOSE_PR_KEEP_BRANCH` |
| `codex/p1a-v3-exact-head-external-approval` | `4baa1c61` | 5 | #24 | feat(governance): v3 exact-head external merge approval gate | — | `CLOSE_PR_KEEP_BRANCH` |
| `codex/stage-a-freeze-baseline-v1` | `38a0a934` | 3 | #19 | fix(governance): freeze Architecture Spine main integration baseline | `F:/reverse-agent-stage-a` (clean) | `CLOSE_PR_KEEP_BRANCH` |
| `plan/framework-adoption-control-plane-v1` | `4e1e0008` | 8 | #6 | plan: transition workflow cutover and CI test bootstrap | — | `CLOSE_PR_KEEP_BRANCH` |

After PR closure, each branch above becomes `KEEP_HISTORICAL_UNIQUE`.

### Branches with unique commits and no open PR

| Branch | HEAD | Unique commits | PR history | Worktree | Disposition |
|--------|------|----------------|------------|----------|-------------|
| `codex/material-hook-runtime-validation` | `d689c28f` | 1 | #2 MERGED (squash) | — | `KEEP_HISTORICAL_UNIQUE` |
| `codex/p1a-v2-premerge-authorization` | `708aeefa` | 3 | no PR found | — | `BLOCKED_UNKNOWN_PROVENANCE` |
| `codex/pr60-final-merge-authorization-v1` | `7e2ef47b` | 2 | no PR found | `F:/reverse-agent-pr60-final-merge-authorization-v1` (clean) | `KEEP_HISTORICAL_UNIQUE` |
| `codex/unattended-base-platform-v0` | `bc9ac0fd` | 66 | #78 CLOSED (not merged) | `F:/reverse-agent-issue82-gate2-runtime-proof-v6` (clean, local HEAD `ca79b53e` differs from remote) | `KEEP_HISTORICAL_UNIQUE` |
| `plan/governance-migration-owner-manual-merge-v1` | `bbbafe2a` | 1 | no PR found | — | `KEEP_HISTORICAL_UNIQUE` |
| `plan/merge-readme-alignment-pilot-v1` | `9f5d8f23` | 1 | no PR found | — | `KEEP_HISTORICAL_UNIQUE` |
| `plan/merge-run-closeout-legacy-doc-pilot-v1` | `4f9d2b45` | 1 | no PR found | — | `KEEP_HISTORICAL_UNIQUE` |

`codex/p1a-v2-premerge-authorization` has no PR and no clear authority
Issue reference; its provenance cannot be fully verified, so it is
`BLOCKED_UNKNOWN_PROVENANCE` until an owner confirms its origin.

### Active implementation branch

| Branch | HEAD | PR | Disposition |
|--------|------|----|-------------|
| `agent/codex-supervisor-foundation-v0` | `16526801` (same as main) | Draft PR to be created under #92 | `KEEP_ACTIVE` |

## Section IV — open Draft PR audit

All nine open Draft PRs are superseded by the current project direction
(Codex Supervisor v0 under Issue #90/#92). Each should be closed without
merge with a brief comment pointing to Issue #92.

| PR | Branch | Title | Unique commits | Superseded by | Branch after close |
|----|--------|-------|----------------|---------------|---------------------|
| #5 | `agent/terminal-status-propagation-seal-restart-rework-v3` | consumed-decision CI preflight parity rework | 44 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #6 | `plan/framework-adoption-control-plane-v1` | transition workflow cutover and CI test bootstrap | 8 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #7 | `codex/legacy-control-plane-transition-disposition-v1` | disposition legacy control plane transition | 2 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #11 | `agent/architecture-constitution-plan-v1` | Replace blocked P0 authority with gate-compatible Decision | 15 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #19 | `codex/stage-a-freeze-baseline-v1` | freeze Architecture Spine main integration baseline | 3 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #21 | `codex/p1a-current-merge-validation-v2` | P1A: bind mainline checks to current merge | 3 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #24 | `codex/p1a-v3-exact-head-external-approval` | v3 exact-head external merge approval gate | 5 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #47 | `codex/base-platform-m1-spec-policy-core-v1` | M1: implement versioned SpecPackage and Policy Resolver core | 2 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |
| #49 | `codex/path-a-r1-state-gate-cutover-v1` | R2: add Path-A R1 State Gate and task-scoped exact-head CI | 8 | Issue #92 direction | `KEEP_HISTORICAL_UNIQUE` |

Closed unmerged Draft PR:

| PR | Branch | State | Disposition |
|----|--------|-------|-------------|
| #78 | `codex/unattended-base-platform-v0` | CLOSED (not merged) | Already closed; branch retained as `KEEP_HISTORICAL_UNIQUE` (66 unique commits) |

## Section V — remote branch deletion conditions

A remote branch may be deleted only when ALL of the following hold:

1. Not `main` or a protected branch.
2. No open PR still needs the branch.
3. No dirty or locked local worktree is linked to the branch.
4. HEAD still equals the audited HEAD SHA (no drift).
5. No open Issue still treats the branch as current execution authority.
6. HEAD is contained in main, OR unique history is preserved by a merged PR
   and the owner decides to drop the remote branch.

Before deletion, re-verify:
```
git ls-remote --heads origin <branch>
git merge-base --is-ancestor <audited-head> origin/main
git log --oneline origin/main..<audited-head>
```

Any state change stops the deletion for that branch.

Forbidden: `git push --force`, `git branch -D` on unverified branches,
wildcard batch deletion, parallel deletion without per-branch verification.

The 11 fully-merged branches listed above meet conditions 1-6 (no open PR,
no dirty worktree, HEAD in main). They are `DELETE_REMOTE_SAFE` pending
owner confirmation and re-verification at deletion time.

## Section VI — local worktree inventory

| Worktree path | Branch | HEAD | Locked | Clean | Disposition |
|---------------|--------|------|--------|-------|-------------|
| `F:/reverse-agent` | `agent/codex-supervisor-foundation-v0` | `16526801` | no | no (working tree — untracked scratch files) | `KEEP_ACTIVE` (main worktree) |
| `F:/reverse-agent-executor-neutral-vertical-slice-v1` | `codex/executor-neutral-vertical-slice-v1` | `0ab750cf` | no | yes | removable (branch fully merged) |
| `F:/reverse-agent-issue46` | `codex/base-platform-m1-spec-policy-core-v1` | `6e096b11` | no | yes | removable after PR #47 closed |
| `F:/reverse-agent-issue82-gate2-runtime-proof-v6` | `codex/unattended-base-platform-v0` | `ca79b53e` | no | yes | removable (PR #78 already closed; local HEAD differs from remote — verify no unpushed unique commits before removal) |
| `F:/reverse-agent-p0` | `agent/architecture-constitution-plan-v1` | `d500c145` | no | yes | removable after PR #11 closed |
| `F:/reverse-agent-path-a-r1-state-gate-cutover-v1` | `codex/path-a-r1-state-gate-cutover-v1` | `40400440` | no | yes | removable after PR #49 closed |
| `F:/reverse-agent-pr60-final-merge-authorization-v1` | `codex/pr60-final-merge-authorization-v1` | `7e2ef47b` | no | yes | removable (branch retained remotely as historical) |
| `F:/reverse-agent-pr60-mainline-landing-repair-v1` | `codex/pr60-mainline-landing-repair-v1` (local only — no remote) | `affb1bca` | no | **no** (14 dirty files) | `BLOCKED_DIRTY_WORKTREE` |
| `F:/reverse-agent-pr60-mainline-landing-repair-v2` | `codex/pr60-mainline-landing-repair-v2` | `4d28cbfb` | no | yes | removable (branch fully merged) |
| `F:/reverse-agent-stage-a` | `codex/stage-a-freeze-baseline-v1` | `38a0a934` | no | yes | removable after PR #19 closed |

`F:/reverse-agent-pr60-mainline-landing-repair-v1` is `BLOCKED_DIRTY_WORKTREE`:
its working tree has 14 modified/untracked files including
`.github/workflows/state-gate.yml` and `reverse_agent/project_gate.py`.
It must NOT be force-removed. The dirty changes must be resolved (committed,
stashed, or discarded by the owner) before the worktree can be pruned.

Before pruning, run:
```
git worktree prune --dry-run
```
Do not use `git worktree remove --force` or `git clean -fdx`.

## Section VII — open Issue cleanup

| Issue | Title | Labels | Disposition | Reason |
|-------|-------|--------|-------------|--------|
| #92 | Repository hygiene + thin Codex Supervisor composition v0 | work-item, r2, owner-accepted | `KEEP_ACTIVE` | Current task |
| #90 | Codex Supervisor Vertical Slice v0 | r1, work-item, owner-accepted | `KEEP_ACTIVE` | Parent product Issue |
| #73 | Plan: Unattended Base Platform Vertical Slice v0 | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 direction |
| #68 | PR #67 rework: generalize mainline Decision binding | work-item, r2 | `CLOSE_COMPLETED` | PR #67 merged; rework addressed |
| #66 | R2 activation rework: capture and repair governance preflight blocker | work-item, r2 | `CLOSE_COMPLETED` | Resolved in PR #67 |
| #65 | R2 Phase B: repair mainline landing lifecycle | work-item, r2 | `CLOSE_COMPLETED` | Resolved in PR #67 |
| #64 | R2 post-merge landing-state repair for PR #60 | work-item, r2 | `CLOSE_COMPLETED` | PR #60 merged and repaired |
| #63 | R2 final merge authorization for PR #60 | work-item, r2 | `CLOSE_COMPLETED` | PR #60 merged |
| #59 | Pivot milestone: executor-neutral vertical slice | r1, work-item | `CLOSE_COMPLETED` | PR #60 merged |
| #55 | Architecture reset: validate differentiation | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #54 | External setup: deploy trusted Path-A GitHub App | work-item, r2 | `KEEP_HISTORICAL_REFERENCE` | Design reference; not current scope |
| #53 | R2 rework v5: run Path-A from trusted evaluator | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by merged PR #67 |
| #52 | R2 rework v4: bind Path-A checks to live authority | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by merged PR #67 |
| #51 | R2 rework v3: enforce Path-A risk floors | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by merged PR #67 |
| #50 | R2 rework: close Path-A routing gaps | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by merged PR #67 |
| #48 | R2: add Path-A R1 State Gate and task-scoped CI | work-item, r2 | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #92; PR #49 to be closed |
| #46 | M1: implement versioned SpecPackage and Policy Resolver | r1, work-item, r1-approved | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #92; PR #47 to be closed |
| #45 | P1: Base Platform v0.1 vertical slice | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #42 | R2 handoff: merge accepted PR #41 | (none) | `CLOSE_COMPLETED` | PR #41 merged |
| #31 | P0 semantic consistency rework | (none) | `CLOSE_COMPLETED` | Resolved by minimal integration baseline |
| #30 | P0 acceptance rework: restore AGENTS.md | (none) | `CLOSE_COMPLETED` | Resolved by minimal integration baseline |
| #29 | P0 activation diagnostic | (none) | `CLOSE_COMPLETED` | Diagnostic completed |
| #28 | R1 Work Item: implement minimal AI integration baseline | (none) | `CLOSE_COMPLETED` | PR #27 merged |
| #26 | P0: direction convergence, minimal AI integration | (none) | `CLOSE_COMPLETED` | Resolved by PR #27 |
| #25 | P1A-v3 completion | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #23 | P1A-v3: bind merge approval to exact head | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #22 | P1A-v2: replace self-referential merge receipts | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #20 | P1A: bind mainline checks to each merge | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #18 | Program: Architecture cutover | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #17 | P1: integrate PR #9 exact head | (none) | `CLOSE_COMPLETED` | PR #9 merged |
| #16 | P0 v8 evidence-derived audit rework plan | (none) | `CLOSE_COMPLETED` | Resolved by subsequent PRs |
| #15 | P0 v5 full-profile convergence | (none) | `CLOSE_COMPLETED` | Resolved by subsequent PRs |
| #14 | Goal-to-Decision handoff and Required Audit simplification | (none) | `CLOSE_COMPLETED` | Resolved by subsequent PRs |
| #13 | P0 test compatibility and completion rework | (none) | `CLOSE_COMPLETED` | Resolved by subsequent PRs |
| #12 | P0 Active Work Item: Architecture Constitution | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |
| #10 | Architecture Constitution and Migration Baseline v1 | (none) | `CLOSE_NOT_PLANNED_SUPERSEDED` | Superseded by #90/#92 |

Issue #91 (superseded by #92) remains closed. Issue #78 (PR) remains closed
and unmodified. No new cleanup Issues are created.

## Section IX — mature tool reuse

The thin Supervisor layer reuses mature tools directly. No framework,
protocol, database, or model backend is introduced.

| Capability | Tool | Notes |
|------------|------|-------|
| Repository observation | `git` | `rev-parse`, `merge-base`, `rev-list`, `log`, `diff`, `worktree list`, `status` |
| GitHub state observation | `gh issue`, `gh pr`, `gh api` | read-only list/view |
| Issue publication | `gh issue create/edit` | dry-run by default; `--live` required for writes |
| Validation | `python` stdlib (`json`, `hashlib`, `re`, `argparse`, `subprocess`) | no external dependencies |
| Testing | `pytest`, `unittest.mock` | local fixtures and fake runners |
| Marker computation | `hashlib.sha256` | stable, deterministic |
| JSON I/O | `json` | schema-validated |

The Supervisor does NOT reimplement: Git object model, GitHub REST client,
PR/Issue state machines, CI system, task scheduler, or model backend.

## Section X — audit-result contract

The minimal audit result is validated by `scripts/supervisor_validate.py`:

```json
{
  "status": "continue | revise | stop",
  "findings": [
    { "claim": "...", "evidence": ["<verifiable reference>"] }
  ],
  "next_task": {
    "title": "...",
    "goal": "<one bounded goal>",
    "allowed_scope": ["<path or operation>"],
    "forbidden_scope": ["<path or operation>"],
    "acceptance_checks": ["<deterministic check>"],
    "execution_prompt": "<complete prompt>"
  }
}
```

Rejected: finding without evidence, `next_task` without
`acceptance_checks`, empty `allowed_scope`, broad scope (`*`, `**`, `.`,
`./`, `entire repository`), requests for merge / auto-merge / push main /
release / deploy / credential access / unrelated Issue or PR mutation.

## Section XI — stable cycle marker

The cycle marker is a SHA-256 over the normalized fields:

```
repository
main SHA
schema/policy version
next_task.goal
next_task.acceptance_checks
```

Marker format: `<!-- reverse-agent-supervisor-cycle:<sha256> -->`

Rules: marker absent → create; marker present and content changed → update;
marker present and content identical → no-op. Equivalent inputs (same goal,
same checks in any order) produce the same marker. No duplicate Issues are
created for the same marker.

## Security notes

- No environment variables, tokens, or credentials are read or dumped by the
  Supervisor scripts. `supervisor_context.py` does not import `os.environ`.
- All `git`/`gh` invocations use explicit argument lists (no `shell=True`,
  no metacharacters).
- Dry-run mode performs zero writes. `--live` is required for any GitHub
  mutation.
- This report contains no tokens, secrets, or environment dumps.
