# ADR-006: Evidence and Claim Versioning

## Status

`ACCEPTED`

## Context

Analysis conclusions evolve, while observations and execution receipts must remain auditable. In-place mutation destroys the basis for later review and falsification.

## Decision

EvidenceUnit, ActionReceipt, ValidationResult, and sealed CapsuleManifest are immutable. Claim has stable identity and evolves only through immutable ClaimRevision objects linked to predecessors. Each revision names support, counterevidence, confidence, validation, policy snapshot, and reason.

`Trust != Confidence != Validation`. Binary-derived content defaults to tainted/untrusted. Verified requires current explicit validation evidence; stale evidence cannot support a current accepted Claim. Versioned JSON Schema is the interchange contract.

## Alternatives considered

- Mutable Claim rows with audit timestamps: rejected because overwrite semantics remain ambiguous.
- Append-only reports without structured revisions: rejected because relationships cannot be validated.
- Python classes as the sole contract: rejected because interchange would be implementation-bound.

## Consequences

Corrections create new objects and storage grows monotonically. Consumers must select current revisions explicitly and preserve history.

## Security implications

Immutable provenance exposes tampering and prevents retroactive promotion of tainted/stale evidence.

## Migration implications

P3 defines schemas/repository semantics; P5/P6 add evidence and Claim ledgers; P9/P10 add validation and Capsule versions.

## Revisit conditions

Retention and compaction may be revisited, but semantic immutability and revision history may not.
