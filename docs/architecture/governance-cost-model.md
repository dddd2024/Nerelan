# Governance Cost Model

## Status

`ACCEPTED` by P0 Architecture Constitution.

## Purpose

Bound governance effort to concrete risk so ordinary work does not inherit high-risk binary-execution ceremony.

## Authority

This document is the unique authority for R0-R3 governance ceilings and Gate admission criteria.

## Scope

Applies to engineering planning, repository mutation, sensitive publication or migration, and hostile-binary execution.

## Non-goals

- No implementation of Execution Envelope or new Gates in P0.
- No reduction of mandatory isolation for high-risk execution.

## Context

Uniform full-profile governance creates duplicate facts and excessive mutable artifacts. Risk-proportional governance keeps controls tied to a specific prevented failure.

## Decisions

| Tier | Typical work | Required controls | Explicit ceiling |
|---|---|---|---|
| R0 | planning, discussion, read-only inspection | Work Item or discussion record | no Decision, Command Plan, seal, or closeout chain |
| R1 | bounded ordinary engineering | Work Item, lightweight Execution Envelope, PR, CI | no full Decision or multi-artifact closeout once Envelope exists |
| R2 | merge, workflow/dependency change, migration, network publication, permissions | compact Decision with scope, risk, operations, checks, expiry, approval | only controls tied to the sensitive operation |
| R3 | unknown binary/security execution | Decision, Command Plan, human approval, sandbox, action provenance, execution evidence, validation, Capsule when applicable | no execution outside the approved action and isolation boundary |

Until the lightweight Execution Envelope exists, a simplified Decision may temporarily authorize R1 work, as in P0.

Every Gate must state:

1. the specific failure it prevents;
2. the single authority it reads;
3. the blocking decision it emits;
4. whether it creates duplicate truth;
5. its retirement condition.

## Invariants

- Risk classification fails closed for unknown or conflicting operations.
- Higher risk may add controls; lower risk must not silently inherit unrelated mutable artifacts.
- A Roadmap or Work Item never becomes command authority by itself.
- Gate success does not promote telemetry or tool output to analysis evidence.

## Interfaces

- Work Item supplies task identity.
- Risk classifier selects R0-R3 deterministically.
- Execution Envelope or Decision supplies allowed/forbidden operations.
- Command Plan enumerates exact high-risk commands where required.

## Failure modes

- A Gate cannot name the threat it prevents.
- A lower tier bypasses a capability that is actually R2/R3.
- A higher tier duplicates GitHub or workflow truth into mutable mirrors.
- An expired authorization remains executable.

## Security implications

Cost ceilings do not weaken R3. They concentrate strong controls on secrets, destructive actions, network publication, privileged changes, and hostile-binary execution while reducing pressure to bypass a uniformly expensive process.

## Migration impact

P2 stops expanding legacy closeout chains. A later engineering phase introduces the lightweight Execution Envelope and retires full Decision usage for ordinary R1 work.

## Acceptance criteria

- Each tier has distinct required controls and a ceiling.
- R2/R3 triggers are explicit.
- Every future Gate must satisfy the five-question admission test.

## Related ADRs

- [ADR-004 Unique Source of Truth](../adr/ADR-004-unique-source-of-truth.md)
- [ADR-010 Legacy Control Plane Exit](../adr/ADR-010-legacy-control-plane-exit.md)
