# Storage and Artifact Ownership

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Assign one owner to metadata, large artifacts, workflow checkpoints, telemetry, and portable proof bundles.

## Authority

This document is the unique authority for storage-class ownership and what belongs inside ordinary Git commits.

## Scope

The local-first target uses four logically separate stores even when all are hosted on one machine:

| Storage class | Initial implementation | Authoritative content |
|---|---|---|
| Analysis Repository | SQLite | structured analysis metadata, Evidence/Claim/Validation relationships |
| Artifact Store | local content-addressed store | binaries, stdout/stderr, traces, exports, dumps, screenshots, large evidence, Capsule payloads |
| Workflow Store | persistent LangGraph SQLite checkpointer | workflow state, interrupts, resumptions, retry/idempotency state |
| Telemetry Backend | OpenTelemetry-compatible backend | traces, metrics, logs, latency, cost, retry, exceptions, health |

Analysis Capsule manifests are portable proof metadata; their referenced payloads remain in the Artifact Store.

## Non-goals

- No database, CAS, checkpointer, telemetry backend, or migration implementation in P0.
- No physical service split is required initially.

## Context

The current worktree often co-locates source, mutable gate output, raw evidence, and reports. This causes noisy diffs and duplicate truth. Logical ownership must be frozen before physical migration.

## Decisions

Keep in Git:

```text
source, tests, JSON Schema, policy, ADRs, architecture docs,
deterministic fixtures, stable Decisions, ArtifactRefs/digests,
small immutable summaries
```

Keep outside ordinary source commits:

```text
stdout/stderr, raw trace bodies, binaries, decompiler exports,
screenshots, memory dumps, debugger sessions, normal test logs,
workflow checkpoints, Capsule payloads, large execution evidence
```

Git may retain an ArtifactRef with `uri`, `digest`, `size`, `media_type`, `producer`, `created_at`, `retention_class`, and `verification_status`.

## Invariants

- Every mutable fact has one storage authority.
- A cache, report, snapshot, or projection cannot claim co-authority.
- Workflow Store contains orchestration state, not Claims.
- Telemetry Backend contains operational observations, not EvidenceUnits by default.
- Artifact content is addressed and verified by digest.

## Interfaces

- AnalysisRepositoryPort reads/writes structured domain metadata.
- ArtifactStorePort puts/gets immutable content by digest and returns ArtifactRef.
- Checkpointer is accessed only by the owning workflow namespace.
- TelemetryPort emits operational signals without domain imports.
- Capsule export resolves immutable references without relocating authority.

## Failure modes

- One SQLite file mixes workflow and analysis truth.
- A mutable report becomes the only location of a Claim.
- Large raw output is committed to Git.
- A URI is trusted without digest verification.
- Telemetry is queried as evidence without an explicit promotion adapter.

## Security implications

Content-addressing detects replacement; logical separation limits accidental authority escalation. Artifact access must be scoped by AnalysisRun and retention policy. Sensitive/hostile payloads remain inaccessible to Web and engineering processes unless an authorized adapter requests them.

## Migration impact

P2 stops new legacy runtime evidence commits and introduces references. P3 creates repository contracts. P4-P10 progressively populate the stores. Physical service separation remains optional until measured need.

## Acceptance criteria

- Metadata, artifact, checkpoint, telemetry, and Capsule ownership are unique.
- Git inclusion/exclusion rules are explicit.
- ArtifactRef mandatory metadata is defined.
- Logical separation does not require premature microservices.

## Related ADRs

- [ADR-005 Storage Ownership](../adr/ADR-005-storage-ownership.md)
- [ADR-007 LangGraph Workflow Ownership](../adr/ADR-007-langgraph-workflow-ownership.md)
- [ADR-009 Telemetry Is Not Analysis Evidence](../adr/ADR-009-telemetry-is-not-analysis-evidence.md)
