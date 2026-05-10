# CODEX_EXECUTION_REPORT

## Summary

Implemented the reusable Function Semantic Audit Layer and applied it to the current `samplereverse` producer-window bottleneck.

The new layer records compact function-level semantic facts for `0x4019e0`, `0x401b50`, `0x4018cd`, and `0x401be3`, centralizes the material hook readiness gate, and keeps Base64/RC4 breakpoint probing blocked until a function is instruction-confirmed, hookable, candidate-dependent, and connected to the compare lhs or known transform chain.

## Files Changed

| area | change | behavior impact |
|---|---|---|
| semantic layer | Added `reverse_agent/function_semantics.py` | normalizes function semantic records and computes conservative breakpoint readiness |
| strategy | Added `function_semantic_audit.json` generation after material confirmation | persists function/dataflow evidence without changing candidate search |
| strategy | Tightened static/material breakpoint gates | confirmed hooks alone no longer allow Base64/RC4 capture without semantic readiness |
| project state | Indexed and summarized `function_semantic_audit` | current bottleneck now points to semantic audit evidence |
| negative cache | Added function-level semantic soft blocks | avoids treating the same function as Base64/RC4 material without new evidence |
| guidance | Documented PowerShell-native search preference | avoids repeating blocked `rg.exe` attempts in this desktop environment |
| tests | Added semantic gate and project_state coverage | protects schema, indexing, compact rendering, and conservative gating |

## Artifact Result

| item | value |
|---|---|
| source run | `samplereverse_material_confirmation_20260510_rerun2` |
| artifact | `solve_reports\harness_runs\samplereverse_material_confirmation_20260510_rerun2\reports\tool_artifacts\samplereverse_patched\function_semantic_audit\function_semantic_audit.json` |
| classification | `runtime_instrumentation_required` |
| function_count | `4` |
| material_hook_candidate_count | `0` |
| breakpoint_probe_allowed | `false` |
| current bottleneck | `function_semantic_audit / runtime_instrumentation_required` |

Semantic facts learned:

| function | current read | missing evidence |
|---|---|---|
| `0x4019e0` | instruction-confirmed but not runtime-hooked in latest confirmation | prove whether it writes `[ebp-0x1168]` on the active path |
| `0x401b50` | strongest bounded suspect; `0x2338` reached for all 3 diagnostic candidates | confirm return/branch outcome and candidate-dependent output after the call |
| `0x4018cd` | downstream call site, not reached | explain why execution stops before `0x234e` |
| `0x401be3` | later downstream call site, not reached | depends on resolving the missed 0x401b50/0x234e path |

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py` | `119 passed` |
| `python -m pytest -q` | `196 passed` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_material_confirmation_20260510_rerun2` | passed |

## Current Best

No runtime candidate improved during this architecture/evidence change. The current best remains exact2:

`78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`.

## Next Suggested Task

Add the smallest runtime/static confirmation for the `0x2338 -> 0x401b50` call outcome: determine why `0x233d`, `0x234e`, and `0x2355` are not reached, and only promote a material hook if it becomes candidate-dependent and connected to compare lhs or the transform chain.
