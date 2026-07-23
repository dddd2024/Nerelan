# ADR-007: LangGraph Workflow Ownership

## Status

`ACCEPTED`

## Context

Competing workflow runtimes and ad-hoc AgentRunner loops duplicate state, retry, approval, and recovery semantics.

## Decision

LangGraph is the only future workflow runtime. Development and Binary Analysis use separate graphs, State Schemas, and checkpoint namespaces. Production workflows require persistent checkpoints, interrupt/resume, idempotent nodes, bounded retry, human approval, provider dispatch through ports, and explicit terminal states.

PR #9 remains a shadow/non-dispatching transition baseline. Durable Binary Analysis workflow work is deferred to P11.

## Alternatives considered

- Keep a second primary AgentRunner: rejected due split orchestration authority.
- Use GitHub or project_state as checkpoint store: rejected because remote/source facts have different ownership.
- Deploy durable workflows before domain contracts: rejected because state would encode unstable semantics.

## Consequences

Legacy runners must become adapters or retire. Workflow state references domain IDs and never becomes Claim authority.

## Security implications

Provider execution remains behind authorization ports; replay and retry must not duplicate high-risk actions without idempotent receipts.

## Migration implications

P1 freezes PR #9; P11 implements durable binary-analysis workflow after contracts, sandbox, validation, and Capsule foundations.

## Revisit conditions

LangGraph may be replaced only by a separate architecture Decision proving feature parity, migration safety, and a single runtime authority.
