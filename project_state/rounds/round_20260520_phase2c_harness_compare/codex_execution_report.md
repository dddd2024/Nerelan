```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_phase2c_harness_compare_20260520",
  "round_id": "round_20260520_phase2c_harness_compare",
  "based_on_decision_id": "decision_phase2c_harness_compare_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/harness.py",
    "tests/test_harness_compare.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent\\harness.py",
    "python -m pytest -q tests\\test_harness_compare.py",
    "python -m pytest -q tests\\test_harness.py",
    "python -m pytest -q tests\\test_harness_resume.py",
    "python -m pytest -q tests\\test_harness_artifact_manifest.py",
    "python -m pytest -q",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-handoff --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2c_harness_compare"
  ],
  "generated_artifacts": [
    "project_state/rounds/round_20260520_phase2c_harness_compare/round_manifest.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/artifact_index.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/current_state.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/negative_results.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/model_gate.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/task_packet.json",
    "project_state/rounds/round_20260520_phase2c_harness_compare/decision_packet.md",
    "project_state/rounds/round_20260520_phase2c_harness_compare/codex_execution_report.md",
    "project_state/rounds/round_20260520_phase2c_harness_compare/pytest_result.txt",
    "project_state/rounds/round_20260520_phase2c_harness_compare/git_diff.patch"
  ],
  "next_suggested_task": "Have GPT audit Phase 2C harness compare semantics before authorizing Phase 2D archive/path semantics or returning to samplereverse runtime work."
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-20 Phase 2C harness compare

This pass implements the approved Phase 2C engineering branch from `project_state/decision_packet.md`. It adds a read-only harness compare command that compares two harness run case results and lightweight artifact manifest fields. It does not advance the `samplereverse` reverse-engineering mainline, run runtime probes, modify `compare_aware_search.py`, modify `olly_scripts`, modify `project_state.py`, or change the GPT/Codex handoff protocol.

## Required Audit

| check | result |
|---|---|
| Current harness CLI shape | `reverse_agent.harness main()` was a flat parser with required `--dataset`; there was no subcommand parser. |
| Compare CLI compatibility | `main()` now checks `argv[0] == "compare"` before building the flat run parser; all other invocations still use the existing `--dataset` run CLI. |
| Case result compare fields | Existing JSON fields used are `case_id`, `status`, `selected_flag`, `candidate_count`, `validation_count`, `tool_artifact_count`, `structured_evidence_count`, and additive `artifact_manifest`. |
| Artifact manifest structure | Manifest entries are lightweight dicts with `kind`, `path`, `classification`, `size_bytes`, `sha256`, `tool_name`, `owner_profile`, and `strategy_name`; classification comes first from the manifest. |
| Artifact JSON reads | Compare reads only the JSON file named by a manifest entry path and only top-level `classification`, `runtime_backed_count`, `candidate_count`, and `evidence_gate`. |
| Missing cases | Cases present only in base/head are emitted with `presence=base_only` or `presence=head_only`; numeric deltas are `null` when one side is absent. |
| Old or partial case JSON | Missing compare fields, old JSON without `artifact_manifest`, and non-list manifests do not fail compare; missing values produce empty changes or `null` deltas. |
| Artifact path handling | Absolute paths are used directly; relative paths are attempted from the current working directory and then from `reports_dir`; missing or invalid JSON produces `null` lightweight fields. |
| Stable output | `case_deltas` are sorted by `case_id`, `artifact_deltas` by `kind`, and CLI output uses `json.dumps(..., indent=2, sort_keys=True)`. |
| Equivalent existing feature | No existing harness compare command or equivalent JSON delta helper was present. |
| Implementation scope | Code changes are limited to `harness.py`, focused compare tests, and this report/result handoff. |
| Runtime/pipeline risk | Compare only reads `harness_runs/<run>/case_results/*.json` plus listed artifact JSON paths; it does not run pipeline, model calls, probes, or recursive solve_reports scans. |
| Phase 2B limitations | Existing artifact path fallback and round manifest source commit semantics are tolerated but not expanded or fixed; those remain Phase 2D concerns. |

## Implementation

- Added `compare_harness_runs()` to load base/head case result JSON from two named harness runs and emit machine-readable case/artifact deltas.
- Added `python -m reverse_agent.harness compare --base-run ... --head-run ... --reports-dir ... [--output ...]`.
- Added tolerant helpers for old case JSON, missing fields, missing or invalid artifact JSON, absolute/relative artifact paths, and stable first-entry selection when duplicate artifact kinds appear.
- Added `tests/test_harness_compare.py` covering CLI behavior, run CLI compatibility, case deltas, artifact deltas, top-level artifact fields, missing cases, invalid artifacts, and stable sorting.

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent\harness.py` | passed |
| `python -m pytest -q tests\test_harness_compare.py` | `9 passed in 0.46s` |
| `python -m pytest -q tests\test_harness.py` | `5 passed in 0.34s` |
| `python -m pytest -q tests\test_harness_resume.py` | `6 passed in 0.42s` |
| `python -m pytest -q tests\test_harness_artifact_manifest.py` | `3 passed in 0.27s` |
| `python -m pytest -q` | `375 passed in 40.97s` |
| pre-report `python -m reverse_agent.project_state status --state-dir project_state` | passed; active decision is Phase 2C and previous report is Phase 2B |
| pre-report `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed |
| pre-report `python -m reverse_agent.project_state lint-handoff --state-dir project_state` | passed as `READY_FOR_CODEX`, tolerating the old report mismatch |
| pre-report `python -m reverse_agent.project_state lint-report --state-dir project_state` | failed as expected because the active report still referenced Phase 2B |
| final `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed before archive |
| final `python -m reverse_agent.project_state lint-handoff --state-dir project_state` | passed as `REVIEW_COMPLETE` before archive |
| `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2c_harness_compare` | passed; command returned exit code 0 with no console output |

## State Notes

- The active sample state still points at `sr_lhs_thread_follow_timing_20260520_r4`; this pass intentionally did not rebuild sample artifacts or advance the runtime mainline.
- `task_packet.task` remains sample-derived, but `execution_scope=decision_packet_controls_current_round` and this report binds the active Phase 2C decision.
- Compare is intentionally read-only and does not require `--dataset`.

## Next Suggested Task

Have GPT audit the Phase 2C compare output contract and archive. Do not start Phase 2D path/round commit semantics or return to `samplereverse` runtime work until a fresh decision packet explicitly authorizes it.
