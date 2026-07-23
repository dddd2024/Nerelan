# Architecture Spine v2

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Freeze the product and module boundary for a local-first trusted binary-analysis application without prematurely introducing distributed services.

## Authority

This document is the unique authority for product shape, module ownership, dependency direction, and the separation of the two workflow families. Object semantics, storage ownership, execution isolation, migration, and governance costs are authoritative in their named companion documents.

## Scope

The target is one Python modular monolith with one Web/API surface, one structured analysis metadata database, one content-addressed artifact store, distinct workflow checkpoint storage, and an isolated execution-worker boundary.

Target logical layout:

```text
reverse_agent/
  engineering/
  analysis/
    domain/
    application/
    ports/
    adapters/
  workflows/
    development/
    binary_analysis/
  infrastructure/
    persistence/
    artifacts/
    sandbox/
    telemetry/
  interfaces/
    api/
    web/
```

This is a target boundary, not authorization to move current files in P0.

## Non-goals

- No microservices, Kubernetes, distributed queue, event bus, or multiple primary databases.
- No Evidence/Claim implementation, database migration, durable workflow rollout, provider integration, or binary execution.
- No modification or integration of PR #9 in P0.

## Context

The repository currently combines engineering governance, reverse-solving code, mutable gate evidence, and reporting. The constitution establishes stable seams before later phases separate runtime ownership and migrate legacy state.

## Decisions

1. The initial deployment is a modular monolith.
2. Interfaces call application services or workflows; application and workflows depend on domain contracts; infrastructure implements ports.
3. Domain code depends only on the Python standard library, pure domain value objects, and stable protocols.
4. Domain code must not depend on LangGraph, GitHub, FastAPI, database drivers, IDA/Ghidra, OpenTelemetry, or Web UI code.
5. Development Workflow and Binary Analysis Workflow use different graphs, state schemas, checkpoint namespaces, risk models, authorization objects, terminal states, and failure semantics.
6. LangGraph is the only future workflow runtime; a second primary AgentRunner is prohibited.

Dependency direction:

```text
interfaces -> application/workflows -> domain
infrastructure adapters -> ports -> domain/application contracts
```

## Invariants

- Engineering acceptance never proves an analysis Claim.
- Analysis evidence never grants repository mutation authority.
- GitHub remains authoritative for branch, commit, PR, review, merge, release, and CI facts.
- Workflow checkpoint state never replaces GitHub truth or Analysis Repository truth.
- P0 freezes contracts only; it does not create runtime implementations.

## Interfaces

- Application ports expose repository, artifact, provider, authorization, and telemetry capabilities.
- Workflow state references domain identifiers and immutable artifact references; it does not embed large outputs.
- Interface adapters translate HTTP/Web/GitHub inputs into application commands without introducing domain dependencies.

## Failure modes

- A shared graph conflates engineering and analysis authorization.
- An adapter type leaks into domain objects.
- A report or checkpoint becomes a second mutable truth source.
- A runtime integration is started before its phase entry criteria are satisfied.

All fail closed at architecture review and must be corrected before the dependent phase unlocks.

## Security implications

Ports isolate credentials and provider execution from the domain. The isolated worker boundary prevents hostile inputs from inheriting repository, user-home, or GitHub access. Tainted analysis data cannot cross into engineering authorization without an explicit proposal/authorization/receipt bridge.

## Migration impact

P1 integrates and freezes PR #9 without mutating its accepted head. P2 contains legacy runtime evidence. P3 introduces domain contracts. Later phases add providers, sandboxing, validation, and durable workflows behind the frozen ports.

## Acceptance criteria

- Module ownership and dependency direction are explicit.
- The two workflows and bounded contexts are distinct.
- Every forbidden domain dependency is named.
- No P0 change implements or relocates runtime code.

## Related ADRs

- [ADR-001 Modular Monolith](../adr/ADR-001-modular-monolith.md)
- [ADR-002 Separate Development and Analysis Workflows](../adr/ADR-002-separate-development-and-analysis-workflows.md)
- [ADR-003 Separate Trust Bounded Contexts](../adr/ADR-003-separate-trust-bounded-contexts.md)
- [ADR-007 LangGraph Workflow Ownership](../adr/ADR-007-langgraph-workflow-ownership.md)
