# Analysis Data Contracts

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Freeze the external object boundaries and version rules required before implementing the Analysis Trust Domain.

## Authority

This document is the unique authority for analysis object semantics, identity, immutability, revision, and interchange policy.

## Scope

The first contract set is: AnalysisRun, SampleIdentity, ArtifactRef, EvidenceUnit, TrustLevel, TaintLabel, Claim, ClaimRevision, EvidenceRelation, InfluenceRelation, ValidationExperiment, ValidationResult, ActionProposal, ActionAuthorization, ActionReceipt, CapsuleManifest, and TrustPolicySnapshot.

## Non-goals

- No Python model, JSON Schema file, database table, migration, repository, or API implementation in P0.
- No final field-level serialization layout beyond mandatory semantic fields.

## Context

External contracts must outlive any Python class or storage adapter. Therefore versioned JSON Schema will be the interchange standard; Python models are implementations of that standard.

## Decisions

### Identity and provenance

- AnalysisRun scopes one analysis effort.
- SampleIdentity binds stable hashes and normalization metadata to the exact input.
- ArtifactRef carries URI, digest, size, media type, producer, creation time, retention class, and verification status.
- EvidenceUnit carries immutable ID, producer, provenance, SampleIdentity, observation time, trust, taint, content reference, and normalization version.

### Claims and relations

- Claim is a stable identity; ClaimRevision is the immutable evolving state.
- Each revision lists supporting evidence, counterevidence, confidence, validation state, policy snapshot, predecessor, and creation reason.
- EvidenceRelation represents support or contradiction. InfluenceRelation records non-evidentiary influence such as heuristic or model suggestion and cannot satisfy verification.

### Validation and action

- ValidationExperiment defines hypothesis, procedure, expected discriminators, authorization, environment, and freshness requirements.
- ValidationResult is immutable and records observations without overwriting the experiment.
- ActionProposal requests a capability; ActionAuthorization grants a bounded, expiring permission; ActionReceipt records immutable execution facts.

### Capsule

- CapsuleManifest references the accepted Claim revisions, validation results, policy snapshot, and artifact digests.
- A sealed CapsuleManifest is immutable; corrections create a new manifest version.

Permanent rules:

1. `Trust != Confidence != Validation`.
2. EvidenceUnit, ActionReceipt, ValidationResult, and sealed CapsuleManifest are append-only.
3. Claim evolves only through ClaimRevision.
4. Binary-derived content defaults to tainted/untrusted.
5. Verified requires explicit validation evidence.
6. Stale evidence cannot support a current accepted Claim.

## Invariants

- Every object has schema version and stable identity.
- References use identifiers/digests, not mutable embedded copies.
- Historical revisions remain addressable.
- Missing provenance cannot be silently repaired from report prose.

## Interfaces

Versioned JSON Schema defines interchange. Domain implementations validate semantics. Repository ports store/query metadata. Artifact ports resolve content by digest. Projection adapters produce reports and UI views without becoming authoritative.

## Failure modes

- In-place Claim mutation erases audit history.
- Evidence lacks sample binding or producer identity.
- A stale or tainted item is presented as verified.
- An implementation-specific Python type becomes the only contract.

## Security implications

Immutable provenance and explicit taint prevent hostile content from acquiring authority through copying. Separate InfluenceRelation prevents model/tool suggestions from masquerading as observations.

## Migration impact

P3 creates schemas and domain types. P4/P5 ingest static evidence through the firewall. P6 adds revisions and counterevidence. P9/P10 add validation and Capsule sealing.

## Acceptance criteria

- All first-wave objects have distinct responsibilities.
- Immutability and revision rules are explicit.
- Interchange ownership belongs to versioned JSON Schema.
- Verification cannot occur without current validation evidence.

## Related ADRs

- [ADR-006 Evidence and Claim Versioning](../adr/ADR-006-evidence-and-claim-versioning.md)
- [ADR-005 Storage Ownership](../adr/ADR-005-storage-ownership.md)
