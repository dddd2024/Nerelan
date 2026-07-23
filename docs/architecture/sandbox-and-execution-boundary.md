# Sandbox and Execution Boundary

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Define S0-S3 execution tiers and the credential, filesystem, network, lifecycle, and authorization boundary for isolated workers.

## Authority

This document is the unique authority for analysis execution tiers and worker permissions.

## Scope

| Tier | Meaning | Target execution | Required boundary |
|---|---|---|---|
| S0 | hashing, headers, strings, pure parsing | none | read-only input, no network, ordinary process isolation |
| S1 | static tooling | target is never launched as a host executable | isolated run directory and bounded output |
| S2 | emulator, debugger, scripted probe | controlled execution | explicit proposal/authorization, isolation, limits, policy, receipt |
| S3 | unknown sample execution | real execution | disposable worker, human approval, default-deny network, destruction after run |

## Non-goals

- No sandbox executor, image, VM, provider, debugger, emulator, or dynamic probe implementation in P0.
- No authorization to execute an unknown binary.

## Context

Static parsing and hostile execution have materially different risks. A single generic runner cannot safely inherit repository credentials or user-home access.

## Decisions

S2/S3 workers never receive:

```text
GitHub token, SSH key, cloud credential, host secrets,
user-home access, repository write access,
other AnalysisRun data, long-lived network credentials
```

S2/S3 require ActionProposal, risk classification, Decision/high-risk authorization, Command Plan, human approval where applicable, timeout, CPU/memory limits, network policy, output isolation, cleanup, and immutable ActionReceipt.

S3 is disposable and defaults to no network. Any exception is explicit, destination-bounded, time-bounded, observable, and separately approved.

## Invariants

- Sample-controlled values are data, never shell authority.
- Each execution has a fresh run directory and scoped ArtifactRefs.
- The worker cannot write to the source repository.
- Outputs cross the boundary only through a normalized artifact/evidence adapter.
- Cleanup failure is recorded and blocks worker reuse.

## Interfaces

- ActionProposal specifies capability and intended inputs.
- ActionAuthorization binds exact policy, subject, environment tier, expiry, and limits.
- SandboxProvider executes only the authorized envelope.
- ActionReceipt records actual image/environment, command identity, limits, timing, exit, cleanup, and output ArtifactRefs.

## Failure modes

- Tier downgrade treats execution as parsing.
- Worker inherits host credentials or writable mounts.
- Network is enabled implicitly.
- Timeout/cleanup fails but the environment is reused.
- Raw output is interpreted as trusted Evidence without normalization and taint.

## Security implications

S2/S3 are security boundaries, not convenience wrappers. Isolation, credential absence, output quarantine, and disposable lifecycle are mandatory defenses against malicious samples and toolchain compromise.

## Migration impact

P4 supports S0/S1 static evidence. P7 defines provider/action provenance. P8 implements the sandbox executor. P9 performs controlled validation. Legacy local runtime probes cannot be promoted into the new path without compliant receipts.

## Acceptance criteria

- S0-S3 are distinct and unambiguous.
- Credential, filesystem, network, and cleanup rules are explicit.
- S2/S3 require authorization and receipts.
- P0 performs no actual provider or binary execution.

## Related ADRs

- [ADR-008 Sandbox Worker Boundary](../adr/ADR-008-sandbox-worker-boundary.md)
- [ADR-003 Separate Trust Bounded Contexts](../adr/ADR-003-separate-trust-bounded-contexts.md)
