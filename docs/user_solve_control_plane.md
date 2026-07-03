# User Solve Control Plane

The User Solve control plane is an offline, fixture-only composition layer. It
connects the request contract, existing in-memory solve/session contracts,
handoff packet, response envelope, and CLI preview without adding Web/API,
database, queue, scheduler, runner, debugger, subprocess, network, upload, or
real-binary processing capabilities.

## Contracts

`UserSolveRequest` is the inbound boundary. It accepts only `fixture`, `demo`, or
`synthetic` input kinds and rejects real local paths, URLs, internal
`project_state` references in user fields, and persistent-session requests.
Developer references are explicit and appear only in developer serialization.

`UserSolveController` is the composition point. It uses `FastSolveWrapper` to
produce a `UserSolveSessionBundle`, derives a `UserSolveHandoffPacket`, and then
builds a `UserSolveResponseEnvelope`. It does not duplicate pipeline, harness,
job, runner, command-plan, or execution-log responsibilities.

`UserSolveResponseEnvelope` is the outbound boundary. Default user serialization
contains request metadata, status, answer/candidates, confidence, validation and
evidence status, public message, next action, fallback summary, handoff,
warnings, and errors. Developer serialization explicitly adds audit references.

## Fixture Behavior

The `candidate` demo returns `candidate_found` with pending validation and a
`validate_candidate` next action. It is not a solved or verified sample claim.

The `missing-evidence` demo returns `deep_analysis_running` with a non-executing
fallback/deep-analysis next action. It does not convert missing evidence into a
solved result.

Verified states remain governed by the lower-level result and session contracts:
`verified` requires passed validation and usable answer evidence.

## Gate Evidence

`prework-provenance` records startup snapshot provenance and blocks undeclared
dirty source, test, or documentation files from supporting `SUCCESS`.

`user-solve-control-plane` runs the safe fixture responses, verifies user
serialization redaction, records non-invasive capability flags, and scans the
new control-plane source surface for forbidden execution, persistence, network,
dispatch, and real-binary terms.

The CLI preview commands are:

```powershell
python -m reverse_agent.user_solve_cli --demo candidate
python -m reverse_agent.user_solve_cli --demo missing-evidence
```

Both commands emit JSON response envelopes from synthetic in-memory fixtures.
