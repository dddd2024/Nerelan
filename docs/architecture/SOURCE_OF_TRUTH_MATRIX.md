# Source-of-Truth Matrix

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This matrix defines the authoritative source for each class of fact in `reverse-agent`. The project defines two authority paths (see below). No document in this matrix authorizes commands, file changes, closeout, or merge by itself.

## Two authority paths

Authority is split across two paths. No source is globally higher when it is not applicable to the selected path.

### Path A — ordinary R0/R1 authority

```text
approved Work Item Issue body (R1 template)
  + Issue allowed_paths / forbidden_operations / acceptance_criteria
  + deterministic checks (pytest, git diff --check, GitHub Actions)
```

The Work Item Issue body is the primary authority for ordinary R0/R1. Issue comments and PR comments are never authority.

### Path B — transition / R2-R3 authority

```text
bounded Decision in project_state/decision_packet.md
  + generated command_plan.json
  + transition-preflight PRE_EXECUTION_AUTHORIZED
```

R2/R3 operations fail closed. No Issue body, Issue comment, PR comment, or roadmap document can authorize R2/R3 work.

## Ownership map

| Fact class | Authoritative source | Applicable path | Notes |
|------------|----------------------|-----------------|-------|
| Product direction | `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` | n/a (planning) | Planning reference only |
| R0/R1 Work Item authority | GitHub Issue body (R1 template) | Path A | Primary authority for ordinary R0/R1 |
| R0/R1 Issue comments / PR comments | none | neither | Never authority |
| Current engineering task | GitHub Issue body / Work Item | Path A (R0/R1) / Path B (R2/R3) | An Issue body is a Work Item for R0/R1; R2/R3 requires a bounded Decision |
| Code and history | Git | both | Branches, commits, trees, tags |
| PR / check / merge state | GitHub | both | GitHub is authoritative; local mirrors are cached observations |
| Ordinary validation | `pytest`, `git diff --check`, GitHub Actions | both | Deterministic checks |
| Transition round execution authority | `project_state/decision_packet.md` | Path B only | Authority for transition rounds and R2/R3 only, not ordinary R0/R1 |
| Transition round command authority | `project_state/gates/command_plan.json` | Path B only | Generated from the active Decision; authority for transition rounds and R2/R3 only |
| Feature-branch push / Draft PR creation | R1 narrow publication (no Decision required) | Path A | Classified as R1; see AGENTS.md |
| Runtime logs / artifacts | Local filesystem or GitHub Actions Artifact | n/a | Never tracked source state (see one-time exception below) |
| JSON contract schemas | `reverse_agent/architecture/contracts.py` | n/a | `SCHEMA_VERSION=1`; stable dataclasses |
| Architecture spec | `docs/architecture/architecture-spine-v1.md` | n/a | Architecture Spine v1 reference |
| Legacy boundary | `docs/architecture/legacy-control-plane-boundary.md` | n/a | Compatibility adapter scope |
| Transition kernel | `docs/architecture/control-plane-transition-kernel.md` | n/a | Fail-closed authorization path |
| Legacy `project_state/**` artifacts | Read-only compatibility evidence | n/a | Cannot authorize a transition |

## One-time tracked transition-evidence exception

Runtime logs and per-run artifacts are normally never tracked source state. There is exactly **one one-time exception**: the compiler-required current-round transition-evidence files tracked under `project_state/gates/**` for the active transition Decision:

```text
project_state/decision_packet.md
project_state/gates/command_plan.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
project_state/gates/bootstrap_state.json
project_state/gates/startup_snapshot.json
```

These files are a one-time compatibility exception for the current transition round. They are **not** the normal R0/R1 model. After the transition round is accepted, ordinary R0/R1 work does not track per-run gate evidence. Creation of any new tracked per-run artifact family is prohibited.

## Rules

1. **GitHub is authoritative for Issue, PR, check, and merge state.** Local observations are timestamped caches; a cache mismatch does not override GitHub.
2. **Runtime logs and per-run artifacts are not tracked source state**, except the one-time transition-evidence exception listed above. Do not commit per-run Gate evidence as new tracked source.
3. **For ordinary R0/R1 work (Path A), the GitHub Issue body (R1 template) is the primary authority.** `decision_packet.md` and `command_plan.json` are not ordinary R0/R1 execution authority; they are authority for transition rounds and R2/R3 only (Path B).
4. **An Issue body is the Work Item authority for R0/R1 (Path A). Issue comments and PR comments are never authority under either path.** For transition rounds and R2/R3 (Path B), only `command_plan.json` authorizes commands.
5. **R2/R3 operations fail closed.** No planning document, audit note, Issue body, or Issue comment can authorize them; only a bounded Decision can.
6. **Feature-branch push and Draft PR creation are R1 narrow publication operations (Path A).** They do not require R2 authorization. Direct `main` push, merge, force push, rebase, squash, tag, release, and mark-ready remain R2 or higher.
7. **No new tracked per-run artifact family may be created.** The one-time transition-evidence exception is exhaustive.
8. **Roadmap documents are planning references.** They describe direction; they do not authorize execution.

## Non-authoritative sources

The following are explicitly **not** sources of truth for execution decisions:

- `docs/roadmap/**` (except the active roadmap as product direction)
- Issue comments and PR comments (never authority under either path)
- Legacy closeout/final-seal/report-synthesis artifacts
- `project_state/current_state.json`, `project_state/state_manifest.json` (read-only state mirrors)
- Local CI observation mirrors
- Any artifact marked `PLANNING_REFERENCE_ONLY` or `HISTORICAL_REFERENCE`
- Any new tracked per-run artifact family beyond the one-time transition-evidence exception
