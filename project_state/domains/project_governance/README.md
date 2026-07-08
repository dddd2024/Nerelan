# Domain: project_governance

> **Skeleton — not execution authority.** This README declares which kinds of
> state this domain owns. Only `project_state/decision_packet.md` authorizes
> execution in any round.

## Purpose

Governance gates, decision packets, reports, and closeout artifacts. This
domain owns the project-governance state used by the gate chain:
`decision_packet.md`, `codex_execution_report.md`, `execution_report.md`,
`pytest_result.txt`, and all `gates/*.json` artifacts.

## Owned State Kinds

- Decision packets and contracts
- Execution reports and codex execution reports
- Gate artifacts (`command_plan.json`, `preflight_result.json`,
  `final_gate_result.json`, `execution_log.json`, etc.)
- Round manifests and round archive artifacts
- State manifest and context packet governance indexes
- Workstream registry

## Phase A Status

Phase A adds `scoped_metadata` to `state_manifest.json` and `scope_metadata`
to `artifact_index.json`. Governance state files remain at the top level
of `project_state/` during Phase A.

## Mainline

`project_governance`

## Scope

`global`
