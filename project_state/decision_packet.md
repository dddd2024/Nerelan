# DECISION_PACKET

## 1. Goal

Resolve the current `function_semantic_audit` bottleneck for `samplereverse`.

The next Codex task is to perform a bounded runtime/static audit around the newly identified material hook candidates:

```text
module+0x233d
module+0x2346
```

The objective is to determine whether these sites can expose candidate-dependent UTF-16LE / pre-Base64 material that connects to the known transform chain:

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

Only if this is proven should the Base64/RC4 breakpoint probe gate be reopened.

Current project state says the bottleneck is:

```text
stage = function_semantic_audit
reason = material_hook_ready
confidence = medium
```

Current best candidates remain:

```text
exact2:
78d540b49c59077041414141414141
runtime exact_wchars = 2
distance5 = 246

frontier / exact1:
5a3e7f46ddd474d041414141414141
runtime exact_wchars = 1
distance5 = 258
```

This round is an evidence-gathering task, not a candidate-search expansion task.

## 2. Current Evidence

Use these facts as ground truth:

### A. Current bottleneck

`project_state/current_state.json` marks the active bottleneck as:

```json
{
  "stage": "function_semantic_audit",
  "reason": "material_hook_ready",
  "confidence": "medium"
}
```

### B. Current best candidates

The current exact2 candidate is:

```text
78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true
source = pairscan
```

The current frontier / exact1 candidate is:

```text
5a3e7f46ddd474d041414141414141
runtime_ci_exact_wchars = 1
runtime_ci_distance5 = 258
compare_semantics_agree = true
source = exact2_seed(78d540b49c590770) -> refine(seed) -> guided(frontier)
```

Do not promote any candidate where `compare_semantics_agree = false`.

### C. New material hook candidates

`function_semantics` now marks two sites as ready material-hook candidates:

```text
0x233d
0x2346
```

Both currently have:

```text
semantic_guess = utf16le_constructor
candidate_dependent = true
hookable = true
instruction_confirmed = true
material_hook_candidate_status = ready
confidence = medium
```

These are the only new material-hook candidates that justify another bounded runtime validation.

### D. Previous Base64/RC4 breakpoint probe result

The previous Base64/RC4 breakpoint probe classified as:

```text
base64_rc4_compare_only
```

Its captured material status was:

```text
compare_buffer = available
base64_input = unavailable
base64_output = unavailable
rc4_input = unavailable
rc4_key = unavailable
rc4_output = unavailable
utf16le_payload = unavailable
```

Therefore, do not repeat the same Base64/RC4 probe unless the new material hook validation confirms a transform-chain material site.

### E. Static point discovery status

Static point discovery found hookable compare-producer points, including:

```text
0x2559
0x1b50
```

But Base64 / RC4 KSA / RC4 PRGA remain unresolved or not hookable. Treat compare-producer hooks as insufficient for Base64/RC4 material capture unless connected to the transform chain by runtime evidence.

### F. Codex previous implementation status

The previous Codex round implemented the reusable Function Semantic Audit Layer:

```text
reverse_agent/function_semantics.py
function_semantic_audit.json generation
project_state indexing and summary
semantic breakpoint readiness gate
tests for schema, indexing, and conservative gating
```

The previous test baseline was:

```text
196 passed
```

No runtime candidate improved during that architecture/evidence change.

## 3. Do Not Do

Do not do any of the following:

```text
1. Do not return to old sample_solver blind search.
2. Do not only increase guided_pool beam, budget, timeout, topN, or search width.
3. Do not use compare_semantics_agree=false candidates as primary frontier.
4. Do not commit the full solve_reports directory.
5. Do not repeat exact2 basin value-pool evaluation with the already-tested pools.
6. Do not repeat the H1/H3 fixed 8-candidate prefix8 plus Base64 boundary contrast set.
7. Do not repeat the current 5-candidate transform trace consistency audit without new runtime evidence.
8. Do not repeat the scripted Base64/RC4 breakpoint probe with the same static access points.
9. Do not rerun Base64/RC4 breakpoint probe before confirming a material construction hook.
10. Do not repeat compare return-site audit without using its classification.
11. Do not repeat compare producer trace without using its classification.
12. Do not repeat producer material confirmation without adding instruction-level evidence.
13. Do not repeat the old 0x401b50 -> 0x2559 helper assumption.
14. Do not scan the entire solve_reports tree unless a specific indexed artifact is insufficient.
```

These constraints are already recorded in `project_state/negative_results.json`. Treat `compare_semantics_agree=false` and committing full `solve_reports` as hard blocks.

## 4. Files To Inspect

Start with the project state files:

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

Then inspect only the bounded implementation files:

```text
reverse_agent/function_semantics.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

Use these indexed artifacts directly. Do not scan full `solve_reports`:

```text
solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\function_semantic_audit\function_semantic_audit.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_pre_compare_handoff_target_probe\compare_pre_compare_handoff_target_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\base64_rc4_breakpoint_probe\base64_rc4_breakpoint_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\base64_rc4_static_point_discovery\base64_rc4_static_point_discovery.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_producer_material_confirmation\compare_producer_material_confirmation.json
```

Search terms:

```text
function_semantic_audit
material_hook_candidate_status
breakpoint_probe_allowed
candidate_dependent
utf16le_payload
base64_rc4_breakpoint_probe
compare_pre_compare_handoff_target_probe
0x233d
0x2346
0x401b50
0x2559
```

## 5. Required Audit

Codex must perform a narrow audit with this exact purpose:

```text
Validate whether 0x233d / 0x2346 expose candidate-dependent UTF-16LE or pre-Base64 transform material.
```

### A. Confirm instruction-level behavior at 0x233d and 0x2346

For each diagnostic candidate, record:

```text
hit_count
register state
pointer values
readable memory windows
preview_hex
preview_utf16le or decoded preview if safe
whether preview changes across candidates
whether preview corresponds to UTF-16LE-expanded user input
whether this material can feed later Base64 / RC4 / compare path
```

Minimum diagnostic candidates:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
414141414141414141414141414141
```

Optional contrast candidate:

```text
78d540b49c59076f41414141414141
```

### B. Classify each hook

For each of `0x233d` and `0x2346`, assign exactly one classification:

```text
confirmed_utf16le_material
candidate_dependent_but_not_transform_material
unreadable_or_unstable_pointer
not_reached
false_positive
```

### C. Verify transform-chain connection

A hook is not sufficient merely because it is candidate-dependent.

Codex must explicitly decide whether the observed material connects to one of:

```text
UTF-16LE payload
Base64 input
Base64 output
RC4 input
RC4 output
compare lhs
```

If the observed material is only compare-side material, classify it as insufficient and keep the Base64/RC4 probe blocked.

### D. Decide whether Base64/RC4 probe is allowed

Only set:

```text
breakpoint_probe_allowed = true
```

if at least one hook satisfies all of:

```text
instruction_confirmed = true
hookable = true
candidate_dependent = true
connects_to_transform_chain = true
material_kind in ["utf16le_payload", "base64_input", "base64_output", "rc4_input", "rc4_output"]
```

Otherwise keep:

```text
breakpoint_probe_allowed = false
```

and state the missing evidence.

### E. Produce a compact artifact

Generate a new compact artifact such as:

```text
solve_reports\...\tool_artifacts\samplereverse_patched\material_hook_runtime_validation\material_hook_runtime_validation.json
```

The artifact should include at least:

```json
{
  "classification": "...",
  "candidate_count": 3,
  "validated_hooks": [],
  "blocked_hooks": [],
  "breakpoint_probe_allowed": false,
  "next_bounded_action": "..."
}
```

For each hook, include compact per-candidate evidence:

```json
{
  "hook": "0x233d",
  "instruction_confirmed": true,
  "hit_count": 3,
  "candidate_dependent": true,
  "material_kind": "utf16le_payload",
  "connects_to_transform_chain": true,
  "classification": "confirmed_utf16le_material",
  "evidence": []
}
```

## 6. Implementation Scope

This round should be mostly instrumentation and evidence collection.

Allowed changes:

```text
1. Add or extend a small runtime validation probe for material hooks.
2. Add compact schema support if necessary.
3. Update project_state builder so the new validation result appears in current_state.json, artifact_index.json, and task_packet.json.
4. Update tests for hook classification, breakpoint gate behavior, and project_state indexing.
```

Avoid broad solver changes.

Do not change:

```text
candidate generation
candidate ranking
frontier promotion
beam
budget
timeout
topN
solver scoring
```

If a hook is validated, the next step is to unlock the bounded Base64/RC4 material probe. Do not also perform a large search expansion in this same round.

## 7. Tests

Run at minimum:

```powershell
python -m py_compile reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
python -m pytest -q
```

Then rebuild project state:

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_run_name>
```

Expected result:

```text
all tests pass
project_state files updated
new artifact indexed
no full solve_reports commit
```

## 8. Stop Conditions

Stop immediately and report if any of these happens:

```text
1. 0x233d and 0x2346 are not reached for diagnostic candidates.
2. The pointers at 0x233d / 0x2346 are unreadable or unstable across runs.
3. The observed material is candidate-dependent but does not match UTF-16LE input expansion or any known transform-chain material.
4. The probe only captures compare-buffer material again.
5. A Base64/RC4 hook is still not instruction-confirmed.
6. Runtime evidence contradicts the current function_semantic_audit classification.
7. The next step would require scanning the full solve_reports tree.
8. Any exact3+ or distance5 improvement appears unexpectedly.
9. Candidate ranking changes unexpectedly.
10. Tests fail and cannot be fixed within the bounded scope.
```

The final `CODEX_EXECUTION_REPORT.md` must explicitly state one of:

```text
ACCEPT: material hook validated, Base64/RC4 probe may proceed
BLOCKED: material hook not validated, need different bounded audit
REJECTED: current hook hypothesis is false
```

It must also include:

```text
1. Which probe was added or modified.
2. Whether 0x233d was reached.
3. Whether 0x2346 was reached.
4. What material was readable at each site.
5. Whether the material was candidate-dependent.
6. Whether the material matched UTF-16LE / Base64 / RC4 / compare-chain expectations.
7. Whether breakpoint_probe_allowed is true or false.
8. Whether any candidate improved.
9. Which tests passed.
10. Which artifact path contains the evidence.
```

One-line instruction for Codex:

```text
Validate the new 0x233d / 0x2346 material hook candidates with a minimal runtime/static probe, update function_semantics and project_state with candidate-dependence and transform-chain evidence, and keep Base64/RC4 probing gated unless a hook becomes instruction-confirmed, hookable, candidate-dependent, and connected to real transform material.
```
