# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

Trace the last-writer / memory provenance of the actual compare lhs immediately before `0x258c`.

当前 bottleneck 已经从 `handoff_exception_or_unwind` 推进到：

```text
stage: post_handoff_exception_unwind_audit
reason: compare_reached_but_path_unresolved
```

Current `task_packet.json` also states the next task as:

```text
Trace last-writer memory provenance before 0x258c
```

本轮目标不是找新候选，不是扩大搜索，而是解释：

```text
compare 0x258c arg0
<- 由哪个寄存器 / 栈槽 / heap buffer 提供
<- 该值最后一次被谁写入
<- 该 writer 是否 candidate-dependent
<- 该 writer 是否连接到 UTF-16LE/Base64/RC4 transform material
```

## 2. Current Evidence

Active strategy remains:

```text
CompareAwareSearchStrategy
```

Current best remains unchanged:

```text
exact2:
78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true

exact1/frontier:
5a3e7f46ddd474d041414141414141
runtime_ci_exact_wchars = 1
runtime_ci_distance5 = 258
compare_semantics_agree = true
```

Latest `post_handoff_exception_unwind_audit` confirms:

```text
compare entry = 0x258c
lhs side = arg0
flag side = arg1
arg0 candidate-dependent = true
arg1 candidate-dependent = false
```

Known transform mainline remains:

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

However, Base64/RC4 breakpoint probing remains blocked because no runtime-backed connected material producer has been confirmed.

Important prior observations:

- `0x401b50` remains candidate-dependent and hookable, but still blocked by missing transform-chain connection.
- Tentative exception / handler hooks `0x1913`, `0x19bb`, `0x19fe`, and `0x1a30` were not promoted to confirmed runtime evidence.
- The latest classification is no longer an exception/unwind classification; it is a compare-lhs provenance problem.

## 3. Do Not Do

Do not:

- return to old `sample_solver` blind search
- only increase beam, budget, topN, or timeout
- use `compare_semantics_agree=false` candidates as primary frontier
- commit the full `solve_reports` directory
- repeat exact2 basin value-pool evaluation
- repeat H1/H3 fixed 8-candidate prefix8 plus Base64 boundary contrast set
- repeat the current transform trace consistency audit without new runtime evidence
- rerun Base64/RC4 breakpoint probe before confirming an instruction-level material producer
- repeat compare return-site audit without using its classification
- repeat producer material confirmation without adding instruction-level evidence
- continue chasing `0x1913` / `0x19bb` / `0x19fe` / `0x1a30` as confirmed exception/handler facts
- treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence
- scan the entire `solve_reports` tree unless an indexed artifact lookup is insufficient

## 4. Files To Inspect

Codex should inspect only the bounded files required for this task:

1. `reverse_agent/strategies/compare_aware_search.py`
   - Check existing sidecar scheduling and artifact naming.
   - Reuse fixed-candidate conventions.
   - Add a narrow last-writer provenance audit only if no existing sidecar already provides this.

2. `reverse_agent/olly_scripts/`
   - Reuse the existing Frida/UIA collector style.
   - Add only a thin runtime entry if needed.

3. `reverse_agent/project_state.py`
   - Index the new artifact if a new artifact kind is introduced.
   - Ensure the bottleneck advances away from `post_handoff_exception_unwind_audit / compare_reached_but_path_unresolved`.

4. `tests/test_compare_aware_search_strategy.py`
   - Add scheduler, classifier, fixed-candidate, no-expansion, and gating tests.

5. `tests/test_project_state.py`
   - Add project_state indexing and task routing coverage.

Suggested artifact name:

```text
compare_arg0_last_writer_memory_provenance_audit
```

Acceptable existing-name alternative:

```text
compare_real_lhs_provenance_audit
```

`latest_compare_real_lhs_provenance_audit` is currently empty, so it may be the cleanest existing continuation point.

## 5. Required Audit

The audit must work backwards from actual compare arg capture.

Use the fixed three candidates:

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

For each candidate, capture at minimum:

```text
0x258c compare entry
arg0 pointer
arg0 preview_hex
arg1 pointer
arg1 preview_hex
0x258b pre-compare push esi
esi value / preview
0x2559 post-handoff lhs reload
[ebp-0x1170] value / preview
0x253a lhs slot store
eax value / preview
nearby memory writes to arg0 buffer before 0x258c
last observed module offset before compare
```

The audit should classify the result as one of:

```text
arg0_last_writer_identified
arg0_last_writer_is_copy_only
arg0_writer_window_rejected
arg0_writer_unobserved_but_compare_confirmed
instrumentation_missing_memory_write
inconclusive
```

Classification evidence gates:

```text
arg0_last_writer_identified:
  must observe 0x258c compare args
  must identify a writer/copy point whose pointer or preview matches arg0
  must be runtime-backed for all 3 candidates

arg0_last_writer_is_copy_only:
  must identify writer to arg0
  writer/copy evidence is runtime-backed
  writer material does not yet match UTF-16LE/Base64/RC4 model

arg0_writer_window_rejected:
  must observe checked hooks
  none connects to compare arg0 pointer or preview

arg0_writer_unobserved_but_compare_confirmed:
  must observe 0x258c arg0/arg1
  no writer hook fires in the bounded checked window

instrumentation_missing_memory_write:
  must show compare arg0 is valid and candidate-dependent
  current hook style cannot observe the write source

inconclusive:
  insufficient runtime-backed observations
```

The artifact must explicitly report:

- whether `arg0` remains candidate-dependent
- whether a concrete writer was found
- whether the writer connects to compare `arg0`
- whether the writer is likely copy-only or transform-material
- whether Base64/RC4 breakpoint probe remains blocked
- the next bounded action

## 6. Implementation Scope

Allowed:

- Add one bounded sidecar for `0x258c` arg0 last-writer provenance.
- Reuse existing runtime collector logic where possible.
- Add hook points around:
  - `0x258b`
  - `0x258c`
  - `0x2559`
  - `0x253a`
  - selected earlier writer candidates only when justified by current artifacts
- Add project_state indexing for the new artifact.
- Add negative-cache entries to prevent repeating this audit if it rejects the checked window without new evidence.
- Add tests for fixed candidates, no search expansion, compare-arg requirements, breakpoint blocking, and state routing.

Not allowed:

- candidate generation changes
- ranking changes
- optimizer changes
- beam / budget / topN / timeout expansion
- Base64/RC4 breakpoint probe
- broad disassembly sweep
- full `solve_reports` commit
- claiming a material producer without runtime-backed writer evidence

## 7. Tests

Run at minimum:

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py
```

If a new runtime script is added, run the corresponding compile check, for example:

```bash
python -m py_compile reverse_agent/olly_scripts/compare_arg0_last_writer_memory_provenance_audit.py
```

or:

```bash
python -m py_compile reverse_agent/olly_scripts/compare_real_lhs_provenance_audit.py
```

Then run:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
python -m pytest -q
```

Suggested harness run name:

```text
sr_arg0_last_writer_20260517_r1
```

Suggested harness command on Windows:

```bat
python -m reverse_agent.harness ^
  --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json ^
  --run-name sr_arg0_last_writer_20260517_r1 ^
  --reports-dir solve_reports ^
  --analysis-mode Auto ^
  --model-type "Copilot CLI" ^
  --runtime-validation-enabled ^
  --tool-enabled
```

After the harness run:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_last_writer_20260517_r1
python -m reverse_agent.project_state status
```

Expected state:

```text
missing: []
current_bottleneck.stage != post_handoff_exception_unwind_audit
current_bottleneck.reason != compare_reached_but_path_unresolved
```

Acceptable next reasons include:

```text
arg0_last_writer_identified
arg0_last_writer_is_copy_only
arg0_writer_window_rejected
arg0_writer_unobserved_but_compare_confirmed
instrumentation_missing_memory_write
```

## 8. Stop Conditions

Stop immediately and report if:

1. `0x258c` compare entry cannot be observed.
2. compare args cannot be captured.
3. `arg0` no longer appears candidate-dependent.
4. writer hooks fire but none can be connected to arg0 pointer or preview.
5. current hook system cannot observe memory writes before `0x258c`.
6. any result suggests running Base64/RC4 probe without connected producer evidence.
7. tests fail.
8. harness hangs or child runtime stalls.

本轮一句话：不要继续追异常路径；现在 compare 已经到了，下一步必须找 `0x258c arg0` 的最后写入者。
