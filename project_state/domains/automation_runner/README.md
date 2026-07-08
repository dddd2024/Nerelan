# Domain: automation_runner

> **Skeleton — not execution authority.** This README declares which kinds of
> state this domain will own. Only `project_state/decision_packet.md`
> authorizes execution in any round.

## Purpose

Automation runner dispatch and lifecycle. This domain will own runner
contracts, job lifecycle artifacts, and orchestration state.

## Owned State Kinds (Future)

- Runner contracts
- Job lifecycle artifacts
- Orchestration results
- Agent runner handoff bundles

## Phase A Status

Phase A does not create any state in this domain. This skeleton exists so
future rounds can place automation runner state here without ambiguity.

## Mainline

`project_governance`

## Scope

`global`
