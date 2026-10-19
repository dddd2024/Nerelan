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
| `landing-state-gate` | `state-gate.yml` | On a Ready PR, the latest trusted review verdict for the exact head is ACCEPT, or an eligible earlier ACCEPT carries over (reported as `accepted_carried_over`). On a Draft the job reports as `landing-state-gate-draft-inert`, so a Draft can never satisfy it. |

The ruleset requires the branch to be up to date with `main` before merging, so the checks always describe the exact merge candidate. Carry-over is only a review exception: `baseline`, `state-gate` and `landing-state-gate` must all be fresh and green on the current head H.

## Review verdicts

The landing gate (`python -m reverse_agent.landing_review review`) reads PR comments and reviews. A verdict is a line of the form:

```text
Nerelan-Review: ACCEPT <40-hex sha>
Nerelan-Review: REJECT <40-hex sha>
```

Rules:

- Only authors whose association is OWNER, MEMBER or COLLABORATOR count.
- Exact-head review is the default: only verdicts naming the exact current head count, so a new push normally needs a new review. The narrow carry-over exception below never overrides a trusted verdict on the exact head.
- The most recent verdict for that head wins, so REJECT after ACCEPT blocks again the next time the gate runs. The gate runs only on `pull_request` events (push, edit, Ready, Draft), not on new comments. An ACCEPT posted after marking Ready therefore needs a re-run, and a REJECT posted after a green gate only takes effect on the next run. That is why the merger re-checks with `python -m reverse_agent.landing_review verdict` immediately before merging.
- Quoted lines (`> ...`), lines inside fenced code blocks, dismissed or pending reviews, and entries without a timestamp never count.
- The checker module (`landing_review.py`) runs from the PR's base commit. The bootstrap PR that introduced it is the one exception: the base has no checker, so the candidate's checker runs.
- The **workflow file itself runs from the candidate** (GitHub uses the PR's version on `pull_request` events). A PR could therefore edit `state-gate.yml` to skip the verdict step. This is why `.github/workflows/**` changes are R2 and the reviewer must read the workflow diff. Closing the gap mechanically needs a ruleset change (require workflows from `main`, or pin required checks to the GitHub Actions app), and ruleset changes need a fresh Owner instruction.
- Only PRs into `main` can land. The ruleset still lists `owner/repository-modernization-v2-planning`, but that v1 planning branch is retired; PRs into it fail `landing-state-gate` by design.

### Carry-over exception

Owner decision 2026-10-19 approved this rule as written. Exact-head precedence applies first: if any trusted verdict names the current head H, it decides, even a REJECT, and carry-over is not evaluated.

Only when H has no trusted verdict may an ACCEPT at an earlier head carry forward across verified merge-main steps. Walking from H along first parents for at most 20 steps, every step must be a merge commit with exactly two parents; the second parent must be ancestral to the already-fetched `origin/main`; the automatic merge (`git merge-tree --write-tree <first> <second>`) must be conflict-free and its tree must equal the merge commit's tree; and the diff of `origin/main` against each head must have identical content and changed paths to the diff at H. The earlier head must have a latest trusted verdict of ACCEPT, and no trusted REJECT created after that ACCEPT may name the earlier head, any traversed merge commit or H. These checks use only local Git objects; any Git error, non-merge commit, unexpected parent count, tree mismatch, different diff or excluded path fails closed and yields no carry-over.

The exception excludes any change touching `AGENTS.md`, `docs/agents/**`, `.github/workflows/**`, `reverse_agent/landing_review.py`, `requirements*.txt`, `pyproject.toml`, `frontend/package.json` or `frontend/package-lock.json`. Excluded paths in either diff fail closed, so R2 governance changes, including this implementation, cannot qualify.

An accepted carry-over reports `accepted_carried_over`, with `accepted_head` naming the earlier reviewed head and `merge_commits` listing the traversed merge commits. It never waives CI: `baseline`, `state-gate` and `landing-state-gate` must still be fresh and green on H.

In a single-account repository the gate cannot prove who the reviewer was. It is a process control that leaves an auditable record, not a cryptographic one. The independence requirement is procedural: the reviewer must be a fresh context that did not author the change and must review the exact diff.

What a reviewer does:

1. Read the full diff of the exact head against `main`, plus the PR's claims.
2. Check correctness, scope, test adequacy and the risk tier. For R2, confirm the change matches the cited Owner decision and does not weaken controls beyond it.
3. Confirm CI is green on that head, or run the relevant suites.
4. Post findings, then the verdict line.

## Landing

After ACCEPT and green checks on the current head H: mark Ready, wait for `landing-state-gate`, then run the mandatory pre-merge re-check `python -m reverse_agent.landing_review verdict --repository dddd2024/Nerelan --pr <n> --head <sha>`, followed by `gh pr merge <n> --merge --match-head-commit <sha>`. The re-check is mandatory because the gate does not re-run when new comments arrive, and the `verdict` command applies the same exact-head and carry-over logic (reporting `accepted_carried_over` with `accepted_head` and `merge_commits` when applicable). If `main` moved, update the branch with a merge from `main` (never a rebase of a shared branch), let CI rerun, and either get a fresh verdict for the new head or satisfy the carry-over conditions; CI on H is never waived. After merging, verify `main` points to the merge commit.

## Delegation record

- 2026-10-11, Owner `dddd2024` in chat: Claude becomes sole developer; Codex no longer participates; Claude may use Nerelan itself for development and acts as supervisor.
- 2026-10-11, Owner `dddd2024` in chat, choosing between explicit options: "先简化治理再自动合并" (simplify governance first, then merge automatically), and permission to close superseded PRs.
- Earlier Owner delegation to the Codex controller, recorded under v1, is superseded by the above for development work.

Delegation never covers R3 actions: secrets, tags/releases, deployment, destructive user-data operations, untrusted binaries. Those need a fresh Owner instruction.

## Worktree guards

Before staging, list the tree and stage only the files the change owns. Untracked runtime scratch stays untracked. Before removing a stale worktree or clone, preserve its uncommitted diff (for example `git stash create` plus a `backup/*` ref, or a patch file) and keep its branch. Never use `git clean`, `reset --hard` or bare `git stash`, which uses the stack shared across worktrees, to make a tree look clean.
