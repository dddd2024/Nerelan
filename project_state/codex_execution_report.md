# CODEX_EXECUTION_REPORT

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
