# Job Lifecycle And Decision Preflight

`job-lifecycle` materializes the deterministic READY job artifact for the active decision round and validates the local `project_state/jobs` inventory. The job remains a static contract until a later decision explicitly authorizes dispatch.

For the current round, the generated job path is derived from the round id:

- `project_state/jobs/job_20260706_post_final_sync_job_preflight_big_step_v1.json`
- `project_state/gates/job_lifecycle_validation_result.json`
- `project_state/gates/job_lifecycle_snapshot.json`

`decision-preflight` validates that the approved decision can be checked locally before execution. It requires a current command plan, current post-final evidence sync, the current READY job artifact, active skill profile metadata, and read-only workflow readiness evidence.

Both gates keep the same safety contract: no remote mutation, no agent dispatch, no model calls, no reverse-solving runtime, no sample execution, no branch or pull request operations, and no cleanup/archive apply.
