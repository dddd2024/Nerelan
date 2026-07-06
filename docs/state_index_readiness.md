# State Index Readiness

State Index Readiness defines the schema and plan for a future SQLite read/query index over decisions, rounds, artifacts, executions, audits, workstreams, and backlog notices.

The readiness artifacts are schema-only. They do not create `project_state/index.sqlite`, `.db` files, migrations, or replacement fact storage. `project_state/` remains the audit fact source.

Primary outputs:

- `project_state/gates/state_index_readiness_schema.json`
- `project_state/gates/state_index_readiness_plan.json`
- `project_state/gates/state_index_readiness_result.json`

