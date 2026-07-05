# State Governance Bundle

State Governance Bundle Big Step v1 is a non-destructive governance round. It creates file-backed planning, index, and schema artifacts under `project_state/` so future cleanup work can be reviewed before any file mutation is allowed.

The bundle produces:

- `project_state/retention_policy.json`
- `project_state/gates/cleanup_plan.json`
- `project_state/gates/archive_index.json`
- `project_state/gates/deletion_manifest_schema.json`
- `project_state/gates/tombstone_schema.json`
- `project_state/state_lifecycle_registry.json`
- refreshed manifest, context packet, and workstream registry artifacts
- `project_state/gates/state_governance_bundle_result.json`

These artifacts are evidence and planning records only. They do not authorize cleanup-apply, deletion, moves, archive compaction, tombstone writes, runner dispatch, model calls, external reverse tools, CI mutation, database work, Web runtime work, or concrete sample processing.

Future cleanup-apply needs a separate approved decision packet, an accepted deletion manifest design, accepted tombstone design, per-file hashes, audit approval for every candidate, and final gate checks that prove the operation is safe.
