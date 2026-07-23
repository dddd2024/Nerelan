# ADR-001: Modular Monolith

## Status

`ACCEPTED`

## Context

The project is local-first and single-developer. Its primary need is enforceable module and trust boundaries, not independent scaling or deployment.

## Decision

Use one Python modular monolith with explicit engineering, analysis domain/application/ports/adapters, workflow, infrastructure, and interface modules. Enforce inward dependency direction and keep domain code free of framework, database-driver, reverse-tool, telemetry, GitHub, FastAPI, and Web dependencies.

## Alternatives considered

- Microservices: rejected as premature operational and consistency cost.
- Preserve the current undifferentiated layout: rejected because ownership and dependency rules remain implicit.
- Plugin-first distributed architecture: deferred until measured extension needs exist.

## Consequences

Atomic changes and local operation remain simple. Architectural tests will be needed to prevent boundary erosion. Physical service extraction remains possible through ports.

## Security implications

Credentials, hostile artifacts, and provider execution stay behind adapters and isolated worker boundaries rather than entering domain code.

## Migration implications

The target layout is introduced incrementally after P1/P2; P0 moves no source files.

## Revisit conditions

Revisit only when measured isolation, scaling, independent deployment, or regulatory requirements cannot be met by process/worker boundaries within the monolith.
