# ADR-004: Unique Source of Truth

## Status

`ACCEPTED`

## Context

Mutable facts copied across Git, project_state, reports, workflow state, and remote systems drift and produce contradictory acceptance decisions.

## Decision

Assign each dynamic fact one mutable authority:

| Fact | Authority |
|---|---|
| product/architecture/story planning | BMAD Artifact |
| current engineering task | GitHub Issue/PR |
| branch, commit, CI, review, merge, release | GitHub |
| workflow run state | LangGraph Checkpointer |
| R2/R3 engineering authorization | Decision |
| exact high-risk commands | Command Plan |
| sample identity | SampleIdentity |
| Evidence, Claim, Validation | Analysis Repository |
| large content | CAS Artifact Store |
| traces, metrics, logs | Telemetry Backend |
| portable proof | Analysis Capsule |

Other locations may hold a reference, URI, digest, immutable snapshot, read-only projection, or cache, but never co-authority.

## Alternatives considered

- Eventual reconciliation among mutable mirrors: rejected because conflict resolution itself becomes another authority.
- Git as authority for every fact: rejected for runtime, remote, and large-artifact facts.
- Report prose as authority: rejected because projections are lossy and mutable.

## Consequences

Consumers must resolve authoritative sources or clearly label stale/unavailable projections. Some legacy convenience mirrors will be retired.

## Security implications

Attackers cannot gain authority by writing a lower-trust mirror. Digest-bound snapshots remain auditable without becoming mutable truth.

## Migration implications

P2 inventories duplicate mirrors and stops new writes before archive/removal.

## Revisit conditions

An authority may move only through a separately approved migration with single-writer cutover, verification, and rollback; two simultaneous authorities are never permitted.
