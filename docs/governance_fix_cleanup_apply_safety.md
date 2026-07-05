# Governance Fix Cleanup Apply Safety

This round is a project_governance round with two lanes under one mainline.

The fix lane records historical sample artifact gaps as visible backlog notices
when the active governance round makes no sample-evidence claim.  The backlog is
not hidden and does not downgrade current non-sample governance evidence.

The cleanup-apply safety lane is dry-run-only.  It generates precondition,
manifest-validation, tombstone-validation, rollback-handoff, and audit-handoff
artifacts, but it does not perform cleanup apply.  It does not delete, move,
archive, compact, or tombstone any real file, and it does not write a real
deletion manifest.

Future real cleanup apply requires a separate approved decision, command-plan
authorization, accepted deletion manifest and tombstone plan, rollback handoff,
audit handoff, and final-check evidence that explicitly permits that future
round's real cleanup capability.
