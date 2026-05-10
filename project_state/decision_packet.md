# DECISION_PACKET

## 1. Goal

Confirm the upstream material candidate at instruction level before enabling Base64/RC4 breakpoint capture.

The current objective is not to generate more candidates. The objective is to explain where the runtime-backed candidate buffer is produced or written, and whether it can be promoted to an instruction-confirmed, hookable material point such as:

- `base64_output`
- `rc4_input`
- `rc4_output`
- `rc4_key`
- `utf16le_payload`

Only after such a point is confirmed may `base64_rc4_breakpoint_probe` be enabled.

## 2. Current Evidence

Current strategy is `CompareAwareSearchStrategy`. The project state says the active bottleneck is:

- stage: `compare_producer_trace_probe`
- reason: `upstream_material_candidate_found`
- confidence: `medium`

Current best remains:

- exact2: `78d540b49c59077041414141414141`
- runtime exact wchars: `2`
- distance5: `246`
- `compare_semantics_agree=true`

The latest producer trace captured bounded producer context:

- `candidate_count=3`
- `runtime_backed_count=3`
- `candidate_material_count=18`
- `write_source_trace_count=0`
- `material_hook_candidate_count=0`
- `breakpoint_probe_allowed=false`

So the next task is specifically to explain the producer-side write source, not to rerun the same producer probe.

Static audit already identified instruction-confirmed compare/producer hook points:

- `0x233d` — producer return site
- `0x253a` — `mov dword ptr [ebp - 0x1170], eax`
- `0x2554` — call suspected handoff helper
- `0x2559` — reload lhs pointer from `[ebp-0x1170]`
- `0x258b` — push compare lhs pointer
- `0x258c` — wide compare call site
- `0x1028ac` — compare helper entry

Static discovery found compare-producer hooks, but no instruction-confirmed Base64/RC4 construction hook. Therefore breakpoint probing remains gated.

## 3. Do Not Do

Do not:

- return to old `sample_solver` blind search
- only increase beam, budget, topN, timeout, or frontier iterations
- use `compare_semantics_agree=false` candidates as the primary frontier
- commit the full `solve_reports` directory
- rerun the exact2 basin value-pool evaluation already marked negative
- rerun the H1/H3 fixed 8-candidate prefix8 contrast set
- repeat the current transform trace consistency audit without new runtime evidence
- rerun `base64_rc4_breakpoint_probe` before confirming a Base64/RC4 or UTF-16LE material instruction hook
- repeat `compare_producer_trace_probe` without using its classification

## 4. Files To Inspect

Inspect only the narrow relevant code and artifacts:

- `reverse_agent/olly_scripts/compare_producer_trace_probe.py`
- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Inspect these artifacts selectively, not the full `solve_reports` tree:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- latest `compare_producer_trace_probe.json`
- latest `base64_rc4_static_point_discovery.json`

## 5. Required Audit

Perform a bounded instruction-level audit around the already identified producer/compare window.

Required questions:

1. At `0x253a`, confirm what `eax` points to before being stored into `[ebp-0x1170]`.
2. Trace backwards from `0x253a` within the bounded producer window to identify the instruction or helper responsible for constructing the buffer pointed to by `eax`.
3. Determine whether the runtime-backed candidate bytes are:
   - actual material transformation output, or
   - only a nearby heap/stack buffer observed in producer context.
4. For the best observed candidate buffer address, identify whether any instruction writes candidate-dependent bytes into it.
5. If a write instruction is found, classify the material kind:
   - `utf16le_payload`
   - `base64_output`
   - `rc4_input`
   - `rc4_output`
   - `rc4_key`
   - or `unknown_buffer`
6. Only promote a hook if both are true:
   - instruction boundary is confirmed
   - hook point is stable and hookable

The output must include a compact `write_source_trace`, even if empty, with a clear reason.

## 6. Implementation Scope

Allowed implementation:

- Improve the producer trace probe so it can capture a bounded write-source trace for the observed `eax` candidate buffer.
- Add static/dynamic correlation between:
  - producer return site
  - `eax`
  - `[ebp-0x1170]`
  - lhs reload at `0x2559`
  - compare push/call at `0x258b/0x258c`
- Add classification logic that distinguishes:
  - instruction-confirmed material hook
  - runtime-backed but not instruction-confirmed buffer
  - unrelated buffer
  - control-flow skipped hook
- Update compact project state rendering to expose the new audit result.

Not allowed:

- broad candidate generation
- full binary-wide scanning
- full `solve_reports` ingestion
- expanding search budgets
- enabling breakpoint probe without a material hook

## 7. Tests

Run at minimum:

```bash
python -m py_compile reverse_agent\olly_scripts\compare_producer_trace_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_compare_producer_backtrace_20260508
```

If code touches shared strategy behavior, also run:

```bash
python -m pytest -q
```

## 8. Stop Conditions

Stop and report if any of the following is reached:

1. A hookable instruction-confirmed material point is found.
2. The candidate buffer is proven to be non-material or unrelated.
3. The write source cannot be recovered within the bounded producer/compare window.
4. The relevant hook is skipped by control flow and needs a different bounded hook site.
5. The artifact lacks enough runtime data to continue, in which case request a narrow rerun that captures only the missing instruction/write context.

Expected final output from Codex:

- updated `CODEX_EXECUTION_REPORT`
- updated compact `project_state`
- new or updated focused artifact showing:
  - `write_source_trace`
  - `material_hook_candidates`
  - `breakpoint_probe_allowed`
  - `next_bounded_action`
