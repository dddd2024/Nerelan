# CODEX_EXECUTION_REPORT

## Summary

Implemented and executed the bounded `compare_handoff_return_site_probe` diagnostic for `samplereverse`.

This iteration does not add candidates and does not change ranking, final selection, promotion, beam, budget, topN, timeout, or frontier iteration limits. It audits the stalled helper slice by recording the actual helper return site and validating whether the compare-call stack arguments can be captured at `module+0x258c`.

## Implemented Changes

| area | change | behavior impact |
|---|---|---|
| script | Added `reverse_agent/olly_scripts/compare_handoff_return_site_probe.py` | Frida/UI hook capture for helper return addresses, dynamic return-site hooks, and compare-call stack arguments |
| strategy | Added `COMPARE_HANDOFF_RETURN_SITE_PROBE_FILE_NAME` and `run_compare_handoff_return_site_probe()` | diagnostic metadata only; no promotable candidates |
| project state | Indexes `compare_handoff_return_site_probe` and makes it the latest bottleneck | compact state now reports `wrong_helper_assumption` |
| tests | Added schema, no-promotion/no-budget, return-site relation, and project_state coverage | protects bounded diagnostic behavior |

## Runtime Artifact

| item | value |
|---|---|
| harness run | `samplereverse_compare_return_site_probe_20260507` |
| status | completed, 1 case, 0 errors |
| artifact | `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\reports\tool_artifacts\samplereverse\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json` |
| classification | `wrong_helper_assumption` |
| candidates | 3 |
| runtime-backed candidates | 3 |
| hook results | `handoff_helper_enter=available`, `handoff_helper_return=available`, `helper_return_site=available`, `lhs_slot=available`, `post_handoff_lhs_reload=unavailable`, `post_handoff_after_reload=unavailable`, `pre_compare_push_esi=unavailable`, `wide_flag_prefix_compare=unavailable`, `compare_call_args=unavailable` |

## Probe Findings

- Static audit confirmed instruction boundaries for `0x253a`, `0x2554`, `0x2559`, `0x258b`, and `0x258c`; `0x255c` is inside the `0x2559` reload instruction.
- The helper return address was `module+0x233d` for all 3 diagnostic candidates, not `module+0x2559`.
- The dynamic return-site hook observed `helper_return_site_0x233d` for all 3 diagnostic candidates.
- `wide_flag_prefix_compare` and compare-call stack args were not captured in this run, so the compare arg order remains unproven.
- Current best runtime candidate did not improve: exact2 remains `78d540b49c59077041414141414141`, `runtime_ci_exact_wchars=2`, `runtime_ci_distance5=246`.

## Commands

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\compare_handoff_return_site_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py` | `85 passed` |
| `python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py` | `25 passed` |
| `python -m pytest -q` | `177 passed` |
| `python -m reverse_agent.harness --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json --run-name samplereverse_compare_return_site_probe_20260507 --reports-dir solve_reports --analysis-mode "Auto" --model-type "Copilot CLI" --copilot-timeout-seconds 300 --ctf-skill-profile compact --case-id samplereverse-exact1-projected-vs-neighbor --no-resume` | completed, 1 case, 0 errors |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_compare_return_site_probe_20260507` | passed |
| `python -m reverse_agent.project_state status` | `reason: wrong_helper_assumption` |

## Conclusion

The return-site audit proves the current `0x401b50` helper observation is not the missing post-helper handoff into `module+0x2559`. The next bounded direction is to move to a nearer pre-compare handoff target instead of expanding candidate search or rerunning the same helper-slice hook set.
