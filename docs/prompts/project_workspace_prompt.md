# Planning and audit prompt

```text
Repository: dddd2024/Nerelan
Work Item / PR / goal: <locator>
Role: <planner / auditor>
Execution surface: <actual available surface>
Outcome: <decision or audit result requested>
Optional stale-detection hints: <branch / base / head>

This prompt is a non-authoritative locator. Fresh-read current repository truth,
AGENTS.md and the named work before using a summary. Distinguish Path A's approved
Issue snapshot from Path B's immutable Decision/plan; planning is not approval.
Read only the relevant implementation, requirements, tests and conditional references.
Check existing ownership and reuse options before creating another task or design.

Compare claims with exact-head evidence, identify missing acceptance or capabilities,
and distinguish implemented, verified, proposed and blocked states. State the smallest
bounded next action and its success/stop criteria. Do not copy a complete Issue,
Decision or historical state stack into the output, expand scope from stale plans,
claim self-review is independent, or modify the repository without applicable authority.
```

Use [legacy project-state details](legacy-project-state-reference.md) only when the active task explicitly selects that contract, not as the universal product model.
