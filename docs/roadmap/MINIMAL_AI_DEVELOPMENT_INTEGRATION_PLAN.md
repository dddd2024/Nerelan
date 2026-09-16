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

## Capability-aware critical-path scheduling

**Priority and execution capability are separate axes.** Product and milestone priority determines what matters most; the execution surfaces currently available determine which ready slice of that priority can be executed now.

A missing user-local shell or runtime is therefore not a project-level blocker while useful work on the active critical path remains executable through GitHub, CI, remote observation, or a trusted worker. GitHub-native implementation, review, CI, static verification, documentation, and repository-state work are real development when they advance the current milestone.

The permanent scheduling loop is:

```text
1. choose the highest-priority active milestone;
2. enumerate its remaining implementation, verification, and validation slices;
3. classify each slice by the execution surface it actually requires;
4. execute the highest-value slice that is runnable on the surfaces currently available;
5. keep unavailable slices explicitly BLOCKED_BY_CAPABILITY, not BLOCKED_PROJECT;
6. do not jump to unrelated lower-priority feature work merely because one
   higher-priority runtime-validation slice is temporarily unavailable;
7. use remote/CI-capable work to prepare implementation, fixtures, telemetry,
   evidence, and deterministic checks so later runtime windows are spent on
   real validation rather than avoidable setup;
8. when trusted-worker or user-local capacity appears, consume the
   highest-priority accumulated runtime-validation backlog first.
```

Scheduling classes align with the execution-surface model owned by #156:

```text
GitHub / remote-preparable
  code changes, Issue/PR work, review, static analysis, CI, deterministic tests,
  documentation, governance, and other repository-native work.

trusted_worker / ci_only
  real checkout, build, test, headless browser E2E, provider/model execution,
  restart/recovery exercises, and other runtime evidence that can execute away
  from the user's workstation.

user_local
  genuinely machine-specific validation only: Windows-only local state,
  desktop/local UX, hardware, local applications, or credentials/sessions that
  cannot safely or technically execute elsewhere.
```

`github_control_plane`, `trusted_worker`, `ci_only`, `remote_observation`, and `user_local` remain distinct execution surfaces under #156. This roadmap section does not redefine their authority or permit an unavailable surface to be silently substituted with a broader one.

The scheduling distinction is:

```text
BLOCKED_BY_CAPABILITY
  the slice cannot run on any execution surface currently available;
  the milestone remains active and other runnable critical-path slices continue.

BLOCKED_PROJECT
  no useful authorized slice of the active milestone can progress on any
  currently available surface, or an actual project-level dependency blocks it.
```

When real-provider dogfood or another top-priority validation requires a temporarily unavailable runtime, development should continue on remote-preparable prerequisites and blockers for that same milestone. Once an appropriate trusted-worker or user-local window becomes available, runtime validation takes precedence over ordinary lower-priority remote work.

This is a scheduling rule, not execution authority. Every selected slice still follows the applicable Path A or Path B authority, risk, publication, and exact-head verification rules below.

## Execution Drift Control

Nerelan must not depend on late human intuition to notice that execution has diverged from the intended design. Non-trivial work is therefore treated as a closed-loop process in which assumptions are made explicit, implementation proceeds in bounded slices, observed evidence is reconciled with the designed state, and material deviations cannot silently rewrite the plan.

The execution loop is:

```text
Requirement / Design
-> Assumption Register
-> Execution Invariants
-> Pre-mortem
-> Small implementation slice
-> Evidence
-> Reality Reconciliation
-> CONTINUE / REPLAN / RETURN_TO_DESIGN / STOP
```

### Execution invariants

Before implementation expands, record the properties that must remain true while the work proceeds. Invariants may cover authority, product behavior, state truth, execution surface, scope, compatibility, safety, complexity budget, or other design commitments. A violated invariant is explicit drift evidence: execution must not silently continue past it.

Examples include:

```text
frontend state must be derived from real backend/runtime truth;
missing user_local capability must not become a project-wide blocker;
GitHub remains publication/check truth;
no new governance family is introduced merely to patch a normal-path defect;
implementation stays inside the approved product and path scope.
```

### Staged implementation and early falsification

Large tasks should be decomposed into independently verifiable slices rather than executed end-to-end before validation. Each meaningful slice ends with an explicit `GO / REVISE / STOP`-equivalent decision before the next slice expands scope. Prefer falsifying a design assumption early to discovering the same defect after a large implementation has accumulated around it.

### Pre-mortem before high-impact implementation

Before a high-impact slice, ask how the proposed design is most likely to fail. Credible failure modes should become acceptance criteria, checks, fixtures, telemetry, recovery scenarios, or explicit known gaps where practical. The objective is not to predict every failure; it is to surface cheap-to-test failure hypotheses before implementation cost rises.

### Drift triggers

Where possible, drift should be detected from observable project evidence rather than intuition alone. The following are examples of signals that require review instead of indefinite patching:

```text
repeated re-anchor or rework cycles;
unexpected material scope expansion;
repeated failures with different root causes;
runtime evidence contradicting the designed state model;
a newly required execution surface that the design did not declare;
governance overhead becoming disproportionate to semantic product work;
implementation repeatedly crossing assumptions that were never made explicit.
```

Owning Work Items may define bounded thresholds appropriate to their scope. This planning rule does not itself introduce a new workflow gate, authority object, or mandatory artifact family.

### Correction classification

Corrections are classified by the level at which the original model remains valid:

```text
L1 IMPLEMENTATION_CORRECTION
  Design and plan remain valid; fix a bounded implementation, configuration,
  integration, or test defect and continue within the approved scope.

L2 PLAN_CORRECTION
  Goal and design remain valid, but task decomposition, sequencing, execution
  path, or implementation plan must change before execution continues.

L3 DESIGN_CORRECTION
  A core assumption, interface, state model, architecture, UX model, or execution
  premise is invalid. Stop expanding implementation and return to design before
  continuing product work on the affected slice.
```

This classification prevents architectural defects from being patched indefinitely as L1 bugs and prevents bounded implementation bugs from triggering unnecessary redesign.

### Reality reconciliation

After every meaningful implementation slice, compare `DESIGNED_STATE` with `OBSERVED_STATE` using available evidence. Reconciliation records invalidated assumptions, newly discovered constraints, unresolved gaps, and whether the next planned slice is still justified.

The disposition is explicit:

```text
CONTINUE
  evidence remains consistent with the design and plan;

REPLAN
  the design still holds but the implementation path must change;

RETURN_TO_DESIGN
  a design-level assumption or model has been invalidated;

STOP
  authority, safety, scope, dependency, or evidence conditions do not justify
  further execution.
```

### No silent plan mutation

Agents may discover better evidence while executing, but material deviation from the approved or recorded plan must become explicit before proceeding. At minimum record:

```text
original assumption or plan;
new evidence;
impact;
proposed correction;
L1 / L2 / L3 classification;
chosen disposition: CONTINUE / REPLAN / RETURN_TO_DESIGN / STOP.
```

This does not require human approval for every bounded R0/R1 correction. Authority still comes from the existing Path A / Path B model, and a correction that exceeds the active authority must obtain the appropriate authority before continuing.

### Progressive proof

Architecture and product design are progressively proven through bounded implementation evidence and real-world dogfood, not assumed complete because a planning document exists. An invalidated assumption is expected input to the next design round. Repeated discovery of the same failure class without updating the design, coverage checks, assumptions, or acceptance model is a process failure and should trigger reconciliation of the design system itself.

Execution Drift Control complements capability-aware scheduling: capability-aware scheduling decides **which critical-path slice can run now**; drift control decides **whether the current slice is still following a valid design and plan**. Neither section creates execution authority or weakens existing risk, publication, or exact-head verification rules.

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
