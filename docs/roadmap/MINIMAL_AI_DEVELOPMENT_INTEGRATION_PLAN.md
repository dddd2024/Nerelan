# Governed Unattended Multi-Agent Platform Plan

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
SUPERSEDES_AS_TOP_LEVEL_PLAN: #18, #25
```

This is the single active top-level roadmap for `reverse-agent`. It is planning reference only and never authorizes commands, file changes, closeout, or merge. The active product outcome is a local-first, unattended multi-Agent platform built as a thin trust layer around mature projects.

## Active development stack

```text
natural-language goal
-> persistent specification, plan, and dependent tasks
-> immutable authority plus owner-activated autonomous window
-> durable multi-Agent execution, reconciliation, and resume
-> deterministic validation and sanitized evidence
-> allowlisted Draft PR
-> independent exact-head acceptance
```

Repository-owned capability remains a thin trust layer: risk and authority classification, bounded path/operation policy, autonomous-window budgets, durable claims/idempotency, evidence confinement, exact-path Draft publication, and deterministic acceptance. Spec Kit, LangGraph, OpenCode, OpenHands Agent Canvas, and GitHub provide the mature planning, orchestration, execution, presentation, and repository surfaces.

## Permanent capability line — Context & Invocation Efficiency

**Context & Invocation Efficiency / 上下文与调用效率治理** is fixed as a permanent long-term mother-platform capability, not a temporary optimization experiment.

The platform must reduce unnecessary model context, repeated retrieval, repeated Agent exploration, tool payload, model calls, latency and cost while preserving durable truth, evidence, validation, authority, recovery and safety boundaries. The governing rules are: provide only context required now, exclude irrelevant context, and do not repeatedly provide already-known context unless provenance or independent verification requires re-reading the source.

The fixed detailed plan is [`context_invocation_efficiency_plan.md`](context_invocation_efficiency_plan.md). Its core direction includes:

```text
Run/Task/Agent/model-call cost attribution
Context Projection and history compaction from durable truth
Pack/Skill progressive disclosure
role/task-specific tool visibility and schema pruning
structured Agent Handoff Packets
stable-prefix / prompt-cache-aware compilation
tool-output reduction with raw evidence retention
code-intelligence adapters before broad repository reads
deterministic-action-first invocation
long-term cost-aware topology selection
```

This capability complements, but does not duplicate, [`model_access_quota_budget_plan.md`](model_access_quota_budget_plan.md): model access owns provider quota/accounting/budget/routing; Context & Invocation Efficiency reduces demand and explains where context/calls are spent. Economic/context optimization never widens repository, operation, permission or publication authority and never substitutes for required validation or independent acceptance.

## Two authority paths

### Path A — ordinary R0/R1

A template-created Issue is a **CANDIDATE**. It becomes ordinary R0/R1 authority only after a repository owner or maintainer applies the `r1-approved` label following review and the executor records an immutable authority snapshot in the Draft PR body.

The snapshot must contain:

```text
repository
issue_number
approval_state: APPROVED
approved_by
approval_event_or_time
body_digest_sha256: <normalized Issue-body SHA-256>
immutable_observation_ref
work_item_identity = {repository}#{issue_number}@{immutable_observation_ref}
target branch
base_sha
```

The approved Issue body supplies the task goal, allowed paths, forbidden operations, acceptance criteria, and required checks. Issue comments and PR comments are never authority. A material Issue-body edit changes `body_digest_sha256`, invalidates the previous snapshot, and requires reapproval before work continues.

`project_state/decision_packet.md` and `project_state/gates/command_plan.json` are not used for ordinary R0/R1.

### Path B — transition / R2-R3

Transition rounds and R2/R3 operations require a bounded approved Decision, generated Command Plan, and `PRE_EXECUTION_AUTHORIZED`. No Issue, label, comment, roadmap, or PR body can authorize R2/R3 work.

## Risk tier model

| Tier | Scope | Authorization path |
|------|-------|--------------------|
| R0 | read-only observation | Path A |
| R1 | bounded edits plus narrow R1 publication | Path A |
| R2 | workflow/dependency/unbounded-network/privileged-publication | Path B |
| R3 | binary execution, debugging, secrets, destructive operations | Path B |

### Narrow R1 publication

During Agent implementation, before independent exact-head acceptance, Path A permits only:

- push to the exact named non-`main` branch bound to the approved Work Item;
- create the exact Draft PR against `main`;
- update that Draft PR description.

These grants do not authorize the Agent to merge, mark-ready, directly push to `main`, rewrite history, perform workflow/dependency publication, cross-repository publication, credentials access, tag, or release. After independent exact-head acceptance, the separate owner-manual final-acceptance carve-out below may apply; it is not part of the Agent-implementation publication grant.

### R1 final acceptance — owner manual merge carve-out

After an ordinary R1 PR has been implemented, has passed required exact-head GitHub Actions, and has been accepted by independent exact-head audit, a repository owner/maintainer may personally perform `mark-ready` and `merge` of that PR without a separate Path-B Decision, provided all R1 final-acceptance conditions in `AGENTS.md` hold (approved immutable Work Item snapshot, allowed-path compliance, exact-head CI success, independent audit acceptance, no unresolved blocking review threads, and the full pre-merge re-observation).

This carve-out is a Path-A lightweight final-acceptance path for already-accepted ordinary R1 PRs. The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used. Permitted: a human-initiated owner/maintainer action performed personally through the GitHub UI or an owner-controlled CLI session. Path-B remains mandatory for agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated mark-ready/merge, and for GitHub auto-merge. The carve-out does not apply to R2/R3 work items.

The one-time rule migration that introduces this carve-out is itself R2/Path-B (it modifies the authority boundary). Future qualifying owner-manual acceptance is a Path-A carve-out.

## Base and branch rule

Ordinary R1 binds `base_sha` to the current approved `origin/main`. If the branch merge-base differs, stop. Path A does not rebase or rewrite history. Obtain a revised and reapproved Work Item, then create a fresh branch from the newly approved base.

## Legacy roadmap classification

All earlier roadmaps are non-active and classified as `HISTORICAL_REFERENCE`, `COMPATIBILITY_PLAN`, `EXTENSION_CANDIDATE`, or `SUPERSEDED`.

| File | Classification |
|------|----------------|
| `architecture_spine_attestation_policy_seal_v1.md` | SUPERSEDED |
| `architecture_spine_authority_closure_rework_v1.md` | SUPERSEDED |
| `architecture_spine_evidence_runtime_closeout_v1.md` | SUPERSEDED |
| `architecture_spine_provenance_integration_final_rework_v1.md` | SUPERSEDED |
| `architecture_spine_trusted_execution_cutover_rework_v1.md` | SUPERSEDED |
| `architecture_transition_next_24h.md` | HISTORICAL_REFERENCE |
| `closeout_order_provenance_rework_plan.md` | SUPERSEDED |
| `evidence_centered_user_solve_execution_plan.md` | SUPERSEDED |
| `next_step_after_fast_close_round_key_fix_audit.md` | HISTORICAL_REFERENCE |
| `next_step_after_scoped_metadata_foundation.md` | HISTORICAL_REFERENCE |
| `project_state_domain_taxonomy_supplement.md` | HISTORICAL_REFERENCE |
| `reverse_agent_larger_step_plan.md` | SUPERSEDED |
| `reverse_agent_normal_pace_plan.md` | SUPERSEDED |
| `reverse_agent_unified_architecture_and_trust_roadmap.md` | SUPERSEDED |
| `trustworthy_hostile_binary_analysis_long_term_plan.md` | EXTENSION_CANDIDATE |

## Extension candidates (deferred)

The following remain deferred until several real R1 pilots succeed:

```text
Open SWE self-hosting
security or binary product extensions
Trust Layer
Binary Evidence Firewall
```

## Platform V2 — implemented integration direction

Platform V2 binds the repository governance layer to reusable mature surfaces while keeping all authority server-side:

```text
Spec Kit-compatible Goal -> Specification -> Plan -> Tasks artifacts
LangGraph sequential and parallel team topology with checkpoints
OpenCode execution and model bindings
OpenHands Agent Canvas presentation patterns
GitHub Draft PR publication and check truth
```

The TaskStore is the single durable source for tasks, goals, windows, receipts, claims, runs, and publication state. The trusted coordinator is explicitly enabled and remains inert without an owner-confirmed bounded window. Draft publication excludes mark-ready and merge. Live provider experiments require separate R3 authority; provider-free CI makes zero model calls. This section is planning reference only and does not authorize commands, file changes, or merge.

## After acceptance

### Historical one-time transition (PR #27, superseded by the carve-out)

The following sequence was the one-time transition path used before the R1 final-acceptance carve-out reached `main`. It is historical transition history, not the active future rule:

```text
[Historical/one-time] separate R2 human merge Decision for the accepted exact head
-> merge PR #27 with expected-head protection
-> first real R1 pilot: align README.md with this roadmap
```

The README pilot must use the approved immutable Work Item model above. No extension candidate starts before that pilot is completed and audited.

### Active future rule (after the carve-out migration is in effect)

After the R1 final-acceptance carve-out migration is in effect, accepted ordinary R1 PRs no longer require a separate R2 merge Decision; the repository owner/maintainer may personally `mark-ready` and `merge` once all R1 final-acceptance conditions in `AGENTS.md` hold (including independent exact-head audit acceptance, exact-head CI success, `mergeable` status, and the full pre-merge re-observation). R2/R3 work and any Agent/automation-initiated merge still require Path-B.
