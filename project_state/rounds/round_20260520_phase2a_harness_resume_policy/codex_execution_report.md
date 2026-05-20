```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_phase2a_harness_resume_policy_20260520",
  "round_id": "round_20260520_phase2a_harness_resume_policy",
  "based_on_decision_id": "decision_phase2a_harness_resume_policy_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/harness.py",
    "tests/test_harness_resume.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\harness.py",
    "python -m pytest -q tests\\test_harness.py",
    "python -m pytest -q tests\\test_harness_resume.py",
    "python -m pytest -q",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state lint-handoff --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2a_harness_resume_policy"
  ],
  "generated_artifacts": [
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/round_manifest.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/artifact_index.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/current_state.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/negative_results.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/model_gate.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/task_packet.json",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/decision_packet.md",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/codex_execution_report.md",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/pytest_result.txt",
    "project_state/rounds/round_20260520_phase2a_harness_resume_policy/git_diff.patch"
  ],
  "next_suggested_task": "Have GPT audit Phase 2A harness resume semantics before authorizing any Phase 2B/2C/2D engineering task or samplereverse runtime work."
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-20 Phase 2A harness resume policy

This pass implements the approved Phase 2A engineering branch from `project_state/decision_packet.md`. It changes only harness resume semantics and tests. It does not advance the `samplereverse` reverse-engineering mainline, does not run runtime probes, and does not modify project_state schema/protocol.

## Required Audit

| check | result |
|---|---|
| current `--resume` implementation | `run_harness()` checked `config.resume and result_path.exists()` before this pass, then loaded `case_results/<case>.json` and counted it as resumed. |
| case result status source | Normal statuses come from `_case_result_from_solve_result()`: `passed`, `failed_expected`, `completed_no_expected`, and `not_found`. Harness exception handling writes `error`. Other unstable statuses such as `timeout`, `interrupted`, `partial`, and `blocked` can appear from future/legacy cached result producers and are now classified centrally. |
| old skip predicate | The old predicate only checked file existence and did not inspect `status`. |
| argparse / run CLI structure | `main()` is a single `argparse.ArgumentParser` harness command. It previously exposed `--no-resume`; this pass adds `--resume-policy`, repeatable `--rerun-status`, and `--rerun-error`. |
| existing harness resume tests | `tests/test_harness.py` already had `test_run_harness_resume_skips_completed_cases`; it covered only terminal cached success behavior. No policy/rerun-status equivalent existed. |
| equivalent policy capability | No existing resume-policy or rerun-status capability was found, so this pass adds the minimum harness-local implementation. |
| why unstable statuses rerun | `error`, `timeout`, `interrupted`, `partial`, and `blocked` represent transient or incomplete harness/tool states; treating them as completed under default resume can create false stability. |
| all-existing compatibility | `--resume-policy all-existing` preserves the old behavior: any existing case result is skipped unless its status is explicitly listed in `rerun_statuses`. |
| rerun priority | `rerun_statuses` wins before policy evaluation, including over `all-existing`; `--rerun-error` appends `error`. |
| implementation file scope | The implementation changed only `reverse_agent/harness.py`; focused coverage was added in `tests/test_harness_resume.py`. |
| reverse runtime / protocol risk | No runtime sidecar/probe, `compare_aware_search.py`, `olly_scripts`, project_state schema, decision schema, or report schema was modified. |

## Implementation

- Added centralized resume constants and helpers in `reverse_agent/harness.py`: terminal statuses, non-terminal statuses, `_case_result_status()`, and `_should_resume_case()`.
- Extended `HarnessConfig` with `resume_policy` defaulting to `terminal-only` and `rerun_statuses`.
- Changed resume behavior so default `terminal-only` skips only known terminal statuses; missing, malformed, or unknown statuses rerun.
- Added `--resume-policy {terminal-only,all-existing}`, repeatable `--rerun-status`, and `--rerun-error`.
- Kept new resume policy fields out of the existing `config_digest` payload so old same-run resumes do not fail simply because Phase 2A introduced new CLI/default fields.
- Added focused harness resume tests for terminal skip, default error rerun, legacy all-existing skip, rerun-status override, CLI `--rerun-error`, and unknown/missing status rerun.

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\harness.py` | passed |
| `python -m pytest -q tests\test_harness.py` | `5 passed in 0.33s` |
| `python -m pytest -q tests\test_harness_resume.py` | `6 passed in 0.43s` |
| `python -m pytest -q` | `360 passed in 52.73s` |
| pre-report `python -m reverse_agent.project_state status --state-dir project_state` | passed; current decision is `decision_phase2a_harness_resume_policy_20260520`, previous report is Phase 1F, and `decision_ready_for_execution: True` |
| pre-report `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed |
| pre-report `python -m reverse_agent.project_state lint-report --state-dir project_state` | failed as expected because the active report still referenced Phase 1F |
| pre-report `python -m reverse_agent.project_state lint-handoff --state-dir project_state` | passed as `READY_FOR_CODEX`, tolerating the old report mismatch |

## State Notes

- The active sample state still points at `sr_lhs_thread_follow_timing_20260520_r4`; this pass intentionally did not rebuild sample artifacts or advance the runtime mainline.
- Final report binding is now `report_phase2a_harness_resume_policy_20260520` -> `decision_phase2a_harness_resume_policy_20260520`.
- After this report is written, final `lint-report`, `lint-handoff`, and `archive-round` should complete the Phase 2A handoff.

## Next Suggested Task

Have GPT audit this Phase 2A report and the resulting archive. Do not start Phase 2B/2C/2D or samplereverse runtime work until a fresh decision packet explicitly authorizes it.
