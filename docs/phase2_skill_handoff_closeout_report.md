# Phase 2 Skill Handoff Closeout Report

Date: 2026-05-24

Decision: `decision_20260524_phase2_skill_handoff_closeout`

## Summary

Phase 2 is closed as an engineering-branch hygiene effort. It did not advance `samplereverse` solving, did not run runtime harnesses or probes, and did not change reverse-solving strategy code.

The final shape is intentionally compact:

```text
skill layer: stable workflow policy and guardrails
project_state layer: dynamic facts and current state
decision_packet layer: per-round delta authority
lint/audit/sync layer: machine checks and controlled local publication
```

## Completed Mechanisms

| area | completed behavior |
| --- | --- |
| active skills | `reverse-agent-iteration` is project_state-first and `samplereverse-frontier` is a stable profile guardrail |
| dynamic facts | candidates, run names, artifact paths, freshness, bottlenecks, and runtime metrics remain in `project_state` |
| forbidden defaults | active skills do not default to `PROJECT_PROGRESS_LOG.txt`, full `solve_reports/`, newest harness runs, or runtime probes |
| registry/schema | `.codex-skills/registry.json` lists the two real active skills; `.codex-skills/schema.md` defines frontmatter, status, scope, facts policy, audit, decision profiles, and sync behavior |
| audit | `tools/audit_codex_skills.py` uses Python standard library only, emits JSON, and fails on hard errors |
| decision lint | `lint-decision` validates `decision_meta.skill_profiles` against active registry entries while preserving legacy compatibility |
| sync | `tools/sync_codex_skills.ps1` supports `-List`, `-Check`, `-DryRun`, and `-IncludeDeprecated`; default sync is active-only and preserves unknown local skills |

## Phase Table

| phase | status | verification |
| --- | --- | --- |
| Phase 2A inventory/stale audit | complete | documented in `docs/phase2_compact_handoff_skill_hygiene_plan.md` |
| Phase 2B skill refactor | complete | active skills no longer store dynamic sample facts |
| Phase 2C schema/registry | complete | registry contains `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` |
| Phase 2D audit tool | complete | `python tools/audit_codex_skills.py` passes |
| Phase 2E decision profiles | complete | current decisions lint with `reverse-agent-iteration@v2` |
| Phase 2F sync hygiene | complete | PowerShell `-List`, `-Check`, and `-DryRun` checks pass |

## Known Limitations

- `round_manifest.source_git_commit` can still describe the pre-execution commit for a round.
- Engineering-branch `round_manifest.source_harness_run` may inherit the current sample run and is noisy as engineering provenance.
- Archived skills remain conservatively excluded from sync; there is no `-IncludeArchived`.
- Mainline policy remains warning-oriented and compatibility-safe rather than newly hard-failing legacy decisions.

## Next Direction

Default next step is to return to the reverse-solving mainline from the current `project_state` handoff. Specifically, the next reverse-solving decision should start from `project_state/current_state.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, and the active `decision_packet.md`, while preserving the Phase 2 rule that dynamic sample facts do not move back into skills.

Continue engineering work only if a future decision packet explicitly opens another engineering branch.
