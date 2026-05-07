# DECISION_PACKET.md

## 1. Goal

Resolve the current `helper_arg_slice_partial` bottleneck for `samplereverse`.

The immediate goal is to determine why `compare_handoff_slice_probe` can capture:

- `handoff_helper_enter`
- `handoff_helper_return`
- `lhs_slot`
- `compare_lhs_buffer`

but cannot close the dataflow relation between helper return / `[ebp-0x1170]` / `esi` / compare lhs.

This round must not generate more search candidates. It must either:

1. correct the missed post-helper hook anchors,
2. prove the compare argument capture is using the wrong stack interpretation,
3. prove helper `0x401b50` is not the missing handoff point,
4. or produce a more precise bounded next probe target.

Expected output:

- A new bounded diagnostic artifact, preferably named:
  - `compare_handoff_return_site_probe.json`
  - or `compare_call_arg_audit.json`
- Updated `project_state/*`
- New `CODEX_EXECUTION_REPORT.md`
- No candidate promotion and no search-budget expansion

## 2. Current Evidence

Current active strategy remains `CompareAwareSearchStrategy`.

Known transform chain remains:

`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`

Current mainline is still `L15(prefix8)`.

Current best exact2 candidate:

- `candidate_hex`: `78d540b49c59077041414141414141`
- `candidate_prefix`: `78d540b49c590770`
- `compare_semantics_agree`: `true`
- `runtime_ci_exact_wchars`: `2`
- `runtime_ci_distance5`: `246`

Current frontier candidate:

- `candidate_hex`: `5a3e7f46ddd474d041414141414141`
- `candidate_prefix`: `5a3e7f46ddd474d0`
- `compare_semantics_agree`: `true`
- `runtime_ci_exact_wchars`: `1`
- `runtime_ci_distance5`: `258`

Latest bottleneck:

- `stage`: `compare_handoff_slice_probe`
- `reason`: `helper_arg_slice_partial`
- `confidence`: `medium`

The previous Codex round implemented `compare_handoff_slice_probe.py` and ran the bounded harness successfully. Unit tests passed: `174 passed`. The harness completed 1 case with 0 errors.

Important previous findings:

- Static anchor remained valid:
  - compare call RVA: `0x258c`
  - helper RVA: `0x1028ac`
  - helper classification: `case_insensitive_wchar_compare`
- Runtime helper enter/return was captured for all 3 diagnostic candidates.
- `post_handoff_lhs_reload`, `post_handoff_after_reload`, and `pre_compare_push_esi` were unavailable.
- Cross-candidate relation counts from helper return to compare lhs were all 0.
- Best runtime candidate did not improve.

Therefore the next bounded action is:

> Audit the actual helper return site and compare-call argument capture before any candidate refinement.

## 3. Do Not Do

Do not:

1. Return to old `sample_solver` blind search.
2. Increase beam, budget, topN, timeout, or frontier iteration limits.
3. Use `compare_semantics_agree=false` candidates as the primary frontier.
4. Commit the full `solve_reports` directory.
5. Repeat exact2 basin value-pool evaluation.
6. Repeat the fixed H1/H3 8-candidate prefix8 boundary contrast set.
7. Repeat the same 5-candidate transform trace consistency audit without new runtime evidence.
8. Expand candidate search while `helper_arg_slice_partial` remains unresolved.
9. Repeat the exact same `compare_handoff_slice_probe` hook set without changing the evidence source.
10. Scan the full `solve_reports` tree.

## 4. Files To Inspect

Primary code files:

1. `reverse_agent/olly_scripts/compare_handoff_slice_probe.py`
2. `reverse_agent/strategies/compare_aware_search.py`
3. `tests/test_compare_aware_search_strategy.py`
4. `tests/test_tool_runners.py`
5. `tests/test_project_state.py`

Project state files:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`

Targeted artifacts only:

1. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\reports\tool_artifacts\samplereverse\compare_handoff_slice_probe\compare_handoff_slice_probe.json`
2. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\reports\tool_artifacts\samplereverse\compare_handoff_slice_probe\candidate_1\compare_handoff_slice_probe.json`
3. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\reports\tool_artifacts\samplereverse\compare_handoff_slice_probe\candidate_2\compare_handoff_slice_probe.json`
4. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\reports\tool_artifacts\samplereverse\compare_handoff_slice_probe\candidate_3\compare_handoff_slice_probe.json`
5. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\summary.json`
6. `solve_reports\harness_runs\samplereverse_helper_arg_slice_probe_20260505\run_manifest.json`

Only inspect other artifacts if these files directly reference them.

## 5. Required Audit

Perform a narrow audit in three parts.

### A. Hook-anchor audit

Inspect the current hook points in `compare_handoff_slice_probe.py`:

- `0x253a` / `pre_lhs_slot_store`
- `0x2554` / `pre_handoff_call`
- `0x1b50` / `handoff_helper_enter`
- `0x2559` / `post_handoff_lhs_reload`
- `0x255c` / `post_handoff_after_reload`
- `0x258b` / `pre_compare_push_esi`
- `0x258c` / `wide_flag_prefix_compare`

For each missing hook, determine whether the cause is:

1. wrong RVA,
2. instruction-boundary mismatch,
3. address is inside a multi-byte instruction,
4. conditional path not taken,
5. control flow skips the anchor,
6. Frida cannot attach to that instruction,
7. or the static disassembly assumption is stale.

Required output:

- actual bytes around `module+0x253a` through `module+0x258c`
- instruction boundary list
- expected hook address vs instruction-confirmed address
- whether each unavailable hook was invalid, skipped, or simply not hit

### B. Helper return-site audit

The previous script captures helper enter/return, but the caller-side reload path is still unresolved.

Add a bounded return-site diagnostic that records:

1. helper enter return address,
2. return address module offset,
3. caller context immediately after helper return if capturable,
4. `eax`,
5. `esi`,
6. `[ebp-0x1170]`,
7. memory preview at `eax`,
8. memory preview at `esi`,
9. memory preview at `[ebp-0x1170]`,
10. whether the return address equals `module+0x2559` or another address.

If direct static hooks at `0x2559` / `0x255c` still miss, derive the return site from the helper call stack at runtime rather than trusting the hardcoded offsets.

### C. Compare-call argument audit

At `module+0x258c`, verify the actual stack layout at the compare call.

The current script assumes:

```text
push 5
push 0x551c4c
push esi
call 0x5028ac
```

Therefore, at the call instruction:

```text
[esp+0x00] = lhs pointer
[esp+0x04] = rhs pointer
[esp+0x08] = count
```

This must be verified against runtime data.

For each of the 3 diagnostic candidates, record:

- `esp`
- `[esp+0x00]`
- `[esp+0x04]`
- `[esp+0x08]`
- preview at `[esp+0x00]`
- preview at `[esp+0x04]`
- decoded UTF-16LE preview if valid
- whether either side equals or points to `flag{`
- whether either side is candidate-dependent
- whether either side matches helper-return / `eax` / `esi` / `[ebp-0x1170]`

Important: if `compare_lhs_buffer` is candidate-independent, Codex must not assume it is the transformed candidate buffer. It must test whether lhs/rhs are swapped, whether the hook is reading the target buffer, or whether `esi` is not the compare lhs at this point.

## 6. Implementation Scope

Allowed:

1. Add one bounded diagnostic script, for example:
   - `reverse_agent/olly_scripts/compare_handoff_return_site_probe.py`
   - or `reverse_agent/olly_scripts/compare_call_arg_audit.py`

2. Add a strategy runner, for example:
   - `run_compare_handoff_return_site_probe()`
   - or `run_compare_call_arg_audit()`

3. Use the same 3 candidates only:
   - `78d540b49c59077041414141414141`
   - `78d540b49c59077040414141414141`
   - `5a3e7f46ddd474d041414141414141`

4. Emit a compact artifact with:
   - static instruction boundary audit
   - runtime helper return-site data
   - compare-call argument table
   - cross-candidate relation table
   - classification
   - next bounded action

5. Update project state builder to index the new artifact.

6. Add tests for:
   - schema stability
   - no candidate promotion
   - no budget expansion
   - project_state indexing
   - classification handling

Not allowed:

1. Do not modify ranking.
2. Do not promote candidates.
3. Do not increase search budgets.
4. Do not introduce a generic broad dynamic tracer.
5. Do not commit full runtime report directories.
6. Do not continue to candidate refinement unless the compare argument path is clarified.

## 7. Tests

Run:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

Then run the bounded harness case with a new run name:

```powershell
python -m reverse_agent.harness ^
  --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json ^
  --run-name samplereverse_compare_return_site_probe_20260507 ^
  --reports-dir solve_reports ^
  --analysis-mode "Auto" ^
  --model-type "Copilot CLI" ^
  --copilot-timeout-seconds 300 ^
  --ctf-skill-profile compact ^
  --case-id samplereverse-exact1-projected-vs-neighbor ^
  --no-resume
```

Then rebuild project state:

```powershell
python -m reverse_agent.project_state build ^
  --reports-dir solve_reports ^
  --sample samplereverse ^
  --run-name samplereverse_compare_return_site_probe_20260507

python -m reverse_agent.project_state status
```

Expected result:

- Unit tests pass.
- Harness completes 1 case with 0 errors.
- New artifact is indexed.
- `current_state.json` no longer merely says `helper_arg_slice_partial` unless the new evidence still cannot identify the dataflow.
- `codex_execution_report.md` explains the next bounded branch.

## 8. Stop Conditions

Stop successfully if one of these is true:

1. The helper return site is identified and explains why `0x2559` / `0x255c` / `0x258b` did not fire.
2. The compare-call argument order is confirmed and the true candidate-dependent compare side is identified.
3. The compare-call argument order is disproven and corrected.
4. The relation between helper return, `[ebp-0x1170]`, `esi`, and compare lhs is closed.
5. Helper `0x401b50` is proven not to be the relevant handoff point, and the report identifies a narrower next probe target.

Stop and report blockage if:

1. The three candidate runs produce nondeterministic hook behavior.
2. The return address cannot be captured reliably.
3. The compare call cannot be reached reliably.
4. The only possible next action appears to be broader candidate search.
5. Required artifacts are missing.

Final report must include:

1. What was inspected.
2. What changed.
3. What did not change.
4. Hook availability table.
5. Compare-call stack argument table.
6. Cross-candidate relation table.
7. Final classification:
   - `return_site_confirmed`
   - `wrong_reload_anchor`
   - `compare_args_swapped`
   - `wrong_compare_arg_capture`
   - `wrong_helper_assumption`
   - `needs_pre_rc4_base64_probe`
   - `helper_arg_slice_still_partial`
8. Recommended next bounded action.
