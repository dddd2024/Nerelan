# CODEX_EXECUTION_REPORT

## 2026-05-17 Summary

Implemented the bounded `post_handoff_exception_unwind_audit` sidecar for `samplereverse`.

The new layer consumes `post_handoff_branch_outcome_audit / handoff_exception_or_unwind`, keeps the fixed three-candidate set, does not expand search, and keeps Base64/RC4 probing blocked unless actual compare lhs, connected producer, and candidate-dependent transform material are all runtime-backed.

## Files Changed This Round

| area | change | behavior impact |
|---|---|---|
| strategy | Added `post_handoff_exception_unwind_audit.json` schema, classifier, runner, and early sidecar scheduling | advances from broad exception/unwind evidence to an evidence-gated path route |
| runtime probe | Added `reverse_agent/olly_scripts/post_handoff_exception_unwind_audit.py` | thin entry reusing the bounded Frida/UIA collector shape |
| project state | Indexed `latest_post_handoff_exception_unwind_audit` and task routing | bottleneck now advances to the new artifact when present |
| negative cache | Added blocks for Base64/RC4 probing before material gates and for repeating inconclusive/hook-miss audits | preserves bounded evidence-driven iteration |
| tests | Added strategy and project_state coverage | protects fixed candidates, evidence gates, routing, early sidecar hard-stop, and state indexing |

## Latest Harness Result

Run:

`sr_401b50_exception_unwind_20260517_r1`

Core artifact:

`solve_reports\harness_runs\sr_401b50_exception_unwind_20260517_r1\reports\tool_artifacts\samplereverse_patched\post_handoff_exception_unwind_audit\post_handoff_exception_unwind_audit.json`

Result:

| field | value |
|---|---|
| `classification` | `compare_reached_but_path_unresolved` |
| `candidate_count` | `3` |
| `runtime_backed_count` | `3` |
| `post_classification_route` | `last_writer_memory_provenance_before_0x258c` |
| `evidence_gate.compare_entry_observed` | `true` |
| `evidence_gate.compare_args_captured` | `true` |
| `evidence_gate.exception_evidence` | `false` |
| `evidence_gate.handler_unwind_evidence` | `false` |
| `evidence_gate.connected_producer_runtime_backed` | `false` |
| `evidence_gate.candidate_dependent_transform_material_runtime_backed` | `false` |
| `breakpoint_probe_allowed` | `false` |

Tentative hook status:

| tentative offset | artifact field | status |
|---|---|---|
| `0x1913` | `tentative_hook_candidates[].module_offset == "0x1913"` | `tentative_not_observed` |
| `0x19bb` | `tentative_hook_candidates[].module_offset == "0x19bb"` | `tentative_not_observed` |
| `0x19fe` | `tentative_hook_candidates[].module_offset == "0x19fe"` | `tentative_not_observed` |
| `0x1a30` | `tentative_hook_candidates[].module_offset == "0x1a30"` | `tentative_not_observed` |

No candidate generation, ranking, frontier, beam, topN, or search timeout expansion was introduced. The current best remains:

`78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`.

Project state now reports:

`reason: compare_reached_but_path_unresolved`, `task: Trace last-writer memory provenance before 0x258c`, `missing: []`.

## Verification This Round

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\post_handoff_exception_unwind_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py` | `195 passed` |
| `python -m pytest -q` | `272 passed` |
| `python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_401b50_exception_unwind_20260517_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled` | completed, 1 case, 0 errors, selected `NOT_FOUND` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_401b50_exception_unwind_20260517_r1` | passed |
| `python -m reverse_agent.project_state status` | `reason: compare_reached_but_path_unresolved`, `missing: []` |

## Next Suggested Task

Keep Base64/RC4 probing blocked. Trace last-writer or memory provenance immediately before `0x258c`, because this run confirmed compare entry and arg capture but did not prove the tentative exception/handler offsets or a connected producer.

## 2026-05-14 Summary

Implemented the bounded `compare_callsite_reanchor_and_lhs_provenance_audit` sidecar for `samplereverse`.

The new layer runs after `compare_lhs_upstream_writer_audit` reports `candidate_dependent_upstream_observed`. It keeps the fixed three-candidate set, does not expand search, and keeps Base64/RC4 probing blocked unless a real compare lhs side and connected producer are both runtime-backed.

## Files Changed This Round

| area | change | behavior impact |
|---|---|---|
| strategy | Added `compare_callsite_reanchor_and_lhs_provenance_audit.json` schema, classifier, runner, and early sidecar scheduling | re-anchors from actual compare entry before trusting old frame slots |
| runtime probe | Added `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py` | thin entry reusing the bounded Frida/UIA collector shape |
| project state | Indexed `latest_compare_callsite_reanchor_and_lhs_provenance_audit` | bottleneck advances to the new audit when present |
| negative cache | Added blocks for old `[ebp-0x1170]` reuse and direct Base64/RC4 probing from this audit | prevents material probing before compare lhs provenance closes |
| tests | Added strategy and project_state coverage | protects fixed candidates, no-expansion flags, scheduler ordering, and state indexing |

## Latest Harness Result

Run:

`sr_callsite_reanchor_20260514_r5`

Core artifact:

`solve_reports\harness_runs\sr_callsite_reanchor_20260514_r5\reports\tool_artifacts\samplereverse_patched\compare_callsite_reanchor_and_lhs_provenance_audit\compare_callsite_reanchor_and_lhs_provenance_audit.json`

Result:

| field | value |
|---|---|
| `classification` | `inconclusive` |
| `candidate_count` | `3` |
| `runtime_backed_count` | `3` |
| `actual_compare.entry_status` | `rejected` |
| `actual_compare.observed_count` | `0` |
| `actual_compare.lhs_side` | `unknown` |
| `actual_compare.flag_side` | `unknown` |
| `frame_anchor.old_slot_ebp_minus_1170_status` | `inconclusive` |
| `breakpoint_probe_allowed` | `false` |

Important correction made during execution: the first implementation treated a three-candidate run as actual compare confirmation even when only upstream hooks fired. The classifier now requires actual compare entry observations before reporting re-anchor success.

Project state now reports:

`reason: inconclusive`

## Verification This Round

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\compare_callsite_reanchor_and_lhs_provenance_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py` | `144 passed` |
| `python -m pytest -q` | `221 passed` |
| `python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_callsite_reanchor_20260514_r5 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled` | completed, 1 case, 0 errors, selected `NOT_FOUND` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_callsite_reanchor_20260514_r5` | passed |
| `python -m reverse_agent.project_state status` | `reason: inconclusive`, `missing: []` |

## Current Best

No candidate generation, ranking, frontier, budget, beam, topN, or search timeout expansion was introduced. The current best remains:

`78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`.

## Next Suggested Task

Keep Base64/RC4 probing blocked. Improve actual compare entry hook coverage or argument capture first; the new sidecar shows upstream hooks are reachable, but `0x1028ac` compare entry did not produce arg0/arg1 observations in r5.

## 2026-05-13 Summary

Implemented the bounded `compare_lhs_producer_audit` sidecar for `samplereverse`.

The new layer consumes the existing `post_handoff_window_rejected` bottleneck, runs only the fixed three-candidate cross-check, and writes `compare_lhs_producer_audit.json`. It does not expand search and never authorizes Base64/RC4 breakpoint probing.

## Files Changed This Round

| area | change | behavior impact |
|---|---|---|
| strategy | Added `compare_lhs_producer_audit.json` builder/classifier/runner | classifies `producer_identified`, `producer_window_rejected`, or `inconclusive` |
| runtime probe | Added `reverse_agent/olly_scripts/compare_lhs_producer_audit.py` | thin entry reusing the existing Frida/UIA collector shape |
| scheduler | Added early sidecar before bridge/search | existing `post_handoff_window_rejected` now runs lhs producer audit first |
| project state | Indexed `latest_compare_lhs_producer_audit` | bottleneck advances to `compare_lhs_producer_audit` |
| negative cache | Added compare lhs producer audit blocks | rejected/inconclusive evidence does not trigger search expansion or Base64/RC4 probe |
| tests | Added builder, runner, sidecar, and project_state coverage | protects fixed candidates, no-expansion flags, relations, and state indexing |

## Latest Harness Result

Run:

`sr_lhs_prod_20260513_r1`

Core artifact:

`solve_reports\harness_runs\sr_lhs_prod_20260513_r1\reports\tool_artifacts\samplereverse_patched\compare_lhs_producer_audit\compare_lhs_producer_audit.json`

Result:

| field | value |
|---|---|
| `classification` | `producer_window_rejected` |
| `candidate_count` | `3` |
| `runtime_backed_count` | `3` |
| `breakpoint_probe_allowed` | `false` |
| `next_bounded_action` | move earlier than `0x253a..0x258b` |

Window summary:

| hook | runtime backed | candidate dependent | connects to compare lhs |
|---|---:|---|---|
| `pre_lhs_slot_store` | 3 | false | false |
| `pre_handoff_call` | 1 | false | false |
| `post_handoff_lhs_reload` | 0 | false | false |
| `pre_compare_lhs_push` | 0 | false | false |
| `compare_helper_entry` | 0 | false | false |

Project state now reports:

`reason: producer_window_rejected`

## Verification This Round

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\compare_lhs_producer_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py` | `135 passed` |
| `python -m pytest -q` | `212 passed` |
| `python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_prod_20260513_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled` | completed |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_prod_20260513_r1` | passed |
| `python -m reverse_agent.project_state status` | `reason: producer_window_rejected`, `missing: []` |

## Current Best

No candidate generation, ranking, frontier, budget, beam, topN, or search timeout expansion was introduced. The current best remains:

`78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`.

## Next Suggested Task

Keep Base64/RC4 probing blocked. Move earlier than `0x253a..0x258b` to locate the real producer feeding compare lhs.

## Summary

Implemented the bounded `material_hook_runtime_validation` gate for `samplereverse`.

The new layer validates only `module+0x233d` and `module+0x2346` against the fixed four-candidate set from the plan. It records register/window/frame previews, classifies each hook, and keeps Base64/RC4 breakpoint probing blocked unless the runtime artifact proves candidate-dependent transform material.

## Files Changed

| area | change | behavior impact |
|---|---|---|
| runtime probe | Added `reverse_agent/olly_scripts/material_hook_runtime_validation.py` | thin script entry for the new material hook validation pass |
| strategy | Added `material_hook_runtime_validation.json` scheduling and schema | runs after `function_semantic_audit / material_hook_ready`, before Base64/RC4 |
| strategy gate | Added validation-backed breakpoint gate | Base64/RC4 probe now requires `ACCEPT` plus confirmed transform material |
| timeout guard | Added subprocess hard timeout for material validation candidates | prevents a stuck Frida/UIA child from hanging the strategy |
| project state | Indexed and summarized material hook runtime validation | exposes `latest_material_hook_runtime_validation` in current state and task packets |
| negative cache | Added material-hook blocked/rejected guidance | avoids rerunning Base64/RC4 when `0x233d/0x2346` fail validation |
| tests | Added accept/block/timeout and project_state coverage | protects schema, gating, indexing, and bounded no-expansion behavior |

## Artifact Schema

New artifact:

`material_hook_runtime_validation/material_hook_runtime_validation.json`

Key fields:

| field | purpose |
|---|---|
| `classification` | `ACCEPT`, `BLOCKED`, or `REJECTED` |
| `candidate_count` | fixed at `4` for the planned candidate set |
| `validated_hooks` | hooks classified as confirmed transform material |
| `blocked_hooks` | reached/readable hooks that do not satisfy transform-chain gating |
| `breakpoint_probe_allowed` | final gate for Base64/RC4 breakpoint probe |
| `next_bounded_action` | compact next action derived from the runtime result |

Per-hook classifications remain restricted to:

`confirmed_utf16le_material`, `candidate_dependent_but_not_transform_material`, `unreadable_or_unstable_pointer`, `not_reached`, `false_positive`.

## Harness Result

Attempted real run:

`samplereverse_material_hook_runtime_validation_20260512`

The run reached the new validation stage but candidate 1 hung inside the child runtime script before writing candidate output. I stopped the two spawned Python processes and added a strategy-level hard timeout so later runs cannot hang indefinitely at this point. The partial run only wrote the initial aggregate artifact, so project state was rebuilt against the last completed run instead:

`samplereverse_pre_compare_handoff_target_20260512`

Current indexed material validation remains empty until a completed run produces the new artifact.

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\material_hook_runtime_validation.py reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py` | `127 passed` |
| `python -m pytest -q` | `204 passed` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_pre_compare_handoff_target_20260512` | passed |

## Current Best

No candidate generation, ranking, frontier, budget, beam, topN, or timeout expansion was introduced for search. The current best remains:

`78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`.

## Next Suggested Task

Rerun the real harness with the new timeout guard. If validation returns `BLOCKED` or `REJECTED`, keep Base64/RC4 probing blocked and inspect why the `0x233d/0x2346` runtime window is not exposing UTF-16LE/Base64/RC4 material.
