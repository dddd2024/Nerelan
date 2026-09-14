# Execution prompt

```text
Repository: dddd2024/Nerelan
Work Item / PR: <locator>
Role: executor
Execution surface: <GitHub / trusted worker / CI / explicitly authorized user-local>
Outcome: <requested result and acceptance target>
Optional stale-detection hints: <branch / base / head>

This prompt is a locator, not execution authority. Fresh-read the named Work Item,
current repository AGENTS.md and live branch/base/head before mutation. Use Path A's
approved Issue snapshot for ordinary R0/R1; use Path B's immutable Decision and
generated plan/preflight for transition/R2-R3. Hints never override current truth.
Read only the task-relevant code and conditional references. No fixed drive or
historical project-state stack is required by this prompt.

Implement, inspect and verify the requested result within the existing scope,
permissions, execution capabilities and retry budget. Preserve other owners' work.
Do not request repeat approval for already-authorized safe development checks.
Mandatory final acceptance, exact-head evidence and landing permissions still apply.
Report actual changes, checks/head/surface, results and explicit blockers; do not
present a first draft, unrun check or self-review as completed acceptance.
```

The applicable authority, not this template, determines command, report and publication permissions.
