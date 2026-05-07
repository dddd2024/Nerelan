# CODEX_EXECUTION_REPORT

## Summary

Implemented and executed the bounded `pre_rc4_material_probe` upgrade for `samplereverse`.

This iteration consumes the prior `producer_trace_inconclusive` bottleneck. It does not add candidates and does not change ranking, final selection, promotion, beam, budget, topN, timeout, or frontier iteration limits. The probe now emits offline/runtime material agreement rows and RC4-to-producer relation rows.

## Files Changed

| area | change | behavior impact |
|---|---|---|
| script | Upgraded `reverse_agent/olly_scripts/pre_rc4_material_probe.py` | normalizes material matches with hex, ASCII, UTF-16LE previews, match counts, and surrogate-safe JSON |
| strategy | Enhanced `run_pre_rc4_material_probe()` | adds material agreement, producer relation, new classifications, and producer-trace-to-material routing |
| project state | Exposes material agreement/relation fields | compact state now reports `pre_rc4_material_probe` / `material_capture_partial` |
| tests | Updated pre-RC4 and project_state coverage | protects schema, no-promotion/no-budget behavior, and RC4-to-producer relation handling |

## Runtime Artifact

| item | value |
|---|---|
| harness run | `samplereverse_pre_rc4_material_probe_20260507` |
| status | completed, 1 case, 0 errors |
| artifact | `solve_reports\harness_runs\samplereverse_pre_rc4_material_probe_20260507\reports\tool_artifacts\samplereverse\pre_rc4_material_probe\pre_rc4_material_probe.json` |
| classification | `material_capture_partial` |
| candidates | 3 |
| runtime-backed candidates | 3 |

## Material Availability

| material | status |
|---|---|
| `raw_input` | unavailable |
| `expanded_bytes` | unavailable |
| `utf16le_payload` | unavailable |
| `base64_material` | unavailable |
| `rc4_ksa_key` | unavailable |
| `rc4_encrypted_const` | unavailable |
| `rc4_output` | unavailable |
| `compare_buffer` | unavailable |

## Agreement And Relation

| check | result |
|---|---|
| offline/runtime UTF-16LE agreement | unknown for all 3 candidates |
| offline/runtime Base64 agreement | unknown for all 3 candidates |
| offline/runtime RC4 agreement | unknown for all 3 candidates |
| first divergence stage | `unknown` |
| RC4 -> producer.eax/lhs relation | `no_match` for all 3, because runtime RC4 material was not captured |

The automatic memory scan reached the compare trigger but did not expose the requested pre-RC4/Base64/RC4 material buffers. This is a partial material capture, not evidence of transform divergence.

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent\olly_scripts\pre_rc4_material_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py` | `88 passed` |
| `python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py` | `26 passed` |
| `python -m pytest -q` | `181 passed` |
| `python -m reverse_agent.harness --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json --run-name samplereverse_pre_rc4_material_probe_20260507 --reports-dir solve_reports --analysis-mode "Auto" --model-type "Copilot CLI" --copilot-timeout-seconds 300 --ctf-skill-profile compact --case-id samplereverse-exact1-projected-vs-neighbor --no-resume` | completed, 1 case, 0 errors |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_pre_rc4_material_probe_20260507` | passed |
| `python -m reverse_agent.project_state status` | `reason: material_capture_partial` |

## Next Suggested Task

Do not expand candidate search. Add a narrower material hook or run the bounded Base64/RC4 breakpoint fallback; the current automatic memory scan did not capture UTF-16LE/Base64/RC4 runtime buffers.
