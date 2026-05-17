# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

Trace the real runtime outcome of the `call 0x401b50` path in `samplereverse`.

The immediate objective is not to generate new candidates. The objective is to determine where execution goes after entering `0x401b50`, because the latest predecessor audit observed `predecessor_handoff_call` at `module+0x2338`, but did not observe the expected linear return path at `module+0x233d` / `0x2343` / `0x2346`.

Required result: produce a bounded runtime artifact that classifies the `0x401b50` outcome as one of:

- returns to expected linear path
- returns to a non-linear return site
- branches internally to another helper
- throws / unwinds / exception path
- hook failure / instrumentation artifact
- inconclusive, with concrete missing evidence

## 2. Current Evidence

The current active strategy is `CompareAwareSearchStrategy`.

Current best candidates remain unchanged:

- exact2 best:
  - `78d540b49c59077041414141414141`
  - runtime exact wide chars: `2`
  - runtime distance5: `246`
- frontier / exact1 best:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wide chars: `1`
  - runtime distance5: `258`

No current evidence justifies beam expansion or old blind search. The current bottleneck is:

- stage: `compare_lhs_slot_writer_predecessor_audit`
- reason: `handoff_call_does_not_return_to_linear_path`
- confidence: medium

The latest predecessor audit found:

- actual compare entry confirmed at `0x258c`
- compare lhs is `arg0`
- flag side is `arg1`
- lhs preview varies by candidate
- `predecessor_handoff_call` at `0x2338` observed once
- expected successor hooks after `0x2338` were not observed
- `breakpoint_probe_allowed=false`
- next bounded action: trace `0x401b50` return, branch, or exception outcome before any Base64/RC4 probe

`artifact_index.json` also shows that `post_handoff_branch_outcome_audit` is still null, so this is the missing next artifact class rather than a repeated already-completed audit.

## 3. Do Not Do

Do not:

- return to old `sample_solver` blind search
- increase beam, budget, topN, or timeout as the main action
- use `compare_semantics_agree=false` candidates as the primary frontier
- commit the full `solve_reports` directory
- rerun Base64/RC4 breakpoint probing before the `0x401b50` path divergence is explained
- validate `0x253a` as a direct material hook after predecessor evidence rejected it
- treat `0x401b50`, `0x4018cd`, `0x4019e0`, or `0x401be3` as confirmed Base64/RC4 material producers without new semantic evidence
- rerun the same compare return-site audit without using the current classification
- rescan the entire `solve_reports` tree unless a missing artifact lookup forces it

These blocks are already encoded in `negative_results.json`; obey them unless there is a written override reason.

## 4. Files To Inspect

Inspect only the bounded files needed for this task:

1. `reverse_agent/strategies/compare_aware_search.py`
   - Find existing sidecar scheduling patterns.
   - Reuse fixed-candidate audit conventions.
   - Add a new bounded audit only if no existing audit already covers this exact path-outcome classification.

2. `reverse_agent/function_semantics.py`
   - Check whether `0x401b50` metadata can be extended with path outcome evidence.
   - Do not reinterpret it as a material producer without runtime proof.

3. `reverse_agent/project_state.py`
   - Add/index the new artifact key only if a new artifact is introduced.
   - Ensure `current_bottleneck.reason` advances from `handoff_call_does_not_return_to_linear_path` to the new classification.

4. `reverse_agent/olly_scripts/`
   - Inspect the existing runtime sidecar scripts.
   - Implement a narrow `0x401b50` path outcome probe by reusing existing Frida/UIA collector style.

5. `tests/test_compare_aware_search_strategy.py`
   - Add scheduler/classifier/artifact tests.

6. `tests/test_project_state.py`
   - Add project_state indexing/status tests if a new artifact key is added.

Do not inspect full historical solve reports by default.

## 5. Required Audit

Create or reuse a bounded audit tentatively named:

`post_handoff_branch_outcome_audit`

The audit must use the fixed three-candidate set from the current state:

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

For each candidate, capture:

- entry count for `0x401b50`
- return address on entering `0x401b50`
- whether `0x233d` is reached
- whether `0x2343` is reached
- whether `0x2346` is reached
- whether execution reaches known compare entry `0x258c`
- actual return target if different from expected
- EIP / stack preview around return or unwind
- exception / SEH / abnormal termination indicators if available
- candidate-dependent fields only if the hook is runtime-backed

The classifier should distinguish:

- `returns_to_expected_linear_path`
- `returns_to_unexpected_site`
- `branches_or_tailcalls_before_linear_return`
- `exception_or_unwind_path`
- `instrumentation_missed_return`
- `inconclusive`

The audit must not authorize Base64/RC4 probing unless it produces a runtime-backed, instruction-confirmed path that reconnects to the actual compare lhs provenance.

## 6. Implementation Scope

Minimal implementation only.

Acceptable changes:

- Add one narrow runtime probe script if no existing script can capture the `0x401b50` path outcome.
- Add one artifact schema/classifier in `compare_aware_search.py`.
- Add project_state indexing for the new artifact.
- Add negative-cache entries to prevent repeating this probe blindly if it returns `inconclusive` without new hooks.
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
python -m py_compile reverse_agent/olly_scripts/post_handoff_branch_outcome_audit.py
```

Then run:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
python -m pytest -q
```

Then run one bounded harness execution using the existing samplereverse dataset and runtime validation. Use a new run name such as:

```bash
sr_post_handoff_branch_20260517_r1
```

After the harness run:

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_post_handoff_branch_20260517_r1
python -m reverse_agent.project_state status
```

Expected state outcome:

- `missing: []`
- current bottleneck reason changes away from raw `handoff_call_does_not_return_to_linear_path`
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

4. A runtime-backed predecessor source is identified.
   - Do not proceed to Base64/RC4 probe automatically.
   - Report the candidate source and request the next decision.

5. The harness hangs or child runtime stalls.
   - Add/verify timeout guard.
   - Report partial artifact status.
   - Do not manually keep rerunning.

6. Tests fail.
   - Stop after the first concrete failing test group and report the failure.

本轮一句话：不要继续找更好的 candidate，先把 `0x401b50` 的真实控制流去向钉住。
