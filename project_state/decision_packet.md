```json decision_meta
{"schema_version":1,"decision_id":"decision_20260611_repair_harness_case_result_materialization_v1","round_id":"round_20260611_repair_harness_case_result_materialization_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair and test harness case-result materialization invariants.

`task_packet.json` has repeatedly suggested `repair_harness_case_result_materialization`, but that task is advisory only. This round should address the underlying engineering issue in a bounded way: after any harness run, every path listed in `HarnessSummary.case_result_paths` must correspond to an existing, readable JSON case-result file, and each listed file must match the corresponding case id. This should be validated for normal completion, error completion, resume/cache paths, and bounded failure paths that still produce a summary.

This is an `engineering_branch` harness correctness round. It must not run real samples, solvers, model calls, runtime probes, debuggers, IDA, Ghidra, OllyDbg, x64dbg, Frida, pywinauto, or full harness runs against live training data. Use unit tests and monkeypatching/stubs only.

## 2. Current Evidence

- The previous round `decision_20260611_add_verified_artifacts_report_schema_v1` was accepted. It added optional `verified_artifacts` support and validated report/pytest/archive/doctor consistency.
- `task_packet.json` remains advisory and still contains old sample-solving context plus derived task `repair_harness_case_result_materialization`.
- `current_state.json` and `artifact_index.json` still contain many stale sample/harness artifacts. These must not be treated as current evidence for this engineering repair.
- `negative_results.json` blocks old blind sample solver search, beam/budget expansion, stale runtime probes, full `solve_reports/` commits, and repeated reverse-solving probes.
- `.codex-skills/registry.json` confirms `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.
- Existing harness capability: `reverse_agent/harness.py` defines `HarnessCase`, `HarnessCaseResult`, `HarnessSummary`, `run_harness`, `compare_harness_runs`, `_load_compare_case_results`, and resume-policy handling.
- Existing harness behavior: `run_harness` creates `run_dir`, `reports`, and `case_results`, writes each case result as `case_results/<sanitized_case_id>.json`, writes `summary.json`, writes `summary.md`, and records `summary_path` / `summary_digest` in `run_manifest.json`.
- Existing summary behavior: `_build_summary` currently computes `case_result_paths` from the result case ids rather than explicitly verifying that those files exist and parse.
- Existing compare behavior: `compare_harness_runs` loads case results from `case_results/*.json`, so missing or malformed case-result files make compare output incomplete.
- Existing tool interfaces include harness CLI flags for IDA/Olly/tool/runtime options, but this round must not execute those tools.
- This round should improve existing harness invariants and tests, not add a new orchestration layer.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not run real harness samples or local training datasets.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not call real Copilot, local LLM, solver, or `run_pipeline` without monkeypatching/stubbing.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not commit full `solve_reports/`.
- Do not change sample metadata, candidate files, or training dataset state.
- Do not broaden into reverse solving or tool integration.
- Do not rewrite the whole harness.
- Do not break existing resume-policy semantics.
- Do not make summary paths point to files that do not exist.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/harness.py`
- `tests/test_harness_resume.py`
- `tests/test_harness_compare.py`
- `tests/test_harness_resource_budget.py`
- `tests/test_project_state.py`

Optional if directly relevant:

- Existing previous round artifacts under `project_state/rounds/` that document harness case-result gaps, but only bounded single-round references. Do not read full history.
- README or local harness docs if they already document `summary.json`, `case_results`, or compare behavior.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Inspect existing `run_harness`, `_build_summary`, `_load_case_result`, `_load_compare_case_results`, and compare behavior before changing code.
4. Identify whether `summary.case_result_paths` can point to missing or malformed files under any existing code path, including resume/cache and error cases.
5. Add or strengthen a harness invariant: at final summary-write time, every `case_result_paths` entry must refer to an existing case result JSON file produced or loaded for that run.
6. Ensure the JSON content for each listed case result contains the matching `case_id`.
7. Preserve resume behavior: cached terminal cases should remain resumable and should still appear in `summary.case_result_paths`.
8. Preserve error behavior: if an individual case errors, its error case-result JSON must be written and included in summary.
9. Preserve fail-fast behavior: if fail-fast raises after a case error, the partial summary/manifest should not claim paths that were not materialized.
10. Preserve compare behavior: `compare_harness_runs` should continue to compare only readable case-result JSON files, but tests should catch missing summary-listed case results before compare hides the gap.
11. Add focused unit tests using monkeypatch/stubbed `run_pipeline`; do not invoke real models or tools.
12. Update current `codex_execution_report.md` using `generated_artifacts` only for current-round outputs and `verified_artifacts` only for pre-existing checked artifacts, if any.
13. Archive this round into `project_state/rounds/round_20260611_repair_harness_case_result_materialization_v1/`.
14. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
15. Record final `git status --short`.
16. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `reverse_agent/harness.py`
- `tests/test_harness_resume.py`
- `tests/test_harness_compare.py`
- `tests/test_harness_resource_budget.py`
- `tests/test_project_state.py` only if project_state tests need minor fixture compatibility with harness output changes
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_repair_harness_case_result_materialization_v1/*`

Allowed only if directly documenting the behavior:

- README or an existing harness documentation file, if it already documents `case_results` or `summary.case_result_paths`

Disallowed:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay unrelated to report validation
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py tests/test_project_state.py -q
python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_repair_harness_case_result_materialization_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- Harness tests use monkeypatch/stubbed pipeline behavior and do not call real models, tools, solvers, runtime probes, debuggers, IDA, Ghidra, Frida, pywinauto, or sample binaries.
- Normal-completion test proves every `summary.case_result_paths` entry exists, is valid JSON, and matches its `case_id`.
- Error-case test proves an errored case writes a case-result JSON and summary includes it.
- Resume/cache test proves cached case results remain included and readable.
- Fail-fast/partial test proves summary/manifest do not claim nonexistent case-result paths.
- Compare test proves missing or malformed case-result materialization gaps are caught by the new invariant/test rather than silently hidden by compare loading.
- Existing resume-policy tests still pass.
- Existing compare tests still pass.
- `lint-report` is OK after report and pytest are written for this round.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` is complete valid JSON or saved as artifact with path and sha256.
- `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- The repair requires real sample execution or real `run_pipeline` execution.
- The repair requires solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- Adding the invariant would break existing valid resume behavior.
- Tests fail.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving, tool execution, or training dataset mutation.
