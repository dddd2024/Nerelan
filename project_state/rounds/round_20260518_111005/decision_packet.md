# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

Fix `compare_real_lhs_provenance_audit` write-monitor instrumentation so the `static_compare_callsite / 0x258c` sidecar itself emits `write_monitor_health` for all 3 fixed candidates.

Current goal is not to search for new candidates and not to run Base64/RC4 probes. The immediate blocker is:

```text
stage: compare_real_lhs_provenance_audit
reason: instrumentation_incomplete
```

Latest runtime state shows:

```text
write_monitor_health.observed_candidate_count = 0
write_monitor_health.enabled = false
write_monitor_health.followed_thread_count = 0
write_monitor_health.raw_write_count = 0
write_monitor_health.filtered_intersecting_write_count = 0
```

This means the last-writer monitor was not effectively observed. Current evidence cannot be interpreted as “arg0 writer missing.” It must be treated as instrumentation incomplete.

## 2. Current Evidence

Latest indexed harness run:

```text
sr_lhs_last_writer_health_20260518_r2
```

Latest artifact:

```text
solve_reports\harness_runs\sr_lhs_last_writer_health_20260518_r2\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

Latest `compare_real_lhs_provenance_audit` evidence:

```text
classification = instrumentation_incomplete
breakpoint_probe_allowed = false
candidate_count = 3
actual_compare.entry = 0x258c
actual_compare.entry_status = confirmed
actual_compare.lhs_side = arg0
actual_compare.flag_side = arg1
actual_compare.arg0_candidate_dependent = true
actual_compare.observed_count = 3
```

Last-writer monitor state:

```text
last_writer_summary.runtime_backed_count = 0
last_writer_summary.retained_write_count = 0
last_writer_summary.intersecting_write_candidate_count = 0
last_writer_summary.write_monitor_health.observed_candidate_count = 0
last_writer_summary.write_monitor_health.enabled = false
last_writer_summary.write_monitor_health.followed_thread_count = 0
last_writer_summary.write_monitor_health.raw_write_count = 0
last_writer_summary.write_monitor_health.ring_capacity = 0
```

Confirmed useful fact:

```text
0x258c compare arg0 is the candidate-dependent real LHS.
0x258c compare arg1 is the flag side.
```

Confirmed blocked fact:

```text
No runtime-backed arg0 last-writer has been identified.
No transform-material producer is connected to compare arg0.
Base64/RC4 breakpoint probe remains blocked.
```

Fact-source inconsistency to fix:

```text
project_state/current_state.json and artifact_index.json point to sr_lhs_last_writer_health_20260518_r2,
but project_state/codex_execution_report.md still describes the earlier pre-health rerun and says the next task is to rerun.
```

## 3. Do Not Do

Do not:

- run Base64/RC4 breakpoint probe
- return to old `sample_solver` blind search
- expand beam, budget, topN, timeout, or frontier iteration
- treat `retained_write_count = 0` as proof that no writer exists
- treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new runtime-backed semantic evidence
- reuse old `[ebp-0x1170]` as the real LHS source
- commit the full `solve_reports` directory
- scan the entire `solve_reports` tree unless indexed artifacts are insufficient
- let `compare_probe` fallback silently mask missing sidecar write-monitor evidence

## 4. Files To Inspect

Inspect only the bounded files required for this repair:

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/compare_real_lhs_provenance_audit.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
project_state/codex_execution_report.md
```

Do not default to full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports`.

## 5. Required Audit

First explain why latest run produced:

```text
observed_candidate_count = 0
enabled = false
followed_thread_count = 0
raw_write_count = 0
ring_capacity = 0
```

Audit these specific paths:

1. Whether `compare_real_lhs_provenance_audit.py` actually invokes the collector with `capture_write_ring = true` for `static_compare_callsite / 0x258c`.
2. Whether the `0x258c` sidecar hook fires for each fixed candidate.
3. Whether `compare_pre_compare_handoff_target_probe.py` emits `write_monitor_health` even when `filteredWrites` is empty.
4. Whether `run_compare_real_lhs_provenance_audit()` falls back to `compare_probe` and thereby obtains compare args without preserving sidecar health.
5. Whether fallback compare args are currently making `actual_compare` look runtime-backed while write-monitor health remains missing.
6. Whether `actual_compare_ready` requires `arg0_candidate_dependent == true`.

Required classification behavior:

```text
static_compare_callsite hook missing
=> instrumentation_incomplete
=> reason: static_compare_callsite_hook_missing

fallback compare args present but write_monitor_health missing
=> instrumentation_incomplete
=> reason: fallback_compare_without_write_monitor_health

write_monitor_health observed for fewer than 3 candidates
=> instrumentation_incomplete

write_monitor_health observed for all 3 candidates but raw_write_count == 0
=> instrumentation_incomplete
=> reason: write_monitor_raw_write_zero

write_monitor_health observed for all 3 candidates and raw_write_count > 0 but no arg0 intersections
=> compare_lhs_runtime_backed_writer_missing

arg0-intersecting writes found but after-preview does not match arg0
=> writer_path_observed_but_unconnected

all 3 candidates have final arg0-connected writer with matching after-preview and candidate-dependent previews
=> last_writer_identified
```

## 6. Implementation Scope

### 6.1 Update report fact source

Update `project_state/codex_execution_report.md` with the latest harness result:

```text
run_name = sr_lhs_last_writer_health_20260518_r2
classification = instrumentation_incomplete
actual_compare.entry = 0x258c
actual_compare.lhs_side = arg0
actual_compare.arg0_candidate_dependent = true
write_monitor_health.observed_candidate_count = 0
write_monitor_health.enabled = false
write_monitor_health.followed_thread_count = 0
write_monitor_health.raw_write_count = 0
write_monitor_health.filtered_intersecting_write_count = 0
breakpoint_probe_allowed = false
next task = fix static_compare_callsite write-monitor observation
```

### 6.2 Fix sidecar health emission

Ensure the `compare_real_lhs_provenance_audit` hook point for `0x258c` is equivalent to:

```json
{
  "name": "static_compare_callsite",
  "module_offset": 9612,
  "instruction": "call 0x5028ac",
  "role": "static_callsite_check",
  "capture_write_ring": true
}
```

At `static_compare_callsite`, emit `write_monitor_health` even when no intersecting writes are found:

```json
{
  "write_monitor_health": {
    "enabled": true,
    "followed_thread_count": 1,
    "raw_write_count": 0,
    "ring_capacity": 4096,
    "eviction_count": 0,
    "descriptor_decode_failures": 0,
    "address_decode_failures": 0,
    "follow_failures": 0,
    "filtered_intersecting_write_count": 0
  },
  "write_ring_buffer": []
}
```

### 6.3 Make fallback explicit

If `compare_probe` fallback is used, record this explicitly:

```text
actual_compare_source = compare_probe_fallback
write_monitor_health_source = missing
instrumentation_gap = fallback_compare_without_write_monitor_health
classification = instrumentation_incomplete
```

Fallback compare args can confirm `arg0`, but cannot prove write-monitor coverage.

### 6.4 Tighten gate

In last-writer mode, require candidate-dependent arg0:

```python
actual_compare_ready = (
    str(actual_compare.get("entry_status", "")) == "confirmed"
    and str(actual_compare.get("lhs_side", "")) == "arg0"
    and bool(actual_compare.get("arg0_candidate_dependent"))
)
```

Keep or add:

```python
if monitor_observed_count < expected_count:
    return "instrumentation_incomplete"
```

### 6.5 Preserve hard stop

After running this sidecar, hard-stop. Do not continue into bridge/search/refine/Base64/RC4 logic in the same run.

## 7. Tests

Add or update focused tests:

```text
1. fallback compare args present but write_monitor_health missing
   => instrumentation_incomplete

2. static_compare_callsite hook missing
   => instrumentation_incomplete

3. write_monitor_health missing for any candidate
   => instrumentation_incomplete

4. write_monitor_health observed for all 3 but raw_write_count == 0
   => instrumentation_incomplete

5. write_monitor_health observed for all 3, raw_write_count > 0, filtered_intersecting_write_count == 0
   => compare_lhs_runtime_backed_writer_missing

6. arg0-intersecting writes found but after_preview does not match arg0
   => writer_path_observed_but_unconnected

7. last_writer_identified only when all 3 candidates have:
   - actual compare arg0 runtime-backed
   - arg0 candidate-dependent
   - final arg0-intersecting writer
   - after_preview matches arg0
   - candidate-dependent final writer previews

8. breakpoint_probe_allowed remains false unless connected + candidate-dependent + transform-material backed.

9. project_state exposes latest write_monitor_health and routes task to instrumentation repair when classification is instrumentation_incomplete.
```

Run:

```bat
python -m py_compile reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py reverse_agent\olly_scripts\compare_real_lhs_provenance_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py

python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py

python -m pytest -q
```

Then run only the bounded harness after the code fix:

```bat
python -m reverse_agent.harness ^
  --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json ^
  --run-name sr_lhs_last_writer_health_fix_20260518_r1 ^
  --reports-dir solve_reports ^
  --analysis-mode Auto ^
  --model-type "Copilot CLI" ^
  --runtime-validation-enabled ^
  --tool-enabled
```

Rebuild project state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r1
python -m reverse_agent.project_state status
```

## 8. Stop Conditions

Stop and report if any of these occur:

```text
A. 0x258c static_compare_callsite hook does not fire for all 3 candidates
   => classification = instrumentation_incomplete
   => next action = fix static callsite hook attachment

B. static_compare_callsite fires but write_monitor_health missing for any candidate
   => classification = instrumentation_incomplete
   => next action = fix health emission / observation normalization

C. write_monitor_health observed for all 3 but raw_write_count == 0
   => classification = instrumentation_incomplete
   => next action = fix Stalker coverage or memory-write descriptor coverage

D. write_monitor_health observed for all 3 and raw_write_count > 0 but no arg0 intersections
   => classification = compare_lhs_runtime_backed_writer_missing
   => next action = inspect ring start time, arg0 range, or writer-before-ring possibility

E. arg0-intersecting writes found but after_preview mismatch
   => classification = writer_path_observed_but_unconnected
   => next action = narrow write window and verify range/sequence

F. final arg0-connected writer is found for all 3 candidates
   => classification = last_writer_identified
   => next action = validate bounded material hook from confirmed compare lhs last writer
```

本轮一句话：先修 `0x258c` sidecar 的 `write_monitor_health` 可观测性，不允许让 `compare_probe` fallback 掩盖 write-monitor 缺失。