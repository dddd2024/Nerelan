# ADR-009: Telemetry Is Not Analysis Evidence

## Status

`ACCEPTED`

## Context

Operational traces and logs describe system behavior but lack the sample binding, provenance, trust, taint, and immutability required of analysis evidence.

## Decision

OpenTelemetry traces, metrics, logs, latency, cost, retry, exceptions, node duration, and provider health are operational telemetry and are not EvidenceUnit, Claim support, ValidationResult, or ActionReceipt by default.

Promotion requires an explicit Evidence Adapter recording the source telemetry identifier, promotion rule, producer, sample binding, normalization, trust/taint, and immutable EvidenceUnit identity.

## Alternatives considered

- Treat all tool traces as evidence: rejected because operational success does not prove semantic correctness.
- Ban telemetry reuse entirely: rejected because specific observations can be useful when normalized and provenance-bound.
- Copy traces into reports: rejected because prose does not create evidence semantics.

## Consequences

Some useful signals require an explicit promotion step. Operational observability remains independent of analysis acceptance.

## Security implications

Sample-controlled log content cannot automatically influence Claims or authorization. Promotion creates a controlled taint boundary.

## Migration implications

Existing telemetry remains operational/historical. P5 introduces the evidence firewall and promotion adapter contract.

## Revisit conditions

Promotion rules may expand through versioned policy; default non-evidence status remains.
