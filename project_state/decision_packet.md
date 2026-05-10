# DECISION_PACKET

## 1. Goal

Build a reusable Function Semantic Audit Layer for reverse-agent, and use the current `samplereverse` bottleneck as the first validation target.

The immediate challenge-specific goal is to resolve the current stall:

```text
compare_producer_material_confirmation / material_confirmation_inconclusive
```

The project-level architectural goal is to stop accumulating one-off probes and instead introduce a persistent semantic-evidence layer that records what suspicious functions do, how data flows through them, and whether they can justify material hooks.

This round must move the project from:

```text
candidate -> probe -> inconclusive -> another probe
```

to:

```text
candidate
  -> suspicious function discovery
  -> function semantic audit
  -> material pipeline hypothesis
  -> hook readiness gate
  -> runtime capture or solver refinement
```

The first seed functions for the new layer are:

```text
0x4019e0  called at module+0x2320
0x401b50  called at module+0x2338
0x4018cd  called at module+0x234e
0x401be3  called at module+0x2355
```

These are the current producer-window calls that need semantic classification before any further Base64/RC4 breakpoint work.

## 2. Current Evidence

The current active strategy is:

```text
CompareAwareSearchStrategy
```

Current bottleneck:

```text
stage = compare_producer_material_confirmation
reason = material_confirmation_inconclusive
confidence = medium
```

The current best candidate remains:

```text
78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true
```

No exact3+ improvement has been recorded.

The latest material confirmation artifact did not find a valid material hook:

```text
candidate_count = 3
runtime_backed_count = 3
confirmed_material_hook_candidate_count = 0
confirmed_material_hook_candidates = []
material_source_trace = []
breakpoint_probe_allowed = false
```

The project state explicitly says the next bounded action is:

```text
manually inspect producer offsets 0x2320, 0x2338, 0x234e, and 0x2355 before expanding search
```

The instruction table confirms these call sites exist, but they did not produce candidate-dependent evidence in the current probe.

The known transform hypothesis is still:

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

But the project currently lacks enough function-level evidence to prove which function implements which transform stage.

## 3. Do Not Do

Do not:

```text
1. Do not return to old sample_solver blind search.
2. Do not only increase beam, budget, topN, timeout, or frontier iteration.
3. Do not use compare_semantics_agree=false candidates as the primary frontier.
4. Do not commit full solve_reports.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed Base64 boundary contrast set.
7. Do not repeat transform trace consistency audit without new runtime evidence.
8. Do not rerun base64_rc4_breakpoint_probe before confirming a Base64/RC4/UTF-16LE material hook.
9. Do not repeat producer material confirmation unless new instruction-level evidence is added.
10. Do not scan the entire solve_reports tree.
11. Do not build another one-off probe that cannot persist semantic facts into project_state.
```

The important new constraint is item 11: this round must improve the architecture, not merely produce another local diagnostic artifact.

## 4. Files To Inspect

Codex must first inspect the existing implementation to avoid duplicating features.

Required project-state files:

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

Required strategy/state files:

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

Required probe-related files, if present:

```text
reverse_agent/olly_scripts/compare_producer_trace_probe.py
reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
reverse_agent/olly_scripts/*material*
reverse_agent/olly_scripts/*compare*
reverse_agent/olly_scripts/*semantic*
```

Codex must search the repository for existing logic related to:

```text
compare_producer_material_confirmation
compare_producer_trace_probe
material_hook_candidates
breakpoint_probe_allowed
candidate_dependent
instruction_confirmation_table
```

Do not implement a duplicate runner if existing logic can be extended cleanly.

## 5. Required Audit

### A. Architecture audit

Before writing code, Codex must answer:

```text
1. Where are probe artifacts normalized?
2. Where is breakpoint_probe_allowed computed?
3. Where are material_hook_candidates extracted?
4. Where does project_state decide which latest artifact to summarize?
5. Is there already a reusable artifact schema mechanism?
6. Is there already a suitable place for function-level semantic records?
7. Which existing tests protect strategy scheduling and project_state rendering?
```

The architecture audit must identify whether the new semantic layer should be implemented as:

```text
Option A: a new artifact kind: function_semantic_audit
Option B: an extension of compare_producer_material_confirmation
Option C: a general semantic evidence module used by multiple probes
```

Preferred direction: Option C, with Option A as the first artifact type.

### B. Function semantic audit

For each function:

```text
0x4019e0
0x401b50
0x4018cd
0x401be3
```

Codex must produce a compact semantic record:

```json
{
  "function": "0x4019e0",
  "call_sites": ["0x2320"],
  "input_sources": [],
  "output_sinks": [],
  "stack_slots_read": [],
  "stack_slots_written": [],
  "registers_read": [],
  "registers_written": [],
  "memory_writes": [],
  "candidate_dependent": false,
  "semantic_guess": "unknown",
  "confidence": "low",
  "positive_evidence": [],
  "negative_evidence": [],
  "next_required_evidence": []
}
```

Allowed semantic guesses:

```text
utf16le_constructor
base64_transform
rc4_ksa
rc4_prga
rc4_transform
copy_or_handoff
compare_preparer
string_helper
allocator_or_container_helper
unrelated_helper
unknown_but_bounded
```

### C. Dataflow audit

For the producer window around:

```text
0x2312
0x2320
0x2325
0x2338
0x233d
0x2346
0x234e
0x2353
0x2355
0x235a
```

Codex must map:

```text
1. Which function produces eax?
2. Which function consumes eax?
3. Which function writes [ebp-0x1168]?
4. Which function writes [ebp-0x116c]?
5. Which function writes [ebp-0x1170]?
6. Which value eventually becomes esi?
7. Which value becomes compare lhs?
8. Which call, if any, introduces candidate-dependent data?
```

If no candidate-dependent data is found, Codex must explicitly classify whether the current producer window is:

```text
compare-side only
copy/handoff only
too late after material transform
too early before material transform
wrong path
insufficient instrumentation
```

### D. Hook readiness audit

Codex must not set `breakpoint_probe_allowed=true` unless all are true:

```text
1. semantic_guess is one of:
   - utf16le_constructor
   - base64_transform
   - rc4_ksa
   - rc4_prga
   - rc4_transform

2. instruction_confirmed = true

3. hookable = true

4. candidate_dependent = true

5. the function output can be connected to compare lhs or known transform chain
```

If these conditions are not met, the output must keep:

```text
breakpoint_probe_allowed = false
```

and explain the missing evidence.

## 6. Implementation Scope

### Phase 1: Add Function Semantic Audit data model

Add a reusable schema for function semantic records.

Suggested names:

```text
FunctionSemanticRecord
FunctionSemanticAuditArtifact
FunctionSemanticMap
```

The schema must support:

```text
sample
profile
run_name
function address
call sites
input sources
output sinks
register effects
stack effects
memory writes
candidate dependence
semantic guess
confidence
positive evidence
negative evidence
next required evidence
material hook candidate status
```

This should not be hard-coded only for `samplereverse`.

### Phase 2: Add compact artifact type

Add a new artifact kind:

```text
function_semantic_audit
```

or:

```text
compare_producer_callee_semantic_audit
```

Preferred artifact path pattern:

```text
solve_reports/.../tool_artifacts/<sample>/function_semantic_audit/function_semantic_audit.json
```

The artifact must be compact. Do not store full dumps.

Required top-level fields:

```json
{
  "classification": "function_semantic_audit_complete",
  "sample": "samplereverse",
  "profile": "samplereverse",
  "target_functions": [],
  "functions": [],
  "material_pipeline_hypothesis": [],
  "material_hook_candidates": [],
  "breakpoint_probe_allowed": false,
  "next_bounded_action": ""
}
```

Allowed classifications:

```text
function_semantic_audit_complete
material_function_identified
material_hook_ready
compare_side_only
copy_handoff_only
wrong_window
manual_disassembly_required
runtime_instrumentation_required
evidence_insufficient
```

### Phase 3: Seed audit with current four functions

Use the current bottleneck to seed the semantic map:

```text
0x4019e0
0x401b50
0x4018cd
0x401be3
```

Codex must not just list them. It must rank them:

```text
most likely material producer
second likely
likely handoff/copy
likely unrelated/unknown
```

The report must answer:

```text
Which function is most likely responsible for Base64/RC4/UTF-16LE material production?
Why?
What evidence is missing?
What is the next minimum probe?
```

### Phase 4: Integrate semantic map into project_state

Extend `project_state/current_state.json` compact rendering with a new section:

```json
{
  "latest_function_semantic_audit": {
    "artifact": "...",
    "classification": "...",
    "function_count": 4,
    "material_hook_candidate_count": 0,
    "breakpoint_probe_allowed": false,
    "top_semantic_guesses": []
  },
  "function_semantics": {
    "0x4019e0": {
      "semantic_guess": "unknown_but_bounded",
      "confidence": "low",
      "evidence_artifact": "..."
    }
  }
}
```

Also update `artifact_index.json` to index:

```text
function_semantic_audit
```

Do not make `project_state` huge. It should summarize, not embed large artifacts.

### Phase 5: Add semantic negative cache

Extend negative tracking so that the project can remember function-level negative results.

Example:

```json
{
  "direction": "treat 0x401b50 as rc4_prga",
  "scope": "function_semantics",
  "function": "0x401b50",
  "do_not_repeat": true,
  "reason": "no candidate-dependent output observed in bounded audit",
  "evidence_artifact": "...",
  "severity": "soft_block"
}
```

This prevents repeated inspection of the same function with no new evidence.

### Phase 6: Add semantic gate before expensive runtime probes

Centralize the rule:

```text
Base64/RC4 breakpoint probe may run only if Function Semantic Audit identifies
an instruction-confirmed, hookable, candidate-dependent material function or instruction.
```

This should be represented as a gate function, not scattered across probes.

Suggested function names:

```text
is_material_hook_ready(...)
compute_breakpoint_probe_allowed(...)
summarize_function_semantic_gate(...)
```

The rule must remain conservative. False positives are worse than false negatives at this stage.

### Phase 7: Preserve candidate-search behavior

This architecture change must not change:

```text
candidate generation
candidate ranking
final selection
promotion logic
beam
budget
topN
timeout
frontier iteration
```

The current exact2 best must remain stable unless new runtime evidence genuinely improves it.

### Phase 8: Update tests

Add tests for:

```text
1. Function semantic record schema normalization.
2. Function semantic audit artifact compact rendering.
3. project_state includes latest_function_semantic_audit.
4. function_semantics are summarized without bloating current_state.
5. breakpoint_probe_allowed remains false without material hook readiness.
6. breakpoint_probe_allowed becomes true only with:
   - instruction_confirmed
   - hookable
   - candidate_dependent
   - material semantic_guess
7. existing candidate ranking tests remain unchanged.
8. negative_results can store function-level negative evidence.
```

## 7. Tests

Minimum test commands:

```bash
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_project_state.py
```

If Codex adds a new probe or artifact parser:

```bash
python -m py_compile reverse_agent\olly_scripts\<new_or_modified_probe>.py
```

If shared strategy, artifact indexing, or project_state logic changes:

```bash
python -m pytest -q
```

Codex must report whether full test count remains consistent with previous baseline. The earlier report showed full test success at `189 passed`; any regression must be explained and fixed before completion.

## 8. Stop Conditions

Codex must stop and report when any of these happens:

```text
1. Function Semantic Audit Layer is implemented and tested.
2. The four seed functions are classified with evidence.
3. A material-producing function is identified.
4. A material hook becomes instruction-confirmed, hookable, and candidate-dependent.
5. All four functions are classified as non-material or inconclusive.
6. The current producer window is proven to be the wrong observation layer.
7. Further progress requires manual IDA/x64dbg inspection.
8. Further progress would require full binary-wide search.
9. Candidate ranking changes unexpectedly.
10. Any exact3+ or distance5 improvement appears.
```

Final `CODEX_EXECUTION_REPORT` must include:

```text
1. What architecture was added?
2. What files changed?
3. What new artifact schema was introduced?
4. What semantic facts were learned about 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3?
5. Which function is currently most likely to be material-producing?
6. Is base64_rc4_breakpoint_probe still gated?
7. What is the next minimum evidence needed?
8. Did any candidate improve?
9. What tests passed?
```

## Expected Deliverables

Codex should produce:

```text
1. New or updated semantic audit implementation.
2. New compact artifact:
   function_semantic_audit.json
3. Updated project_state/current_state.json rendering.
4. Updated project_state/artifact_index.json indexing.
5. Updated project_state/codex_execution_report.md.
6. Updated or added tests.
7. No full solve_reports commit.
```

## Strategic Interpretation

This is the important project-level change:

```text
Before:
reverse-agent primarily stores candidates and probe outcomes.

After:
reverse-agent stores semantic evidence about the binary:
- functions
- call sites
- dataflow
- material pipeline hypotheses
- hook readiness
- negative semantic conclusions
```

This makes the project more reusable across future reverse challenges.

For `samplereverse`, the short-term target is still to break the current deadlock around Base64/RC4 material discovery. But the correct way to do that now is not another broad search. It is to make the project understand what the suspicious functions do.

One-line instruction to Codex:

```text
Implement a reusable Function Semantic Audit Layer, seed it with 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3, persist the semantic map into project_state, and keep Base64/RC4 breakpoint probing gated until a material hook is instruction-confirmed, hookable, and candidate-dependent.
```
