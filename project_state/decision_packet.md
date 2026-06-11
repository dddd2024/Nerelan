```json decision_meta
{"schema_version":1,"decision_id":"decision_20260611_classify_doctor_artifact_freshness_v1","round_id":"round_20260611_classify_doctor_artifact_freshness_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Reduce doctor artifact-freshness noise by classifying stale/missing sample artifacts as informational when they are not required for the active engineering round.

Recent accepted rounds still end with `doctor: WARN` because historical sample artifacts are reported as `3 missing, 48 stale artifacts`. That warning is technically true, but it is not actionable for engineering-only rounds that do not rely on current sample evidence. This round should refine doctor/status reporting so artifact freshness remains visible but does not obscure whether the active engineering handoff is healthy.

The goal is not to delete stale artifacts, rebuild sample artifacts, run harness samples, or mark stale evidence as current. The goal is to make doctor output more semantically precise: active-round blockers should remain `WARN`/`FAIL`, while historical sample-artifact staleness should be reported in a separate informational or non-blocking bucket when the active decision is `engineering_branch` and does not claim sample artifact freshness.

## 2. Current Evidence

- The previous round `decision_20260611_repair_harness_case_result_materialization_v1` was accepted. It repaired `HarnessSummary.case_result_paths` materialization checks and stayed within `engineering_branch`.
- Previous final doctor remained `WARN` only because of historical artifact freshness: `3 missing, 48 stale artifacts`.
- Multiple recent accepted engineering rounds had the same residual doctor warning, despite report/pytest/archive/status being healthy.
- `task_packet.json` remains advisory only and still contains old sample-solving context plus stale derived tasks.
- `current_state.json` and `artifact_index.json` include historical sample/harness artifacts. Many are stale and must not be treated as current evidence.
- `negative_results.json` blocks old blind sample search, beam/budget expansion, stale runtime probes, direct Base64/RC4 reruns, and full `solve_reports/` commits.
- Existing project-state capability includes `lint-report`, `status`, `doctor`, artifact freshness checks, report/decision/pytest consistency checks, and round archive classification.
- Existing artifact freshness warning is useful when reverse-solving relies on current artifacts, but too noisy for engineering-only rounds that intentionally do not use sample artifacts.
- This round must preserve the rule: stale or missing artifacts cannot be used as current evidence.
- This round should improve doctor classification/reporting only; it should not change sample evidence, run tools, or alter solver behavior.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not delete, rewrite, or rebuild historical sample artifacts.
- Do not run real harness samples or local training datasets.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not call real Copilot, local LLM, solver, or `run_pipeline`.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not commit full `solve_reports/`.
- Do not mark stale or missing artifacts as current.
- Do not suppress artifact freshness visibility entirely.
- Do not make reverse-solving doctor checks weaker when an active reverse-solving decision depends on current artifact evidence.
- Do not broaden into reverse solving, tool integration, or training dataset mutation.

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
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional if directly relevant:

- README or local project-state docs if they already document `doctor`, artifact freshness, or handoff health semantics.
- The most recent round manifest only for confirming the recurring warning pattern.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Inspect existing `doctor`, `lint_report`, `status_summary`, and artifact freshness implementation before changing behavior.
4. Identify where the `3 missing, 48 stale artifacts` warning is produced.
5. Add a small classification layer that distinguishes:
   - active-round state health problems;
   - report/decision/pytest/archive problems;
   - artifact freshness problems that are relevant to active reverse-solving evidence;
   - historical sample artifact freshness that is visible but non-blocking for engineering-only rounds.
6. Preserve visibility of missing/stale artifact counts in doctor JSON and/or text output.
7. For `engineering_branch` decisions with healthy report/pytest/archive and no current sample-artifact dependency, ensure stale historical artifacts do not by themselves force an otherwise healthy doctor result to `WARN`.
8. For `reverse_solving`, `tool_integration`, and `training_dataset` decisions, preserve conservative behavior: stale/missing artifacts that are needed for current evidence must still produce `WARN` or `FAIL` as appropriate.
9. Add focused tests for doctor classification:
   - engineering round with stale historical artifacts but healthy report/pytest/archive should be non-blocking or informational;
   - reverse-solving round with stale current evidence should still warn/fail;
   - missing current artifact should remain visible and not be silently suppressed;
   - doctor JSON should expose enough fields for audits to see the counts and classification.
10. Update `codex_execution_report.md` using `generated_artifacts` only for current-round outputs and `verified_artifacts` only for pre-existing checked artifacts, if any.
11. Archive this round into `project_state/rounds/round_20260611_classify_doctor_artifact_freshness_v1/`.
12. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
13. Record final `git status --short`.
14. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, sidecar, or model.

## 6. Implementation Scope

Allowed without further justification:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_classify_doctor_artifact_freshness_v1/*`

Allowed only if directly documenting doctor semantics:

- README or an existing project-state documentation file

Disallowed:

- `.codex-skills/`
- `reverse_agent/harness.py` unless a test fixture import needs trivial compatibility; this round should not change harness behavior
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_classify_doctor_artifact_freshness_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `python -m pytest tests/test_project_state.py -q` passes.
- Tests cover artifact freshness classification for engineering and reverse-solving contexts.
- Doctor text and JSON still expose missing/stale artifact counts and classification.
- Engineering-only healthy handoff is not forced to `WARN` solely by historical sample artifact staleness.
- Reverse-solving/tool/training evidence freshness remains conservative.
- `lint-report` is OK after report and pytest are written for this round.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, but if it is `WARN`, the warning must be for a real active-round issue, not solely historical sample artifact freshness.
- Final `doctor --json` is complete valid JSON or saved as artifact with path and sha256.
- `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra/model execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- The repair requires deleting or rebuilding historical sample artifacts.
- The repair would mark stale/missing artifacts as current.
- The repair would hide artifact freshness counts entirely.
- The repair weakens reverse-solving/tool/training freshness checks.
- Tests fail.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `WARN` solely because of historical artifact freshness after the classification change.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving, tool execution, or training dataset mutation.
