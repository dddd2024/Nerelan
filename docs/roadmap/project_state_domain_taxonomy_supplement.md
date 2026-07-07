# Project State Domain Taxonomy Supplement

> **Roadmap material — not execution authority.** This supplement defines the
> intended phase breakdown for classifying project state by domain. Only
> `project_state/decision_packet.md` authorizes execution in any round. This
> document records direction so contributors can see how Phase A connects to
> future phases without implying those phases are complete or authorized.

## Background

`project_state/current_state.json` still contains reverse-solving sample state
for `samplereverse`, which is not suitable as a permanent global project
summary. `project_state/negative_results.json` mixes reverse-solving failure
directions with global policy restrictions. `artifact_index.json` and the
state manifest lack scope/freshness metadata, so consumers cannot safely tell
which entries belong to reverse-solving, governance, or another domain.

This supplement defines a staged taxonomy migration that adds domain metadata
before moving any files or creating domain directories.

## Authority

- Execution authority: `project_state/decision_packet.md`.
- This supplement is **roadmap direction only** and is not execution authority.
- The workstream registry entry `project_state_domain_taxonomy` in
  `project_state/roadmap/workstreams.json` records lifecycle status; it does
  not authorize commands.

## Phases

### Phase A — Metadata Foundation (active)

Add backward-compatible `scope`, `domain`, `mainline`, `role`, and
`freshness` metadata to:

- `state_manifest.json` (a new `scoped_metadata` section classifying current
  state files).
- `artifact_index.json` (a new `scope_metadata` section and `scope_coverage`
  summary for each artifact kind).
- `negative_results.json` (per-record `scope`/`domain`/`sample_id`/
  `replacement_direction` added best-effort; list-style JSON preserved).

Policies for Phase A:

- Missing scope metadata on legacy entries is a **non-blocking warning**.
- No state files are moved, deleted, or migrated.
- No `project_state/domains/*` directory is created.
- `negative_results.json` is not split into domain-specific files.
- `current_state.json` and `task_packet.json` are not modified.
- final-check/report-summary surface scoped metadata coverage as warnings,
  not as hard failures, unless a current-round record violates the decision.

### Phase B — Domain Skeleton (future)

Create `project_state/domains/*` as an empty skeleton with domain manifests,
without moving any files. Each domain declares which kinds of state it owns.
This is a separate future decision and is not authorized by Phase A.

### Phase C — Reverse-Solving current_state Copy (future)

Copy the reverse-solving `current_state.json` content into the reverse-solving
domain scope, leaving the top-level file in place. This is a separate future
decision.

### Phase D — negative_results Split (future)

Split `negative_results.json` into domain-specific files under
`project_state/domains/<domain>/negative_results.json`, preserving the legacy
file as a compatibility shim during migration. This is a separate future
decision.

### Phase E — Top-Level current_state Summary (future)

Turn the top-level `current_state.json` into a global project summary that
references domain-scoped state rather than embedding reverse-solving sample
state. This is a separate future decision.

### Phase F — Final-Check Hardening (future)

Harden final-check to require scope metadata on new current-round records
(legacy entries remain non-blocking). This is the last phase and is a separate
future decision.

## Non-Goals for Phase A

- Phase A does not complete the state taxonomy migration.
- Phase A does not create `project_state/domains/*`.
- Phase A does not move, delete, or migrate any state file.
- Phase A does not split `negative_results.json`.
- Phase A does not turn `current_state.json` into a global summary.
- Phase A does not harden final-check to hard-fail on missing scope metadata.

## Relationship to the Normal-Pace Plan

`docs/roadmap/reverse_agent_normal_pace_plan.md` sets the overall phase order.
This supplement details the state-taxonomy phases (A–F) that sit inside step 3
of the normal-pace plan.
