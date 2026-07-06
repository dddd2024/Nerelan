# Governance Operations Bundle

Governance Operations Bundle is a readiness-only project_governance round. It combines cleanup review, round compaction dry-run, bounded archive indexing, SQLite read-index schema readiness, state-hygiene dashboard feed output, and lifecycle transition guards.

The bundle keeps `project_state/` as the audit fact source. It does not run cleanup apply, archive compaction apply, database creation, Web runtime, runner dispatch, CI dispatch, model API calls, external reverse tools, or sample processing.

Primary gate output:

- `project_state/gates/governance_operations_bundle_result.json`
- `project_state/gates/governance_operations_bundle_snapshot.json`

