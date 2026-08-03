# Source-of-Truth Matrix

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This matrix identifies the authoritative source for each fact class. It does not itself authorize commands, file changes, closeout, or merge.

## Two authority paths

### Path A — ordinary R0/R1

A template-created Issue is a **CANDIDATE**. Path-A authority activates only when a repository owner or maintainer applies `r1-approved` after review and the Draft PR body records an immutable Work Item authority snapshot.

```text
approved Issue body
+ approved_by: <repository owner or maintainer>
+ approval_event_or_time
+ body_digest_sha256: <normalized Issue-body SHA-256>
+ immutable_observation_ref
+ target branch and base_sha
+ deterministic checks
```

The Work Item identity is:

```text
{repository}#{issue_number}@{immutable_observation_ref}
```

Issue comments and PR comments are never authority. A material Issue-body edit changes `body_digest_sha256`, invalidates the previous snapshot, and requires reapproval.

### Path B — transition / R2-R3

```text
bounded APPROVED Decision
+ generated command_plan.json
+ transition-preflight PRE_EXECUTION_AUTHORIZED
```

R2/R3 fail closed. No Issue body, label, comment, roadmap, or PR body can authorize Path-B operations.

## Ownership map

| Fact class | Authoritative source | Applicable path | Notes |
|------------|----------------------|-----------------|-------|
| Product direction | `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` | planning | Planning reference only |
| Candidate R1 task | GitHub Issue body from R1 template | Path A | Not authority until approved and snapshotted |
| R1 approval state | GitHub `r1-approved` label event by owner/maintainer | Path A | `approved_by` and event/time recorded in Draft PR snapshot |
| Approved R1 task scope | Normalized approved Issue body + `body_digest_sha256` | Path A | Digest change invalidates prior authority |
| R1 authority identity | `{repository}#{issue_number}@{immutable_observation_ref}` | Path A | Observation ref is approved body digest unless a stronger immutable revision exists |
| Issue comments / PR comments | none | neither | Never authority |
| Code and history | Git | both | Commits, branches, trees, tags |
| PR/check/merge state | GitHub | both | GitHub is authoritative |
| Ordinary validation | `pytest`, `git diff --check`, GitHub Actions | both | Deterministic checks |
| Transition/R2-R3 execution authority | `project_state/decision_packet.md` | Path B only | Not ordinary R0/R1 authority |
| Transition/R2-R3 command authority | `project_state/gates/command_plan.json` | Path B only | Generated from the active Decision |
| Narrow feature-branch/Draft-PR publication | Approved Work Item snapshot | Path A | Exact non-main branch and exact Draft PR only |
| Runtime logs/artifacts | Local filesystem or Actions Artifact | n/a | Not tracked source state except the one-time transition exception |
| JSON contracts | `reverse_agent/architecture/contracts.py` | n/a | Existing `GitHubWorkItem.immutable_observation_ref` is retained |
| Legacy `project_state/**` | Read-only compatibility evidence | n/a | Cannot independently authorize work |

## One-time tracked transition-evidence exception

The active transition round may track only these compiler-required compatibility files:

```text
project_state/decision_packet.md
project_state/gates/command_plan.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
project_state/gates/bootstrap_state.json
project_state/gates/startup_snapshot.json
```

They are not the normal R0/R1 model. No new tracked per-run artifact family may be created.

## Approval and invalidation rules

1. Creating an Issue from the template produces `CANDIDATE`, not authority.
2. Only a repository owner or maintainer may activate Path A by applying `r1-approved` after review.
3. The Draft PR body records repository, Issue number, `APPROVED`, `approved_by`, approval event/time, `body_digest_sha256`, immutable observation reference, identity, target branch, and base SHA.
4. The executor and reviewer recompute `body_digest_sha256` from the current normalized Issue body.
5. A material Issue-body edit invalidates the snapshot. Work stops until a new owner/maintainer approval and new snapshot are recorded.
6. Comments never modify authority.
7. If the approved base no longer matches the branch merge-base, Path A stops. It does not rebase or rewrite history; a revised Work Item and fresh branch are required.

## Publication boundary

Path A permits push to the exact approved non-`main` branch and creation/update of the exact Draft PR. Direct `main` push, force push, rebase, squash, release, tag, cross-repository publication, unbounded network, credentials, or operations outside the snapshot require Path B.

`merge` and `mark-ready` are Path-A only under the narrow R1 final-acceptance carve-out in `AGENTS.md`: a repository owner/maintainer may personally perform `mark-ready` and `merge` of an already-accepted ordinary R1 PR when all R1 final-acceptance conditions hold (approved immutable Work Item snapshot, allowed-path compliance, exact-head CI success, independent audit acceptance, no unresolved blocking review threads, `mergeable` status, and the full pre-merge re-observation). The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used. Permitted: a human-initiated owner/maintainer action performed personally through the GitHub UI or an owner-controlled CLI session.

Agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated `merge` or `mark-ready`, GitHub auto-merge, and `merge`/`mark-ready` of R2/R3 work items or of R1 PRs that fail any final-acceptance condition remain Path-B.

## Cross-Agent memory layers

Different Agent products do not automatically share private memory. The following layers are defined in `docs/architecture/CROSS_AGENT_CONTEXT_CONTRACT.md` and recorded here so their authority status is explicit.

| Memory layer | Authoritative source | Applicable path | Notes |
|--------------|----------------------|-----------------|-------|
| Repository-backed shared state | tracked files at an exact commit | both | Shared project fact only at the exact commit read |
| GitHub-backed shared state | verifiable GitHub state | both | Comments and Issue bodies are not Path-B authority |
| Product/platform memory | ChatGPT/Codex/OpenHands/Claude/Cursor/Trae product configuration | neither | Not automatically visible to another Agent product; not repository policy |
| Agent-local persistent memory | role assumptions, prior summaries, cached constraints | neither | Advisory only unless grounded in current repository or GitHub authority |
| Run/session scratch state | current conversation, scratchpad, runtime state | neither | Not assumed to survive or transfer to another Agent |
| User-provided transient context | in-session user input | neither | Advisory only; must be grounded in tracked files before being treated as policy |

Product/platform memory, Agent-local persistent memory, run/session scratch state, and user-provided transient context are not authority unless independently grounded in the current repository or GitHub state. Private Agent memory is not repository policy. A constraint local to one Agent product does not establish a repository-wide prohibition.

## Non-authoritative sources

- roadmap text as execution authority;
- Issue comments and PR comments;
- candidate Issues without verified approval and immutable snapshot;
- local CI mirrors;
- legacy closeout/final-seal/report artifacts;
- `project_state/current_state.json` and `state_manifest.json`;
- product/platform memory and Agent-local memory as repository policy;
- run/session scratch state and user-provided transient context as repository policy;
- any new tracked per-run artifact family.
