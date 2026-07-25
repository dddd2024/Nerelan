# Minimal AI Development Integration Plan

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
EXECUTION_AUTHORITY: NONE
SUPERSEDES_AS_TOP_LEVEL_PLAN: #18, #25
```

This is the **single active top-level roadmap** for `reverse-agent`. All other roadmap documents in `docs/roadmap/` are classified below as `HISTORICAL_REFERENCE`, `COMPATIBILITY_PLAN`, `EXTENSION_CANDIDATE`, or `SUPERSEDED`. No older document remains an independent active top-level roadmap.

This document is planning reference only. It does not authorize commands, file changes, closeout, or merge. Execution authority lives in `project_state/decision_packet.md` and `project_state/gates/command_plan.json`.

## Active development stack

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

## Current product scope

The project does not build a generic AI software-development platform. The current product scope is a **minimal integration layer** around mature development tools while product extensions remain undecided.

## Risk tier model

| Tier | Scope | Authorization |
|------|-------|---------------|
| R0 | read-only observation | standard path (no Decision required) |
| R1 | bounded local edits (docs, tests, config) + feature-branch push + Draft PR creation | standard path (no Decision required) |
| R2 | workflow/dependency/network/publication | bounded Decision + Trust Authorization |
| R3 | binary execution, debugging, secrets, destructive | bounded Decision + Trust Authorization |

After the one-time transition round (Issue #26 / Issue #28 / PR #27), ordinary R0/R1 development no longer requires a full Decision/Command Plan. An R0/R1 Work Item is authorized by an approved GitHub Issue (using the R1 template), its `allowed_paths` and `forbidden_operations`, and deterministic checks. `project_state/decision_packet.md` and `project_state/gates/command_plan.json` are authority for transition rounds and R2/R3 only, not ordinary R0/R1. R2/R3 remain fail-closed.

Feature-branch push (`git push origin <feature-branch>`) and Draft PR creation (`gh pr create --draft`) are R1 operations and do not require R2 authorization. Direct `main` push, merge, force push, rebase, squash, tag, and release remain R2 or higher.

## Legacy roadmap classification

Every prior roadmap in `docs/roadmap/` is classified below. None remains an independent active top-level roadmap.

| File | Classification | Note |
|------|----------------|------|
| `architecture_spine_attestation_policy_seal_v1.md` | SUPERSEDED | Architecture Spine v1 attestation rework; superseded by minimal-integration direction |
| `architecture_spine_authority_closure_rework_v1.md` | SUPERSEDED | Authority closure rework; superseded by minimal-integration direction |
| `architecture_spine_evidence_runtime_closeout_v1.md` | SUPERSEDED | Evidence/runtime closeout rework; superseded by minimal-integration direction |
| `architecture_spine_provenance_integration_final_rework_v1.md` | SUPERSEDED | Provenance integration rework; superseded by minimal-integration direction |
| `architecture_spine_trusted_execution_cutover_rework_v1.md` | SUPERSEDED | Trusted execution cutover rework; superseded by minimal-integration direction |
| `architecture_transition_next_24h.md` | HISTORICAL_REFERENCE | Gate bootstrap & Architecture Spine v1 merged execution plan; historical record of `decision_20260720` |
| `closeout_order_provenance_rework_plan.md` | SUPERSEDED | Closeout order provenance rework; legacy chain, no new features |
| `evidence_centered_user_solve_execution_plan.md` | SUPERSEDED | Evidence-centered user solve plan; product direction changed |
| `next_step_after_fast_close_round_key_fix_audit.md` | HISTORICAL_REFERENCE | Next-step recommendation after fast-close audit; historical only |
| `next_step_after_scoped_metadata_foundation.md` | HISTORICAL_REFERENCE | Next-step after scoped metadata foundation; historical only |
| `project_state_domain_taxonomy_supplement.md` | HISTORICAL_REFERENCE | Project state domain taxonomy; historical reference |
| `reverse_agent_larger_step_plan.md` | SUPERSEDED | Larger-step roadmap; superseded by minimal-integration direction |
| `reverse_agent_normal_pace_plan.md` | SUPERSEDED | Normal-pace plan; superseded by minimal-integration direction |
| `reverse_agent_unified_architecture_and_trust_roadmap.md` | SUPERSEDED | Unified architecture/trust long-term roadmap; superseded by minimal-integration direction |
| `trustworthy_hostile_binary_analysis_long_term_plan.md` | EXTENSION_CANDIDATE | Trustworthy hostile-binary analysis; deferred as extension candidate, not current scope |

## Extension candidates (deferred)

The following are **not current implementation scope**. They may be reconsidered only after several R1 pilots validate the minimal integration baseline:

```text
Spec Kit repository bootstrap
Open SWE self-hosting
persistent LangGraph workflow runtime
Web control console
specific security/binary product extension
Trust Layer
Binary Evidence Firewall
```

No decision to start any extension candidate is made by this roadmap.

## After acceptance

Once `MINIMAL_AI_DEVELOPMENT_INTEGRATION_BASELINE_ACCEPTED` is reached, the next step is one real R1 pilot using:

```text
small approved specification
-> GitHub Issue
-> Codex branch and implementation
-> deterministic GitHub Actions
-> independent review
-> human merge
```

Only after several pilots should the project decide whether it actually needs any extension candidate. No such decision is made in this roadmap.
