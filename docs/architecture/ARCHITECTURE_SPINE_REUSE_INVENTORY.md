# Architecture Spine Reuse Inventory

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

Per-module disposition for the Architecture Spine v1 codebase. Each module receives exactly one disposition: `KEEP`, `ADAPT`, `DEFER`, or `ARCHIVE_CANDIDATE`. No module deletion or production refactor belongs to the current round (Issue #26 / Issue #28).

## Disposition legend

| Disposition | Meaning |
|-------------|---------|
| `KEEP` | Retain as-is; actively used by the current direction. |
| `ADAPT` | Retain and adjust incrementally under a future bounded Decision; do not refactor now. |
| `DEFER` | Retain as compatibility/experiment; do not productize until a future Decision reactivates it. |
| `ARCHIVE_CANDIDATE` | Candidate for archive once an explicit Decision moves it to `READ_ONLY_COMPATIBILITY`. |

## Contracts (`reverse_agent/architecture/contracts.py`)

| Module / class | Disposition | Note |
|----------------|-------------|------|
| `PlanningReference` | KEEP | Read-only planning artifact reference; carries `command_authority: False` |
| `GitHubWorkItem` | KEEP | Task identity from GitHub; `identity` property `{repo}#{number}@{observation_ref}` |
| `WorkflowIdentity` | KEEP | Workflow execution identity (workflow_id, work_item, attempt, decision_id, round_id, policy_digest) |
| `ExecutionEnvelope` | KEEP | What the workflow wants to do (operations, paths, network, binary) |
| `AuthorizationRequirement` | KEEP | Trust authorization requirement invariant |
| `AuthorizationRequest` | KEEP | Authorization request object |
| `AuthorizationResult` | KEEP | Authorization result object |
| `ArchitectureDecision` | KEEP | Risk classification result (risk_tier, route, reasons) |
| `AcceptanceResult` | KEEP | Acceptance gate output (status, executable, reasons) |
| `PathRiskFloorSnapshot` | KEEP | Path-pattern to risk-tier floor mapping with glob/fnmatch |
| `CapabilityRiskRule` | KEEP | Operation-name to minimum RiskTier mapping |
| `RiskPolicySnapshot` | KEEP | Decision-bound immutable runtime policy (Phase D); carries decision_id/round_id and policy_digest |
| `DevelopmentWorkflowState` | KEEP | TypedDict for LangGraph state |
| `stable_json` / `SCHEMA_VERSION` | KEEP | Deterministic serialization helpers |

## Risk enums (`reverse_agent/architecture/risk.py`)

| Module / class | Disposition | Note |
|----------------|-------------|------|
| `RiskTier` (R0/R1/R2/R3) | KEEP | Core risk classification |
| `WorkflowRoute` | KEEP | Standard vs. TrustAuthorizationRequired routing |
| `AuthorizationStatus` | KEEP | Authorization result status |
| `AcceptanceStatus` | KEEP | Acceptance gate status |

## Workflow graph (`reverse_agent/workflows/development_graph.py`)

| Module / node | Disposition | Note |
|---------------|-------------|------|
| `load_work_item` node | DEFER | Part of non-dispatching shadow runtime; not a required product runtime |
| `load_planning_context` node | DEFER | Part of non-dispatching shadow runtime |
| `classify_risk` node | ADAPT | Risk classification logic is reused; the LangGraph node wrapper is deferred |
| `request_trust_authorization` node | DEFER | Part of non-dispatching shadow runtime |
| `acceptance_gate` node | DEFER | Part of non-dispatching shadow runtime |
| `_route` routing function | DEFER | Part of non-dispatching shadow runtime |
| `InMemorySaver` checkpointer | DEFER | Shadow runtime only |

The graph is explicitly **non-dispatching**. It validates fixtures, classifies risk, requests authorization, and calculates acceptance. It does not execute shell commands, mutate repos, access networks, invoke models, or run RE tools. It remains an experiment/compatibility asset; it must not drive a plan to build a full orchestration platform before a product direction exists.

## Control plane (`reverse_agent/control_plane/**`)

| Module | Disposition | Note |
|--------|-------------|------|
| `project_gate.py` (transition routing: `transition-lint`, `transition-command-plan`, `transition-preflight`) | KEEP | Thin routing for transition kernel |
| `project_gate.py` (legacy closeout/final-check/seal/report chain) | ARCHIVE_CANDIDATE | Legacy chain; containment tier is the no-new-features tier (see containment doc); reuse disposition is ARCHIVE_CANDIDATE because the chain is a candidate for archive after R0/R1 pilots stabilize. |
| Transition kernel validation implementation | KEEP | Fail-closed authorization path |
| Compatibility adapter (three responsibilities only) | KEEP | Identify transition Decisions; convert command plan; dispatch selected validator |
| Legacy closeout / final-seal / report-synthesis | ARCHIVE_CANDIDATE | Candidate for archive after R0/R1 pilots stabilize |
| Local execution seal / reconciliation candidate | ARCHIVE_CANDIDATE | Candidate for archive |
| Mainline authorization receipt variants | ARCHIVE_CANDIDATE | Candidate for archive |

## Tests (`tests/**`)

| Module | Disposition | Note |
|--------|-------------|------|
| `test_architecture_contracts.py` | KEEP | Contract round-trip validation |
| `test_risk_classifier.py` | KEEP | Risk classification tests |
| `test_planning_and_github_adapters.py` | KEEP | GitHub adapter tests |
| Legacy gate/closeout tests | ARCHIVE_CANDIDATE | Candidate for archive as legacy chain moves to READ_ONLY_COMPATIBILITY |
| v3 exact-head / premerge tests | ARCHIVE_CANDIDATE | PR #24 work; outside current round scope |

## Documentation (`docs/**`)

| Document | Disposition | Note |
|----------|-------------|------|
| `AGENTS.md` | KEEP | Root operating guide |
| `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` | KEEP | Single active top-level roadmap |
| `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md` | KEEP | Ownership map |
| `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md` | KEEP | This document |
| `docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md` | KEEP | This inventory |
| `docs/architecture/architecture-spine-v1.md` | KEEP | Architecture Spine v1 reference |
| `docs/architecture/legacy-control-plane-boundary.md` | KEEP | Legacy boundary reference |
| `docs/architecture/control-plane-transition-kernel.md` | KEEP | Transition kernel reference |
| `docs/roadmap/**` (all other roadmaps) | ARCHIVE_CANDIDATE | Classified SUPERSEDED or HISTORICAL_REFERENCE in the active roadmap |
| Legacy `docs/**` governance bundles | ARCHIVE_CANDIDATE | Candidate for archive |

## Rules

1. This inventory does not authorize deletion or refactor. Each `ARCHIVE_CANDIDATE` becomes `ARCHIVED` only under an explicit bounded Decision.
2. `KEEP` modules may still receive bug fixes under a bounded Decision; the disposition labels scope, not freeze.
3. `DEFER` modules are not started by this round. Reactivating any `DEFER` module requires a new bounded Decision.
4. The Architecture Spine contracts are inventoried individually. They are not accepted or rejected wholesale.
5. No new tracked per-run Gate artifact family is introduced by this inventory.
