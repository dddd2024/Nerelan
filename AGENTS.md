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

## Risk tiers and authority model

The project uses a four-tier risk model. The authority required for each tier is different:

| Tier | Scope | Authority required | Path |
|------|-------|--------------------|------|
| R0 | read-only observation | none (standard path) | standard |
| R1 | bounded local edits (docs, tests, config) + feature-branch push + Draft PR creation | none (standard path) | standard |
| R2 | workflow/dependency/network/publication | bounded Decision in `project_state/decision_packet.md` + `command_plan.json` | Trust Authorization required |
| R3 | binary execution, debugging, secrets, destructive | bounded Decision in `project_state/decision_packet.md` + `command_plan.json` | Trust Authorization required |

### R0/R1 authority model (after the transition round)

After the one-time transition round that establishes this baseline, **ordinary R0/R1 work does not require a full Decision or Command Plan**. An R0/R1 Work Item is authorized by:

- an approved GitHub Issue using the `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml` template;
- the Issue's `allowed_paths`, `forbidden_operations`, and `acceptance_criteria` fields;
- deterministic checks (`pytest`, `git diff --check`, GitHub Actions).

`project_state/decision_packet.md` and `project_state/gates/command_plan.json` are **not** ordinary R0/R1 execution authority. They are authority for:

- transition rounds (when `transition_kernel_required=true`);
- R2/R3 operations (which fail closed without a bounded Decision).

### R2/R3 approval boundary

R2/R3 operations fail closed. They require:

- an explicit bounded Decision in `project_state/decision_packet.md` with `authorized_risk_tier: R2` or higher;
- a generated `command_plan.json` that lists the exact commands;
- `transition-preflight --mode pre` returning `PRE_EXECUTION_AUTHORIZED`.

No Issue, comment, or roadmap document can authorize R2/R3 work.

### Feature-branch push and Draft PR creation are R1

The following routine publication operations are classified as **R1** and do not require R2 authorization:

- pushing to a non-`main` feature branch (`git push origin <feature-branch>`);
- creating a Draft PR against `main` (`gh pr create --draft`);
- updating a Draft PR description (`gh pr edit`).

The following publication operations are **R2 or higher** and remain fail-closed without a bounded Decision:

- direct push to `main`;
- merge;
- force push;
- rebase;
- squash;
- tag or release;
- marking a PR ready for review (when the round requires Draft).

## R0/R1 allowed operations

- read repository state;
- edit documentation and tests within the Issue's `allowed_paths`;
- run `pytest`, `git diff --check`, and local lint;
- create a feature branch from `main`;
- push to the feature branch;
- create a Draft PR against `main`;
- update the Draft PR description.

## Startup checks

Before any work, an agent must:

1. Confirm the current branch and HEAD: `git status` and `git rev-parse HEAD`.
2. Confirm `main` is fixed at `38de9106d191d6b66d5f878354144817095e7bca` unless a later Decision has explicitly moved it.
3. Read the active GitHub Issue to identify `allowed_paths`, `forbidden_operations`, and `acceptance_criteria`.
4. If the work is R2/R3 or a transition round, read `project_state/decision_packet.md` and `project_state/gates/command_plan.json`.
5. If the active Decision requires the transition kernel, run the gate sequence below before any implementation.

## Source-of-truth order

Authoritative sources, in descending precedence:

1. `project_state/decision_packet.md` — round execution authority for transition rounds and R2/R3 only.
2. `project_state/gates/command_plan.json` — command authority for transition rounds and R2/R3 only.
3. Git — code and history.
4. GitHub — Issue, PR, check, and merge state.
5. `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` — product direction (planning reference only, never command authority).
6. `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md` — ownership map.
7. All other `docs/**` and legacy `project_state/**` artifacts — read-only compatibility evidence.

For ordinary R0/R1 work, the GitHub Issue (using the R1 template) is the primary authority. Roadmap documents, Issue comments, and audit notes are **planning references**; they do not authorize commands, file changes, closeout, or merge.

## Work Item acceptance requirements

A Work Item (GitHub Issue) is acceptable for R0/R1 work only when it captures:

- approved specification or explicit task goal;
- allowed paths;
- forbidden operations;
- acceptance criteria;
- required deterministic checks;
- Draft PR and human acceptance boundary.

An Issue does not itself authorize R2/R3 operations. See `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml`.

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
- Feature-branch push and Draft PR creation are R1 operations (see above).
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
- branch, base SHA, or allowed path differs from the active Issue or Decision;
- implementation requires source, test, dependency, or workflow changes not authorized;
- a new governance artifact family appears necessary;
- any operation would mutate an older Draft PR or `main`;
- focused tests fail for reasons inside the current round;
- exact-head CI is not green;
- independent audit has not accepted the final head.

When in doubt, stop and request a new bounded Decision. Do not create a new Gate, receipt, verifier, or mainline-authorization schema to unblock yourself.
