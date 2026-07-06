# Cleanup Apply Review Bundle

Cleanup Apply Review Bundle is a human review package layered on the existing cleanup-apply safety artifacts. It prepares risk, approval, evidence-lock, deletion-manifest dry-run, tombstone dry-run, rollback, and audit handoff evidence.

All cleanup review outputs are advisory. No row may set `delete_allowed_now=true` or `archive_allowed_now=true`. A future real cleanup apply still requires a separate approved decision, command-plan authority, deletion manifest, tombstone plan, rollback handoff, audit approval, and final-check acceptance.

Primary outputs:

- `project_state/gates/cleanup_apply_review_bundle.json`
- `project_state/gates/cleanup_apply_review_result.json`
- `project_state/gates/cleanup_candidate_risk_matrix.json`
- `project_state/gates/cleanup_apply_approval_checklist.json`
- `project_state/gates/evidence_lock_manifest.json`

