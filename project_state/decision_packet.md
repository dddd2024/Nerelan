# DECISION_PACKET

## 1. Goal

把当前停滞点从 `pre_rc4_material_probe / material_capture_partial` 推进到一个更窄的动态证据捕获步骤：优先运行或补齐 `base64_rc4_breakpoint_probe` 的 bounded fallback，用断点/静态点钩子捕获 UTF-16LE、Base64、RC4、compare buffer 相关运行时材料。

本轮目标不是增加候选搜索，而是确认运行时材料链路中到底哪一层可以被捕获。

## 2. Current Evidence

- 当前 active strategy 是 `CompareAwareSearchStrategy`，任务是 `Investigate stalled pre_rc4_material_probe path`。`task_packet.json` 标明当前瓶颈为 `pre_rc4_material_probe`，原因是 `material_capture_partial`。
- 当前 best candidates 仍然是：
  - exact2: `78d540b49c59077041414141414141`, `runtime_ci_exact_wchars=2`, `runtime_ci_distance5=246`
  - frontier/exact1: `5a3e7f46ddd474d041414141414141`, `runtime_ci_exact_wchars=1`, `runtime_ci_distance5=258`
  这些候选的 `compare_semantics_agree` 都是 true。
- 最新 `pre_rc4_material_probe` 对 3 个 candidate 做了运行时支持，但 `raw_input / expanded_bytes / utf16le_payload / base64_material / rc4_ksa_key / rc4_encrypted_const / rc4_output / compare_buffer` 全部是 unavailable；offline/runtime agreement 因此都是 unknown。
- `artifact_index.json` 显示 `base64_rc4_breakpoint_probe` 目前还是 null，但 `pre_rc4_material_probe`、`transform_trace_consistency` 等已有最新 artifact。
- `codex_execution_report.md` 明确建议：不要扩大 candidate search；下一步应添加更窄的 material hook，或运行 bounded Base64/RC4 breakpoint fallback。
- 仓库中已经存在 `reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py`，其 hook result keys 包括 `utf16le_payload`、`base64_input`、`base64_output`、`rc4_key`、`rc4_input`、`rc4_output`、`compare_buffer`，说明下一轮优先应审查和接通这个 probe，而不是新写一条大搜索路径。

## 3. Do Not Do

- Do not return to old `sample_solver` blind search.
- Do not only increase beam, budget, topN, timeout, or frontier iteration limits.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports` directory.
- Do not repeat exact2 basin value-pool evaluation with pools:
  `0:78 1:d5/3e/3c 2:40/7f/80 3:b4/8f 4:9c`.
- Do not repeat the fixed H1/H3 8-candidate Base64 boundary contrast set.
- Do not repeat the current 5-candidate transform trace consistency audit unless new runtime material evidence is produced.
- Do not scan entire `solve_reports` by default.

## 4. Files To Inspect

Inspect these first:

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py`
- `reverse_agent/olly_scripts/pre_rc4_material_probe.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`
- `tests/test_tool_runners.py`

Inspect artifact references only as needed:

- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `solve_reports\harness_runs\samplereverse_pre_rc4_material_probe_20260507\reports\tool_artifacts\samplereverse\pre_rc4_material_probe\pre_rc4_material_probe.json`
- `solve_reports\harness_runs\samplereverse_pre_rc4_material_probe_20260507\reports\tool_artifacts\samplereverse\profile_transform_hypothesis_matrix.json`

## 5. Required Audit

Before changing behavior, audit the existing `base64_rc4_breakpoint_probe` path:

1. Confirm whether `CompareAwareSearchStrategy` already has a runner for `BASE64_RC4_BREAKPOINT_PROBE_FILE_NAME`.
2. Confirm whether the runner is invoked after `pre_rc4_material_probe` returns `classification=material_capture_partial`.
3. Confirm the probe receives a valid `--points` JSON file.
4. Validate that static points contain usable entries:
   - `module_offset` is present and integer-like.
   - `hookable=true` for at least one Base64/RC4/compare-relevant point.
   - point kinds are normalized into `utf16le`, `base64`, `rc4_ksa`, `rc4_prga`, `encrypted_const`, or `compare`.
5. Confirm the probe is bounded:
   - candidate set must stay at `BASE64_RC4_BREAKPOINT_PROBE_CANDIDATES`.
   - no beam/search expansion.
   - per-probe timeout remains small.
6. Confirm output schema includes:
   - `candidate_hex`
   - `success`
   - `hook_events`
   - `hook_results`
   - `static_points`
   - `evidence`
   - `error`
7. Confirm project_state can surface:
   - latest base64/rc4 breakpoint artifact path
   - per-material availability
   - whether compare hook fired
   - whether Base64/RC4 material was captured, inferred, unavailable, or failed

## 6. Implementation Scope

Preferred implementation order:

### A. Wire or repair the bounded fallback

If `base64_rc4_breakpoint_probe.py` exists but is not connected:

- Add a strategy runner, for example `run_base64_rc4_breakpoint_probe()`.
- Invoke it only when:
  - sample is `samplereverse`
  - current path reaches `pre_rc4_material_probe`
  - `pre_rc4_material_probe.classification == "material_capture_partial"`
- Reuse the existing 3-candidate bounded set:
  - `78d540b49c59077041414141414141`
  - `78d540b49c59077040414141414141`
  - `5a3e7f46ddd474d041414141414141`

### B. Do not modify ranking/search

This task must not change:

- final selection logic
- candidate promotion
- guided pool beam
- frontier iteration limit
- timeout budget except the local bounded probe timeout
- compare-aware ranking policy

### C. Improve classification only around material capture

Add or refine classifications such as:

- `base64_rc4_material_captured`
- `base64_rc4_material_partial`
- `base64_rc4_static_points_unavailable`
- `base64_rc4_hook_failed`
- `base64_rc4_compare_only`

The classification must distinguish:

- compare hook fired but Base64/RC4 material not captured
- static points missing/unhookable
- Frida/pywinauto execution failure
- successful capture of any UTF-16LE/Base64/RC4 material

### D. Persist compact evidence

Update `project_state` compact output to expose only bounded summary fields, not bulky event dumps:

- artifact path
- candidate_count
- runtime_backed_count or hook_event_count
- hook_results availability table
- first captured material kind
- next_bounded_action

Do not commit full runtime artifacts.

## 7. Tests

Run at minimum:

```powershell
python -m py_compile reverse_agent\olly_scripts\base64_rc4_breakpoint_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

Then run the bounded harness:

```powershell
python -m reverse_agent.harness --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json --run-name samplereverse_base64_rc4_breakpoint_probe_20260507 --reports-dir solve_reports --analysis-mode "Auto" --model-type "Copilot CLI" --copilot-timeout-seconds 300 --ctf-skill-profile compact --case-id samplereverse-exact1-projected-vs-neighbor --no-resume
```

Then rebuild project state:

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_base64_rc4_breakpoint_probe_20260507
python -m reverse_agent.project_state status
```

## 8. Stop Conditions

Stop and report immediately if any of these happens:

1. Any runtime material becomes available or inferred:
   - `utf16le_payload`
   - `base64_input`
   - `base64_output`
   - `rc4_key`
   - `rc4_input`
   - `rc4_output`
   - `compare_buffer`
2. The compare hook fires but all Base64/RC4 hooks remain unavailable.
3. Static points are missing, empty, or all unhookable.
4. Frida/pywinauto target execution fails.
5. Candidate ranking unexpectedly changes without intentional search/ranking modification.
6. A candidate reaches exact3+ or improves beyond current exact2/distance5 baseline.

## Expected Output

Codex should produce:

- updated code if needed
- updated tests
- one bounded harness run
- rebuilt `project_state`
- `project_state/codex_execution_report.md`

The report must explicitly say whether the next bottleneck is:

- static point discovery,
- hook placement,
- runtime GUI triggering,
- compare-only capture,
- or actual transform divergence.
