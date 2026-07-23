# ADR-003: Separate Trust Bounded Contexts

## Status

`ACCEPTED`

## Context

Repository authorization proves permitted engineering action. Binary-analysis trust evaluates hostile or uncertain observations. Treating them as one model enables authority escalation.

## Decision

Engineering Control Plane and Binary Analysis Trust Domain are separate bounded contexts. Their sole execution bridge is ActionProposal -> Engineering authorization -> ActionAuthorization -> isolated provider -> ActionReceipt.

Engineering acceptance is never analysis validation, and analysis evidence never grants repository write access.

## Alternatives considered

- Shared Decision/Evidence status model: rejected because identical labels have different semantics.
- Allow providers to interpret Claims as permission: rejected as sample/model-controlled authority.
- Manual prose handoff: rejected because it loses scope, expiry, and provenance.

## Consequences

Adapters must translate between explicit contracts. Audit trails become longer but semantically precise.

## Security implications

The bridge fails closed and prevents tainted content from selecting commands, paths, credentials, or capabilities.

## Migration implications

Legacy mixed reports remain projections. P3-P8 implement the Trust Domain and bridge incrementally.

## Revisit conditions

Context boundaries are permanent; only contract field versions and adapter implementation may evolve.
