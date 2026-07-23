# ADR-002: Separate Development and Analysis Workflows

## Status

`ACCEPTED`

## Context

Engineering delivery and binary analysis have different identities, risks, authorization objects, evidence, and terminal states.

## Decision

Development Workflow and Binary Analysis Workflow use separate LangGraph graphs, State Schemas, checkpoint namespaces, risk models, authorizations, terminal states, and failure semantics. No generic graph may process both.

Development ends in reviewed human merge/release state. Binary analysis ends in Claims, validation results, and a portable Analysis Capsule.

## Alternatives considered

- One universal workflow with conditional nodes: rejected because state and authority would be conflated.
- Separate business code but shared checkpoint namespace: rejected because identity and recovery could cross-contaminate.
- Keep ad-hoc runners: rejected because LangGraph is the single future workflow runtime.

## Consequences

Some orchestration utilities may be duplicated or factored into non-authoritative libraries. Cross-workflow handoff must use explicit identifiers and contracts.

## Security implications

Binary-derived inputs cannot become repository commands through shared workflow state. CI success cannot promote a Claim to verified.

## Migration implications

PR #9 remains a non-dispatching Development Workflow baseline. Durable Binary Analysis Workflow arrives only after domain contracts and sandbox boundaries exist.

## Revisit conditions

The separation is constitutional. Shared implementation helpers may be revisited; graph/state/namespace/authority separation may not.
