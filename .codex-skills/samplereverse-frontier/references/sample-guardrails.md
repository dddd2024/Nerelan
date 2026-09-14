# Stable sample guardrails

Applies only to an explicitly authorized samplereverse task. This reference supplies no execution permission; binary/runtime work requires the applicable bounded Path-B authority.

Read needed sample facts from `project_state/current_state.json`, `artifact_index.json` and `negative_results.json`, subject to the active Decision. Resolve the current task and authority before using those facts. Never promote candidate strings, run names, historical baselines or artifact locations from a skill or old note into current evidence.

Use the samplereverse profile and `CompareAwareSearchStrategy` path unless a fresh evidence-backed Decision authorizes an override. Check `artifact_index.latest_artifacts_v2` before reading runtime/compare artifacts; `freshness=stale` is historical only. Check applicable negative results before repeating a direction.

Do not default to the old `sample_solver` blind-search path. Do not widen beam, topN, budget, timeout or frontier iterations by default. Do not use `compare_semantics_agree=false` candidates as the primary frontier.

Do not run the Base64/RC4 breakpoint probe by default. Do not treat Base64/RC4 producer hypotheses as confirmed without new instruction-level evidence. Do not reuse old `[ebp-0x1170]` as a real LHS source without new runtime-backed provenance. Prefer bounded compare/runtime evidence referenced by the current artifact index.

An engineering round must not advance sample solving, candidate search, probes or strategy tuning. A separately authorized solving round resolves the active mainline, bottleneck, candidate set, run and acceptance criteria from current project state. If it conflicts with historical notes, prefer fresh state evidence and report the conflict; neither state nor this skill can override the Decision.
