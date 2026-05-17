# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

Trace the `0x401b50` post-handoff exception/unwind path and identify the real branch/call outcome that connects candidate-dependent material to the actual compare lhs.

本轮目标不是生成新候选，也不是扩大 beam/budget，而是把当前瓶颈 `post_handoff_branch_outcome_audit / handoff_exception_or_unwind` 变成更明确的运行时分类：

- `normal_return_to_compare_path`
- `exception_dispatch_to_compare_path`
- `seh_unwind_to_compare_path`
- `alternate_return_to_compare_path`
- `compare_reached_but_path_unresolved`
- `compare_not_reached`
- `inconclusive`

## 2. Current Evidence

- Active strategy: `CompareAwareSearchStrategy`.
- Profile/sample: `samplereverse`.
- Current task: `Trace 0x401b50 exception or unwind handler`.
- Current bottleneck:
  - stage: `post_handoff_branch_outcome_audit`
  - reason: `handoff_exception_or_unwind`
  - confidence: `medium`
- Current best candidates:
  - exact2: `78d540b49c59077041414141414141`, runtime exact2 / distance5 `246`, `compare_semantics_agree=true`
  - frontier/exact1: `5a3e7f46ddd474d041414141414141`, runtime exact1 / distance5 `258`, `compare_semantics_agree=true`
- Known transform mainline remains:
  - `input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`
- Function semantics currently mark `0x401b50` as:
  - `candidate_dependent=true`
  - `hookable=true`
  - `semantic_guess=copy_or_handoff`
  - still blocked by `missing_transform_chain_connection`
- Latest actual compare evidence anchors compare at `0x258c`:
  - actual compare `arg0` is candidate-dependent
  - actual compare `arg1` is the stable flag-side constant
  - lhs preview varies by candidate
- Latest indexed harness run:
  - `solve_reports\harness_runs\sr_401b50_outcome_20260517_r1`
- Core latest artifact class:
  - `post_handoff_branch_outcome_audit`
- Important limitation:
  - Do not assume uncommitted full `solve_reports` contents. Use committed `project_state` summaries and indexed artifacts as the fact source.

## 3. Do Not Do

Do not:

- return to old `sample_solver` blind search
- only increase beam, budget, topN, or timeout
- use `compare_semantics_agree=false` candidates as primary frontier
- commit the full `solve_reports` directory
- repeat exact2 basin value-pool evaluation
- repeat H1/H3 fixed 8-candidate prefix8 plus Base64 boundary contrast set
- repeat the current transform trace consistency audit without new runtime evidence
- rerun Base64/RC4 breakpoint probe before confirming an instruction-level Base64/RC4 or material-construction hook
- repeat compare return-site audit without using its classification
- repeat producer material confirmation without adding instruction-level evidence
- reuse `0x233d` / `0x2346` as material-hook breakpoints after the post-handoff audit rejected them
- probe downstream `0x234e` / `0x2355` Base64/RC4 hooks before branch outcome reaches them
- treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence
- scan the entire `solve_reports` tree unless a missing artifact lookup explicitly forces it

## 4. Files To Inspect

Inspect only the bounded files needed for this task:

1. `reverse_agent/strategies/compare_aware_search.py`
   - Find existing sidecar scheduling patterns.
   - Reuse fixed-candidate audit conventions.
   - Add or refine a bounded sidecar only if no existing audit already covers this exact exception/unwind outcome classification.

2. `reverse_agent/function_semantics.py`
   - Check whether `0x401b50` metadata can be extended with path outcome evidence.
   - Do not reinterpret it as a material producer without runtime proof.

3. `reverse_agent/project_state.py`
   - Index `latest_post_handoff_exception_unwind_audit` if a new artifact is introduced.
   - Ensure `current_bottleneck.reason` advances from `handoff_exception_or_unwind` to a more concrete runtime classification.

4. `reverse_agent/olly_scripts/`
   - Inspect existing runtime sidecar scripts.
   - Implement a narrow `0x401b50` path outcome probe by reusing existing Frida/UIA collector style.

5. `tests/test_compare_aware_search_strategy.py`
   - Add scheduler/classifier/artifact tests.

6. `tests/test_project_state.py`
   - Add project_state indexing/status tests if a new artifact key is added.

Do not inspect full historical solve reports by default.

## 5. Required Audit

Create or refine a bounded sidecar tentatively named:

`post_handoff_exception_unwind_audit`

It should consume the current `post_handoff_branch_outcome_audit / handoff_exception_or_unwind` bottleneck and use the fixed candidate set already present in current state. Do not expand candidate search.

For each fixed candidate, capture:

- `0x401b50` enter count
- `0x401b50` leave/return count if observable
- return address on entering `0x401b50`
- actual return target if it differs from expected post-handoff site
- whether expected post-handoff linear sites are reached
- whether exception dispatcher / SEH handler / unwind-like path / alternate return path is observed
- whether compare entry `0x258c` is reached
- actual compare `arg0` pointer/value preview
- actual compare `arg1` pointer/value preview
- whether compare lhs material remains candidate-dependent
- last observed module offset before compare
- stack/register preview around the divergence point

The classifier should distinguish:

- `normal_return_to_compare_path`
- `exception_dispatch_to_compare_path`
- `seh_unwind_to_compare_path`
- `alternate_return_to_compare_path`
- `compare_reached_but_path_unresolved`
- `compare_not_reached`
- `instrumentation_missed_return`
- `inconclusive`

Critical classifier rule:

Actual compare confirmation must require observed compare entry and argument capture. Do not classify success merely because upstream hooks fired. A previous implementation class already required this correction, so preserve that discipline.

The audit must not authorize Base64/RC4 probing unless it proves all of the following with runtime-backed evidence:

1. actual compare lhs side confirmed
2. connected producer confirmed
3. candidate-dependent transform material confirmed

## 6. Implementation Scope

Minimal implementation only.

Acceptable changes:

- Add one narrow runtime probe script if no existing script can capture the `0x401b50` exception/unwind outcome.
- Add one artifact schema/classifier in `compare_aware_search.py`.
- Add sidecar scheduling only for the current `handoff_exception_or_unwind` bottleneck.
- Add project_state indexing for the new artifact.
- Add negative-cache entries to prevent blindly repeating this probe if it returns `inconclusive` without new hook evidence.
- Add tests for:
  - no candidate expansion
  - fixed candidate set
  - breakpoint probe remains blocked
  - classifier transitions
  - project_state bottleneck update

Not acceptable:

- candidate generation changes
- scoring/ranking changes
- optimizer changes
- broad disassembly sweep
- full `solve_reports` commit
- Base64/RC4 breakpoint probe run

## 7. Tests

Run at minimum:

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py
```

If a new runtime script is added:

```bash
python -m py_compile reverse_agent/olly_scripts/post_handoff_exception_unwind_audit.py
```

Then run:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
python -m pytest -q
```

Then run one bounded harness execution using the existing `samplereverse` dataset and runtime validation. Suggested run name:

```bash
sr_401b50_exception_unwind_20260517_r1
```

Suggested harness command:

```bash
python -m reverse_agent.harness \
  --dataset solve_reports/samplereverse_compare_producer_backtrace_20260508_dataset.json \
  --run-name sr_401b50_exception_unwind_20260517_r1 \
  --reports-dir solve_reports \
  --analysis-mode Auto \
  --model-type "Copilot CLI" \
  --runtime-validation-enabled \
  --tool-enabled
```

After the harness run:

```bash
python -m reverse_agent.project_state build \
  --reports-dir solve_reports \
  --sample samplereverse \
  --run-name sr_401b50_exception_unwind_20260517_r1

python -m reverse_agent.project_state status
```

Expected state outcome:

- `missing: []`
- current bottleneck reason changes away from raw `handoff_exception_or_unwind`
- new artifact appears in `artifact_index.json`
- `breakpoint_probe_allowed` remains false unless a real connected material source is proven

## 8. Stop Conditions

Stop immediately and report if any of the following happens:

1. `0x401b50` returns to a non-expected address.
   - Report the actual target and supporting register/stack evidence.

2. `0x401b50` does not return normally.
   - Report exception/unwind evidence.

3. Expected hooks are not hit but compare still occurs.
   - Report whether this is likely instrumentation miss, wrong module base, wrong offset, or control-flow divergence.

4. A runtime-backed predecessor/source path is identified.
   - Do not proceed to Base64/RC4 probe automatically.
   - Report the candidate source and request the next decision.

5. The harness hangs or child runtime stalls.
   - Add or verify timeout guard.
   - Report partial artifact status.
   - Do not manually keep rerunning.

6. Tests fail.
   - Stop after the first concrete failing test group and report the failure.

本轮一句话：不要继续找更好的 candidate，先把 `0x401b50` 后的真实控制流去向钉住。
