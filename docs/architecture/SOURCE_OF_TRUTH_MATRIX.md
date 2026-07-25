# Source-of-Truth Matrix

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This matrix defines the single authoritative source for each class of fact in `reverse-agent`. When two sources disagree, the higher-precedence source wins. No document in this matrix authorizes commands, file changes, closeout, or merge by itself; execution authority lives in `project_state/decision_packet.md` and `project_state/gates/command_plan.json`.

## Ownership map

| Fact class | Authoritative source | Precedence | Notes |
|------------|----------------------|------------|-------|
| Product direction | `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` | 5 | Planning reference only |
| R0/R1 Work Item authority | GitHub Issue (R1 template) | 4 | Primary authority for ordinary R0/R1 work after the transition round |
| Current engineering task | GitHub Issue / Work Item | 4 | An Issue is a Work Item; for R0/R1 it is the primary authority |
| Code and history | Git | 3 | Branches, commits, trees, tags |
| PR / check / merge state | GitHub | 4 | GitHub is authoritative; local mirrors are cached observations |
| Ordinary validation | `pytest`, `git diff --check`, GitHub Actions | n/a | Deterministic checks |
| R2/R3 authorization | Bounded Decision in `project_state/decision_packet.md` | 1 | Fail-closed; no Issue/comment authorizes R2/R3 |
| Transition round execution authority | `project_state/decision_packet.md` | 1 | Authority for transition rounds and R2/R3 only, not ordinary R0/R1 |
| Transition round command authority | `project_state/gates/command_plan.json` | 2 | Generated from the active Decision; authority for transition rounds and R2/R3 only |
| Feature-branch push / Draft PR creation | R1 (no Decision required) | n/a | Classified as R1; see AGENTS.md |
| Runtime logs / artifacts | Local filesystem or GitHub Actions Artifact | n/a | Never tracked source state |
| JSON contract schemas | `reverse_agent/architecture/contracts.py` | n/a | `SCHEMA_VERSION=1`; stable dataclasses |
| Architecture spec | `docs/architecture/architecture-spine-v1.md` | 6 | Architecture Spine v1 reference |
| Legacy boundary | `docs/architecture/legacy-control-plane-boundary.md` | 6 | Compatibility adapter scope |
| Transition kernel | `docs/architecture/control-plane-transition-kernel.md` | 6 | Fail-closed authorization path |
| Legacy `project_state/**` artifacts | Read-only compatibility evidence | 7 | Cannot authorize a transition |

## Rules

1. **GitHub is authoritative for Issue, PR, check, and merge state.** Local observations are timestamped caches; a cache mismatch does not override GitHub.
2. **Runtime logs and per-run artifacts are not tracked source state.** They live in the local filesystem or as GitHub Actions Artifacts. Do not commit per-run Gate evidence as new tracked source.
3. **For ordinary R0/R1 work, the GitHub Issue (R1 template) is the primary authority.** `decision_packet.md` and `command_plan.json` are not ordinary R0/R1 execution authority; they are authority for transition rounds and R2/R3 only.
4. **An Issue or PR comment is planning reference, not command authority.** For transition rounds and R2/R3, only `command_plan.json` authorizes commands.
5. **R2/R3 operations fail closed.** No planning document, audit note, or Issue body can authorize them; only a bounded Decision can.
6. **Feature-branch push and Draft PR creation are R1 operations.** They do not require R2 authorization. Direct `main` push, merge, force push, rebase, squash, tag, and release remain R2 or higher.
7. **When sources disagree, the higher-precedence source wins.** Precedence is numbered above (1 = highest).
8. **Roadmap documents are planning references.** They describe direction; they do not authorize execution.

## Non-authoritative sources

The following are explicitly **not** sources of truth for execution decisions:

- `docs/roadmap/**` (except the active roadmap as product direction)
- Issue comments and audit notes
- Legacy closeout/final-seal/report-synthesis artifacts
- `project_state/current_state.json`, `project_state/state_manifest.json` (read-only state mirrors)
- Local CI observation mirrors
- Any artifact marked `PLANNING_REFERENCE_ONLY` or `HISTORICAL_REFERENCE`
