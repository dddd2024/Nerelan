# AGENTS.md

Repository operating guide for agents (Codex, human contributors, reviewers) working in `dddd2024/reverse-agent`.

## Repository purpose

`reverse-agent` is a governance and control-plane tooling repository. The current direction is a **minimal AI development integration baseline**: the project does not build a generic AI software-development platform.

The default development stack is:

```text
approved specification
-> GitHub Issue / Work Item
-> Codex implementation
-> GitHub Actions as deterministic validation
-> independent review
-> human merge
```

Repository-owned custom capability is limited to:

- thin risk classification
- bounded path/operation policy
- high-risk approval boundary
- deterministic acceptance checks
- future domain-specific adapters and verification logic

## Current non-goals

```text
generic LangGraph orchestration platform
generic Agent Registry
generic multi-agent organization
generic Web agent control console
GitHub Issue/PR state replication
generic checkpoint/retry/reconciliation platform
Open SWE fork or OpenHands control-plane product
specific hostile-binary, reverse-solving, crash, patch, malware, or firmware product work
```

Security and binary directions remain **extension candidates**, not current implementation scope.

## Two authority paths

The project defines two distinct authority paths. No source is globally higher when it is not applicable to the selected path.

### Path A — ordinary R0/R1 authority

For ordinary R0/R1 work (after the one-time transition round that establishes this baseline), authority is:

```text
approved Work Item Issue body (R1 template)
  + Issue allowed_paths / forbidden_operations / acceptance_criteria
  + deterministic checks (pytest, git diff --check, GitHub Actions)
```

The Work Item Issue body is the primary authority for R0/R1. Issue comments and PR comments are **never** authority. `project_state/decision_packet.md` and `project_state/gates/command_plan.json` are **not** used for ordinary R0/R1.

### Path B — transition / R2-R3 authority

For transition rounds (when `transition_kernel_required=true`) and R2/R3 operations, authority is:

```text
bounded Decision in project_state/decision_packet.md
  + generated command_plan.json
  + transition-preflight PRE_EXECUTION_AUTHORIZED
```

R2/R3 operations fail closed. No Issue, Issue comment, PR comment, or roadmap document can authorize R2/R3 work.

## Risk tiers and authority model

The project uses a four-tier risk model. Each tier selects one of the two authority paths above.

| Tier | Scope | Authority path | Path |
|------|-------|-----------------|------|
| R0 | read-only observation | Path A (no Decision required) | standard |
| R1 | bounded local edits + narrow R1 publication (see below) | Path A (no Decision required) | standard |
| R2 | workflow/dependency/unbounded-network/privileged-publication | Path B (bounded Decision + Trust Authorization) | Trust Authorization required |
| R3 | binary execution, debugging, secrets, destructive | Path B (bounded Decision + Trust Authorization) | Trust Authorization required |

### R1 publication — narrow exception

R1 publication is a **narrow exception** to the general rule that network/publication operations are R2. The following routine publication operations are classified as **R1** and do not require R2 authorization:

- pushing to a non-`main` feature branch (`git push origin <feature-branch>`);
- creating a Draft PR against `main` (`gh pr create --draft`);
- updating a Draft PR description (`gh pr edit`).

These R1 publication operations are bounded: they apply only to the exact named non-`main` branch bound to the Work Item, only to the exact Draft PR, and they forbid merge, mark-ready, and history rewrite.

### R2 publication/network — precisely bounded

The following publication and network operations are **R2 or higher** and remain fail-closed without a bounded Decision:

- direct push to `main`;
- merge;
- force push;
- rebase;
- squash;
- tag or release;
- marking a PR ready for review (when the round requires Draft);
- workflow/dependency publication;
- unbounded network access;
- cross-repository publication;
- credentials/secrets access;
- any operation outside the Work Item binding.

## R0/R1 allowed operations

- read repository state;
- edit documentation and tests within the Issue's `allowed_paths`;
- run `pytest`, `git diff --check`, and local lint;
- create a feature branch from the current `origin/main`;
- push to the non-`main` feature branch (R1 narrow publication exception);
- create a Draft PR against `main` (R1 narrow publication exception);
- update the Draft PR description (R1 narrow publication exception).

## Startup checks

Before any work, an agent must:

1. Confirm the current branch and HEAD: `git status` and `git rev-parse HEAD`.
2. Fetch and observe the current `origin/main` SHA: `git fetch origin main && git rev-parse origin/main`.
3. Confirm the Work Item Issue's `base_sha` equals the approved current `origin/main`. If the branch merge-base differs from the Work Item binding, stop and re-base or request a new Work Item.
4. Read the active GitHub Issue body (R1 template) to identify `allowed_paths`, `forbidden_operations`, and `acceptance_criteria`.
5. If the work is R2/R3 or a transition round, read `project_state/decision_packet.md` and `project_state/gates/command_plan.json`.
6. If the active Decision requires the transition kernel, run the gate sequence below before any implementation.

Permanent operating guidance does **not** hard-code a frozen `main` SHA. Ordinary R1 work uses the current `origin/main` SHA as approved by the Work Item. The historical transition base SHA remains valid only for the current transition round.

## Work Item acceptance requirements

A Work Item (GitHub Issue body, using the R1 template) is acceptable for R0/R1 work only when it captures:

- approved specification or explicit task goal;
- allowed paths;
- forbidden operations;
- acceptance criteria;
- required deterministic checks;
- `base_sha` bound to the current `origin/main`;
- Draft PR and human acceptance boundary.

An Issue body does not itself authorize R2/R3 operations. Issue comments and PR comments are never authority. See `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml`.

## Test commands

Focused regression (authorized for this round):

```bash
python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q
git diff --check
```

Transition gate sequence (only when the active Decision requires the transition kernel):

```bash
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre
```

Do not run a full repository test unless the Decision compiler makes it mandatory.

## Branch and PR rules

- Work on a feature branch, never directly on `main`.
- Feature-branch push and Draft PR creation are R1 narrow publication operations (see above).
- Open a **Draft PR** against `main` for review.
- PR creation is the publication boundary; merge remains separately authorized and human-controlled.
- Keep the PR Draft until independent audit accepts the final head.

## Prohibited actions

```text
direct push to main
force push
rebase
squash
merge without explicit authorization
tag or release
unknown-binary execution
model API invocation from repository code
external reverse-tool invocation
runner dispatch
automatic merge
```

## Stop conditions

Stop immediately, rather than inventing a new governance artifact, when:

- the Decision or generated Command Plan does not validate (transition rounds only);
- branch, base SHA, or allowed path differs from the active Issue body or Decision;
- implementation requires source, test, dependency, or workflow changes not authorized;
- a new governance artifact family appears necessary;
- any operation would mutate an older Draft PR or `main`;
- focused tests fail for reasons inside the current round;
- exact-head CI is not green;
- independent audit has not accepted the final head.

When in doubt, stop and request a new bounded Decision. Do not create a new Gate, receipt, verifier, or mainline-authorization schema to unblock yourself.
