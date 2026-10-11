# Governance v2 reference

Companion to [AGENTS.md](../../AGENTS.md). Read only the section the current action needs.

## Product boundaries

Nerelan's thin adapter layer is `reverse_agent/platform_v1/`. Reuse GitHub Spec Kit-compatible planning, LangGraph topology/checkpoints, OpenCode repository execution/model bindings and OpenHands presentation patterns; do not copy their runtimes or replicate GitHub Issue/PR state.

The trusted host owns one TaskStore database for task, goal, window, receipt, claim, run and publication truth. The unattended coordinator requires `REVERSE_AGENT_AUTONOMOUS=1` and an owner-activated bounded window before doing work. Live model/API probes require an explicit Owner instruction. Provider-free startup and CI make zero model calls. Runtime/module/environment names such as `reverse_agent` remain compatibility identifiers, not a request for a broader rename.

## Why v2

Under v1 every change needed an approved Issue digest or an immutable Decision packet, a generated command plan, transition preflight, an authority snapshot in the PR body and rebinding after every push. Any movement of `main` invalidated the snapshot. By 2026-10-11 about 95 PRs were open and nearly nothing was landing. The Owner chose to simplify governance first and then let verified changes land automatically. v2 keeps the controls that protect `main`: required CI, exact-head binding, independent review, merge-commit history, no force push. It drops the per-PR paperwork.

## Required checks

| Check | Workflow | What it proves |
| --- | --- | --- |
| `baseline` | `ci.yml` | Focused governance, platform and integration suites pass on the exact head. |
| `state-gate` | `state-gate.yml` | `git diff --check` is clean for the exact PR range; no runtime/scratch paths (`.platform_v1_runtime/`, `node_modules/`, `*.sqlite3`, `__pycache__/`) and no files over 5 MB are committed; governance unit tests pass. |
| `landing-state-gate` | `state-gate.yml` | On a Ready PR, the latest trusted review verdict for the exact head is ACCEPT. On a Draft the job reports as `landing-state-gate-draft-inert`, so a Draft can never satisfy it. |

The ruleset requires the branch to be up to date with `main` before merging, so the checks always describe the exact merge candidate.

## Review verdicts

The landing gate (`python -m reverse_agent.landing_review review`) reads PR comments and reviews. A verdict is a line of the form:

```text
Nerelan-Review: ACCEPT <40-hex sha>
Nerelan-Review: REJECT <40-hex sha>
```

Rules:

- Only authors whose association is OWNER, MEMBER or COLLABORATOR count.
- Only verdicts naming the exact current head count, so a new push needs a new review.
- The most recent verdict for that head wins, so REJECT after ACCEPT blocks again.
- The checker runs from the PR's base commit, so a PR cannot weaken the check that admits it. The single exception is the bootstrap PR that introduces the checker.

In a single-account repository the gate cannot prove who the reviewer was. It is a process control that leaves an auditable record, not a cryptographic one. The independence requirement is procedural: the reviewer must be a fresh context that did not author the change and must review the exact diff.

What a reviewer does:

1. Read the full diff of the exact head against `main`, plus the PR's claims.
2. Check correctness, scope, test adequacy and the risk tier. For R2, confirm the change matches the cited Owner decision and does not weaken controls beyond it.
3. Confirm CI is green on that head, or run the relevant suites.
4. Post findings, then the verdict line.

## Landing

After ACCEPT and green checks: mark Ready, wait for `landing-state-gate`, then run `gh pr merge <n> --merge --match-head-commit <sha>`. If `main` moved, update the branch with a merge from `main` (never a rebase of a shared branch), let CI rerun, and get a fresh verdict for the new head. After merging, verify `main` points to the merge commit.

## Delegation record

- 2026-10-11, Owner `dddd2024` in chat: Claude becomes sole developer; Codex no longer participates; Claude may use Nerelan itself for development and acts as supervisor.
- 2026-10-11, Owner `dddd2024` in chat, choosing between explicit options: "先简化治理再自动合并" (simplify governance first, then merge automatically), and permission to close superseded PRs.
- Earlier Owner delegation to the Codex controller, recorded under v1, is superseded by the above for development work.

Delegation never covers R3 actions: secrets, tags/releases, deployment, destructive user-data operations, untrusted binaries. Those need a fresh Owner instruction.

## Worktree guards

Before staging, list the tree and stage only the files the change owns. Untracked runtime scratch stays untracked. Before removing a stale worktree or clone, preserve its uncommitted diff (for example `git stash create` plus a `backup/*` ref, or a patch file) and keep its branch. Never use `git clean`, `reset --hard` or bare `git stash`, which uses the stack shared across worktrees, to make a tree look clean.
