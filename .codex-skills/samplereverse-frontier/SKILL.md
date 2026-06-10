---
name: samplereverse-frontier
description: Use with reverse-agent-iteration for samplereverse.exe work as a sample profile guardrail. This active skill preserves stable sample constraints while requiring all dynamic candidates, run names, bottlenecks, baselines, and artifact paths to come from project_state.
version: 2
status: active
scope: sample_profile
owner: project_state
last_reviewed: "2026-05-24"
facts_policy:
  dynamic_facts_allowed: false
  source_of_truth:
    - project_state/current_state.json
    - project_state/artifact_index.json
    - project_state/negative_results.json
    - project_state/decision_packet.md
forbidden_defaults:
  - store_candidate_hex
  - store_run_name
  - store_artifact_path
  - run_runtime_probe_without_decision
metadata:
  short-description: Samplereverse project_state-backed profile
---

# Samplereverse Profile Guardrails

Use this skill only after the generic `reverse-agent-iteration` workflow has loaded the current project_state packet and classified the round. This skill is a stable sample profile, not a dynamic handoff memo.

## Source Of Truth

Read current sample facts from:

1. `project_state/current_state.json`
2. `project_state/artifact_index.json`
3. `project_state/negative_results.json`
4. `project_state/decision_packet.md`

Do not treat candidate hex strings, run names, historical baselines, or artifact paths from this skill as current evidence. Current bottleneck, candidate quality, runtime metrics, and artifact freshness must come from `project_state`.

## Stable Constraints

- `samplereverse` work uses the profile and CompareAwareSearchStrategy path unless a decision packet gives a fresh evidence-backed override.
- Check `artifact_index.latest_artifacts_v2` before reading any runtime or compare-aware artifact.
- Treat `freshness=stale` as historical evidence only; do not promote stale artifacts to current facts.
- Respect `negative_results.json` before repeating a direction.
- Do not return to the old `sample_solver` blind-search path by default.
- Do not widen beam, topN, budget, timeout, or frontier iteration by default.
- Do not use `compare_semantics_agree=false` candidates as the primary frontier.

## Runtime Probe Guardrails

- Do not run the Base64/RC4 breakpoint probe by default.
- Do not treat Base64/RC4 material producer hypotheses as confirmed without new instruction-level evidence.
- Do not reuse old `[ebp-0x1170]` as a real LHS source unless there is new runtime-backed provenance.
- Prefer bounded compare/runtime evidence captured through current artifact paths listed in `artifact_index`.

## Engineering Rounds

When the decision packet classifies the round as an engineering branch, do not advance sample solving, candidate search, runtime probing, or strategy tuning. Sample facts may explain why a skill or handoff rule is stale, but the implementation should stay in the authorized engineering files.

## Reverse-Solving Rounds

When a future decision packet authorizes reverse-solving work, use current project_state to identify the active mainline, current bottleneck, candidate set, run name, and acceptance criteria. If project_state and a historical note disagree, prefer project_state and report the conflict.
