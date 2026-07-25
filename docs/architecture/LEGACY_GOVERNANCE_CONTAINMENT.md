# Legacy Governance Containment

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This document classifies repository components into containment tiers and defines the lifecycle for legacy governance assets. It does not authorize deletion, refactor, or behavior change in this round.

## Containment tiers

### RETAIN

Components actively used by the current minimal-integration direction.

```text
reverse_agent/architecture/contracts.py
reverse_agent/architecture/risk.py
risk classification logic (R0-R3 classifier, path-risk floor, capability rules)
selected GitHub observation adapters (read-only)
deterministic tests under tests/
project_state/decision_packet.md (active round authority)
project_state/gates/command_plan.json (active command authority)
docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md
docs/architecture/SOURCE_OF_TRUTH_MATRIX.md
AGENTS.md
```

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
