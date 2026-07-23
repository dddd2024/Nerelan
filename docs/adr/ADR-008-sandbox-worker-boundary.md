# ADR-008: Sandbox Worker Boundary

## Status

`ACCEPTED`

## Context

Unknown binaries and dynamic tooling can compromise the host, exfiltrate credentials, alter the repository, or contaminate other analyses.

## Decision

Classify execution as S0 pure parsing, S1 static tooling without target execution, S2 isolated emulator/debugger/scripted probe, or S3 disposable unknown-sample execution. S2/S3 require explicit action authorization, limits, network policy, output isolation, cleanup, and ActionReceipt; S3 additionally requires human approval and defaults to no network.

S2/S3 workers receive no GitHub token, SSH/cloud credential, host secret, user-home access, repository write access, or other AnalysisRun data.

## Alternatives considered

- Execute locally with process timeout: rejected as insufficient isolation.
- Give a shared worker repository access for convenience: rejected due privilege and persistence.
- Treat all tooling as S1: rejected because debuggers/emulators execute or model target behavior.

## Consequences

Dynamic analysis costs more and may be unavailable until P8. S0/S1 can progress earlier with bounded artifacts.

## Security implications

Disposable isolation, credential absence, default-deny network, and quarantined outputs are mandatory controls against malicious samples and tool compromise.

## Migration implications

Legacy runtime evidence is not grandfathered into trusted status; new dynamic runs require compliant authorization and receipts.

## Revisit conditions

Tier implementations may evolve. Credential and repository-write prohibitions for S2/S3 remain.
