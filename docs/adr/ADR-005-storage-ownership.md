# ADR-005: Storage Ownership

## Status

`ACCEPTED`

## Context

Metadata, large artifacts, workflow recovery state, telemetry, and portable proof have different consistency, retention, and security needs.

## Decision

Use logically separate Analysis Repository, content-addressed Artifact Store, LangGraph Workflow Store, and Telemetry Backend. The local-first implementations are SQLite metadata, local CAS, persistent LangGraph SQLite checkpointer, and an OpenTelemetry-compatible backend. Capsule manifests reference immutable payloads in the Artifact Store.

Git stores source, schemas, policy, docs, ADRs, deterministic fixtures, stable Decisions, and small immutable references/summaries—not ordinary runtime output.

## Alternatives considered

- One SQLite database for all state: rejected because authority and lifecycle boundaries would blur.
- Git for raw runtime artifacts: rejected due mutable/noisy source diffs and scale.
- Object store only: rejected because structured queries and workflow transactions require distinct stores.

## Consequences

Local operation remains possible, but adapters and retention policies must respect storage class. ArtifactRefs become first-class.

## Security implications

Run-scoped access and digest verification limit substitution and cross-run disclosure. Telemetry access does not imply artifact access.

## Migration implications

P2 stops new runtime-evidence commits; P3 onward introduces store ports and implementations.

## Revisit conditions

Physical backends may change with measured scale. Logical ownership and separation remain.
