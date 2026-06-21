# Prompt Documents

This directory contains stable, version-controlled prompt templates for the reverse-agent project.

These files define long-lived workflow rules. They are not dynamic project state. Do not store candidates, run names, artifact paths, freshness, runtime metrics, or single-sample conclusions in these files.

## Files

- `project_workspace_prompt.md` — stable project-level rules for GPT acting as decision and audit planner.
- `codex_execution_prompt.md` — stable local Codex execution rules.

## Policy-Lint Integration

These prompt documents are scanned by `policy-lint` by default. Drift in these files (obsolete profile names, authority violations, unsupported report statuses, dynamic facts) will be detected and reported.

Do not weaken policy-lint to make prompt docs pass. If the prompt docs contain drift, fix the prompt wording rather than hiding findings.
