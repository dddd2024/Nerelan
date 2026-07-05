# State Hygiene Retention Policy

`project_state/retention_policy.json` defines retention classes for current audit facts, accepted round evidence, generated governance indexes, current gate artifacts, historical nonblocking artifacts, historical sample references, missing historical sample references, transient closeout logs, transient PID files, documentation, configuration, unknown files, and future disposable candidates.

Every class records retain, archive, and delete policy. Every class also records that deletion is not allowed in the current round, a future cleanup-apply decision is required, and a tombstone is required if a future approved round deletes a file.

The policy is intentionally conservative. It protects current decision, report, pytest, command-plan, execution-log, final-check, closeout, state manifest, context packet, workstream registry, and accepted-round minimum evidence.

The retention policy is not cleanup-apply. It is a design artifact used by gates and reports to make future cleanup work reviewable.
