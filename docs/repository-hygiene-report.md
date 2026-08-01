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

## Current observed state (post-cleanup evidence)

This section records the repository state observed on the
`agent/codex-supervisor-foundation-v0` branch at HEAD
`30ad6e9b0aa0dcfca9e3c3f899f4ca4c15933a94`, against
`origin/main` = `16526801bda2a816fc707342f903c1ad037de9bd`.

| Metric | Current value |
|--------|---------------|
| Remote branches (incl. main) | 18 |
| Open Draft PRs | 1 (PR #93, branch `agent/codex-supervisor-foundation-v0`) |
| Closed old Draft PRs (superseded, not merged) | 9 (#5, #6, #7, #11, #19, #21, #24, #47, #49) |
| Pre-existing closed unmerged Draft PR | 1 (#78) — already closed before this work |
| Open Issues | 2 (#90 parent product, #92 current task) |
| Issue #54 | CLOSED as `NOT_PLANNED` after owner audit |
| CI run `30681854828` (baseline) | SUCCESS |
| State Gate run `30681854818` | FAILURE |
| State Gate failure cause | Legacy PR #67 Decision carries branch/path binding that does not cover the `agent/codex-supervisor-foundation-v0` branch; State Gate refuses to validate a PR whose head branch is not named in the approved Work Item |
| Dirty worktree (`F:/reverse-agent-pr60-mainline-landing-repair-v1`) | Retained as `BLOCKED_DIRTY_WORKTREE`; NOT force-removed |

## Before / after summary (historical reference)

| Metric | Before | After |
|--------|--------|-------|
| Remote branches (excl. main) | 28 | 17 retained, 11 delete-safe branches deleted |
| Open Draft PRs | 9 | 1 (PR #93 only) |
| Closed old Draft PRs (this work) | 0 | 9 |
| Open Issues | 36 | 2 (#90, #92) |
| Local worktrees (excl. main) | 9 | 1 blocked dirty worktree retained; 8 removable worktrees pruned |

Note: the 11 fully-merged delete-safe branches were deleted by the owner
during the Issue #92 hygiene pass. The 9 superseded Draft PRs were closed
without merge. The single dirty worktree
`F:/reverse-agent-pr60-mainline-landing-repair-v1` is retained and MUST
NOT be force-removed; its dirty changes must be resolved by the owner.

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
| `agent/codex-supervisor-foundation-v0` | `30ad6e9b0aa0dcfca9e3c3f899f4ca4c15933a94` | Draft PR #93 (open) | `KEEP_ACTIVE` |

## Section IV — Draft PR audit (current state)

After the Issue #92 hygiene pass, exactly one Draft PR remains open and
nine superseded Draft PRs have been closed without merge.

### Open Draft PR (1)

| PR | Branch | Head SHA | Title | Disposition |
|----|--------|----------|-------|-------------|
| #93 | `agent/codex-supervisor-foundation-v0` | `30ad6e9b0aa0dcfca9e3c3f899f4ca4c15933a94` | Repository hygiene + thin Codex Supervisor composition v0 (#92) | `KEEP_ACTIVE` — current work item |

### Closed old Draft PRs (9, superseded under Issue #92)

Each was closed without merge. Their branches are retained as
`KEEP_HISTORICAL_UNIQUE` because they carry unique commits not in main.

| PR | Branch | Title | Close reason |
|----|--------|-------|--------------|
| #5 | `agent/terminal-status-propagation-seal-restart-rework-v3` | consumed-decision CI preflight parity rework | Superseded by Issue #92 direction |
| #6 | `plan/framework-adoption-control-plane-v1` | transition workflow cutover and CI test bootstrap | Superseded by Issue #92 direction |
| #7 | `codex/legacy-control-plane-transition-disposition-v1` | disposition legacy control plane transition | Superseded by Issue #92 direction |
| #11 | `agent/architecture-constitution-plan-v1` | Replace blocked P0 authority with gate-compatible Decision | Superseded by Issue #92 direction |
| #19 | `codex/stage-a-freeze-baseline-v1` | freeze Architecture Spine main integration baseline | Superseded by Issue #92 direction |
| #21 | `codex/p1a-current-merge-validation-v2` | P1A: bind mainline checks to current merge | Superseded by Issue #92 direction |
| #24 | `codex/p1a-v3-exact-head-external-approval` | v3 exact-head external merge approval gate | Superseded by Issue #92 direction |
| #47 | `codex/base-platform-m1-spec-policy-core-v1` | M1: implement versioned SpecPackage and Policy Resolver core | Superseded by Issue #92 direction |
| #49 | `codex/path-a-r1-state-gate-cutover-v1` | R2: add Path-A R1 State Gate and task-scoped exact-head CI | Superseded by Issue #92 direction |

### Pre-existing closed unmerged Draft PR (1)

| PR | Branch | State | Disposition |
|----|--------|-------|-------------|
| #78 | `codex/unattended-base-platform-v0` | CLOSED (not merged) | Already closed before this work; branch retained as `KEEP_HISTORICAL_UNIQUE` (66 unique commits) |

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

## Section VII — Issue cleanup (current state)

After the Issue #92 hygiene pass, only two Issues remain open: #90 (parent
product) and #92 (current task). All other Issues have been closed by the
owner — either as `COMPLETED` (work merged/resolved) or as `NOT_PLANNED`
(superseded by the #90/#92 direction).

### Open Issues (2)

| Issue | Title | Labels | Disposition |
|-------|-------|--------|-------------|
| #92 | Repository hygiene + thin Codex Supervisor composition v0 | work-item, r2, owner-accepted | `KEEP_ACTIVE` — current task |
| #90 | Codex Supervisor Vertical Slice v0 | r1, work-item, owner-accepted | `KEEP_ACTIVE` — parent product Issue |

### Notable closed Issues (post-audit)

| Issue | Title | State | State reason | Note |
|-------|-------|-------|--------------|------|
| #54 | External setup: deploy trusted Path-A GitHub App | CLOSED | `NOT_PLANNED` | Closed by owner after audit; not current scope |
| #91 | (superseded by #92) | CLOSED | — | Remains closed, unmodified |
| #78 | (PR) | CLOSED | — | Remains closed, unmodified |

All other historical Issues (#10, #12, #13, #14, #15, #16, #17, #18, #20,
#22, #23, #25, #26, #28, #29, #30, #31, #42, #45, #46, #48, #50, #51, #52,
#53, #55, #59, #63, #64, #65, #66, #68, #73) are CLOSED. No new cleanup
Issues were created.

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

## Section X — audit-result contract (v0.2, fail-closed)

The audit result is validated by `scripts/supervisor_validate.py` against
the closed v0.2 schema (`docs/supervisor/audit-result.schema.json`).
Unknown fields are rejected at every level (top level, finding, next_task).

```json
{
  "schema_version": "0.2",
  "repository": "dddd2024/reverse-agent",
  "audited_main_sha": "<full 40-hex-char SHA>",
  "status": "continue | revise | stop",
  "findings": [
    { "claim": "...", "evidence": ["<verifiable reference>"] }
  ],
  "next_task": null | {
    "title": "...",
    "goal": "<one bounded goal>",
    "allowed_scope": ["<path or operation>"],
    "forbidden_scope": ["<path or operation>"],
    "requested_operations": ["<closed-whitelist operation>"],
    "acceptance_checks": ["<deterministic check>"],
    "execution_prompt": "<complete prompt>"
  }
}
```

Fail-closed rejections (finite, machine-readable error codes):

- `SCHEMA_VERSION_MISMATCH` — `schema_version` is not `"0.2"`.
- `REPOSITORY_MISMATCH` — `repository` does not equal the expected value.
- `INVALID_MAIN_SHA_FORMAT` / `MAIN_SHA_MISMATCH` — `audited_main_sha` is not
  a full 40-hex SHA or does not equal the expected value.
- `UNKNOWN_FIELD` — any field outside the closed set (top level, finding, or
  next_task) is rejected.
- `INVALID_JSON` — payload is not a JSON object.
- `INVALID_STATUS` — `status` not in `{continue, revise, stop}`.
- `FINDINGS_MISSING` / `FINDING_NO_EVIDENCE` / `FINDING_INVALID_CLAIM`.
- `NEXT_TASK_ALLOWED_SCOPE_EMPTY` / `NEXT_TASK_SCOPE_TOO_BROAD`.
- `NEXT_TASK_OPERATIONS_REQUIRED` / `NEXT_TASK_OPERATION_UNKNOWN` —
  `requested_operations` is the **authoritative** permission grant and must
  be a non-empty subset of the closed whitelist:
  `{read_repository, edit_bounded_files, run_checks, push_named_branch,
  create_or_update_draft_pr}`.
- `POLICY_DANGEROUS_ACCEPTANCE_CHECK` — `acceptance_checks` is scanned for
  dangerous commands (push main, merge, release, deploy, force push, rebase,
  reset --hard, credential/secret/token access).
- `POLICY_MERGE_FORBIDDEN` / `POLICY_MAIN_PUSH_FORBIDDEN` /
  `POLICY_RELEASE_FORBIDDEN` / `POLICY_DEPLOYMENT_FORBIDDEN` /
  `POLICY_CREDENTIAL_ACCESS_FORBIDDEN` /
  `POLICY_UNRELATED_MUTATION_FORBIDDEN` — secondary natural-language scan of
  `allowed_scope`, `goal`, `execution_prompt` (auxiliary only; never
  authorizes an operation absent from `requested_operations`).
- `FIELD_TOO_LONG` / `FIELD_TOO_MANY` — bounded limit exceeded.
- `NEXT_TASK_FORBIDDEN_SCOPE_INVALID` — `forbidden_scope` element is not a
  non-empty string or exceeds the length cap.

Validation failure never proceeds to marker computation or publication
planning.

## Section XI — stable cycle marker (v0.2)

The cycle marker is a SHA-256 digest over the canonical JSON encoding of:

```
repository
exact main SHA (40 hex chars, lowercased)
schema_version (fixed "0.2")
policy_version (fixed "0.2")
normalized next_task.goal
sorted, de-duplicated next_task.allowed_scope
sorted, de-duplicated next_task.forbidden_scope
sorted, de-duplicated next_task.requested_operations
sorted, de-duplicated next_task.acceptance_checks
```

Marker format: `<!-- reverse-agent-supervisor-cycle:<sha256> -->`

Rules: marker absent → `create_issue`; marker present and content changed →
`update_issue`; marker present and content identical → `no_op`. A material
change to **any** covered field (repository, main SHA, schema/policy
version, goal, allowed/forbidden scope, requested operations, or acceptance
checks) changes the marker. Equivalent inputs (same fields in any order,
extra whitespace) produce the same marker. No duplicate Issues are created
for the same marker.

## Security notes

- No environment variables, tokens, or credentials are read or dumped by the
  Supervisor scripts. `supervisor_context.py` does not import `os.environ`.
- All `git`/`gh` invocations use explicit argument lists (no `shell=True`,
  no metacharacters).
- Dry-run mode performs zero writes. `--live` is required for any GitHub
  mutation, and even then only `gh issue create` / `gh issue edit` (never
  merge, mark-ready, close, release, deploy, or main push).
- Context collection is fail-closed: any `git`/`gh` failure, timeout,
  invalid JSON, or missing main SHA raises `ContextError` and emits no
  context. Read failures are never masked as empty Issue/PR lists.
- Publication is fail-closed:
  - Discovery failure (gh failure, invalid JSON, incomplete results) → zero writes.
  - Marker found in two Issues → zero writes (`DUPLICATE_MARKER`).
  - Closed Issue with the same marker → no duplicate create.
  - Body exceeding `MAX_BODY_LENGTH` → rejected, NOT truncated.
  - Live guard verifies `gh` login user is `dddd2024`, worktree is clean,
    current branch is `agent/codex-supervisor-foundation-v0` (never `main`),
    and `origin/main` equals `audited_main_sha`. Any failure → zero writes.
  - TOCTOU: marker is re-queried immediately before any live `gh issue`
    write; if it appeared or duplicated, zero writes.
  - `update_issue` updates both title and body together.
- This report contains no tokens, secrets, or environment dumps.
