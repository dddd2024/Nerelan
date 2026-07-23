# Trust Model

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Define the two non-overlapping trust bounded contexts and the rules for taint, authorization, confidence, and validation.

## Authority

This document is the unique authority for trust boundaries and cross-context trust rules. Data object fields are defined in `data-contracts.md`; execution permissions are defined in `sandbox-and-execution-boundary.md`.

## Scope

### Engineering Control Plane

Owns Work Item, Execution Envelope, Engineering Decision, Command Plan, Repository Mutation, PR/CI Observation, Review, Merge, and Release authorization.

### Binary Analysis Trust Domain

Owns AnalysisRun, SampleIdentity, ArtifactRef, EvidenceUnit, Claim/ClaimRevision, Counterevidence, ValidationExperiment, ActionProposal, ActionAuthorization, ActionReceipt, and Analysis Capsule trust semantics.

## Non-goals

- No claim-scoring algorithm or policy implementation.
- No provider or sandbox execution.
- No inference that engineering success validates binary analysis.

## Context

Engineering evidence answers whether an authorized repository change was performed and reviewed. Binary-analysis evidence answers what was observed about a sample and how strongly a Claim survived validation. These are different questions and must not share acceptance states.

## Decisions

1. `Trust != Confidence != Validation` is permanent.
2. Trust describes provenance and handling policy; confidence is an assessment; validation records an explicit experiment and observed result.
3. Binary-derived content defaults to `tainted/untrusted` regardless of tool success.
4. `verified` requires explicit current validation evidence bound to the same SampleIdentity and Claim revision.
5. Stale evidence cannot support a current accepted Claim.
6. CI PASS, PR approval, Decision acceptance, and tool exit code 0 do not validate a Claim.
7. The only cross-context execution bridge is:

```text
ActionProposal
-> Engineering authorization boundary
-> ActionAuthorization
-> isolated provider execution
-> ActionReceipt
```

## Invariants

- Engineering acceptance is not analysis validation.
- Evidence does not grant repository write access.
- Authorization does not assert output correctness.
- Counterevidence remains visible and linked to the Claim revision it challenges.
- Trust/taint labels are explicit and never inferred from prose.

## Interfaces

- Engineering emits an ActionAuthorization containing exact scope, expiry, capability, and policy identity.
- The provider returns an immutable ActionReceipt and ArtifactRefs.
- An Evidence Adapter may normalize outputs into immutable EvidenceUnits while preserving producer, provenance, sample binding, time, trust, and taint.

## Failure modes

- Treating successful command execution as correct evidence.
- Reusing evidence across sample identities or after expiry.
- Hiding counterevidence during Claim revision.
- Letting analysis data inject commands or paths into engineering execution.

## Security implications

All binary-derived strings, paths, arguments, and model/tool outputs are data, not authority. Authorization inputs are constructed from trusted policy and explicit user/Decision approval, never from sample-controlled content alone.

## Migration impact

Legacy reports remain readable but become projections. P3 introduces versioned trust-domain contracts; P5/P6 add evidence firewall and claim ledger; P7/P8 add authorized providers and isolation.

## Acceptance criteria

- Both bounded contexts and their sole bridge are explicit.
- Trust, confidence, and validation are distinct.
- Taint defaults and verified requirements are unambiguous.
- Engineering outcomes cannot be read as analysis conclusions.

## Related ADRs

- [ADR-003 Separate Trust Bounded Contexts](../adr/ADR-003-separate-trust-bounded-contexts.md)
- [ADR-006 Evidence and Claim Versioning](../adr/ADR-006-evidence-and-claim-versioning.md)
- [ADR-009 Telemetry Is Not Analysis Evidence](../adr/ADR-009-telemetry-is-not-analysis-evidence.md)
