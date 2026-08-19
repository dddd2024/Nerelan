# AGENTS.md

Repository operating guide for agents, maintainers, and reviewers working in `dddd2024/reverse-agent`.

## Repository purpose

`reverse-agent` currently provides a **minimal AI development integration baseline** around GitHub, Codex, deterministic checks, independent review, and human merge. It is not a generic AI software-development platform.

```text
approved specification
-> approved immutable GitHub Work Item snapshot
-> Codex implementation
-> deterministic GitHub Actions
-> independent review
-> human merge
```

Repository-owned custom capability is limited to thin risk classification, bounded path/operation policy, high-risk approval boundaries, deterministic acceptance checks, and future domain-specific adapters.

## Current non-goals

```text
generic LangGraph orchestration platform
generic Agent Registry or multi-agent organization
generic Web agent control console
GitHub Issue/PR state replication
generic checkpoint/retry/reconciliation platform
Open SWE/OpenHands control-plane product
hostile-binary, reverse-solving, crash, patch, malware, or firmware product work
```

Security and binary directions remain extension candidates, not current implementation scope.

## Platform V1 — bounded OpenHands Agent Canvas + Codex ACP direction

The current selected bounded Platform V1 integration direction is **OpenHands Agent Canvas + Codex ACP**. This is a thin adapter layer (`reverse_agent/platform_v1/`) that binds the repository's governance layer to the pinned OpenHands Agent Canvas + Codex ACP platform surface.

```text
do not fork OpenHands
do not copy its frontend or Agent Loop
do not build a second control platform
do not auto-merge
```

The adapter does not implement an executor, agent loop, sandbox, database, or frontend. Live compatibility probes require a trusted host with explicit opt-in. The current status is `PR97_CODE_REWORK_COMPLETE_AWAITING_TRUSTED_HOST_LIVE_PROBE` — the full vertical slice is not yet accepted.

## Two authority paths

No source is globally authoritative outside the path in which it applies.

### Path A — ordinary R0/R1 authority

A template-created Issue is initially a **CANDIDATE**, not execution authority. Ordinary R0/R1 authority becomes active only after all of the following are true:

```text
Issue created from the R1 template
+ repository owner/maintainer applies the `r1-approved` label after review
+ executor computes SHA-256 over the normalized approved Issue body
+ executor records the approval snapshot in the Draft PR body
```

The Draft PR body must record:

```text
repository
issue_number
approval_state: APPROVED
approved_by
approval_event_or_time
body_digest_sha256
immutable_observation_ref
work_item_identity: {repository}#{issue_number}@{immutable_observation_ref}
target_branch
integration_base_ref
base_sha
exact_head_sha
```

For this minimal model, `immutable_observation_ref` is the approved normalized Issue-body SHA-256 digest unless GitHub supplies a stronger immutable revision reference. The approved Issue body, exact digest, allowed paths, forbidden operations, acceptance criteria, target branch, `integration_base_ref`, and `base_sha` together form the Path-A authority snapshot. `integration_base_ref` may be `main` or an explicitly owner-approved repository planning branch; no implicit `main` fallback is permitted.

Issue comments and PR comments are never authority. A material Issue-body edit changes the digest, invalidates the previous snapshot, and requires owner/maintainer reapproval plus a new snapshot before execution continues.

`project_state/decision_packet.md` and `project_state/gates/command_plan.json` are not used for ordinary R0/R1 work.

### Fresh R1 activation lifecycle

After owner/maintainer approval, verify the approved Issue digest, exact target branch, `integration_base_ref`, and `base_sha`. Create the fresh target branch from that exact base and create exactly one tree-identical empty activation commit:

```text
git commit --allow-empty -m "chore: activate R1 work item #<issue>"
```

Push that exact branch, create the Draft PR, and record the complete authority snapshot with initial `exact_head_sha` equal to the empty activation commit. No product/source/test file may change before the first Draft PR snapshot exists. The bootstrap grant is only for this empty commit; arbitrary seed-file commits and history rewrite remain forbidden.

After an implementation push, the permitted Draft-PR-body update must rebind `exact_head_sha` to the new exact implementation head. Final State Gate must pass against that rebinding. A transient synchronize failure against the stale previous `exact_head_sha` is not acceptance and grants no merge authority.

### Path B — transition / R2-R3 authority

Transition rounds and R2/R3 operations require:

```text
bounded APPROVED Decision in project_state/decision_packet.md
+ generated project_state/gates/command_plan.json
+ transition-preflight PRE_EXECUTION_AUTHORIZED
```

R2/R3 fail closed. No Issue body, label, comment, roadmap, or PR body can authorize R2/R3 operations.

## Risk tiers and authority model

| Tier | Scope | Authority path |
|------|-------|----------------|
| R0 | read-only observation | Path A; no Decision required |
| R1 | bounded edits plus narrow R1 publication | Path A; approved immutable Work Item snapshot |
| R2 | workflow/dependency/unbounded-network/privileged-publication | Path B; bounded Decision |
| R3 | binary execution, debugging, secrets, destructive operations | Path B; bounded Decision |

### R1 publication — narrow exception

During Agent implementation, before independent exact-head acceptance, Path A permits only the following network/publication operations:

- push to the exact named non-`main` branch bound to the approved Work Item;
- create the exact Draft PR against the snapshot `integration_base_ref`;
- update that Draft PR description.

These grants do not authorize the Agent to merge, mark-ready, directly push to `main`, rewrite history, perform cross-repository publication, tag, or release. After independent exact-head acceptance, the separate owner-manual final-acceptance carve-out below may apply; it is not part of the Agent-implementation publication grant.

### R1 final acceptance — owner manual merge carve-out

A repository owner/maintainer may personally perform `mark-ready` and `merge` of an already-accepted ordinary R1 PR without a separate Path-B Decision, iff ALL of the following hold immediately before the merge:

- approved immutable R1 Work Item snapshot is recorded in the Draft PR body and its `body_digest_sha256` matches the current normalized Issue body;
- the source Work Item Issue carries `r1-approved` applied by an owner/maintainer, and no material Issue-body edit has occurred since;
- the PR is a Draft PR targeting the snapshot `integration_base_ref`, created from a fresh branch whose merge-base equals the snapshot `base_sha`;
- allowed-path compliance: the PR diff touches only paths listed in the approved Work Item;
- deterministic local checks passed on the exact head (`pytest`, `git diff --check`);
- required exact-head GitHub Actions checks are SUCCESS on the PR head;
- independent exact-head audit accepted and recorded as a PR comment by the auditor, identifying the accepted head SHA;
- no unresolved blocking review threads;
- owner/maintainer immediate re-observation immediately before merge:
  - the remote snapshot `integration_base_ref` == snapshot `base_sha` (no integration-base drift);
  - PR `headRefOid` == accepted audit head (no head movement);
  - PR `baseRefOid` == snapshot `base_sha`;
  - PR `mergeable` == MERGEABLE;
  - PR `mergeStateStatus` == CLEAN;
  - PR CI on exact head == SUCCESS;
  - no concurrent Agent publication or branch mutation is active.

If all conditions hold, the owner/maintainer may perform the manual sequence:

```text
owner/maintainer manual mark-ready
-> immediate owner/maintainer manual merge (merge method = merge,
   with --match-head-commit or equivalent expected-head protection)
-> post-merge verification (merged == true, mergeCommit.oid recorded,
   new remote integration_base_ref == mergeCommit.oid)
-> close the source Work Item Issue as completed
```

The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used. Permitted carve-out: a human-initiated owner/maintainer action performed personally through the GitHub UI or an owner-controlled CLI session. `gh pr merge` run personally by an owner/maintainer is permitted under this carve-out.

Local working-tree cleanliness is conditional:
- GitHub UI merge: no universal local-working-tree requirement; no concurrent Agent publication or branch mutation may be active.
- owner-controlled local CLI merge: the local session/worktree must be clean enough to prevent accidental commit, push, branch mutation, or mixing of unrelated changes.

### Working-tree state classification

Working-tree observations are classified without deleting, restoring, staging, or hiding any path:

- `AUTHORIZED_TRACKED_DELTA`: a tracked change within the exact approved allowlist; it is the only stageable class.
- `KNOWN_RUNTIME_SCRATCH`: untracked content under `task_workspaces/` or `.platform_v1_runtime/`; it is non-blocking and non-stageable.
- `GENERATED_GOVERNANCE_ARTIFACT`: generated content under `project_state/gates/`; it is non-stageable unless a separate authority explicitly lists it.
- `UNKNOWN_UNTRACKED`: unexplained untracked content; preserve it, allow read-only bootstrap, and block publication until resolved by authority or the owner.
- `UNAUTHORIZED_TRACKED_OR_SENSITIVE`: a tracked change outside the allowlist or any sensitive-looking path; stop immediately and never stage it.

Classification is not cleanup authorization. Agents must not use reset, clean, stash, restore, deletion, or broad staging to manufacture a clean tree.
`startup-snapshot` machine-enforces bootstrap classification; before product staging or publication, run `python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state` and require `PUBLICATION_READY`.

For ordinary R1 local readiness, run `python -m reverse_agent.project_gate worktree-r1-publication-readiness --issue-body-file <approved-issue-body-file> --pr-body-file <draft-pr-body-file>` using frozen approved Issue body and current Draft PR body material stored outside the repository. This command derives allowed paths only from the approved Issue body and proves the frozen digest plus local branch/base/head/merge-base binding and worktree classification. It does not replace live `r1-approved`, owner/maintainer permission, Issue state, Draft PR state, auto-merge, or authority-revision verification; GitHub State Gate remains the final live authority verification.

This carve-out does not authorize Agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated mark-ready or merge. Those remain Path-B. This carve-out does not apply to R2/R3 work items; each requires its own Path-B Decision.

### R2 publication/network

The following require Path B:

- direct push to `main`;
- agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated `merge` or `mark-ready`;
- GitHub auto-merge;
- force push, rebase, squash, or another history rewrite;
- workflow/dependency publication;
- unbounded network access or cross-repository publication;
- credentials or secrets access;
- tag or release;
- any operation outside the approved Work Item binding;
- merge or mark-ready of R2/R3 work items;
- merge or mark-ready when any R1 final-acceptance carve-out condition has failed.

Note: owner/maintainer manual `merge` and `mark-ready` of an accepted ordinary R1 PR that satisfies all R1 final-acceptance carve-out conditions is Path-A (see `R1 final acceptance — owner manual merge carve-out` above).

## R0/R1 allowed operations

- observe repository and GitHub state;
- edit only the approved `allowed_paths`;
- run approved deterministic checks;
- create a fresh feature branch from the exact approved `integration_base_ref` at `base_sha`;
- use the narrow R1 publication exception for the exact branch and Draft PR.

## Startup checks

Before Path-A work:

1. Confirm the repository, current branch, and HEAD.
2. Fetch and observe the exact owner-approved `integration_base_ref`.
3. Read the Issue body and verify it was created from the R1 template.
4. Confirm the `r1-approved` label was applied by a repository owner or maintainer.
5. Normalize the Issue body and compute its SHA-256 digest.
6. Confirm the Draft PR authority snapshot records the same digest, approver, approval event/time, repository, Issue number, target branch, `integration_base_ref`, and `base_sha`.
7. Confirm the live PR base ref equals `integration_base_ref`, its base SHA equals `base_sha`, and the branch merge-base equals `base_sha`.
8. Confirm requested paths and operations remain inside the approved Work Item.

If the branch merge-base differs, **stop**. Do not rebase or rewrite history under Path A. Obtain a revised and reapproved Work Item, then create a fresh branch from the newly approved base. Intentional history rewriting requires separate Path-B authorization.

Permanent guidance never hard-codes a historical integration-base SHA. Historical transition bases apply only to their bounded Decisions.

For Path-B work, also read the active Decision and generated Command Plan, run the required gate sequence, and require `PRE_EXECUTION_AUTHORIZED` before implementation.

## Work Item acceptance requirements

A Path-A Work Item is usable only when it captures:

- approved specification or task goal;
- exact allowed paths;
- forbidden operations;
- acceptance criteria;
- required deterministic checks;
- exact target branch, exact owner-approved `integration_base_ref`, and its exact `base_sha`;
- CANDIDATE-to-APPROVED lifecycle;
- owner/maintainer approver identity;
- immutable observation reference and normalized body SHA-256 digest;
- invalidation and reapproval rule for material body edits;
- Draft PR and human merge boundary.

## Test commands

Run only tests applicable to the Work Item. For this transition round:

```bash
python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q
git diff --check
```

Transition gate sequence, only when Path B requires it:

```bash
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre
```

## Branch and PR rules

- Never work directly on `main`.
- Path A uses a fresh branch from the approved base; it never rebases or rewrites history.
- Open a Draft PR and record the immutable Work Item authority snapshot in its body.
- Keep the PR Draft until independent audit accepts the exact head.
- Merge remains separately authorized and human-controlled.

## Prohibited actions

```text
direct push to main
force push
rebase
squash
agent-initiated or automation-initiated merge without explicit Path-B authorization
agent-initiated or automation-initiated mark-ready without explicit Path-B authorization
owner/maintainer manual merge or mark-ready of an R1 PR that fails any R1 final-acceptance carve-out condition
owner/maintainer manual merge or mark-ready of an R2/R3 PR without Path-B authorization
tag or release
unknown-binary execution
model API invocation from repository code
external reverse-tool invocation
runner dispatch
automatic merge
```

Note: owner/maintainer manual `merge` and `mark-ready` of an accepted ordinary R1 PR that satisfies all R1 final-acceptance carve-out conditions is permitted Path-A publication (see `R1 final acceptance — owner manual merge carve-out`).

## Stop conditions

Stop immediately when:

- the Work Item is still CANDIDATE or lacks verified owner/maintainer approval;
- the Issue-body digest differs from the recorded authority snapshot;
- a material Issue-body edit occurred after approval;
- branch, base SHA, allowed path, operation, or acceptance criterion differs from the snapshot;
- Path-A work would require rebase, history rewrite, privileged publication, unbounded network, workflow, dependency, secrets, binary, or destructive scope;
- a Path-B Decision or Command Plan does not validate;
- focused tests or exact-head CI fail;
- independent audit has not accepted the exact head.

When blocked, stop and request a revised Work Item or bounded Decision. Do not invent a new Gate, receipt, verifier, mainline authorization schema, or tracked artifact family to unblock yourself.
