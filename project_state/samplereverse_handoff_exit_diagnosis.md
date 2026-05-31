# Samplereverse Handoff-Exit Diagnosis

## Decision Metadata

- Decision: `decision_20260531_resume_samplereverse_handoff_exit_diagnosis`
- Round: `round_20260531_resume_samplereverse_handoff_exit_diagnosis`
- Status: `APPROVED`
- Mainline: `reverse_solving`
- Skill profiles: `reverse-agent-iteration@v2`, `samplereverse-frontier@v2`
- State build: `state_20260527_153028_1d6dd81ecbd6`
- State digest: `1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02`

## State Source

- Selected/current run: `sr_arg0_hook_readiness_ordering_20260526_r1`
- Run status: `completed`
- Case: `samplereverse-compare-producer-backtrace`
- Summary: 1 case executed, 0 errors, 1 `NOT_FOUND`, evidence coverage `1.0`
- Current bottleneck: `compare_hook_path_reachability_audit`
- Current blocker: `decrypt_handler_entered_but_candidate_path_exits_before_handoff`
- Confidence: `medium`
- Best exact2 remains `78d540b49c59077041414141414141` with `runtime_ci_exact_wchars=2`, `runtime_ci_distance5=246`
- Best exact1/frontier remains `5a3e7f46ddd474d041414141414141` with `runtime_ci_exact_wchars=1`, `runtime_ci_distance5=258`

`project_state/task_packet.json` still carries the derived task text `Diagnose bounded compare hook path reachability`, but this is not the execution authority for this round. The current authority is `project_state/decision_packet.md`.

## Artifact Freshness

| Artifact | Freshness | Use in this diagnosis |
|---|---:|---|
| `run_manifest` | current | Current run identity and bounded sidecar configuration |
| `summary` | current | Current run outcome and case coverage |
| `compare_hook_path_reachability_audit` | current | Primary current evidence for handoff-exit classification |
| `compare_real_lhs_provenance_audit` | current | Current evidence limiting real-LHS provenance claims |
| `base64_rc4_static_point_discovery` | stale | Historical background only; not current evidence |
| `compare_handoff_return_site_probe` | stale | Historical background only; not current evidence |
| `function_semantic_audit` | stale | Historical background only; not current evidence |
| `compare_probe` | stale | Historical background only; not current evidence |
| `post_handoff_branch_outcome_audit` | missing | Not evidence |
| `post_handoff_exception_unwind_audit` | missing | Not evidence |
| `base64_rc4_breakpoint_probe` | missing | Not evidence |

No stale or missing artifact is used as current proof in this diagnosis.

## Current Evidence

`compare_hook_path_reachability_audit` is current and classifies the blocker as `decrypt_handler_entered_but_candidate_path_exits_before_handoff`.

Observed facts:

- Candidate count: 3
- Runtime-backed count: 3
- `actual_compare.observed_count`: 0
- `actual_compare.entry_status`: `rejected`
- `breakpoint_probe_allowed`: false
- Next bounded action from artifact: `continue the bounded path-reachability diagnosis without search expansion`
- For all 3 fixed candidates, hook hits include `predecessor_handoff_call=1`, `handoff_helper_entry=1`, and `process_exception=1`

The three fixed candidates were:

- `78d540b49c59077041414141414141`
- `5a3e7f46ddd474d041414141414141`
- `78d540b49c59076f41414141414141`

This means the current evidence reaches the predecessor/handoff region and observes process exception behavior, but it does not observe the actual compare call. The candidate path therefore exits before the compare/handoff connection can be proven.

`compare_real_lhs_provenance_audit` is current but remains an observability limiter, not a real-LHS proof.

Observed facts:

- Classification: `instrumentation_incomplete`
- Candidate count: 3
- Runtime-backed count: 3
- `scripted_hook_status`: `scripted_hook_no_observations`
- `scripted_returncode`: 124
- `scripted_error`: `timeout`
- `compare_probe_fallback_status`: `compare_probe_fallback_captured_compare_args`
- `compare_probe_fallback_is_provenance`: false
- `provenance.candidate_dependent`: false
- `provenance.connects_to_compare_lhs`: false
- `write_monitor_health.enabled`: true
- `write_monitor_health.raw_write_count`: 0
- Missing reason: `no_write_ring_events_observed`
- `breakpoint_probe_allowed`: false

Therefore the fallback compare argument capture cannot be treated as provenance, and the old `[ebp-0x1170]` frame anchor cannot be reused as the real LHS source.

## Handoff-Exit Hypotheses

1. `candidate-dependent path not reaching handoff/compare` is the strongest current explanation. All 3 fixed candidates enter the predecessor/handoff-adjacent region, hit `handoff_helper_entry`, then see `process_exception=1`, while actual compare observation remains zero.
2. `exception unwind before compare` is plausible and should be the first runtime-probe design target if a later decision allows runtime. The current audit observes process exceptions but does not include a current `post_handoff_exception_unwind_audit`, so it cannot yet classify the unwind path.
3. `branch guard before compare` is possible but not proven. Current artifacts do not include a current branch-outcome audit, so branch guard should stay a secondary hypothesis.
4. `wrong hook site` is weaker than the path-exit explanation. The hook-readiness audit shows the predecessor and helper entry are reached for all candidates, so the current problem is not simply that no bounded hook point can fire.

Minimum explanation: the candidates reach decrypt/handoff-adjacent code, then leave through an exception or candidate-dependent path before the actual compare call is observed. Current evidence is enough to design the next bounded runtime probe, but not enough to assert the exact branch or unwind instruction.

## Negative-Results Compliance

This diagnosis does not repeat blocked directions:

- No old `sample_solver` blind search.
- No beam, topN, budget, or timeout expansion.
- No exact2 basin value-pool evaluation.
- No H1/H3 fixed boundary contrast rerun.
- No current 5-candidate transform trace consistency audit rerun.
- No Base64/RC4 breakpoint probe.
- No compare return-site audit rerun.
- No producer material confirmation rerun.
- No claim that `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` is a Base64/RC4 material producer.
- No reuse of old `[ebp-0x1170]` as real LHS source.

## Next Action Recommendation

Next round should be a bounded runtime-probe decision, not a search expansion.

Recommended minimum probe:

- Keep the same 3 fixed candidates.
- Hook only the already implicated predecessor/handoff/exception path surface from the current run.
- Capture per-candidate control-flow outcome between `predecessor_handoff_call`, `handoff_helper_entry`, process exception, and the first possible compare/handoff successor.
- Classify whether the exit is branch guard, exception unwind, wrong successor/hook site, or candidate-dependent non-reaching path.
- Keep `breakpoint_probe_allowed=false` for Base64/RC4 material capture until real-LHS producer provenance is established.

If implementation cannot design that probe from these current artifacts without reading broader `solve_reports/`, first rebuild or refresh project_state for `sr_arg0_hook_readiness_ordering_20260526_r1` rather than running a new probe.

## Required Audit Answers

| # | Requirement | Answer |
|---:|---|---|
| 1 | Current mainline switched back to `reverse_solving` | Yes |
| 2 | `task_packet.task` is derived, not authority | Yes |
| 3 | `decision_packet.md` controls this round | Yes |
| 4 | Skill profiles are `reverse-agent-iteration@v2` + `samplereverse-frontier@v2` | Yes |
| 5 | `compare_hook_path_reachability_audit` is current | Yes |
| 6 | `compare_real_lhs_provenance_audit` is current | Yes |
| 7 | `run_manifest` / `summary` are current | Yes |
| 8 | Stale/missing artifacts were not used as current evidence | Yes |
| 9 | Hook path audit core conclusion | Candidate paths enter decrypt/handoff-adjacent code but exit before actual compare observation |
| 10 | Real-LHS provenance audit core conclusion | Instrumentation remains incomplete; fallback compare args are not provenance |
| 11 | Minimal handoff-exit explanation | Candidate-dependent exit or exception before compare/handoff connection |
| 12 | Enough to design next bounded runtime probe | Yes, for a targeted handoff/exception path classifier |
| 13 | Need project_state build first? | Not currently; all four current artifact paths exist and are readable |
| 14 | sample.exe not run | Yes |
| 15 | runtime probe not run | Yes |
| 16 | Base64/RC4 breakpoint probe not run | Yes |
| 17 | Full `solve_reports/` not read | Yes |
| 18 | Full `PROJECT_PROGRESS_LOG.txt` not read | Yes |
| 19 | `.codex-skills/` not modified | Yes |
| 20 | `sample_corpus/reverse/` not modified | Yes |
| 21 | Old sample_solver/search budget not used | Yes |
| 22 | negative_results failed directions not repeated | Yes |

