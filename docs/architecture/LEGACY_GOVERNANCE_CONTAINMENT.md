# Legacy Governance Containment

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This document classifies repository components into containment tiers and defines the lifecycle for legacy governance assets. It does not authorize deletion, refactor, or behavior change in this round.

## Two authority paths

The project defines two authority paths (see `AGENTS.md` and `SOURCE_OF_TRUTH_MATRIX.md`):

- **Path A — ordinary R0/R1**: authority is the approved Work Item Issue body (R1 template) + deterministic checks. `decision_packet.md` and `command_plan.json` are **not** used.
- **Path B — transition / R2-R3**: authority is the bounded Decision + generated `command_plan.json` + `PRE_EXECUTION_AUTHORIZED`.

All authority labels in this document (e.g., "transition/R2-R3 authority only") refer to Path B unless explicitly stated otherwise. Ordinary R0/R1 work does not use `decision_packet.md` or `command_plan.json`.

## Containment tiers

### RETAIN

Components actively used by the current minimal-integration direction.

```text
reverse_agent/architecture/contracts.py
reverse_agent/architecture/risk.py
risk classification logic (R0-R3 classifier, path-risk floor, capability rules)
selected GitHub observation adapters (read-only)
deterministic tests under tests/
project_state/decision_packet.md (transition/R2-R3 authority only, Path B)
project_state/gates/command_plan.json (transition/R2-R3 command authority only, Path B)
docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md
docs/architecture/SOURCE_OF_TRUTH_MATRIX.md
AGENTS.md
```

Note: `decision_packet.md` and `command_plan.json` are authority for transition rounds and R2/R3 only (Path B). For ordinary R0/R1 work (Path A), the Work Item Issue body is the primary authority; these files are not used.

### READ_ONLY_COMPATIBILITY

Components preserved as read-only evidence. They may be read for audit but must not drive new behavior, and no new feature may depend on them as authority.

```text
legacy project_state readers (rounds/**, audits/**, context/**)
legacy Decision history (decision_packet.md in archived rounds)
legacy reports and archived evidence (codex_execution_report.md, execution_report.md, final_gate_result.json)
project_state/current_state.json
project_state/state_manifest.json
project_state/artifact_index.json
docs/audits/**
legacy docs/** governance bundles (state_governance_bundle.md, governance_operations_bundle.md, etc.)
```

### NO_NEW_FEATURES

Components that remain functional for existing Decisions but receive no new feature work. Bug fixes that do not expand scope are permitted only under an explicit bounded Decision.

```text
legacy closeout / final-seal / report-synthesis chain
legacy mainline authorization receipt variants (MainlineIntegrationReceipt and related schemas)
tracked per-run Gate evidence (project_state/gates/evidence/**)
legacy transition compatibility adapter (only the three documented responsibilities; no new responsibilities)
legacy local execution seal / reconciliation candidate chain
```

### DEFERRED

Components explicitly deferred as extension candidates. They are not current implementation scope. Starting any of these requires a new bounded Decision that reactivates the corresponding workstream.

```text
LangGraph production runtime (reverse_agent/workflows/development_graph.py stays non-dispatching)
Agent Registry
Web control console
Open SWE / OpenHands integration
Spec Kit repository bootstrap
all security/binary extension directions (Trust Layer, Binary Evidence Firewall, hostile-binary analysis)
reverse-solving, crash, patch, malware, or firmware product work
```

## Lifecycle

Legacy components move through the following states in order. A component may not skip a state. Each transition requires an explicit bounded Decision; this document does not authorize any transition.

```text
ACTIVE_COMPATIBILITY
-> READ_ONLY_COMPATIBILITY
-> ARCHIVED
-> REMOVED_FROM_RUNTIME
```

| State | Meaning |
|-------|---------|
| `ACTIVE_COMPATIBILITY` | Component runs for existing Decisions; no new features. |
| `READ_ONLY_COMPATIBILITY` | Component is preserved as evidence; no runtime behavior depends on it as authority. |
| `ARCHIVED` | Component is moved to an archive location (e.g., `docs/archive/**`, `project_state/rounds/**`); no runtime path reads it. |
| `REMOVED_FROM_RUNTIME` | Component is deleted from the repository. Requires explicit Decision and independent audit. |

## Current state assignments

| Component | Current state | Next target state |
|-----------|---------------|-------------------|
| Legacy closeout/final-seal/report-synthesis | ACTIVE_COMPATIBILITY | READ_ONLY_COMPATIBILITY (after R0/R1 pilots stabilize) |
| Mainline authorization receipt variants | ACTIVE_COMPATIBILITY | READ_ONLY_COMPATIBILITY |
| Tracked per-run Gate evidence | ACTIVE_COMPATIBILITY | READ_ONLY_COMPATIBILITY |
| Legacy `project_state/rounds/**` | READ_ONLY_COMPATIBILITY | ARCHIVED |
| Legacy `project_state/audits/**` | READ_ONLY_COMPATIBILITY | ARCHIVED |
| Legacy `docs/**` governance bundles | READ_ONLY_COMPATIBILITY | ARCHIVED |
| LangGraph production runtime | (not started) | DEFERRED |
| Agent Registry / Web console / Open SWE | (not started) | DEFERRED |

## Rules

1. No module deletion or production refactor belongs to the current round (Issue #26 / Issue #28).
2. Legacy components classified `NO_NEW_FEATURES` may receive only bug fixes that do not expand scope, and only under an explicit bounded Decision.
3. The compatibility adapter has exactly three responsibilities: (1) identify explicit transition Decisions; (2) convert the machine-generated command plan into typed command contracts; (3) dispatch an explicitly selected transition validator while leaving the legacy validator unchanged for every other Decision. No fourth responsibility may be added.
4. Transition mode is opt-in via `decision_contract.transition_kernel_required`. Missing, malformed, or non-boolean values fail nonzero; there is no silent pipeline choice.
5. Rollback of the transition kernel = restore unconditional legacy workflow routing, leaving the kernel modules installed.
6. `NO_NEW_FEATURES` is a **containment tier** label used in this document, not a reuse disposition. The reuse inventory (`ARCHITECTURE_SPINE_REUSE_INVENTORY.md`) uses only `KEEP / ADAPT / DEFER / ARCHIVE_CANDIDATE`.
7. After the transition round, ordinary R0/R1 work does not require `decision_packet.md` or `command_plan.json`. Those files are authority for transition rounds and R2/R3 only. R0/R1 Work Items are authorized by an approved GitHub Issue (R1 template) and deterministic checks. R2/R3 remain fail-closed.
8. Feature-branch push and Draft PR creation are R1 operations. Direct `main` push, force push, rebase, squash, tag, and release remain R2 or higher. `merge` and `mark-ready` of an accepted ordinary R1 PR are R1 operations under the narrow owner-manual-merge carve-out in `AGENTS.md` (a human-initiated repository owner/maintainer action performed personally through the GitHub UI or an owner-controlled CLI session, after all R1 final-acceptance conditions hold — including approved immutable Work Item snapshot with `base_sha`, allowed-path compliance, independent exact-head audit acceptance, exact-head CI success, `mergeable` status, and the full pre-merge re-observation); agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated `merge`/`mark-ready`, GitHub auto-merge, and `merge`/`mark-ready` of R2/R3 work items remain R2 or higher. The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used.
