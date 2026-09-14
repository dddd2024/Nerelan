# AGENTS.md

Operating entry for `dddd2024/Nerelan`. Read this entry and the current task authority, then only the references needed for the action. Historical repository names in evidence are not current repository identities.

## Repository purpose

Nerelan is a local-first governed multi-Agent development platform: persistent goals, bounded autonomous windows, reusable planning/execution adapters, deterministic checks, independent review and exact-path Draft publication. Keep custom authority, risk, budgets, durable claims/idempotency and evidence confinement thin; reuse mature runtimes rather than copying them. The current adapter layer is `reverse_agent/platform_v1/`; the product/runtime boundaries are in [the conditional reference](docs/agents/governance-reference.md#product-boundaries).

## Current non-goals and hard boundaries

No GitHub state replica, copied upstream runtime, unbounded plugin manager, browser-side shell/filesystem/credential/policy authority, or unauthorized automatic deployment. Hostile-binary, reverse-solving, crash, patch, malware and firmware work remain extension candidates, not the default product scope. Provider-free startup and CI make zero model calls.

## Two authority paths

No source is globally authoritative outside its applicable path. Prompts, skills, roadmaps and summaries are not grants. Issue comments and PR comments are never authority.

### Path A — ordinary R0/R1

A template-created Issue starts as CANDIDATE, not execution authority. Work requires owner/maintainer review and `r1-approved`, the normalized approved Issue body SHA-256, and an immutable authority snapshot in the Draft PR body. A material Issue-body edit invalidates that snapshot and requires owner/maintainer reapproval before continuation.

Snapshot fields: `repository`, `issue_number`, `approval_state: APPROVED`, `approved_by`, `approval_event_or_time`, `body_digest_sha256`, `immutable_observation_ref`, `work_item_identity: {repository}#{issue_number}@{immutable_observation_ref}`, `target_branch`, `integration_base_ref`, `base_sha`, `exact_head_sha`. The immutable reference is the approved body digest unless GitHub supplies a stronger immutable revision. The approved base may be main or an explicitly approved planning branch; there is no implicit main fallback.

For activation, verify the current approval/digest and exact branch/base, create a fresh branch from that base, then exactly one tree-identical empty activation commit:

```text
git commit --allow-empty -m "chore: activate R1 work item #<issue>"
```

Push the exact branch and create the Draft with the full snapshot bound to that commit. No product/source/test file may change before the first Draft PR snapshot exists. Seed-file commits are not this exception. After each implementation push, rebind `exact_head_sha` in the Draft PR body; a transient State Gate failure against the previous head is not acceptance.

Ordinary R0/R1 work does not use `project_state/decision_packet.md` or `project_state/gates/command_plan.json`. See [Path A details](docs/agents/governance-reference.md#path-a) when activating or publishing.

### Path B — transition / R2-R3

Require a bounded APPROVED `project_state/decision_packet.md`, generated `project_state/gates/command_plan.json`, and transition-preflight `PRE_EXECUTION_AUTHORIZED` before implementation. The activated Decision is immutable. Issue bodies, labels, comments, roadmaps and PR bodies cannot authorize R2/R3. Read [Path B details](docs/agents/governance-reference.md#path-b) for those actions, not for every R1 edit.

## Risk tiers

R0: read-only observation. R1: bounded edits/checks and narrow publication under Path A. R2: governance, workflows, dependencies, unbounded network and privileged publication. R3: secrets, binary execution/debugging and destructive operations. R2/R3 require Path B; actual path/operation risk floors override a task's self-description. A documentation edit to an authority surface is not automatically R1.

### R1 publication — Agent implementation

During Agent implementation, before independent exact-head acceptance, Path A permits only push to the exact approved non-main branch, creation of its exact Draft PR against `integration_base_ref`, and updates to that Draft PR description. It does not grant the Agent mark-ready, merge, direct main push, history rewrite, cross-repository publication, tag or release. After independent exact-head acceptance, the owner-manual carve-out below is a separate stage, not part of the Agent-implementation publication grant.

### R1 final acceptance — owner manual merge carve-out

Only a human-initiated owner/maintainer action, reviewed, decided and personally triggered through GitHub UI or an owner-controlled CLI, can use this carve-out. Immediately before action, ALL must hold:

- The current source Issue has verified owner/maintainer `r1-approved`, no subsequent material edit, and the recorded immutable snapshot matches its current `body_digest_sha256`.
- The PR is Draft, targets the approved `integration_base_ref`, has a fresh branch with merge-base equal to `base_sha`, and changes only approved paths.
- Deterministic local `pytest` and `git diff --check` passed on the exact head; required exact-head Actions are SUCCESS; an independent auditor's PR comment accepts that head; no blocking review thread remains.
- Immediate remote observation confirms integration ref == `base_sha`, `baseRefOid` == `base_sha`, `headRefOid` == accepted audit head, MERGEABLE, CLEAN, exact-head CI SUCCESS, and no concurrent Agent publication or branch mutation.

The sequence is personal manual mark-ready, immediate manual merge (`merge method = merge`, `--match-head-commit` or equivalent expected-head protection), then verify `merged == true`, record `mergeCommit.oid`, and verify the new remote integration ref equals that commit before closing the source Issue. UI use needs no universal local clean tree; an owner CLI session must be clean enough to prevent accidental commit/push/branch mutation or unrelated changes.

Agent identity using the owner's account does not make an action personal human acceptance. Delegated actions and all R2/R3 work are excluded. See [landing details](docs/agents/governance-reference.md#landing) only when preparing acceptance.

### R2 publication/network

Path B is required for agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated or external-service mark-ready/merge; auto-merge; main push; force push/rebase/squash/history rewrite; workflow/dependency publication; unbounded network/cross-repository publication; credentials/secrets; tag/release; operations outside the Work Item; and R2/R3 landing or any failed R1 carve-out predicate. The fully satisfied personal R1 carve-out is the sole stated exception.

## Startup checks

Fresh-read repository, branch, head, approved integration ref/base, live authority/approval/digest, requested paths/operations and concurrent ownership. For Path A, verify the current Draft snapshot, PR base and merge-base; for Path B, verify its Decision/plan/preflight. Do not load a repository map or historical state/report stack unless this task needs it. A missing local capability is not proof of failure on CI, and a partial checkout is not a complete checkout.

Preserve existing work. Classify without cleanup: `AUTHORIZED_TRACKED_DELTA` is the only normally stageable class; `KNOWN_RUNTIME_SCRATCH` is untracked runtime content, non-blocking/non-stageable; `GENERATED_GOVERNANCE_ARTIFACT` needs an explicit grant to stage; `UNKNOWN_UNTRACKED` permits read-only bootstrap but blocks publication until resolved; `UNAUTHORIZED_TRACKED_OR_SENSITIVE` stops work and must never be staged. Do not reset, clean, stash, restore, delete or bulk-stage to manufacture cleanliness.

For local staging/publication use the applicable [worktree guard](docs/agents/governance-reference.md#worktree-guards). R1 `worktree-r1-publication-readiness` uses the frozen approved Issue body and current Draft PR body; it does not replace live authority verification by GitHub State Gate. Path B requires `worktree-publication-readiness` and `PUBLICATION_READY`.

## Work Item acceptance requirements

The approved specification must bind exact allowed paths, forbidden operations, acceptance criteria, required deterministic checks, target branch, `integration_base_ref` and `base_sha`, owner/maintainer approval, immutable identity/digest, material-edit invalidation/reapproval, and Draft/human-merge boundaries. Missing fields are not invitations to infer permission. Reuse existing approved work; do not take another active owner's task.

## Test commands

Use the current Work Item's applicable checks, not a historical round's fixed suite. Within existing authority, capability and retry budget, use disposable, provider-free development checks to implement, inspect and fix the requested result; do not request the same permission at every already-authorized step. This is not a blanket claim that all repository tests are safe or permission for installs, runtime probes or workflow reruns.

Final mandatory checks, exact-head CI and independent acceptance remain required; optional development checks are not final acceptance. Run `git diff --check` for the scoped change. [Transition commands](docs/agents/governance-reference.md#path-b) apply only to Path B. Report the actual commands, head/surface, results and unavailable checks; a fixture, first draft or self-review is not product acceptance.

## Branch and PR rules

Never work directly on main. Use the authority's fresh exact-base branch and Draft binding; Path A never rebases or rewrites history. Keep Draft until independent exact-head audit; Ready/Merge remain separately controlled. A published Draft is not a mainline landing.

## Prohibited actions

Without separate applicable Path-B authority: no direct main push, force/history rewrite, agent-initiated or automation-initiated merge/mark-ready, auto-merge, tag/release, unknown-binary/model-API/external-reverse-tool execution, runner dispatch, secrets or destructive work. No personal R1 landing that fails any R1 final-acceptance carve-out condition; no R2/R3 landing under that carve-out. Preserve user edits, existing evidence and security boundaries.

## Stop conditions

Stop the affected action on missing approval, candidate-only authority, digest/material-edit mismatch, branch/base/head/scope/criteria drift, unauthorized risk/operation, invalid or changed Decision/plan, failed mandatory focused tests or exact-head CI, or exhausted budget. Missing independent exact-head acceptance blocks landing, not already-authorized implementation. Request revised bounded authority for scope/contract changes; never invent a Gate, receipt, verifier, mainline-authorization schema or tracked artifact family to unblock yourself. Report what is implemented, what was actually verified, and what remains blocked; do not label unverified work complete.
