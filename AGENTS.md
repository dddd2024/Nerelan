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
```

For this minimal model, `immutable_observation_ref` is the approved normalized Issue-body SHA-256 digest unless GitHub supplies a stronger immutable revision reference. The approved Issue body, exact digest, allowed paths, forbidden operations, acceptance criteria, branch, and base SHA together form the Path-A authority snapshot.

Issue comments and PR comments are never authority. A material Issue-body edit changes the digest, invalidates the previous snapshot, and requires owner/maintainer reapproval plus a new snapshot before execution continues.

`project_state/decision_packet.md` and `project_state/gates/command_plan.json` are not used for ordinary R0/R1 work.

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

Only these network/publication operations are R1:

- push to the exact named non-`main` branch bound to the approved Work Item;
- create the exact Draft PR against `main`;
- update that Draft PR description.

They do not authorize merge, mark-ready, direct `main` push, history rewrite, cross-repository publication, tag, or release.

### R2 publication/network

The following require Path B:

- direct push to `main`;
- merge or mark-ready;
- force push, rebase, squash, or another history rewrite;
- workflow/dependency publication;
- unbounded network access or cross-repository publication;
- credentials or secrets access;
- tag or release;
- any operation outside the approved Work Item binding.

## R0/R1 allowed operations

- observe repository and GitHub state;
- edit only the approved `allowed_paths`;
- run approved deterministic checks;
- create a fresh feature branch from the approved current `origin/main`;
- use the narrow R1 publication exception for the exact branch and Draft PR.

## Startup checks

Before Path-A work:

1. Confirm the repository, current branch, and HEAD.
2. Fetch and observe current `origin/main`.
3. Read the Issue body and verify it was created from the R1 template.
4. Confirm the `r1-approved` label was applied by a repository owner or maintainer.
5. Normalize the Issue body and compute its SHA-256 digest.
6. Confirm the Draft PR authority snapshot records the same digest, approver, approval event/time, repository, Issue number, branch, and `base_sha`.
7. Confirm the branch merge-base equals the approved `base_sha`.
8. Confirm requested paths and operations remain inside the approved Work Item.

If the branch merge-base differs, **stop**. Do not rebase or rewrite history under Path A. Obtain a revised and reapproved Work Item, then create a fresh branch from the newly approved base. Intentional history rewriting requires separate Path-B authorization.

Permanent guidance never hard-codes a historical `main` SHA. The historical transition base applies only to its transition Decision.

For Path-B work, also read the active Decision and generated Command Plan, run the required gate sequence, and require `PRE_EXECUTION_AUTHORIZED` before implementation.

## Work Item acceptance requirements

A Path-A Work Item is usable only when it captures:

- approved specification or task goal;
- exact allowed paths;
- forbidden operations;
- acceptance criteria;
- required deterministic checks;
- exact target branch and current `origin/main` base SHA;
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
merge without explicit authorization
mark ready without explicit authorization
tag or release
unknown-binary execution
model API invocation from repository code
external reverse-tool invocation
runner dispatch
automatic merge
```

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
