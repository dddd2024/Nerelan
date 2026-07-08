# Domain: reverse_solving

> **Skeleton — not execution authority.** This README declares which kinds of
> state this domain owns. Only `project_state/decision_packet.md` authorizes
> execution in any round. Moving live state into this directory is a separate
> future decision.

## Purpose

Reverse-solving sample state and artifact traces. This domain owns the
sample-scoped reverse-engineering state currently held in
`project_state/current_state.json`, `project_state/task_packet.json`, and
`project_state/artifact_index.json`.

## Owned State Kinds

- Sample-scoped `current_state` payloads
- Sample-scoped `task_packet` entries
- Reverse-solving artifact traces (compare probes, handoff audits, etc.)
- Reverse-solving `negative_results` entries

## Phase A Status

Phase A adds scope/domain metadata to existing top-level state files. No
files are moved into this directory during Phase A. Phase C will copy
reverse-solving `current_state` content here.

## Mainline

`reverse_solving`

## Scope

`sample`
