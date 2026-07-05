# User Solve Task Lifecycle

Demo tasks live only under `project_state/solve_tasks/demo_*.json`.

Allowed statuses are `DRAFT`, `READY`, `MANUAL_DISPATCHED`, `MANUAL_RESULT_IMPORTED`, `FINAL_CHECKED`, `AUDITED`, `ACCEPTED`, `REWORK_REQUIRED`, and `BLOCKED`.

The lifecycle is intentionally manual. A handoff can be exported, and a structured result can be previewed or imported, but no runner is dispatched and no concrete sample is treated as solved.
